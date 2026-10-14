"""
src/v2/weighting.py
───────────────────
Step 07: Weighting schemes for multi-hazard composite indicators.
Implements:
  1. Equal Weighting (w_equal)
  2. Entropy Weight Method (w_ewm)
  3. CRITIC method (w_critic)
  4. Principal Component Analysis (w_pca)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def w_equal(X: pd.DataFrame) -> pd.Series:
    """Equal weights across all indicators."""
    return pd.Series(1.0 / X.shape[1], index=X.columns, name="equal")


def w_ewm(X: pd.DataFrame, eps: float = 1e-12) -> pd.Series:
    """
    Entropy Weight Method (EWM).
    Measures information entropy; lower entropy -> higher information dispersion -> higher weight.
    """
    P = (X + eps) / (X + eps).sum(axis=0)
    e = -(P * np.log(P)).sum(axis=0) / np.log(len(X))
    d = 1.0 - e
    weights = d / d.sum()
    return pd.Series(weights, index=X.columns, name="ewm")


def w_critic(X: pd.DataFrame) -> pd.Series:
    """
    CRITIC Method (Criteria Importance Through Intercriteria Correlation).
    Balances contrast intensity (std) with conflict between indicators (1 - correlation).
    """
    s = X.std(ddof=0)
    r = X.corr().fillna(0.0)
    # Conflict = sum(1 - r_jk)
    conflict = (1.0 - r).sum(axis=1)
    c = s * conflict
    weights = c / c.sum()
    return pd.Series(weights, index=X.columns, name="critic")


def w_pca(X: pd.DataFrame) -> tuple[pd.Series, float]:
    """
    Principal Component Analysis (PC1 absolute loadings).
    Returns (weights pd.Series, pc1_explained_variance float).
    """
    std = X.std(ddof=0).replace(0.0, 1.0)
    Z = (X - X.mean()) / std
    _, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
    loadings = np.abs(Vt[0])
    weights = loadings / loadings.sum()
    explained_var = float(S[0] ** 2 / (S ** 2).sum())
    return pd.Series(weights, index=X.columns, name="pca"), explained_var


def fit_all_weights(X: pd.DataFrame) -> tuple[dict[str, pd.Series], float]:
    """
    Fit all four schemes on indicator DataFrame X.
    Returns (dict of scheme_name -> weight_series, pc1_explained).
    """
    w_eq = w_equal(X)
    w_e = w_ewm(X)
    w_cr = w_critic(X)
    w_pc, pc1_var = w_pca(X)

    return {
        "equal": w_eq,
        "ewm": w_e,
        "critic": w_cr,
        "pca": w_pc,
    }, pc1_var


def composite(df: pd.DataFrame, w: pd.Series) -> pd.Series:
    """Calculate linear composite index from weights."""
    cols = list(w.index)
    return (df[cols] * w).sum(axis=1)
