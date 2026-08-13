import pandas as pd
import h3

from src.utils.config_loader import load_config


def convert_points_to_h3():
    config = load_config()
    resolution = config["spatial"]["h3_resolution"]

    # 1. Load CSV
    df = pd.read_csv("data/raw/sample_temperature.csv")

    # 2. Convert each row to H3
    df["h3_id"] = df.apply(
        lambda row : h3.latlng_to_cell(
        row["latitude"],
        row["longitude"],
        resolution            
        ),
        axis =1
    )

    # 3. Group by H3 and take mean temperature

    grouped = df.groupby("h3_id")["temperature"].mean().reset_index()

    print(grouped)

    # 4. Print result
    print(df)
    grouped.to_csv("data/processed/sample_temperature_h3.csv", index=False)
    print("Saved processed H3 data.")


if __name__ == "__main__":
    convert_points_to_h3()