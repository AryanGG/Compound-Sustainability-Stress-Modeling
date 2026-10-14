"""
tests/test_weighting.py
───────────────────────
Unit tests for Step 07 weighting schemes:
1. Each weight vector sums to 1.0 (±1e-9) and has all non-negative weights.
2. Verified on simulated multi-hazard indicator data.
3. Linear composite sum matches dot product.
"""

import numpy as np
import pandas as pd
from src.v2.weighting import w_equal, w_ewm, w_critic, w_pca, composite, fit_all_weights


def test_weighting_schemes():
    np.random.seed(20260101)
    n = 200
    df = pd.DataFrame({
        "heat_v2": np.random.uniform(0.1, 0.9, n),
        "water_v2": np.random.uniform(0.0, 0.8, n),
        "veg_v2": np.random.uniform(0.2, 0.7, n),
        "pollution_v2": np.random.uniform(0.05, 0.85, n),
        "exposure_v2": np.random.uniform(0.1, 0.6, n),
    })

    schemes, pc1_var = fit_all_weights(df)
    assert 0.0 < pc1_var <= 1.0

    for name, w in schemes.items():
        assert len(w) == 5
        assert (w >= 0.0).all(), f"{name} produced negative weights"
        assert np.isclose(w.sum(), 1.0, atol=1e-9), f"{name} weights do not sum to 1: {w.sum()}"

    # Test composite function
    comp = composite(df, schemes["equal"])
    assert len(comp) == n
    assert np.allclose(comp, df.mean(axis=1))
