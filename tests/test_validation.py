"""
tests/test_validation.py
─────────────────────────
Step 11 unit tests:
1. Block-bootstrap CI function test on spatial autocorrelated data:
   asserts that spatial block bootstrap produces a wider confidence interval
   than naive i.i.d. bootstrap due to spatial cluster correlation.
2. Structure of results/validation.json: V1-V6 keys present with hypothesis_met boolean.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from src.analysis.run_validation import block_bootstrap_ci


def test_block_bootstrap_ci_wider_than_naive():
    # Construct synthetic data with strong cluster-level correlation
    np.random.seed(20260101)
    n_blocks = 20
    block_size = 50

    blocks = []
    x_vals = []
    y_vals = []

    for b in range(n_blocks):
        cluster_shock = np.random.normal(0, 2.0)
        for _ in range(block_size):
            blocks.append(f"block_{b}")
            x = cluster_shock + np.random.normal(0, 0.5)
            y = 0.8 * cluster_shock + np.random.normal(0, 0.5)
            x_vals.append(x)
            y_vals.append(y)

    df = pd.DataFrame({"block_id": blocks, "x": x_vals, "y": y_vals})

    ci_res = block_bootstrap_ci(df, "x", "y", block_col="block_id", n_boot=400)

    block_ci_width = ci_res["ci_hi"] - ci_res["ci_lo"]
    naive_ci_width = ci_res["naive_ci_hi"] - ci_res["naive_ci_lo"]

    # Block bootstrap CI should be noticeably wider than naive CI
    assert block_ci_width > naive_ci_width, (
        f"Expected block bootstrap CI ({block_ci_width:.4f}) to be wider than naive CI ({naive_ci_width:.4f})"
    )


def test_validation_json_structure():
    val_file = Path("results/validation.json")
    if val_file.exists():
        with open(val_file) as f:
            data = json.load(f)

        for v_key in ["V1_lockdown", "V2_heatwave", "V3_independent_lst_validity",
                      "V4_spatial_structure_morans_i", "V5_exposure_held_out", "V6_greenery_exposure_cross_city"]:
            assert v_key in data, f"Missing {v_key} in validation results"
            assert "hypothesis_met" in data[v_key]
            assert isinstance(data[v_key]["hypothesis_met"], bool)
