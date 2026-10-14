"""
src/v2/indices.py
─────────────────
Step 06: Global-baseline normalization (the seasonality fix).
Fits once on pooled reference panel, saved to results/fit_parameters.json,
and applied unchanged to every city.
Vegetation is inverted (1 - z) so all indices represent: higher = higher stress.
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

IDX_COLS = ["heat_v2", "water_v2", "veg_v2", "pollution_v2", "exposure_v2"]

RAW_MAP: dict[str, tuple[str, int]] = {
    "heat_raw": ("heat_v2", +1),
    "water_raw": ("water_v2", +1),
    "veg_raw": ("veg_v2", -1),
    "pollution_raw": ("pollution_v2", +1),
    "exposure_raw": ("exposure_v2", +1),
}


def fit_baseline(ref: pd.DataFrame, lo: float = 0.02, hi: float = 0.98) -> dict[str, dict[str, float]]:
    """
    Fit reference normalization bounds across pooled reference observations.
    Bounds are empirical quantiles [lo, hi].
    """
    baseline: dict[str, dict[str, float]] = {}
    for raw in RAW_MAP:
        if raw not in ref.columns:
            raise KeyError(f"Reference dataframe missing raw driver column: {raw}")
        s = ref[raw].dropna()
        q_lo = float(s.quantile(lo))
        q_hi = float(s.quantile(hi))
        if q_hi <= q_lo:
            q_hi = q_lo + 1e-6
        baseline[raw] = {"lo": q_lo, "hi": q_hi}
    return baseline


def apply_baseline(df: pd.DataFrame, base: dict[str, dict[str, float]]) -> pd.DataFrame:
    """
    Apply frozen normalization baseline to raw drivers.
    Returns DataFrame with added/computed [heat_v2, water_v2, veg_v2, pollution_v2, exposure_v2].
    """
    out = df.copy()
    for raw, (name, sign) in RAW_MAP.items():
        if raw not in df.columns:
            raise KeyError(f"Dataframe missing raw driver column: {raw}")
        lo = base[raw]["lo"]
        hi = base[raw]["hi"]
        denom = hi - lo if hi != lo else 1e-6
        z = ((df[raw] - lo) / denom).clip(0.0, 1.0)
        out[name] = z if sign > 0 else (1.0 - z)
    return out
