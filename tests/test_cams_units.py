"""
tests/test_cams_units.py
────────────────────────
Step 05 unit test:
Asserts unit conversion from CAMS NetCDF (kg/m³) to standard air quality units (µg/m³).
A value of 2.5e-8 kg/m³ must convert exactly to 25.0 µg/m³.
"""

from pathlib import Path
import numpy as np
import xarray as xr
from src.ingest.cams_pm25_ingest import extract_pm25_ug_m3


def test_cams_unit_conversion(tmp_path: Path):
    # Create fake 1x1 NetCDF with raw CAMS value 2.5e-8 kg/m³
    nc_path = tmp_path / "fake_cams.nc"
    da = xr.DataArray(
        np.array([[2.5e-8]], dtype=np.float32),
        coords={"latitude": [19.0], "longitude": [72.8]},
        dims=["latitude", "longitude"],
        name="pm2p5",
    )
    ds = da.to_dataset()
    ds.to_netcdf(nc_path)

    converted_val = extract_pm25_ug_m3(nc_path)
    assert np.isclose(converted_val, 25.0, atol=1e-5), f"Expected 25.0, got {converted_val}"
