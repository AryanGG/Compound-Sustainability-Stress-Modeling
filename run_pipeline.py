"""
run_pipeline.py
────────────────
Main CLI orchestrator for the Compound SSI pipeline.

Usage:
    python run_pipeline.py --city mumbai --phase all
    python run_pipeline.py --city all --phase all --synthetic
    python run_pipeline.py --city delhi --phase features
    python run_pipeline.py --city mumbai --phase ingest

Phases:
    ingest   → Download raw data (ERA5, Satellite, PM2.5, OSM, Vulnerability)
    process  → Process raw data → per-hex monthly DataFrames
    features → Compute 5 stress indicators
    ssi      → Compute SSI composite + bands + archetypes + anomaly flags
    all      → Run all phases end-to-end

Options:
    --synthetic  Use realistic synthetic data (no API keys required)
    --overwrite  Re-download existing files
    --resolution H3 resolution override (default: 8)
    --start      Start month override (e.g. 2018-01)
    --end        End month override (e.g. 2023-12)
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import pandas as pd

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger("run_pipeline")


def get_city_list(city_arg: str) -> list[str]:
    """Resolve --city 'all' or a single city slug to a list."""
    config = load_config()
    all_cities = config.get("cities", [])
    if city_arg == "all":
        return all_cities
    if city_arg not in all_cities:
        log.warning(
            "City '{c}' not in config.yml cities list. Proceeding anyway.",
            c=city_arg,
        )
    return [city_arg]


# ─── Phase Functions ──────────────────────────────────────────────────────────

def run_ingest(
    city: str,
    bbox: dict,
    overwrite: bool,
    start_month: str | None = None,
    end_month: str | None = None,
) -> None:
    """Run data ingestion for a single city."""
    log.info("=== INGEST phase: {city} ===", city=city)

    # ERA5
    try:
        from src.ingest.era5_ingest import ingest_era5_city
        ingest_era5_city(
            city, bbox,
            start_month=start_month, end_month=end_month,
            overwrite=overwrite,
        )
    except Exception as exc:
        log.error("ERA5 ingestion failed for {city}: {err}", city=city, err=exc)

    # Satellite
    try:
        from src.ingest.satellite_ingest import ingest_satellite_city
        ingest_satellite_city(
            city, bbox,
            start_month=start_month, end_month=end_month,
            overwrite=overwrite,
        )
    except Exception as exc:
        log.error("Satellite ingestion failed for {city}: {err}", city=city, err=exc)

    # PM2.5
    try:
        from src.ingest.pm25_ingest import ingest_pm25_city
        ingest_pm25_city(
            city, bbox,
            start_month=start_month, end_month=end_month,
            overwrite=overwrite,
        )
    except Exception as exc:
        log.error("PM2.5 ingestion failed for {city}: {err}", city=city, err=exc)

    # OSM
    try:
        from src.ingest.osm_ingest import ingest_osm_city
        ingest_osm_city(city, bbox, overwrite=overwrite)
    except Exception as exc:
        log.error("OSM ingestion failed for {city}: {err}", city=city, err=exc)

    # Vulnerability template
    try:
        from src.ingest.vulnerability_ingest import save_vulnerability_template
        save_vulnerability_template()
    except Exception as exc:
        log.warning("Vulnerability template creation failed: {err}", err=exc)


def run_process(
    city: str,
    panel: pd.DataFrame,
    synthetic: bool,
    start_month: str | None = None,
    end_month: str | None = None,
) -> pd.DataFrame:
    """Build the H3 × monthly panel (harmonize step)."""
    log.info("=== PROCESS / HARMONIZE phase: {city} ===", city=city)

    from src.process.harmonize import build_h3_panel
    panel = build_h3_panel(
        city,
        synthetic=synthetic,
        start_month=start_month,
        end_month=end_month,
    )
    return panel


def run_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute all 5 stress indicators on an existing panel."""
    log.info("=== FEATURES phase ===")

    from src.features.heat_stress import add_heat_stress_idx
    from src.features.water_stress import add_water_stress_idx
    from src.features.pollution_exposure import add_pollution_idx
    from src.features.vegetation_degradation import add_vegetation_idx
    from src.features.urban_vulnerability import add_urban_vulnerability_idx

    panel = add_heat_stress_idx(panel)
    panel = add_water_stress_idx(panel)
    panel = add_pollution_idx(panel)
    panel = add_vegetation_idx(panel)
    panel = add_urban_vulnerability_idx(panel)

    return panel


def run_ssi(panel: pd.DataFrame, city: str) -> pd.DataFrame:
    """Compute the SSI composite score and derived columns."""
    log.info("=== SSI phase ===")

    from src.features.ssi import compute_ssi
    panel = compute_ssi(panel, city)
    return panel


def validate_output(panel: pd.DataFrame, city: str) -> bool:
    """
    Quick schema + sanity validation on the output panel.

    Returns True if validation passes.
    """
    required_cols = [
        "city_id", "h3_index", "date",
        "ssi_value", "ssi_band", "archetype_id", "anomaly_flag",
    ]

    missing = [c for c in required_cols if c not in panel.columns]
    if missing:
        log.error("Validation FAILED for {city}: missing columns {m}", city=city, m=missing)
        return False

    if panel["ssi_value"].between(0, 1).mean() < 0.95:
        log.error("Validation FAILED: ssi_value out of [0,1] range")
        return False

    if panel.duplicated(subset=["h3_index", "date"]).any():
        n_dup = panel.duplicated(subset=["h3_index", "date"]).sum()
        log.warning("Validation Warning: {n} duplicate (h3_index, date) rows", n=n_dup)

    log.info(
        "Validation PASSED for {city}: {rows:,} rows × {cols} cols",
        city=city,
        rows=len(panel),
        cols=len(panel.columns),
    )
    return True


def save_final(panel: pd.DataFrame, city: str) -> Path:
    """Save final panel to Parquet with snappy compression."""
    from src.process.harmonize import save_panel
    return save_panel(panel, city, intermediate=False)


def print_summary(panel: pd.DataFrame, city: str) -> None:
    """Print a quick summary of the final panel."""
    log.info("\n" + "-" * 60)
    log.info("SUMMARY for {city}", city=city)
    log.info("Rows: {n:,}", n=len(panel))
    log.info("Cols: {c}", c=len(panel.columns))

    if "date" in panel.columns:
        log.info(
            "Date range: {s} -> {e}",
            s=panel["date"].min(),
            e=panel["date"].max(),
        )

    if "h3_index" in panel.columns:
        log.info("Unique hexes: {n:,}", n=panel["h3_index"].nunique())

    if "ssi_value" in panel.columns:
        log.info("SSI stats: mean={m:.3f}, p50={p:.3f}, p90={p9:.3f}, max={mx:.3f}",
                 m=panel["ssi_value"].mean(),
                 p=panel["ssi_value"].quantile(0.5),
                 p9=panel["ssi_value"].quantile(0.9),
                 mx=panel["ssi_value"].max())

    if "ssi_band" in panel.columns:
        band_dist = panel["ssi_band"].value_counts(normalize=True) * 100
        log.info("SSI Band distribution: {b}", b=band_dist.round(1).to_dict())

    if "anomaly_flag" in panel.columns:
        log.info("Anomaly fraction: {a:.1%}", a=panel["anomaly_flag"].mean())


# ─── CLI ─────────────────────────────────────────────────────────────────────

@click.command()
@click.option("--city", default="mumbai", help="City slug or 'all'")
@click.option(
    "--phase",
    default="all",
    type=click.Choice(["ingest", "process", "features", "ssi", "all"]),
    help="Pipeline phase to run",
)
@click.option("--synthetic", is_flag=True, default=False, help="Use synthetic data (no API keys needed)")
@click.option("--overwrite", is_flag=True, default=False, help="Re-download existing files")
@click.option("--resolution", default=None, type=int, help="H3 resolution override")
@click.option("--start", default=None, help="Start month YYYY-MM")
@click.option("--end", default=None, help="End month YYYY-MM")
def main(
    city: str,
    phase: str,
    synthetic: bool,
    overwrite: bool,
    resolution: int | None,
    start: str | None,
    end: str | None,
) -> None:
    """
    Compound Sustainability Stress Index (SSI) Pipeline.

    Example:
        python run_pipeline.py --city mumbai --phase all --synthetic
    """
    import json

    config = load_config()
    cities = get_city_list(city)

    with open("cities_bbox.json") as f:
        all_bboxes = json.load(f)

    for city_id in cities:
        log.info("=" * 60)
        log.info("Processing city: {city}", city=city_id)
        log.info("Phase: {phase} | Synthetic: {syn}", phase=phase, syn=synthetic)
        log.info("=" * 60)

        bbox = all_bboxes.get(city_id, {})

        panel = pd.DataFrame()

        # ── Ingest ───────────────────────────────────────────────────────────
        if phase in ("ingest", "all") and not synthetic:
            run_ingest(city_id, bbox, overwrite, start_month=start, end_month=end)

        # ── Process / Harmonize ───────────────────────────────────────────────
        if phase in ("process", "all"):
            panel = run_process(city_id, panel, synthetic, start_month=start, end_month=end)
            if panel.empty:
                log.error("Empty panel for {city}. Stopping.", city=city_id)
                continue

            # Save intermediate
            int_path = (
                Path(config["paths"]["processed_data"]) / f"{city_id}.parquet"
            )
            int_path.parent.mkdir(parents=True, exist_ok=True)
            panel.to_parquet(int_path, index=False)
            log.info("Intermediate panel saved -> {p}", p=int_path)

        elif phase in ("features", "ssi"):
            # Load previously processed intermediate panel
            int_path = (
                Path(config["paths"]["processed_data"]) / f"{city_id}.parquet"
            )
            if int_path.exists():
                panel = pd.read_parquet(int_path)
                log.info("Loaded intermediate panel: {p}", p=int_path)
            else:
                log.error(
                    "No intermediate panel for {city}. Run 'process' phase first.",
                    city=city_id,
                )
                continue

        # ── Features ──────────────────────────────────────────────────────────
        if phase in ("features", "all"):
            panel = run_features(panel)

        # ── SSI ───────────────────────────────────────────────────────────────
        if phase in ("ssi", "all"):
            panel = run_ssi(panel, city_id)

        # ── Validate & Save ───────────────────────────────────────────────────
        if phase in ("ssi", "all") and not panel.empty:
            valid = validate_output(panel, city_id)
            if valid:
                out_path = save_final(panel, city_id)
                log.info("Final output -> {p}", p=out_path)

        print_summary(panel, city_id)

    log.info("Pipeline complete.")


if __name__ == "__main__":
    main()
