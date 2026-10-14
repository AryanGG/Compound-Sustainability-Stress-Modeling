#!/usr/bin/env python3
"""
audit/fit_check.py
──────────────────
Step 02 provenance check:
Regress ssi_linear on the 5 stress indices using numpy.linalg.lstsq (no intercept).
Validates that the linear index is an exact linear combination of the indicators.
"""

from pathlib import Path
import numpy as np
import pandas as pd

INDICATOR_COLS = [
    "heat_stress_idx",
    "water_stress_idx",
    "vegetation_idx",
    "pollution_idx",
    "urban_vulnerability_idx",
]


def check_linear_fit(csv_path: Path):
    print("=" * 65)
    print(f"Checking linear fit for: {csv_path}")
    print("=" * 65)

    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        return None

    df = pd.read_csv(csv_path)
    available = [c for c in INDICATOR_COLS if c in df.columns]

    if "ssi_linear" not in df.columns:
        print("Error: ssi_linear column missing.")
        return None

    sub = df[available + ["ssi_linear"]].dropna()
    X = sub[available].values
    y = sub["ssi_linear"].values

    coefs, residuals, rank, s = np.linalg.lstsq(X, y, rcond=None)
    y_pred = X @ coefs

    ss_tot = np.sum((y - np.mean(y)) ** 2)
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    print(f"Fitted on {len(sub):,} observations (Rank={rank}):")
    for col, w in zip(available, coefs):
        print(f"  {col:26s} : {w:8.4f}")
    print(f"  {'R-squared':26s} : {r2:8.6f}")
    print(f"  {'Sum of weights':26s} : {np.sum(coefs):8.4f}")

    return {
        "path": str(csv_path),
        "weights": dict(zip(available, coefs)),
        "r2": r2,
        "n_obs": len(sub),
    }


if __name__ == "__main__":
    archive_csv = Path("archive/v1/final/mumbai.csv")
    final_csv = Path("data/h3_panel/final/mumbai.csv")

    target = archive_csv if archive_csv.exists() else final_csv
    check_linear_fit(target)
