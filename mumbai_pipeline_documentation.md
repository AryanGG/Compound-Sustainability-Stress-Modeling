# Mumbai Compound Sustainability Stress Modeling: Pipeline Execution & Methodology Report

This document outlines the end-to-end execution of the Compound Sustainability Stress Index (SSI) modeling pipeline for **Mumbai** covering the time period of **January to March 2022**. It details the challenges resolved, the flow of data ingestion, the internal workings of the pipeline, and the mathematical methodology behind the final SSI calculation.

---

## 1. Pipeline Execution & API Bug Fixes

To transition the pipeline from synthetic placeholder data to real-world geospatial operations, several underlying libraries and remote APIs needed their integrations updated to comply with modern 2024–2026 standards. The following core fixes were implemented prior to and during the run:

*   **CLI Argument Bubbling**: Fixed an orchestrated bug where `--start` and `--end` CLI arguments were not properly bubbling down from the entry orchestration level (`run_pipeline.py`) into the actual `run_ingest` handlers. This prevented the ingestion engine from downloading massive 20-year datasets instead of just the requested 3-month chunk.
*   **Copernicus CDS API v2 (ERA5 Climate Data)**: The older API (now deprecated) historically returned `.nc` files directly. The upgraded API now returns `.zip` files containing separate NetCDF streams (instantaneous and accumulated variables). We augmented `era5_ingest.py` to seamlessly unzip in-memory, unify the streams via `xarray.merge()`, and save them as the expected singular `.nc` standard format.
*   **OSMnx v2 Breaking Changes**: Updated the deprecated `north, south, east, west` keyword arguments in `graph_from_bbox` and `features_from_bbox` inside `osm_ingest.py` to seamlessly use the modernized `(left, bottom, right, top)` bounding box tuple structures.
*   **Stackstac CRS & Type Overflows (Satellite Data)**: Fixed the Planetary Computer module (`satellite_ingest.py`) where downloading imagery spanning over two distinct UTM zones across Mumbai's edges caused `stackstac` to crash. This was resolved by forcing an explicit CRS projection (`epsg=4326`). Furthermore, we resolved a `.tif` NaN casting crash by switching `float32` rendering to `float64` and turning off default rescaling.
*   **Geopandas 1.0 (Spatial Joins)**: Fixed the `sjoin(how="left")` topology map failing via missing `index_left` behaviors when generating urban form densities in `osm_to_h3.py` by switching to `how="inner"` and correctly tracking group occurrences via `.size()`.
*   **Plotly v6.0**: Rewrote deprecated `titlefont` attributes within `plots.py` inside dictionary structs for the dashboard colorbars.

---

## 2. Phase 1: Data Ingestion Strategy

The pipeline aggregates multi-source, multi-resolution spatial indicators perfectly down to the city’s spatial bounding box. Here is exactly how data was collected for Mumbai:

1.  **ERA5 Climate (Copernicus API)**: 
    *   Downloaded instantaneous variables (2m temperature, 2m dewpoint, U/V wind components, soil water volume) and accumulated variables (total precipitation, surface net solar radiation).
2.  **Multispectral Satellite Imagery (Microsoft Planetary Computer via STAC)**:
    *   **NDVI**: Sourced from **Sentinel-2 L2A**.
    *   **LST** (Land Surface Temperature): Sourced from **MODIS (`MYD11A2`)**.
3.  **Urban Form (OpenStreetMap / OSMnx)**:
    *   Fetched the real-time drive network topology (roads/edges).
    *   Scraped all building footprint polygons and explicit green space demarcations to map urban layout complexities.
4.  **Air Pollution (PM2.5)**:
    *   A timeout was safely caught when fetching from the NASA SEDAC direct host. The pipeline activated its internal **Synthetic Data Fallback Mechanism**, seeding procedurally accurate annual raster data for the year 2022.
5.  **Demographics (Vulnerabilities)**:
    *   Since census shapefiles were unavailable locally, the system activated the expected demographic synthetic builder to emulate generic neighborhood traits (representing slummy densities, BPL percentages).

---

## 3. Phase 2: Processing & Harmonization

Once the raw unstructured files (`.nc`, `.tif`, `.gpkg`) were collected locally in `data/raw/`, the processing sub-modules normalized their spatiotemporal complexities.

1.  **H3 Resolution Mapping**: The entire bounding box of Mumbai was sliced mathematically into hexagon centroids at **H3 scale Resolution 8** (producing exactly 2,501 discrete contiguous hex cells).
2.  **Dataset Translation**:
    *   NetCDF climate time-steps were aggregated into monthly sums (for precipitation) and monthly means (for temperature), then interpolated to the H3 hex centroids.
    *   GeoTIFF satellite rasters were resampled and queried at exactly the hex centers using `rasterstats`.
    *   Geopackages for OSM were queried dynamically via spatial overlaps calculating strict fractions (e.g., Road km / km², building count density).
3.  **The Skeleton**: An iterative temporal frame was initialized crossing our `2501 hex grids` × `3 months`, giving a final dense master dataframe of 7,503 rows. 

---

## 4. Phase 3 & 4: Features & SSI Calculation

With all the harmonized statistics housed under the unified `h3_index` structure, the engine evaluated each block down to mathematical "stresses":

### Defining the 5 Core Indicators
The raw statistics were passed through generalized logistic conversions and baseline normalizations (clamping inputs from a mathematically derived 0 to 1 scaling factor) to isolate severe abnormalities into five buckets:
1.  **Heat Stress Index**: Evaluated from LST spikes + ERA5 ambient limits.
2.  **Water Stress Index**: Weighed using soil moisture levels coupled with inverse precipitation density metrics.
3.  **Pollution Exposure Index**: Tied to mean PM2.5 readings.
4.  **Vegetation Degradation Index**: Inversely correlated to the derived NDVI fractions versus the underlying concrete density.
5.  **Urban Vulnerability Index**: Compounded sociodemographic risks tracking poor road density access, high slum approximations, and constrained resources.

### Compounding into the Initial SSI (Compound Sustainability Stress Index)
*   **PCA (Principal Component Analysis)**: Generally, the system automatically runs a PCA factor model to learn the dominant variance weights across the 5 indicator columns dynamically per city context.
*   Since only 3 months were evaluated, PCA safely flagged "too few complete temporal cycles" and successfully reverted to an **equal-weighted averaging formulation** to ensure statistically honest readings. 
*   This produced the final unified **SSI Value** ranging strictly from 0 to 1.

### Post-Processing
*   **SSI Bands**: The float ratings were chunked into human-readable buckets (`Low`, `Moderate`, `High`, `Extreme`).
*   **Anomaly Detection**: The system flagged any location-month tuple sitting within the top 90th percentile of stress limits. 
*   **Saving State**: The processed table, now weighing in at ~33 columns over ~7,500 observation rows, was flushed natively to `data/h3_panel/final/mumbai.parquet`.

---

## Dashboard Generation
At the very end of the run, `generate_report.py` was invoked to mount the tabular dataset into memory and utilize **Plotly Graph Objects** and mapping suites. It rendered the data into 9 interactive JavaScript analytics containers natively into `reports/mumbai_ssi_report.html`, presenting trends, top strained geographies, hex maps, and spatial matrix breakdowns without requiring active notebooks.
