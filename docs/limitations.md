# Modeling & Data Limitations (SSI v2)

This document establishes the methodological boundaries, structural data constraints, and interpretation caveats for the Compound Sustainability Stress Index (SSI v2) framework. Transparent disclosure of these limitations is required to ensure scientific integrity and prevent unwarranted claims.

---

### 1. Spatial Resolution of Atmospheric Pollution (CAMS EAC4)
Atmospheric PM₂.₅ concentrations are derived from ECMWF Copernicus Atmosphere Monitoring Service (CAMS) EAC4 global reanalysis at approximately 0.75° × 0.75° horizontal resolution (~80 km grid spacing). Because this resolution encompasses the entire metropolitan extent of individual cities, the pollution indicator functions as a city-wide monthly temporal forcing rather than providing intra-urban spatial discrimination across individual H3 resolution 8 cells (~0.74 km²). In `results/diagnostics_variance.json`, the between-hex spatial variance share for PM₂.₅ is 0.0000 in Coimbatore and 0.0000 in Mumbai. Fine-scale neighborhood air pollution disparities are therefore not captured by this global reanalysis layer.

### 2. Temporal Dominance of Hydrological Water Stress
Water stress inputs derived from ERA5 reanalysis (total precipitation deficit and volumetric soil water layers 1 and 2 at ~11 km resolution) are predominantly temporal signals. In `results/diagnostics_variance.json`, between-month variance accounts for 98.16% of total water stress variance in Mumbai and 92.99% in Coimbatore, whereas between-hex spatial variance accounts for only 0.81% and 4.95% respectively. Water stress accurately reflects regional seasonal drought and monsoon timing across the entire metropolitan basin, but does not model hyper-local stormwater ponding, piped water distribution inequities, or micro-watershed drainage differences.

### 3. Static Socio-Economic Vulnerability and Built Exposure
The exposure component (`exposure_v2`) combines Census of India 2011 demographic indicators (Below Poverty Line household percentage, slum population percentage, elderly population percentage, and illiteracy) with OpenStreetMap building and road morphology. While spatial variation across hexes is high (accounting for 100% of exposure variance in `results/diagnostics_variance.json`), these inputs are time-invariant across the 36-month study window (2020–2022). Consequently, temporal fluctuations in the composite SSI index are driven strictly by the biophysical and environmental components, while exposure acts as a stationary spatial vulnerability multiplier.

### 4. Missing Observation Window (November 2022)
As documented in `docs/data_dictionary.md`, satellite and reanalysis feeds experienced an ingestion gap in November 2022. To maintain panel continuity without introducing synthetic artefacts, November 2022 values were imputed via nearest-month temporal forward-fill from October 2022 across both cities. As a result, November 2022 reflects late-monsoon transition conditions and does not capture distinct short-term meteorological anomalies occurring in that calendar month.

### 5. Modest Spatial Agreement with Independent Satellite LST
The heat stress indicator (`heat_v2`) is constructed from ERA5 2m dry-bulb temperature and dewpoint temperature (Heat Index) to capture human bioclimatic thermal stress. Validation check V3 in `results/validation.json` against held-out MODIS MOD11A2 Land Surface Temperature (LST, 1 km resolution) reveals modest within-month spatial rank agreement: mean within-month Spearman $\rho = -0.1345$ in Mumbai (positive in 25% of months; pooled block-bootstrap $\rho = 0.2176$, 95% CI [0.1951, 0.2501]) and mean within-month $\rho = 0.2436$ in Coimbatore (positive in 91.7% of months; pooled block-bootstrap $\rho = 0.5915$, 95% CI [0.5071, 0.6681]). Modest correlation is expected because ambient bioclimatic air temperature varies over broader atmospheric scales than surface radiometric skin temperature, which is heavily influenced by surface emissivity and micro-scale albedo.

### 6. Parametric Formulation of Compound Hazard Coupling ($\gamma$ and $q$)
The non-linear compound coupling mechanism ($ssi_{v2} = ssi_{lin} + \gamma \Omega (1 - ssi_{lin})$) utilizes a coupling intensity $\gamma = 0.30$ and an empirical joint-tail activation threshold $q = 0.90$. These are deliberate modeling selections rather than physical constants. Robustness sweeps in `results/sensitivity_summary.csv` demonstrate that spatial rankings are highly insensitive to these parameters (minimum hex-mean $\rho = 0.9988$ across $\gamma \in [0.1, 0.5]$ and minimum $\rho = 0.9989$ across $q \in \{0.75, 0.90\}$), confirming that spatial targeting is stable while absolute index levels and compound activation frequencies scale monotonically with the parameter choice.

### 7. Monthly-Aggregated Anomaly Flags
The anomaly flag designates observations exceeding the 90th percentile of the composite index distribution. Because the dominant variance drivers (heat, water, and pollution) have substantial seasonal components, anomaly flags tend to activate simultaneously across large metropolitan areas during acute seasonal stress periods (e.g., pre-monsoon heat and drought in May, or post-monsoon pollution peaks in December–January), rather than isolating isolated individual hexes in isolation.

### 8. Absence of Empirical Health and Economic Outcome Calibration
The composite SSI v2 is an environmental hazard exposure index, not an empirically calibrated damage or mortality function. No municipal hospital admission registers, all-cause excess mortality records, or documented infrastructure disruption datasets were available for calibration or end-to-end outcome verification. Validation is restricted to physically observable historical events (April–May 2020 national lockdown PM₂.₅ drop and March–April 2022 heatwave surge) and independent geospatial layer consistency.

### 9. Relative Quantile Risk Classification
The risk classification bands (Low, Moderate, High, Extreme) are partitioned according to empirical quartiles (25th, 50th, 75th percentiles) of the pooled reference city distribution. These boundaries reflect relative standing across the modeled metropolitan panel; they do not represent absolute physiological thresholds, toxicological safety limits, or statutory urban planning benchmarks.

### 10. Sample Size Constraints in Cross-City Ranking
With two reference cities (Mumbai and Coimbatore) currently scored under the unified v2 baseline parameters, cross-city comparative analysis (`results/crosscity.json`) confirms that city ordering is preserved across all four weighting schemes (Equal, EWM, CRITIC, and PCA). However, formal statistical rank correlation tests (e.g., Kendall's $\tau$ or Spearman's $\rho$ across cities) require a sample size of $N \ge 3$ cities and cannot be meaningfully computed on two locations. Cross-city comparisons are strictly descriptive.
