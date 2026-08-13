"""
src/process/era5_process.py
────────────────────────────
ERA5 NetCDF preprocessing:
  - Unit conversions (K→°C, m→mm precipitation)
  - Wind speed computation from U/V components
  - Soil moisture averaging (layers 1 + 2)
  - Temporal aggregation: hourly/6-hourly → monthly means
  - Spatial interpolation: ERA5 grid → H3 hex centroids

Output: pd.DataFrame with columns:
  [h3_index, date, temp_mean_c, dewpoint_mean_c, precip_sum_mm,
   wind_speed, radiation, soil_moisture]
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xarray as xr

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# ERA5 variable name mapping in NetCDF files
ERA5_NC_VARS = {
    "t2m": "temp_mean_c",          # 2m temperature (K)
    "d2m": "dewpoint_mean_c",      # 2m dewpoint (K)
    "tp":  "precip_sum_mm",        # Total precipitation (m)
    "u10": "_u10",                 # 10m U-wind (m/s)
    "v10": "_v10",                 # 10m V-wind (m/s)
    "ssrd": "radiation",           # Surface solar radiation (J/m²)
    "swvl1": "_swvl1",            # Soil water layer 1 (m³/m³)
    "swvl2": "_swvl2",            # Soil water layer 2 (m³/m³)
}


def open_era5_monthly_nc(nc_path: Path) -> xr.Dataset:
    """
    Open a monthly ERA5 NetCDF file with xarray.

    Args:
        nc_path: Path to the .nc file.

    Returns:
        xr.Dataset with all ERA5 variables.
    """
    ds = xr.open_dataset(nc_path, engine="netcdf4", chunks={"time": -1})
    return ds


def compute_monthly_aggregates(ds: xr.Dataset) -> xr.Dataset:
    """
    Aggregate 6-hourly ERA5 data to monthly statistics.

    Aggregation rules:
      - Temperature, dewpoint, wind → monthly mean
      - Precipitation → monthly sum (accumulate)
      - Radiation → monthly mean (W/m² conversion from J/m²)
      - Soil moisture → monthly mean

    Args:
        ds: xr.Dataset with 6-hourly time dimension.

    Returns:
        xr.Dataset with a single time step (month).
    """
    agg: dict[str, xr.DataArray] = {}

    present = set(ds.data_vars)

    # Temperature (K → °C)
    if "t2m" in present:
        agg["temp_mean_c"] = ds["t2m"].mean(dim="valid_time" if "valid_time" in ds.dims else "time") - 273.15

    # Dewpoint (K → °C)
    if "d2m" in present:
        agg["dewpoint_mean_c"] = ds["d2m"].mean(dim="valid_time" if "valid_time" in ds.dims else "time") - 273.15

    # Precipitation (m → mm, sum over month)
    # ERA5 TP is hourly accumulation; 6-hourly steps → multiply by 6 to get hourly-equiv
    if "tp" in present:
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        agg["precip_sum_mm"] = ds["tp"].sum(dim=time_dim) * 1000.0   # m → mm

    # Wind speed from U + V components
    if "u10" in present and "v10" in present:
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        u = ds["u10"].mean(dim=time_dim)
        v = ds["v10"].mean(dim=time_dim)
        agg["wind_speed"] = np.sqrt(u**2 + v**2)

    # Surface radiation (J/m² per 6h step → W/m²: divide by 6*3600)
    if "ssrd" in present:
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        agg["radiation"] = ds["ssrd"].mean(dim=time_dim) / (6 * 3600)

    # Soil moisture: average of layer 1 and 2
    if "swvl1" in present and "swvl2" in present:
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        swvl1 = ds["swvl1"].mean(dim=time_dim)
        swvl2 = ds["swvl2"].mean(dim=time_dim)
        agg["soil_moisture"] = (swvl1 + swvl2) / 2.0
    elif "swvl1" in present:
        time_dim = "valid_time" if "valid_time" in ds.dims else "time"
        agg["soil_moisture"] = ds["swvl1"].mean(dim=time_dim)

    return xr.Dataset(agg)


def interpolate_era5_to_h3_centroids(
    ds_monthly: xr.Dataset,
    h3_gdf,
    method: str = "linear",
) -> pd.DataFrame:
    """
    Interpolate ERA5 spatial field to H3 hex centroids.

    Args:
        ds_monthly: xr.Dataset with spatial coords (latitude, longitude).
        h3_gdf    : GeoDataFrame indexed by h3_index with centroid_lat/lon.
        method    : xarray interpolation method ('linear' or 'nearest').

    Returns:
        DataFrame with [h3_index, {era5_vars}].
    """
    lats = xr.DataArray(h3_gdf["centroid_lat"].values, dims="h3_index")
    lons = xr.DataArray(h3_gdf["centroid_lon"].values, dims="h3_index")

    # Determine lat/lon coordinate names
    lat_name = "latitude" if "latitude" in ds_monthly.coords else "lat"
    lon_name = "longitude" if "longitude" in ds_monthly.coords else "lon"

    interp_ds = ds_monthly.interp(
        {lat_name: lats, lon_name: lons},
        method=method,
    )

    result = interp_ds.to_dataframe().reset_index(drop=True)
    result.index = h3_gdf.index
    result.index.name = "h3_index"
    return result.reset_index()


def process_era5_for_city(
    city: str,
    h3_gdf,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> pd.DataFrame:
    """
    Process all downloaded ERA5 NetCDF files for a city into a monthly H3 DataFrame.

    Args:
        city      : City slug.
        h3_gdf    : H3 hex GeoDataFrame with centroid_lat/lon.
        start_month: Override config time range.
        end_month : Override config time range.

    Returns:
        DataFrame with [h3_index, date, temp_mean_c, dewpoint_mean_c,
                        precip_sum_mm, wind_speed, radiation, soil_moisture].
    """
    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    raw_dir = Path(config["paths"]["raw_data"]) / "era5" / city

    months = pd.date_range(start=start, end=end, freq="MS")
    all_frames = []

    for dt in months:
        nc_path = raw_dir / f"{dt.year}_{dt.month:02d}.nc"

        if not nc_path.exists():
            log.warning("ERA5 file missing: {p}", p=nc_path)
            continue

        try:
            ds = open_era5_monthly_nc(nc_path)
            ds_monthly = compute_monthly_aggregates(ds)
            df = interpolate_era5_to_h3_centroids(ds_monthly, h3_gdf)
            df["date"] = dt
            all_frames.append(df)
            ds.close()

        except Exception as exc:
            log.error(
                "ERA5 processing failed for {city} {dt}: {err}",
                city=city, dt=dt, err=exc,
            )

    if not all_frames:
        log.warning("No ERA5 data processed for {city}", city=city)
        return pd.DataFrame()

    result = pd.concat(all_frames, ignore_index=True)
    result["date"] = pd.to_datetime(result["date"]).dt.to_period("M").dt.to_timestamp()

    log.info(
        "ERA5 processing complete for {city}: {rows} rows",
        city=city, rows=len(result),
    )
    return result
