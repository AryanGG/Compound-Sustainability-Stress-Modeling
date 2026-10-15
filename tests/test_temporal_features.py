"""
tests/test_temporal_features.py
───────────────────────────────
Unit tests for Step 02: Temporal Feature Engineering Pipeline.
Verifies lag integrity, forward target shifting, velocities, and zero cross-cell leakage.
"""

import numpy as np
import pandas as pd
import pytest

from src.ml.temporal_features import (
    build_temporal_feature_matrix,
    get_feature_column_names,
)


@pytest.fixture
def synthetic_panel_data():
    """Create a 2-cell, 12-month synthetic panel to test temporal lag and target shifts."""
    records = []
    cells = ["hex_A", "hex_B"]
    dates = pd.date_range("2021-01-01", periods=12, freq="MS").strftime("%Y-%m-%d")

    for c_idx, cell in enumerate(cells):
        base_val = 10.0 * (c_idx + 1)
        for m_idx, dt in enumerate(dates):
            records.append({
                "h3_index": cell,
                "date": dt,
                "temp_mean_c": base_val + m_idx,
                "lst_c": base_val + 5.0 + m_idx * 1.5,
                "dewpoint_mean_c": 15.0 + m_idx * 0.5,
                "precip_sum_mm": 50.0 + m_idx * 10.0,
                "soil_moisture": 0.40 - m_idx * 0.02,
                "wind_speed": 3.0,
                "radiation": 200.0,
                "pm25": 80.0 + m_idx * 5.0,
                "ndvi": 0.50 - m_idx * 0.02,
                "heat_v2": 0.20 + m_idx * 0.05,
                "water_v2": 0.30 + m_idx * 0.04,
                "pollution_v2": 0.40 + m_idx * 0.03,
                "veg_v2": 0.35 + m_idx * 0.02,
                "exposure_v2": 0.50,
                "ssi_v2": 0.30 + (0.35 if m_idx in [4, 5, 6, 7] else 0.05),
                "omega_v2": 0.15 if m_idx in [5, 6] else 0.0,
                "event_heatwave": 1 if m_idx in [5, 6] else 0,
                "event_smog": 1 if m_idx in [9, 10] else 0,
                "event_compound": 1 if m_idx in [5, 6] else 0,
                "event_extreme_ssi": 1 if m_idx in [5, 6, 7] else 0,
                "event_any_emergency": 1 if m_idx in [5, 6, 7, 9, 10] else 0,
                "built_up_fraction": 0.75,
                "building_density": 120.0,
                "road_density_km_km2": 15.0,
                "building_fp_fraction": 0.30,
                "green_space_fraction": 0.10,
                "latitude": 19.0 + c_idx * 0.1,
                "longitude": 72.8 + c_idx * 0.1,
            })
    return pd.DataFrame(records)


def test_temporal_lags_and_forward_targets(synthetic_panel_data):
    df = synthetic_panel_data
    featured = build_temporal_feature_matrix(df)

    for cell in ["hex_A", "hex_B"]:
        sub = featured[featured["h3_index"] == cell].sort_values("date").reset_index(drop=True)

        # Check Lag 1: sub['temp_mean_c_lag1'][t] == sub['temp_mean_c'][t-1]
        assert pd.isna(sub.loc[0, "temp_mean_c_lag1"])
        for t in range(1, len(sub)):
            assert np.isclose(sub.loc[t, "temp_mean_c_lag1"], sub.loc[t - 1, "temp_mean_c"])

        # Check Lag 2
        assert pd.isna(sub.loc[0, "temp_mean_c_lag2"])
        assert pd.isna(sub.loc[1, "temp_mean_c_lag2"])
        for t in range(2, len(sub)):
            assert np.isclose(sub.loc[t, "temp_mean_c_lag2"], sub.loc[t - 2, "temp_mean_c"])

        # Check Forward Target (1-month lead time): target_1m[t] == event[t+1]
        assert pd.isna(sub.loc[len(sub) - 1, "target_event_heatwave_1m"])
        for t in range(len(sub) - 1):
            assert sub.loc[t, "target_event_heatwave_1m"] == sub.loc[t + 1, "event_heatwave"]

        # Check Forward Target (2-month lead time): target_2m[t] == event[t+2]
        assert pd.isna(sub.loc[len(sub) - 1, "target_event_heatwave_2m"])
        assert pd.isna(sub.loc[len(sub) - 2, "target_event_heatwave_2m"])
        for t in range(len(sub) - 2):
            assert sub.loc[t, "target_event_heatwave_2m"] == sub.loc[t + 2, "event_heatwave"]


def test_velocities_and_momentum(synthetic_panel_data):
    df = synthetic_panel_data
    featured = build_temporal_feature_matrix(df)

    sub = featured[featured["h3_index"] == "hex_A"].sort_values("date").reset_index(drop=True)

    # 1-month velocity = current - lag1
    valid_idx = sub["lst_velocity_1m"].notna()
    expected_v1 = sub.loc[valid_idx, "lst_c"] - sub.loc[valid_idx, "lst_c_lag1"]
    assert np.allclose(sub.loc[valid_idx, "lst_velocity_1m"], expected_v1)

    # 2-month acceleration = current - lag2
    valid_accel = sub["lst_accel_2m"].notna()
    expected_accel = sub.loc[valid_accel, "lst_c"] - sub.loc[valid_accel, "lst_c_lag2"]
    assert np.allclose(sub.loc[valid_accel, "lst_accel_2m"], expected_accel)


def test_stress_exhaustion_streak(synthetic_panel_data):
    df = synthetic_panel_data
    featured = build_temporal_feature_matrix(df)

    sub = featured[featured["h3_index"] == "hex_A"].sort_values("date").reset_index(drop=True)

    # In synthetic fixture, ssi_v2 >= 0.50 at months 4, 5, 6, 7 (indices 4 to 7)
    # Months 0..3: streak = 0
    for t in range(4):
        assert sub.loc[t, "stress_exhaustion_streak"] == 0

    # Month 4: streak = 1
    assert sub.loc[4, "stress_exhaustion_streak"] == 1
    # Month 5: streak = 2
    assert sub.loc[5, "stress_exhaustion_streak"] == 2
    # Month 6: streak = 3
    assert sub.loc[6, "stress_exhaustion_streak"] == 3
    # Month 7: streak = 4
    assert sub.loc[7, "stress_exhaustion_streak"] == 4
    # Month 8: stress drops below 0.50 -> streak resets to 0
    assert sub.loc[8, "stress_exhaustion_streak"] == 0


def test_cyclical_calendar_encoding(synthetic_panel_data):
    df = synthetic_panel_data
    featured = build_temporal_feature_matrix(df)

    assert (featured["sin_month"] >= -1.0).all() and (featured["sin_month"] <= 1.0).all()
    assert (featured["cos_month"] >= -1.0).all() and (featured["cos_month"] <= 1.0).all()

    # sin^2 + cos^2 = 1.0
    trig_identity = featured["sin_month"] ** 2 + featured["cos_month"] ** 2
    assert np.allclose(trig_identity, 1.0)


def test_feature_columns_extraction(synthetic_panel_data):
    df = synthetic_panel_data
    featured = build_temporal_feature_matrix(df)
    features = get_feature_column_names(featured)

    # Verify no target or raw event flags leaked into predictor feature list
    for f in features:
        assert not f.startswith("target_")
        assert not f.startswith("event_")
        assert f not in ["h3_index", "date", "city_id"]

    assert "lst_c_lag1" in features
    assert "soil_moisture_drawdown_1m" in features
    assert "stress_exhaustion_streak" in features
    assert "sin_month" in features
