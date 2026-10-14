"""
src/features/proper_ssi.py
───────────────────────────
Complete, physically grounded Compound Sustainability Stress Index (JT-SSI) pipeline.
Replaces compressed per-calendar-month normalization with absolute physical scaling:
  1. Heat Stress: Rothfusz Heat Index (°C) blended with MODIS LST (°C)
  2. Water Stress: Multi-variable soil moisture + precipitation deficit
  3. Pollution: Logarithmic scaling anchored to NAAQS & acute smog levels
  4. Vegetation: Inverse photosynthetic canopy density (Sentinel-2 NDVI)
  5. Urban Vulnerability: Built footprint and impervious surface density
  6. Weighting: Information Entropy Weight Method (EWM) with physical balancing
  7. Compound Coupling: Bivariate Joint-Tail Risk Amplifier (JT-SSI, gamma=0.3)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.features.heat_stress import compute_relative_humidity, compute_heat_index
from src.utils.logger import get_logger

log = get_logger(__name__)

INDICATOR_COLS = [
    "heat_stress_idx",
    "water_stress_idx",
    "pollution_idx",
    "vegetation_idx",
    "urban_vulnerability_idx",
]

PHYSICAL_PAIRS = [
    ("heat_stress_idx", "water_stress_idx"),
    ("heat_stress_idx", "pollution_idx"),
    ("water_stress_idx", "vegetation_idx"),
    ("pollution_idx", "urban_vulnerability_idx"),
]


def compute_physical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all 5 physical stress indicators with unmasked ground-truth dynamics."""
    df = df.copy()

    # 1. Heat Stress Index: Ambient Heat Index + MODIS LST
    temp = df["temp_mean_c"].fillna(df["temp_mean_c"].median())
    dew = df["dewpoint_mean_c"].fillna(temp - 10.0)
    rh = compute_relative_humidity(temp, dew)
    hi = compute_heat_index(temp, rh)
    hi_norm = ((hi - 20.0) / 25.0).clip(0.0, 1.0)

    if "lst_c" in df.columns and df["lst_c"].notna().sum() > 0:
        lst = df["lst_c"].fillna(temp + 5.0)
        lst_norm = ((lst - 15.0) / 30.0).clip(0.0, 1.0)
        df["heat_stress_idx"] = (0.70 * hi_norm + 0.30 * lst_norm).clip(0.0, 1.0)
    else:
        df["heat_stress_idx"] = hi_norm.clip(0.0, 1.0)

    # 2. Water Stress Index: Volumetric soil moisture + precipitation deficit
    soil = df["soil_moisture"].fillna(0.15) if "soil_moisture" in df.columns else pd.Series(0.15, index=df.index)
    precip = df["precip_sum_mm"].fillna(0.0) if "precip_sum_mm" in df.columns else pd.Series(0.0, index=df.index)
    soil_deficit = ((0.28 - soil) / 0.22).clip(0.0, 1.0)
    precip_deficit = (1.0 - (precip / 150.0)).clip(0.0, 1.0)
    df["water_stress_idx"] = (0.60 * soil_deficit + 0.40 * precip_deficit).clip(0.0, 1.0)

    # 3. Air Pollution Index: Logarithmic scaling
    if "pm25" in df.columns:
        pm = df["pm25"].fillna(df["pm25"].median())
        df["pollution_idx"] = (np.log1p(pm) / np.log1p(350.0)).clip(0.0, 1.0)
    else:
        df["pollution_idx"] = 0.50

    # 4. Vegetation Degradation Index: Inverse NDVI
    if "ndvi" in df.columns:
        ndvi = df["ndvi"].fillna(df["ndvi"].median())
        df["vegetation_idx"] = (1.0 - ((ndvi - 0.05) / 0.65)).clip(0.0, 1.0)
    else:
        df["vegetation_idx"] = 0.50

    # 5. Urban Structural Vulnerability: Built footprint + green canopy deficit
    built = df["built_up_fraction"].fillna(0.5) if "built_up_fraction" in df.columns else pd.Series(0.5, index=df.index)
    green = df["green_space_fraction"].fillna(0.1) if "green_space_fraction" in df.columns else pd.Series(0.1, index=df.index)
    df["urban_vulnerability_idx"] = (0.70 * built + 0.30 * (1.0 - green)).clip(0.0, 1.0)

    return df


def compute_entropy_weights(df: pd.DataFrame, cols: list[str] = INDICATOR_COLS) -> dict[str, float]:
    """Compute objective Entropy Weight Method (EWM) weights."""
    sub = df[cols].dropna()
    if len(sub) < 30:
        return {c: 1.0 / len(cols) for c in cols}

    X = sub.values.astype(float)
    # Scale to positive range
    X_scaled = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + 1e-9) + 1e-4
    p = X_scaled / X_scaled.sum(axis=0)
    k = 1.0 / np.log(len(sub))
    entropy = -k * np.sum(p * np.log(p), axis=0)
    divergence = np.maximum(1.0 - entropy, 1e-4)
    weights = divergence / divergence.sum()
    return {c: float(w) for c, w in zip(cols, weights)}


def compute_joint_tail_amplifier(
    df: pd.DataFrame,
    pairs: list[tuple[str, str]] = PHYSICAL_PAIRS,
    quantile_thresh: float = 0.75,
) -> pd.Series:
    """Compute Bivariate Joint Tail Risk Amplifier Omega."""
    omega = pd.Series(0.0, index=df.index, name="omega_compound")
    quantiles = {}
    for col in set([p[0] for p in pairs] + [p[1] for p in pairs]):
        if col in df.columns:
            s = df[col].dropna()
            quantiles[col] = float(s.quantile(quantile_thresh)) if len(s) > 0 else 0.75

    for c1, c2 in pairs:
        if c1 in df.columns and c2 in df.columns:
            val_1 = df[c1].fillna(0.0).clip(lower=0.0)
            val_2 = df[c2].fillna(0.0).clip(lower=0.0)
            q1 = quantiles.get(c1, 0.75)
            q2 = quantiles.get(c2, 0.75)
            mask = (val_1 > q1) & (val_2 > q2)
            geom_mean = np.sqrt(val_1 * val_2)
            omega += mask.astype(float) * geom_mean

    return omega


def assign_bands(ssi_series: pd.Series) -> pd.Series:
    """Categorize SSI into Low, Moderate, High, Extreme bands."""
    conditions = [
        ssi_series < 0.25,
        (ssi_series >= 0.25) & (ssi_series < 0.50),
        (ssi_series >= 0.50) & (ssi_series < 0.75),
        ssi_series >= 0.75,
    ]
    choices = ["Low", "Moderate", "High", "Extreme"]
    return pd.Series(np.select(conditions, choices, default="Moderate"), index=ssi_series.index)


def compute_proper_ssi(
    df: pd.DataFrame,
    city: str,
    gamma: float = 0.30,
    k_archetypes: int = 6,
    anomaly_pct: float = 90.0,
) -> pd.DataFrame:
    """
    Run end-to-end proper SSI pipeline for a city panel.
    Returns DataFrame with updated indicators, ssi_linear, omega_compound, ssi_value, ssi_band, archetype_id, anomaly_flag.
    """
    log.info("Computing Proper SSI for {city}…", city=city)
    df = compute_physical_indicators(df)

    # 1. Weights
    weights = compute_entropy_weights(df, INDICATOR_COLS)

    # 2. Linear composite baseline
    ssi_linear = pd.Series(0.0, index=df.index)
    for col, w in weights.items():
        ssi_linear += w * df[col].fillna(df[col].median())
    df["ssi_linear"] = ssi_linear.clip(0.0, 1.0)

    # 3. Joint Tail Compound Amplifier
    omega = compute_joint_tail_amplifier(df, pairs=PHYSICAL_PAIRS, quantile_thresh=0.75)
    df["omega_compound"] = omega

    # 4. Final JT-SSI composite score
    ssi_jt = ssi_linear + gamma * omega
    df["ssi_value"] = ssi_jt.clip(0.0, 1.0)

    # 5. Bands
    df["ssi_band"] = assign_bands(df["ssi_value"])

    # 6. Archetypes (K-Means on 5 indicators)
    try:
        sub = df[INDICATOR_COLS].values
        imputer = SimpleImputer(strategy="mean")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(imputer.fit_transform(sub))
        km = KMeans(n_clusters=k_archetypes, random_state=42, n_init=10)
        df["archetype_id"] = km.fit_predict(X_scaled) + 1
    except Exception as exc:
        log.warning("KMeans failed: {e}", e=exc)
        df["archetype_id"] = 1

    # 7. Anomaly Flag
    threshold = np.nanpercentile(df["ssi_value"].values, anomaly_pct)
    df["anomaly_flag"] = df["ssi_value"] > threshold

    log.info(
        "Proper SSI for {city}: mean={m:.3f}, omega>0={pct:.1f}%, extreme={ext:.1f}%",
        city=city,
        m=df["ssi_value"].mean(),
        pct=(df["omega_compound"] > 0).mean() * 100,
        ext=(df["ssi_band"] == "Extreme").mean() * 100,
    )
    return df
