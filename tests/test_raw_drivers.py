"""
tests/test_raw_drivers.py
─────────────────────────
Acceptance checks for Step 04 (raw physical driver panels):
1. Balanced panel: rows == n_hexes * n_months.
2. Seasonality test: max(month_mean) - min(month_mean) > 1% of total range.
3. Physical value ranges: heat in [10, 60] °C, veg in [-1, 1], water >= 0.
4. Exposure invariance: zero within-hex variance across months.
5. No rank-compression: raw continuous distribution.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest


@pytest.mark.parametrize("city", ["mumbai", "coimbatore"])
def test_raw_panel_integrity(city: str):
    file_path = Path(f"data/h3_panel/v2_raw/{city}.parquet")
    assert file_path.exists(), f"Missing raw panel: {file_path}"

    df = pd.read_parquet(file_path)

    # 1. Balanced panel check
    n_hex = df["h3_index"].nunique()
    n_months = df["date"].nunique()
    assert len(df) == n_hex * n_months, f"{city} panel unbalanced: {len(df)} != {n_hex} * {n_months}"
    assert n_months == 36, f"Expected 36 months, got {n_months}"

    # 2. Seasonality: monthly means must NOT be constant
    for col in ["heat_raw", "water_raw", "veg_raw"]:
        month_means = df.groupby("date")[col].mean()
        overall_range = df[col].max() - df[col].min()
        spread = month_means.max() - month_means.min()
        assert overall_range > 0, f"{col} has zero overall range"
        spread_pct = (spread / overall_range) * 100.0
        assert spread_pct > 1.0, f"{col} in {city} failed seasonality: spread={spread:.4f} ({spread_pct:.2f}% of range)"

    # 3. Physical ranges
    # Heat Index: between 10°C and 60°C
    assert df["heat_raw"].min() >= 10.0, f"Heat min too low: {df['heat_raw'].min()}"
    assert df["heat_raw"].max() <= 60.0, f"Heat max too high: {df['heat_raw'].max()}"

    # NDVI: between -1.0 and 1.0
    assert df["veg_raw"].min() >= -1.0, f"NDVI min < -1: {df['veg_raw'].min()}"
    assert df["veg_raw"].max() <= 1.0, f"NDVI max > 1: {df['veg_raw'].max()}"

    # Climatic Water Deficit: non-negative (clipped at 0)
    assert df["water_raw"].min() >= 0.0, f"Water deficit < 0: {df['water_raw'].min()}"

    # 4. Exposure invariance: zero within-hex variance across months
    hex_var = df.groupby("h3_index")["exposure_raw"].var().fillna(0.0)
    assert np.allclose(hex_var, 0.0, atol=1e-7), f"exposure_raw varies across months within hex in {city}"

    # 5. Continuous distributions (no discrete rank compression)
    # Average distinct values per date for heat_raw should be substantially greater than a few discrete bins
    distinct_per_month = df.groupby("date")["heat_raw"].nunique().mean()
    assert distinct_per_month > 10, f"heat_raw appears discrete/rank-compressed: avg {distinct_per_month} unique per month"
