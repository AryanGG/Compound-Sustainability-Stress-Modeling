"""
src/features/normalize.py
──────────────────────────
Normalization utilities for stress indicators.

Rules:
  - Z-score normalization: zero-mean, unit-std across all hexes × time
  - Floor to 0: negative values clamped to 0 so "0 = normal/good"
  - Direction consistent: higher value = more stress
  - Rolling baseline option for time-aware normalization (avoids future leakage)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Literal


def zscore_normalize(
    series: pd.Series,
    baseline_mean: float | None = None,
    baseline_std: float | None = None,
) -> pd.Series:
    """
    Z-score normalize a Series.

    Args:
        series        : Input values.
        baseline_mean : Precomputed mean (use for out-of-sample normalization).
        baseline_std  : Precomputed std.

    Returns:
        Normalized Series (mean≈0, std≈1).
    """
    mu = baseline_mean if baseline_mean is not None else series.mean()
    sigma = baseline_std if baseline_std is not None else series.std()

    if sigma < 1e-9:
        return pd.Series(0.0, index=series.index, name=series.name)

    return (series - mu) / sigma


def minmax_normalize(
    series: pd.Series,
    feature_min: float | None = None,
    feature_max: float | None = None,
) -> pd.Series:
    """
    Min-max normalize a Series to [0, 1].

    Args:
        series      : Input values.
        feature_min : Override minimum.
        feature_max : Override maximum.

    Returns:
        Normalized Series in [0, 1].
    """
    lo = feature_min if feature_min is not None else series.min()
    hi = feature_max if feature_max is not None else series.max()

    if hi - lo < 1e-9:
        return pd.Series(0.0, index=series.index, name=series.name)

    return (series - lo) / (hi - lo)


def clip_and_floor(
    series: pd.Series,
    floor: float = 0.0,
    ceiling: float | None = None,
) -> pd.Series:
    """
    Clamp values: floor to `floor`, optionally cap at `ceiling`.

    0 = normal baseline; values > 0 = elevated stress.

    Args:
        series  : Input values (typically z-scored).
        floor   : Minimum output value (default 0).
        ceiling : Maximum output value (None = no cap).

    Returns:
        Clamped Series.
    """
    result = series.clip(lower=floor)
    if ceiling is not None:
        result = result.clip(upper=ceiling)
    return result


def normalize_indicator(
    series: pd.Series,
    method: Literal["zscore", "minmax"] = "zscore",
    invert: bool = False,
    apply_floor: bool = True,
    baseline_mean: float | None = None,
    baseline_std: float | None = None,
) -> pd.Series:
    """
    Full normalization pipeline for a single stress indicator.

    Steps:
      1. Optionally invert (for variables where lower = more stress, e.g. NDVI)
      2. Normalize (z-score or min-max)
      3. Floor at 0 (so 0 = at-baseline, positive = elevated stress)

    Args:
        series        : Raw indicator values.
        method        : Normalization method.
        invert        : If True, negate before normalizing (lower raw → higher stress).
        apply_floor   : If True, clamp negatives to 0.
        baseline_mean : External baseline mean (optional).
        baseline_std  : External baseline std (optional).

    Returns:
        Normalized stress series.
    """
    s = series.copy()

    if invert:
        s = -s

    if method == "zscore":
        s = zscore_normalize(s, baseline_mean, baseline_std)
    elif method == "minmax":
        s = minmax_normalize(s)
    else:
        raise ValueError(f"Unknown normalization method: {method}")

    if apply_floor:
        s = clip_and_floor(s, floor=0.0)

    return s


def compute_monthly_baseline(
    df: pd.DataFrame,
    value_col: str,
    date_col: str = "date",
    groupby_col: str = "h3_index",
    baseline_years: int = 3,
) -> pd.DataFrame:
    """
    Compute per-hex, per-calendar-month baseline statistics for anomaly detection.

    Strategy: Use the first `baseline_years` of data as the reference period.

    Args:
        df            : Panel DataFrame.
        value_col     : Variable column to baseline.
        date_col      : Date column.
        groupby_col   : Grouping column (usually h3_index).
        baseline_years: Number of years for baseline window.

    Returns:
        DataFrame with [groupby_col, month, baseline_mean, baseline_std].
    """
    df = df.copy()
    df["_date"] = pd.to_datetime(df[date_col])
    df["_year"] = df["_date"].dt.year
    df["_month"] = df["_date"].dt.month

    # Baseline period: first N years
    min_year = df["_year"].min()
    baseline_df = df[df["_year"] <= (min_year + baseline_years - 1)]

    stats = (
        baseline_df
        .groupby([groupby_col, "_month"])[value_col]
        .agg(baseline_mean="mean", baseline_std="std")
        .reset_index()
        .rename(columns={"_month": "month"})
    )

    return stats


def apply_baseline_zscore(
    df: pd.DataFrame,
    value_col: str,
    baseline_stats: pd.DataFrame,
    date_col: str = "date",
    groupby_col: str = "h3_index",
    output_col: str | None = None,
    invert: bool = False,
    apply_floor: bool = True,
) -> pd.DataFrame:
    """
    Apply monthly baseline z-score normalization to a panel column.

    For each row, computes: (value - baseline_mean[h3, month]) / baseline_std[h3, month]

    Args:
        df             : Panel DataFrame.
        value_col      : Column to normalize.
        baseline_stats : Output of compute_monthly_baseline().
        date_col       : Date column name.
        groupby_col    : Grouping column.
        output_col     : Output column name (default: value_col + '_norm').
        invert         : Negate before scoring (lower = more stress).
        apply_floor    : Clamp negatives to 0.

    Returns:
        DataFrame with additional normalized column.
    """
    df = df.copy()
    df["_month"] = pd.to_datetime(df[date_col]).dt.month

    # baseline_stats uses column name "month" (from compute_monthly_baseline);
    # we need to align it with the "_month" temp column we just added to df.
    stats = baseline_stats.copy()
    if "month" in stats.columns and "_month" not in stats.columns:
        stats = stats.rename(columns={"month": "_month"})

    merged = df.merge(stats, on=[groupby_col, "_month"], how="left")

    raw = merged[value_col]
    if invert:
        raw = -raw

    normalized = (raw - merged["baseline_mean"]) / merged["baseline_std"].replace(0, np.nan)

    if apply_floor:
        normalized = normalized.clip(lower=0.0)

    # Fill NaN (e.g. zero-std baseline, or unmatched hex–month) with 0 (= at-baseline)
    normalized = normalized.fillna(0.0)

    out_name = output_col or f"{value_col}_norm"
    df[out_name] = normalized.values

    df = df.drop(columns=["_month"])
    return df
