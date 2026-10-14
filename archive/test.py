from src.utils.config_loader import load_config
from src.utils.h3_utils import generate_h3_cells_for_city

config = load_config()

resolution = config["spatial"]["h3_resolution"]

cells = generate_h3_cells_for_city("mumbai", resolution)

print("Total H3 cells:", len(cells))
print("First 5:", cells[:5])