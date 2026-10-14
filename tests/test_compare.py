"""
tests/test_compare.py
─────────────────────
Step 09 tests:
1. Merge integrity: assert that merging v1 and v2 produces no duplicate suffix columns (_x, _y).
2. Row preservation: merged row count matches original v2 panel count.
"""

from pathlib import Path
import pandas as pd
import pytest


@pytest.mark.parametrize("city", ["mumbai", "coimbatore"])
def test_compare_merge_columns(city: str):
    v1_file = Path(f"archive/v1/final/{city}.parquet")
    if not v1_file.exists():
        v1_file = Path(f"data/h3_panel/final/{city}.parquet")
    v2_file = Path(f"data/h3_panel/v2/{city}.parquet")

    assert v1_file.exists(), f"Missing v1 panel: {v1_file}"
    assert v2_file.exists(), f"Missing v2 panel: {v2_file}"

    v1 = pd.read_parquet(v1_file)[["h3_index", "date", "ssi_value"]].rename(columns={"ssi_value": "ssi_v1"})
    v2 = pd.read_parquet(v2_file)

    v1["date"] = pd.to_datetime(v1["date"]).dt.strftime("%Y-%m-01")
    v2["date"] = pd.to_datetime(v2["date"]).dt.strftime("%Y-%m-01")

    m = v2.merge(v1, on=["h3_index", "date"], how="inner", validate="one_to_one")

    # Assert no _x or _y suffix columns
    suffix_cols = [c for c in m.columns if c.endswith(("_x", "_y"))]
    assert len(suffix_cols) == 0, f"Found duplicate suffix columns in merge: {suffix_cols}"

    # Assert exact row count match
    assert len(m) == len(v2), f"Merged length {len(m)} does not equal v2 length {len(v2)}"
