"""
tests/test_event_definitions.py
───────────────────────────────
Unit tests for Step 01: Pre-Registration of Event Definitions.
Verifies binary bounds, statutory thresholds, relative tails, and compound logic.
"""

import numpy as np
import pandas as pd
import pytest

from src.ml.event_definitions import (
    compute_event_heatwave,
    compute_event_smog,
    compute_event_compound,
    compute_event_extreme_ssi,
    compute_all_events,
)


@pytest.fixture
def sample_event_data():
    """Synthetic multi-cell dataset with known boundary points."""
    np.random.seed(20260101)
    n = 100
    df = pd.DataFrame({
        "h3_index": [f"hex_{i%10}" for i in range(n)],
        "date": [f"2022-{(i%12)+1:02d}-01" for i in range(n)],
        "lst_c": np.linspace(25.0, 45.0, n),
        "heat_v2": np.linspace(0.1, 0.95, n),
        "pm25": np.linspace(30.0, 350.0, n),
        "pollution_v2": np.linspace(0.1, 0.95, n),
        "omega_v2": np.array([0.0]*85 + [0.15]*15),
        "ssi_band_v2": ["Low"]*40 + ["Moderate"]*30 + ["High"]*20 + ["Extreme"]*10,
        "ssi_v2": np.linspace(0.1, 0.85, n),
    })
    return df


def test_heatwave_event_properties(sample_event_data):
    df = sample_event_data

    # Statutory mode
    e_stat = compute_event_heatwave(df, mode="statutory", statutory_c=42.0)
    assert set(e_stat.unique()).issubset({0, 1})
    # Every row with lst_c >= 42.0 must be 1
    assert (e_stat[df["lst_c"] >= 42.0] == 1).all()
    # Rows below 42 and below heat_v2 0.85 must be 0
    below_mask = (df["lst_c"] < 42.0) & (df["heat_v2"] < 0.85)
    assert (e_stat[below_mask] == 0).all()

    # Relative tail mode
    e_rel = compute_event_heatwave(df, mode="relative_tail", q=0.90)
    assert set(e_rel.unique()).issubset({0, 1})
    assert e_rel.mean() >= 0.10

    # Hybrid mode
    e_hyb = compute_event_heatwave(df, mode="hybrid")
    assert (e_hyb >= e_stat).all()
    assert (e_hyb >= e_rel).all()


def test_smog_event_properties(sample_event_data):
    df = sample_event_data

    # Statutory mode (CPCB Severe limit = 250 µg/m³)
    e_stat = compute_event_smog(df, mode="statutory", statutory_ugm3=250.0)
    assert set(e_stat.unique()).issubset({0, 1})
    assert (e_stat[df["pm25"] >= 250.0] == 1).all()
    below_mask = (df["pm25"] < 250.0) & (df["pollution_v2"] < 0.85)
    assert (e_stat[below_mask] == 0).all()

    # Relative tail mode
    e_rel = compute_event_smog(df, mode="relative_tail", q=0.90)
    assert set(e_rel.unique()).issubset({0, 1})
    assert e_rel.mean() >= 0.10


def test_compound_and_ssi_event_properties(sample_event_data):
    df = sample_event_data

    # Compound crisis: triggers iff omega_v2 > 0
    e_comp = compute_event_compound(df)
    assert (e_comp[df["omega_v2"] > 0] == 1).all()
    assert (e_comp[df["omega_v2"] == 0] == 0).all()

    # Extreme SSI breach: triggers iff ssi_band_v2 == 'Extreme'
    e_ssi = compute_event_extreme_ssi(df)
    assert (e_ssi[df["ssi_band_v2"] == "Extreme"] == 1).all()
    assert (e_ssi[df["ssi_band_v2"] != "Extreme"] == 0).all()


def test_compute_all_events(sample_event_data):
    df = sample_event_data
    out = compute_all_events(df, city_name="test_city", mode="hybrid")

    expected_cols = [
        "event_heatwave",
        "event_smog",
        "event_compound",
        "event_extreme_ssi",
        "event_any_emergency",
        "city_id",
    ]
    for col in expected_cols:
        assert col in out.columns

    # Any emergency must be 1 if any constituent is 1
    any_manual = (
        (out["event_heatwave"] == 1)
        | (out["event_smog"] == 1)
        | (out["event_compound"] == 1)
        | (out["event_extreme_ssi"] == 1)
    ).astype(int)
    assert (out["event_any_emergency"] == any_manual).all()
    assert out["city_id"].iloc[0] == "test_city"
