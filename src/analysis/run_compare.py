"""
src/analysis/run_compare.py
───────────────────────────
Step 09: Empirical comparison between v1 and v2 indices.
Avoids merge duplicate column naming bugs by renaming before join.
Calculates:
  - Hex-mean Spearman & Kendall tau (spatial ranking stability)
  - Mean within-month Spearman
  - Top-decile hex overlap (Jaccard)
  - Mean SSI shift (v2 - v1)
  - 20 hexes with largest rank change
  - Two-way additive variance decomposition
Saves artifacts via save_result("compare_<city>", ...).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
import yaml

from src.analysis.diagnostics import variance_shares
from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("run_compare")


def compare_city(city: str, cfg: dict[str, Any]) -> dict[str, Any]:
    v2_cfg = cfg.get("v2", {})
    v1_dir = Path(v2_cfg.get("paths", {}).get("v1", "data/h3_panel/final"))
    v2_dir = Path(v2_cfg.get("paths", {}).get("v2", "data/h3_panel/v2"))
    results_dir = v2_cfg.get("paths", {}).get("results", "results")

    # Fallback to archive/v1 if final is unpopulated
    v1_path = v1_dir / f"{city}.parquet"
    if not v1_path.exists():
        v1_path = Path("archive/v1/final") / f"{city}.parquet"

    v2_path = v2_dir / f"{city}.parquet"

    if not v1_path.exists():
        raise FileNotFoundError(f"v1 panel missing: {v1_path}")
    if not v2_path.exists():
        raise FileNotFoundError(f"v2 panel missing: {v2_path}")

    # Explicit column selection and renaming BEFORE merge to prevent duplicate suffix bugs
    v1_df = pd.read_parquet(v1_path)[["h3_index", "date", "ssi_value"]].rename(columns={"ssi_value": "ssi_v1"})
    v2_df = pd.read_parquet(v2_path)

    v1_df["date"] = pd.to_datetime(v1_df["date"]).dt.strftime("%Y-%m-01")
    v2_df["date"] = pd.to_datetime(v2_df["date"]).dt.strftime("%Y-%m-01")

    # One-to-one merge
    m = v2_df.merge(v1_df, on=["h3_index", "date"], how="inner", validate="one_to_one")
    assert not any(c.endswith(("_x", "_y")) for c in m.columns), "Found unexpected _x/_y columns after merge"

    if len(m) != len(v2_df):
        log.warning(f"Merge row count ({len(m):,}) differs from v2 row count ({len(v2_df):,})")

    # 1. Spatial ranking agreement on hex-means
    hex_means = m.groupby("h3_index")[["ssi_v1", "ssi_v2"]].mean()
    rho_hex, _ = spearmanr(hex_means["ssi_v1"], hex_means["ssi_v2"])
    tau_hex, _ = kendalltau(hex_means["ssi_v1"], hex_means["ssi_v2"])

    # 2. Within-month Spearman rank correlation
    wm_rhos = []
    for _, g in m.groupby("date"):
        if g["ssi_v1"].nunique() > 1 and g["ssi_v2"].nunique() > 1:
            r, _ = spearmanr(g["ssi_v1"], g["ssi_v2"])
            wm_rhos.append(r)
    mean_wm_rho = float(np.nanmean(wm_rhos)) if wm_rhos else np.nan

    # 3. Pooled Spearman (with caveat)
    rho_pooled, _ = spearmanr(m["ssi_v1"], m["ssi_v2"])

    # 4. Top-decile hex overlap (Jaccard)
    k = max(1, int(0.10 * len(hex_means)))
    top_v1 = set(hex_means["ssi_v1"].nlargest(k).index)
    top_v2 = set(hex_means["ssi_v2"].nlargest(k).index)
    jaccard = float(len(top_v1 & top_v2) / len(top_v1 | top_v2))

    # 5. Mean SSI shift (v2 - v1) and monthly profile
    m["shift"] = m["ssi_v2"] - m["ssi_v1"]
    mean_shift = float(m["shift"].mean())
    monthly_shift = m.groupby("date")["shift"].mean().round(4).to_dict()

    # 6. Largest rank changes (top 20 hexes)
    hex_means["rank_v1"] = hex_means["ssi_v1"].rank(ascending=False)
    hex_means["rank_v2"] = hex_means["ssi_v2"].rank(ascending=False)
    hex_means["rank_diff"] = (hex_means["rank_v1"] - hex_means["rank_v2"]).abs()
    top20_hexes = hex_means.nlargest(20, "rank_diff").reset_index()

    # Merge in average raw driver values for these 20 hexes
    raw_cols = [c for c in ["heat_raw", "water_raw", "veg_raw", "pollution_raw", "exposure_raw"] if c in m.columns]
    hex_raw_means = m.groupby("h3_index")[raw_cols].mean().reset_index()
    top20_table = top20_hexes.merge(hex_raw_means, on="h3_index", how="left")

    # 7. Variance shares for v1 vs v2
    var_v1 = variance_shares(m, "ssi_v1")
    var_v2 = variance_shares(m, "ssi_v2")

    payload = {
        "city": city,
        "n_obs": len(m),
        "n_hexes": len(hex_means),
        "rho_hexmean": round(float(rho_hex), 4),
        "tau_hexmean": round(float(tau_hex), 4),
        "mean_within_month_rho": round(mean_wm_rho, 4),
        "pooled_rho_with_caveat": round(float(rho_pooled), 4),
        "top_decile_jaccard": round(jaccard, 4),
        "mean_ssi_shift": round(mean_shift, 4),
        "monthly_shift_profile": monthly_shift,
        "variance_v1": var_v1,
        "variance_v2": var_v2,
        "top20_rank_changes": top20_table,
    }

    out_file = save_result(f"compare_{city}", payload, cfg, out_dir=results_dir)

    print("=" * 75)
    print(f"  STEP 09 COMPARISON REPORT: {city.upper()}")
    print("=" * 75)
    print(f"  Spatial rank correlation (Hex-Mean Spearman ρ) : {rho_hex:.4f}")
    print(f"  Spatial rank correlation (Hex-Mean Kendall τ)  : {tau_hex:.4f}")
    print(f"  Mean within-month Spearman ρ                   : {mean_wm_rho:.4f}")
    print(f"  Top-10% hex overlap (Jaccard similarity)       : {jaccard:.4f}")
    print(f"  Mean SSI Shift (v2 - v1)                       : {mean_shift:+.4f}")
    print(f"  v1 Variance Shares (Month / Hex / Res)         : {var_v1['between_month']*100:.1f}% / {var_v1['between_hex']*100:.1f}% / {var_v1['residual']*100:.1f}%")
    print(f"  v2 Variance Shares (Month / Hex / Res)         : {var_v2['between_month']*100:.1f}% / {var_v2['between_hex']*100:.1f}% / {var_v2['residual']*100:.1f}%")
    print("=" * 75)
    log.info(f"Saved comparison result -> {out_file}")

    return payload


def main():
    parser = argparse.ArgumentParser(description="Run v1 vs v2 comparison.")
    parser.add_argument("--city", default="all", help="City name or 'all'")
    args = parser.parse_args()

    cfg = yaml.safe_load(open("config.yml"))
    v2_cfg = cfg.get("v2", {})
    all_cities = v2_cfg.get("cities", ["mumbai", "coimbatore"])

    target_cities = all_cities if args.city == "all" else [args.city]
    for c in target_cities:
        compare_city(c, cfg)


if __name__ == "__main__":
    main()
