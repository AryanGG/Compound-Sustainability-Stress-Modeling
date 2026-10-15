"""
tests/test_predict_extreme_events.py
─────────────────────────────────────
Unit & integration tests for the unified predict_extreme_events master pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from src.ml.predict_extreme_events import run_end_to_end_pipeline
from src.ml.event_definitions import CITIES


def test_predict_extreme_events_pipeline_single_city(tmp_path):
    """
    Test running the end-to-end early warning pipeline for a single city (Coimbatore).
    """
    res = run_end_to_end_pipeline(
        cities=["coimbatore"],
        generate_figures=False,
        export_playbooks=False,
    )

    assert "coimbatore" in res["cities"]
    assert "coimbatore" in res["event_prevalence"]
    assert "coimbatore" in res["feature_meta"]
    assert "coimbatore" in res["training_metrics"]

    # Verify event prevalence output
    prev = res["event_prevalence"]["coimbatore"]["event_prevalence"]
    assert "heatwave_share" in prev
    assert "smog_share" in prev
    assert "compound_share" in prev
    assert 0.0 <= prev["heatwave_share"] <= 1.0

    # Verify feature meta
    feat = res["feature_meta"]["coimbatore"]
    assert feat["valid_rows_1m_lead"] > 0
    assert feat["total_features"] >= 40

    # Verify training metrics
    metrics = res["training_metrics"]["coimbatore"]
    assert "events" in metrics
    assert "heatwave" in metrics["events"]
    assert "continuous_ssi" in metrics
    assert "r2_score" in metrics["continuous_ssi"]

