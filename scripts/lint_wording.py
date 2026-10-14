#!/usr/bin/env python3
"""
scripts/lint_wording.py
───────────────────────
Lints documentation, slides, and dashboard text against forbidden words from Rule G10:
  - '100% verified'
  - 'zero-hallucination'
  - 'guarantee'
  - 'proves'
  - 'proven'
  - 'completely robust'
  - 'standard threshold'
  - 'validated' (allowed only if citing a ledger id like C01..C16 or [V1..V6])
Exits 0 on clean scan, exits non-zero if violations are found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    re.compile(r"100%\s*verified", re.IGNORECASE),
    re.compile(r"zero-hallucination", re.IGNORECASE),
    re.compile(r"\bguarantee\b", re.IGNORECASE),
    re.compile(r"\bproves\b", re.IGNORECASE),
    re.compile(r"\bproven\b", re.IGNORECASE),
    re.compile(r"completely\s+robust", re.IGNORECASE),
    re.compile(r"standard\s+threshold", re.IGNORECASE),
]

# 'validated' allowed only if citing a claim or validation id
VALIDATED_PATTERN = re.compile(r"\bvalidated\b", re.IGNORECASE)
CITATION_PATTERN = re.compile(r"(C\d{2}|V[1-6]|claims_ledger|ledger)", re.IGNORECASE)

SCAN_PATHS = ["docs", "slides", "dashboard"]


def lint_file(file_path: Path) -> list[str]:
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Could not read {file_path}: {e}"]

    lines = content.splitlines()
    for line_num, line in enumerate(lines, 1):
        # Check forbidden patterns
        for pat in FORBIDDEN_PATTERNS:
            match = pat.search(line)
            if match:
                violations.append(
                    f"{file_path}:{line_num}: Forbidden wording '{match.group(0)}' found in line: {line.strip()}"
                )

        # Check 'validated'
        val_match = VALIDATED_PATTERN.search(line)
        if val_match:
            if not CITATION_PATTERN.search(line):
                violations.append(
                    f"{file_path}:{line_num}: 'validated' used without citing ledger ID (C01..C16 or V1..V6): {line.strip()}"
                )

    return violations


def main():
    print("=" * 80)
    print("  WORDING LINT (RULE G10 AND INTEGRITY SCAN)")
    print("=" * 80)

    all_violations: list[str] = []
    for p_str in SCAN_PATHS:
        p = Path(p_str)
        if not p.exists():
            continue
        for ext in ["*.md", "*.html", "*.txt", "*.json", "*.py"]:
            for f in p.rglob(ext):
                # Skip raw audit artifacts from Step 01
                if "audit/data_audit_" in str(f) or "archive/" in str(f):
                    continue
                v = lint_file(f)
                all_violations.extend(v)

    if all_violations:
        print(f"FAILED: Found {len(all_violations)} wording violations:")
        for viol in all_violations:
            print(f"  [-] {viol}")
        sys.exit(1)
    else:
        print("PASS: Clean wording scan across documentation, slides, and dashboard.")
        sys.exit(0)


if __name__ == "__main__":
    main()
