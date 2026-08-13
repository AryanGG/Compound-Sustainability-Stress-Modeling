"""
src/ingest/osm_ingest.py
─────────────────────────
OpenStreetMap urban form data ingestion via OSMnx.

Extracts and saves per-city:
  - Road network → road density (km road / km² hex area)
  - Building footprints → building count density + footprint fraction
  - Green space (parks, forests, gardens) → green space fraction

Output:
  data/raw/osm/{city}_roads.gpkg
  data/raw/osm/{city}_buildings.gpkg
  data/raw/osm/{city}_greenspace.gpkg
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# OSM tags for green space
GREEN_SPACE_TAGS = {
    "leisure": ["park", "garden", "nature_reserve", "recreation_ground"],
    "landuse": ["forest", "grass", "meadow", "village_green", "recreation_ground"],
    "natural": ["wood", "scrub", "grassland"],
}


def _bbox_to_polygon(bbox: dict):
    """Convert bbox dict to Shapely polygon."""
    return box(bbox["min_lon"], bbox["min_lat"], bbox["max_lon"], bbox["max_lat"])


def fetch_road_network(
    city: str,
    bbox: dict,
    out_dir: Path,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download and save the road network for a city using OSMnx.

    Args:
        city    : City slug.
        bbox    : City bounding box.
        out_dir : Output directory.
        overwrite: Re-download if file exists.

    Returns:
        Path to saved GeoPackage or None on failure.
    """
    try:
        import osmnx as ox
    except ImportError as exc:
        raise ImportError("Install osmnx for OSM ingestion.") from exc

    out_path = out_dir / f"{city}_roads.gpkg"
    if out_path.exists() and not overwrite:
        log.debug("Roads already cached: {p}", p=out_path)
        return out_path

    log.info("Fetching OSM road network for {city}...", city=city)

    try:
        config = load_config()
        network_type = config.get("osm", {}).get("network_type", "drive")

        # osmnx v2: graph_from_bbox takes (left, bottom, right, top)
        bbox_tuple = (
            bbox["min_lon"], bbox["min_lat"],
            bbox["max_lon"], bbox["max_lat"],
        )
        G = ox.graph_from_bbox(
            bbox_tuple,
            network_type=network_type,
            retain_all=False,
        )

        # Convert to GeoDataFrames
        _, edges = ox.graph_to_gdfs(G)
        edges = edges.reset_index()

        # Keep only essential columns
        keep_cols = ["geometry", "length", "highway"]
        edges = edges[[c for c in keep_cols if c in edges.columns]]

        edges.to_file(out_path, driver="GPKG", layer="roads")
        log.success("Roads saved → {p}", p=out_path)
        return out_path

    except Exception as exc:
        log.error("Road network fetch failed for {city}: {err}", city=city, err=exc)
        return None


def fetch_buildings(
    city: str,
    bbox: dict,
    out_dir: Path,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download building footprints for a city from OSM.

    Args:
        city    : City slug.
        bbox    : City bounding box.
        out_dir : Output directory.
        overwrite: Re-download if file exists.

    Returns:
        Path to saved GeoPackage or None on failure.
    """
    try:
        import osmnx as ox
    except ImportError as exc:
        raise ImportError("Install osmnx for OSM ingestion.") from exc

    out_path = out_dir / f"{city}_buildings.gpkg"
    if out_path.exists() and not overwrite:
        log.debug("Buildings already cached: {p}", p=out_path)
        return out_path

    log.info("Fetching OSM buildings for {city}...", city=city)

    try:
        # osmnx v2: features_from_bbox takes (left, bottom, right, top)
        bbox_tuple = (
            bbox["min_lon"], bbox["min_lat"],
            bbox["max_lon"], bbox["max_lat"],
        )
        buildings = ox.features_from_bbox(
            bbox_tuple,
            tags={"building": True},
        )

        if buildings.empty:
            log.warning("No buildings found for {city}", city=city)
            return None

        # Keep polygon geometries only
        buildings = buildings[buildings.geometry.geom_type == "Polygon"].copy()
        buildings = buildings[["geometry"]].reset_index(drop=True)
        buildings.to_file(out_path, driver="GPKG", layer="buildings")
        log.success("Buildings saved → {p} ({n} features)", p=out_path, n=len(buildings))
        return out_path

    except Exception as exc:
        log.error("Buildings fetch failed for {city}: {err}", city=city, err=exc)
        return None


def fetch_green_space(
    city: str,
    bbox: dict,
    out_dir: Path,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download green space polygons for a city from OSM.

    Args:
        city    : City slug.
        bbox    : City bounding box.
        out_dir : Output directory.
        overwrite: Re-download if file exists.

    Returns:
        Path to saved GeoPackage or None on failure.
    """
    try:
        import osmnx as ox
    except ImportError as exc:
        raise ImportError("Install osmnx for OSM ingestion.") from exc

    out_path = out_dir / f"{city}_greenspace.gpkg"
    if out_path.exists() and not overwrite:
        log.debug("Green space already cached: {p}", p=out_path)
        return out_path

    log.info("Fetching OSM green space for {city}...", city=city)

    try:
        # Try each tag category and merge
        all_green = []
        # osmnx v2: features_from_bbox takes (left, bottom, right, top)
        bbox_tuple = (
            bbox["min_lon"], bbox["min_lat"],
            bbox["max_lon"], bbox["max_lat"],
        )
        for tag_key, tag_values in GREEN_SPACE_TAGS.items():
            for val in tag_values:
                try:
                    gdf = ox.features_from_bbox(
                        bbox_tuple,
                        tags={tag_key: val},
                    )
                    if not gdf.empty:
                        all_green.append(gdf[["geometry"]])
                except Exception:
                    continue

        if not all_green:
            log.warning("No green space found for {city}", city=city)
            return None

        green = pd.concat(all_green).drop_duplicates()
        green = green[green.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
        green = gpd.GeoDataFrame(green, crs="EPSG:4326").reset_index(drop=True)
        green.to_file(out_path, driver="GPKG", layer="greenspace")
        log.success("Green space saved → {p} ({n} features)", p=out_path, n=len(green))
        return out_path

    except Exception as exc:
        log.error("Green space fetch failed for {city}: {err}", city=city, err=exc)
        return None


def ingest_osm_city(
    city: str,
    bbox: dict,
    overwrite: bool = False,
) -> dict[str, Optional[Path]]:
    """
    Run full OSM ingestion for a city.

    Args:
        city     : City slug.
        bbox     : City bounding box.
        overwrite: Re-download existing files.

    Returns:
        Dict with keys 'roads', 'buildings', 'greenspace' → Paths.
    """
    config = load_config()
    out_dir = Path(config["paths"]["raw_data"]) / "osm"
    out_dir.mkdir(parents=True, exist_ok=True)

    return {
        "roads": fetch_road_network(city, bbox, out_dir, overwrite),
        "buildings": fetch_buildings(city, bbox, out_dir, overwrite),
        "greenspace": fetch_green_space(city, bbox, out_dir, overwrite),
    }
