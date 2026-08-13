"""
src/utils/geo_utils.py
───────────────────────
Geospatial helper functions used across the pipeline:
  - bbox_with_buffer     → expand bbox by N km
  - raster_zonal_stats_h3 → per-hex raster stats via rasterstats
  - gdf_to_h3_agg        → vector GeoDataFrame aggregated to H3 hexes
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box


# ─── Bounding Box Utilities ───────────────────────────────────────────────────

def bbox_with_buffer(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    buffer_km: float = 10.0,
) -> dict[str, float]:
    """
    Expand a bounding box by `buffer_km` in all directions.

    Uses approximate degree conversion:
        1° latitude  ≈ 111 km
        1° longitude ≈ 111 * cos(lat_centre) km

    Args:
        min_lon, min_lat, max_lon, max_lat: Original bbox in WGS84.
        buffer_km: Buffer distance in kilometres.

    Returns:
        Expanded bbox dict with keys min_lon, min_lat, max_lon, max_lat.
    """
    lat_centre = (min_lat + max_lat) / 2.0
    deg_lat = buffer_km / 111.0
    deg_lon = buffer_km / (111.0 * np.cos(np.radians(lat_centre)))

    return {
        "min_lon": min_lon - deg_lon,
        "min_lat": min_lat - deg_lat,
        "max_lon": max_lon + deg_lon,
        "max_lat": max_lat + deg_lat,
    }


def bbox_to_shapely(
    min_lon: float, min_lat: float, max_lon: float, max_lat: float
):
    """Return a Shapely box geometry for the given bbox."""
    return box(min_lon, min_lat, max_lon, max_lat)


# ─── Raster → H3 ─────────────────────────────────────────────────────────────

def raster_zonal_stats_h3(
    raster_path: str | Path,
    h3_gdf: gpd.GeoDataFrame,
    stat: str = "mean",
    band: int = 1,
    nodata: Optional[float] = None,
) -> pd.Series:
    """
    Compute zonal statistics of a raster for each H3 hex polygon.

    Args:
        raster_path : Path to GeoTIFF (COG or regular).
        h3_gdf      : GeoDataFrame with hex polygons, index = h3_index.
        stat        : One of mean | median | min | max | sum | count.
        band        : Raster band number (1-indexed).
        nodata      : Override nodata value; None uses raster's native nodata.

    Returns:
        pd.Series indexed by h3_index, values = zonal stat.
    """
    from rasterstats import zonal_stats

    raster_path = str(raster_path)

    # Ensure GeoDataFrame is in EPSG:4326 (WGS84)
    gdf_wgs84 = h3_gdf.to_crs("EPSG:4326") if h3_gdf.crs else h3_gdf

    stats = zonal_stats(
        vectors=gdf_wgs84,
        raster=raster_path,
        stats=[stat],
        band=band,
        nodata=nodata,
        all_touched=True,
    )

    values = [s[stat] if s[stat] is not None else np.nan for s in stats]
    return pd.Series(values, index=h3_gdf.index, name=stat)


# ─── Vector → H3 ─────────────────────────────────────────────────────────────

def gdf_to_h3_agg(
    gdf: gpd.GeoDataFrame,
    h3_gdf: gpd.GeoDataFrame,
    value_col: str,
    agg_fn: Literal["mean", "sum", "count", "max", "min"] = "mean",
    how: Literal["intersection", "centroid"] = "intersection",
) -> pd.Series:
    """
    Aggregate a vector GeoDataFrame to H3 hexes.

    Args:
        gdf       : Source GeoDataFrame (polygons or points) in EPSG:4326.
        h3_gdf    : H3 hex GeoDataFrame, index = h3_index.
        value_col : Column to aggregate.
        agg_fn    : Aggregation function.
        how       : 'intersection' (area-weighted) or 'centroid' join.

    Returns:
        pd.Series indexed by h3_index.
    """
    gdf = gdf.to_crs("EPSG:4326") if gdf.crs else gdf
    h3_wgs84 = h3_gdf.to_crs("EPSG:4326") if h3_gdf.crs else h3_gdf

    if how == "centroid":
        pts = gdf.copy()
        pts["geometry"] = gdf.geometry.centroid
        joined = gpd.sjoin(pts, h3_wgs84.reset_index(), how="left", predicate="within")
        result = joined.groupby("h3_index")[value_col].agg(agg_fn)
    else:
        # Spatial intersection with area weighting
        gdf_proj = gdf.to_crs("EPSG:3857")
        h3_proj = h3_wgs84.reset_index().to_crs("EPSG:3857")

        intersected = gpd.overlay(gdf_proj, h3_proj, how="intersection")
        if intersected.empty:
            return pd.Series(dtype=float, name=value_col)

        intersected["_area"] = intersected.geometry.area
        gen = intersected.groupby("h3_index")

        if agg_fn in ("mean",):
            # Area-weighted mean
            intersected["_weighted"] = (
                intersected[value_col] * intersected["_area"]
            )
            result = (
                intersected.groupby("h3_index")["_weighted"].sum()
                / intersected.groupby("h3_index")["_area"].sum()
            )
        else:
            result = gen[value_col].agg(agg_fn)

    result.name = value_col
    return result.reindex(h3_gdf.index)
