# Data Dictionary — SSI v2 Raw Drivers (`v2_raw`)

This document defines the schema, physical units, data sources, resolutions, and assumptions for all variables in `data/h3_panel/v2_raw/{city}.parquet`.

---

## 1. Primary Variables

| Column | Definition | Physical Unit | Primary Source File | Time Res. | Spatial Res. | Direction | Known Issues & Notes |
|---|---|---|---|---|---|---|---|
| `h3_index` | Uber H3 spatial index | Hexadecimal string | Pipeline boundary generation | Static | Resolution 8 (~0.74 km²) | N/A | Unique geographic identifier per cell. |
| `date` | Timestamp for monthly observation | Date (`YYYY-MM-01`) | Model calendar | Monthly | N/A | N/A | Strictly month-start date (36 months: 2020-01 to 2022-12). |
| `heat_raw` | Meteorological Steadman/Rothfusz Heat Index | Degrees Celsius (°C) | ERA5 Reanalysis (`temp_mean_c`, `dewpoint_mean_c`) | Monthly mean | ~11 km (0.1°) ERA5 downscaled to H3 | Higher = More Stress | Physical air temperature blended with relative humidity. Independent satellite LST (`lst_c`) is held out. |
| `water_raw` | Climatic Water Deficit (CWD = PET - Precip) | Millimeters per month (mm/month) | ERA5 Reanalysis (`temp_mean_c`, `precip_sum_mm`) | Monthly aggregate | ~11 km downscaled to H3 | Higher = More Stress | Derived via Thornthwaite (1948) daylength-adjusted PET minus monthly rainfall. Clipped at zero (negative values denote moisture surplus). |
| `veg_raw` | Sentinel-2 Normalized Difference Vegetation Index (NDVI) | Dimensionless index [-1, +1] | Sentinel-2 L2A via Planetary Computer | Monthly composite | 10m/20m aggregated to H3 | Higher = Greener | Inverted in Step 06 (`1 - z`) so higher denotes vegetative degradation. November 2022 cloud gap is linearly interpolated temporally per hex (`is_imputed=True`). |
| `pollution_raw` | Atmospheric Particulate Matter PM2.5 | Micrograms per cubic meter (µg/m³) | CAMS Reanalysis / SEDAC | Monthly mean | City-wide / regional grid (~0.75° CAMS or 1km SEDAC) | Higher = More Stress | *PM2.5 has ≈3 distinct values per month across city extents.* Acts as a temporal modulator across seasons rather than a fine spatial discriminator. |
| `exposure_raw` | Built environment exposure composite | Dimensionless score [0, 1] | GHSL & OpenStreetMap | Static | H3 Resolution 8 | Higher = More Exposure | *Exposure inputs are constant in time (zero within-hex variance across months).* Equal-weighted composite of min-max scaled built-up fraction, building density, and road density. |
| `exp_built_up` | Human settlement built-up surface fraction | Fraction [0, 1] | GHSL Built-Up S2 (10m) | Static (2020 epoch) | 10m aggregated to H3 | Higher = More Built | Measures physical impervious surface coverage. |
| `exp_building_density` | Count of building footprints per square kilometer | Buildings / km² | OpenStreetMap building polygons | Static (as of ingestion) | Vector to H3 | Higher = Denser | OSM completeness varies across suburban perimeters. |
| `exp_road_density` | Total length of road network per unit area | km / km² | OpenStreetMap highway lines | Static | Vector to H3 | Higher = Denser | Captures transportation network density and vehicular corridor concentration. |
| `is_imputed` | Flag indicating whether any driver was imputed for this row | Boolean (`True`/`False`) | Pipeline calculation | Monthly | H3 Resolution 8 | N/A | `True` for rows where November 2022 NDVI was linearly interpolated across surrounding months. Never silently filled. |

---

## 2. Held-Out Variables (Circularity Prevention)

Under Rule G8 and the Circularity Prevention Standard, the following independent empirical datasets are **strictly excluded** from index construction (`heat_raw`, `veg_raw`, `exposure_raw`, and the resulting SSI composites) and reserved solely for out-of-sample validation:

1. **MODIS Land Surface Temperature (`lst_c` in °C):**
   - Independent thermal infrared satellite observation (MODIS Terra/Aqua MOD11A2 / MYD11A2, 1km resolution).
   - Reserved strictly for Step 11 **convergent construct validity** and the Thermal Random Forest machine learning benchmark (`train_thermal_ml.py`).
2. **Socio-Economic Census Deprivation (`bpl_pct`, `slum_pct`, `elderly_pct`, `literacy_pct`):**
   - Ward and district-level social vulnerability metrics.
   - Reserved for evaluating socio-environmental inequality traps and archetype profiling, not mixed into the baseline physical exposure index.
