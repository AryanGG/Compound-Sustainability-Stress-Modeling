"""
src/utils/h3_utils.py
──────────────────────
H3 grid utilities: city bbox loading, grid generation, GeoDataFrame conversion,
and point-to-H3 assignment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon


# ─── City BBox ────────────────────────────────────────────────────────────────

def load_city_bbox(city: str, bbox_file: str = "cities_bbox.json") -> dict:
    """
    Load bounding box for a given city from the JSON registry.

    Args:
        city: City slug (e.g. 'mumbai').
        bbox_file: Path to cities_bbox.json.

    Returns:
        Dict with min_lon, min_lat, max_lon, max_lat (+ metadata).
    """
    bbox_path = Path(bbox_file)
    if not bbox_path.exists():
        raise FileNotFoundError(f"BBox registry not found: {bbox_path}")

    with open(bbox_path, "r") as f:
        data = json.load(f)

    if city not in data:
        raise ValueError(
            f"City '{city}' not in bbox registry. "
            f"Available: {list(data.keys())}"
        )
    return data[city]


# ─── H3 Grid Generation ───────────────────────────────────────────────────────

def generate_h3_cells_for_city(
    city: str,
    resolution: int = 8,
    bbox_file: str = "cities_bbox.json",
) -> List[str]:
    """
    Generate all H3 cell IDs covering a city's bounding box.

    Args:
        city      : City slug matching cities_bbox.json key.
        resolution: H3 resolution (8 ≈ 0.74 km², 7 ≈ 5.1 km²).
        bbox_file : Path to cities_bbox.json.

    Returns:
        List of H3 cell ID strings.
    """
    bbox = load_city_bbox(city, bbox_file)

    outer = [
        (bbox["min_lat"], bbox["min_lon"]),
        (bbox["max_lat"], bbox["min_lon"]),
        (bbox["max_lat"], bbox["max_lon"]),
        (bbox["min_lat"], bbox["max_lon"]),
        (bbox["min_lat"], bbox["min_lon"]),  # Close ring
    ]

    poly = h3.LatLngPoly(outer)
    cells = h3.polygon_to_cells(poly, resolution)
    return list(cells)


# ─── H3 → GeoDataFrame ────────────────────────────────────────────────────────

def h3_cells_to_geodataframe(cells: List[str]) -> gpd.GeoDataFrame:
    """
    Convert a list of H3 cell IDs to a GeoDataFrame with polygon geometry.

    Args:
        cells: List of H3 cell ID strings.

    Returns:
        GeoDataFrame indexed by h3_index with columns:
            geometry   - hex polygon (WGS84)
            centroid_lat, centroid_lon - hex centre coordinates
    """
    rows = []
    for cell in cells:
        boundary = h3.cell_to_boundary(cell)   # List of (lat, lon) tuples
        # Shapely Polygon expects (lon, lat)
        polygon = Polygon([(lon, lat) for lat, lon in boundary])
        centre = h3.cell_to_latlng(cell)       # (lat, lon)
        rows.append(
            {
                "h3_index": cell,
                "geometry": polygon,
                "centroid_lat": centre[0],
                "centroid_lon": centre[1],
            }
        )

    gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326").set_index("h3_index")
    return gdf


def build_city_h3_gdf(
    city: str,
    resolution: int = 8,
    bbox_file: str = "cities_bbox.json",
) -> gpd.GeoDataFrame:
    """
    One-shot helper: generate H3 grid for a city and return GeoDataFrame.

    Args:
        city      : City slug.
        resolution: H3 resolution.
        bbox_file : Path to cities_bbox.json.

    Returns:
        GeoDataFrame indexed by h3_index.
    """
    cells = generate_h3_cells_for_city(city, resolution, bbox_file)
    return h3_cells_to_geodataframe(cells)


# ─── Point → H3 Assignment ────────────────────────────────────────────────────

def assign_h3_to_points(
    df: pd.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    resolution: int = 8,
    output_col: str = "h3_index",
) -> pd.DataFrame:
    """
    Assign an H3 cell ID to each row of a DataFrame with lat/lon columns.

    Args:
        df         : Input DataFrame.
        lat_col    : Column name for latitude.
        lon_col    : Column name for longitude.
        resolution : H3 resolution.
        output_col : Name of the new H3 ID column.

    Returns:
        DataFrame with added `output_col` column.
    """
    df = df.copy()
    df[output_col] = [
        h3.latlng_to_cell(lat, lon, resolution)
        for lat, lon in zip(df[lat_col], df[lon_col])
    ]
    return df


# ─── Temporal Grid Builder ────────────────────────────────────────────────────

def build_h3_time_skeleton(
    cells: List[str],
    start_month: str,
    end_month: str,
) -> pd.DataFrame:
    """
    Build the cartesian product of H3 cells × monthly dates.

    This forms the backbone panel that all other data is left-joined onto,
    ensuring every (hex, month) combination is present even if data is missing.

    Args:
        cells      : List of H3 cell IDs.
        start_month: ISO month string e.g. '2015-01'.
        end_month  : ISO month string e.g. '2025-12'.

    Returns:
        DataFrame with columns [h3_index, date] — one row per hex×month.
    """
    dates = pd.date_range(start=start_month, end=end_month, freq="MS")
    h3_series = pd.Series(cells, name="h3_index")
    date_series = pd.Series(dates, name="date")

    # Cartesian product via merge on a dummy key
    h3_df = h3_series.to_frame()
    h3_df["_key"] = 1
    date_df = date_series.to_frame()
    date_df["_key"] = 1

    panel = pd.merge(h3_df, date_df, on="_key").drop(columns="_key")
    panel["date"] = panel["date"].dt.to_period("M").dt.to_timestamp()
    return panel.reset_index(drop=True)
