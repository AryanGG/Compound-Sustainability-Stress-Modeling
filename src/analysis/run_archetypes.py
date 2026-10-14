"""
src/analysis/run_archetypes.py
──────────────────────────────
Step 12: Hex-level stress typology (archetypes).
Extracts hex-level features:
  - Mean SSI v2
  - Seasonal amplitude of SSI
  - Mean heat_v2
  - Mean veg_v2
  - Exposure_v2
  - Compound event frequency (mean omega_v2)
Evaluates k in [2..8] using silhouette score and 50-bootstrap ARI stability.
Computes spatial coherence using H3 topological adjacency vs. permutation null.
Produces results/archetypes.json and results/archetypes__hex_assignments.csv.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import h3
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler
import yaml

from src.utils.logger import get_logger
from src.utils.results_io import save_result

log = get_logger("run_archetypes")


def extract_hex_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract stationary hex-level feature profiles."""
    df["_month"] = pd.to_datetime(df["date"]).dt.month

    # 1. Base means per hex
    base = df.groupby("h3_index").agg(
        mean_ssi=("ssi_v2", "mean"),
        mean_heat=("heat_v2", "mean"),
        mean_veg=("veg_v2", "mean"),
        mean_exposure=("exposure_v2", "mean"),
        compound_freq=("omega_v2", "mean"),
    )

    # 2. Seasonal amplitude of monthly SSI
    month_means = df.groupby(["h3_index", "_month"])["ssi_v2"].mean().unstack("_month")
    amplitude = (month_means.max(axis=1) - month_means.min(axis=1)).rename("seasonal_amplitude")

    hex_features = base.join(amplitude).dropna()
    return hex_features


def evaluate_k_range(
    X_scaled: np.ndarray,
    k_range: range = range(2, 9),
    n_bootstrap: int = 50,
    seed: int = 20260101,
) -> dict[int, dict[str, float]]:
    """Evaluate k=2..8 via silhouette score and bootstrap Adjusted Rand Index."""
    results = {}
    rng = np.random.RandomState(seed)
    n = len(X_scaled)

    for k in k_range:
        km = KMeans(n_clusters=k, n_init=20, random_state=seed)
        labels = km.fit_predict(X_scaled)
        sil = float(silhouette_score(X_scaled, labels))

        # Check cluster size distribution
        counts = pd.Series(labels).value_counts(normalize=True)
        min_cluster_share = float(counts.min())

        # Bootstrap stability
        ari_scores = []
        for _ in range(n_bootstrap):
            idx = rng.choice(n, size=n, replace=True)
            km_boot = KMeans(n_clusters=k, n_init=10, random_state=rng.randint(1, 100000))
            km_boot.fit(X_scaled[idx])
            # Assign full dataset by nearest centroid
            boot_labels = km_boot.predict(X_scaled)
            ari_scores.append(adjusted_rand_score(labels, boot_labels))

        mean_ari = float(np.mean(ari_scores))

        results[k] = {
            "silhouette": round(sil, 4),
            "mean_ari": round(mean_ari, 4),
            "min_cluster_share": round(min_cluster_share, 4),
            "qualifies": bool(mean_ari >= 0.70 and min_cluster_share >= 0.03),
        }

    return results


def compute_spatial_coherence(
    labels: pd.Series,
    n_permutations: int = 500,
    seed: int = 20260101,
) -> tuple[float, float, float]:
    """
    Compute fraction of adjacent hex pairs sharing the same archetype label,
    compared against a random permutation null distribution.
    """
    hex_list = list(labels.index)
    hex_to_label = labels.to_dict()

    # Form unique adjacent pairs
    adjacent_pairs = set()
    for h in hex_list:
        neighbors = h3.grid_disk(h, 1)
        for nbr in neighbors:
            if nbr != h and nbr in hex_to_label:
                pair = tuple(sorted([h, nbr]))
                adjacent_pairs.add(pair)

    if not adjacent_pairs:
        return 0.0, 0.0, 0.0

    # Observed concordance
    same_count = sum(1 for h1, h2 in adjacent_pairs if hex_to_label[h1] == hex_to_label[h2])
    observed_coherence = float(same_count / len(adjacent_pairs))

    # Permutation null
    rng = np.random.RandomState(seed)
    label_vals = labels.values
    null_coherences = []
    for _ in range(n_permutations):
        shuffled = rng.permutation(label_vals)
        perm_map = dict(zip(hex_list, shuffled))
        perm_same = sum(1 for h1, h2 in adjacent_pairs if perm_map[h1] == perm_map[h2])
        null_coherences.append(perm_same / len(adjacent_pairs))

    null_mean = float(np.mean(null_coherences))
    null_p95 = float(np.percentile(null_coherences, 95))

    return round(observed_coherence, 4), round(null_mean, 4), round(null_p95, 4)


def label_clusters(feature_df: pd.DataFrame, cluster_series: pd.Series) -> dict[int, str]:
    """Generate descriptive cluster names from feature means."""
    df = feature_df.copy()
    df["cluster"] = cluster_series
    means = df.groupby("cluster").mean()

    names = {}
    for cl in sorted(means.index):
        row = means.loc[cl]
        # Profile descriptor based on distinguishing traits
        heat_tag = "High Heat" if row["mean_heat"] > 0.50 else "Moderate Heat"
        veg_tag = "Low Canopy" if row["mean_veg"] > 0.45 else "Green Canopy"
        exp_tag = "Dense Built" if row["mean_exposure"] > 0.40 else "Suburban/Open"
        names[cl] = f"Cluster {cl}: {exp_tag} / {veg_tag} / {heat_tag}"
    return names


def run_archetypes(cfg: dict[str, Any]) -> dict[str, Any]:
    v2_cfg = cfg.get("v2", {})
    results_dir = v2_cfg.get("paths", {}).get("results", "results")
    v2_dir = Path(v2_cfg.get("paths", {}).get("v2", "data/h3_panel/v2"))
    ref_cities = v2_cfg.get("reference_cities", ["mumbai", "coimbatore"])

    # Load pooled reference v2 panels
    dfs = [pd.read_parquet(v2_dir / f"{c}.parquet") for c in ref_cities]
    pooled_df = pd.concat(dfs, ignore_index=True)

    hex_features = extract_hex_features(pooled_df)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(hex_features.values)

    # Evaluate k=2..8
    k_eval = evaluate_k_range(X_scaled, k_range=range(2, 9))

    # Selection rule: highest silhouette among k with ARI >= 0.70 and min_cluster >= 3%
    qualifying_k = [k for k, metrics in k_eval.items() if metrics["qualifies"]]

    if qualifying_k:
        best_k = max(qualifying_k, key=lambda k: k_eval[k]["silhouette"])
        typology_found = True
    else:
        # Fallback to highest silhouette overall if none strictly passed ARI threshold
        best_k = max(k_eval.keys(), key=lambda k: k_eval[k]["silhouette"])
        typology_found = False
        log.warning("No k met strict ARI >= 0.70 threshold. Reporting diagnostic best-k with caveat.")

    # Fit optimal model
    km_final = KMeans(n_clusters=best_k, n_init=30, random_state=20260101)
    labels = km_final.fit_predict(X_scaled)
    cluster_series = pd.Series(labels, index=hex_features.index, name="archetype_id")

    # Cluster sizes
    sizes = cluster_series.value_counts(normalize=True).round(4).to_dict()

    # Spatial coherence
    obs_coh, null_mean, null_p95 = compute_spatial_coherence(cluster_series)

    # Cluster descriptions
    cluster_names = label_clusters(hex_features, cluster_series)

    # Assignments table
    assignments_df = hex_features.copy()
    assignments_df["archetype_id"] = cluster_series
    assignments_df["archetype_label"] = assignments_df["archetype_id"].map(cluster_names)

    payload = {
        "status": "typology_found" if typology_found else "diagnostic_typology",
        "optimal_k": best_k,
        "silhouette": k_eval[best_k]["silhouette"],
        "mean_ari": k_eval[best_k]["mean_ari"],
        "cluster_shares": sizes,
        "cluster_names": cluster_names,
        "spatial_coherence_observed": obs_coh,
        "spatial_coherence_null_mean": null_mean,
        "spatial_coherence_null_p95": null_p95,
        "k_evaluation": k_eval,
        "hex_assignments": assignments_df.reset_index(),
    }

    save_result("archetypes", payload, cfg, out_dir=results_dir)

    print("=" * 75)
    print("  STEP 12 HEX-LEVEL STRESS TYPOLOGY (ARCHETYPES)")
    print("=" * 75)
    print(f"  Selected k                 : {best_k} (Silhouette = {k_eval[best_k]['silhouette']:.4f}, Mean ARI = {k_eval[best_k]['mean_ari']:.4f})")
    print(f"  Spatial Coherence Observed : {obs_coh*100:.1f}% (Null: {null_mean*100:.1f}%, 95th: {null_p95*100:.1f}%)")
    print("  Cluster Profiles:")
    for cl, desc in cluster_names.items():
        share = sizes.get(cl, 0.0) * 100
        print(f"    - {desc} ({share:.1f}% of cells)")
    print("=" * 75)
    log.info(f"Saved archetype results -> {results_dir}/archetypes.json")

    return payload


def main():
    cfg = yaml.safe_load(open("config.yml"))
    run_archetypes(cfg)


if __name__ == "__main__":
    main()
