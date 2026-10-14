"""
src/ingest/cams_pm25_ingest.py
──────────────────────────────
Step 05: Ingest Copernicus Atmosphere Monitoring Service (CAMS) PM2.5 monthly reanalysis.
Extracts PM2.5 in µg/m³ (file unit is kg/m³, conversion factor = 1e9).
Generates data/processed/cams_pm25_monthly_{city}.csv.
"""

from __future__ import annotations

import glob
import json
import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import xarray as xr

from src.utils.logger import get_logger

log = get_logger(__name__)


def extract_pm25_ug_m3(nc_path: Path | str) -> float:
    """
    Extract spatial mean PM2.5 from a CAMS NetCDF file and convert kg/m³ → µg/m³.
    Conversion: 1 kg/m³ = 1e9 µg/m³.
    """
    ds = xr.open_dataset(nc_path)
    # Identify PM2.5 variable name (typically 'pm2p5' or 'pm25')
    candidates = [v for v in ds.data_vars if "pm2" in v or "pm" in v or "particulate" in v]
    if not candidates:
        raise ValueError(f"No PM2.5 data variable found in {nc_path}. Variables: {list(ds.data_vars)}")
    var_name = candidates[0]
    val_kg_m3 = float(ds[var_name].mean().values)
    ds.close()
    return float(val_kg_m3 * 1e9)


def to_city_series(city: str, raw_dir: Path | str = "data/raw/pm25") -> pd.DataFrame:
    """
    Compile all monthly NetCDF files for a city into a continuous DataFrame:
    Columns: date (YYYY-MM-01), pm25_cams (µg/m³).
    """
    city_dir = Path(raw_dir) / city
    if not city_dir.exists():
        raise FileNotFoundError(f"CAMS raw directory not found: {city_dir}")

    nc_files = sorted(glob.glob(str(city_dir / "cams_pm25_*.nc")))
    records = []
    for f in nc_files:
        p = Path(f)
        parts = p.stem.split("_")
        if len(parts) >= 4:
            year, month = parts[2], parts[3]
            date_str = f"{year}-{month}-01"
            val_ug = extract_pm25_ug_m3(p)
            records.append({"date": date_str, "pm25_cams": val_ug})

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError(f"No valid CAMS NetCDF files parsed for {city} in {city_dir}")

    df = df.sort_values("date").reset_index(drop=True)
    return df


def process_cams_city(city: str, raw_dir: str = "data/raw/pm25", out_dir: str = "data/processed") -> Path:
    """
    Process city CAMS data to data/processed/cams_pm25_monthly_{city}.csv.
    """
    out_path = Path(out_dir) / f"cams_pm25_monthly_{city}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = to_city_series(city, raw_dir=raw_dir)
    df.to_csv(out_path, index=False)
    log.info(f"Saved {len(df)} months CAMS PM2.5 for {city} -> {out_path}")
    return out_path


def check_pm25_source_correlation(
    cities: list[str] = ["mumbai", "coimbatore"],
    out_file: str = "results/pm25_source_check.json",
) -> dict[str, Any]:
    """
    Compute Spearman correlation between CAMS PM2.5 and existing legacy PM2.5.
    Saves summary to results/pm25_source_check.json.
    """
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    results = {}

    for city in cities:
        cams_file = Path(f"data/processed/cams_pm25_monthly_{city}.csv")
        legacy_file = Path(f"data/processed/{city}.parquet")

        if not cams_file.exists() or not legacy_file.exists():
            continue

        cams_df = pd.read_csv(cams_file)
        cams_df["date"] = pd.to_datetime(cams_df["date"]).dt.strftime("%Y-%m-01")

        legacy_df = pd.read_parquet(legacy_file)
        legacy_df["date"] = pd.to_datetime(legacy_df["date"]).dt.strftime("%Y-%m-01")
        legacy_monthly = legacy_df.groupby("date")["pm25"].mean().reset_index()

        merged = pd.merge(cams_df, legacy_monthly, on="date")
        if len(merged) > 3:
            r, pval = spearmanr(merged["pm25_cams"], merged["pm25"])
            results[city] = {
                "n_months": len(merged),
                "spearman_rho": round(float(r), 4),
                "p_value": float(pval),
                "cams_mean": round(float(merged["pm25_cams"].mean()), 2),
                "legacy_mean": round(float(merged["pm25"].mean()), 2),
            }

    with open(out_file, "w") as fh:
        json.dump(results, fh, indent=2)

    log.info(f"Saved PM2.5 source check -> {out_file}: {results}")
    return results


def main():
    cities = ["mumbai", "coimbatore"]
    for c in cities:
        process_cams_city(c)
    check_pm25_source_correlation(cities)


if __name__ == "__main__":
    main()
