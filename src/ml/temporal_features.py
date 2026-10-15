"""
src/ml/temporal_features.py
───────────────────────────
Step 02: Temporal Feature Engineering Pipeline for Early Warning & Event Prediction.

Engineers multi-scale temporal precursors per H3 hexagon without lookahead bias:
  1. Antecedent lags (t-1, t-2) for meteorological, satellite, and stress indicators.
  2. Rates of change / velocities (1-month velocity, 2-month acceleration).
  3. 3-month rolling statistics (mean, volatility).
  4. Cumulative antecedent stress exhaustion (consecutive high-stress months).
  5. Cross-hazard precursor interaction terms (Heat x Water, Heat x Smog).
  6. Fixed spatial morphology & urban canopy baseline features.
  7. Cyclical calendar encodings and seasonal markers.
  8. Forward event targets at horizon h = 1 (30 days) and h = 2 (60 days).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

log = get_logger("temporal_features")

# Columns to lag
DYNAMIC_CLIMATE_COLS = [
    "temp_mean_c",
    "lst_c",
    "dewpoint_mean_c",
    "precip_sum_mm",
    "soil_moisture",
    "wind_speed",
    "radiation",
    "pm25",
    "ndvi",
]

DYNAMIC_INDEX_COLS = [
    "heat_v2",
    "water_v2",
    "pollution_v2",
    "veg_v2",
    "exposure_v2",
    "ssi_v2",
    "omega_v2",
]

STATIC_MORPHOLOGY_COLS = [
    "built_up_fraction",
    "building_density",
    "road_density_km_km2",
    "building_fp_fraction",
    "green_space_fraction",
    "latitude",
    "longitude",
]

EVENT_TARGET_COLS = [
    "event_heatwave",
    "event_smog",
    "event_compound",
    "event_extreme_ssi",
    "event_any_emergency",
]


def build_temporal_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct temporal lags, momentum, and forward targets for a panel DataFrame.
    DataFrame MUST contain 'h3_index' and 'date'.
    """
    df = df.sort_values(["h3_index", "date"]).reset_index(drop=True).copy()

    # Ensure date is sorted
    df["date"] = pd.to_datetime(df["date"])

    # 1. Antecedent Lags (t-1, t-2)
    lag_targets = [c for c in DYNAMIC_CLIMATE_COLS + DYNAMIC_INDEX_COLS if c in df.columns]
    for col in lag_targets:
        df[f"{col}_lag1"] = df.groupby("h3_index")[col].shift(1)
        df[f"{col}_lag2"] = df.groupby("h3_index")[col].shift(2)

    # 2. Environmental Momentum & Accelerations (Velocities)
    if "lst_c" in df.columns and "lst_c_lag1" in df.columns:
        df["lst_velocity_1m"] = df["lst_c"] - df["lst_c_lag1"]
        df["lst_accel_2m"] = df["lst_c"] - df["lst_c_lag2"]

    if "temp_mean_c" in df.columns and "temp_mean_c_lag1" in df.columns:
        df["temp_velocity_1m"] = df["temp_mean_c"] - df["temp_mean_c_lag1"]

    if "soil_moisture" in df.columns and "soil_moisture_lag1" in df.columns:
        # Negative value means soil drying / moisture drawdown
        df["soil_moisture_drawdown_1m"] = df["soil_moisture"] - df["soil_moisture_lag1"]
        df["soil_moisture_drawdown_2m"] = df["soil_moisture"] - df["soil_moisture_lag2"]

    if "precip_sum_mm" in df.columns and "precip_sum_mm_lag1" in df.columns:
        df["precip_delta_1m"] = df["precip_sum_mm"] - df["precip_sum_mm_lag1"]

    if "pm25" in df.columns and "pm25_lag1" in df.columns:
        df["pm25_surge_1m"] = df["pm25"] - df["pm25_lag1"]
        df["pm25_surge_2m"] = df["pm25"] - df["pm25_lag2"]

    if "ndvi" in df.columns and "ndvi_lag1" in df.columns:
        # Negative value means canopy degradation / browning
        df["ndvi_browning_1m"] = df["ndvi"] - df["ndvi_lag1"]

    if "ssi_v2" in df.columns and "ssi_v2_lag1" in df.columns:
        df["ssi_velocity_1m"] = df["ssi_v2"] - df["ssi_v2_lag1"]

    # 3. 3-Month Rolling Window Statistics (t-2, t-1, t)
    for col in ["temp_mean_c", "soil_moisture", "pm25", "ssi_v2"]:
        if col in df.columns:
            df[f"{col}_roll3_mean"] = (
                df.groupby("h3_index")[col].rolling(3).mean().reset_index(0, drop=True)
            )

    if "precip_sum_mm" in df.columns:
        df["precip_sum_roll3"] = (
            df.groupby("h3_index")["precip_sum_mm"].rolling(3).sum().reset_index(0, drop=True)
        )

    if "ssi_v2" in df.columns:
        # Stress volatility
        df["ssi_volatility_roll3"] = (
            df.groupby("h3_index")["ssi_v2"].rolling(3).std().reset_index(0, drop=True).fillna(0.0)
        )

    # 4. Cumulative Antecedent Stress Exhaustion (Consecutive High Stress Months)
    if "ssi_v2" in df.columns:
        high_stress = (df["ssi_v2"] >= 0.50).astype(int)
        streak_block = (high_stress == 0).cumsum()
        df["stress_exhaustion_streak"] = high_stress.groupby([df["h3_index"], streak_block]).cumsum()

    # 5. Cross-Hazard Interaction Precursors
    if "heat_v2" in df.columns and "water_v2" in df.columns:
        df["precursor_heat_water"] = df["heat_v2"] * df["water_v2"]

    if "heat_v2" in df.columns and "pollution_v2" in df.columns:
        df["precursor_heat_smog"] = df["heat_v2"] * df["pollution_v2"]

    # 6. Cyclical Calendar & Seasonal Markers
    months = df["date"].dt.month
    df["sin_month"] = np.sin(2.0 * np.pi * months / 12.0)
    df["cos_month"] = np.cos(2.0 * np.pi * months / 12.0)
    df["is_premonsoon_summer"] = months.isin([3, 4, 5]).astype(int)
    df["is_monsoon"] = months.isin([6, 7, 8, 9]).astype(int)
    df["is_postmonsoon_winter"] = months.isin([10, 11, 12, 1, 2]).astype(int)

    # 7. Forward Horizon Targets (Lead time h = 1 month and h = 2 months)
    for lead in [1, 2]:
        for ev in EVENT_TARGET_COLS:
            if ev in df.columns:
                df[f"target_{ev}_{lead}m"] = df.groupby("h3_index")[ev].shift(-lead)

        if "ssi_v2" in df.columns:
            df[f"target_ssi_v2_{lead}m"] = df.groupby("h3_index")["ssi_v2"].shift(-lead)

    # Format date back to string ISO
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    return df


def get_feature_column_names(df: pd.DataFrame) -> list[str]:
    """
    Return all clean predictor feature columns (excluding identifiers and target columns).
    """
    excluded_prefixes = ["target_", "event_"]
    excluded_exact = [
        "h3_index",
        "date",
        "city_id",
        "ssi_band_v2",
        "ssi_band",
        "anomaly_flag",
        "archetype_id",
        "is_imputed",
    ]

    features = [
        c for c in df.columns
        if c not in excluded_exact and not any(c.startswith(p) for p in excluded_prefixes)
    ]
    return features


def process_and_save_temporal_features(
    city: str,
    input_dir: str | Path = "data/h3_panel/ml_events",
    out_dir: str | Path = "data/h3_panel/ml_features",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Read ml_events parquet for a city, engineer all temporal features,
    and save the feature matrix to parquet.
    """
    input_path = Path(input_dir) / f"{city}.parquet"
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    raw_df = pd.read_parquet(input_path)
    featured_df = build_temporal_feature_matrix(raw_df)

    out_path = out_dir / f"{city}.parquet"
    featured_df.to_parquet(out_path, index=False)
    log.info(f"Saved {city} temporal feature matrix ({featured_df.shape}) -> {out_path}")

    # Feature statistics & valid row counts
    feature_cols = get_feature_column_names(featured_df)

    # Rows with valid lag2 and 1-month forward target
    valid_1m_mask = featured_df["temp_mean_c_lag2"].notna() & featured_df["target_event_heatwave_1m"].notna()
    n_valid_1m = int(valid_1m_mask.sum())

    # Rows with valid lag2 and 2-month forward target
    valid_2m_mask = featured_df["temp_mean_c_lag2"].notna() & featured_df["target_event_heatwave_2m"].notna()
    n_valid_2m = int(valid_2m_mask.sum())

    summary = {
        "city": city,
        "total_rows_raw": len(featured_df),
        "total_columns": len(featured_df.columns),
        "total_features": len(feature_cols),
        "valid_rows_1m_lead": n_valid_1m,
        "valid_rows_2m_lead": n_valid_2m,
        "valid_dates_1m": int(featured_df.loc[valid_1m_mask, "date"].nunique()),
        "valid_dates_2m": int(featured_df.loc[valid_2m_mask, "date"].nunique()),
        "date_range_1m": {
            "start": featured_df.loc[valid_1m_mask, "date"].min(),
            "end": featured_df.loc[valid_1m_mask, "date"].max(),
        },
        "feature_list_sample": feature_cols[:15],
    }

    return featured_df, summary


def run_temporal_feature_pipeline(
    cities: list[str] | None = None,
    input_dir: str | Path = "data/h3_panel/ml_events",
    out_dir: str | Path = "data/h3_panel/ml_features",
    report_path: str | Path = "reports/ml_temporal_features_summary.json",
) -> dict[str, Any]:
    """
    Run Step 02 temporal feature generation across all study cities and save summary.
    """
    if cities is None:
        cities = ["delhi", "mumbai", "kolkata", "hyderabad", "bikaner", "coimbatore", "indore"]

    all_summaries: dict[str, Any] = {}
    for c in cities:
        log.info(f"Generating temporal features for {c}...")
        _, summary = process_and_save_temporal_features(c, input_dir=input_dir, out_dir=out_dir)
        all_summaries[c] = summary

    # Save summary report in reports/
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as fh:
        json.dump(all_summaries, fh, indent=2)

    # Maintain provenance-tracked results in results/
    try:
        from src.utils.results_io import save_result
        save_result("ml_temporal_features", all_summaries, config={"step": "02_temporal_features", "seed": 20260101})
        log.info("Saved provenance-tracked result -> results/ml_temporal_features.json")
    except Exception as exc:
        log.warning(f"Failed to save to results/: {exc}")

    log.info(f"Temporal feature summary saved to {report_path}")
    return all_summaries


if __name__ == "__main__":
    summaries = run_temporal_feature_pipeline()
    print("=== Step 02 Temporal Feature Engineering Summary ===")
    for city, stats in summaries.items():
        print(
            f"{city:12s} | Cols: {stats['total_columns']:3d} | "
            f"Features: {stats['total_features']:2d} | "
            f"Valid 1m: {stats['valid_rows_1m_lead']:6d} ({stats['valid_dates_1m']} mos: {stats['date_range_1m']['start']} to {stats['date_range_1m']['end']})"
        )
