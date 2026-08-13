"""
src/process/osm_to_h3.py
─────────────────────────
Process cached OSM GeoPackages into per-H3-hex urban form metrics:
  - road_density_km_km2   : Total road length (km) / hex area (km²)
  - building_density      : Building count / km²
  - building_fp_fraction  : Building footprint area / hex area
  - green_space_fraction  : Green space area / hex area

Output: pd.DataFrame with [h3_index, road_density_km_km2,
         building_density, building_fp_fraction, green_space_fraction]
(static — no temporal dimension)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# Projected CRS for area/length calculations (Mercator)
PROJECTED_CRS = "EPSG:3857"


def _hex_areas_km2(h3_gdf: gpd.GeoDataFrame) -> pd.Series:
    """Return series of hex areas in km² (using Mercator projection)."""
    projected = h3_gdf.to_crs(PROJECTED_CRS)
    return projected.geometry.area / 1e6   # m² → km²


def compute_road_density(
    h3_gdf: gpd.GeoDataFrame,
    roads_gdf: gpd.GeoDataFrame,
) -> pd.Series:
    """
    Compute road density (km road / km²) per H3 hex.

    Strategy:
      1. Project both to Mercator.
      2. Intersect road lines with each hex polygon.
      3. Sum intersected lengths per hex, divide by hex area.

    Args:
        h3_gdf   : H3 GeoDataFrame indexed by h3_index.
        roads_gdf: GeoDataFrame of road geometries (LineStrings).

    Returns:
        pd.Series indexed by h3_index, values in km/km².
    """
    h3_proj = h3_gdf.reset_index().to_crs(PROJECTED_CRS)
    roads_proj = roads_gdf.to_crs(PROJECTED_CRS)[["geometry"]]

    # Spatial intersection of roads with each hex
    joined = gpd.overlay(roads_proj, h3_proj[["h3_index", "geometry"]], how="intersection")

    if joined.empty:
        return pd.Series(0.0, index=h3_gdf.index, name="road_density_km_km2")

    # Total road length (m → km) per hex
    joined["length_km"] = joined.geometry.length / 1000.0
    road_length = joined.groupby("h3_index")["length_km"].sum()

    # Hex areas (km²)
    hex_areas = _hex_areas_km2(h3_gdf)   # indexed by h3_index

    density = (road_length / hex_areas).fillna(0.0)
    density.name = "road_density_km_km2"
    return density.reindex(h3_gdf.index, fill_value=0.0)


def compute_building_metrics(
    h3_gdf: gpd.GeoDataFrame,
    buildings_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    Compute building density (count/km²) and footprint fraction per H3 hex.

    Args:
        h3_gdf       : H3 GeoDataFrame indexed by h3_index.
        buildings_gdf: GeoDataFrame of building polygons.

    Returns:
        DataFrame with [h3_index, building_density, building_fp_fraction].
    """
    h3_proj = h3_gdf.reset_index().to_crs(PROJECTED_CRS)
    bld_proj = buildings_gdf.to_crs(PROJECTED_CRS)[["geometry"]]

    hex_areas = _hex_areas_km2(h3_gdf)  # km²

    # Spatial join: which hex does each building centroid fall into?
    bld_centroids = bld_proj.copy()
    bld_centroids["geometry"] = bld_proj.geometry.centroid

    joined = gpd.sjoin(
        bld_centroids,
        h3_proj[["h3_index", "geometry"]],
        how="inner",
        predicate="within",
    )

    # Building count per hex
    building_count = joined.groupby("h3_index").size()
    density = (building_count / hex_areas).fillna(0.0)
    density.name = "building_density"

    # Building footprint area: intersect, compute area
    bld_intersect = gpd.overlay(bld_proj, h3_proj[["h3_index", "geometry"]], how="intersection")
    if not bld_intersect.empty:
        bld_intersect["area_m2"] = bld_intersect.geometry.area
        fp_area = bld_intersect.groupby("h3_index")["area_m2"].sum()
        fp_fraction = (fp_area / (hex_areas * 1e6)).fillna(0.0).clip(0, 1)
    else:
        fp_fraction = pd.Series(0.0, index=h3_gdf.index)

    fp_fraction.name = "building_fp_fraction"

    result = pd.DataFrame(
        {"building_density": density, "building_fp_fraction": fp_fraction}
    ).reindex(h3_gdf.index, fill_value=0.0)
    result.index.name = "h3_index"
    return result.reset_index()


def compute_green_space_fraction(
    h3_gdf: gpd.GeoDataFrame,
    green_gdf: gpd.GeoDataFrame,
) -> pd.Series:
    """
    Compute green space fraction per H3 hex.

    Args:
        h3_gdf   : H3 GeoDataFrame indexed by h3_index.
        green_gdf: GeoDataFrame of green space polygons.

    Returns:
        pd.Series indexed by h3_index, values in [0, 1].
    """
    h3_proj = h3_gdf.reset_index().to_crs(PROJECTED_CRS)
    green_proj = green_gdf.to_crs(PROJECTED_CRS)[["geometry"]]

    hex_areas_m2 = h3_proj.set_index("h3_index").geometry.area  # m²

    intersected = gpd.overlay(green_proj, h3_proj[["h3_index", "geometry"]], how="intersection")
    if intersected.empty:
        return pd.Series(0.0, index=h3_gdf.index, name="green_space_fraction")

    intersected["area_m2"] = intersected.geometry.area
    green_area = intersected.groupby("h3_index")["area_m2"].sum()

    fraction = (green_area / hex_areas_m2).fillna(0.0).clip(0, 1)
    fraction.name = "green_space_fraction"
    return fraction.reindex(h3_gdf.index, fill_value=0.0)


def process_osm_for_city(
    city: str,
    h3_gdf: gpd.GeoDataFrame,
) -> pd.DataFrame:
    """
    Load cached OSM GeoPackages and compute all urban form metrics per H3 hex.

    Args:
        city  : City slug.
        h3_gdf: H3 hex GeoDataFrame indexed by h3_index.

    Returns:
        DataFrame with [h3_index, road_density_km_km2, building_density,
                        building_fp_fraction, green_space_fraction].
    """
    config = load_config()
    osm_dir = Path(config["paths"]["raw_data"]) / "osm"

    result = pd.DataFrame({"h3_index": list(h3_gdf.index)})
    result = result.set_index("h3_index")

    # ── Road density ────────────────────────────────────────────────────────
    roads_path = osm_dir / f"{city}_roads.gpkg"
    if roads_path.exists():
        try:
            roads = gpd.read_file(roads_path)
            result["road_density_km_km2"] = compute_road_density(h3_gdf, roads)
        except Exception as exc:
            log.error("Road density failed for {city}: {err}", city=city, err=exc)
            result["road_density_km_km2"] = np.nan
    else:
        log.warning("Roads GeoPackage not found for {city}", city=city)
        result["road_density_km_km2"] = np.nan

    # ── Building metrics ─────────────────────────────────────────────────────
    bld_path = osm_dir / f"{city}_buildings.gpkg"
    if bld_path.exists():
        try:
            buildings = gpd.read_file(bld_path)
            bld_metrics = compute_building_metrics(h3_gdf, buildings)
            bld_metrics = bld_metrics.set_index("h3_index")
            result["building_density"] = bld_metrics["building_density"]
            result["building_fp_fraction"] = bld_metrics["building_fp_fraction"]
        except Exception as exc:
            log.error("Building metrics failed for {city}: {err}", city=city, err=exc)
            result["building_density"] = np.nan
            result["building_fp_fraction"] = np.nan
    else:
        log.warning("Buildings GeoPackage not found for {city}", city=city)
        result["building_density"] = np.nan
        result["building_fp_fraction"] = np.nan

    # ── Green space fraction ─────────────────────────────────────────────────
    green_path = osm_dir / f"{city}_greenspace.gpkg"
    if green_path.exists():
        try:
            green = gpd.read_file(green_path)
            result["green_space_fraction"] = compute_green_space_fraction(h3_gdf, green)
        except Exception as exc:
            log.error("Green space failed for {city}: {err}", city=city, err=exc)
            result["green_space_fraction"] = np.nan
    else:
        log.warning("Green space GeoPackage not found for {city}", city=city)
        result["green_space_fraction"] = np.nan

    result = result.reset_index()
    log.info(
        "OSM metrics computed for {city}: {n} hexes",
        city=city,
        n=len(result),
    )
    return result
