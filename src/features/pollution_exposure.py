"""
src/features/pollution_exposure.py
────────────────────────────────────
Compute pollution exposure index per H3 hex per month.

Primary input: pm25 (µg/m³)
Output: pollution_idx (normalized, 0 = baseline/safe, >0 = elevated pollution)

WHO guideline: 15 µg/m³ annual mean PM2.5
Normalization: baseline z-score (city-level monthly mean)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.normalize import (
    compute_monthly_baseline,
    apply_baseline_zscore,
    normalize_indicator,
)
from src.utils.logger import get_logger

log = get_logger(__name__)

# WHO PM2.5 annual guideline value (µg/m³)
WHO_PM25_GUIDELINE = 15.0
# Indian NAAQS standard (µg/m³)  
INDIA_NAAQS_PM25 = 60.0


def compute_who_exceedance(pm25: pd.Series) -> pd.Series:
    """
    Compute PM2.5 exceedance above WHO guideline.

    exceedance = (PM2.5 - WHO_guideline) / WHO_guideline
    Values < 0 are floored to 0 (below guideline = no excess stress).

    Args:
        pm25: PM2.5 series in µg/m³.

    Returns:
        pd.Series of non-negative exceedance values.
    """
    excess = (pm25 - WHO_PM25_GUIDELINE) / WHO_PM25_GUIDELINE
    return excess.clip(lower=0.0)


def add_pollution_idx(
    df: pd.DataFrame,
    pm25_col: str = "pm25",
    baseline_years: int = 3,
    use_who_floor: bool = True,
) -> pd.DataFrame:
    """
    Add normalized `pollution_idx` column to the panel DataFrame.

    Strategy:
      1. If use_who_floor: use WHO exceedance as the base signal
         (respects absolute health thresholds, not just relative variability)
      2. Apply additional baseline z-score normalization (relative temporal anomaly)
      3. Combine: final = 0.5 * WHO_exceedance_norm + 0.5 * temporal_zscore
      4. Floor at 0.

    Args:
        df            : Panel DataFrame.
        pm25_col      : Column name for PM2.5.
        baseline_years: Years for baseline.
        use_who_floor : Include WHO guideline exceedance component.

    Returns:
        DataFrame with added `pollution_idx` column.
    """
    log.info("Computing pollution exposure index…")
    df = df.copy()

    if pm25_col not in df.columns or df[pm25_col].notna().sum() == 0:
        log.warning("No PM2.5 data; pollution_idx set to NaN")
        df["pollution_idx"] = np.nan
        return df

    # Component 1: WHO exceedance (absolute threshold-based)
    who_excess = compute_who_exceedance(df[pm25_col])
    who_excess_norm = normalize_indicator(
        who_excess, method="zscore", invert=False, apply_floor=True
    )

    # Component 2: Temporal anomaly (relative to historical baseline)
    baseline = compute_monthly_baseline(df, pm25_col, baseline_years=baseline_years)
    df = apply_baseline_zscore(
        df, pm25_col, baseline,
        output_col="_pm25_temporal_z",
        invert=False, apply_floor=True,
    )

    if use_who_floor:
        df["pollution_idx"] = (0.5 * who_excess_norm + 0.5 * df["_pm25_temporal_z"]).clip(lower=0)
    else:
        df["pollution_idx"] = df["_pm25_temporal_z"]

    df = df.drop(columns=["_pm25_temporal_z"], errors="ignore")

    log.info(
        "Pollution exposure: mean={m:.2f}, max={mx:.2f}",
        m=df["pollution_idx"].mean(),
        mx=df["pollution_idx"].max(),
    )
    return df
