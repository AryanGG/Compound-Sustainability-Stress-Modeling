"""
src/features/heat_stress.py
────────────────────────────
Compute heat stress index per H3 hex per month.

Inputs: temp_mean_c, dewpoint_mean_c, lst_c
Output: heat_stress_idx (normalized, 0 = baseline, >0 = stress)

Method:
  1. Compute Relative Humidity from T and Td (August-Roche-Magnus)
  2. Compute Heat Index via Rothfusz regression equation
  3. Blend with LST anomaly (skin temperature signal)
  4. Normalize against city-level baseline
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.normalize import normalize_indicator, apply_baseline_zscore, compute_monthly_baseline
from src.utils.logger import get_logger

log = get_logger(__name__)


def compute_relative_humidity(
    temp_c: pd.Series,
    dewpoint_c: pd.Series,
) -> pd.Series:
    """
    Estimate relative humidity (%) from temperature and dewpoint.

    Formula: Magnus approximation
    RH ≈ 100 * exp(17.625 * Td / (243.04 + Td)) / exp(17.625 * T / (243.04 + T))

    Args:
        temp_c     : 2m air temperature in °C.
        dewpoint_c : 2m dewpoint temperature in °C.

    Returns:
        Relative humidity in % (0–100).
    """
    def _e_sat(t):
        """Saturation vapour pressure (kPa) via Magnus formula."""
        return np.exp(17.625 * t / (243.04 + t))

    rh = 100.0 * _e_sat(dewpoint_c) / _e_sat(temp_c)
    return rh.clip(0, 100)


def compute_heat_index(
    temp_c: pd.Series,
    rh: pd.Series,
) -> pd.Series:
    """
    Compute Steadman / Rothfusz Heat Index in °C.

    Note: Valid for T > 26°C and RH > 40%; returns T for cooler conditions.

    Rothfusz equation (NWS formulation):
    HI = -8.78469 + 1.61139411*T + 2.338549*RH
         - 0.14611605*T*RH - 0.01230809*T² - 0.01642482*RH²
         + 0.002211732*T²*RH + 0.00072546*T*RH² - 0.000003582*T²*RH²

    Args:
        temp_c : Temperature in °C.
        rh     : Relative humidity (%).

    Returns:
        Heat Index in °C.
    """
    T = temp_c.values.astype(float)
    R = rh.values.astype(float)

    hi = (
        -8.78469
        + 1.61139411 * T
        + 2.338549 * R
        - 0.14611605 * T * R
        - 0.01230809 * T ** 2
        - 0.01642482 * R ** 2
        + 0.002211732 * (T ** 2) * R
        + 0.00072546 * T * (R ** 2)
        - 0.000003582 * (T ** 2) * (R ** 2)
    )

    # Use simple T where conditions are outside valid range
    valid = (T > 26) & (R > 40)
    hi = np.where(valid, hi, T)

    return pd.Series(hi, index=temp_c.index, name="heat_index_c")


def compute_heat_stress_pca_weights(
    hi: pd.Series,
    lst: pd.Series,
) -> tuple[float, float]:
    """
    Compute weights for Heat Index and LST dynamically using PCA on available data.
    """
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return 0.7, 0.3  # Fallback

    sub = pd.DataFrame({"hi": hi, "lst": lst}).dropna()
    if len(sub) < 30:
        return 0.7, 0.3  # Fallback

    try:
        scaler = StandardScaler()
        X = scaler.fit_transform(sub)
        pca = PCA(n_components=1)
        pca.fit(X)
        loadings = np.abs(pca.components_[0])
        total = loadings.sum()
        if total > 0:
            w_hi, w_lst = float(loadings[0] / total), float(loadings[1] / total)
            log.info(
                "Nested PCA for Heat Stress derived weights: HeatIndex={hi:.3f}, LST={lst:.3f}",
                hi=w_hi, lst=w_lst
            )
            return w_hi, w_lst
    except Exception as exc:
        log.warning(
            "Nested PCA for Heat Stress failed ({err}); using default 0.7/0.3 weights.",
            err=exc
        )

    return 0.7, 0.3


def compute_heat_stress(
    df: pd.DataFrame,
    temp_col: str = "temp_mean_c",
    dewpoint_col: str = "dewpoint_mean_c",
    lst_col: str = "lst_c",
    lst_weight: float = 0.3,
) -> pd.Series:
    """
    Compute raw heat stress score per row using nested PCA weights for Heat Index and LST.

    Args:
        df          : Panel DataFrame with climate columns.
        temp_col    : Temperature column.
        dewpoint_col: Dewpoint column.
        lst_col     : Land Surface Temperature column.
        lst_weight  : Fallback weight for LST in composite (0–1).

    Returns:
        pd.Series of raw heat scores.
    """
    temp = df[temp_col].copy()
    dew = df[dewpoint_col].copy()

    # Fill missing dewpoint with proxy (dew ≈ temp - 10 over dry areas)
    dew = dew.fillna(temp - 10.0)

    rh = compute_relative_humidity(temp, dew)
    hi = compute_heat_index(temp, rh)

    if lst_col in df.columns and df[lst_col].notna().sum() > 0:
        lst = df[lst_col].fillna(temp + 5)   # Proxy if missing
        w_hi, w_lst = compute_heat_stress_pca_weights(hi, lst)
        heat_raw = w_hi * hi + w_lst * lst
    else:
        heat_raw = hi

    return pd.Series(heat_raw.values, index=df.index, name="heat_stress_raw")


def add_heat_stress_idx(
    df: pd.DataFrame,
    baseline_years: int = 3,
    method: str = "zscore",
) -> pd.DataFrame:
    """
    Add normalized `heat_stress_idx` column to the panel DataFrame.

    Normalization is baseline-aware:
      - Computes per-hex, per-month baseline from first `baseline_years`
      - Applies z-score against that baseline
      - Floors at 0

    Args:
        df            : Panel DataFrame.
        baseline_years: Years to use as baseline period.
        method        : 'zscore' or 'minmax'.

    Returns:
        DataFrame with added columns: heat_index_c, heat_stress_idx.
    """
    log.info("Computing heat stress index…")

    df = df.copy()

    # Raw heat score
    df["heat_stress_raw"] = compute_heat_stress(df)

    # Compute baseline stats
    baseline_stats = compute_monthly_baseline(
        df, "heat_stress_raw", baseline_years=baseline_years
    )

    # Apply baseline-aware z-score
    df = apply_baseline_zscore(
        df,
        "heat_stress_raw",
        baseline_stats,
        output_col="heat_stress_idx",
        invert=False,   # Higher = more stress (correct direction)
        apply_floor=True,
    )

    df = df.drop(columns=["heat_stress_raw"])
    log.info(
        "Heat stress: mean={m:.2f}, max={mx:.2f}",
        m=df["heat_stress_idx"].mean(),
        mx=df["heat_stress_idx"].max(),
    )
    return df
