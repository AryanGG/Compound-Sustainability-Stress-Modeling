"""
tests/test_pipeline.py
────────────────────────
Unit and integration tests for the SSI pipeline.
No external API calls; uses synthetic data throughout.

Run:
    python -m pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ─── H3 Utilities Tests ───────────────────────────────────────────────────────

class TestH3Utils:
    def test_load_city_bbox_mumbai(self):
        from src.utils.h3_utils import load_city_bbox
        bbox = load_city_bbox("mumbai")
        assert "min_lon" in bbox
        assert bbox["min_lat"] < bbox["max_lat"]
        assert bbox["min_lon"] < bbox["max_lon"]

    def test_load_city_bbox_missing(self):
        from src.utils.h3_utils import load_city_bbox
        with pytest.raises(ValueError):
            load_city_bbox("nonexistent_city_xyz")

    def test_generate_cells_returns_list(self):
        from src.utils.h3_utils import generate_h3_cells_for_city
        cells = generate_h3_cells_for_city("mumbai", resolution=8)
        assert isinstance(cells, list)
        assert len(cells) > 0
        # All cells should be valid H3 strings at resolution 8
        import h3
        for cell in cells[:5]:
            assert h3.get_resolution(cell) == 8

    def test_h3_cells_to_geodataframe(self):
        import geopandas as gpd
        from src.utils.h3_utils import generate_h3_cells_for_city, h3_cells_to_geodataframe
        cells = generate_h3_cells_for_city("mumbai", resolution=8)[:10]
        gdf = h3_cells_to_geodataframe(cells)
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert "centroid_lat" in gdf.columns
        assert gdf.index.name == "h3_index"

    def test_time_skeleton_shape(self):
        from src.utils.h3_utils import build_h3_time_skeleton
        cells = ["abc123", "def456"]
        skeleton = build_h3_time_skeleton(cells, "2020-01", "2020-03")
        # 2 cells × 3 months = 6 rows
        assert len(skeleton) == 6
        assert "h3_index" in skeleton.columns
        assert "date" in skeleton.columns


# ─── Normalization Tests ──────────────────────────────────────────────────────

class TestNormalization:
    def test_zscore_normalizes_correctly(self):
        from src.features.normalize import zscore_normalize
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        norm = zscore_normalize(s)
        assert abs(norm.mean()) < 1e-9
        assert abs(norm.std() - 1.0) < 0.01

    def test_minmax_normalizes_to_01(self):
        from src.features.normalize import minmax_normalize
        s = pd.Series([10.0, 20.0, 30.0])
        norm = minmax_normalize(s)
        assert abs(norm.min()) < 1e-9
        assert abs(norm.max() - 1.0) < 1e-9

    def test_clip_and_floor_removes_negatives(self):
        from src.features.normalize import clip_and_floor
        s = pd.Series([-2.0, -1.0, 0.0, 1.0, 2.0])
        floored = clip_and_floor(s)
        assert (floored >= 0).all()

    def test_normalize_indicator_floor(self):
        from src.features.normalize import normalize_indicator
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 100.0])
        norm = normalize_indicator(s, method="zscore", apply_floor=True)
        assert (norm >= 0).all()

    def test_normalize_indicator_invert(self):
        from src.features.normalize import normalize_indicator
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        norm_normal = normalize_indicator(s, method="zscore", invert=False, apply_floor=False)
        norm_inverted = normalize_indicator(s, method="zscore", invert=True, apply_floor=False)
        # Inverted should have reversed ranking
        assert norm_normal.iloc[0] < norm_normal.iloc[-1]
        assert norm_inverted.iloc[0] > norm_inverted.iloc[-1]


# ─── Heat Stress Tests ────────────────────────────────────────────────────────

class TestHeatStress:
    def _make_panel(self):
        n = 200
        dates = pd.date_range("2015-01", periods=n // 10, freq="MS")
        cells = [f"cell_{i}" for i in range(10)]
        rows = []
        for cell in cells:
            for dt in dates:
                rows.append({
                    "h3_index": cell,
                    "date": dt,
                    "temp_mean_c": 28 + np.random.randn(),
                    "dewpoint_mean_c": 20 + np.random.randn(),
                    "lst_c": 32 + np.random.randn(),
                })
        return pd.DataFrame(rows)

    def test_relative_humidity_range(self):
        from src.features.heat_stress import compute_relative_humidity
        t = pd.Series([30.0, 25.0, 20.0])
        td = pd.Series([25.0, 20.0, 15.0])
        rh = compute_relative_humidity(t, td)
        assert (rh >= 0).all() and (rh <= 100).all()

    def test_heat_index_shape(self):
        from src.features.heat_stress import compute_heat_index
        t = pd.Series([35.0, 28.0, 22.0])
        rh = pd.Series([80.0, 60.0, 50.0])
        hi = compute_heat_index(t, rh)
        assert len(hi) == 3

    def test_add_heat_stress_adds_column(self):
        from src.features.heat_stress import add_heat_stress_idx
        panel = self._make_panel()
        out = add_heat_stress_idx(panel)
        assert "heat_stress_idx" in out.columns
        assert (out["heat_stress_idx"] >= 0).all()


# ─── Water Stress Tests ───────────────────────────────────────────────────────

class TestWaterStress:
    def _make_panel(self):
        n = 200
        dates = pd.date_range("2015-01", periods=20, freq="MS")
        cells = [f"c{i}" for i in range(10)]
        rows = []
        rng = np.random.default_rng(42)
        for cell in cells:
            for dt in dates:
                rows.append({
                    "h3_index": cell,
                    "date": dt,
                    "precip_sum_mm": rng.exponential(50),
                    "soil_moisture": rng.uniform(0.1, 0.4),
                })
        return pd.DataFrame(rows)

    def test_water_stress_non_negative(self):
        from src.features.water_stress import add_water_stress_idx
        panel = self._make_panel()
        out = add_water_stress_idx(panel)
        assert "water_stress_idx" in out.columns
        assert (out["water_stress_idx"] >= 0).all()


# ─── SSI Tests ────────────────────────────────────────────────────────────────

class TestSSI:
    def _make_indicator_panel(self):
        n = 300
        dates = pd.date_range("2015-01", periods=30, freq="MS")
        cells = [f"h{i}" for i in range(10)]
        rng = np.random.default_rng(99)
        rows = []
        for cell in cells:
            for dt in dates:
                rows.append({
                    "city_id": "mumbai",
                    "h3_index": cell,
                    "date": dt,
                    "heat_stress_idx": rng.exponential(1.5),
                    "water_stress_idx": rng.exponential(1.2),
                    "pollution_idx": rng.exponential(1.0),
                    "vegetation_idx": rng.exponential(0.8),
                    "urban_vulnerability_idx": rng.exponential(1.0),
                })
        return pd.DataFrame(rows)

    def test_ssi_value_range(self):
        from src.features.ssi import compute_ssi
        panel = self._make_indicator_panel()
        out = compute_ssi(panel, "mumbai")
        assert "ssi_value" in out.columns
        assert out["ssi_value"].between(0, 1).all()

    def test_ssi_bands_labels(self):
        from src.features.ssi import compute_ssi
        panel = self._make_indicator_panel()
        out = compute_ssi(panel, "mumbai")
        valid_bands = {"Low", "Moderate", "High", "Extreme"}
        assert set(out["ssi_band"].unique()).issubset(valid_bands)

    def test_anomaly_flag_is_boolean(self):
        from src.features.ssi import compute_ssi
        panel = self._make_indicator_panel()
        out = compute_ssi(panel, "mumbai")
        assert out["anomaly_flag"].dtype == bool

    def test_archetype_id_in_range(self):
        from src.features.ssi import compute_ssi
        panel = self._make_indicator_panel()
        out = compute_ssi(panel, "mumbai")
        assert out["archetype_id"].between(1, 6).all()


# ─── Synthetic Panel Integration Test ────────────────────────────────────────

class TestSyntheticPipeline:
    """End-to-end smoke test using synthetic data — no API keys required."""

    def test_synthetic_panel_mumbai(self):
        """Full pipeline from harmonize → features → SSI using synthetic data."""
        from src.process.harmonize import build_h3_panel
        from src.features.heat_stress import add_heat_stress_idx
        from src.features.water_stress import add_water_stress_idx
        from src.features.pollution_exposure import add_pollution_idx
        from src.features.vegetation_degradation import add_vegetation_idx
        from src.features.urban_vulnerability import add_urban_vulnerability_idx
        from src.features.ssi import compute_ssi

        # Use a short time range to keep test fast
        panel = build_h3_panel(
            "mumbai",
            resolution=8,
            start_month="2020-01",
            end_month="2020-06",
            synthetic=True,
        )

        assert not panel.empty, "Panel should not be empty"
        assert "h3_index" in panel.columns
        assert "date" in panel.columns
        assert len(panel) > 0

        # Run all features
        panel = add_heat_stress_idx(panel)
        panel = add_water_stress_idx(panel)
        panel = add_pollution_idx(panel)
        panel = add_vegetation_idx(panel)
        panel = add_urban_vulnerability_idx(panel)
        panel = compute_ssi(panel, "mumbai")

        # Validate final output
        required = ["ssi_value", "ssi_band", "archetype_id", "anomaly_flag"]
        for col in required:
            assert col in panel.columns, f"Missing column: {col}"

        assert panel["ssi_value"].between(0, 1).all()
        assert panel.notna().any().any()

        print(f"\n✓ Synthetic pipeline test passed: {len(panel):,} rows × {len(panel.columns)} cols")
        print(panel[["h3_index", "date", "ssi_value", "ssi_band"]].head())
