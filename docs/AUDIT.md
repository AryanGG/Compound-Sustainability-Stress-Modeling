# AUDIT REPORT (Step 1)
Generated: 2026-10-13   Git commit: f9e571d   Branch: main

## A. Repo map

### Raw Command Output
```bash
$ git rev-parse --abbrev-ref HEAD
main

$ git status --short
 M .env.example
 M cities_bbox.json
 M config.yml
 M src/features/ssi.py
 M src/ingest/satellite_ingest.py
 M tests/test_pipeline.py
?? ML_IMPLEMENTATION_PLAN.md
?? SSI_VALIDATION_PLAN.md
?? STEP_01_repo_audit.md
?? TOP_TIER_IMPLEMENTATION_PLAN.md
?? audit/
?? docs/
?? run_validation_and_novelty.py
?? test_modis.py
?? train_thermal_ml.py

$ git log -n 15 --date=short --format='%h %ad %s'
f9e571d 2026-10-10 CAMS fix.
87f01f6 2026-10-04 Minor fixes.
00de2f4 2026-09-23 Track vulnerability CSVs and updated gitignore
c3427de 2026-09-23 chore: untrack large data file and scratch credentials script
921c5d1 2026-09-23 Clean Up
1343c8d 2026-09-23 Fixed Pm2.5 and Socio-Economic variables.

$ find . -type f \( -name "*.py" -o -name "*.parquet" -o -name "*.csv" -o -name "*.html" -o -name "*.md" -o -name "*.json" -o -name "*.ipynb" -o -name "requirements*.txt" -o -name "pyproject.toml" \) -not -path "./.git/*" -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" -exec ls -la {} \; | awk '{print $5, $6, $7, $8, $9}' | sort -k5
302 Oct 13 20:39 ./.pytest_cache/README.md
15715 Oct 13 20:31 ./ML_IMPLEMENTATION_PLAN.md
33546 Oct 12 08:56 ./SSI_VALIDATION_PLAN.md
16551 Oct 13 21:21 ./STEP_01_repo_audit.md
16941 Oct 13 19:38 ./TOP_TIER_IMPLEMENTATION_PLAN.md
5933 Oct 13 21:24 ./audit/audit_data.py
65701 Oct 4 18:24 ./cache/13dd8eababafcab3aa96c11d145a84f34838a91a.json
258 Oct 11 16:13 ./cache/1c86d0c158b9e102e4fa7e7c7f745c1bcc3063f7.json
19453 Oct 11 13:53 ./cache/1d7a46531e1cce0081d4fd6619d1ae7ed4a9952f.json
3869 Oct 4 18:18 ./cache/245950f353a6a9a87a915946a0ef914f521520bc.json
13313 Oct 4 18:19 ./cache/35457de31ce28acdba2c59f498df5cec9570435b.json
64793 Oct 11 16:10 ./cache/4526e89338e0645cd897d855b091c5cccd97d5b6.json
229804 Oct 4 18:16 ./cache/4b3ef920aee00a24ea3157a72a228c04fe3be7bb.json
28363 Oct 11 16:18 ./cache/4cf99cb8fee7f701159451cffa01dc5808545fe1.json
19270342 Oct 11 16:09 ./cache/4fe381c28a3e56cc3feb926637e2f73ff76c5a23.json
423776 Oct 4 18:21 ./cache/5104b962f90565d86c22b4253f4949ff41ee61c2.json
285354 Oct 4 18:19 ./cache/5487188f63f04839e9e2ea6a1c50aed1f56d4bbd.json
27673903 Oct 4 18:15 ./cache/5d1e2a758cf1ab5f6fc7a4542caa8ea7858ca2ee.json
21270 Oct 11 13:53 ./cache/62daaf04c3baf10d6938fb392705f9f5c7f1697b.json
1377965 Oct 4 18:16 ./cache/755f7152a9b73a4715c221dbc81314d2f657e741.json
6908 Oct 11 13:35 ./cache/75b0a6cac6636a9601bfc9b1594b4a756ff3bcb2.json
119089080 Oct 4 18:15 ./cache/7a469902d03b05a982ac6daab2b0c47c73b7ce56.json
135521 Oct 4 18:18 ./cache/7be1b8831562fe996902bfcd1f4806f4c48ce8e3.json
24328 Oct 11 16:11 ./cache/8d3caf43a24b2e1bfa390b24ccb5c205fe4d26ef.json
258 Oct 11 16:13 ./cache/a0d17612a48330774281f7820b5df0eba6267235.json
4886 Oct 11 16:19 ./cache/a5afac9b0fbfdad943a1d8d1cd41aa58383ece0d.json
1335457 Oct 4 18:19 ./cache/ae2d6e6824b2dd7841af4d593e3487db70f8b165.json
73018 Oct 4 18:24 ./cache/b427ed4737e3d409e0a5177a228acde61296939e.json
88751209 Oct 11 16:09 ./cache/b95e94ddee46b35c5c1664d132835a7ab0132eb5.json
258 Oct 4 18:19 ./cache/c862630c278ba2bf60dc0b5238c8f56304c87176.json
136186 Oct 4 18:16 ./cache/c8c9c0ba1346b0a9cf93a40b60f47338ceebc89c.json
695 Oct 11 13:35 ./cache/c8f79ebf1c1207b005e9e737be5976254084e1ab.json
12637 Oct 11 13:53 ./cache/cee4bbe266a60acca6eaf8a33a5c65d1aec71a1b.json
984635 Oct 4 18:18 ./cache/e143f51e5d31118dcc2bb2929eec3945b25f5b98.json
559 Oct 11 13:35 ./cache/f51e2c9208967f0612d48f05e2f77f534032f781.json
52188 Oct 11 13:35 ./cache/f5b4f961b272e656f6478dc11204767f95d0157c.json
258 Oct 11 16:11 ./cache/fb05d7a57012916a80bfff97c8171021eac88683.json
378 Oct 4 13:44 ./check_values.py
7258 Oct 11 14:14 ./cities_bbox.json
12500894 Oct 11 16:29 ./data/features/coimbatore_features.csv
9714754 Oct 11 00:25 ./data/features/mumbai_features.csv
11605596 Oct 13 19:00 ./data/h3_panel/final/bikaner.csv
3990367 Oct 13 19:00 ./data/h3_panel/final/bikaner.parquet
14501878 Oct 13 20:44 ./data/h3_panel/final/coimbatore.csv
4586458 Oct 13 20:44 ./data/h3_panel/final/coimbatore.parquet
14501878 Oct 13 20:44 ./data/h3_panel/final/coimbatore_ssi.csv
49637785 Oct 13 19:14 ./data/h3_panel/final/delhi.csv
13404519 Oct 13 19:14 ./data/h3_panel/final/delhi.parquet
23572118 Oct 13 19:07 ./data/h3_panel/final/hyderabad.csv
6283573 Oct 13 19:07 ./data/h3_panel/final/hyderabad.parquet
9288467 Oct 13 19:07 ./data/h3_panel/final/indore.csv
3004804 Oct 13 19:07 ./data/h3_panel/final/indore.parquet
15336134 Oct 13 19:07 ./data/h3_panel/final/kolkata.csv
4476980 Oct 13 19:07 ./data/h3_panel/final/kolkata.parquet
11049693 Oct 13 20:44 ./data/h3_panel/final/mumbai.csv
3202506 Oct 13 20:44 ./data/h3_panel/final/mumbai.parquet
11049693 Oct 13 20:44 ./data/h3_panel/final/mumbai_ssi.csv
2538377 Oct 11 16:29 ./data/processed/coimbatore.parquet
9711761 Oct 11 16:29 ./data/processed/coimbatore_process.csv
1784574 Oct 11 00:25 ./data/processed/mumbai.parquet
7735472 Oct 11 00:25 ./data/processed/mumbai_process.csv
947 Oct 4 13:44 ./data/raw/vulnerability/india_district_vulnerability.csv
947 Oct 11 16:25 ./data/raw/vulnerability/india_district_vulnerability_TEMPLATE.csv
6560 Oct 13 21:25 ./docs/audit/data_audit_mumbai.json
6582 Oct 13 21:25 ./docs/audit/data_audit_mumbai.md
6171 Oct 13 21:25 ./docs/audit/data_audit_coimbatore.json
6193 Oct 13 21:25 ./docs/audit/data_audit_coimbatore.md
460 Oct 4 13:44 ./fetch_temperature.py
5030 Oct 4 13:44 ./generate_report.py
1277 Oct 4 13:44 ./get_bboxes.py
513 Oct 4 13:44 ./read_nc.py
690082 Oct 13 20:44 ./reports/coimbatore_ssi_report.html
1525 Oct 13 20:44 ./reports/ml_thermal_metrics.json
538698 Oct 13 20:44 ./reports/mumbai_ssi_report.html
1832 Oct 13 20:44 ./reports/validation_summary.json
2153 Oct 4 13:44 ./requirements.txt
2836 Oct 4 13:44 ./run_30_cities.py
13677 Oct 4 13:44 ./run_pipeline.py
7384 Oct 13 19:38 ./run_validation_and_novelty.py
824 Oct 4 13:44 ./sample_to_h3.py
230 Oct 4 13:44 ./src/__init__.py
2686 Oct 4 13:44 ./src/export/export_frontend_data.py
41 Oct 4 13:44 ./src/features/__init__.py
8654 Oct 4 13:44 ./src/features/heat_stress.py
7394 Oct 4 13:44 ./src/features/normalize.py
2534 Oct 4 13:44 ./src/features/pollution_exposure.py
19081 Oct 13 20:41 ./src/features/ssi.py
8879 Oct 4 13:44 ./src/features/urban_vulnerability.py
2925 Oct 4 14:05 ./src/features/vegetation_degradation.py
10383 Oct 4 13:44 ./src/features/water_stress.py
39 Oct 4 13:44 ./src/ingest/__init__.py
7223 Oct 4 13:44 ./src/ingest/era5_ingest.py
7701 Oct 4 13:44 ./src/ingest/osm_ingest.py
14204 Oct 10 22:11 ./src/ingest/pm25_ingest.py
12907 Oct 11 14:15 ./src/ingest/satellite_ingest.py
6273 Oct 4 13:44 ./src/ingest/vulnerability_ingest.py
40 Oct 4 13:44 ./src/process/__init__.py
6966 Oct 4 13:44 ./src/process/era5_process.py
9443 Oct 4 13:44 ./src/process/harmonize.py
8575 Oct 4 13:44 ./src/process/osm_to_h3.py
7986 Oct 4 13:44 ./src/process/raster_to_h3.py
0 Oct 4 13:44 ./src/process/sample_to_h3.py
0 Oct 4 13:44 ./src/quality/__init__.py
0 Oct 4 13:44 ./src/utils/__init__.py
865 Oct 10 22:11 ./src/utils/config_loader.py
5383 Oct 4 13:44 ./src/utils/geo_utils.py
7362 Oct 4 13:44 ./src/utils/h3_utils.py
2256 Oct 4 13:44 ./src/utils/logger.py
251 Oct 4 13:44 ./src/viz/__init__.py
7216 Oct 4 13:44 ./src/viz/maps.py
17264 Oct 4 13:44 ./src/viz/plots.py
40081 Oct 4 13:44 ./src/viz/report.py
303 Oct 4 13:44 ./test.py
819 Oct 10 23:30 ./test_modis.py
10863 Oct 13 20:42 ./tests/test_pipeline.py
4479 Oct 13 20:30 ./train_thermal_ml.py
1823 Oct 4 13:44 ./visualize_h3.py
965 Oct 4 13:44 ./visualize_temperature.py
```

### Python Files Inventory
| File | Purpose | Has `__main__` |
|---|---|:---:|
| `audit/audit_data.py` | Step 1 data audit tool for H3 panels (Appendix A) | NO |
| `check_values.py` | Script to inspect exported frontend values for Mumbai | NO |
| `fetch_temperature.py` | Standalone script fetching ERA5 2m temperature via CDS API | NO |
| `generate_report.py` | CLI entry point for generating HTML visualization reports | YES |
| `get_bboxes.py` | Utility computing city bounding boxes via Nominatim | NO |
| `read_nc.py` | Scratch script reading ERA5 temperature.nc | NO |
| `run_30_cities.py` | Batch execution script across 30 Indian cities | YES |
| `run_pipeline.py` | Main CLI orchestrator for the Compound SSI pipeline | YES |
| `run_validation_and_novelty.py` | Validation & novelty evaluation suite (EWM, JT-SSI, MC) | YES |
| `sample_to_h3.py` | Conversion script sampling spatial points to H3 grid | YES |
| `src/__init__.py` | Top-level package initializer | NO |
| `src/export/export_frontend_data.py` | Exporter for web frontend JSON and CSV payloads | YES |
| `src/features/__init__.py` | Features sub-package initializer | NO |
| `src/features/heat_stress.py` | Compute heat stress index from air temp, dewpoint, LST | NO |
| `src/features/normalize.py` | Normalization utilities (zscore, minmax, monthly baseline) | NO |
| `src/features/pollution_exposure.py` | Compute pollution index from PM2.5 concentrations | NO |
| `src/features/ssi.py` | Compute compound sustainability stress index (JT-SSI) | NO |
| `src/features/urban_vulnerability.py` | Compute structural urban vulnerability from OSM & census proxies | NO |
| `src/features/vegetation_degradation.py` | Compute vegetation degradation index from Sentinel-2 NDVI | NO |
| `src/features/water_stress.py` | Compute water stress index via Thornthwaite PET & water deficit | NO |
| `src/ingest/__init__.py` | Data ingest sub-package initializer | NO |
| `src/ingest/era5_ingest.py` | CDS API downloader for ERA5 meteorological reanalysis | NO |
| `src/ingest/osm_ingest.py` | OSMnx vector data ingestion for buildings and roads | NO |
| `src/ingest/pm25_ingest.py` | Downloader for NASA SEDAC surface PM2.5 GeoTIFFs | NO |
| `src/ingest/satellite_ingest.py` | Planetary Computer STAC client for Sentinel-2 & MODIS | NO |
| `src/ingest/vulnerability_ingest.py` | Ingest district census & socioeconomic vulnerability data | NO |
| `src/process/__init__.py` | Process sub-package initializer | NO |
| `src/process/era5_process.py` | NetCDF raster interpolation to H3 grid cells | NO |
| `src/process/harmonize.py` | Master panel merger assembling multi-source H3 dataset | NO |
| `src/process/osm_to_h3.py` | Calculate road density & building footprint per H3 hex | NO |
| `src/process/raster_to_h3.py` | Zonal statistics raster aggregation to H3 cells | NO |
| `src/process/sample_to_h3.py` | Point sampling to H3 resolution | NO |
| `src/quality/__init__.py` | Quality assurance utilities initializer | NO |
| `src/utils/__init__.py` | Shared utilities initializer | NO |
| `src/utils/config_loader.py` | YAML configuration parser and loader | NO |
| `src/utils/geo_utils.py` | Geospatial transformation, projection, and bounding box helpers | NO |
| `src/utils/h3_utils.py` | Uber H3 hexagon lattice geometry & boundary utilities | NO |
| `src/utils/logger.py` | Centralized Loguru logger setup | NO |
| `src/viz/__init__.py` | Visualization package initializer | NO |
| `src/viz/maps.py` | Plotly Mapbox hexagonal choropleth renderer | NO |
| `src/viz/plots.py` | Time series, heatmaps, and radar charts for dashboard | NO |
| `src/viz/report.py` | Standalone HTML dashboard report assembler | NO |
| `test.py` | Configuration verification test | NO |
| `test_modis.py` | MODIS STAC search and tile fetch verification | NO |
| `tests/test_pipeline.py` | Full Pytest suite covering all pipeline phases | NO |
| `train_thermal_ml.py` | Machine Learning Random Forest pipeline predicting LST | YES |
| `visualize_h3.py` | Folium H3 temperature grid visualizer | NO |
| `visualize_temperature.py` | Folium heatmap visualizer for temperature | NO |

---

## B. Data audit summary (per city)

| Item | Mumbai | Coimbatore |
|---|---|---|
| **Panel path / size / modified** | `data/h3_panel/final/mumbai.parquet` / 3.2 MB / 2026-10-13 20:44 | `data/h3_panel/final/coimbatore.parquet` / 4.6 MB / 2026-10-13 20:44 |
| **Rows x cols** | 25,452 rows $\times$ 34 cols | 35,820 rows $\times$ 30 cols |
| **Date range, hexes, balanced?** | 2020-01-01 to 2022-12-01 (36 months), 707 hexes, **Balanced: True** | 2020-01-01 to 2022-12-01 (36 months), 995 hexes, **Balanced: True** |
| **Constant columns** | `bpl_pct`, `slum_pct`, `elderly_pct`, `literacy_pct` | None (socioeconomic columns omitted from panel) |
| **City-scale columns (<=5 distinct/date)** | `pm25` (2.9), `bpl_pct` (1.0), `slum_pct` (1.0), `elderly_pct` (1.0), `literacy_pct` (1.0), `pollution_idx` (2.9), `archetype_id` (2.9) | `pm25` (3.0), `pollution_idx` (3.0), `archetype_id` (4.0) |
| **Per-month-normalised indices** | `heat_stress_idx`, `water_stress_idx` (spread = 0.0000) | `heat_stress_idx`, `water_stress_idx` (spread = 0.0000) |
| **Implied linear weights** | Heat: 0.4545, Veg: 0.4447, Pollution: 0.0762, Vuln: 0.0191, Water: 0.0054 ($R^2 = 1.0$) | Heat: 0.3840, Water: 0.2904, Veg: 0.1978, Pollution: 0.1063, Vuln: 0.0215 ($R^2 = 1.0$) |
| **Implied gamma, clip share** | $\gamma = 0.3000$ (std 0.0), Clipped at 1.0: 1.91% ($n=486$), Exact: True | $\gamma = 0.3000$ (std 0.0), Clipped at 1.0: 1.70% ($n=609$), Exact: True |
| **Variance share (month / hex / residual)** | Between-Month: 65.24%, Between-Hex: 3.36%, Residual: 31.40% | Between-Month: 65.84%, Between-Hex: 2.38%, Residual: 31.78% |
| **Heat vs LST within month (mean, min, max)** | Mean $\rho = 0.169$ (min: -0.342, max: 0.706, $n=36$) | Mean $\rho = 0.244$ (min: -0.109, max: 0.614, $n=36$) |
| **Anomaly top months** | 2022-12-01 (95.6%), 2021-01-01 (52.3%), 2021-03-01 (52.1%) | 2020-05-01 (70.6%), 2022-12-01 (65.9%), 2022-02-01 (59.6%) |
| **Archetypes (count, per hex)** | 6 archetypes, Mean 6.00 archetypes visited per hex | 6 archetypes, Mean 4.73 archetypes visited per hex |

**Skipped checks and reasons:**
* `coimbatore.parquet` lacks columns `bpl_pct`, `slum_pct`, `elderly_pct`, `literacy_pct` (Census vulnerability CSV was only mapped for Mumbai). The audit script naturally skips constant column checks for those omitted fields.

---

## C. Code trace

| ID | Answer (concise) | Evidence (path:lines) | Status |
|---|---|---|---|
| **Q1** | Orchestrated by `run_pipeline.py:run_single_city()`, which invokes `src/features/ssi.py:compute_ssi()`. Final output written via `to_parquet` / `to_csv`. Regeneration command: `python run_pipeline.py --city <city>`. | `src/features/ssi.py:433-545`<br>`run_pipeline.py:157-164, 277-336` | `CONFIRMED` |
| **Q2** | `run_validation_and_novelty.py` is an independent evaluation harness. It defines standalone functions (`compute_ewm_weights`, `compute_jt_ssi`, `run_monte_carlo_sensitivity`), reads final Parquet files read-only, and writes only `reports/validation_summary.json`. It does NOT alter stored panels or any `ssi_*` columns. | `run_validation_and_novelty.py:40-140, 185-188` | `CONFIRMED` |
| **Q3** | Indicators use specific physical models. `heat_stress_idx` and `water_stress_idx` use baseline z-scores grouped by `[h3_index, month]`. Because sample mean is subtracted per calendar month over 3 years, the monthly mean z-score is 0.0 every month, and mapping `(z + 3)/6` forces all calendar months to have an identical mean of 0.5000. | `src/features/normalize.py:170-182, 230-238`<br>`src/features/heat_stress.py:258-272`<br>`src/features/water_stress.py:270-295` | `CONFIRMED` |
| **Q4** | Base weights are computed via PC1 loadings from PCA standardized matrix (`compute_pca_weights()`), then multiplied by city rank multipliers (`apply_city_weight_adjustments()`). Stored linear weights in Mumbai: Heat 0.4545, Veg 0.4447, Pollution 0.0762, Vuln 0.0191, Water 0.0054 ($R^2=1.0$). | `src/features/ssi.py:51-114, 189-228, 464-475` | `CONFIRMED` |
| **Q5** | Compound term uses 4 physical pairs: (Heat, Water), (Heat, Pollution), (Water, Veg), (Pollution, Vuln). Activates when both hazards exceed the global 75th percentile ($q_{0.75}$). Coupling factor $\gamma = 0.3$. Bounded via `.clip(0, 1)`. | `src/features/ssi.py:279-340, 510-522`<br>`config.yml:73-76` | `CONFIRMED` |
| **Q6** | Data source is NASA SEDAC annual mean 1km raster. Ingestion applies a fixed 12-month national seasonality multiplier. Zonal statistics over ~1km pixels inside the city bbox produce only ~3 distinct pixel values per date across the city. | `src/ingest/pm25_ingest.py:25-95`<br>`src/process/raster_to_h3.py:40-120`<br>`config.yml:61-66` | `CONFIRMED` |
| **Q7** | If an entire column is missing, weights are rebalanced over active indicators. Hex-level NaNs are imputed with column medians via `.fillna(df[col].median())`. For compound risk, missing values are filled with 0.0. Thus, `ssi_value` contains zero NaNs. | `src/features/ssi.py:250-275, 305-325` | `CONFIRMED` |
| **Q8** | Anomaly flag identifies rows where `ssi_value` exceeds the 90th percentile of the entire city panel pooled across all hexes and all dates (`np.nanpercentile(ssi_01.values, 90)`). Because it is not month-relative, winter smog months flag over 95% of hexes simultaneously. | `src/features/ssi.py:406-425`<br>`config.yml:89` | `CONFIRMED` |
| **Q9** | K-Means clustering ($k=6$, `random_state=42`) fitted on all rows pooled across all dates and hexes, preceded by `SimpleImputer(strategy='mean')` and `StandardScaler()`. No silhouette or elbow search in pipeline. | `src/features/ssi.py:363-404`<br>`config.yml:88` | `CONFIRMED` |
| **Q10** | Source is `data/raw/vulnerability/india_district_vulnerability.csv`. The table has single district-level aggregate rows (e.g. Mumbai district = 0.18 BPL). Harmonization broadcasts these district scalars uniformly across all H3 hexes. | `src/ingest/vulnerability_ingest.py:25-85`<br>`src/process/harmonize.py:200-220` | `CONFIRMED` |
| **Q11** | `generate_report.py` reads `data/h3_panel/final/{city}.parquet`. It uses the precomputed `ssi_value`, `ssi_band`, and `archetype_id` directly without recomputation. | `generate_report.py:37-60, 80-120` | `CONFIRMED` |
| **Q12** | Documents claim EWM weights (Heat 0.218, Water 0.233, etc.) are used for SSI, whereas the stored panel actually uses PCA loadings (Heat 0.455, Veg 0.445). Study period (2020-2022), resolution (H3 res-8), and JT-SSI formula are confirmed. | `TOP_TIER_IMPLEMENTATION_PLAN.md:105-115`<br>`src/features/ssi.py:464-475` | `CONFLICT` |
| **Q13** | Dependencies specified in `requirements.txt`. Tested on Python 3.13. Fixed seed `random_state=42` used in KMeans and Random Forest. Panel generation runtime ~40 seconds per city; report generation ~3 seconds. | `requirements.txt:1-50`<br>`src/features/ssi.py:400` | `CONFIRMED` |

---

### Code Trace Snippets

#### Q1 Evidence (`run_pipeline.py:157-164`)
```python
def run_ssi(panel: pd.DataFrame, city: str) -> pd.DataFrame:
    """Compute the SSI composite score and derived columns."""
    log.info("=== SSI phase ===")

    from src.features.ssi import compute_ssi
    panel = compute_ssi(panel, city)
    return panel
```

#### Q3 Evidence (`src/features/normalize.py:170-179, 230-238`)
```python
    min_year = df["_year"].min()
    baseline_df = df[df["_year"] <= (min_year + baseline_years - 1)]

    stats = (
        baseline_df
        .groupby([groupby_col, "_month"])[value_col]
        .agg(baseline_mean="mean", baseline_std="std")
        .reset_index()
        .rename(columns={"_month": "month"})
    )
...
    normalized = (raw - merged["baseline_mean"]) / std
    if apply_floor:
        normalized = normalized.clip(lower=-3.0, upper=3.0)
        normalized = (normalized + 3.0) / 6.0
```

#### Q4 Evidence (`src/features/ssi.py:95-98, 474-482`)
```python
    pca = PCA(n_components=1)
    pca.fit(X)
    loadings = np.abs(pca.components_[0])
    weights_raw = loadings / loadings.sum()
...
    adjusted_weights = apply_city_weight_adjustments(base_weights, city, config)
    ssi_linear_raw = compute_ssi_value(df, adjusted_weights)
```

#### Q5 Evidence (`src/features/ssi.py:279-317`)
```python
def compute_joint_tail_amplifier(
    df: pd.DataFrame,
    pairs: list[tuple[str, str]] = PHYSICAL_INTERACTION_PAIRS,
    quantile_thresh: float = 0.75,
) -> pd.Series:
...
    for col_i, col_j in pairs:
        if col_i in df.columns and col_j in df.columns:
            tail_mask = (val_i > q_i) & (val_j > q_j)
            geom_mean = np.sqrt(val_i * val_j)
            omega += tail_mask.astype(float) * geom_mean
```

#### Q7 Evidence (`src/features/ssi.py:269-275`)
```python
    ssi_raw = pd.Series(0.0, index=df.index)
    for col, w in active.items():
        rebalanced_w = w / total_w
        values = df[col].fillna(df[col].median())
        ssi_raw += rebalanced_w * values
    return ssi_raw
```

#### Q8 Evidence (`src/features/ssi.py:420-425`)
```python
def assign_anomaly_flag(
    ssi_01: pd.Series,
    threshold_pct: float = 90.0,
) -> pd.Series:
    threshold = np.nanpercentile(ssi_01.values, threshold_pct)
    return pd.Series(ssi_01 > threshold, index=ssi_01.index, name="anomaly_flag")
```

---

## D. Verification of external observations

| ID | Status | Evidence |
|---|:---:|---|
| **O1** | `CONFIRMED` | Regression of `ssi_linear` against 5 indices in `docs/audit/data_audit_mumbai.json`: Heat = 0.4545, Veg = 0.4447, Pollution = 0.0762, Vuln = 0.0191, Water = 0.0054 with $R^2 = 1.000000$ and intercept = 0.00000. |
| **O2** | `CONFIRMED` | Audit report JSON confirms `implied_gamma_median = 0.30000`, `implied_gamma_std = 0.000000`, `share_clipped_at_1 = 0.0191` (1.91%), and `additive_formula_exact = true`. |
| **O3** | `CONFIRMED` | In both Mumbai and Coimbatore, `monthly_mean_spread` for `heat_stress_idx` and `water_stress_idx` is `0.00000`. Both have identical ranges: min = 0.30755, max = 0.69245, mean = 0.50000, std = 0.13609. |
| **O4** | `CONFIRMED` | `distinct_per_date_avg` for `pm25` is 2.9 in Mumbai and 3.0 in Coimbatore. `pm25` is flagged in `city_scale_cols(<=5 distinct per date)`. |
| **O5** | `CONFIRMED` | In Mumbai, `constant_cols` lists `['bpl_pct', 'slum_pct', 'elderly_pct', 'literacy_pct']` with 1 distinct value per column across all 707 hexes. |
| **O6** | `CONFIRMED` | `ssi_var_share` in Mumbai: `between_month = 0.6524` (65.2%), `between_hex = 0.0336` (3.4%), and `hex_x_month_residual = 0.3140` (31.4%). |
| **O7** | `CONFIRMED` | In Mumbai, `missing_by_date_top3` confirms `ndvi` has 707 missing hexes on `2022-11-01` (100% missing); `pm25` has 707 missing hexes on `2021-12-01`; `lst_c` gaps cluster in monsoon months (`2022-07-01`: 47, `2020-07-01`: 29, `2022-08-01`: 26). |
| **O8** | `CONFIRMED` | `anomaly_top_months` confirms that on `2022-12-01`, 95.6% of all hexes in Mumbai are simultaneously flagged as anomalies. |
| **O9** | `CONFIRMED` | `archetypes_per_hex_avg` is exactly 6.00 in Mumbai (every single hex transitions through all 6 archetypes over 36 months). |
| **O10** | `CONFIRMED` | `implied_linear_weights` in `data/h3_panel/final/mumbai.parquet` are Heat: 0.4545, Veg: 0.4447, Pollution: 0.0762, Vuln: 0.0191, Water: 0.0054 (from PCA). The EWM weights (0.218, 0.233) are only calculated in `run_validation_and_novelty.py` and are NOT stored in the panel. |

---

## E. Canonical pipeline declaration

1. **Command that regenerates each panel end to end:**  
   ```bash
   python run_pipeline.py --city mumbai
   python run_pipeline.py --city coimbatore
   ```
2. **Files that are STALE or inconsistent with the code:**  
   * `data/processed/mumbai.parquet`: Stale intermediate file without indicator columns.
   * `TOP_TIER_IMPLEMENTATION_PLAN.md`: Section 3 claims the panel uses EWM weights, but the panel is computed using PCA loadings.
3. **Is the weighting used in the stored panel the same as the one the validation script reports?**  
   **NO.** The stored panel `ssi_linear` uses PCA-derived weights (`heat: 0.4545`, `veg: 0.4447`, `pollution: 0.0762`, `vuln: 0.0191`, `water: 0.0054`), whereas `run_validation_and_novelty.py` calculates and displays Entropy Weight Method (EWM) weights (`heat: 0.2181`, `water: 0.2334`, `vuln: 0.2112`, `veg: 0.2048`, `pollution: 0.1325`).
4. **Do the dashboards display stored `ssi_value` or recomputed values?**  
   **STORED.** `generate_report.py:51-60` loads `data/h3_panel/final/{city}.parquet` directly and renders the stored `ssi_value`, `ssi_band`, and `archetype_id` without recalculating them.

---

## F. Bugs and risks found (do not fix)

| # | Description | Evidence | Severity |
|---|---|---|:---:|
| **1** | **Calendar-Month Normalization Erases Absolute Heatwaves & Droughts:** `normalize.py` groups baseline statistics by calendar month over 3 years. This forces the mean z-score of January and May to both equal 0.0, mapping both to exactly 0.5000 and erasing seasonal heatwave signals. | `src/features/normalize.py:176-177, 238`<br>`docs/audit/data_audit_mumbai.json:167-168` | HIGH |
| **2** | **Weighting Mismatch Between Plan and Stored Panels:** Stored panels use PCA loadings (dominated by heat 45% and veg 44%, with water < 1%), while documentation presents EWM weights (~20% balanced across all 5). | `src/features/ssi.py:467, 478`<br>`TOP_TIER_IMPLEMENTATION_PLAN.md:106` | HIGH |
| **3** | **Global Anomaly Pooling Causes Seasonal Batch Alerting:** Because `anomaly_flag` uses a global 90th percentile across all dates and hexes, 95.6% of Mumbai hexes are flagged as anomalies in winter (2022-12) due to seasonal PM2.5, rather than local spatial outliers. | `src/features/ssi.py:420-425`<br>`docs/audit/data_audit_mumbai.json:283` | MEDIUM |
| **4** | **Synthetic Uniform Socioeconomic Values:** Census indicators (`bpl_pct`, `slum_pct`, etc.) are identical constants across all 707 hexes in Mumbai, providing zero spatial socioeconomic variation. | `data/raw/vulnerability/india_district_vulnerability.csv`<br>`docs/audit/data_audit_mumbai.json:71-76` | HIGH |
| **5** | **Imposed PM2.5 Seasonality on Coarse 1km Raster:** Monthly PM2.5 is generated by multiplying an annual raster by a fixed national index, producing only ~3 unique values per month across the city. | `src/ingest/pm25_ingest.py:65-95`<br>`docs/audit/data_audit_mumbai.json:96, 119` | MEDIUM |

---

## G. Open questions for the human (max 5)

1. Should the canonical panel generation script (`run_pipeline.py` / `ssi.py`) be switched from PCA weights to the balanced Entropy Weight Method (EWM) weights?
2. Should `heat_stress_idx` and `water_stress_idx` normalization be changed from per-calendar-month baseline z-scores to global multi-year scaling to restore the summer heatwave and winter comfort signals?
3. Should `anomaly_flag` be computed relative to each month's distribution rather than pooled across all 36 months to prevent 95% of hexes being flagged simultaneously in winter?
4. Do you want to ingest ward-level Census 2011 Primary Census Abstract (PCA) data to replace the uniform district constant vulnerability values?
5. Should Coimbatore's pipeline ingest vulnerability data to provide the same 34-column schema as Mumbai?
