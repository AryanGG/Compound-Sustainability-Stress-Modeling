#!/usr/bin/env python3
"""
run_v2.py
─────────
Canonical CLI pipeline runner for SSI v2:
  --stage fit:
      Fits global baseline, weighting schemes, compound interaction thresholds,
      and risk band cuts ONCE on pooled reference cities.
      Saves frozen parameters to results/fit_parameters.json with provenance metadata.

  --stage score --city <name|all>:
      Scores cities using frozen parameters without per-city refitting.
      Writes data/h3_panel/v2/{city}.parquet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
import yaml

from src.utils.logger import get_logger
from src.utils.results_io import save_result
from src.v2.indices import fit_baseline, apply_baseline, IDX_COLS
from src.v2.ssi import fit_compound, apply_ssi, fit_cuts, assign_bands
from src.v2.weighting import fit_all_weights

log = get_logger("run_v2")


def stage_fit(cfg: dict[str, Any]) -> dict[str, Any]:
    v2_cfg = cfg.get("v2", {})
    ref_cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])
    raw_dir = Path(v2_cfg.get("paths", {}).get("raw", "data/h3_panel/v2_raw"))

    log.info(f"=== STAGE FIT: Fitting pooled parameters on reference cities {ref_cities} ===")

    # 1. Load and concatenate reference raw panels
    raw_dfs = []
    for city in ref_cities:
        p = raw_dir / f"{city}.parquet"
        if not p.exists():
            raise FileNotFoundError(f"Reference raw panel not found: {p}")
        df = pd.read_parquet(p)
        raw_dfs.append(df)

    pooled_raw = pd.concat(raw_dfs, ignore_index=True)
    log.info(f"Loaded {len(pooled_raw):,} pooled observations across {len(ref_cities)} reference cities")

    # 2. Fit baseline normalization
    lo_q = v2_cfg.get("baseline", {}).get("lo_q", 0.02)
    hi_q = v2_cfg.get("baseline", {}).get("hi_q", 0.98)
    baseline_params = fit_baseline(pooled_raw, lo=lo_q, hi=hi_q)

    # Apply baseline to pooled data to obtain IDX_COLS
    pooled_norm = apply_baseline(pooled_raw, baseline_params)

    # 3. Fit four weighting schemes
    weights_schemes, pc1_var = fit_all_weights(pooled_norm[IDX_COLS])
    primary_scheme = v2_cfg.get("primary_scheme", "equal")
    primary_weights = weights_schemes[primary_scheme]

    # 4. Fit compound thresholds on primary pair and q
    compound_cfg = v2_cfg.get("compound", {})
    compound_pair = tuple(compound_cfg.get("pair", ["heat_v2", "pollution_v2"]))
    compound_q = float(compound_cfg.get("q", 0.90))
    gamma = float(compound_cfg.get("gamma", 0.30))

    compound_thresholds = fit_compound(pooled_norm, pair=compound_pair, q=compound_q)

    # Score reference panel to obtain reference SSI distribution for band cuts
    ref_scored = apply_ssi(pooled_norm, primary_weights, compound_thresholds, gamma=gamma)

    # 5. Fit band cuts
    band_quantiles = v2_cfg.get("bands", {}).get("quantiles", [0.25, 0.50, 0.75])
    band_labels = v2_cfg.get("bands", {}).get("labels", ["Low", "Moderate", "High", "Extreme"])
    band_cuts = fit_cuts(ref_scored["ssi_v2"], qs=band_quantiles)

    # Assemble fit_parameters payload
    fit_payload = {
        "reference_cities": ref_cities,
        "n_reference_obs": len(pooled_raw),
        "baseline": baseline_params,
        "weights": {s: w.to_dict() for s, w in weights_schemes.items()},
        "primary_scheme": primary_scheme,
        "primary_weights": primary_weights.to_dict(),
        "pc1_explained": round(pc1_var, 4),
        "compound": {
            "pair": list(compound_pair),
            "q": compound_q,
            "gamma": gamma,
            "thresholds": compound_thresholds,
        },
        "band_cuts": band_cuts,
        "band_labels": list(band_labels),
    }

    # Save via results_io
    results_dir = v2_cfg.get("paths", {}).get("results", "results")
    out_file = save_result("fit_parameters", fit_payload, cfg, out_dir=results_dir)
    log.info(f"Stage fit complete. Saved frozen parameters -> {out_file}")
    return fit_payload


def stage_score(city_arg: str, cfg: dict[str, Any]) -> None:
    v2_cfg = cfg.get("v2", {})
    all_cities = v2_cfg.get("cities", ["mumbai", "coimbatore"])
    target_cities = all_cities if city_arg == "all" else [city_arg]

    results_dir = Path(v2_cfg.get("paths", {}).get("results", "results"))
    fit_param_file = results_dir / "fit_parameters.json"
    if not fit_param_file.exists():
        raise FileNotFoundError(f"Fit parameters not found: {fit_param_file}. Run --stage fit first.")

    with open(fit_param_file) as f:
        params_meta = json.load(f)

    # Extract clean parameters
    params = {k: v for k, v in params_meta.items() if not k.startswith("_")}
    baseline_params = params["baseline"]
    weights_dict = {s: pd.Series(w) for s, w in params["weights"].items()}
    primary_scheme = params["primary_scheme"]
    primary_weights = weights_dict[primary_scheme]

    compound_cfg = params["compound"]
    compound_thr = compound_cfg["thresholds"]
    gamma = compound_cfg["gamma"]
    band_cuts = params["band_cuts"]
    band_labels = params["band_labels"]

    raw_dir = Path(v2_cfg.get("paths", {}).get("raw", "data/h3_panel/v2_raw"))
    out_dir = Path(v2_cfg.get("paths", {}).get("v2", "data/h3_panel/v2"))
    out_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"=== STAGE SCORE: Scoring {target_cities} with frozen parameters ===")

    for city in target_cities:
        raw_file = raw_dir / f"{city}.parquet"
        if not raw_file.exists():
            log.error(f"Raw panel for {city} missing at {raw_file}")
            continue

        raw_df = pd.read_parquet(raw_file)

        # 1. Apply frozen baseline normalization
        norm_df = apply_baseline(raw_df, baseline_params)

        # 2. Compute linear combinations for each sensitivity scheme
        for scheme_name, w_series in weights_dict.items():
            norm_df[f"ssi_lin_{scheme_name}"] = (norm_df[list(w_series.index)] * w_series).sum(axis=1)

        # 3. Apply primary SSI formulation (linear base + smooth compound interaction)
        scored_df = apply_ssi(norm_df, primary_weights, compound_thr, gamma=gamma)

        # 4. Assign relative risk bands using frozen cuts
        scored_df["ssi_band_v2"] = assign_bands(scored_df["ssi_v2"], band_cuts, labels=band_labels)

        # 5. Validate integrity
        n_nan = scored_df["ssi_v2"].isna().sum()
        assert n_nan == 0, f"Found {n_nan} NaNs in ssi_v2 for {city}"

        # Write output parquet
        out_path = out_dir / f"{city}.parquet"
        scored_df.to_parquet(out_path, index=False)
        print(f"[score] {city}: shape={scored_df.shape}, NaN ssi_v2 = {n_nan}")
        log.info(f"Scored {city}: rows={len(scored_df):,}, mean_ssi={scored_df['ssi_v2'].mean():.4f} -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="SSI v2 canonical execution pipeline.")
    parser.add_argument("--stage", required=True, choices=["fit", "score", "all"], help="Pipeline stage")
    parser.add_argument("--city", default="all", help="City name or 'all' for score stage")
    args = parser.parse_args()

    cfg = yaml.safe_load(open("config.yml"))

    if args.stage in ("fit", "all"):
        stage_fit(cfg)

    if args.stage in ("score", "all"):
        stage_score(args.city, cfg)


if __name__ == "__main__":
    main()
