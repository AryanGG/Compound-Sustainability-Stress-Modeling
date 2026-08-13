import pandas as pd
import folium
import h3
import numpy as np
from scipy.spatial import cKDTree

# -------------------------
# LOAD DATA
# -------------------------
df = pd.read_csv("data/processed/temperature_h3.csv")

# use single timestamp
df = df[df["valid_time"] == df["valid_time"].iloc[0]]

# -------------------------
# STEP 1: CREATE FULL H3 GRID (RES = 6)
# -------------------------
lat_range = np.arange(28.4, 28.9, 0.02)
lon_range = np.arange(76.8, 77.5, 0.02)

all_hexes = set()

for lat in lat_range:
    for lon in lon_range:
        all_hexes.add(h3.latlng_to_cell(lat, lon, 6))  # 👈 resolution 6

grid_df = pd.DataFrame({"h3_id": list(all_hexes)})

# -------------------------
# STEP 2: NEAREST NEIGHBOR
# -------------------------
points = df.copy()

coords = [h3.cell_to_latlng(h) for h in points["h3_id"]]
tree = cKDTree(coords)

def assign_value(row):
    lat, lon = h3.cell_to_latlng(row["h3_id"])
    _, idx = tree.query([lat, lon])
    return points.iloc[idx]["temperature_c"]

grid_df["temperature_c"] = grid_df.apply(assign_value, axis=1)

df = grid_df

# -------------------------
# STEP 3: VISUALIZATION
# -------------------------
m = folium.Map(location=[28.6, 77.2], zoom_start=11, tiles="CartoDB positron")
min_temp = df["temperature_c"].min()
max_temp = df["temperature_c"].max()

def get_color(temp):
    norm = (temp - min_temp) / (max_temp - min_temp + 1e-6)
    return f"#{int(255*norm):02x}0000"

for _, row in df.iterrows():
    boundary = h3.cell_to_boundary(row["h3_id"])
    boundary = [(lat, lon) for lat, lon in boundary]

    folium.Polygon(
        locations=boundary,
        fill=True,
        fill_color=get_color(row["temperature_c"]),
        fill_opacity=0.6,
        color=None
    ).add_to(m)

m.save("temperature_h3_map.html")

print("Resolution 6 map generated")