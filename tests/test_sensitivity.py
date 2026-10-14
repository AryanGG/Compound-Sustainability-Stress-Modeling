"""
tests/test_sensitivity.py
─────────────────────────
Acceptance checks for Step 10:
1. Experiment count: 48 rows (40 grid + 5 leave-one-out + 3 baseline bounds).
2. Reference row self-consistency: rho == 1.0 against itself.
3. Summary table integrity and non-empty classification.
"""

from pathlib import Path
import numpy as np
import pandas as pd


def test_sensitivity_results():
    grid_csv = Path("results/sensitivity__grid.csv")
    summary_csv = Path("results/sensitivity_summary.csv")

    assert grid_csv.exists(), f"Missing grid CSV: {grid_csv}"
    assert summary_csv.exists(), f"Missing summary CSV: {summary_csv}"

    df_grid = pd.read_csv(grid_csv)
    # 40 scheme x gamma x q + 5 leave-one-out + 3 baseline-bounds = 48 rows
    assert len(df_grid) == 48, f"Expected 48 rows in sensitivity grid, got {len(df_grid)}"

    # Self-consistency check on reference experiment
    ref = df_grid[
        (df_grid["scheme"] == "equal") &
        (df_grid["gamma"] == 0.30) &
        (df_grid["q"] == 0.90) &
        (df_grid["dropped_index"] == "none") &
        (df_grid["baseline_lo"] == 0.02)
    ]
    assert len(ref) >= 1
    assert np.isclose(ref.iloc[0]["rho_hexmean"], 1.0, atol=1e-4)

    # Summary table checks
    df_sum = pd.read_csv(summary_csv)
    assert len(df_sum) == 5
    for col in ["family", "min_rho_hexmean", "min_tau_hexmean", "min_jaccard", "bucket"]:
        assert col in df_sum.columns
        assert not df_sum[col].isna().any()
