import xarray as xr
import pandas as pd
import h3

ds = xr.open_dataset("temperature.nc")

df = ds.to_dataframe().reset_index()

df = df[["valid_time", "latitude", "longitude", "t2m"]]

df["temperature_c"] = df["t2m"] - 273.15

df["h3_id"] = df.apply(
    lambda row: h3.latlng_to_cell(row["latitude"], row["longitude"], 6),
    axis=1
)

df_h3 = df.groupby(["h3_id", "valid_time"])["temperature_c"].mean().reset_index()

df_h3.to_csv("data/processed/temperature_h3.csv", index=False)

print("Saved successfully")