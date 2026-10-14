"""
tests/test_indices.py
─────────────────────
Step 06 unit tests for normalization and index properties:
(a) monotonic in raw: higher raw -> higher index (except veg)
(b) veg inverted: higher NDVI -> lower veg_v2 (less vegetative stress)
(c) pooled baseline invariance: applying a baseline fitted elsewhere does not adapt to city-local data
"""

import numpy as np
import pandas as pd
from src.v2.indices import fit_baseline, apply_baseline, RAW_MAP, IDX_COLS


def test_monotonicity_and_inversion():
    n = 100
    df = pd.DataFrame({
        "heat_raw": np.linspace(20.0, 45.0, n),
        "water_raw": np.linspace(0.0, 300.0, n),
        "veg_raw": np.linspace(-0.2, 0.8, n),
        "pollution_raw": np.linspace(20.0, 200.0, n),
        "exposure_raw": np.linspace(0.0, 1.0, n),
    })

    base = fit_baseline(df, lo=0.05, hi=0.95)
    out = apply_baseline(df, base)

    # All indices in [0, 1]
    for c in IDX_COLS:
        assert out[c].min() >= 0.0
        assert out[c].max() <= 1.0

    # (a) monotonic in raw for positive drivers
    assert np.all(np.diff(out["heat_v2"]) >= 0.0), "heat_v2 not monotonic increasing"
    assert np.all(np.diff(out["water_v2"]) >= 0.0), "water_v2 not monotonic increasing"
    assert np.all(np.diff(out["pollution_v2"]) >= 0.0), "pollution_v2 not monotonic increasing"
    assert np.all(np.diff(out["exposure_v2"]) >= 0.0), "exposure_v2 not monotonic increasing"

    # (b) veg inverted: higher NDVI -> lower veg stress
    assert np.all(np.diff(out["veg_v2"]) <= 0.0), "veg_v2 not inverted (should decrease as veg_raw increases)"


def test_baseline_invariance():
    # City A (e.g. desert regime: higher heat)
    city_a = pd.DataFrame({
        "heat_raw": [35.0, 40.0, 45.0],
        "water_raw": [100.0, 150.0, 200.0],
        "veg_raw": [0.1, 0.2, 0.3],
        "pollution_raw": [50.0, 60.0, 70.0],
        "exposure_raw": [0.5, 0.6, 0.7],
    })

    # City B (e.g. coastal regime: lower heat)
    city_b = pd.DataFrame({
        "heat_raw": [25.0, 27.0, 30.0],
        "water_raw": [50.0, 80.0, 100.0],
        "veg_raw": [0.5, 0.6, 0.7],
        "pollution_raw": [30.0, 40.0, 50.0],
        "exposure_raw": [0.3, 0.4, 0.5],
    })

    # Fit baseline on pooled [city_a, city_b]
    pooled = pd.concat([city_a, city_b], ignore_index=True)
    frozen_base = fit_baseline(pooled, lo=0.0, hi=1.0)

    # Applying the frozen baseline to city B alone yields identical results regardless of city B's local distribution
    out_b1 = apply_baseline(city_b, frozen_base)

    # If city B is evaluated alongside duplicate city B rows, frozen baseline outputs remain identical
    city_b_doubled = pd.concat([city_b, city_b], ignore_index=True)
    out_b2 = apply_baseline(city_b_doubled, frozen_base)

    for c in IDX_COLS:
        assert np.allclose(out_b1[c].values, out_b2[c].iloc[:3].values)
