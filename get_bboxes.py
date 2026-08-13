import json
import osmnx as ox

cities = [
    "mumbai", "delhi", "bengaluru", "chennai", "hyderabad", "kolkata", "pune", "ahmedabad",
    "surat", "jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "visakhapatnam",
    "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "ranchi", "meerut",
    "rajkot", "varanasi", "srinagar", "aurangabad", "amritsar", "coimbatore"
]

bboxes = {}
try:
    with open('cities_bbox.json', 'r') as f:
        bboxes = json.load(f)
except FileNotFoundError:
    pass

for city in cities:
    if city in bboxes:
        print(f"Skipping {city}, already exists.")
        continue
    query = f"{city}, India"
    print(f"Fetching bbox for {query}...")
    try:
        gdf = ox.geocode_to_gdf(query)
        bbox = gdf.bounds.iloc[0]
        bboxes[city] = {
            "min_lon": float(bbox['minx']),
            "min_lat": float(bbox['miny']),
            "max_lon": float(bbox['maxx']),
            "max_lat": float(bbox['maxy']),
            "primary_stresses": ["heat", "water", "pollution"],
            "state": "Unknown"
        }
    except Exception as e:
        print(f"Failed to fetch {city}: {e}")

with open('cities_bbox.json', 'w') as f:
    json.dump(bboxes, f, indent=2)
print("Updated cities_bbox.json")
