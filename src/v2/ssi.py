"""
src/v2/ssi.py
─────────────
Step 08: Compound SSI calculation, non-linear coupling, and band categorizations.
Formula:
    ssi_v2 = ssi_lin_v2 + gamma * omega_v2 * (1 - ssi_lin_v2)
Where:
    omega_v2 = I(hazard_1 >= q_90) * I(hazard_2 >= q_90)
    gamma = 0.30 (coupling scaling parameter)
"""

from __future__ import annotations

from typing import Any, Sequence
import numpy as np
import pandas as pd


def fit_compound(
    ref: pd.DataFrame,
    pair: tuple[str, str] = ("heat_v2", "pollution_v2"),
    q: float = 0.90,
) -> dict[str, float]:
    """Fit quantile thresholds for the compound interaction pair."""
    return {c: float(ref[c].quantile(q)) for c in pair}


def apply_ssi(
    df: pd.DataFrame,
    w: pd.Series,
    thr: dict[str, float],
    gamma: float = 0.30,
) -> pd.DataFrame:
    """
    Apply linear weighting, compound joint-tail activation, and smooth coupling.
    Ensures 0 <= ssi_v2 <= 1 without hard clipping artifacts.
    """
    out = df.copy()
    cols = list(w.index)
    out["ssi_lin_v2"] = (df[cols] * w).sum(axis=1)

    # Compound trigger: all indicators in pair exceed their respective quantile threshold
    condition_list = [df[c] >= t for c, t in thr.items() if c in df.columns]
    if condition_list:
        out["omega_v2"] = np.logical_and.reduce(condition_list).astype(int)
    else:
        out["omega_v2"] = 0

    # Smooth non-linear coupling: ssi_v2 = ssi_lin + gamma * omega * (1 - ssi_lin)
    out["ssi_v2"] = out["ssi_lin_v2"] + gamma * out["omega_v2"] * (1.0 - out["ssi_lin_v2"])
    return out


def fit_cuts(
    ref_ssi: pd.Series,
    qs: Sequence[float] = (0.25, 0.50, 0.75),
) -> list[float]:
    """Fit relative risk band cuts on the reference SSI pool."""
    return [float(ref_ssi.quantile(q)) for q in qs]


def assign_bands(
    s: pd.Series,
    cuts: Sequence[float],
    labels: Sequence[str] = ("Low", "Moderate", "High", "Extreme"),
) -> pd.Series:
    """Assign relative risk bands based on frozen quantile cuts."""
    return pd.cut(
        s,
        bins=[-np.inf, *cuts, np.inf],
        labels=list(labels),
        right=True,
    ).astype(str)
