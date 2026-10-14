#!/usr/bin/env python3
"""
audit/schema_check.py
─────────────────────
Schema and integrity checker for v2 panel parquet files (data/h3_panel/v2/{city}.parquet).
Validates:
- Required columns present
- No duplicate (h3_index, date)
- Balanced panel (rows == n_hexes * n_months)
- No NaN in index or SSI columns
- Date is month-start
- 0 <= ssi_v2 <= 1
"""

from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd
import yaml

REQUIRED_COLUMNS = [
    "h3_index",
    "date",
    "heat_v2",
    "water_v2",
    "veg_v2",
    "pollution_v2",
    "exposure_v2",
    "ssi_lin_v2",
    "omega_v2",
    "ssi_v2",
    "ssi_band_v2",
]


def check_city(city: str, base_dir: Path) -> tuple[bool, int, int, int, str]:
    file_path = base_dir / f"{city}.parquet"
    if not file_path.exists():
        return False, 0, 0, 0, f"File not found: {file_path}"

    df = pd.read_parquet(file_path)

    # 1. Column check
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return False, len(df), 0, 0, f"Missing columns: {missing}"

    # 2. Duplicate check
    dups = df.duplicated(subset=["h3_index", "date"]).sum()
    if dups > 0:
        return False, len(df), 0, 0, f"{dups} duplicate (h3_index, date) rows"

    # 3. Balanced panel check
    n_hex = df["h3_index"].nunique()
    n_months = df["date"].nunique()
    expected_rows = n_hex * n_months
    if len(df) != expected_rows:
        return False, len(df), n_hex, n_months, f"Unbalanced: {len(df)} != {n_hex} x {n_months}"

    # 4. No NaN in index and SSI columns
    check_cols = [c for c in REQUIRED_COLUMNS if c != "ssi_band_v2"]
    na_counts = df[check_cols].isna().sum()
    bad_nas = na_counts[na_counts > 0]
    if not bad_nas.empty:
        return False, len(df), n_hex, n_months, f"NaNs found: {bad_nas.to_dict()}"

    # 5. Date is month-start (YYYY-MM-01)
    dates = pd.to_datetime(df["date"])
    if not (dates.dt.day == 1).all():
        return False, len(df), n_hex, n_months, "Dates are not month-start (day != 1)"

    # 6. Range: 0 <= ssi_v2 <= 1
    if not ((df["ssi_v2"] >= 0.0) & (df["ssi_v2"] <= 1.0)).all():
        min_v, max_v = df["ssi_v2"].min(), df["ssi_v2"].max()
        return False, len(df), n_hex, n_months, f"ssi_v2 out of [0, 1] range: [{min_v}, {max_v}]"

    return True, len(df), n_hex, n_months, "OK"


def main():
    cfg_path = Path("config.yml")
    if not cfg_path.exists():
        print("config.yml not found.")
        sys.exit(1)

    with open(cfg_path) as f:
        cfg = yaml.safe_load(f)

    v2_cfg = cfg.get("v2", {})
    cities = v2_cfg.get("cities", ["mumbai", "coimbatore"])
    base_dir = Path(v2_cfg.get("paths", {}).get("v2", "data/h3_panel/v2"))

    print("=" * 75)
    print("  SCHEMA CHECK: v2 H3 Panels")
    print(f"  Target directory: {base_dir}")
    print("=" * 75)
    print(f"{'City':15s} | {'Rows':10s} | {'Hexes':8s} | {'Months':8s} | {'Status':8s} | Details")
    print("-" * 75)

    all_ok = True
    for c in cities:
        ok, rows, hexes, months, detail = check_city(c, base_dir)
        status_str = "PASS" if ok else "FAIL"
        print(f"{c:15s} | {rows:10,d} | {hexes:8,d} | {months:8,d} | {status_str:8s} | {detail}")
        if not ok:
            all_ok = False

    print("-" * 75)
    if not all_ok:
        print("Schema check FAILED (expected until Step 08 generates v2 panels).")
        sys.exit(1)
    else:
        print("All v2 panels PASSED schema check.")
        sys.exit(0)


if __name__ == "__main__":
    main()
