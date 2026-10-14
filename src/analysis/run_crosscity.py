"""
src/analysis/run_crosscity.py
─────────────────────────────
Step 13: Cross-city comparative evaluation across Mumbai and Coimbatore.
Validates:
  - Absolute stress level differentials under shared frozen parameters
  - Compound hazard activation frequency
  - Extreme risk band allocations
  - Hazard contribution decompositions
  - Weight scheme invariance (checking whether city rank flips)
Produces results/crosscity.json and results/crosscity__table.csv.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
import yaml

from src.analysis.diagnostics import variance_shares
from src.utils.logger import get_logger
from src.utils.results_io import save_result
from src.v2.indices import IDX_COLS

log = get_logger("run_crosscity")


def run_crosscity_comparison(cfg: dict[str, Any]) -> tuple[dict[str, Any], pd.DataFrame]:
    v2_cfg = cfg.get("v2", {})
    results_dir = v2_cfg.get("paths", {}).get("results", "results")
    v2_dir = Path(v2_cfg.get("paths", {}).get("v2", "data/h3_panel/v2"))
    cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])

    fit_file = Path(results_dir) / "fit_parameters.json"
    if not fit_file.exists():
        raise FileNotFoundError(f"Missing fit parameters at {fit_file}")

    with open(fit_file) as f:
        fit_meta = json.load(f)

    # Clean parameters
    fit_params = {k: v for k, v in fit_meta.items() if not k.startswith("_")}
    primary_w = fit_params["primary_weights"]

    city_records = []
    city_summaries: dict[str, Any] = {}

    for c in cities:
        panel_file = v2_dir / f"{c}.parquet"
        if not panel_file.exists():
            raise FileNotFoundError(f"Missing v2 panel for {c}: {panel_file}")

        df = pd.read_parquet(panel_file)
        n_hex = int(df["h3_index"].nunique())
        n_months = int(df["date"].nunique())

        mean_ssi = float(df["ssi_v2"].mean())
        mean_lin = float(df["ssi_lin_v2"].mean())
        omega_share = float(df["omega_v2"].mean())
        extreme_share = float((df["ssi_band_v2"] == "Extreme").mean())

        # Variance decomposition
        vd = variance_shares(df, "ssi_v2")

        # Contribution of each index: mean(index) * weight, normalized
        raw_contribs = {col: float(df[col].mean() * primary_w[col]) for col in IDX_COLS}
        total_contrib = sum(raw_contribs.values())
        norm_contribs = {col: round(val / total_contrib, 4) for col, val in raw_contribs.items()}

        # Scheme sensitivity means
        scheme_means = {
            s: round(float(df[f"ssi_lin_{s}"].mean()), 4)
            for s in ["equal", "ewm", "critic", "pca"]
            if f"ssi_lin_{s}" in df.columns
        }

        city_record = {
            "city": c,
            "n_hex": n_hex,
            "n_months": n_months,
            "mean_ssi_v2": round(mean_ssi, 4),
            "mean_ssi_lin_v2": round(mean_lin, 4),
            "share_compound_triggered": round(omega_share, 4),
            "share_extreme_band": round(extreme_share, 4),
            "var_between_month": vd["between_month"],
            "var_between_hex": vd["between_hex"],
            "var_residual": vd["residual"],
            **{f"contrib_{col}": norm_contribs[col] for col in IDX_COLS},
            **{f"mean_lin_{s}": scheme_means[s] for s in scheme_means},
        }
        city_records.append(city_record)
        city_summaries[c] = {
            "summary": city_record,
            "contributions": norm_contribs,
            "schemes": scheme_means,
        }

    comp_df = pd.DataFrame(city_records)

    # Check whether city ordering flips under any scheme
    # Order under equal scheme:
    mumbai_eq = comp_df.loc[comp_df["city"] == "mumbai", "mean_lin_equal"].values[0]
    coim_eq = comp_df.loc[comp_df["city"] == "coimbatore", "mean_lin_equal"].values[0]
    expected_order = mumbai_eq > coim_eq

    order_invariance = {}
    for s in ["equal", "ewm", "critic", "pca"]:
        m_s = comp_df.loc[comp_df["city"] == "mumbai", f"mean_lin_{s}"].values[0]
        c_s = comp_df.loc[comp_df["city"] == "coimbatore", f"mean_lin_{s}"].values[0]
        order_invariance[s] = bool((m_s > c_s) == expected_order)

    payload = {
        "cities": cities,
        "fit_parameters_file": str(fit_file),
        "order_invariance_across_schemes": order_invariance,
        "all_schemes_preserve_order": all(order_invariance.values()),
        "table": comp_df,
    }

    save_result("crosscity", payload, cfg, out_dir=results_dir)

    print("=" * 85)
    print("  STEP 13 CROSS-CITY COMPARISON: MUMBAI vs COIMBATORE")
    print("=" * 85)
    print(comp_df[["city", "mean_ssi_v2", "mean_ssi_lin_v2", "share_compound_triggered", "share_extreme_band", "var_between_month", "var_between_hex"]].to_string(index=False))
    print("-" * 85)
    print(f"Ranking Invariance Across All 4 Weighting Schemes: {all(order_invariance.values())}")
    for s, inv in order_invariance.items():
        m_s = comp_df.loc[comp_df["city"] == "mumbai", f"mean_lin_{s}"].values[0]
        c_s = comp_df.loc[comp_df["city"] == "coimbatore", f"mean_lin_{s}"].values[0]
        print(f"  Scheme {s:7s}: Mumbai = {m_s:.4f} vs Coimbatore = {c_s:.4f} (Order preserved: {inv})")
    print("=" * 85)
    log.info(f"Saved crosscity results -> {results_dir}/crosscity.json")

    return payload, comp_df


def main():
    import json
    cfg = yaml.safe_load(open("config.yml"))
    run_crosscity_comparison(cfg)


if __name__ == "__main__":
    main()
