"""
src/analysis/run_sensitivity.py
───────────────────────────────
Step 10: Multi-dimensional sensitivity and robustness suite.
Sweeps:
  - S1: Weighting schemes (equal, ewm, critic, pca)
  - S2: Compound coupling factor gamma (0.1, 0.2, 0.3, 0.4, 0.5)
  - S3: Compound trigger quantile q (0.75, 0.90, 0.95)
  - S4: Leave-one-index-out (drop each of 5 indicators)
  - S5: Global baseline quantiles (0.01/0.99, 0.02/0.98, 0.05/0.95)
Produces:
  - results/sensitivity.json
  - results/sensitivity__grid.csv
  - results/sensitivity_summary.csv
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
import yaml

from src.utils.logger import get_logger
from src.utils.results_io import save_result
from src.v2.indices import fit_baseline, apply_baseline, IDX_COLS
from src.v2.ssi import fit_compound, apply_ssi
from src.v2.weighting import fit_all_weights

log = get_logger("run_sensitivity")


def rank_agreement(df: pd.DataFrame, a: str, b: str, hexc: str = "h3_index", datec: str = "date") -> dict[str, float]:
    """Compute spatial and temporal rank agreement metrics between two index columns."""
    hm = df.groupby(hexc)[[a, b]].mean()
    rho_h, _ = spearmanr(hm[a], hm[b])
    tau_h, _ = kendalltau(hm[a], hm[b])

    wm_rhos = []
    for _, g in df.groupby(datec):
        if g[a].nunique() > 1 and g[b].nunique() > 1:
            r, _ = spearmanr(g[a], g[b])
            wm_rhos.append(r)
    mean_wm_rho = float(np.nanmean(wm_rhos)) if wm_rhos else 1.0

    k = max(1, int(0.10 * len(hm)))
    top_a = set(hm[a].nlargest(k).index)
    top_b = set(hm[b].nlargest(k).index)
    jaccard = float(len(top_a & top_b) / len(top_a | top_b))

    return {
        "rho_hexmean": round(float(rho_h), 4),
        "tau_hexmean": round(float(tau_h), 4),
        "rho_withinmonth_mean": round(mean_wm_rho, 4),
        "top_decile_jaccard": round(jaccard, 4),
    }


def classify_bucket(rho: float) -> str:
    """Pre-declared reading rule bucket."""
    if rho >= 0.90:
        return "stable"
    elif rho >= 0.70:
        return "moderately sensitive"
    else:
        return "sensitive"


def run_sensitivity(cfg: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    v2_cfg = cfg.get("v2", {})
    ref_cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])
    raw_dir = Path(v2_cfg.get("paths", {}).get("raw", "data/h3_panel/v2_raw"))
    results_dir = v2_cfg.get("paths", {}).get("results", "results")

    compound_pair = tuple(v2_cfg.get("compound", {}).get("pair", ["heat_v2", "water_v2"]))

    # 1. Load pooled reference raw observations
    raw_dfs = [pd.read_parquet(raw_dir / f"{c}.parquet") for c in ref_cities]
    pooled_raw = pd.concat(raw_dfs, ignore_index=True)

    # Base reference normalization (lo=0.02, hi=0.98)
    base_default = fit_baseline(pooled_raw, lo=0.02, hi=0.98)
    Z = apply_baseline(pooled_raw, base_default)

    schemes, _ = fit_all_weights(Z[IDX_COLS])
    primary = v2_cfg.get("primary_scheme", "equal")

    gammas = [0.1, 0.2, 0.3, 0.4, 0.5]
    qs = [0.75, 0.90]

    # Canonical baseline reference run (equal, gamma=0.3, q=0.90)
    ref_thr = fit_compound(Z, pair=compound_pair, q=0.90)
    ref = apply_ssi(Z, schemes[primary], ref_thr, gamma=0.30)

    rows = []

    # --- S1, S2, S3 Grid: scheme x gamma x q (4 x 5 x 2 = 40 rows) ---
    for s, g, q in itertools.product(["equal", "ewm", "critic", "pca"], gammas, qs):
        thr = fit_compound(Z, pair=compound_pair, q=q)
        S = apply_ssi(Z, schemes[s], thr, gamma=g)
        T = ref[["h3_index", "date", "ssi_v2"]].assign(alt=S["ssi_v2"].values)
        metrics = rank_agreement(T, "ssi_v2", "alt")
        rows.append({
            "experiment": "grid_sweep",
            "family": "S1_S2_S3",
            "scheme": s,
            "gamma": g,
            "q": q,
            "dropped_index": "none",
            "baseline_lo": 0.02,
            "baseline_hi": 0.98,
            "omega_share": round(float(S["omega_v2"].mean()), 4),
            "mean_ssi": round(float(S["ssi_v2"].mean()), 4),
            **metrics,
        })

    # --- S4: Leave-One-Index-Out (5 rows) ---
    for col in IDX_COLS:
        w_dropped = schemes[primary].drop(col)
        w_norm = w_dropped / w_dropped.sum()
        S = apply_ssi(Z, w_norm, ref_thr, gamma=0.30)
        T = ref[["h3_index", "date", "ssi_v2"]].assign(alt=S["ssi_v2"].values)
        metrics = rank_agreement(T, "ssi_v2", "alt")
        rows.append({
            "experiment": "leave_one_out",
            "family": "S4_leave_one_out",
            "scheme": primary,
            "gamma": 0.30,
            "q": 0.90,
            "dropped_index": col,
            "baseline_lo": 0.02,
            "baseline_hi": 0.98,
            "omega_share": round(float(S["omega_v2"].mean()), 4),
            "mean_ssi": round(float(S["ssi_v2"].mean()), 4),
            **metrics,
        })

    # --- S5: Baseline Bounds refit (3 rows) ---
    bound_pairs = [(0.01, 0.99), (0.02, 0.98), (0.05, 0.95)]
    for lo_b, hi_b in bound_pairs:
        base_alt = fit_baseline(pooled_raw, lo=lo_b, hi=hi_b)
        Z_alt = apply_baseline(pooled_raw, base_alt)
        schemes_alt, _ = fit_all_weights(Z_alt[IDX_COLS])
        thr_alt = fit_compound(Z_alt, pair=compound_pair, q=0.90)
        S = apply_ssi(Z_alt, schemes_alt[primary], thr_alt, gamma=0.30)
        T = ref[["h3_index", "date", "ssi_v2"]].assign(alt=S["ssi_v2"].values)
        metrics = rank_agreement(T, "ssi_v2", "alt")
        rows.append({
            "experiment": "baseline_bounds",
            "family": "S5_baseline_bounds",
            "scheme": primary,
            "gamma": 0.30,
            "q": 0.90,
            "dropped_index": "none",
            "baseline_lo": lo_b,
            "baseline_hi": hi_b,
            "omega_share": round(float(S["omega_v2"].mean()), 4),
            "mean_ssi": round(float(S["ssi_v2"].mean()), 4),
            **metrics,
        })

    grid_df = pd.DataFrame(rows)

    # Self-consistency check on reference row
    ref_row = grid_df[
        (grid_df["scheme"] == primary) &
        (grid_df["gamma"] == 0.30) &
        (grid_df["q"] == 0.90) &
        (grid_df["dropped_index"] == "none") &
        (grid_df["baseline_lo"] == 0.02)
    ].iloc[0]
    assert np.isclose(ref_row["rho_hexmean"], 1.0, atol=1e-4), "Reference row self-correlation != 1.0"

    # Family summary table
    summary_rows = []
    # 1. Scheme comparison (S1)
    s1_sub = grid_df[(grid_df["gamma"] == 0.30) & (grid_df["q"] == 0.90) & (grid_df["dropped_index"] == "none") & (grid_df["baseline_lo"] == 0.02)]
    min_rho_s1 = float(s1_sub["rho_hexmean"].min())
    summary_rows.append({
        "family": "S1 (Weighting scheme: Equal/EWM/CRITIC/PCA)",
        "min_rho_hexmean": min_rho_s1,
        "min_tau_hexmean": float(s1_sub["tau_hexmean"].min()),
        "min_jaccard": float(s1_sub["top_decile_jaccard"].min()),
        "bucket": classify_bucket(min_rho_s1),
    })

    # 2. Gamma coupling (S2)
    s2_sub = grid_df[(grid_df["scheme"] == primary) & (grid_df["q"] == 0.90) & (grid_df["dropped_index"] == "none") & (grid_df["baseline_lo"] == 0.02)]
    min_rho_s2 = float(s2_sub["rho_hexmean"].min())
    summary_rows.append({
        "family": "S2 (Coupling parameter gamma: 0.1 to 0.5)",
        "min_rho_hexmean": min_rho_s2,
        "min_tau_hexmean": float(s2_sub["tau_hexmean"].min()),
        "min_jaccard": float(s2_sub["top_decile_jaccard"].min()),
        "bucket": classify_bucket(min_rho_s2),
    })

    # 3. Quantile threshold q (S3)
    s3_sub = grid_df[(grid_df["scheme"] == primary) & (grid_df["gamma"] == 0.30) & (grid_df["dropped_index"] == "none") & (grid_df["baseline_lo"] == 0.02)]
    min_rho_s3 = float(s3_sub["rho_hexmean"].min())
    summary_rows.append({
        "family": "S3 (Compound trigger threshold q: 0.75, 0.90)",
        "min_rho_hexmean": min_rho_s3,
        "min_tau_hexmean": float(s3_sub["tau_hexmean"].min()),
        "min_jaccard": float(s3_sub["top_decile_jaccard"].min()),
        "bucket": classify_bucket(min_rho_s3),
    })

    # 4. Leave-one-out (S4)
    s4_sub = grid_df[grid_df["family"] == "S4_leave_one_out"]
    min_rho_s4 = float(s4_sub["rho_hexmean"].min())
    summary_rows.append({
        "family": "S4 (Leave-one-index-out)",
        "min_rho_hexmean": min_rho_s4,
        "min_tau_hexmean": float(s4_sub["tau_hexmean"].min()),
        "min_jaccard": float(s4_sub["top_decile_jaccard"].min()),
        "bucket": classify_bucket(min_rho_s4),
    })

    # 5. Baseline bounds (S5)
    s5_sub = grid_df[grid_df["family"] == "S5_baseline_bounds"]
    min_rho_s5 = float(s5_sub["rho_hexmean"].min())
    summary_rows.append({
        "family": "S5 (Global baseline bounds: 1/99% to 5/95%)",
        "min_rho_hexmean": min_rho_s5,
        "min_tau_hexmean": float(s5_sub["tau_hexmean"].min()),
        "min_jaccard": float(s5_sub["top_decile_jaccard"].min()),
        "bucket": classify_bucket(min_rho_s5),
    })

    summary_df = pd.DataFrame(summary_rows)

    # Save outputs via results_io
    payload = {
        "n_experiments": len(grid_df),
        "grid": grid_df,
    }
    save_result("sensitivity", payload, cfg, out_dir=results_dir)

    summary_csv_path = Path(results_dir) / "sensitivity_summary.csv"
    summary_df.to_csv(summary_csv_path, index=False)

    print("=" * 80)
    print("  STEP 10 SENSITIVITY AND ROBUSTNESS SUMMARY")
    print("=" * 80)
    print(summary_df.to_string(index=False))
    print("=" * 80)
    log.info(f"Saved sensitivity grid ({len(grid_df)} rows) and summary -> {summary_csv_path}")

    return grid_df, summary_df


def main():
    cfg = yaml.safe_load(open("config.yml"))
    run_sensitivity(cfg)


if __name__ == "__main__":
    main()
