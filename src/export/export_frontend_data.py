import pandas as pd
import h3
import argparse
from pathlib import Path

def export_data(city: str):
    print(f"Exporting data for {city}...")
    
    # Try parquet first, then fallback to CSV
    input_file = Path(f"data/h3_panel/final/{city}.parquet")
    if not input_file.exists():
        input_file = Path(f"data/h3_panel/final/{city}_ssi.csv")
    
    if not input_file.exists():
        print(f"Error: Could not find final output for {city} at {input_file}")
        return

    print(f"Loading data from {input_file}...")
    if input_file.suffix == '.parquet':
        df = pd.read_parquet(input_file)
    else:
        df = pd.read_csv(input_file)

    # Compute lat/lng from h3_index for Deck.gl / UI
    print("Computing coordinates for hexes...")
    try:
        # h3-py 3.x uses h3_to_geo, 4.x uses cell_to_latlng
        if hasattr(h3, 'cell_to_latlng'):
            df['lat'] = df['h3_index'].apply(lambda x: h3.cell_to_latlng(x)[0])
            df['lng'] = df['h3_index'].apply(lambda x: h3.cell_to_latlng(x)[1])
        else:
            df['lat'] = df['h3_index'].apply(lambda x: h3.h3_to_geo(x)[0])
            df['lng'] = df['h3_index'].apply(lambda x: h3.h3_to_geo(x)[1])
    except Exception as e:
        print(f"Error computing coordinates: {e}")
        return

    # Extract required columns (including the 5 sub indices and composite SSI)
    columns = [
        'city_id', 'h3_index', 'lat', 'lng', 'date', 
        'ssi_value', 'heat_stress_idx', 'water_stress_idx', 
        'pollution_idx', 'vegetation_idx', 'urban_vulnerability_idx'
    ]
    
    available_cols = [c for c in columns if c in df.columns]
    export_df = df[available_cols].copy()
    
    # Format date strictly to YYYY-MM
    if 'date' in export_df.columns:
        export_df['date'] = pd.to_datetime(export_df['date']).dt.strftime('%Y-%m')

    # Sort for consistent UI rendering
    export_df = export_df.sort_values(by=['date', 'h3_index'])
    df = export_df

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True, parents=True)
    
    # Save as CSV
    out_csv = out_dir / f"frontend_data_{city}.csv"
    df.to_csv(out_csv, index=False)
    
    # Save as JS file for local HTML access (bypasses CORS)
    out_js = out_dir / f"frontend_data_{city}.js"
    csv_string = df.to_csv(index=False).replace('`', '\\`')
    with open(out_js, 'w') as f:
        f.write(f"const MAP_CSV_DATA = `{csv_string}`;")
        
    print(f"Successfully exported {len(df)} rows to {out_csv} and {out_js}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="mumbai")
    args = parser.parse_args()
    export_data(args.city)
