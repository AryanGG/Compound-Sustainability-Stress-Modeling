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


INDICATOR_MAP = {
    "heat_v2": "heat_stress_idx",
    "water_v2": "water_stress_idx",
    "pollution_v2": "pollution_idx",
    "veg_v2": "vegetation_idx",
    "exposure_v2": "urban_vulnerability_idx",
}


def _load_v2_panel(city: str) -> pd.DataFrame | None:
    """
    Load a city panel from the v2 canonical Parquet store.
    """
    config = load_config()
    v2_dir = Path(config.get("v2", {}).get("paths", {}).get("v2", "data/h3_panel/v2"))
    path = v2_dir / f"{city}.parquet"

    if not path.exists():
        log.warning("v2 Panel not found for {city} at {p}", city=city, p=path)
        return None

    df = pd.read_parquet(path)
    log.info("Loaded v2 {city}: {rows:,} rows x {cols} cols", city=city, rows=len(df), cols=len(df.columns))

    # Standardize column mappings for visual reports
    df["ssi_value"] = df["ssi_v2"]
    if "ssi_band_v2" in df.columns:
        df["ssi_band"] = df["ssi_band_v2"]
    else:
        df["ssi_band"] = "Moderate"

    for v2_col, disp_col in INDICATOR_MAP.items():
        if v2_col in df.columns:
            df[disp_col] = df[v2_col]

    # Compute anomaly flag (top 10% monthly or compound event)
    q90 = df["ssi_v2"].quantile(0.90)
    df["anomaly_flag"] = (df["ssi_v2"] >= q90).astype(int)

    # Attach hex-level archetypes if available
    archetypes_file = Path("results/archetypes__hex_assignments.csv")
    if archetypes_file.exists():
        try:
            arch_df = pd.read_csv(archetypes_file)
            if "h3_index" in arch_df.columns and "archetype_id" in arch_df.columns:
                df = df.merge(
                    arch_df[["h3_index", "archetype_id"]],
                    on="h3_index",
                    how="left",
                )
                df["archetype_id"] = df["archetype_id"].fillna(1).astype(int)
        except Exception as e:
            log.warning("Could not merge archetypes: {e}", e=e)

    if "archetype_id" not in df.columns:
        df["archetype_id"] = 1

    return df


@click.command()
@click.option(
    "--city", default="mumbai",
    help="City slug (e.g. mumbai, coimbatore) or 'all' to process all v2 cities.",
)
@click.option(
    "--out", default=None,
    help="Output HTML path override (ignored when --city all).",
)
def main(city: str, out: str | None) -> None:
    """
    Generate an interactive SSI v2 visualisation report for one or all cities.
    """
    config = load_config()
    v2_cities = config.get("v2", {}).get("cities", ["mumbai", "coimbatore"])

    cities_to_run = v2_cities if city == "all" else [city]

    for city_id in cities_to_run:
        print(f"\n{'='*60}")
        print(f"  Generating v2 report for: {city_id.upper()}")
        print(f"{'='*60}")

        df = _load_v2_panel(city_id)
        if df is None:
            print(f"  [SKIP] No v2 data found for {city_id}. Run: python run_v2.py --stage score --city {city_id}")
            continue

        # Determine output path
        if out and city == city_id:
            out_path = Path(out)
        else:
            out_path = Path("reports") / f"{city_id}_ssi_report.html"

        # Generate report
        from src.viz.report import generate_report
        generate_report(city_id, df, out_path)

        # For primary city (mumbai), also write to dashboard/index.html
        if city_id == "mumbai":
            dash_dir = Path("dashboard")
            dash_dir.mkdir(parents=True, exist_ok=True)
            dash_file = dash_dir / "index.html"
            dash_file.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  Dashboard updated -> {dash_file.resolve().as_posix()}")

        print(f"\n  Open in browser:")
        print(f"  file:///{out_path.resolve().as_posix()}")

    print("\nDone.")


if __name__ == "__main__":
    main()
