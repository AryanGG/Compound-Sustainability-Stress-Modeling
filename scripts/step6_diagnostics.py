#!/usr/bin/env python3
"""
scripts/step6_diagnostics.py
────────────────────────────
Step 06: Variance diagnostics comparing v1 sub-indices (from final/)
against v2 global-baseline indices.
Computes two-way additive variance decomposition and monthly-mean spread.
Saves results to results/diagnostics_variance.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import yaml

from src.analysis.diagnostics import variance_shares, monthly_mean_spread
from src.utils.logger import get_logger
from src.v2.indices import fit_baseline, apply_baseline, IDX_COLS

log = get_logger(__name__)

V1_MAP = {
    "heat": "heat_stress_idx",
    "water": "water_stress_idx",
    "veg": "vegetation_idx",
    "pollution": "pollution_idx",
    "exposure": "urban_vulnerability_idx",
}

V2_MAP = {
    "heat": "heat_v2",
    "water": "water_v2",
    "veg": "veg_v2",
    "pollution": "pollution_v2",
    "exposure": "exposure_v2",
}


def run_diagnostics_city(city: str, base: dict[str, Any]) -> dict[str, Any]:
    # 1. Load v1 from archive/v1/final or data/h3_panel/final
    v1_file = Path(f"archive/v1/final/{city}.parquet")
    if not v1_file.exists():
        v1_file = Path(f"data/h3_panel/final/{city}.parquet")

    # 2. Load v2_raw and apply baseline
    raw_file = Path(f"data/h3_panel/v2_raw/{city}.parquet")
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw panel not found: {raw_file}")

    raw_df = pd.read_parquet(raw_file)
    v2_df = apply_baseline(raw_df, base)

    v1_df = pd.read_parquet(v1_file) if v1_file.exists() else None

    report: dict[str, Any] = {}
    print("=" * 80)
    print(f"  STEP 06 VARIANCE DIAGNOSTICS: {city.upper()}")
    print("=" * 80)
    print(f"{'Dimension':10s} | {'v1 Spread':10s} | {'v2 Spread':10s} | {'v2 Month %':10s} | {'v2 Hex %':10s} | {'v2 Res %':10s}")
    print("-" * 80)

    for dim in ["heat", "water", "veg", "pollution", "exposure"]:
        v2_col = V2_MAP[dim]
        v1_col = V1_MAP[dim]

        v2_spread = monthly_mean_spread(v2_df, v2_col)
        v2_var = variance_shares(v2_df, v2_col)

        v1_spread = monthly_mean_spread(v1_df, v1_col) if v1_df is not None and v1_col in v1_df.columns else np.nan
        v1_var = variance_shares(v1_df, v1_col) if v1_df is not None and v1_col in v1_df.columns else {}

        report[dim] = {
            "v1_spread": v1_spread,
            "v1_variance": v1_var,
            "v2_spread": v2_spread,
            "v2_variance": v2_var,
            "v2_min": round(float(v2_df[v2_col].min()), 4),
            "v2_max": round(float(v2_df[v2_col].max()), 4),
            "v2_clip_0_share": round(float((v2_df[v2_col] <= 0.0001).mean()), 4),
            "v2_clip_1_share": round(float((v2_df[v2_col] >= 0.9999).mean()), 4),
        }

        v1_sp_str = f"{v1_spread:10.4f}" if not np.isnan(v1_spread) else "       N/A"
        print(f"{dim:10s} | {v1_sp_str} | {v2_spread:10.4f} | {v2_var['between_month']*100:9.1f}% | {v2_var['between_hex']*100:9.1f}% | {v2_var['residual']*100:9.1f}%")

    print("-" * 80)
    return report


def main():
    parser = argparse.ArgumentParser(description="Run Step 06 variance diagnostics.")
    parser.add_argument("city", nargs="?", default="mumbai", help="City name or 'all'")
    args = parser.parse_args()

    cfg = yaml.safe_load(open("config.yml"))
    v2_cfg = cfg.get("v2", {})
    ref_cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])

    # Fit pooled baseline on reference cities
    pooled_dfs = [pd.read_parquet(f"data/h3_panel/v2_raw/{c}.parquet") for c in ref_cities]
    pooled_ref = pd.concat(pooled_dfs, ignore_index=True)

    lo_q = v2_cfg.get("baseline", {}).get("lo_q", 0.02)
    hi_q = v2_cfg.get("baseline", {}).get("hi_q", 0.98)
    base = fit_baseline(pooled_ref, lo=lo_q, hi=hi_q)

    # Save fit_parameters
    fit_params_path = Path("results/fit_parameters.json")
    fit_params_path.parent.mkdir(parents=True, exist_ok=True)
    with open(fit_params_path, "w") as fh:
        json.dump(base, fh, indent=2)
    log.info(f"Saved frozen baseline parameters -> {fit_params_path}")

    target_cities = ref_cities if args.city == "all" else [args.city]
    all_reports = {}

    for c in target_cities:
        all_reports[c] = run_diagnostics_city(c, base)

    out_file = Path("results/diagnostics_variance.json")
    with open(out_file, "w") as fh:
        json.dump(all_reports, fh, indent=2)
    log.info(f"Saved diagnostics summary -> {out_file}")


if __name__ == "__main__":
    main()
