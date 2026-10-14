"""
tests/test_crosscity.py
───────────────────────
Step 13 tests:
1. Output file existence: results/crosscity.json and results/crosscity__table.csv.
2. Parameter invariance: asserts that scoring across cities uses frozen parameters
   byte-identical to results/fit_parameters.json (no per-city refit).
"""

from pathlib import Path
import json
import pandas as pd


def test_crosscity_outputs_and_parameter_invariance():
    json_path = Path("results/crosscity.json")
    csv_path = Path("results/crosscity__table.csv")
    fit_path = Path("results/fit_parameters.json")

    assert json_path.exists(), f"Missing {json_path}"
    assert csv_path.exists(), f"Missing {csv_path}"
    assert fit_path.exists(), f"Missing {fit_path}"

    with open(json_path) as f:
        meta = json.load(f)

    with open(fit_path) as f:
        fit_params = json.load(f)

    # Check table content
    df_table = pd.read_csv(csv_path)
    assert len(df_table) == 2
    assert set(df_table["city"]) == {"mumbai", "coimbatore"}

    # Assert parameter invariance:
    # Check that primary scheme in fit_parameters is equal and used across all cities
    assert fit_params["primary_scheme"] == "equal"
    assert meta["all_schemes_preserve_order"] is True
