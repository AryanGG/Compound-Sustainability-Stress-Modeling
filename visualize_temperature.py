import pandas as pd
import folium
import h3

# Load processed data
df = pd.read_csv("data/processed/sample_temperature_h3.csv")

# Create base map centered on Mumbai
m = folium.Map(location=[19.07, 72.88], zoom_start=10)

# Normalize temperature for coloring
min_temp = df["temperature"].min()
max_temp = df["temperature"].max()

def get_color(value):
    # simple blue to red scale
    ratio = (value - min_temp) / (max_temp - min_temp)
    red = int(255 * ratio)
    blue = 255 - red
    return f"#{red:02x}00{blue:02x}"

# Draw each H3 cell
for _, row in df.iterrows():
    boundary = h3.cell_to_boundary(row["h3_id"])

    folium.Polygon(
        locations=boundary,
        color="black",
        weight=1,
        fill=True,
        fill_color=get_color(row["temperature"]),
        fill_opacity=0.6,
        tooltip=f"Temp: {row['temperature']:.2f}"
    ).add_to(m)

# Save map
m.save("temperature_h3_map.html")

print("Map saved as temperature_h3_map.html")