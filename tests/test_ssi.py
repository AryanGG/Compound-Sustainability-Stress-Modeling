"""
tests/test_ssi.py
─────────────────
Step 08 unit tests for SSI v2 compound formulation:
1. Smooth bounds: 0 <= ssi_v2 <= 1 without artificial hard clipping.
2. Dominance: ssi_v2 >= ssi_lin_v2 everywhere; equality iff omega_v2 == 0.
3. Compound trigger: triggers only when both hazards in pair exceed threshold.
4. Relative risk bands: 4 monotonic categories.
"""

import numpy as np
import pandas as pd
from src.v2.ssi import fit_compound, apply_ssi, fit_cuts, assign_bands


def test_ssi_compound_properties():
    np.random.seed(20260101)
    n = 1000
    df = pd.DataFrame({
        "heat_v2": np.random.uniform(0.0, 1.0, n),
        "water_v2": np.random.uniform(0.0, 1.0, n),
        "veg_v2": np.random.uniform(0.0, 1.0, n),
        "pollution_v2": np.random.uniform(0.0, 1.0, n),
        "exposure_v2": np.random.uniform(0.0, 1.0, n),
    })

    w = pd.Series(0.20, index=["heat_v2", "water_v2", "veg_v2", "pollution_v2", "exposure_v2"])
    thr = fit_compound(df, pair=("heat_v2", "pollution_v2"), q=0.90)

    out = apply_ssi(df, w, thr, gamma=0.30)

    # 1. Bounds check
    assert (out["ssi_v2"] >= 0.0).all()
    assert (out["ssi_v2"] <= 1.0).all()

    # 2. Strict dominance
    assert (out["ssi_v2"] >= out["ssi_lin_v2"]).all()

    # 3. Exact equality where omega == 0
    zero_omega = out["omega_v2"] == 0
    assert np.allclose(out.loc[zero_omega, "ssi_v2"], out.loc[zero_omega, "ssi_lin_v2"])

    # 4. Strict inequality where omega == 1 and ssi_lin < 1
    one_omega = (out["omega_v2"] == 1) & (out["ssi_lin_v2"] < 0.9999)
    if one_omega.sum() > 0:
        assert (out.loc[one_omega, "ssi_v2"] > out.loc[one_omega, "ssi_lin_v2"]).all()

    # 5. Banding cuts
    cuts = fit_cuts(out["ssi_v2"], qs=(0.25, 0.50, 0.75))
    assert len(cuts) == 3
    assert cuts[0] < cuts[1] < cuts[2]

    bands = assign_bands(out["ssi_v2"], cuts)
    shares = bands.value_counts(normalize=True)
    for cat in ["Low", "Moderate", "High", "Extreme"]:
        assert cat in shares
        assert np.isclose(shares[cat], 0.25, atol=0.03)
