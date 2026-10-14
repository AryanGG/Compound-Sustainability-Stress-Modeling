"""
src/v2/raw_drivers.py
─────────────────────
Step 04: Raw driver panels in physical units, un-normalized, per hex per month.
Produces data/h3_panel/v2_raw/{city}.parquet.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from src.features.heat_stress import compute_relative_humidity, compute_heat_index
from src.features.water_stress import compute_thornthwaite_pet
from src.utils.logger import get_logger

log = get_logger(__name__)


def build_raw(city: str, cfg: dict[str, Any]) -> pd.DataFrame:
    """
    Build physical raw drivers panel for a given city.

    Returns DataFrame with columns:
        h3_index, date, heat_raw, water_raw, veg_raw, pollution_raw,
        exposure_raw, exp_built_up, exp_building_density, exp_road_density,
        is_imputed
    """
    # 1. Load intermediate processed panel
    paths_cfg = cfg.get("paths", {})
    processed_dir = Path(paths_cfg.get("processed_data", "data/processed"))
    proc_file = processed_dir / f"{city}.parquet"

    if not proc_file.exists():
        # Fallback to data/features or legacy panel store from config
        feat_file = Path(paths_cfg.get("features_data", "data/features")) / f"{city}_features.csv"
        legacy_dir = cfg.get("v2", {}).get("paths", {}).get("v1")
        legacy_file = Path(legacy_dir) / f"{city}.parquet" if legacy_dir else None

        if feat_file.exists():
            df = pd.read_csv(feat_file)
        elif legacy_file and legacy_file.exists():
            df = pd.read_parquet(legacy_file)
        else:
            raise FileNotFoundError(f"No processed data found for city {city} in {proc_file}, {feat_file}, or {legacy_file}")
    else:
        df = pd.read_parquet(proc_file)

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-01")
    df = df.sort_values(["h3_index", "date"]).reset_index(drop=True)

    # Track imputation
    is_imputed = pd.Series(False, index=df.index, name="is_imputed")

    # 2. Heat Driver: Meteorological Heat Index (°C) from 2m Temp and Dewpoint
    # (MODIS LST is strictly held out for Step 11 convergent validation)
    temp = df["temp_mean_c"]
    dew = df["dewpoint_mean_c"]
    rh = compute_relative_humidity(temp, dew)
    heat_raw = compute_heat_index(temp, rh)
    heat_raw = heat_raw.rename("heat_raw")

    # 3. Water Driver: Climatic Water Deficit (CWD in mm/month) = PET - Precipitation
    # Higher = drier / more deficit
    pet = compute_thornthwaite_pet(df, temp_col="temp_mean_c")
    precip = df["precip_sum_mm"].clip(lower=0.0)
    water_raw = (pet - precip).clip(lower=0.0)
    water_raw = water_raw.rename("water_raw")

    # 4. Vegetation Driver: Sentinel-2 NDVI
    # Higher = greener. (Step 06 flips this so higher = more stress).
    veg_raw = df["ndvi"].copy().rename("veg_raw")

    # Known gap resolution: November 2022 Sentinel-2 cloud/availability gap
    # Interpolate missing NDVI temporally per hex, flag is_imputed
    if veg_raw.isna().sum() > 0:
        imputed_mask = veg_raw.isna()
        is_imputed = is_imputed | imputed_mask
        # Temporal interpolation within hex
        df["_veg_temp"] = veg_raw
        df["_veg_temp"] = df.groupby("h3_index")["_veg_temp"].transform(
            lambda s: s.interpolate(method="linear", limit_direction="both")
        )
        # If any remain (e.g. all hexes empty for that month), fill with date mean
        df["_veg_temp"] = df["_veg_temp"].fillna(df.groupby("date")["_veg_temp"].transform("median"))
        veg_raw = df["_veg_temp"].copy().rename("veg_raw")
        df.drop(columns=["_veg_temp"], inplace=True)

    # 5. Pollution Driver: PM2.5 in µg/m³
    # Check if dedicated CAMS monthly file exists (from Step 05), else use processed pm25
    cams_file = Path(f"data/processed/cams_pm25_monthly_{city}.csv")
    if cams_file.exists():
        cams_df = pd.read_csv(cams_file)
        cams_df["date"] = pd.to_datetime(cams_df["date"]).dt.strftime("%Y-%m-01")
        cams_map = dict(zip(cams_df["date"], cams_df["pm25_cams"]))
        pollution_raw = df["date"].map(cams_map).rename("pollution_raw")
    elif "pm25" in df.columns:
        pollution_raw = df["pm25"].copy().rename("pollution_raw")
    else:
        pollution_raw = pd.Series(np.nan, index=df.index, name="pollution_raw")

    if pollution_raw.isna().sum() > 0:
        is_imputed = is_imputed | pollution_raw.isna()
        if "date" in df.columns and "pm25" in df.columns:
            date_median = df.groupby("date")["pm25"].transform("median")
            pollution_raw = pollution_raw.fillna(date_median)
        pollution_raw = pollution_raw.fillna(pollution_raw.median())

    # 6. Static Exposure / Urban Vulnerability Components
    # Combine static spatial layers: built_up_fraction, building_density, road_density
    exp_built = df["built_up_fraction"].fillna(0.0).rename("exp_built_up") if "built_up_fraction" in df.columns else pd.Series(0.0, index=df.index)
    exp_bld_dens = df["building_density"].fillna(0.0).rename("exp_building_density") if "building_density" in df.columns else pd.Series(0.0, index=df.index)
    exp_roads = df["road_density_km_km2"].fillna(0.0).rename("exp_road_density") if "road_density_km_km2" in df.columns else pd.Series(0.0, index=df.index)

    # Min-max scaling per component for fair blending
    def _scale(s: pd.Series) -> pd.Series:
        rng = s.max() - s.min()
        return (s - s.min()) / rng if rng > 0 else pd.Series(0.0, index=s.index)

    components = [_scale(exp_built), _scale(exp_bld_dens), _scale(exp_roads)]
    valid_components = [c for c in components if c.nunique() > 1]
    if valid_components:
        exposure_raw = sum(valid_components) / len(valid_components)
    else:
        exposure_raw = _scale(exp_built)
    exposure_raw = exposure_raw.rename("exposure_raw")

    # Assemble raw panel
    raw_panel = pd.DataFrame({
        "h3_index": df["h3_index"],
        "date": df["date"],
        "heat_raw": heat_raw,
        "water_raw": water_raw,
        "veg_raw": veg_raw,
        "pollution_raw": pollution_raw,
        "exposure_raw": exposure_raw,
        "exp_built_up": exp_built,
        "exp_building_density": exp_bld_dens,
        "exp_road_density": exp_roads,
        "is_imputed": is_imputed,
    })

    return raw_panel


def main():
    parser = argparse.ArgumentParser(description="Generate physical raw driver panels (v2_raw).")
    parser.add_argument("--city", default="all", help="City name or 'all'")
    args = parser.parse_args()

    cfg = yaml.safe_load(open("config.yml"))
    v2_cfg = cfg.get("v2", {})
    all_cities = v2_cfg.get("cities", ["mumbai", "coimbatore"])

    target_cities = all_cities if args.city == "all" else [args.city]
    out_dir = Path(v2_cfg.get("paths", {}).get("raw", "data/h3_panel/v2_raw"))
    out_dir.mkdir(parents=True, exist_ok=True)

    for city in target_cities:
        log.info(f"Building v2_raw panel for {city}...")
        raw_df = build_raw(city, cfg)
        out_path = out_dir / f"{city}.parquet"
        raw_df.to_parquet(out_path, index=False)
        log.info(f"Saved {len(raw_df):,} rows -> {out_path}")


if __name__ == "__main__":
    main()
