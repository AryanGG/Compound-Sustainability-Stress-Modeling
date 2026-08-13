"""
generate_report.py
───────────────────
CLI entry point for generating SSI visualisation reports.

Usage:
    python generate_report.py --city mumbai
    python generate_report.py --city all
    python generate_report.py --city delhi --source processed   (raw variables, no SSI)
    python generate_report.py --city mumbai --out reports/custom.html
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
import pandas as pd

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger("generate_report")


INDICATOR_COLS = [
    "heat_stress_idx", "water_stress_idx", "pollution_idx",
    "vegetation_idx", "urban_vulnerability_idx",
]
SSI_COLS = ["ssi_value", "ssi_band", "archetype_id", "anomaly_flag"]


def _load_panel(city: str, source: str) -> pd.DataFrame | None:
    """
    Load a city panel from either the final or intermediate Parquet store.

    Args:
        city  : City slug.
        source: 'final' (with SSI) or 'processed' (raw variables only).

    Returns:
        DataFrame or None if file not found.
    """
    config = load_config()

    if source == "final":
        path = Path(config["paths"]["h3_panel"]) / "final" / f"{city}.parquet"
    else:
        path = Path(config["paths"]["processed_data"]) / f"{city}.parquet"

    if not path.exists():
        log.warning("Panel not found for {city} at {p}", city=city, p=path)
        return None

    df = pd.read_parquet(path)
    log.info("Loaded {city}: {rows:,} rows x {cols} cols", city=city, rows=len(df), cols=len(df.columns))
    return df


def _ensure_ssi_columns(df: pd.DataFrame, city: str) -> pd.DataFrame:
    """
    If SSI columns are missing (e.g. loaded from 'processed' store),
    run the feature + SSI pipeline inline on the panel.
    """
    missing_indicators = [c for c in INDICATOR_COLS if c not in df.columns]
    missing_ssi = [c for c in SSI_COLS if c not in df.columns]

    if not missing_indicators and not missing_ssi:
        return df   # All good, nothing to compute

    log.info("SSI/indicator columns missing — running feature pipeline inline...")

    from src.features.heat_stress       import add_heat_stress_idx
    from src.features.water_stress      import add_water_stress_idx
    from src.features.pollution_exposure import add_pollution_idx
    from src.features.vegetation_degradation import add_vegetation_idx
    from src.features.urban_vulnerability import add_urban_vulnerability_idx
    from src.features.ssi               import compute_ssi

    if "heat_stress_idx" not in df.columns:
        df = add_heat_stress_idx(df)
    if "water_stress_idx" not in df.columns:
        df = add_water_stress_idx(df)
    if "pollution_idx" not in df.columns:
        df = add_pollution_idx(df)
    if "vegetation_idx" not in df.columns:
        df = add_vegetation_idx(df)
    if "urban_vulnerability_idx" not in df.columns:
        df = add_urban_vulnerability_idx(df)
    if "ssi_value" not in df.columns:
        df = compute_ssi(df, city)

    return df


@click.command()
@click.option(
    "--city", default="mumbai",
    help="City slug (e.g. mumbai) or 'all' to process every available city.",
)
@click.option(
    "--source", default="final",
    type=click.Choice(["final", "processed"]),
    help="Load from final panel (with SSI) or intermediate processed panel.",
)
@click.option(
    "--out", default=None,
    help="Output HTML path override (ignored when --city all).",
)
def main(city: str, source: str, out: str | None) -> None:
    """
    Generate an interactive SSI visualisation report for one or all cities.

    Examples:

        python generate_report.py --city mumbai

        python generate_report.py --city all

        python generate_report.py --city delhi --source processed
    """
    config   = load_config()
    all_cities = config.get("cities", [])

    cities_to_run = all_cities if city == "all" else [city]

    for city_id in cities_to_run:
        print(f"\n{'='*60}")
        print(f"  Generating report for: {city_id.upper()}")
        print(f"{'='*60}")

        df = _load_panel(city_id, source)
        if df is None:
            print(f"  [SKIP] No data found for {city_id}. "
                  f"Run: python run_pipeline.py --city {city_id} --phase all --synthetic")
            continue

        df = _ensure_ssi_columns(df, city_id)

        # Determine output path
        if out and city == city_id:   # single city with explicit path
            out_path = Path(out)
        else:
            out_path = Path("reports") / f"{city_id}_ssi_report.html"

        # Generate the report
        from src.viz.report import generate_report
        generate_report(city_id, df, out_path)

        print(f"\n  Open in browser:")
        print(f"  file:///{out_path.resolve().as_posix()}")

    print("\nDone.")


if __name__ == "__main__":
    main()
