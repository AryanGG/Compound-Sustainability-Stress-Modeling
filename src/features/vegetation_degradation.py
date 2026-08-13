"""
src/features/vegetation_degradation.py
────────────────────────────────────────
Compute vegetation degradation index per H3 hex per month.

Input: ndvi (0 to 1)
Output: vegetation_idx (normalized, 0 = baseline, >0 = degradation stress)

Method:
  - NDVI anomaly: (NDVI_t - NDVI_baseline_month) / NDVI_baseline_std
  - Inverted: lower NDVI relative to baseline → higher stress
  - Baseline: calendar-month mean from first `baseline_years` of data
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.normalize import compute_monthly_baseline, apply_baseline_zscore
from src.utils.logger import get_logger

log = get_logger(__name__)


def add_vegetation_idx(
    df: pd.DataFrame,
    ndvi_col: str = "ndvi",
    baseline_years: int = 3,
) -> pd.DataFrame:
    """
    Add normalized `vegetation_idx` column to the panel DataFrame.

    Logic:
      - Per hex, per calendar month: z-score NDVI relative to the baseline period
      - Invert: below-baseline NDVI → positive stress score
      - Floor at 0

    Args:
        df            : Panel DataFrame.
        ndvi_col      : Column name for NDVI.
        baseline_years: Years for baseline period.

    Returns:
        DataFrame with added `vegetation_idx` column.
    """
    log.info("Computing vegetation degradation index…")
    df = df.copy()

    if ndvi_col not in df.columns or df[ndvi_col].notna().sum() == 0:
        log.warning("No NDVI data; vegetation_idx set to NaN")
        df["vegetation_idx"] = np.nan
        return df

    baseline = compute_monthly_baseline(df, ndvi_col, baseline_years=baseline_years)

    # Invert=True: lower NDVI than baseline → higher stress
    df = apply_baseline_zscore(
        df,
        ndvi_col,
        baseline,
        output_col="vegetation_idx",
        invert=True,      # ← Key: low NDVI = high degradation
        apply_floor=True,
    )

    log.info(
        "Vegetation degradation: mean={m:.2f}, max={mx:.2f}",
        m=df["vegetation_idx"].mean(),
        mx=df["vegetation_idx"].max(),
    )
    return df
