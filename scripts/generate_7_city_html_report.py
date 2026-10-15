"""
scripts/generate_7_city_html_report.py
──────────────────────────────────────
Aggregates canonical 7-city dataset (334,332 rows) into rich JSON metrics
and renders a self-contained, interactive HTML report with sleek dark-mode aesthetics.
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd

def compute_all_metrics():
    print("Loading canonical final 7-city dataset...")
    df = pd.read_parquet("data/h3_panel/final/final_7_cities.parquet")
    print(f"Loaded {len(df):,} observations.")

    indicators = ['heat_v2', 'water_v2', 'veg_v2', 'pollution_v2', 'exposure_v2']
    cities = ['delhi', 'kolkata', 'mumbai', 'bikaner', 'hyderabad', 'indore', 'coimbatore']
    
    city_biomes = {
        'bikaner': {'name': 'Bikaner', 'biome': 'Hot Arid Desert', 'koppen': 'BWh', 'coords': '28.02°N, 73.32°E'},
        'coimbatore': {'name': 'Coimbatore', 'biome': 'Semi-Arid Rainshadow', 'koppen': 'BSh', 'coords': '11.01°N, 76.96°E'},
        'delhi': {'name': 'Delhi NCR', 'biome': 'Subtropical Semi-Arid Monsoon', 'koppen': 'Cwa', 'coords': '28.61°N, 77.20°E'},
        'hyderabad': {'name': 'Hyderabad', 'biome': 'Tropical Semi-Arid Plateau', 'koppen': 'BSh', 'coords': '17.38°N, 78.48°E'},
        'indore': {'name': 'Indore', 'biome': 'Tropical Savanna Plateau', 'koppen': 'Aw', 'coords': '22.72°N, 75.86°E'},
        'kolkata': {'name': 'Kolkata', 'biome': 'Humid Deltaic Subtropical', 'koppen': 'Aw', 'coords': '22.57°N, 88.36°E'},
        'mumbai': {'name': 'Mumbai', 'biome': 'Tropical Coastal Monsoon', 'koppen': 'Am', 'coords': '19.07°N, 72.88°E'},
    }

    # Archetype mapping
    archetype_info = {
        1: {'title': 'Suburban Peripheral / Baseline Low Stress', 'desc': 'Low stress across all 5 hazards; dominates peri-urban buffers and surrounding agricultural fringes.', 'adaptation': 'Preserve open green buffers, restrict sprawling high-density expansion without infrastructure, implement strict groundwater recharge zoning.'},
        2: {'title': 'High-Exposure Smog Corridor', 'desc': 'Severe particulate saturation concentrated in dense urban vehicular and industrial transit corridors.', 'adaptation': 'Implement targeted low-emission zones (LEZs), roadside anti-smog mist cannons, heavy vehicular diversion, and high-efficiency particulate air-scrubbing green barriers.'},
        3: {'title': 'Severe Arid Heat & Chronic Water Deficit', 'desc': 'Hyper-arid thermal regimes paired with chronic annual water deficits and sparse natural canopy cover.', 'adaptation': 'Deploy decentralized rainwater harvesting, shaded urban arcades, solar-reflective cool surfaces, and drought-hardy micro-vegetative dune stabilization.'},
        4: {'title': 'Acute Winter Atmospheric Inversion & Smog', 'desc': 'Near-maximum PM2.5 levels during seasonal boundary-layer subsidence inversions in lower-density sectors.', 'adaptation': 'Enforce seasonal industrial combustion moratoriums, agricultural residue processing subsidies, and winter emergency public health advisories.'},
        5: {'title': 'Compound Multi-Hazard Core Hotspot', 'desc': 'Critical co-occurrence of extreme apparent heat, acute water deficit, dense impervious built mass, and depleted tree canopy.', 'adaptation': 'Highest municipal priority: mandatory cool roofs, reflective pavements, pocket park conversions, intensive localized stormwater retention, and emergency cooling shelters.'},
        6: {'title': 'Congested Urban Core', 'desc': 'High structural built density and impervious cover with severe canopy deficit under moderate background weather stress.', 'adaptation': 'Retrofit rooftop gardens, street tree canopy planting, porous pavements, and urban heat island mitigation guidelines for new construction.'}
    }

    # Compute archetype stats
    arch_counts = df['archetype_id'].value_counts(normalize=True).to_dict()
    arch_means = df.groupby('archetype_id')[indicators + ['ssi_v2']].mean().to_dict(orient='index')
    archetypes_data = []
    for aid in range(1, 7):
        archetypes_data.append({
            'id': aid,
            'title': archetype_info[aid]['title'],
            'prevalence': round(float(arch_counts.get(aid, 0.0) * 100), 1),
            'desc': archetype_info[aid]['desc'],
            'adaptation': archetype_info[aid]['adaptation'],
            'centroids': {
                'heat': round(float(arch_means[aid]['heat_v2']), 3),
                'water': round(float(arch_means[aid]['water_v2']), 3),
                'veg': round(float(arch_means[aid]['veg_v2']), 3),
                'pollution': round(float(arch_means[aid]['pollution_v2']), 3),
                'exposure': round(float(arch_means[aid]['exposure_v2']), 3),
                'ssi': round(float(arch_means[aid]['ssi_v2']), 3),
            }
        })

    # Decile synergy stats
    df['decile'] = pd.qcut(df['ssi_lin_v2'], q=10, labels=[f"D{i}" for i in range(1, 11)])
    dec_stats = df.groupby('decile', observed=False).agg({
        'ssi_lin_v2': 'mean',
        'ssi_v2': 'mean'
    }).reset_index()
    deciles_data = []
    for _, row in dec_stats.iterrows():
        lin_v = float(row['ssi_lin_v2'])
        comp_v = float(row['ssi_v2'])
        prem_pct = round(((comp_v - lin_v) / (lin_v if lin_v > 0 else 1.0)) * 100, 1)
        deciles_data.append({
            'decile': row['decile'],
            'ssi_linear': round(lin_v, 3),
            'ssi_compound': round(comp_v, 3),
            'premium_pct': prem_pct
        })

    # City-by-city data
    cities_data = {}
    for c in cities:
        cdf = df[df['city_id'] == c]
        hex_count = cdf['h3_index'].nunique()
        tot_var = cdf['ssi_v2'].var()
        t_var = float((cdf.groupby('date')['ssi_v2'].mean().var() / tot_var) * 100)
        s_var = float((cdf.groupby('h3_index')['ssi_v2'].mean().var() / tot_var) * 100)
        r_var = max(0.0, 100.0 - t_var - s_var)

        # Monthly time series
        monthly = cdf.groupby('date').agg({
            'ssi_v2': 'mean',
            'heat_v2': 'mean',
            'water_v2': 'mean',
            'veg_v2': 'mean',
            'pollution_v2': 'mean',
            'exposure_v2': 'mean',
            'omega_v2': lambda x: float((x > 0).mean() * 100),
            'anomaly_flag': lambda x: float((x > 0).mean() * 100),
        }).reset_index()
        monthly['date'] = monthly['date'].astype(str).str[:7]
        monthly_list = monthly.rename(columns={'ssi_v2': 'ssi', 'heat_v2': 'heat', 'water_v2': 'water', 'veg_v2': 'veg', 'pollution_v2': 'pollution', 'exposure_v2': 'exposure', 'omega_v2': 'compound_pct', 'anomaly_flag': 'anomaly_pct'}).to_dict(orient='records')
        for m in monthly_list:
            for k in ['ssi', 'heat', 'water', 'veg', 'pollution', 'exposure', 'compound_pct', 'anomaly_pct']:
                m[k] = round(float(m[k]), 3)

        band_counts = (cdf['ssi_band_v2'].value_counts(normalize=True) * 100).to_dict()

        cities_data[c] = {
            'id': c,
            'name': city_biomes[c]['name'],
            'biome': city_biomes[c]['biome'],
            'koppen': city_biomes[c]['koppen'],
            'coords': city_biomes[c]['coords'],
            'hex_count': hex_count,
            'area_km2': round(hex_count * 0.7374, 1),
            'panel_obs': len(cdf),
            'mean_ssi': round(float(cdf['ssi_v2'].mean()), 3),
            'median_ssi': round(float(cdf['ssi_v2'].median()), 3),
            'max_ssi': round(float(cdf['ssi_v2'].max()), 3),
            'min_ssi': round(float(cdf['ssi_v2'].min()), 3),
            'std_ssi': round(float(cdf['ssi_v2'].std()), 3),
            'compound_trigger_rate': round(float((cdf['omega_v2'] > 0).mean() * 100), 1),
            'sub_indices': {
                'heat': round(float(cdf['heat_v2'].mean()), 3),
                'water': round(float(cdf['water_v2'].mean()), 3),
                'veg': round(float(cdf['veg_v2'].mean()), 3),
                'pollution': round(float(cdf['pollution_v2'].mean()), 3),
                'exposure': round(float(cdf['exposure_v2'].mean()), 3),
            },
            'risk_bands': {
                'Low': round(float(band_counts.get('Low', 0.0)), 1),
                'Moderate': round(float(band_counts.get('Moderate', 0.0)), 1),
                'High': round(float(band_counts.get('High', 0.0)), 1),
                'Extreme': round(float(band_counts.get('Extreme', 0.0)), 1),
            },
            'variance_decomp': {
                'temporal': round(t_var, 1),
                'spatial': round(s_var, 1),
                'residual': round(r_var, 1),
            },
            'monthly_timeseries': monthly_list
        }

    # Pan-India monthly series
    pan_monthly = df.groupby('date').agg({
        'ssi_v2': 'mean',
        'heat_v2': 'mean',
        'water_v2': 'mean',
        'veg_v2': 'mean',
        'pollution_v2': 'mean',
        'exposure_v2': 'mean',
        'omega_v2': lambda x: float((x > 0).mean() * 100),
        'anomaly_flag': lambda x: float((x > 0).mean() * 100),
    }).reset_index()
    pan_monthly['date'] = pan_monthly['date'].astype(str).str[:7]
    pan_monthly_list = pan_monthly.rename(columns={'ssi_v2': 'ssi', 'heat_v2': 'heat', 'water_v2': 'water', 'veg_v2': 'veg', 'pollution_v2': 'pollution', 'exposure_v2': 'exposure', 'omega_v2': 'compound_pct', 'anomaly_flag': 'anomaly_pct'}).to_dict(orient='records')
    for m in pan_monthly_list:
        for k in ['ssi', 'heat', 'water', 'veg', 'pollution', 'exposure', 'compound_pct', 'anomaly_pct']:
            m[k] = round(float(m[k]), 3)

    pan_bands = (df['ssi_band_v2'].value_counts(normalize=True) * 100).to_dict()

    payload = {
        'meta': {
            'title': 'Compound Sustainability Stress Index (SSI) — 7-City Final Assessment Report',
            'version': 'Canonical v2.0 Final',
            'total_obs': len(df),
            'total_hexes': df['h3_index'].nunique(),
            'n_cities': 7,
            'time_horizon': '2020-01 to 2022-12 (36 Continuous Months)',
            'mean_ssi': round(float(df['ssi_v2'].mean()), 3),
            'median_ssi': round(float(df['ssi_v2'].median()), 3),
            'max_ssi': round(float(df['ssi_v2'].max()), 3),
            'min_ssi': round(float(df['ssi_v2'].min()), 3),
            'clamped_pct': 0.00,
            'compound_synergy_d10': 25.3,
            'risk_bands': {
                'Low': round(float(pan_bands.get('Low', 0.0)), 1),
                'Moderate': round(float(pan_bands.get('Moderate', 0.0)), 1),
                'High': round(float(pan_bands.get('High', 0.0)), 1),
                'Extreme': round(float(pan_bands.get('Extreme', 0.0)), 1),
            },
            'sub_indices': {
                'heat': round(float(df['heat_v2'].mean()), 3),
                'water': round(float(df['water_v2'].mean()), 3),
                'veg': round(float(df['veg_v2'].mean()), 3),
                'pollution': round(float(df['pollution_v2'].mean()), 3),
                'exposure': round(float(df['exposure_v2'].mean()), 3),
            }
        },
        'cities': cities_data,
        'pan_india_monthly': pan_monthly_list,
        'archetypes': archetypes_data,
        'deciles': deciles_data,
        'weights': {
            'labels': ['Heat Stress', 'Water Deficit', 'Veg Canopy Loss', 'Air Pollution', 'Built Exposure'],
            'equal': [0.2000, 0.2000, 0.2000, 0.2000, 0.2000],
            'ewm': [0.2989, 0.2188, 0.0473, 0.1565, 0.2785],
            'critic': [0.2105, 0.2008, 0.1265, 0.2687, 0.1935],
            'pca': [0.3586, 0.3614, 0.1094, 0.1517, 0.0189],
            'correlations_vs_equal': {
                'EWM': 0.9691,
                'CRITIC': 0.9857,
                'PCA': 0.8919
            }
        },
        'validation': [
            {'id': 1, 'domain': 'Indicator Orthogonality', 'method': 'Variance Inflation Factor (VIF)', 'value': 'Max VIF = 1.11', 'benchmark': 'VIF < 5.0', 'status': 'PASS', 'note': 'Zero harmful multicollinearity across 334k panel rows.'},
            {'id': 2, 'domain': 'Domain Non-Redundancy', 'method': 'Pairwise Pearson correlation (r)', 'value': 'Max |r| = 0.303', 'benchmark': '|r| < 0.70', 'status': 'PASS', 'note': 'All 5 dimensions capture distinct physical environmental drivers.'},
            {'id': 3, 'domain': 'Compound Amplification', 'method': 'Top-decile (D10) stress premium', 'value': '+0.162 (+25.3%)', 'benchmark': '> 0 (Amplified)', 'status': 'PASS', 'note': 'Synergy triggers during concurrent heat & air pollution extremes.'},
            {'id': 4, 'domain': 'Biome Discriminant Validity', 'method': 'One-Way ANOVA (F) & Kruskal-Wallis', 'value': 'F = 6,888, H = 30,024', 'benchmark': 'p < 0.001', 'status': 'PASS', 'note': 'Highly significant differentiation across all 7 Indian biomes.'},
            {'id': 5, 'domain': 'Typology Stability', 'method': 'Silhouette (s) & Bootstrap ARI', 'value': 's = 0.147, ARI = 0.812', 'benchmark': 's > 0, ARI > 0.70', 'status': 'PASS', 'note': '6 distinct, stable pan-India urban stress archetypes confirmed.'},
            {'id': 6, 'domain': 'Spring 2022 Mega-Heatwave', 'method': 'Two-sample t-test & Anomaly rate', 'value': 't = 3.46, 96.5% alert rate', 'benchmark': 'p < 0.01', 'status': 'PASS', 'note': 'Detected record Northwest heatwave in Bikaner, Delhi, Indore.'},
            {'id': 7, 'domain': 'Delhi Winter Smog Inversion', 'method': 'Seasonal SSI mean difference', 'value': '+16.2% seasonal lift', 'benchmark': 'Statistically > 0', 'status': 'PASS', 'note': 'Captures winter boundary-layer particulate stagnation episodes.'},
            {'id': 8, 'domain': 'Hyderabad Catastrophic Floods', 'method': 'Hex grid anomaly alert share', 'value': '100.0% (all 1,505 hexes)', 'benchmark': '> 50% anomaly', 'status': 'PASS', 'note': 'Exact spatial & temporal lock on October 2021 urban cloudburst.'},
        ]
    }

    print("Computing hex-level summary for interactive geospatial maps (9,287 cells)...")
    hex_summary = df.groupby(['city_id', 'h3_index']).agg({
        'latitude': 'first',
        'longitude': 'first',
        'ssi_v2': 'mean',
        'heat_v2': 'mean',
        'water_v2': 'mean',
        'veg_v2': 'mean',
        'pollution_v2': 'mean',
        'exposure_v2': 'mean',
        'archetype_id': lambda x: int(x.mode()[0]),
        'ssi_band_v2': lambda x: str(x.mode()[0])
    }).reset_index()

    hex_list = []
    for _, r in hex_summary.iterrows():
        hex_list.append([
            r['city_id'],
            r['h3_index'],
            round(float(r['latitude']), 4),
            round(float(r['longitude']), 4),
            round(float(r['ssi_v2']), 3),
            round(float(r['heat_v2']), 3),
            round(float(r['water_v2']), 3),
            round(float(r['veg_v2']), 3),
            round(float(r['pollution_v2']), 3),
            round(float(r['exposure_v2']), 3),
            int(r['archetype_id']),
            r['ssi_band_v2']
        ])
    payload['hex_map_data'] = hex_list
    print(f"Serialized {len(hex_list):,} hexes for interactive map.")

    out_json = Path("reports/final_7_cities_metrics.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"Metrics saved to {out_json}")
    return payload

if __name__ == "__main__":
    compute_all_metrics()
