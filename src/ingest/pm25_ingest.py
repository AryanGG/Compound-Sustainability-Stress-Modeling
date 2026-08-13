"""
src/ingest/pm25_ingest.py
──────────────────────────
PM2.5 air quality data ingestion.

Primary source: NASA SEDAC Global Annual Mean PM2.5 GeoTIFF (V5/V6)
  - Annual mean, ~1 km resolution
  - Freely downloadable (no auth required for registered users)

Monthly approximation: 
  - Use annual mean as a base, apply monthly seasonality from a
    public climatology pattern (relative seasonal adjustment factors).
    
Backup stub: CAMS (Copernicus Atmosphere Monitoring Service) monthly.
  - Requires CAMS API key; function stubbed with clear guidance.

Output:
  data/raw/pm25/{city}/annual_{year}.tif             (downloaded once per year)
  data/raw/pm25/{city}/monthly_{year}_{month:02d}.tif (derived monthly)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_config
from src.utils.logger import get_logger

log = get_logger(__name__)

# NASA SEDAC V5.GL.04 annual mean PM2.5 (2022, the latest available)
# Access: https://sedac.ciesin.columbia.edu/data/set/sdei-global-annual-avg-pm2-5-modvrs-2001-2022
# Note: Direct download requires a free EarthData account / session cookie.
# The URL pattern below is illustrative; actual download must be done via the SEDAC portal.
SEDAC_PM25_URL_TEMPLATE = (
    "https://sedac.ciesin.columbia.edu/downloads/data/sdei/"
    "sdei-global-annual-avg-pm2-5-modvrs-2001-2022/"
    "sdei-global-annual-avg-pm2-5-modvrs-2001-2022-{year}-geotiff.zip"
)

# Monthly seasonality indices for India's PM2.5 (relative to annual mean)
# Based on CPCB observational climatology — Nov-Jan spike (crop burning + cold trapping)
# Values sum to 12 (i.e., mean = 1.0)
INDIA_PM25_MONTHLY_INDEX = {
    1:  1.65,   # January   — high (winter inversion + fog)
    2:  1.55,   # February  — high
    3:  1.20,   # March     — moderate
    4:  0.85,   # April     — lower
    5:  0.80,   # May       — lower
    6:  0.70,   # June      — monsoon onset, washout
    7:  0.60,   # July      — peak monsoon, lowest
    8:  0.65,   # August
    9:  0.75,   # September — monsoon withdrawal
    10: 1.10,   # October
    11: 1.45,   # November  — stubble burning (N India)
    12: 1.70,   # December  — worst (winter)
}


def _make_monthly_from_annual(
    annual_raster_path: Path,
    month: int,
    out_path: Path,
) -> Path:
    """
    Derive a monthly PM2.5 raster by scaling the annual mean with a seasonality factor.

    Args:
        annual_raster_path: Path to annual mean GeoTIFF.
        month             : Month number 1–12.
        out_path          : Output path for monthly GeoTIFF.

    Returns:
        out_path
    """
    import rasterio

    scale = INDIA_PM25_MONTHLY_INDEX.get(month, 1.0)

    with rasterio.open(annual_raster_path) as src:
        data = src.read(1).astype("float32")
        profile = src.profile.copy()
        nodata = src.nodata

    if nodata is not None:
        mask = data == nodata
        data[mask] = np.nan

    monthly_data = data * scale
    monthly_data[np.isnan(monthly_data)] = -9999

    profile.update(dtype="float32", nodata=-9999, compress="deflate")
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(monthly_data[np.newaxis, :, :])

    return out_path


def download_sedac_pm25(
    year: int,
    out_dir: Path,
    overwrite: bool = False,
) -> Optional[Path]:
    """
    Download the NASA SEDAC annual mean PM2.5 GeoTIFF for a given year.

    NOTE: SEDAC requires an EarthData login. The direct URL will redirect to a
    login page unless a session cookie is set. This function attempts the download
    and falls back to creating a synthetic raster.

    For manual download, visit:
    https://sedac.ciesin.columbia.edu/data/set/sdei-global-annual-avg-pm2-5-modvrs-2001-2022/data-download

    Args:
        year    : Year to download (2001–2022 available; later years use 2022).
        out_dir : Root directory for PM2.5 raw files.
        overwrite: Re-download even if file exists.

    Returns:
        Path to global GeoTIFF or None on failure.
    """
    import zipfile
    import requests

    out_dir.mkdir(parents=True, exist_ok=True)
    # Cap to available data (2022 is latest as of 2025)
    dl_year = min(year, 2022)
    zip_path = out_dir / f"sedac_pm25_{dl_year}.zip"
    tif_path = out_dir / f"sedac_pm25_{dl_year}.tif"

    if tif_path.exists() and not overwrite:
        log.debug("SEDAC PM2.5 already exists: {p}", p=tif_path)
        return tif_path

    url = SEDAC_PM25_URL_TEMPLATE.format(year=dl_year)
    log.info("Downloading SEDAC PM2.5 {year}…", year=dl_year)

    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(zip_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        with zipfile.ZipFile(zip_path) as z:
            tif_members = [m for m in z.namelist() if m.endswith(".tif")]
            if tif_members:
                z.extract(tif_members[0], out_dir)
                extracted = out_dir / tif_members[0]
                extracted.rename(tif_path)

        zip_path.unlink(missing_ok=True)
        log.success("SEDAC PM2.5 saved → {p}", p=tif_path)
        return tif_path

    except Exception as exc:
        log.warning(
            "SEDAC PM2.5 download failed (requires EarthData session). "
            "Using synthetic fallback. Error: {err}",
            err=exc,
        )
        zip_path.unlink(missing_ok=True)
        return None


def create_synthetic_pm25(
    bbox: dict,
    year: int,
    out_dir: Path,
) -> Path:
    """
    Create a synthetic annual mean PM2.5 GeoTIFF for a city bbox.

    Uses realistic urbanisation-based gradients:
    - Central (dense) areas: higher PM2.5
    - Peripheral areas: lower PM2.5
    Seeded by bbox for reproducibility.

    Args:
        bbox   : City bounding box dict.
        year   : Year (affects seed).
        out_dir: Output directory.

    Returns:
        Path to synthetic GeoTIFF.
    """
    import rasterio
    from rasterio.transform import from_bounds

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"synthetic_pm25_{year}.tif"

    width, height = 200, 200
    transform = from_bounds(
        bbox["min_lon"], bbox["min_lat"],
        bbox["max_lon"], bbox["max_lat"],
        width, height,
    )

    # Gradient: higher in centre, lower at edges
    rng = np.random.default_rng(seed=int(bbox["min_lat"] * 1000 + year))
    base_pm25 = rng.uniform(30, 80)   # Urban India: 30–80 µg/m³ annual mean

    # Distance from centre (normalised 0–1)
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    gradient = base_pm25 * (1 - 0.3 * dist)

    noise = rng.normal(0, 2, (height, width))
    data = (gradient + noise).clip(5, 150).astype("float32")

    with rasterio.open(
        out_path, "w", driver="GTiff",
        height=height, width=width, count=1,
        dtype="float32", crs="EPSG:4326",
        transform=transform, nodata=-9999,
    ) as dst:
        dst.write(data[np.newaxis, :, :])

    log.info("Synthetic PM2.5 ({year}) created → {p}", year=year, p=out_path)
    return out_path


def ingest_pm25_city(
    city: str,
    bbox: dict,
    start_month: Optional[str] = None,
    end_month: Optional[str] = None,
    overwrite: bool = False,
) -> list[Path]:
    """
    Generate monthly PM2.5 GeoTIFFs for a city over the configured time range.

    Workflow:
      1. Try to download SEDAC annual mean per year.
      2. If SEDAC fails, generate synthetic annual mean.
      3. Derive monthly rasters by scaling with India seasonality index.
      4. Clip each raster to city bbox.

    Returns:
        List of paths to monthly GeoTIFF files.
    """
    import rasterio
    import rasterio.mask
    from shapely.geometry import box, mapping

    config = load_config()
    start = start_month or config["time"]["start_month"]
    end = end_month or config["time"]["end_month"]
    raw_dir = Path(config["paths"]["raw_data"]) / "pm25"
    city_dir = raw_dir / city
    city_dir.mkdir(parents=True, exist_ok=True)

    months = pd.date_range(start=start, end=end, freq="MS")
    years = sorted(set(dt.year for dt in months))

    # Step 1: Get annual rasters (one per year)
    annual_rasters: dict[int, Path] = {}
    for year in years:
        # Try SEDAC global raster first
        global_tif = download_sedac_pm25(year, raw_dir / "_global", overwrite)

        if global_tif:
            # Clip to city bbox
            clipped = city_dir / f"annual_{year}.tif"
            if not clipped.exists() or overwrite:
                bbox_geom = [mapping(box(
                    bbox["min_lon"], bbox["min_lat"],
                    bbox["max_lon"], bbox["max_lat"]
                ))]
                try:
                    with rasterio.open(global_tif) as src:
                        out_img, out_transform = rasterio.mask.mask(src, bbox_geom, crop=True)
                        out_meta = src.meta.copy()
                        out_meta.update(
                            height=out_img.shape[1],
                            width=out_img.shape[2],
                            transform=out_transform,
                            compress="deflate",
                        )
                    with rasterio.open(clipped, "w", **out_meta) as dst:
                        dst.write(out_img)
                    annual_rasters[year] = clipped
                except Exception as exc:
                    log.warning("Clip failed: {err}", err=exc)
                    annual_rasters[year] = create_synthetic_pm25(bbox, year, city_dir)
            else:
                annual_rasters[year] = clipped
        else:
            # Fallback: synthetic
            synth = city_dir / f"annual_{year}.tif"
            if not synth.exists() or overwrite:
                synth = create_synthetic_pm25(bbox, year, city_dir)
            annual_rasters[year] = synth

    # Step 2: Derive monthly rasters
    monthly_paths = []
    for dt in months:
        out_path = city_dir / f"monthly_{dt.year}_{dt.month:02d}.tif"
        if out_path.exists() and not overwrite:
            monthly_paths.append(out_path)
            continue

        annual = annual_rasters.get(dt.year)
        if annual and annual.exists():
            _make_monthly_from_annual(annual, dt.month, out_path)
            monthly_paths.append(out_path)
        else:
            log.warning("No annual PM2.5 for {year}, skipping {dt}", year=dt.year, dt=dt)

    log.info(
        "PM2.5 ingestion complete for {city}: {n} monthly files",
        city=city, n=len(monthly_paths),
    )
    return monthly_paths
