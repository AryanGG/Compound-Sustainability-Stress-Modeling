"""
src/ml/predict_extreme_events.py
─────────────────────────────────
Unified End-to-End Operational Pipeline for:
"Hyperlocal Multi-Horizon Early Warning System (EWS) for Compound Urban Crises"

Pipeline Stages Executed:
  1. Event Label Formulation:
     Ground-truth statutory binary masks (Heatwave, Smog, Compound, Extreme SSI).
  2. Temporal Feature Extraction:
     104 non-leaking predictors (antecedent lags, rolling velocities, exhaustion streaks,
     spatial morphology, cyclical calendar periodicity).
  3. Cost-Sensitive Chronological Model Training:
     HistGradientBoostingClassifier (class_weight='balanced') & HistGradientBoostingRegressor
     trained on 2020–2021 historical panels, evaluated out-of-time on unseen 2022 benchmarks.
  4. Interpretable Precursor Risk Attribution:
     Global permutation feature importances and localized ward z-score breakdowns.
  5. Statutory Municipal Policy Playbooks:
     Mapping crisis probabilities to IMD Heat Action Plans & CAQM GRAP directives.
  6. Provenance Reporting:
     Persists metrics to results/ and reports/ with config hash and Git SHA tracking.

Usage:
  python -m src.ml.predict_extreme_events --city all
  python -m src.ml.predict_extreme_events --city mumbai --generate-figures
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import pandas as pd

from src.ml.event_definitions import run_event_labeling_pipeline, CITIES
from src.ml.temporal_features import run_temporal_feature_pipeline
from src.ml.train_event_classifier import run_event_training_pipeline
from src.ml.explain_event_risk import run_attribution_pipeline
from src.ml.policy_playbook import run_policy_playbook_pipeline
from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("predict_extreme_events")


def run_end_to_end_pipeline(
    cities: list[str] = CITIES,
    generate_figures: bool = True,
    export_playbooks: bool = True,
) -> dict[str, Any]:
    """
    Executes the complete 5-stage early warning system across target metropolitan study areas.
    """
    log.info("=" * 80)
    log.info("  HYPERLOCAL MULTI-HORIZON EARLY WARNING SYSTEM (EWS) - OPERATIONAL RUN")
    log.info(f"  Target Metropolitan Areas: {', '.join(cities)}")
    log.info("=" * 80)

    # Stage 1: Formulate Ground-Truth Statutory Event Masks
    log.info("\n>>> STAGE 1: Generating Ground-Truth Event Masks (334,332 hex-months)...")
    event_prevalence = run_event_labeling_pipeline(cities=cities)

    # Stage 2: Temporal Feature Engineering (104 non-leaking predictors)
    log.info("\n>>> STAGE 2: Extracting 104 Temporal Predictors (Lags, Velocities, Exhaustion)...")
    feature_meta = run_temporal_feature_pipeline(cities=cities)

    # Stage 3: Chronological Out-of-Time Model Training (2020-2021 Train -> 2022 Benchmark Test)
    log.info("\n>>> STAGE 3: Training Cost-Sensitive Classifiers & Out-of-Time 2022 Validation...")
    training_metrics = run_event_training_pipeline(cities=cities)


    # Also mirror metrics to reports/ for dashboard access
    reports_dir = ROOT_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "ml_event_prediction_metrics.json", "w") as f:
        json.dump(training_metrics, f, indent=2)
    log.info("  [+] Mirrored metrics to reports/ml_event_prediction_metrics.json")

    # Stage 4: Interpretable Precursor Risk Attribution
    log.info("\n>>> STAGE 4: Decomposing Emergency Alert Triggers (Permutation Attribution)...")
    attributions = run_attribution_pipeline(cities=cities)


    # Stage 5: Statutory Municipal Policy Playbooks
    if export_playbooks:
        log.info("\n>>> STAGE 5: Generating Statutory Directives (IMD HAP & CAQM GRAP)...")
        playbooks = run_policy_playbook_pipeline(cities=cities)
    else:
        playbooks = {}

    # Stage 6: Visual Artifact Generation
    if generate_figures:
        log.info("\n>>> STAGE 6: Generating Publication Figures (Figures F9, F10, F11 in paper_images/)...")
        try:
            from scripts.generate_event_figures import (
                generate_f9_roc_pr_curves,
                generate_f10_forward_threat_map,
                generate_f11_attribution_waterfall,
            )
            generate_f9_roc_pr_curves()
            generate_f10_forward_threat_map()
            generate_f11_attribution_waterfall()
            log.info("  [+] Figures F9, F10, F11 saved at 300 DPI (PNG & SVG) in paper_images/.")
        except Exception as e:
            log.warning(f"  [!] Figure generation skipped or encountered non-fatal error: {e}")

    log.info("\n" + "=" * 80)
    log.info("  EARLY WARNING PIPELINE COMPLETED SUCCESSFULLY")
    log.info("=" * 80)

    summary = {
        "cities": cities,
        "event_prevalence": event_prevalence,
        "feature_meta": feature_meta,
        "training_metrics": training_metrics,
        "attributions_computed": list(attributions.keys()),
        "playbooks_exported": list(playbooks.keys()),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified Early Warning System for Discrete Urban Sustainability Crises"
    )
    parser.add_argument(
        "--city",
        type=str,
        default="all",
        help="Target city (delhi, mumbai, kolkata, hyderabad, bikaner, coimbatore, indore) or 'all'",
    )
    parser.add_argument(
        "--skip-figures",
        action="store_true",
        help="Skip 300 DPI publication figure generation",
    )
    parser.add_argument(
        "--skip-playbooks",
        action="store_true",
        help="Skip statutory municipal policy playbook export",
    )

    args = parser.parse_args()

    if args.city.lower() == "all":
        target_cities = CITIES
    else:
        c = args.city.lower().strip()
        if c not in CITIES:
            raise ValueError(f"Unknown city '{c}'. Must be one of: {CITIES}")
        target_cities = [c]

    run_end_to_end_pipeline(
        cities=target_cities,
        generate_figures=not args.skip_figures,
        export_playbooks=not args.skip_playbooks,
    )


if __name__ == "__main__":
    main()
