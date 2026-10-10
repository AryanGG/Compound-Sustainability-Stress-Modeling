import os
import yaml
from pathlib import Path


def load_config(config_path: str = "config.yml") -> dict:
    """
    Loads the YAML configuration file and ensures .env variables
    are loaded into os.environ.

    Args:
        config_path (str): Path to config.yml file

    Returns:
        dict: Parsed configuration dictionary
    """
    # Load .env into os.environ (silent if file not found)
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)  # override=False: real env vars take precedence
    except ImportError:
        pass  # python-dotenv not installed; rely on env vars being set externally

    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"{config_path} not found.")

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config