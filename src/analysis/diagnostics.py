"""
src/analysis/diagnostics.py
───────────────────────────
Step 06: Two-way additive variance decomposition and monthly-mean spread diagnostics.
Decomposes total indicator variance into:
  - between_month: temporal variance across months
  - between_hex: spatial variance across hex cells
  - residual: hex x month spatio-temporal interaction
"""

from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd


def variance_shares(
    df: pd.DataFrame,
    col: str,
    hexc: str = "h3_index",
    datec: str = "date",
) -> dict[str, float]:
    """
    Compute two-way additive variance decomposition on a balanced panel.
    Returns:
        {'between_month': float, 'between_hex': float, 'residual': float}
    """
    s = df[col].dropna()
    if len(s) == 0:
        return {"between_month": 0.0, "between_hex": 0.0, "residual": 1.0}

    mu = s.mean()
    tot = ((s - mu) ** 2).sum()
    if tot == 0.0:
        return {"between_month": 0.0, "between_hex": 0.0, "residual": 0.0}

    sub = df[[hexc, datec, col]].dropna()
    m = sub.groupby(datec)[col].agg(["mean", "size"])
    h = sub.groupby(hexc)[col].agg(["mean", "size"])

    sm = float((m["size"] * (m["mean"] - mu) ** 2).sum() / tot)
    sh = float((h["size"] * (h["mean"] - mu) ** 2).sum() / tot)
    residual = float(max(0.0, 1.0 - sm - sh))

    return {
        "between_month": round(sm, 4),
        "between_hex": round(sh, 4),
        "residual": round(residual, 4),
    }


def monthly_mean_spread(df: pd.DataFrame, col: str, datec: str = "date") -> float:
    """
    Compute spread of monthly means: max(mean_m) - min(mean_m).
    """
    m = df.groupby(datec)[col].mean()
    return float(round(m.max() - m.min(), 4))
