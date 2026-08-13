# Compound Sustainability Stress Index (SSI) -- Complete Project Walkthrough

This reference guide provides a complete, mathematically detailed walkthrough of the **Compound Sustainability Stress Index (SSI)** modeling pipeline. It details the project architecture, directory structure, data ingestion methods, and exact calculations used to generate the monthly grid-scale stress profiles and visual reports.

---

## Executive Summary
The Compound Sustainability Stress Index (SSI) is a composite spatial-temporal environmental risk modeling framework. Designed to run at a city-scale across 10 major Indian cities, the pipeline harmonizes heterogeneous climate, satellite, air quality, urban form, and demographic datasets onto a uniform **H3 hexagonal grid (Resolution 8)**. By calculating five localized stress indicators and combining them using weights derived from **Principal Component Analysis (PCA)**, the framework enables local municipal corporations and urban planners to identify compounding environmental stress hotspots and target interventions effectively.

---

## 1. Project Overview & Folder Structure

This project implements an end-to-end data ingestion, processing, modeling, and reporting pipeline. The workflow is organized into the following phases:

```
[Phase 1: Ingest]       --> Download raw variables from Copernicus CDS, STAC, OSM, and priors
[Phase 2: Process]      --> Resample and map vector/raster variables onto H3 hexagonal grids
[Phase 3: Features]     --> Compute 5 stress indicators (Heat, Water, Pollution, Vegetation, Vulnerability)
[Phase 4: SSI Model]    --> Standardize inputs and calculate weighted composite SSI via PCA
[Phase 5: Report]       --> Compile final tabular datasets into interactive HTML dashboards
```

### Folder Layout
```
Compound-Sustainability-Stress-Modeling/
├── config.yml                  # Master config (parameters, cities, weights)
├── cities_bbox.json            # Reference boundaries & stressors per city
├── requirements.txt            # Package dependencies
├── run_pipeline.py             # Main CLI execution orchestrator
├── generate_report.py          # Visual dashboard builder
├── get_bboxes.py               # Helper to fetch bounding boxes from OSMnx
├── fetch_temperature.py        # Helper to fetch test ERA5 NetCDF files
│
├── src/
│   ├── __init__.py
│   ├── ingest/                 # Raw data downloader wrappers
│   │   ├── era5_ingest.py      # Copernicus CDS API climate variables
│   │   ├── satellite_ingest.py # NDVI, LST, Built-up via Planetary Computer
│   │   ├── pm25_ingest.py      # PM2.5 download & fallback generators
│   │   ├── osm_ingest.py       # OpenStreetMap features download via OSMnx
│   │   └── vulnerability_ingest.py  # Demographic vulnerability prior generator
│   │
│   ├── process/                # Spatial & temporal alignment modules
│   │   ├── era5_process.py     # NetCDF parsing and H3 mapping
│   │   ├── raster_to_h3.py     # Satellite rasters to H3 zonal statistics
│   │   ├── osm_to_h3.py        # Road/Building density & green space overlays
│   │   └── harmonize.py        # Master left-merger for spacetime skeleton
│   │
│   ├── features/               # Stress indicators & composite index calculation
│   │   ├── heat_stress.py      # Magnus RH, Rothfusz Heat Index, LST blending
│   │   ├── water_stress.py     # Precipitation deficit, Thornthwaite PET, Soil Moisture
│   │   ├── pollution_exposure.py # WHO PM2.5 exceedance and z-score blending
│   │   ├── vegetation_degradation.py # Inverted baseline NDVI z-scores
│   │   ├── urban_vulnerability.py # Physical (OSM) & Socio-Economic UVI
│   │   ├── normalize.py        # Baseline rolling z-score and minmax logic
│   │   └── ssi.py              # PCA weights, K-means archetypes, anomaly flags
│   │
│   ├── viz/                    # Data visualization scripts
│   │   ├── maps.py             # Interactive choropleth map generation
│   │   ├── plots.py            # Component trend plots, correlation matrix, radar chart
│   │   └── report.py           # Single-page HTML assembly script
│   │
│   └── utils/                  # Cross-cutting utility functions
│       ├── h3_utils.py         # H3 indexing & time skeleton structures
│       ├── geo_utils.py        # Vector-to-raster utilities
│       ├── config_loader.py    # Loads config.yml parameters
│       └── logger.py           # Console and file logging configuration
│
├── tests/                      # Integration test suite
│   └── test_pipeline.py
│
├── data/                       # Directory structure (empty in clean state)
│   ├── raw/                    # Cached remote data downloads
│   ├── processed/              # Spatial-temporal tabular parquet panels (pre-SSI)
│   ├── metadata/               # Log metadata, runs checksums
│   └── h3_panel/               # Final computed SSI parquet panels
└── reports/                    # Generated self-contained HTML dashboards
```

---

## 2. Spatial & Temporal Harmonization (Phase 1 & 2)

Before any indices are computed, the codebase creates a uniform spatial-temporal skeleton to integrate raw datasets of disparate formats (NetCDF, GeoTIFF, vector polygons, CSVs).

1. **City Spatial Boundary Mapping**:
   The bounding box of a city is retrieved from `cities_bbox.json`. 
2. **Grid Generation**:
   The project overlays a grid of **H3 hexagonal cells at resolution 8 (cell area ~0.74 km2)** over the bounding box. This is executed using:
   ```python
   h3.polygon_to_cells(geojson_geometry, resolution=8)
   ```
3. **Temporal Spacing**:
   A master template table is generated by taking the Cartesian product of all active H3 index cells and every month within the timeline (e.g., `2015-01` to `2025-12`).
4. **Data Joining**:
   Processed climate, satellite, pollution, and static socio-economic features are mapped to H3 indices and merged onto this master spacetime skeleton via a left-join.

---

## 3. Mathematical Calculations of the 5 Stress Indicators (Phase 3)

| Indicator | Short Name | Key Data Inputs | Core Logic |
| :--- | :--- | :--- | :--- |
| **Heat Stress Index** | HSI | ERA5 Temp, Dewpoint; satellite LST | Blends perceived Heat Index and skin LST; baseline-normalized |
| **Water Stress Index** | WSI | ERA5 Precipitation, Soil Moisture | Evaluates precipitation deficits against PET and soil water levels |
| **Pollution Exposure** | PEI | Ground/Satellite PM2.5 | Compares PM2.5 levels to WHO guideline and seasonal z-score |
| **Vegetation Degradation**| VDI | Sentinel-2 NDVI | Identifies loss of vegetation via inverted monthly NDVI anomalies |
| **Urban Vulnerability** | UVI | OSM building/road data; demographics | Combines physical densities and socio-economic vulnerability priors |

---

### Indicator 1: Heat Stress Index (HSI)
The Heat Stress Index measures extreme thermal exposure by blending ambient heat index metrics with skin surface temperatures.

1. **Relative Humidity (RH)**: Estimated using the Magnus-Tetens approximation from 2m air temperature ($T$) and 2m dewpoint temperature ($T_d$):
   $$RH = 100 \times \frac{\exp\left(\frac{17.625 \cdot T_d}{243.04 + T_d}\right)}{\exp\left(\frac{17.625 \cdot T}{243.04 + T}\right)}$$
   The output is clipped to $[0, 100]$ percent.
2. **Steadman/Rothfusz Heat Index (HI)**: 
   If $T > 26^\circ\text{C}$ and $RH > 40\%$, the Rothfusz regression equation calculates perceived temperature in degrees Celsius:
   $$HI = -8.78469 + 1.61139411 \cdot T + 2.338549 \cdot RH - 0.14611605 \cdot T \cdot RH - 0.01230809 \cdot T^2 - 0.01642482 \cdot RH^2 + 0.002211732 \cdot T^2 \cdot RH + 0.00072546 \cdot T \cdot RH^2 - 0.000003582 \cdot T^2 \cdot RH^2$$
   If conditions are cooler than the threshold, it defaults to:
   $$HI = T$$
3. **LST Blending**: Land Surface Temperature (LST) is combined with the perceived Heat Index using weights derived dynamically from PCA or equal weighting (0.5 each):
   $$\text{Blended Heat} = w_{hi} \cdot HI + w_{lst} \cdot LST$$
4. **Baseline-Aware Normalization**: The blended score is normalized using a calendar-month baseline z-score (using the first 3 years as a reference period) to extract the anomaly relative to seasonal expectations:
   $$HSI = \max\left(0, \frac{\text{Blended Heat} - \mu_{\text{baseline}, \text{month}}}{\sigma_{\text{baseline}, \text{month}}}\right)$$

---

### Indicator 2: Water Stress Index (WSI)
The Water Stress Index captures agricultural and hydrological drought by evaluating precipitation deficits against evapotranspiration demands and soil moisture.

1. **Thornthwaite Potential Evapotranspiration (PET)**:
   PET (mm/month) is computed using:
   $$PET_{\text{unadj}} = 16 \times \left(10 \times \frac{T_+}{I}\right)^a$$
   where:
   *   $T_+$ is the mean monthly temperature clamped at $0^\circ\text{C}$.
   *   $I$ is the annual heat index of the hex cell: $I = \sum_{m=1}^{12} \left(\frac{T_m}{5}\right)^{1.514}$
   *   $a = 6.75 \times 10^{-7} \cdot I^3 - 7.71 \times 10^{-5} \cdot I^2 + 0.01792 \cdot I + 0.49239$
   *   This raw PET is adjusted for latitude ($\phi$) and solar declination ($\delta$) to account for day length and calendar month length:
       $$PET = PET_{\text{unadj}} \times \left(\frac{L}{12}\right) \times \left(\frac{N}{30}\right)$$
       where $L$ is daylight hours and $N$ is the number of days in the month.
2. **Precipitation Deficit**: Computed by evaluating negative rainfall anomalies against the historical monthly baseline (lower rainfall yields higher stress).
3. **Soil Moisture Deficit**: Evaluated as the deviation below the historical 25th percentile of soil moisture.
4. **Blending**: The Precipitation Deficit and Soil Moisture Deficit are merged (using PCA or equal weighting) and baseline-normalized:
   $$WSI = \max\left(0, \frac{\text{Blended Deficit} - \mu_{\text{baseline}, \text{month}}}{\sigma_{\text{baseline}, \text{month}}}\right)$$

---

### Indicator 3: Pollution Exposure Index (PEI)
The Pollution Exposure Index weights ambient PM2.5 concentrations against WHO health limits alongside local anomalies.

1. **WHO Exceedance Component**:
   Calculated as the fraction by which local PM2.5 exceeds the WHO annual guideline threshold ($15\,\mu\text{g}/\text{m}^3$):
   $$\text{WHO Exceedance} = \max\left(0, \frac{\text{PM2.5} - 15.0}{15.0}\right)$$
   This is then minmax-normalized to $[0, 1]$.
2. **Temporal Anomaly Component**:
   The baseline-normalized z-score of the raw PM2.5 values:
   $$\text{Temporal Anomaly} = \max\left(0, \frac{\text{PM2.5} - \mu_{\text{baseline}, \text{month}}}{\sigma_{\text{baseline}, \text{month}}}\right)$$
3. **Combined PEI**:
   $$PEI = 0.5 \times \text{WHO Exceedance (Normalized)} + 0.5 \times \text{Temporal Anomaly (Z-score)}$$

---

### Indicator 4: Vegetation Degradation Index (VDI)
The Vegetation Degradation Index tracks green cover loss using baseline-normalized NDVI anomalies.

1. **NDVI Z-Score**:
   NDVI values ($0$ to $1$) are compared to historical calendar-month baselines:
   $$z_{\text{ndvi}} = \frac{\text{NDVI} - \mu_{\text{baseline}, \text{month}}}{\sigma_{\text{baseline}, \text{month}}}$$
2. **Inversion & Flooring**:
   Since lower NDVI values indicate higher degradation (stress), the z-score is inverted (multiplied by $-1$) and floored at $0$:
   $$VDI = \max\left(0, -z_{\text{ndvi}}\right)$$

---

### Indicator 5: Urban Vulnerability Index (UVI)
Urban Vulnerability is a static index mapping exposure built from physical (OSM) and socio-economic datasets.

1. **Physical/Structural Vulnerability**:
   Combines building density, building footprint fraction, road density, and the absence of green spaces:
   $$\text{Physical} = w_1 \cdot \text{norm}(\text{Building Density}) + w_2 \cdot \text{norm}(\text{Footprint Fraction}) + w_3 \cdot \text{norm}(\text{Road Density}) + w_4 \cdot (1 - \text{norm}(\text{Green Space}))$$
   The sub-indicator weights are derived dynamically using nested PCA.
2. **Socio-Economic Vulnerability**:
   Combines percentage of population below the poverty line (BPL), slum residency fractions, elderly demographic fractions, and inverse literacy rates:
   $$\text{Socio-Economic} = v_1 \cdot \text{norm}(\text{BPL\%}) + v_2 \cdot \text{norm}(\text{Slum\%}) + v_3 \cdot \text{norm}(\text{Elderly\%}) + v_4 \cdot (1 - \text{norm}(\text{Literacy\%}))$$
3. **Combined UVI**:
   $$UVI = 0.4 \times \text{Physical} + 0.6 \times \text{Socio-Economic}$$

---

## 4. Compound SSI Calculation & Post-Processing (Phase 4)

Once the 5 component indices (HSI, WSI, PEI, VDI, UVI) are computed, they are integrated into a single index.

### Principal Component Analysis (PCA) Weighting
The pipeline extracts the principal driver of environmental variance:
1. The 5 indicators are gathered into a matrix $\mathbf{X}$ and standardized to zero-mean and unit-variance.
2. PCA is fit to solve the eigenvectors:
   $$\mathbf{X}^T \mathbf{X} \mathbf{v}_i = \lambda_i \mathbf{v}_i$$
3. The loadings of the first principal component (PC1), which explains the maximum variance, define the indicator weights:
   $$w_i = \frac{|v_{1, i}|}{\sum_{j=1}^5 |v_{1, j}|}$$
4. **Fallback**: If the city dataset contains fewer than 30 valid observation rows (e.g. during test runs), the pipeline reverts to equal weights:
   $$w_i = 0.20 \quad (\forall i)$$

### Composite Calculation
The compound index is the weighted sum adjusted by city-specific parameter overrides:
$$SSI_{\text{raw}} = \sum_{i=1}^5 w_i \cdot \text{Indicator}_i$$
The final $SSI$ value is minmax-normalized to fit strictly within $[0, 1]$.

### Post-Processing Steps
*   **SSI Risk Bands**: Categorizes cell states into four bins:
    *   `Low`: $SSI \le 0.25$
    *   `Moderate`: $0.25 < SSI \le 0.50$
    *   `High`: $0.50 < SSI \le 0.75$
    *   `Extreme`: $SSI > 0.75$
*   **Anomaly Flag**: Marks observations where $SSI > 90\text{th percentile}$ of the city's historical records.
*   **Stress Archetypes**: A K-means algorithm groups cells into 6 clusters based on the 5-dimensional indicator profiles.

---

## 5. Report Generation & Visualizations (Phase 5)

The `generate_report.py` script aggregates the spatial-temporal table into a single self-contained interactive HTML dashboard containing the following visual elements:
1. **Interactive H3 Map**: A choropleth map showing time-averaged SSI values per hexagon.
2. **SSI Risk Band Donut**: A breakdown of observations across Low, Moderate, High, and Extreme categories.
3. **Temporal SSI Trend**: A line chart showing monthly city-wide mean SSI with standard deviation bands.
4. **Anomaly Timeline**: A bar chart illustrating the percentage of cells flagged as anomalies over time.
5. **5-Indicator Trends**: Multi-line trends tracking components (Heat, Water, Pollution, Vegetation, Vulnerability).
6. **Seasonal Heatmap**: A Year $\times$ Month grid detailing monthly seasonal stress intensity.
7. **Indicator Correlation Matrix**: A Pearson correlation grid mapping indicators.
8. **Stress Archetype Radar Chart**: A radar visualization mapping the K-means cluster centroids.
9. **Priority Scatter Plot**: BPL% plotted against SSI to identify compounding socio-economic deprivation hotspots.

---

## 6. Execution Guide

### Environment Setup
Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Pipeline
Run the entire end-to-end pipeline (Ingestion $\to$ Processing $\to$ Feature Extraction $\to$ SSI Calculation) using synthetic fallback data for all cities:
```bash
python run_pipeline.py --city all --phase all --synthetic
```

To run for a specific city (e.g., Mumbai) using real API data (requires CDS API credentials and key setups):
```bash
python run_pipeline.py --city mumbai --phase all
```

### Generating the HTML Reports
Compile the final calculated parquet outputs into the interactive HTML dashboards:
```bash
python generate_report.py --city all
```
The resulting dashboards will be generated and saved in the `reports/` folder.
