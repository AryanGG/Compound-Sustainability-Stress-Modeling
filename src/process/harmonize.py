"""
src/process/harmonize.py
─────────────────────────
Master harmonization step: merges all processed H3 datasets into a single
H3 × monthly panel DataFrame.

pipeline:
  1. Generate H3 grid (cells + GeoDataFrame)
  2. Build temporal skeleton: all (h3_index × month) combinations
  3. Left-join ERA5 monthly variables
  4. Left-join NDVI monthly values
  5. Left-join LST monthly values
  6. Left-join PM2.5 monthly values
  7. Left-join built-up fraction (static → broadcast across time)
  8. Left-join OSM urban form metrics (static → broadcast)
  9. Left-join vulnerability indicators (static → broadcast)

Output:
  data/processed/{city}_h3_panel.parquet
  Columns: city_id, h3_index, date + all raw variable columns
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_config
from src.utils.h3_utils import (
    build_city_h3_gdf,
    build_h3_time_skeleton,
    generate_h3_cells_for_city,
)
from src.utils.logger import get_logger

log = get_logger(__name__)


def _safe_merge(
    base: pd.DataFrame,
    incoming: pd.DataFrame,
    on: list[str],
    label: str,
) -> pd.DataFrame:
    """
    Left-merge `incoming` onto `base`. Log merge stats for debugging.
    """
    before = len(base)
    merged = base.merge(incoming, on=on, how="left")
    after = len(merged)

    if after != before:
        log.warning(
            "Merge '{label}' changed row count: {before} -> {after}",
            label=label, before=before, after=after,
        )

    fill_rate = (
        merged[[c for c in incoming.columns if c not in on]]
        .notna()
        .mean()
        .mean()
    )
    log.debug(
        "Merge '{label}': fill rate {rate:.1%}",
        label=label, rate=fill_rate if not pd.isna(fill_rate) else 0,
    )
    return merged


def build_h3_panel(
    city: str,
    resolution: Optional[int] = None,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build the full H3 × monthly panel for a single city.

    Args:
        city      : City slug.
        resolution: H3 resolution override (default from config).
        start_month: Time range override.
        end_month  : Time range override.

    Returns:
        Full panel DataFrame with all raw variables.
    """
    config = load_config()
    res = resolution or config["spatial"]["h3_resolution"]
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]

    log.info("Building H3 panel for {city} (res={res})", city=city, res=res)

    # ── Step 1: H3 grid ───────────────────────────────────────────────────────
    cells = generate_h3_cells_for_city(city, res)
    h3_gdf = build_city_h3_gdf(city, res)
    log.info("{city}: {n} H3 cells at resolution {res}", city=city, n=len(cells), res=res)

    # ── Step 2: Temporal skeleton ─────────────────────────────────────────────
    panel = build_h3_time_skeleton(cells, start, end)
    panel["city_id"] = city
    log.info("{city}: Skeleton has {n} rows", city=city, n=len(panel))

    # ── Step 3: ERA5 ──────────────────────────────────────────────────────────
    try:
        from src.process.era5_process import process_era5_for_city
        era5_df = process_era5_for_city(city, h3_gdf, start, end)
        if not era5_df.empty:
            panel = _safe_merge(panel, era5_df, ["h3_index", "date"], "ERA5")
    except Exception as exc:
        log.warning("ERA5 processing skipped for {city}: {err}", city=city, err=exc)

    # ── Step 4: NDVI ──────────────────────────────────────────────────────────
    try:
        from src.process.raster_to_h3 import process_ndvi_for_city
        ndvi_df = process_ndvi_for_city(city, h3_gdf, start, end)
        if not ndvi_df.empty:
            panel = _safe_merge(panel, ndvi_df, ["h3_index", "date"], "NDVI")
    except Exception as exc:
        log.warning("NDVI processing skipped: {err}", err=exc)

    # ── Step 5: LST ───────────────────────────────────────────────────────────
    try:
        from src.process.raster_to_h3 import process_lst_for_city
        lst_df = process_lst_for_city(city, h3_gdf, start, end)
        if not lst_df.empty:
            panel = _safe_merge(panel, lst_df, ["h3_index", "date"], "LST")
    except Exception as exc:
        log.warning("LST processing skipped: {err}", err=exc)

    # ── Step 6: PM2.5 ─────────────────────────────────────────────────────────
    try:
        from src.process.raster_to_h3 import process_pm25_for_city, process_built_up_for_city
        pm25_df = process_pm25_for_city(city, h3_gdf, start, end)
        if not pm25_df.empty:
            panel = _safe_merge(panel, pm25_df, ["h3_index", "date"], "PM2.5")
    except Exception as exc:
        log.warning("PM2.5 processing skipped: {err}", err=exc)

    # ── Step 7: Built-up fraction (static) ───────────────────────────────────
    try:
        from src.process.raster_to_h3 import process_built_up_for_city
        built_df = process_built_up_for_city(city, h3_gdf)
        if not built_df.empty:
            panel = _safe_merge(panel, built_df, ["h3_index"], "built_up")
    except Exception as exc:
        log.warning("Built-up processing skipped: {err}", err=exc)

    # ── Step 8: OSM urban form (static) ──────────────────────────────────────
    try:
        from src.process.osm_to_h3 import process_osm_for_city
        osm_df = process_osm_for_city(city, h3_gdf)
        if not osm_df.empty:
            panel = _safe_merge(panel, osm_df, ["h3_index"], "OSM")
    except Exception as exc:
        log.warning("OSM processing skipped: {err}", err=exc)

    # ── Step 9: Vulnerability (static) ───────────────────────────────────────
    try:
        from src.ingest.vulnerability_ingest import get_vulnerability_for_city
        vuln_df = get_vulnerability_for_city(city, cells)
        if not vuln_df.empty:
            panel = _safe_merge(panel, vuln_df, ["h3_index"], "vulnerability")
    except Exception as exc:
        log.warning("Vulnerability processing skipped: {err}", err=exc)

    # ── Final reorder ─────────────────────────────────────────────────────────
    priority_cols = [
        "city_id", "h3_index", "date",
        "temp_mean_c", "dewpoint_mean_c", "precip_sum_mm",
        "wind_speed", "radiation", "soil_moisture",
        "ndvi", "lst_c", "pm25", "built_up_fraction",
        "road_density_km_km2", "building_density",
        "building_fp_fraction", "green_space_fraction",
        "bpl_pct", "slum_pct", "elderly_pct", "literacy_pct",
    ]
    existing = [c for c in priority_cols if c in panel.columns]
    extra = [c for c in panel.columns if c not in priority_cols]
    panel = panel[existing + extra]

    # ── Step 10: Temporal Interpolation ───────────────────────────────────────
    # Fill gaps caused by missing satellite data (e.g. NDVI during monsoon)
    if "ndvi" in panel.columns:
        panel = panel.sort_values(["h3_index", "date"])
        panel["ndvi"] = panel.groupby("h3_index")["ndvi"].transform(
            lambda g: g.interpolate(method="linear", limit_direction="both")
        )

    log.info(
        "Panel built for {city}: {rows:,} rows × {cols} cols",
        city=city, rows=len(panel), cols=len(panel.columns),
    )
    return panel





def save_panel(
    panel: pd.DataFrame,
    city: str,
    intermediate: bool = False,
) -> Path:
    """
    Save panel DataFrame to Parquet.

    Args:
        panel      : Panel DataFrame.
        city       : City slug (determines output filename).
        intermediate: If True, save to data/processed/. If False, save to data/h3_panel/final/.

    Returns:
        Path to saved file.
    """
    config = load_config()

    if intermediate:
        out_dir = Path(config["paths"]["processed_data"])
    else:
        out_dir = Path(config["paths"]["h3_panel"]) / "final"

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{city}.parquet"

    panel.to_parquet(out_path, index=False, compression="snappy")
    log.success(
        "Panel saved -> {p} ({rows:,} rows x {cols} cols)",
        p=out_path, rows=len(panel), cols=len(panel.columns),
    )
    return out_path
