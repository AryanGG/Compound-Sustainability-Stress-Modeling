"""
src/ml/policy_playbook.py
─────────────────────────
Step 06: Statutory Municipal Policy Playbook Mapping.

Automates the translation of machine-learning early-warning probabilities into
statutory government emergency response playbooks:
  1. Indian Meteorological Department (IMD) Heat Action Plan (HAP)
  2. Commission for Air Quality Management (CAQM) / CPCB Graded Response Action Plan (GRAP)
  3. Power DISCOM & State Water Board Emergency Resource Staging
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("policy_playbook")

STATUTORY_DIRECTIVES = {
    "heatwave": {
        "RED": {
            "tier_label": "Severe Heatwave Emergency (HAP Stage III)",
            "statutory_authority": "Municipal Corporation & District Disaster Management Authority (DDMA)",
            "mandatory_directives": [
                "Mandatory cessation of outdoor construction and manual labor between 11:00 AM and 4:00 PM",
                "Dispatch dedicated fleet of mobile drinking water tankers to high-density informal settlements and transit hubs",
                "Activate designated public transit halls, community centers, and libraries as air-conditioned emergency cooling shelters",
                "Pre-stock government casualty hospital wards with oral rehydration solutions (ORS), IV saline, and ice cooling packs",
                "Deploy high-pressure water misting cannons along congested commercial and traffic corridors",
            ],
        },
        "ORANGE": {
            "tier_label": "Heat Alert Precautionary Watch (HAP Stage II)",
            "statutory_authority": "Municipal Health & Engineering Departments",
            "mandatory_directives": [
                "Issue public heat advisory via SMS and local radio targeting gig workers, traffic police, and outdoor vendors",
                "Ensure shade canopies are erected at major bus stops and transit interchanges",
                "Conduct night-time road misting to accelerate urban canyon nocturnal sensible heat dissipation",
                "Put municipal ambulance services on standby for heat-exhaustion dispatch calls",
            ],
        },
    },
    "smog": {
        "RED": {
            "tier_label": "Severe Atmospheric Smog Crisis (GRAP Stage IV)",
            "statutory_authority": "Commission for Air Quality Management (CAQM) & State Pollution Control Board (SPCB)",
            "mandatory_directives": [
                "Immediate statutory ban on entry of non-BS-VI diesel commercial trucks (except essential goods)",
                "Complete moratorium on all construction, excavation, demolition, and road-cutting dust activities",
                "Mandatory 50% work-from-home mandate for all government and commercial corporate offices",
                "Temporary transition of primary educational institutions to online remote learning",
                "Immediate shutdown of non-emergency industrial diesel generator sets",
            ],
        },
        "ORANGE": {
            "tier_label": "Very Poor Air Quality Episode (GRAP Stage III)",
            "statutory_authority": "Municipal Corporation & Traffic Police",
            "mandatory_directives": [
                "Intensify mechanized vacuum sweeping and water sprinkling on arterial roads twice daily",
                "Impose strict speed restrictions and anti-idling enforcement at congested traffic choke-points",
                "Prohibit burning of municipal solid waste, leaf litter, and biomass with spot financial penalties",
                "Halt stone crushers, brick kilns, and ready-mix concrete batching plants within municipal limits",
            ],
        },
    },
    "compound": {
        "RED": {
            "tier_label": "Compound Climate-Energy-Hydrological Shock",
            "statutory_authority": "State Power DISCOM & State Water Supply Board",
            "mandatory_directives": [
                "Power distribution companies (DISCOMs) pre-order peaking capacity on the Indian Energy Exchange (IEX) 30 days ahead",
                "State load dispatch centers (SLDC) reschedule thermal/hydro generation reserves to prevent grid brownouts",
                "Municipal water boards place strict moratoriums on commercial and industrial groundwater extraction",
                "Activate emergency inter-basin raw water transfers to protect municipal drinking water reservoirs",
            ],
        },
        "ORANGE": {
            "tier_label": "Compound Hazard Early Advisory",
            "statutory_authority": "Municipal Utility Coordination Committee",
            "mandatory_directives": [
                "Issue water conservation advisories to high-consumption commercial complexes and hotels",
                "Audit transformer substation cooling systems in wards flagged for high compound thermal-demand stress",
            ],
        },
    },
}


def classify_alert_tier(prob: float) -> str:
    """Classify probability into standard emergency alert tier."""
    if prob >= 0.75:
        return "RED"
    elif prob >= 0.50:
        return "ORANGE"
    elif prob >= 0.30:
        return "YELLOW"
    else:
        return "GREEN"


def build_city_playbook_schedule(
    city: str,
    predictions_dir: str | Path = "data/h3_panel/ml_predictions",
) -> dict[str, Any]:
    """
    Process 2022 test predictions and generate monthly statutory emergency alert timelines.
    """
    pred_path = Path(predictions_dir) / f"{city}_2022_predictions.parquet"
    if not pred_path.exists():
        raise FileNotFoundError(f"Predictions not found for {city}: {pred_path}")

    df = pd.read_parquet(pred_path)

    # Classify alert tiers for each event
    for ev in ["heatwave", "smog", "compound"]:
        col = f"prob_{ev}"
        if col in df.columns:
            df[f"tier_{ev}"] = df[col].apply(classify_alert_tier)

    # Monthly breakdown of alerts
    monthly_schedule = {}
    for dt, group in df.groupby("date"):
        total_hexes = len(group)
        month_stats = {
            "total_hexes": total_hexes,
            "heatwave_red_alerts": int((group["tier_heatwave"] == "RED").sum()) if "tier_heatwave" in group else 0,
            "heatwave_orange_alerts": int((group["tier_heatwave"] == "ORANGE").sum()) if "tier_heatwave" in group else 0,
            "smog_red_alerts": int((group["tier_smog"] == "RED").sum()) if "tier_smog" in group else 0,
            "smog_orange_alerts": int((group["tier_smog"] == "ORANGE").sum()) if "tier_smog" in group else 0,
            "compound_red_alerts": int((group["tier_compound"] == "RED").sum()) if "tier_compound" in group else 0,
        }
        monthly_schedule[dt] = month_stats

    # Extract sample high-priority emergency intervention wards
    high_priority_hexes = []
    # Find up to 5 top critical hexes in 2022
    if "prob_heatwave" in df.columns:
        top_hw_hexes = df.sort_values("prob_heatwave", ascending=False).drop_duplicates(subset=["h3_index"]).head(3)
        for _, row in top_hw_hexes.iterrows():
            tier = classify_alert_tier(row["prob_heatwave"])
            if tier in ["RED", "ORANGE"]:
                directives = STATUTORY_DIRECTIVES["heatwave"][tier]["mandatory_directives"][:3]
                high_priority_hexes.append({
                    "h3_index": row["h3_index"],
                    "peak_date": row["date"],
                    "hazard_type": "Heatwave Shock",
                    "predicted_prob": float(row["prob_heatwave"]),
                    "alert_tier": tier,
                    "statutory_playbook": STATUTORY_DIRECTIVES["heatwave"][tier]["tier_label"],
                    "priority_interventions": directives,
                })

    if "prob_smog" in df.columns:
        top_smog_hexes = df.sort_values("prob_smog", ascending=False).drop_duplicates(subset=["h3_index"]).head(3)
        for _, row in top_smog_hexes.iterrows():
            tier = classify_alert_tier(row["prob_smog"])
            if tier in ["RED", "ORANGE"]:
                directives = STATUTORY_DIRECTIVES["smog"][tier]["mandatory_directives"][:3]
                high_priority_hexes.append({
                    "h3_index": row["h3_index"],
                    "peak_date": row["date"],
                    "hazard_type": "Hazardous Smog Inversion",
                    "predicted_prob": float(row["prob_smog"]),
                    "alert_tier": tier,
                    "statutory_playbook": STATUTORY_DIRECTIVES["smog"][tier]["tier_label"],
                    "priority_interventions": directives,
                })

    return {
        "city": city,
        "monthly_alert_timeline": monthly_schedule,
        "sample_priority_ward_interventions": high_priority_hexes,
        "statutory_frameworks_invoked": [
            "Indian Meteorological Department (IMD) Heat Action Plan",
            "Commission for Air Quality Management (CAQM) / CPCB GRAP Stage I-IV",
            "State Disaster Management Authority (SDMA) / Power Grid DISCOM Protocol",
        ],
    }


def run_policy_playbook_pipeline(
    cities: list[str] | None = None,
    predictions_dir: str | Path = "data/h3_panel/ml_predictions",
    report_path: str | Path = "reports/ml_policy_playbook_summary.json",
) -> dict[str, Any]:
    """
    Execute Step 06 municipal policy playbook generation across all study cities.
    """
    if cities is None:
        cities = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

    all_playbooks: dict[str, Any] = {}
    for c in cities:
        log.info(f"Generating municipal emergency playbook for {c}...")
        try:
            playbook = build_city_playbook_schedule(c, predictions_dir=predictions_dir)
            all_playbooks[c] = playbook
        except Exception as exc:
            log.warning(f"Could not build playbook for {c}: {exc}")

    # Save summary report in reports/
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(all_playbooks, fh, indent=2)

    # Maintain provenance-tracked results in results/
    try:
        save_result(
            "ml_policy_playbook_summary",
            all_playbooks,
            config={"step": "06_policy_playbook", "seed": 20260101},
        )
        log.info("Saved provenance-tracked result -> results/ml_policy_playbook_summary.json")
    except Exception as exc:
        log.warning(f"Failed to save to results/: {exc}")

    log.info(f"Policy playbook summary saved to {report_path}")
    return all_playbooks


if __name__ == "__main__":
    playbooks = run_policy_playbook_pipeline()
    print("\n=== Step 06 Statutory Municipal Policy Playbook Summary ===")
    for city, pb in playbooks.items():
        timeline = pb["monthly_alert_timeline"]
        # Find month with highest heatwave red alerts
        max_hw = max(timeline.items(), key=lambda x: x[1].get("heatwave_red_alerts", 0))
        max_sm = max(timeline.items(), key=lambda x: x[1].get("smog_red_alerts", 0))
        print(
            f"{city:12s} | Peak Heatwave Alert: {max_hw[0]} ({max_hw[1]['heatwave_red_alerts']} Red Hexes) | "
            f"Peak Smog Alert: {max_sm[0]} ({max_sm[1]['smog_red_alerts']} Red Hexes)"
        )
