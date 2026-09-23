"""
src/ingest/era5_ingest.py
──────────────────────────
ERA5 / ERA5-Land data ingestion via the CDS API.

Downloads 8 variables per (city, month):
  2m_temperature, 2m_dewpoint_temperature, total_precipitation,
  10m_u_component_of_wind, 10m_v_component_of_wind,
  surface_solar_radiation_downwards,
  volumetric_soil_water_layer_1, volumetric_soil_water_layer_2

Output files: data/raw/era5/{city}/{year}_{month:02d}.nc
"""

from __future__ import annotations

import calendar
from pathlib import Path
from typing import Optional

import pandas as pd

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

ERA5_VARIABLES = [
    "2m_temperature",
    "2m_dewpoint_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "surface_solar_radiation_downwards",
    "volumetric_soil_water_layer_1",
    "volumetric_soil_water_layer_2",
]


def _make_day_list(year: int, month: int) -> list[str]:
    """Return zero-padded day strings for all days in a given month."""
    n_days = calendar.monthrange(year, month)[1]
    return [f"{d:02d}" for d in range(1, n_days + 1)]


def _bbox_to_era5_area(bbox: dict, margin: float = 0.5) -> list[float]:
    """
    Convert bbox dict → ERA5 'area' parameter [N, W, S, E] with margin.

    Args:
        bbox  : Dict with min_lon, min_lat, max_lon, max_lat.
        margin: Extra margin in degrees around the city bbox.

    Returns:
        [north, west, south, east] list expected by CDS API.
    """
    return [
        bbox["max_lat"] + margin,   # North
        bbox["min_lon"] - margin,   # West
        bbox["min_lat"] - margin,   # South
        bbox["max_lon"] + margin,   # East
    ]


def download_era5_month(
    city: str,
    year: int,
    month: int,
    bbox: dict,
    out_dir: Path,
    overwrite: bool = False,
) -> Path:
    """
    Download ERA5 NetCDF for a single city × month.

    Args:
        city    : City slug (used for sub-folder naming).
        year    : 4-digit year.
        month   : Month number 1–12.
        bbox    : City bounding box dict.
        out_dir : Root directory for raw ERA5 files.
        overwrite: Re-download even if file already exists.

    Returns:
        Path to the downloaded NetCDF file.

    Raises:
        ImportError  : If cdsapi is not installed.
        RuntimeError : If CDS download fails.
    """
    try:
        import cdsapi
    except ImportError as exc:
        raise ImportError(
            "cdsapi is required for ERA5 ingestion. "
            "Install with: pip install cdsapi"
        ) from exc

    city_dir = out_dir / city
    city_dir.mkdir(parents=True, exist_ok=True)

    nc_path = city_dir / f"{year}_{month:02d}.nc"

    if nc_path.exists() and not overwrite:
        log.debug(
            "ERA5 file already exists, skipping: {path}", path=nc_path
        )
        return nc_path

    config = load_config()
    era5_cfg = config.get("era5", {})

    request = {
        "product_type": era5_cfg.get("product_type", "reanalysis"),
        "variable": ERA5_VARIABLES,
        "year": str(year),
        "month": f"{month:02d}",
        "day": _make_day_list(year, month),
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "area": _bbox_to_era5_area(bbox),
        "grid": [
            era5_cfg.get("grid_resolution", 0.1),
            era5_cfg.get("grid_resolution", 0.1),
        ],
        "format": "netcdf",
    }

    log.info(
        "Downloading ERA5 {city} {year}-{month:02d}...",
        city=city,
        year=year,
        month=month,
    )

    try:
        client = cdsapi.Client(quiet=True)
        client.retrieve(
            era5_cfg.get("dataset", "reanalysis-era5-single-levels"),
            request,
            str(nc_path),
        )

        # CDS API v2 returns a ZIP containing two NetCDF files:
        #   data_stream-oper_stepType-instant.nc  (t2m, d2m, u10, v10, swvl1, swvl2)
        #   data_stream-oper_stepType-accum.nc    (tp, ssrd)
        # Detect if the downloaded file is actually a ZIP and merge NetCDFs.
        import zipfile as _zipfile
        if _zipfile.is_zipfile(nc_path):
            import tempfile, shutil
            import xarray as xr

            with _zipfile.ZipFile(nc_path) as zf:
                nc_members = [m for m in zf.namelist() if m.endswith(".nc")]
                tmp_dir = Path(tempfile.mkdtemp())
                try:
                    datasets = []
                    for member in nc_members:
                        extracted = tmp_dir / member
                        zf.extract(member, tmp_dir)
                        ds = xr.open_dataset(extracted, engine="netcdf4")
                        datasets.append(ds)

                    if datasets:
                        merged = xr.merge(datasets, compat="override")
                        # Save back as a proper NetCDF replacing the ZIP
                        nc_path.unlink()
                        merged.to_netcdf(str(nc_path))
                        for ds in datasets:
                            ds.close()
                        merged.close()
                        log.info(
                            "ERA5 merged {n} NetCDF streams for {city} {year}-{month:02d}",
                            n=len(datasets), city=city, year=year, month=month,
                        )
                finally:
                    shutil.rmtree(tmp_dir, ignore_errors=True)

        log.success(
            "ERA5 saved -> {path}", path=nc_path
        )
    except Exception as exc:
        log.error("ERA5 download failed: {err}", err=exc)
        raise RuntimeError(f"ERA5 download failed for {city} {year}-{month:02d}") from exc

    return nc_path


def ingest_era5_city(
    city: str,
    bbox: dict,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    overwrite: bool = False,
) -> list[Path]:
    """
    Ingest all ERA5 monthly files for a city over the configured time range.

    Args:
        city        : City slug.
        bbox        : City bounding box dict.
        start_month : Override config start (ISO string 'YYYY-MM').
        end_month   : Override config end.
        overwrite   : Re-download existing files.

    Returns:
        List of paths to downloaded NetCDF files.
    """
    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    out_dir = Path(config["paths"]["raw_data"]) / "era5"

    months = pd.date_range(start=start, end=end, freq="MS")
    paths = []

    for dt in months:
        try:
            path = download_era5_month(
                city=city,
                year=dt.year,
                month=dt.month,
                bbox=bbox,
                out_dir=out_dir,
                overwrite=overwrite,
            )
            paths.append(path)
        except RuntimeError as exc:
            log.warning("Skipping {city} {dt}: {err}", city=city, dt=dt, err=exc)

    log.info(
        "ERA5 ingestion complete for {city}: {n} files",
        city=city,
        n=len(paths),
    )
    return paths
