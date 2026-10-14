#!/usr/bin/env python3
"""
scripts/step7_weights.py
────────────────────────
Step 07: Fit all four weighting schemes (Equal, EWM, CRITIC, PCA) on the
pooled reference panel (Mumbai + Coimbatore).
Outputs results/weights_preview.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import yaml

from src.utils.logger import get_logger
from src.v2.indices import fit_baseline, apply_baseline, IDX_COLS
from src.v2.weighting import fit_all_weights

log = get_logger(__name__)


def main():
    cfg = yaml.safe_load(open("config.yml"))
    v2_cfg = cfg.get("v2", {})
    ref_cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])

    # 1. Load and pool reference raw panels
    raw_dfs = [pd.read_parquet(f"data/h3_panel/v2_raw/{c}.parquet") for c in ref_cities]
    pooled_raw = pd.concat(raw_dfs, ignore_index=True)

    # 2. Fit and apply baseline
    lo_q = v2_cfg.get("baseline", {}).get("lo_q", 0.02)
    hi_q = v2_cfg.get("baseline", {}).get("hi_q", 0.98)
    base = fit_baseline(pooled_raw, lo=lo_q, hi=hi_q)
    pooled_v2 = apply_baseline(pooled_raw, base)

    # 3. Fit weighting schemes on IDX_COLS
    X = pooled_v2[IDX_COLS]
    schemes, pc1_var = fit_all_weights(X)

    # 4. Compute pairwise Spearman correlation matrix
    spearman_mat = pd.DataFrame(index=IDX_COLS, columns=IDX_COLS, dtype=float)
    for c1 in IDX_COLS:
        for c2 in IDX_COLS:
            r, _ = spearmanr(X[c1], X[c2])
            spearman_mat.loc[c1, c2] = round(float(r), 4)

    # Print summary table
    print("=" * 75)
    print("  STEP 07 WEIGHTING SCHEMES (POOLED REFERENCE PANEL)")
    print(f"  Reference cities: {ref_cities} | Total rows: {len(X):,}")
    print("=" * 75)
    print(f"{'Indicator':15s} | {'Equal':10s} | {'EWM':10s} | {'CRITIC':10s} | {'PCA':10s}")
    print("-" * 75)
    weights_dict = {}
    for col in IDX_COLS:
        w_eq = float(schemes["equal"][col])
        w_ew = float(schemes["ewm"][col])
        w_cr = float(schemes["critic"][col])
        w_pc = float(schemes["pca"][col])
        print(f"{col:15s} | {w_eq:10.4f} | {w_ew:10.4f} | {w_cr:10.4f} | {w_pc:10.4f}")

    print("-" * 75)
    print(f"PC1 Explained Variance: {pc1_var * 100:.2f}%")
    print("=" * 75)
    print("\nPairwise Spearman Correlation Matrix:")
    print(spearman_mat.to_string())

    # Format JSON payload
    payload = {
        "reference_cities": ref_cities,
        "n_obs": len(X),
        "pc1_explained_variance": round(pc1_var, 4),
        "weights": {
            s: {col: round(float(schemes[s][col]), 4) for col in IDX_COLS}
            for s in ["equal", "ewm", "critic", "pca"]
        },
        "spearman_matrix": spearman_mat.to_dict(),
    }

    out_file = Path("results/weights_preview.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as fh:
        json.dump(payload, fh, indent=2)

    log.info(f"Saved weights preview -> {out_file}")


if __name__ == "__main__":
    main()
