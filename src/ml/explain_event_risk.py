"""
src/ml/explain_event_risk.py
────────────────────────────
Step 05: Interpretable Risk Attribution & Precursor Decomposition.

Computes global permutation importances and decomposes localized alerts into
physical, human-interpretable precursor percentages for every flagged H3 hexagon.
Translates statistical feature splits into physical mechanisms:
  - Soil moisture deficit
  - Built-up impervious concrete inertia
  - Thermal acceleration momentum
  - Atmospheric inversion & wind stagnation
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance

from src.ml.temporal_features import get_feature_column_names
from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("explain_event_risk")

PHYSICAL_EXPLANATIONS = {
    "temp_mean_c": "Regional macro ambient air temperature surge",
    "temp_mean_c_lag1": "Elevated antecedent air temperature baseline",
    "temp_mean_c_lag2": "Persistent multi-week macro heat accumulation",
    "lst_c": "Satellite radiometric surface temperature anomaly",
    "lst_c_lag1": "Prior-month residual urban heat island retention",
    "lst_c_lag2": "Multi-week surface thermal mass retention",
    "lst_velocity_1m": "Accelerated rate of ground surface heating",
    "dewpoint_mean_c": "High ambient atmospheric moisture / heat index trap",
    "dewpoint_mean_c_lag1": "Antecedent humidity trapping nocturnal sensible heat",
    "dewpoint_mean_c_lag2": "Sustained high latent heat capacity in boundary layer",
    "precip_sum_mm": "Seasonal rainfall deficit reducing surface evaporative cooling",
    "precip_sum_mm_lag1": "Prior-month cumulative rainfall deficit",
    "soil_moisture": "Severe soil moisture depletion preventing evaporative cooling",
    "soil_moisture_lag1": "Antecedent soil drying limiting natural cooling buffering",
    "soil_moisture_drawdown_1m": "Rapid soil moisture depletion velocity",
    "pm25": "Particulate matter concentration exceeding statutory crisis limits",
    "pm25_lag1": "Prior-month particulate buildup in stagnant boundary layer",
    "pm25_surge_1m": "Rapid atmospheric particulate surge velocity",
    "pm25_roll3_mean": "Cumulative 3-month prolonged toxic aerosol burden",
    "ndvi": "Low photosynthetic canopy health and reduced vegetative transpiration",
    "ndvi_browning_1m": "Accelerated urban vegetation browning / canopy die-back",
    "built_up_fraction": "High impervious concrete cover storing solar radiation",
    "building_density": "Dense urban street canyon geometry reducing wind ventilation",
    "road_density_km_km2": "Asphalt transport corridor density absorbing daytime solar flux",
    "building_fp_fraction": "Direct structural built footprint trapping radiant heat",
    "green_space_fraction": "Absence of mitigating neighborhood pocket parks and tree canopy",
    "stress_exhaustion_streak": "Prolonged multi-month stress exhausting neighborhood ecological resilience",
    "precursor_heat_water": "Simultaneous co-occurrence of thermal surge and soil moisture deficit",
    "precursor_heat_smog": "Compound trapping of particulate pollution under thermal inversion dome",
    "sin_month": "Cyclical solar / pre-monsoon summer seasonal alignment",
    "cos_month": "Cyclical winter atmospheric inversion seasonal alignment",
}


def compute_global_feature_importances(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    feature_names: list[str],
    n_top: int = 10,
    random_state: int = 42,
) -> dict[str, float]:
    """
    Fit a fast classifier and compute permutation importance on a sample.
    """
    if y_train.sum() == 0 or y_train.sum() == len(y_train):
        return {}

    clf = HistGradientBoostingClassifier(class_weight="balanced", random_state=random_state, max_iter=50)
    clf.fit(X_train, y_train)

    sample_size = min(len(X_train), 1500)
    idx_sample = np.random.RandomState(random_state).choice(len(X_train), sample_size, replace=False)
    X_sub = X_train.iloc[idx_sample]
    y_sub = y_train.iloc[idx_sample]

    perm = permutation_importance(clf, X_sub, y_sub, n_repeats=3, random_state=random_state, scoring="roc_auc")
    importances = perm.importances_mean
    top_indices = np.argsort(importances)[::-1][:n_top]

    return {
        feature_names[i]: round(float(importances[i]), 4)
        for i in top_indices
        if importances[i] > 0.0001
    }


def explain_single_hexagon_alert(
    hex_features: pd.Series,
    city_means: pd.Series,
    city_stds: pd.Series,
    global_weights: dict[str, float],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Decompose a single high-risk hexagon's alert into top-k physical precursor contributions.
    """
    scores = {}
    for feat, weight in global_weights.items():
        if feat in hex_features and feat in city_means and feat in city_stds:
            val = hex_features[feat]
            mean_val = city_means[feat]
            std_val = city_stds[feat] if city_stds[feat] > 1e-6 else 1.0
            z_score = abs(val - mean_val) / std_val
            scores[feat] = weight * (1.0 + z_score)

    total_score = sum(scores.values()) if scores else 1.0
    sorted_feats = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    attributions = []
    for feat, sc in sorted_feats:
        pct = round(float(sc / total_score * 100.0), 1)
        meaning = PHYSICAL_EXPLANATIONS.get(feat, f"Precursor driver: {feat}")
        attributions.append({
            "feature": feat,
            "contribution_pct": pct,
            "physical_meaning": meaning,
            "observed_value": round(float(hex_features[feat]), 4),
        })

    return attributions


def run_attribution_pipeline(
    cities: list[str] | None = None,
    features_dir: str | Path = "data/h3_panel/ml_features",
    predictions_dir: str | Path = "data/h3_panel/ml_predictions",
    report_path: str | Path = "reports/ml_event_attributions_summary.json",
    split_date: str = "2022-01-01",
) -> dict[str, Any]:
    """
    Execute Step 05 risk attribution across all cities and produce sample explanation cards.
    """
    if cities is None:
        cities = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

    all_attributions: dict[str, Any] = {}

    for c in cities:
        log.info(f"Extracting precursor risk attributions for {c}...")
        feat_path = Path(features_dir) / f"{c}.parquet"
        pred_path = Path(predictions_dir) / f"{c}_2022_predictions.parquet"

        if not feat_path.exists() or not pred_path.exists():
            continue

        df_feat = pd.read_parquet(feat_path)
        df_pred = pd.read_parquet(pred_path)

        valid_mask = df_feat["temp_mean_c_lag2"].notna() & df_feat["target_event_heatwave_1m"].notna()
        df_valid = df_feat.loc[valid_mask].copy().reset_index(drop=True)

        features = get_feature_column_names(df_valid)
        numeric_features = [f for f in features if np.issubdtype(df_valid[f].dtype, np.number)]

        train_mask = df_valid["date"] < split_date
        X_train = df_valid.loc[train_mask, numeric_features]

        city_means = X_train.mean()
        city_stds = X_train.std()

        # Compute global feature importances for heatwave and smog
        global_heat_imp = compute_global_feature_importances(
            X_train, df_valid.loc[train_mask, "target_event_heatwave_1m"].astype(int), numeric_features
        )
        global_smog_imp = compute_global_feature_importances(
            X_train, df_valid.loc[train_mask, "target_event_smog_1m"].astype(int), numeric_features
        )

        # Decompose sample alerted hexagons from 2022 test set
        test_feat = df_valid.loc[df_valid["date"] >= split_date].copy().reset_index(drop=True)
        # Find high-probability heatwave alerts in 2022
        heat_alerts = df_pred[df_pred["prob_heatwave"] >= 0.70]
        sample_heat_explanations = []
        if len(heat_alerts) > 0 and global_heat_imp:
            sample_indices = heat_alerts.index[:5]
            for idx in sample_indices:
                row_pred = df_pred.loc[idx]
                row_feat = test_feat.loc[idx]
                top_precursors = explain_single_hexagon_alert(row_feat, city_means, city_stds, global_heat_imp)
                sample_heat_explanations.append({
                    "h3_index": row_pred["h3_index"],
                    "date": row_pred["date"],
                    "event": "Heatwave Shock",
                    "predicted_probability": float(row_pred["prob_heatwave"]),
                    "alert_tier": "RED" if row_pred["prob_heatwave"] >= 0.75 else "ORANGE",
                    "precursor_breakdown": top_precursors,
                })

        # Find high-probability smog alerts in 2022
        smog_alerts = df_pred[df_pred["prob_smog"] >= 0.70]
        sample_smog_explanations = []
        if len(smog_alerts) > 0 and global_smog_imp:
            sample_indices = smog_alerts.index[:5]
            for idx in sample_indices:
                row_pred = df_pred.loc[idx]
                row_feat = test_feat.loc[idx]
                top_precursors = explain_single_hexagon_alert(row_feat, city_means, city_stds, global_smog_imp)
                sample_smog_explanations.append({
                    "h3_index": row_pred["h3_index"],
                    "date": row_pred["date"],
                    "event": "Hazardous Smog Inversion",
                    "predicted_probability": float(row_pred["prob_smog"]),
                    "alert_tier": "RED" if row_pred["prob_smog"] >= 0.75 else "ORANGE",
                    "precursor_breakdown": top_precursors,
                })

        all_attributions[c] = {
            "city": c,
            "global_heatwave_drivers": global_heat_imp,
            "global_smog_drivers": global_smog_imp,
            "sample_heatwave_alerts_explained": sample_heat_explanations,
            "sample_smog_alerts_explained": sample_smog_explanations,
        }

    # Save summary report in reports/
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(all_attributions, fh, indent=2)

    # Maintain provenance-tracked results in results/
    try:
        save_result(
            "ml_event_attributions_summary",
            all_attributions,
            config={"step": "05_risk_attribution", "split_date": split_date, "seed": 20260101},
        )
        log.info("Saved provenance-tracked result -> results/ml_event_attributions_summary.json")
    except Exception as exc:
        log.warning(f"Failed to save to results/: {exc}")

    log.info(f"Attribution summary saved to {report_path}")
    return all_attributions


if __name__ == "__main__":
    attributions = run_attribution_pipeline()
    print("=== Step 05 Risk Attribution Summary ===")
    for city, stats in attributions.items():
        top_hw = list(stats["global_heatwave_drivers"].keys())[:3]
        top_sm = list(stats["global_smog_drivers"].keys())[:3]
        print(f"{city:12s} | Top Heat Precursors: {top_hw} | Top Smog Precursors: {top_sm}")
