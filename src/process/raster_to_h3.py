"""
src/process/raster_to_h3.py
────────────────────────────
Convert raster GeoTIFFs (NDVI, LST, PM2.5, built-up) to per-H3-hex
values via zonal statistics (mean).

Works for:
  - Single-band rasters (NDVI, LST, PM2.5, built-up)
  - Monthly time series (iterate over a list of raster files)

Output: pd.DataFrame with [h3_index, date, {variable_name}]
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)


def raster_to_h3_single(
    raster_path: Path,
    h3_gdf: gpd.GeoDataFrame,
    variable_name: str,
    stat: str = "mean",
    band: int = 1,
    nodata: Optional[float] = None,
    scale_factor: float = 1.0,
    add_offset: float = 0.0,
) -> pd.Series:
    """
    Compute zonal statistics for a single raster → one value per H3 hex.

    Args:
        raster_path   : Path to GeoTIFF.
        h3_gdf        : GeoDataFrame indexed by h3_index (polygon geometries).
        variable_name : Name for the output Series.
        stat          : Zonal stat: 'mean', 'median', 'min', 'max', 'sum'.
        band          : Raster band (1-indexed).
        nodata        : Override nodata value.
        scale_factor  : Multiply result by this (e.g. 0.02 for MODIS LST).
        add_offset    : Add this to result after scaling (e.g. -273.15 for K→°C).

    Returns:
        pd.Series indexed by h3_index, named variable_name.
    """
    try:
        from rasterstats import zonal_stats
    except ImportError as exc:
        raise ImportError("Install rasterstats: pip install rasterstats") from exc

    gdf_wgs84 = h3_gdf.to_crs("EPSG:4326") if h3_gdf.crs else h3_gdf.copy()

    raw_stats = zonal_stats(
        vectors=gdf_wgs84.__geo_interface__["features"],
        raster=str(raster_path),
        stats=[stat],
        band_num=band,
        nodata=nodata,
        all_touched=True,
    )

    values = np.array(
        [s[stat] if (s and s[stat] is not None) else np.nan for s in raw_stats],
        dtype="float32",
    )

    # Apply scale + offset
    mask = ~np.isnan(values)
    values[mask] = values[mask] * scale_factor + add_offset

    return pd.Series(values, index=h3_gdf.index, name=variable_name)


def process_raster_time_series(
    raster_paths: list[Path],
    h3_gdf: gpd.GeoDataFrame,
    variable_name: str,
    dates: list[pd.Timestamp],
    stat: str = "mean",
    band: int = 1,
    scale_factor: float = 1.0,
    add_offset: float = 0.0,
) -> pd.DataFrame:
    """
    Process a list of monthly rasters into a long-format H3 × time DataFrame.

    Args:
        raster_paths  : List of GeoTIFF paths (one per month, in date order).
        h3_gdf        : H3 hex GeoDataFrame.
        variable_name : Column name for the variable.
        dates         : List of timestamps (one per raster).
        stat          : Zonal stat type.
        band          : Raster band number.
        scale_factor  : Multiply raw values by this.
        add_offset    : Add offset after scaling.

    Returns:
        DataFrame with columns [h3_index, date, variable_name].
    """
    assert len(raster_paths) == len(dates), (
        f"Mismatch: {len(raster_paths)} rasters vs {len(dates)} dates"
    )

    frames = []
    for raster, dt in zip(raster_paths, dates):
        if not raster.exists():
            log.warning("Raster not found: {p}", p=raster)
            continue

        try:
            series = raster_to_h3_single(
                raster, h3_gdf, variable_name, stat, band, scale_factor=scale_factor, add_offset=add_offset,
            )
            df = series.reset_index()
            df.columns = ["h3_index", variable_name]
            df["date"] = dt
            frames.append(df)
        except Exception as exc:
            log.error(
                "Zonal stats failed for {p}: {err}", p=raster, err=exc
            )

    if not frames:
        log.warning("No raster data processed for {var}", var=variable_name)
        return pd.DataFrame(columns=["h3_index", "date", variable_name])

    result = pd.concat(frames, ignore_index=True)
    result["date"] = pd.to_datetime(result["date"]).dt.to_period("M").dt.to_timestamp()
    return result


def process_ndvi_for_city(
    city: str,
    h3_gdf: gpd.GeoDataFrame,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> pd.DataFrame:
    """
    Process NDVI monthly rasters for a city.

    Returns:
        DataFrame with [h3_index, date, ndvi].
    """
    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    sat_dir = Path(config["paths"]["raw_data"]) / "satellite" / city

    months = pd.date_range(start=start, end=end, freq="MS")
    raster_paths = [sat_dir / f"ndvi_{dt.year}_{dt.month:02d}.tif" for dt in months]

    return process_raster_time_series(
        raster_paths=raster_paths,
        h3_gdf=h3_gdf,
        variable_name="ndvi",
        dates=list(months),
        stat="mean",
    )


def process_lst_for_city(
    city: str,
    h3_gdf: gpd.GeoDataFrame,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> pd.DataFrame:
    """
    Process LST monthly rasters for a city.

    Note: Planetary Computer LST files are already in °C after our ingestion
    step applies the MODIS scale factor.

    Returns:
        DataFrame with [h3_index, date, lst_c].
    """
    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    sat_dir = Path(config["paths"]["raw_data"]) / "satellite" / city

    months = pd.date_range(start=start, end=end, freq="MS")
    raster_paths = [sat_dir / f"lst_{dt.year}_{dt.month:02d}.tif" for dt in months]

    return process_raster_time_series(
        raster_paths=raster_paths,
        h3_gdf=h3_gdf,
        variable_name="lst_c",
        dates=list(months),
        stat="mean",
    )


def process_pm25_for_city(
    city: str,
    h3_gdf: gpd.GeoDataFrame,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> pd.DataFrame:
    """
    Process PM2.5 monthly rasters for a city.

    Returns:
        DataFrame with [h3_index, date, pm25].
    """
    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    pm25_dir = Path(config["paths"]["raw_data"]) / "pm25" / city

    months = pd.date_range(start=start, end=end, freq="MS")
    raster_paths = [pm25_dir / f"monthly_{dt.year}_{dt.month:02d}.tif" for dt in months]

    return process_raster_time_series(
        raster_paths=raster_paths,
        h3_gdf=h3_gdf,
        variable_name="pm25",
        dates=list(months),
        stat="mean",
    )


def process_built_up_for_city(
    city: str,
    h3_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    Process static GHSL built-up fraction raster for a city.

    Returns:
        DataFrame with [h3_index, built_up_fraction] — no date (static).
    """
    config = load_config()
    sat_dir = Path(config["paths"]["raw_data"]) / "satellite" / city
    raster_path = sat_dir / "built_up.tif"

    if not raster_path.exists():
        log.warning("Built-up raster not found for {city}", city=city)
        return pd.DataFrame(columns=["h3_index", "built_up_fraction"])

    series = raster_to_h3_single(
        raster_path, h3_gdf, "built_up_fraction", stat="mean"
    )
    df = series.reset_index()
    df.columns = ["h3_index", "built_up_fraction"]

    # Normalise to 0–1 if values appear to be 0–100
    if df["built_up_fraction"].max() > 1.5:
        df["built_up_fraction"] = df["built_up_fraction"] / 100.0

    df["built_up_fraction"] = df["built_up_fraction"].clip(0, 1)
    return df
