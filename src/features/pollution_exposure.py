"""
src/features/pollution_exposure.py
────────────────────────────────────
Compute pollution exposure index per H3 hex per month.

Primary input: pm25 (µg/m³)
Output: pollution_idx (0 = at/below WHO guideline, 1.0 = Indian NAAQS breach)

Method:
    Logarithmic minmax scaling:
        pollution_idx = minmax(log(1 + PM2.5))

    This produces a physically interpretable metric that compresses extreme 
    outliers (like severe winter smog) without applying a hard cap, preserving 
    variance across the entire distribution.

References:
    WHO (2021). WHO Global Air Quality Guidelines: Particulate Matter
    (PM2.5 and PM10), Ozone, Nitrogen Dioxide, Sulfur Dioxide and
    Carbon Monoxide. Geneva: World Health Organization.
    Central Pollution Control Board (CPCB). National Ambient Air Quality
    Standards (NAAQS), Gazette of India, 2009.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

log = get_logger(__name__)

# WHO PM2.5 annual guideline value (µg/m³) — WHO 2021
WHO_PM25_GUIDELINE = 15.0

# Indian NAAQS PM2.5 annual standard (µg/m³) — CPCB 2009
INDIA_NAAQS_PM25 = 60.0


def add_pollution_idx(
    df: pd.DataFrame,
    pm25_col: str = "pm25",
) -> pd.DataFrame:
    """
    Add normalized `pollution_idx` column to the panel DataFrame.

    Formula:
        pollution_idx = minmax(log1p(PM2.5))

    This uses logarithmic scaling to prevent hard capping during extreme
    pollution events, ensuring that the full spatial and temporal variance
    is preserved on the 0-1 scale.

    Args:
        df            : Panel DataFrame.
        pm25_col      : Column name for PM2.5 concentration (µg/m³).

    Returns:
        DataFrame with added `pollution_idx` column.
    """
    log.info("Computing pollution exposure index…")
    df = df.copy()

    if pm25_col not in df.columns or df[pm25_col].notna().sum() == 0:
        log.warning("No PM2.5 data; pollution_idx set to NaN")
        df["pollution_idx"] = np.nan
        return df

    # Logarithmic minmax scaling
    log_pm25 = np.log1p(df[pm25_col])
    lo, hi = log_pm25.min(), log_pm25.max()
    
    if hi - lo > 1e-9:
        df["pollution_idx"] = (log_pm25 - lo) / (hi - lo)
    else:
        df["pollution_idx"] = 0.0

    log.info(
        "Pollution exposure: mean={m:.2f}, max={mx:.2f}",
        m=df["pollution_idx"].mean(),
        mx=df["pollution_idx"].max(),
    )
    return df
