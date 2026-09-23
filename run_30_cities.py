import json
import subprocess
import shutil
import os
from pathlib import Path

def main():
    with open('cities_bbox.json', 'r') as f:
        bboxes = json.load(f)
        
    cities = [
        "mumbai", "delhi", "bengaluru", "chennai", "hyderabad", "kolkata", "pune", "ahmedabad",
        "surat", "jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "visakhapatnam",
        "patna", "vadodara", "ghaziabad", "ludhiana", "agra", "nashik", "ranchi", "meerut",
        "rajkot", "varanasi", "srinagar", "aurangabad", "amritsar", "coimbatore"
    ]

    for city in cities:
        print(f"\n=======================================================")
        print(f"  STARTING PIPELINE FOR {city.upper()} ")
        print(f"=======================================================\n")
        
        # 1. Run Pipeline
        cmd_pipeline = [
            "python3", "run_pipeline.py", 
            "--city", city, 
            "--phase", "all", 
            "--start", "2022-01", 
            "--end", "2022-02"
        ]
        
        print(f"Running: {' '.join(cmd_pipeline)}")
        result_pipe = subprocess.run(cmd_pipeline)
        
        if result_pipe.returncode == 0:
            # 2. Run Dashboard Report Generation
            cmd_report = ["python3", "generate_report.py", "--city", city]
            print(f"\nRunning: {' '.join(cmd_report)}")
            result_report = subprocess.run(cmd_report)
            
            if result_report.returncode == 0:
                print(f"✅ Dashboard generated for {city}")
            else:
                print(f"❌ Dashboard generation failed for {city}")
        else:
            print(f"❌ Pipeline failed for {city}")
            
        # 3. Clean Up Raw Data ("Delete As You Go" Strategy)
        print(f"🧹 Sweeping raw cached data for {city} to free up local storage...")
        
        # Paths to wipe
        paths_to_clean = [
            Path(f"data/raw/era5/{city}"),
            Path(f"data/raw/satellite/{city}"),
            Path(f"data/raw/pm25/{city}")
        ]
        
        for p in paths_to_clean:
            if p.exists():
                try:
                    shutil.rmtree(p)
                    print(f"   Deleted {p}")
                except Exception as e:
                    print(f"   Failed to delete {p}: {e}")
                    
        # Remove individual geopackages for OSM
        osm_dir = Path("data/raw/osm")
        if osm_dir.exists():
            for f in osm_dir.glob(f"{city}_*.gpkg"):
                try:
                    f.unlink()
                    print(f"   Deleted {f}")
                except Exception as e:
                    print(f"   Failed to delete {f}: {e}")
                    
        print(f"🏁 Finished processing {city}\n")

if __name__ == "__main__":
    main()
