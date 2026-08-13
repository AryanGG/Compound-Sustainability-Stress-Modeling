"""
src/features/water_stress.py
─────────────────────────────
Compute water stress index per H3 hex per month.

Inputs: precip_sum_mm, soil_moisture
Output: water_stress_idx (normalized, 0 = baseline, >0 = stress)

Components:
  1. Precipitation deficit: negative anomaly from long-term monthly mean
     (lower-than-normal precip → higher water stress)
  2. Soil moisture deficit: deviation below historical 25th percentile
     (low soil water content → drought stress)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import h3

from src.features.normalize import (
    compute_monthly_baseline,
    apply_baseline_zscore,
    normalize_indicator,
)
from src.utils.logger import get_logger

log = get_logger(__name__)


def compute_thornthwaite_pet(df: pd.DataFrame, temp_col: str = "temp_mean_c") -> pd.Series:
    """
    Calculate Thornthwaite potential evapotranspiration (PET) in mm/month.
    Formula:
        PET = 16 * (10 * T / I) ** a
    adjusted for latitude-dependent day length.
    """
    df = df.copy()
    df["_month"] = pd.to_datetime(df["date"]).dt.month
    
    # Calculate annual heat index I per hex
    # Sum over 12 calendar months of (T_mean / 5) ** 1.514
    monthly_mean_temp = df.groupby(["h3_index", "_month"])[temp_col].mean().reset_index()
    monthly_mean_temp["temp_clamped"] = monthly_mean_temp[temp_col].clip(lower=0.0)
    monthly_mean_temp["I_term"] = (monthly_mean_temp["temp_clamped"] / 5.0) ** 1.514
    I_hex = monthly_mean_temp.groupby("h3_index")["I_term"].sum().reset_index().rename(columns={"I_term": "I"})
    
    # Merge I back to df
    df = df.merge(I_hex, on="h3_index", how="left")
    
    # Exponent a
    I = df["I"].replace(0, np.nan)
    a = 6.75e-7 * (I ** 3) - 7.71e-5 * (I ** 2) + 0.01792 * I + 0.49239
    
    # Unadjusted PET
    T = df[temp_col].clip(lower=0.0)
    pet_unadj = 16.0 * ((10.0 * T) / I) ** a
    pet_unadj = pet_unadj.fillna(0.0)
    
    # Latitude mapping
    hexes = df["h3_index"].unique()
    lats_deg = {}
    for h in hexes:
        try:
            lats_deg[h] = h3.cell_to_latlon(h)[0]
        except Exception:
            try:
                lats_deg[h] = h3.h3_to_geo(h)[0]
            except Exception:
                lats_deg[h] = 20.0  # Default center latitude of India
                
    df["_lat"] = df["h3_index"].map(lats_deg)
    
    # Solar declination and day length calculations
    julian_days = {
        1: 15, 2: 46, 3: 74, 4: 105, 5: 135, 6: 166,
        7: 196, 8: 227, 9: 258, 10: 288, 11: 319, 12: 349
    }
    days_in_month = {
        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    df["_jday"] = df["_month"].map(julian_days)
    df["_days"] = df["_month"].map(days_in_month)
    
    phi = np.radians(df["_lat"])
    delta = 0.409 * np.sin(2.0 * np.pi * df["_jday"] / 365.0 - 1.39)
    
    tan_term = -np.tan(phi) * np.tan(delta)
    tan_term = tan_term.clip(-1.0, 1.0)
    omega_s = np.arccos(tan_term)
    L = (24.0 / np.pi) * omega_s
    
    d = (L / 12.0) * (df["_days"] / 30.0)
    pet_adj = pet_unadj * d
    
    return pd.Series(pet_adj.values, index=df.index, name="pet")


def compute_precip_deficit(
    df: pd.DataFrame,
    precip_col: str = "precip_sum_mm",
    baseline_years: int = 3,
) -> pd.DataFrame:
    """
    Compute precipitation deficit as a z-score relative to monthly baseline.

    Negative precip anomaly (rain below normal) → positive deficit score.

    Args:
        df            : Panel DataFrame.
        precip_col    : Column with monthly precipitation.
        baseline_years: Years for baseline.

    Returns:
        DataFrame with added `precip_deficit` column.
    """
    baseline = compute_monthly_baseline(df, precip_col, baseline_years=baseline_years)

    # Invert=True: less rain = higher deficit score
    df = apply_baseline_zscore(
        df,
        precip_col,
        baseline,
        output_col="precip_deficit",
        invert=True,    # Invert so deficit direction is correct
        apply_floor=True,
    )
    return df


def compute_soil_moisture_deficit(
    df: pd.DataFrame,
    sm_col: str = "soil_moisture",
    low_threshold_pct: float = 25.0,
) -> pd.Series:
    """
    Compute soil moisture deficit as deviation below the historical 25th percentile.

    Approach:
      - For each (h3_index, calendar_month), compute p25 of soil moisture
      - Deficit = max(0, p25 - observed) / p25  → fraction below normal
      - This is always non-negative (0 = above p25, >0 = below normal)

    Args:
        df               : Panel DataFrame.
        sm_col           : Soil moisture column.
        low_threshold_pct: Percentile to use as drought threshold.

    Returns:
        pd.Series of soil moisture deficit scores.
    """
    df = df.copy()
    df["_month"] = pd.to_datetime(df["date"]).dt.month

    p25 = (
        df.groupby(["h3_index", "_month"])[sm_col]
        .quantile(low_threshold_pct / 100.0)
        .reset_index()
        .rename(columns={sm_col: "sm_p25"})
    )

    merged = df.merge(p25, on=["h3_index", "_month"], how="left")

    sm_obs = merged[sm_col].fillna(merged["sm_p25"])
    threshold = merged["sm_p25"]

    # Deficit increases as observed drops below threshold
    deficit = (threshold - sm_obs) / (threshold.replace(0, np.nan) + 1e-6)
    deficit = deficit.clip(lower=0.0)

    return pd.Series(deficit.values, index=df.index, name="soil_moisture_deficit")


def add_water_stress_idx(
    df: pd.DataFrame,
    precip_weight: float = 0.6,
    soil_weight: float = 0.4,
    baseline_years: int = 3,
) -> pd.DataFrame:
    """
    Add normalized `water_stress_idx` column to the panel DataFrame using the field-standard SPEI.

    If SPEI inputs (precip + temp) are not available, falls back to custom soil moisture + precipitation deficit.

    Args:
        df            : Panel DataFrame.
        precip_weight : Fallback weight for precipitation deficit.
        soil_weight   : Fallback weight for soil moisture deficit.
        baseline_years: Baseline window.

    Returns:
        DataFrame with added `water_stress_idx` column.
    """
    log.info("Computing water stress index…")
    df = df.copy()

    has_precip = "precip_sum_mm" in df.columns and df["precip_sum_mm"].notna().any()
    has_temp = "temp_mean_c" in df.columns and df["temp_mean_c"].notna().any()

    if has_precip and has_temp:
        try:
            log.info("Using field-standard SPEI (precipitation-evapotranspiration deficit) for water stress.")
            # 1. Compute Potential Evapotranspiration
            df["pet"] = compute_thornthwaite_pet(df)
            # 2. Compute deficit D = P - PET
            df["D"] = df["precip_sum_mm"] - df["pet"]
            
            # 3. Compute 3-month rolling sum of D per hex
            df = df.sort_values(by=["h3_index", "date"])
            df["D_rolled"] = (
                df.groupby("h3_index")["D"]
                .rolling(window=3, min_periods=1)
                .sum()
                .reset_index(level=0, drop=True)
            )
            
            # 4. Standardize via baseline Z-score
            baseline_stats = compute_monthly_baseline(df, "D_rolled", baseline_years=baseline_years)
            df = apply_baseline_zscore(
                df,
                "D_rolled",
                baseline_stats,
                output_col="water_stress_idx",
                invert=True,  # Invert so lower water surplus (drier) = higher stress
                apply_floor=True
            )
            
            # Drop temp columns
            df = df.drop(columns=["pet", "D", "D_rolled"], errors="ignore")
            
            log.info(
                "Water stress (SPEI-based): mean={m:.2f}, max={mx:.2f}",
                m=df["water_stress_idx"].mean(),
                mx=df["water_stress_idx"].max(),
            )
            return df
        except Exception as exc:
            log.warning("SPEI calculation failed ({err}); falling back to default deficit blend.", err=exc)

    # Fallback to existing precipitation deficit + soil moisture deficit blend
    log.info("Using fallback custom deficit blend for water stress.")
    has_soil = "soil_moisture" in df.columns and df["soil_moisture"].notna().any()

    if not has_precip and not has_soil:
        log.warning("No precip or soil moisture data; water_stress_idx set to NaN")
        df["water_stress_idx"] = np.nan
        return df

    if has_precip:
        df = compute_precip_deficit(df, baseline_years=baseline_years)
    else:
        df["precip_deficit"] = 0.0
        precip_weight = 0.0
        soil_weight = 1.0

    if has_soil:
        df["soil_moisture_deficit"] = compute_soil_moisture_deficit(df)
    else:
        df["soil_moisture_deficit"] = 0.0
        precip_weight = 1.0
        soil_weight = 0.0

    # Normalise weights
    total_w = precip_weight + soil_weight
    df["water_stress_raw"] = (
        (precip_weight / total_w) * df["precip_deficit"]
        + (soil_weight / total_w) * df["soil_moisture_deficit"]
    )

    # Final z-score normalisation of composite
    df["water_stress_idx"] = normalize_indicator(
        df["water_stress_raw"], method="zscore", apply_floor=True
    )

    df = df.drop(
        columns=["precip_deficit", "soil_moisture_deficit", "water_stress_raw"],
        errors="ignore",
    )

    log.info(
        "Water stress (fallback): mean={m:.2f}, max={mx:.2f}",
        m=df["water_stress_idx"].mean(),
        mx=df["water_stress_idx"].max(),
    )
    return df
