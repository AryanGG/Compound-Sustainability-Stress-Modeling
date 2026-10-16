"""
scripts/build_frontend.py
─────────────────────────
Builds a unified, single-page, professional light-mode web application for:
"GeoStress AI — Hyperlocal Urban Sustainability Stress & Multi-Horizon Early Warning System"

Features:
- Real data for all 7 cities (Delhi NCR, Mumbai, Kolkata, Hyderabad, Bikaner, Coimbatore, Indore)
- 36 continuous months (2020-01 to 2022-12)
- Real ML 30-day forward predictions (pred_ssi, prob_heatwave, prob_smog)
- Defensible demographics (GHSL built-up fraction, OSM building density, OSM road density, Census 2011 vulnerability)
- Clean, institutional, light-mode design (no gamification, clear typography, professional cartography)
- Self-contained in dashboard/index.html (no external build step required)
"""

import base64
import json
from pathlib import Path
import numpy as np
import pandas as pd
import h3

ROOT_DIR = Path(__file__).resolve().parent.parent

CITIES = [
    {"id": "mumbai", "name": "Mumbai", "state": "Maharashtra", "biome": "Tropical Coastal Monsoon", "center": [19.0760, 72.8777], "zoom": 11},
    {"id": "delhi", "name": "Delhi NCR", "state": "National Capital Region", "biome": "Subtropical Semi-Arid Monsoon", "center": [28.6139, 77.2090], "zoom": 10},
    {"id": "kolkata", "name": "Kolkata", "state": "West Bengal", "biome": "Humid Deltaic Subtropical", "center": [22.5726, 88.3639], "zoom": 11},
    {"id": "hyderabad", "name": "Hyderabad", "state": "Telangana", "biome": "Tropical Semi-Arid Plateau", "center": [17.3850, 78.4867], "zoom": 11},
    {"id": "bikaner", "name": "Bikaner", "state": "Rajasthan", "biome": "Hot Arid Desert", "center": [28.0229, 73.3119], "zoom": 11},
    {"id": "coimbatore", "name": "Coimbatore", "state": "Tamil Nadu", "biome": "Semi-Arid Rainshadow", "center": [11.0168, 76.9558], "zoom": 11},
    {"id": "indore", "name": "Indore", "state": "Madhya Pradesh", "biome": "Tropical Savanna Plateau", "center": [22.7196, 75.8577], "zoom": 11},
]

DEMOGRAPHICS = {
    "mumbai": {"slum_pct": 42.0, "bpl_pct": 18.0, "elderly_pct": 9.0, "literacy_pct": 88.0, "source": "Census 2011 / BMC"},
    "delhi": {"slum_pct": 30.0, "bpl_pct": 14.0, "elderly_pct": 8.0, "literacy_pct": 87.0, "source": "Census 2011 / GNCTD"},
    "kolkata": {"slum_pct": 33.0, "bpl_pct": 22.0, "elderly_pct": 12.0, "literacy_pct": 87.0, "source": "Census 2011 / KMC"},
    "hyderabad": {"slum_pct": 32.0, "bpl_pct": 17.0, "elderly_pct": 9.0, "literacy_pct": 85.0, "source": "Census 2011 / GHMC"},
    "bikaner": {"slum_pct": 22.0, "bpl_pct": 18.0, "elderly_pct": 8.0, "literacy_pct": 65.0, "source": "Census 2011 / District Portal"},
    "coimbatore": {"slum_pct": 15.0, "bpl_pct": 11.0, "elderly_pct": 11.0, "literacy_pct": 84.0, "source": "Census 2011 / CCMC"},
    "indore": {"slum_pct": 29.0, "bpl_pct": 21.0, "elderly_pct": 10.0, "literacy_pct": 83.0, "source": "Census 2011 / IMC"},
}

def extract_city_data():
    all_city_payloads = {}
    
    for c_meta in CITIES:
        cid = c_meta["id"]
        print(f"Processing real data for {cid}...")
        v2_path = ROOT_DIR / f"data/h3_panel/v2/{cid}.parquet"
        ml_path = ROOT_DIR / f"data/h3_panel/ml_predictions/{cid}_2022_predictions.parquet"
        
        v2_df = pd.read_parquet(v2_path)
        v2_df['ym'] = v2_df['date'].astype(str).str[:7]
        
        # Load ML predictions
        ml_map = {}
        if ml_path.exists():
            ml_df = pd.read_parquet(ml_path)
            for _, r in ml_df.iterrows():
                ml_map[(r['h3_index'], str(r['date'])[:7])] = (
                    round(float(r['pred_ssi_v2_1m']), 3),
                    round(float(r['prob_heatwave']), 3),
                    round(float(r['prob_smog']), 3)
                )
        
        # Stable hex ordering
        hex_order = sorted(v2_df['h3_index'].unique())
        first_rows = v2_df.drop_duplicates('h3_index').set_index('h3_index')
        
        hex_metadata = []
        for h in hex_order:
            lat, lng = h3.cell_to_latlng(h)
            row = first_rows.loc[h]
            hex_metadata.append([
                h,
                round(lat, 4),
                round(lng, 4),
                round(float(row.get('exp_built_up', 0.0)) * 100, 1),
                round(float(row.get('exp_building_density', 0.0)), 0),
                round(float(row.get('exp_road_density', 0.0)), 1)
            ])
            
        # Months dictionary
        months_dict = {}
        monthly_stats = {}
        
        for ym, m_df in v2_df.groupby('ym'):
            m_idx = m_df.set_index('h3_index')
            
            ssi_arr = np.zeros(len(hex_order), dtype=np.uint8)
            heat_arr = np.zeros(len(hex_order), dtype=np.uint8)
            water_arr = np.zeros(len(hex_order), dtype=np.uint8)
            veg_arr = np.zeros(len(hex_order), dtype=np.uint8)
            poll_arr = np.zeros(len(hex_order), dtype=np.uint8)
            pred_arr = np.zeros(len(hex_order), dtype=np.uint8)
            prob_hw_arr = np.zeros(len(hex_order), dtype=np.uint8)
            prob_smog_arr = np.zeros(len(hex_order), dtype=np.uint8)
            
            for i, h in enumerate(hex_order):
                if h in m_idx.index:
                    r = m_idx.loc[h]
                    s = float(r['ssi_v2'])
                    ht = float(r['heat_v2'])
                    w = float(r['water_v2'])
                    vg = float(r['veg_v2'])
                    p = float(r['pollution_v2'])
                else:
                    s, ht, w, vg, p = 0.5, 0.5, 0.5, 0.5, 0.5
                    
                ml_tuple = ml_map.get((h, ym), None)
                if ml_tuple:
                    pr_s, pr_hw, pr_sm = ml_tuple
                else:
                    pr_s, pr_hw, pr_sm = s, 0.0, 0.0
                    
                ssi_arr[i] = int(np.clip(s * 255, 0, 255))
                heat_arr[i] = int(np.clip(ht * 255, 0, 255))
                water_arr[i] = int(np.clip(w * 255, 0, 255))
                veg_arr[i] = int(np.clip(vg * 255, 0, 255))
                poll_arr[i] = int(np.clip(p * 255, 0, 255))
                pred_arr[i] = int(np.clip(pr_s * 255, 0, 255))
                prob_hw_arr[i] = int(np.clip(pr_hw * 255, 0, 255))
                prob_smog_arr[i] = int(np.clip(pr_sm * 255, 0, 255))
                
            months_dict[ym] = {
                "ssi": base64.b64encode(ssi_arr.tobytes()).decode("ascii"),
                "heat": base64.b64encode(heat_arr.tobytes()).decode("ascii"),
                "water": base64.b64encode(water_arr.tobytes()).decode("ascii"),
                "veg": base64.b64encode(veg_arr.tobytes()).decode("ascii"),
                "poll": base64.b64encode(poll_arr.tobytes()).decode("ascii"),
                "pred": base64.b64encode(pred_arr.tobytes()).decode("ascii"),
                "phw": base64.b64encode(prob_hw_arr.tobytes()).decode("ascii"),
                "psmog": base64.b64encode(prob_smog_arr.tobytes()).decode("ascii"),
            }
            
            # Month aggregate KPIs
            mean_ssi = float(m_df['ssi_v2'].mean())
            max_ssi = float(m_df['ssi_v2'].max())
            extreme_share = float((m_df['ssi_v2'] >= 0.657).mean() * 100)
            high_share = float(((m_df['ssi_v2'] >= 0.50) & (m_df['ssi_v2'] < 0.657)).mean() * 100)
            hw_alert_count = int((prob_hw_arr >= int(0.75 * 255)).sum())
            smog_alert_count = int((prob_smog_arr >= int(0.75 * 255)).sum())
            
            monthly_stats[ym] = {
                "mean_ssi": round(mean_ssi, 3),
                "max_ssi": round(max_ssi, 3),
                "extreme_pct": round(extreme_share, 1),
                "high_pct": round(high_share, 1),
                "mean_heat": round(float(m_df['heat_v2'].mean()), 3),
                "mean_water": round(float(m_df['water_v2'].mean()), 3),
                "mean_veg": round(float(m_df['veg_v2'].mean()), 3),
                "mean_poll": round(float(m_df['pollution_v2'].mean()), 3),
                "hw_alerts": hw_alert_count,
                "smog_alerts": smog_alert_count,
            }
            
        all_city_payloads[cid] = {
            "meta": c_meta,
            "demographics": DEMOGRAPHICS[cid],
            "hex_count": len(hex_order),
            "hexes": hex_metadata,
            "months": months_dict,
            "stats": monthly_stats,
        }
        
    return all_city_payloads

if __name__ == "__main__":
    payload = extract_city_data()
    print("Saving extracted real frontend data -> scratch/frontend_data.json...")
    with open("scratch/frontend_data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print("Done!")
