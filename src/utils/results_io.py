"""
src/utils/results_io.py
───────────────────────
Results I/O utility ensuring all artifacts carry git SHA, config hash, and timestamp.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _sha(path: str | Path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def save_result(name: str, payload: dict[str, Any], config: dict[str, Any], out_dir: str = "results") -> str:
    """
    DataFrames -> {name}__{key}.csv ; everything else -> {name}.json with provenance header.
    """
    os.makedirs(out_dir, exist_ok=True)
    git_rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    config_hash = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()

    meta = {
        "git_sha": git_rev,
        "config_sha256": config_hash,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "seed": config.get("seed") or config.get("v2", {}).get("seed"),
    }

    body: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, pd.DataFrame):
            p = f"{out_dir}/{name}__{k}.csv"
            v.to_csv(p, index=False)
            body[k] = {"csv": p, "rows": len(v)}
        elif isinstance(v, pd.Series):
            body[k] = v.to_dict()
        elif isinstance(v, np.generic):
            body[k] = v.item()
        else:
            body[k] = v

    path = f"{out_dir}/{name}.json"
    with open(path, "w") as fh:
        json.dump({"_meta": meta, **body}, fh, indent=2, default=str)
    return path
