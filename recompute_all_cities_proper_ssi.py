"""
recompute_all_cities_proper_ssi.py
───────────────────────────────────
Batch execution script to recompute the Proper Physical SSI (JT-SSI)
across all 7 cities in data/h3_panel/final/.
"""

import time
from pathlib import Path
import pandas as pd

from src.features.proper_ssi import compute_proper_ssi

CITIES = [
    "bikaner",
    "coimbatore",
    "delhi",
    "hyderabad",
    "indore",
    "kolkata",
    "mumbai",
]


def main():
    print("=" * 70)
    print("  BATCH EXECUTION: PROPER PHYSICAL SSI (JT-SSI) FOR 7 CITIES")
    print("=" * 70)

    data_dir = Path("data/h3_panel/final")
    summary = []

    for city in CITIES:
        csv_path = data_dir / f"{city}.csv"
        if not csv_path.exists():
            print(f"[-] CSV missing for {city}: {csv_path}")
            continue

        print(f"\n[+] Processing {city.upper()} ({csv_path})")
        t0 = time.time()
        df = pd.read_csv(csv_path)
        print(f"    Loaded {len(df):,} rows x {len(df.columns)} cols")

        # Run proper SSI calculation
        updated = compute_proper_ssi(df, city)

        # Save Parquet
        pq_path = data_dir / f"{city}.parquet"
        updated.to_parquet(pq_path, compression="snappy")

        # Save CSV
        updated.to_csv(csv_path, index=False)

        # Save _ssi.csv for dashboard compatibility
        ssi_csv_path = data_dir / f"{city}_ssi.csv"
        updated.to_csv(ssi_csv_path, index=False)

        elapsed = time.time() - t0

        # Diagnostics
        dates = pd.to_datetime(updated["date"])
        may_heat = updated[dates.dt.month == 5]["heat_stress_idx"].mean()
        jan_heat = updated[dates.dt.month == 1]["heat_stress_idx"].mean()
        may_water = updated[dates.dt.month == 5]["water_stress_idx"].mean()
        aug_water = updated[dates.dt.month == 8]["water_stress_idx"].mean()
        omega_pct = (updated["omega_compound"] > 0).mean() * 100
        bands = (updated["ssi_band"].value_counts(normalize=True) * 100).round(1).to_dict()

        print(f"    [COMPLETED in {elapsed:.1f}s]")
        print(f"      - Heat Stress Seasonality:  May={may_heat:.2f} vs Jan={jan_heat:.2f} (Spread={may_heat - jan_heat:+.2f})")
        print(f"      - Water Stress Seasonality: May={may_water:.2f} vs Aug={aug_water:.2f} (Spread={may_water - aug_water:+.2f})")
        print(f"      - Mean SSI Value:           {updated['ssi_value'].mean():.3f} (Max={updated['ssi_value'].max():.3f})")
        print(f"      - Compound Trigger Rate:    {omega_pct:.1f}%")
        print(f"      - Bands (%):                {bands}")

        summary.append({
            "city": city,
            "hexes": updated["h3_index"].nunique(),
            "rows": len(updated),
            "mean_ssi": round(float(updated["ssi_value"].mean()), 3),
            "compound_pct": round(float(omega_pct), 1),
            "extreme_pct": round(float(bands.get("Extreme", 0.0)), 1),
            "heat_may_vs_jan": f"{may_heat:.2f} / {jan_heat:.2f}",
            "water_may_vs_aug": f"{may_water:.2f} / {aug_water:.2f}",
        })

    # Summary table
    print("\n" + "=" * 70)
    print("  SUMMARY OF ALL 7 CITIES PROCESSED")
    print("=" * 70)
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))
    print("=" * 70)


if __name__ == "__main__":
    main()
