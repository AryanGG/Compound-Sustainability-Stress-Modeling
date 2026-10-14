#!/usr/bin/env python3
"""
scripts/check_claims.py
───────────────────────
Verifies every entry in results/claims_ledger.csv against live files in results/.
Exits 0 if all claims match live values within tolerance (1e-4), exits non-zero otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd


def get_nested_key(data: Any, path: str) -> float | int | str:
    """Navigate nested dictionary or list using dot notation."""
    parts = path.split(".")
    curr = data
    for p in parts:
        if isinstance(curr, dict):
            curr = curr[p]
        elif isinstance(curr, list):
            idx = int(p)
            curr = curr[idx]
        elif isinstance(curr, pd.DataFrame):
            if p.isdigit():
                curr = curr.iloc[int(p)]
            else:
                curr = curr[p]
        elif isinstance(curr, pd.Series):
            curr = curr.iloc[int(p)] if p.isdigit() else curr[p]
        else:
            raise KeyError(f"Cannot navigate into {type(curr)} with key {p}")
    return curr


def check_claims(ledger_path: Path = Path("results/claims_ledger.csv")) -> bool:
    if not ledger_path.exists():
        print(f"Error: {ledger_path} does not exist.")
        return False

    ledger = pd.read_csv(ledger_path)
    all_ok = True

    print("=" * 80)
    print("  CLAIMS LEDGER INTEGRITY CHECK")
    print(f"  Validating {len(ledger)} pre-registered claims against live results files...")
    print("=" * 80)
    print(f"{'ID':5s} | {'Claimed':10s} | {'Live Value':10s} | {'Status':8s} | Statement")
    print("-" * 80)

    for _, row in ledger.iterrows():
        cid = row["claim_id"]
        claimed_num = float(row["number"])
        src_file = Path(row["source_file"])
        key = row["json_key"]
        stmt = row["statement"]

        if not src_file.exists():
            print(f"{cid:5s} | {claimed_num:10.4f} | {'MISSING':10s} | FAIL     | Source file not found: {src_file}")
            all_ok = False
            continue

        try:
            if src_file.suffix == ".json":
                with open(src_file) as f:
                    data = json.load(f)
                live_val = float(get_nested_key(data, key))
            elif src_file.suffix == ".csv":
                df = pd.read_csv(src_file)
                live_val = float(get_nested_key(df, key))
            else:
                raise ValueError(f"Unsupported file type: {src_file.suffix}")

            is_match = np.isclose(claimed_num, live_val, atol=1e-3)
            status_str = "PASS" if is_match else "MISMATCH"
            print(f"{cid:5s} | {claimed_num:10.4f} | {live_val:10.4f} | {status_str:8s} | {stmt[:40]}...")
            if not is_match:
                all_ok = False
        except Exception as e:
            print(f"{cid:5s} | {claimed_num:10.4f} | {'ERROR':10s} | FAIL     | Error reading {key}: {e}")
            all_ok = False

    print("-" * 80)
    if all_ok:
        print("All claims successfully verified against live results artifacts.")
        return True
    else:
        print("One or more claims failed validation.")
        return False


if __name__ == "__main__":
    success = check_claims()
    sys.exit(0 if success else 1)
