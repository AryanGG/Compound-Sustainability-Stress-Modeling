import cdsapi

client = cdsapi.Client()

dataset = "reanalysis-era5-single-levels"

request = {
    "product_type": "reanalysis",
    "variable": "2m_temperature",
    "year": "2026",
    "month": "01",
    "day": ["01", "02", "03"],
    "time": ["00:00", "06:00", "12:00", "18:00"],
    "area": [28.9, 76.8, 28.4, 77.5],  # Delhi
    "grid": [0.1, 0.1],
    "format": "netcdf"
}

client.retrieve(dataset, request, "temperature.nc")

print("Download complete")