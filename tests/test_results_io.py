"""
tests/test_results_io.py
────────────────────────
Test results I/O functionality: dict + DataFrame writing, _meta provenance header, reading back.
"""

import json
from pathlib import Path
import pandas as pd
from src.utils.results_io import save_result


def test_save_result(tmp_path: Path):
    cfg = {"seed": 20260101, "v2": {"seed": 20260101}}
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
    payload = {
        "status": "success",
        "metric": 0.85,
        "table": df,
    }

    out_file = save_result("test_experiment", payload, cfg, out_dir=str(tmp_path))
    assert Path(out_file).exists()

    with open(out_file) as f:
        data = json.load(f)

    assert "_meta" in data
    assert "git_sha" in data["_meta"]
    assert "config_sha256" in data["_meta"]
    assert "created_utc" in data["_meta"]
    assert data["_meta"]["seed"] == 20260101
    assert data["status"] == "success"
    assert data["metric"] == 0.85
    assert "table" in data
    assert "csv" in data["table"]

    # Verify CSV was written and matches
    csv_path = Path(data["table"]["csv"])
    assert csv_path.exists()
    loaded_df = pd.read_csv(csv_path)
    assert len(loaded_df) == 3
    assert list(loaded_df.columns) == ["a", "b"]
