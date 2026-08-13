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
    synthetic: bool = False,
) -> pd.DataFrame:
    """
    Build the full H3 × monthly panel for a single city.

    Args:
        city      : City slug.
        resolution: H3 resolution override (default from config).
        start_month: Time range override.
        end_month  : Time range override.
        synthetic : If True, generate synthetic data for all variables.

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

    if synthetic:
        return _build_synthetic_panel(panel, city)

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

    log.info(
        "Panel built for {city}: {rows:,} rows × {cols} cols",
        city=city, rows=len(panel), cols=len(panel.columns),
    )
    return panel


def _build_synthetic_panel(panel: pd.DataFrame, city: str) -> pd.DataFrame:
    """
    Fill a panel skeleton with realistic synthetic data for testing.
    Each city is seeded deterministically so results are reproducible.
    """
    from src.ingest.vulnerability_ingest import CITY_VULNERABILITY_PRIORS

    n = len(panel)
    rng = np.random.default_rng(seed=abs(hash(city)) % (2**31))
    priors = CITY_VULNERABILITY_PRIORS.get(city, {})

    # Temperature varies seasonally; add city-specific base
    city_base_temp = {
        "mumbai": 28, "delhi": 25, "bengaluru": 23, "chennai": 29,
        "hyderabad": 27, "pune": 26, "ahmedabad": 29, "kolkata": 27,
        "surat": 28, "indore": 26,
    }.get(city, 26)

    months = pd.to_datetime(panel["date"]).dt.month.values
    seasonal_t = city_base_temp + 5 * np.sin((months - 3) * np.pi / 6)
    panel["temp_mean_c"] = seasonal_t + rng.normal(0, 1.5, n)
    panel["dewpoint_mean_c"] = panel["temp_mean_c"] - rng.uniform(5, 12, n)

    # Precipitation: monsoon peak June–September
    precip_base = np.where(
        (months >= 6) & (months <= 9),
        rng.exponential(80, n),
        rng.exponential(10, n),
    )
    panel["precip_sum_mm"] = precip_base.clip(0)

    panel["wind_speed"] = rng.exponential(3, n).clip(0.5, 15)
    panel["radiation"] = (
        200 + 100 * np.cos((months - 4) * np.pi / 6) + rng.normal(0, 15, n)
    ).clip(50, 500)
    panel["soil_moisture"] = (
        0.2 + 0.15 * np.sin((months - 7) * np.pi / 6) + rng.normal(0, 0.03, n)
    ).clip(0.05, 0.5)

    panel["ndvi"] = (
        0.35 + 0.15 * np.sin((months - 7) * np.pi / 6) + rng.normal(0, 0.05, n)
    ).clip(0, 1)

    panel["lst_c"] = panel["temp_mean_c"] + rng.uniform(2, 8, n)
    panel["pm25"] = (
        45 - 15 * np.sin((months - 7) * np.pi / 6) + rng.normal(0, 5, n)
    ).clip(5, 150)
    panel["built_up_fraction"] = rng.beta(2, 2, n).clip(0, 1)

    panel["road_density_km_km2"] = rng.exponential(8, n).clip(0)
    panel["building_density"] = rng.exponential(300, n).clip(0)
    panel["building_fp_fraction"] = rng.beta(2, 3, n).clip(0, 1)
    panel["green_space_fraction"] = rng.beta(1, 5, n).clip(0, 1)

    for col, default in [
        ("bpl_pct", 0.18), ("slum_pct", 0.30),
        ("elderly_pct", 0.10), ("literacy_pct", 0.85),
    ]:
        base = priors.get(col, default)
        panel[col] = (base + rng.normal(0, 0.03, n)).clip(0, 1)

    log.info("Synthetic panel built for {city}: {n} rows", city=city, n=n)
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
