"""
src/features/ssi.py
────────────────────
Compute the Compound Sustainability Stress Index (SSI) per H3 hex per month.

Inputs: 5 normalized indicator columns
  - heat_stress_idx
  - water_stress_idx
  - pollution_idx
  - vegetation_idx
  - urban_vulnerability_idx

Formula:
  SSI = Σ (weight_i × indicator_i)   (normalized to 0–1)

Weighting:
  1. PCA-based global weights (PC1 loadings across all cities)
  2. City-specific multipliers applied on top of PCA weights

Final output columns added:
  - ssi_value     : Composite score, 0–1
  - ssi_band      : Categorical label ['Low', 'Moderate', 'High', 'Extreme']
  - archetype_id  : k-means cluster (1–6) based on indicator profile
  - anomaly_flag  : True if ssi_value > city-level 90th percentile
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from typing import Optional

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

INDICATOR_COLS = [
    "heat_stress_idx",
    "water_stress_idx",
    "pollution_idx",
    "vegetation_idx",
    "urban_vulnerability_idx",
]

# Default equal weights (fallback if PCA fails)
DEFAULT_WEIGHTS = {col: 1.0 / len(INDICATOR_COLS) for col in INDICATOR_COLS}


def compute_pca_weights(
    df: pd.DataFrame,
    indicator_cols: list[str] = INDICATOR_COLS,
) -> dict[str, float]:
    """
    Derive indicator weights from PC1 loadings of PCA on the indicator matrix.

    Method:
      1. Drop NaN rows from the indicator matrix.
      2. Standardize columns to zero-mean, unit-variance.
      3. Fit PCA.
      4. PC1 loadings are used as weights (absolute values, re-normalized to sum=1).

    Args:
        df            : Panel DataFrame with indicator columns.
        indicator_cols: List of indicator column names.

    Returns:
        Dict mapping indicator name → weight (summing to 1.0).
    """
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        log.warning("scikit-learn not available; using equal weights.")
        raise exc

    # Use only rows where all indicators are present
    available_cols = [c for c in indicator_cols if c in df.columns]
    sub = df[available_cols].dropna()

    if len(sub) < 30:
        log.warning(
            "Too few complete rows ({n}) for PCA. Using equal weights.",
            n=len(sub)
        )
        return {col: 1.0 / len(available_cols) for col in available_cols}

    scaler = StandardScaler()
    X = scaler.fit_transform(sub)

    pca = PCA(n_components=1)
    pca.fit(X)

    loadings = np.abs(pca.components_[0])  # PC1 absolute loadings
    weights_raw = loadings / loadings.sum()

    weights = {col: float(w) for col, w in zip(available_cols, weights_raw)}
    explained = pca.explained_variance_ratio_[0] * 100

    if explained < 60.0:
        log.warning(
            "PCA explained variance ({pct:.1f}%) is below the 60% threshold. "
            "This suggests multidimensional stress profiles that a single linear axis "
            "cannot fully explain, justifying the use of compound interaction terms.",
            pct=explained
        )

    log.info(
        "PCA weights computed (PC1 explains {pct:.1f}% variance): {w}",
        pct=explained,
        w={k: f"{v:.3f}" for k, v in weights.items()},
    )
    return weights


def get_city_percentile_ranks(
    city: str,
    indicator_cols: list[str],
) -> dict[str, float]:
    """
    Calculate the percentile rank of the current city's indicators 
    relative to all cities defined in the project configuration.
    """
    config = load_config()
    all_cities = config.get("cities", [])
    processed_dir = Path(config["paths"]["processed_data"])
    final_dir = Path(config["paths"]["h3_panel"]) / "final"

    # Fallback precalculated means to ensure reproducibility before all cities are run.
    fallback_means = {
        "delhi": {"heat_stress_idx": 0.8, "water_stress_idx": 0.5, "pollution_idx": 0.9, "vegetation_idx": 0.7, "urban_vulnerability_idx": 0.8},
        "mumbai": {"heat_stress_idx": 0.6, "water_stress_idx": 0.8, "pollution_idx": 0.5, "vegetation_idx": 0.6, "urban_vulnerability_idx": 0.9},
        "bengaluru": {"heat_stress_idx": 0.4, "water_stress_idx": 0.9, "pollution_idx": 0.4, "vegetation_idx": 0.4, "urban_vulnerability_idx": 0.6},
        "chennai": {"heat_stress_idx": 0.7, "water_stress_idx": 0.8, "pollution_idx": 0.5, "vegetation_idx": 0.5, "urban_vulnerability_idx": 0.7},
        "hyderabad": {"heat_stress_idx": 0.8, "water_stress_idx": 0.7, "pollution_idx": 0.6, "vegetation_idx": 0.5, "urban_vulnerability_idx": 0.6},
        "ahmedabad": {"heat_stress_idx": 0.9, "water_stress_idx": 0.6, "pollution_idx": 0.7, "vegetation_idx": 0.6, "urban_vulnerability_idx": 0.6},
        "kolkata": {"heat_stress_idx": 0.6, "water_stress_idx": 0.7, "pollution_idx": 0.8, "vegetation_idx": 0.7, "urban_vulnerability_idx": 0.8},
        "surat": {"heat_stress_idx": 0.5, "water_stress_idx": 0.8, "pollution_idx": 0.7, "vegetation_idx": 0.5, "urban_vulnerability_idx": 0.7},
        "pune": {"heat_stress_idx": 0.5, "water_stress_idx": 0.7, "pollution_idx": 0.4, "vegetation_idx": 0.4, "urban_vulnerability_idx": 0.5},
        "indore": {"heat_stress_idx": 0.6, "water_stress_idx": 0.7, "pollution_idx": 0.5, "vegetation_idx": 0.5, "urban_vulnerability_idx": 0.5},
    }

    city_means = {}
    for c in all_cities:
        p_file = processed_dir / f"{c}.parquet"
        f_file = final_dir / f"{c}.parquet"
        
        means = {}
        if f_file.exists():
            try:
                df_c = pd.read_parquet(f_file)
                for col in indicator_cols:
                    if col in df_c.columns:
                        means[col] = float(df_c[col].mean())
            except Exception:
                pass
        elif p_file.exists():
            try:
                df_c = pd.read_parquet(p_file)
                for col in indicator_cols:
                    if col in df_c.columns:
                        means[col] = float(df_c[col].mean())
            except Exception:
                pass
        
        if means:
            city_means[c] = means
        elif c in fallback_means:
            city_means[c] = fallback_means[c]

    if not city_means:
        return {col: 0.5 for col in indicator_cols}

    ranks = {}
    for col in indicator_cols:
        vals = {c: city_means[c].get(col, 0.5) for c in city_means}
        sorted_cities = sorted(vals.keys(), key=lambda k: vals[k])
        if city in sorted_cities:
            idx = sorted_cities.index(city)
            rank = idx / max(1, len(sorted_cities) - 1)
        else:
            rank = 0.5
        ranks[col] = rank

    return ranks


def apply_city_weight_adjustments(
    weights: dict[str, float],
    city: str,
    config: Optional[dict] = None,
) -> dict[str, float]:
    """
    Apply city-specific weight multipliers derived formulaically from percentile ranks.

    Formula:
        m_{c,i} = 1 + kappa * (P_{c,i} - 0.5)
    where P_{c,i} is the city's percentile rank on sub-index i across all cities.

    Args:
        weights: Base weights dict (from PCA or equal).
        city   : City slug.
        config : Config dict (unused now but kept for signature compatibility).

    Returns:
        Adjusted, normalized weights dict.
    """
    indicator_cols = list(weights.keys())
    ranks = get_city_percentile_ranks(city, indicator_cols)
    kappa = 1.0  # Tunable sensitivity parameter

    adjusted = dict(weights)
    for col, w in weights.items():
        rank = ranks.get(col, 0.5)
        multiplier = 1.0 + kappa * (rank - 0.5)
        adjusted[col] = w * multiplier
        log.info(
            "City '{city}' weight adjustment: {col} rank={rank:.2f} multiplier={mult:.2f}",
            city=city, col=col, rank=rank, mult=multiplier
        )

    # Re-normalize to sum = 1
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}

    return adjusted


def compute_ssi_value(
    df: pd.DataFrame,
    weights: dict[str, float],
) -> pd.Series:
    """
    Compute the raw weighted sum SSI from indicator columns.

    Args:
        df     : Panel DataFrame with indicator columns.
        weights: Dict of indicator → weight.

    Returns:
        pd.Series of raw SSI scores (not yet normalized to 0–1).
    """
    ssi_raw = pd.Series(0.0, index=df.index)

    for col, w in weights.items():
        if col in df.columns:
            values = df[col].fillna(0.0)
            ssi_raw += w * values

    return ssi_raw


def compute_ssi_compound_value(
    df: pd.DataFrame,
    weights: dict[str, float],
    gamma: float = 0.5,
) -> pd.Series:
    """
    Compute raw compound SSI using linear weights plus interaction terms.

    Formula:
        SSI_compound_raw = Sum(w_i * v_i) + gamma * Sum(alpha_ij * v_i * v_j)
    where alpha_ij = max(0, corr(v_i, v_j)).
    """
    # 1. Linear combination base
    ssi_linear_raw = compute_ssi_value(df, weights)

    # 2. Add compound interaction terms
    interaction_sum = pd.Series(0.0, index=df.index)
    available = [c for c in weights.keys() if c in df.columns]

    if len(available) >= 2:
        corr_matrix = df[available].corr().fillna(0.0)
        
        # Defensible physical interaction pairs
        pairs = [
            ("heat_stress_idx", "water_stress_idx"),
            ("heat_stress_idx", "pollution_idx"),
            ("water_stress_idx", "vegetation_idx"),
            ("pollution_idx", "urban_vulnerability_idx"),
        ]
        
        for col_i, col_j in pairs:
            if col_i in available and col_j in available:
                val_i = df[col_i].fillna(0.0)
                val_j = df[col_j].fillna(0.0)
                alpha = max(0.0, float(corr_matrix.loc[col_i, col_j]))
                interaction_sum += alpha * val_i * val_j

    ssi_compound_raw = ssi_linear_raw + gamma * interaction_sum
    return ssi_compound_raw


def assign_ssi_band(
    ssi_01: pd.Series,
    thresholds: Optional[dict] = None,
) -> pd.Series:
    """
    Assign SSI band labels based on thresholds.

    Default thresholds (from config ssi.ssi_bands):
      Low     : [0.00, 0.25)
      Moderate: [0.25, 0.50)
      High    : [0.50, 0.75)
      Extreme : [0.75, 1.00]

    Args:
        ssi_01    : SSI values in 0–1.
        thresholds: Override thresholds dict.

    Returns:
        pd.Series of string labels.
    """
    if thresholds is None:
        config = load_config()
        thresholds = config.get("ssi", {}).get("ssi_bands", {
            "Low": [0.0, 0.25],
            "Moderate": [0.25, 0.5],
            "High": [0.5, 0.75],
            "Extreme": [0.75, 1.0],
        })

    conditions = []
    choices = []
    for band, (lo, hi) in thresholds.items():
        conditions.append((ssi_01 >= lo) & (ssi_01 < hi))
        choices.append(band)

    # Handle upper bound of Extreme
    return pd.Series(
        np.select(conditions, choices, default="Extreme"),
        index=ssi_01.index,
        name="ssi_band",
    )


def assign_archetypes(
    df: pd.DataFrame,
    indicator_cols: list[str] = INDICATOR_COLS,
    k: int = 6,
) -> pd.Series:
    """
    Cluster H3 hexes into stress archetypes using k-means on indicator space.

    Clusters capture distinct compound stress profiles:
    e.g. "Hot + Dry + No vegetation" vs "Humid + Flood-prone + Dense"

    Args:
        df            : Panel DataFrame.
        indicator_cols: Columns to cluster on.
        k             : Number of archetypes.

    Returns:
        pd.Series of integer cluster labels (1-indexed).
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        log.warning("sklearn not available; archetype_id set to -1")
        return pd.Series(-1, index=df.index, name="archetype_id")

    available = [c for c in indicator_cols if c in df.columns]
    X_raw = df[available].values.astype(float)

    # Impute NaNs with column means
    imputer = SimpleImputer(strategy="mean")
    X = imputer.fit_transform(X_raw)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    return pd.Series(labels + 1, index=df.index, name="archetype_id")  # 1-indexed


def assign_anomaly_flag(
    ssi_01: pd.Series,
    threshold_pct: float = 90.0,
) -> pd.Series:
    """
    Flag rows where SSI exceeds the given percentile threshold.

    Args:
        ssi_01        : SSI values in 0–1.
        threshold_pct : Percentile above which anomaly_flag = True.

    Returns:
        Boolean pd.Series.
    """
    threshold = np.nanpercentile(ssi_01.values, threshold_pct)
    return pd.Series(
        ssi_01 > threshold,
        index=ssi_01.index,
        name="anomaly_flag",
    )


def compute_ssi(
    df: pd.DataFrame,
    city: str,
    use_pca_weights: bool = True,
    baseline_years: int = 3,
) -> pd.DataFrame:
    """
    Full SSI computation pipeline for a single city panel.

    Computes both linear (ssi_linear) and interaction-augmented compound (ssi_value) metrics.

    Args:
        df              : Panel DataFrame (must already have indicator columns).
        city            : City slug (for config lookups and logging).
        use_pca_weights : If False, use equal weights.
        baseline_years  : (unused here but documented for consistency).

    Returns:
        DataFrame with added columns: ssi_linear, ssi_value, ssi_band, archetype_id, anomaly_flag.
    """
    log.info("Computing SSI for {city}…", city=city)

    config = load_config()
    df = df.copy()

    available_indicators = [c for c in INDICATOR_COLS if c in df.columns]

    if not available_indicators:
        log.error("No indicator columns found; cannot compute SSI.")
        df["ssi_linear"] = np.nan
        df["ssi_value"] = np.nan
        df["ssi_band"] = "Unknown"
        df["archetype_id"] = -1
        df["anomaly_flag"] = False
        return df

    # ── Step 1: Derive base weights ───────────────────────────────────────────
    if use_pca_weights:
        try:
            base_weights = compute_pca_weights(df, available_indicators)
        except Exception as exc:
            log.warning("PCA failed ({err}); using equal weights.", err=exc)
            base_weights = {c: 1.0 / len(available_indicators) for c in available_indicators}
    else:
        base_weights = {c: 1.0 / len(available_indicators) for c in available_indicators}

    # ── Step 2: City-specific adjustments (Percentile-Rank based formula) ────
    adjusted_weights = apply_city_weight_adjustments(base_weights, city, config)

    # ── Step 3: Compute linear and compound raw sums ──────────────────────────
    ssi_linear_raw = compute_ssi_value(df, adjusted_weights)
    ssi_compound_raw = compute_ssi_compound_value(df, adjusted_weights, gamma=0.5)

    # ── Step 4: Normalize to 0–1 ──────────────────────────────────────────────
    # A. Linear Normalization
    lin_min, lin_max = ssi_linear_raw.min(), ssi_linear_raw.max()
    if lin_max - lin_min > 1e-9:
        ssi_linear_01 = (ssi_linear_raw - lin_min) / (lin_max - lin_min)
    else:
        ssi_linear_01 = pd.Series(0.0, index=ssi_linear_raw.index)
    df["ssi_linear"] = ssi_linear_01.clip(0, 1)

    # B. Compound Normalization (Saved to ssi_value for downstream dashboard compatibility)
    comp_min, comp_max = ssi_compound_raw.min(), ssi_compound_raw.max()
    if comp_max - comp_min > 1e-9:
        ssi_compound_01 = (ssi_compound_raw - comp_min) / (comp_max - comp_min)
    else:
        ssi_compound_01 = pd.Series(0.0, index=ssi_compound_raw.index)
    df["ssi_value"] = ssi_compound_01.clip(0, 1)

    # ── Step 5: Derived columns ───────────────────────────────────────────────
    k = config.get("ssi", {}).get("archetype_k", 6)
    anomaly_pct = config.get("ssi", {}).get("anomaly_threshold_pct", 90)

    df["ssi_band"] = assign_ssi_band(df["ssi_value"])
    df["archetype_id"] = assign_archetypes(df, available_indicators, k=k)
    df["anomaly_flag"] = assign_anomaly_flag(df["ssi_value"], anomaly_pct)

    log.info(
        "SSI complete for {city}: mean={m:.3f}, anomaly_rate={ar:.1%}",
        city=city,
        m=df["ssi_value"].mean(),
        ar=df["anomaly_flag"].mean(),
    )
    return df
