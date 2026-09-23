import yaml
from pathlib import Path


def load_config(config_path: str = "config.yml") -> dict:
    """
    Loads the YAML configuration file.

    Args:
        config_path (str): Path to config.yml file

    Returns:
        dict: Parsed configuration dictionary
    """

    config_file = Path(config_path)

    # Check if config file exists
    if not config_file.exists():
        raise FileNotFoundError(f"{config_path} not found.")

    # Open and load YAML
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config