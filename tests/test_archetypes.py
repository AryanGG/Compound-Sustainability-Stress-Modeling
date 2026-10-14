"""
tests/test_archetypes.py
────────────────────────
Step 12 tests:
1. Each hex has exactly one unique archetype assigned.
2. Results JSON contains silhouette, mean ARI, cluster shares, coherence and null statistics.
"""

from pathlib import Path
import json
import pandas as pd


def test_archetypes_output_integrity():
    json_path = Path("results/archetypes.json")
    csv_path = Path("results/archetypes__hex_assignments.csv")

    assert json_path.exists(), f"Missing {json_path}"
    assert csv_path.exists(), f"Missing {csv_path}"

    with open(json_path) as f:
        meta = json.load(f)

    for field in ["optimal_k", "silhouette", "mean_ari", "cluster_shares", "spatial_coherence_observed", "spatial_coherence_null_mean"]:
        assert field in meta, f"Missing field in archetypes.json: {field}"

    df_assign = pd.read_csv(csv_path)
    assert "h3_index" in df_assign.columns
    assert "archetype_id" in df_assign.columns

    # Each hex has exactly one archetype
    assert df_assign["h3_index"].is_unique, "Hexes are not uniquely assigned to archetypes"
    assert df_assign["archetype_id"].nunique() == meta["optimal_k"]
