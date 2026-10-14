# SSI Validation Implementation Plan

## Comprehensive Validation Framework for the Compound Sustainability Stress Index

> **Target venue:** ICAMET 2026  
> **Study period:** 2020-01 → 2022-12 (36 months)  
> **Completed cities:** Mumbai (707 H3 hexes), Coimbatore (995 H3 hexes)  
> **H3 resolution:** 8 (~0.74 km² per hex)

---

## 0. Honest Assessment of Current Data State

> [!CAUTION]
> Before designing validation, you must acknowledge and address the following
> limitations discovered in the current pipeline output. Reviewers will catch
> these immediately.

### Critical Issues Found in Current Results

| Issue | Evidence | Impact on Validation |
|-------|----------|---------------------|
| **Socioeconomic data is uniform/synthetic** | `bpl_pct`, `slum_pct`, `elderly_pct`, `literacy_pct` each have **1 unique value** across all 707 Mumbai hexes (e.g., `bpl_pct = 0.18` everywhere). Source is labelled *"Synthetic (replace with Census 2011 / NFHS-5)"*. | `urban_vulnerability_idx` has **no real spatial variation** from socioeconomic inputs. Variation comes only from OSM building/road density proxy scaling. Cannot validate against Census data when Census data was never actually used. |
| **PM2.5 monthly seasonality is imposed, not observed** | Monthly PM2.5 is derived by multiplying an annual SEDAC raster by a fixed `INDIA_PM25_MONTHLY_INDEX` dictionary (hardcoded seasonality factors). Mumbai January PM2.5 = 232 µg/m³, which is unrealistically high for Mumbai (these factors are calibrated for north India / IGP). | The `pollution_idx` temporal pattern is **predetermined by the seasonality table**, not learned from data. Temporal validation against CPCB stations will only confirm that the imposed seasonality matches CPCB seasonality — this is circular. |
| **PM2.5 has almost no spatial variation** | Mumbai has only **3 unique PM2.5 values per month** across 707 hexes (the SEDAC raster is ~1 km, and the bbox captures only a few pixels). | Spatial validation of pollution hotspots within a city is impossible with this resolution. |
| **Heat/water stress z-score normalization compresses signal** | `heat_stress_idx` and `water_stress_idx` both have exactly the range [0.3075, 0.6925] with mean = 0.5000. The `[-3, +3] → [0, 1]` mapping means values cluster tightly around 0.5, with monthly means of heat/water stress being essentially **constant at 0.5**. | Temporal validation for heat/water is severely limited — the monthly mean is 0.5 every month. Only spatial variation within a month is captured (inter-hex differences from baseline). |
| **SSI variation is driven almost entirely by pollution_idx** | Monthly SSI varies from 0.48 (monsoon) to 0.54 (winter) — and this variation tracks `pollution_idx` almost perfectly. Heat, water, and vegetation contribute almost no temporal signal. | The compound SSI is effectively a pollution index with noise from the other four indicators. |
| **Only 2 cities completed** | Only Mumbai and Coimbatore have final panels. Delhi, Bengaluru, and Bikaner are configured but not run. | Cross-city validation is limited to 2 cities, both of which are in western/southern India. |

### What This Means for Your Paper

You **cannot** present the current results as fully validated. You must either:
1. **Fix the inputs first** (replace synthetic socioeconomic data, obtain real monthly PM2.5), then validate, OR  
2. **Be transparent** about these limitations in the paper and frame the validation as demonstrating the *framework's capability* rather than claiming validated results

**I strongly recommend Option 1** for ICAMET 2026 — it will significantly strengthen the paper.

---

## 1. Pre-Validation: Fix Data Inputs

> [!IMPORTANT]
> Complete these steps BEFORE running any validation. Without them, validation
> results will be misleading.

### 1.1 Replace Synthetic Socioeconomic Data

**Current state:** Single uniform values per city from `CITY_VULNERABILITY_PRIORS` dict.

**What to do:**

| Data Source | Variables | Resolution | Access |
|-------------|-----------|------------|--------|
| **Census 2011 Ward-level data** | BPL households, slum HH, population by age, literacy | Ward (~1-5 km²) | [censusindia.gov.in](https://censusindia.gov.in/census.website/data/census-tables) — free download |
| **NFHS-5 (2019-21) District Factsheets** | Multidimensional poverty, nutrition, health access | District | [rchiips.org/nfhs](http://rchiips.org/nfhs/) — free PDFs |
| **SECC 2011 (Socio-Economic Caste Census)** | BPL classification at village/ward level | Village/ward | Available through [data.gov.in](https://data.gov.in) |
| **NITI Aayog SDG India Index 2023-24** | Composite deprivation metrics | District | [sdgindiaindex.niti.gov.in](https://sdgindiaindex.niti.gov.in) |

**Implementation:**
```
1. Download Census 2011 Primary Census Abstract (PCA) tables for Mumbai
   and Coimbatore at ward level
2. Map wards to H3 cells using ward boundary shapefiles
   (available from Municipal Corporation GIS portals)
3. Compute ward-level: bpl_pct, slum_pct, elderly_pct, literacy_pct
4. Assign to H3 cells via spatial join (point-in-polygon or area-weighted)
5. Update vulnerability_ingest.py to read this instead of uniform values
```

**Effort estimate:** 2-3 days (data download + processing script)

### 1.2 Replace Imposed PM2.5 Seasonality

**Current state:** Annual SEDAC raster x hardcoded `INDIA_PM25_MONTHLY_INDEX` factors.

**What to do:**

| Source | Type | Resolution | Access |
|--------|------|------------|--------|
| **CPCB Continuous Ambient Air Quality Monitoring (CAAQMS)** | Observed hourly PM2.5 | Station-level | [app.cpcbccr.com](https://app.cpcbccr.com/ccr/#/caaqm-dashboard-all/caaqm-landing) — free |
| **OpenAQ** | Aggregated from CPCB + others | Station-level | [openaq.org](https://openaq.org/) — free API |
| **CAMS EAC4 Monthly Reanalysis** | Model-assimilated PM2.5 | ~0.75 deg | [ADS](https://ads.atmosphere.copernicus.eu) — free, requires registration |
| **MERRA-2 Aerosol** | AOD/PM2.5 estimate | ~0.5 x 0.625 deg | [GES DISC](https://disc.gsfc.nasa.gov/) — free |

**Recommended approach for your paper:**
```
1. Download CPCB hourly PM2.5 data for all monitoring stations in
   Mumbai and Coimbatore (2020-2022) using the CPCB CCR portal
2. Compute monthly station-level means
3. Interpolate to H3 grid using IDW (Inverse Distance Weighting) or
   Ordinary Kriging from station locations
4. This gives you REAL monthly PM2.5 with REAL spatial variation
5. BONUS: Keep the SEDAC-scaled version as a comparison
   -> "Station-interpolated vs SEDAC-scaled PM2.5"
```

**Effort estimate:** 3-4 days (CPCB data download is manual per station, but OpenAQ API can bulk-download)

### 1.3 Run Pipeline for All 5 Cities

After fixing inputs, run the full pipeline for Delhi, Bengaluru, and Bikaner (in addition to Mumbai and Coimbatore). This is essential for cross-city validation.

```bash
python run_pipeline.py --city delhi --phase all
python run_pipeline.py --city bengaluru --phase all
python run_pipeline.py --city bikaner --phase all
```

---

## 2. Validation Framework

After fixing the inputs above, implement the following validation tiers. They are ordered by importance and feasibility.

### Tier Structure

```
                     SSI VALIDATION
                          |
          +---------------+---------------+
          v               v               v
     TIER 1           TIER 2          TIER 3
   (Must-have)      (Should-have)   (Nice-to-have)
                          
  - Temporal         - Spatial        - Expert
    coherence          agreement        elicitation
  - Component        - Cross-city     - Health-impact
    plausibility       construct        correlation
  - Sensitivity        validity       - Lag analysis
    analysis         - External
  - Ablation           index
    study              comparison
```

---

## TIER 1: Must-Have Validations (Essential for the Paper)

### 2.1 Temporal Coherence Validation

**Goal:** Show that SSI and its components respond correctly to known seasonal patterns.

**Method:**
1. Plot monthly mean SSI and each sub-index for each city (2020-2022)
2. Overlay known climatological stress periods
3. Compute Spearman rank correlation between monthly SSI and independent reference time series

**Reference data (freely available):**

| City | Reference Variable | Source | Expected Pattern |
|------|-------------------|--------|-----------------|
| Mumbai | Monthly temperature | IMD gridded / ERA5 (already in your data) | Peak pre-monsoon (Apr-May) |
| Mumbai | Monthly rainfall | IMD gridded / ERA5 (already in your data) | Monsoon Jun-Sep -> low water stress |
| Mumbai | Monthly PM2.5 | **CPCB station data** (must download) | Peak Nov-Feb |
| Coimbatore | Monthly temperature | IMD / ERA5 | Peak Apr-May |
| Coimbatore | Monthly rainfall | IMD / ERA5 | Northeast monsoon Oct-Dec |
| Delhi | Monthly PM2.5 | CPCB | Severe Nov-Jan |
| Delhi | Monthly temperature | ERA5 | Extreme May-Jun |
| Bikaner | Monthly temperature | ERA5 | Extreme May-Jun (>45 C) |
| Bikaner | Monthly soil moisture | ERA5 | Persistently low (arid) |

**Statistical test:**

```
rho_temporal = Spearman(SSI_t, Reference_t)    t = 1, ..., 36
```

Report: rho, p-value, 95% CI (use `scipy.stats.spearmanr`)

**What to present in the paper:**
- Figure: 36-month time series (SSI vs reference) for each city
- Table: Spearman rho for each component vs its reference variable

> [!WARNING]
> With the current data, heat_stress_idx and water_stress_idx monthly means are
> ~0.5 every month (the z-score normalization centres everything). You will get
> near-zero temporal correlation for these components unless you fix the
> normalization or use a different aggregation (e.g., 90th percentile per month
> instead of mean).

**Suggested fix for temporal signal:** Instead of monthly mean, use:
- Monthly **90th percentile** of each indicator (captures spatial extremes)
- Monthly **anomaly count** (fraction of hexes with indicator > 0.6)
- Monthly **max** of the indicator

**Implementation code structure:**
```python
# src/validation/temporal_coherence.py

def compute_temporal_correlation(
    panel: pd.DataFrame,
    indicator_col: str,
    reference_col: str,  # or external reference Series
    aggregation: str = "p90",  # "mean", "p90", "max", "anomaly_frac"
) -> dict:
    """
    Returns: {
        'spearman_rho': float,
        'spearman_pvalue': float,
        'pearson_r': float,
        'n_months': int,
    }
    """
```

### 2.2 Component-Level Plausibility Check

**Goal:** Verify that each of the 5 sub-indices independently makes physical sense before validating the composite SSI.

**Method for each indicator:**

#### Heat Stress Index
| Check | How | Expected Outcome |
|-------|-----|-----------------|
| Seasonal cycle | Plot monthly mean | Peak Apr-May (pre-monsoon), trough Dec-Jan |
| Spatial pattern | Map high-heat hexes | Inland/concrete areas > coastal/green areas |
| Against raw temperature | Scatter plot: `heat_stress_idx` vs `temp_mean_c` | Strong positive correlation (Pearson r > 0.7) |
| Against Heat Index formula | Compare your computed HI to NWS lookup tables | Exact match for known (T, RH) pairs |

#### Water Stress Index
| Check | How | Expected Outcome |
|-------|-----|-----------------|
| Seasonal cycle | Plot monthly mean | Peak pre-monsoon (Mar-May), trough monsoon (Jul-Sep) |
| Against precipitation | Scatter: `water_stress_idx` vs `precip_sum_mm` | Negative correlation |
| Against soil moisture | Scatter: `water_stress_idx` vs `soil_moisture` | Negative correlation |
| SWD vs SPEI comparison | If possible, compute true SPEI-3 from same P/T data | High correlation (rho > 0.8) |

#### Pollution Index
| Check | How | Expected Outcome |
|-------|-----|-----------------|
| Seasonal cycle | Plot monthly mean | Peak winter (Nov-Feb) for north India |
| Against CPCB observations | Scatter: `pollution_idx` vs CPCB monthly PM2.5 | rho > 0.85 expected (since both derive from same base signal) |
| WHO threshold crossing | Flag months where PM2.5 > 15 ug/m3 | Most Indian months should exceed this |

#### Vegetation Index
| Check | How | Expected Outcome |
|-------|-----|-----------------|
| Seasonal cycle | Plot monthly mean NDVI | Peak post-monsoon (Oct-Nov), trough pre-monsoon (Apr-May) |
| Against MODIS NDVI | Compare Sentinel-2 NDVI with MODIS MOD13Q1 monthly | rho > 0.8 |
| Known green vs built hexes | Compare NDVI for hexes with `green_space_fraction > 0.3` vs `< 0.05` | Green hexes should have higher NDVI and lower vegetation stress |

#### Urban Vulnerability Index
| Check | How | Expected Outcome |
|-------|-----|-----------------|
| Spatial pattern | Map high-vulnerability hexes | Correlate with known informal settlements / old city areas |
| Against OSM density | Scatter: `urban_vulnerability_idx` vs `building_density` | Positive correlation |
| Static consistency | Check values don't change month-to-month for same hex | All months identical (expected for static indicator) |

**Implementation:**
```python
# src/validation/component_plausibility.py

def validate_indicator_against_raw(
    panel: pd.DataFrame,
    indicator_col: str,
    raw_col: str,
    expected_direction: str = "positive",  # or "negative"
) -> dict:
    """Compute correlation and report plausibility."""
```

### 2.3 Sensitivity Analysis

**Goal:** Show that SSI rankings are robust to parameter choices.

**Parameters to vary:**

| Parameter | Baseline | Test Values | Description |
|-----------|----------|-------------|-------------|
| gamma | 0.5 | 0, 0.25, 0.75, 1.0 | Compound interaction scaling |
| kappa | 1.0 | 0, 0.5, 1.5 | City-rank adjustment sensitivity |
| Normalization | z-score | min-max | Indicator normalization method |
| PCA vs Equal | PCA | Equal weights | Weighting scheme |
| H3 resolution | 8 | 7, 9 | Spatial granularity |
| Anomaly threshold | 90th pct | 85th, 95th pct | Anomaly classification |

**Protocol:**
1. For each parameter configuration, recompute SSI for the same city panel
2. Compare resulting SSI rankings to the baseline using Spearman rho
3. Compute rank displacement: how many hexes change SSI band?

**Statistical output (table for paper):**

```
rho_config = Spearman(SSI_baseline, SSI_config)
```

| Configuration | Spearman rho vs Baseline | Band Agreement (%) | Interpretation |
|---------------|------------------------|--------------------|-|
| Baseline (gamma=0.5, kappa=1.0, PCA, z-score, res-8) | 1.000 | 100% | Reference |
| gamma = 0 (no interactions) | ? | ? | Interaction importance |
| gamma = 0.25 | ? | ? | |
| gamma = 1.0 | ? | ? | |
| kappa = 0 (no city adjustment) | ? | ? | City adjustment importance |
| Equal weights | ? | ? | PCA necessity |
| Min-max normalization | ? | ? | Normalization sensitivity |

**If rho > 0.85 across all configurations** -> model is robust  
**If rho < 0.70 for some configuration** -> investigate which parameter drives instability

**Implementation:**
```python
# src/validation/sensitivity.py

def run_sensitivity_analysis(
    panel: pd.DataFrame,
    city: str,
    parameter_grid: dict,  # {"gamma": [0, 0.25, 0.5, 0.75, 1.0], ...}
) -> pd.DataFrame:
    """
    Returns DataFrame with columns:
        config_name, spearman_rho, band_agreement_pct, mean_rank_shift
    """
```

### 2.4 Ablation Study (Linear vs Compound SSI)

**Goal:** Demonstrate that compound interaction terms add value over a purely linear combination.

**Your code already computes both:**
- `ssi_linear` — weighted sum only
- `ssi_value` — weighted sum + gamma x interaction terms

**Protocol:**
1. For each city, compute Spearman rho between `ssi_linear` and `ssi_value`
2. Identify hexes where the two diverge most (rank difference > 10th percentile)
3. Check whether divergent hexes correspond to locations with known compound stress

**Key question:** Do areas where multiple stressors co-occur (e.g., hot + dry + polluted) get higher SSI_compound than SSI_linear?

**Statistical tests:**
```
rho(ssi_linear, ssi_value) -> if very high (>0.98), interaction terms
                               have negligible effect on rankings
                            -> if moderate (0.80-0.95), interactions
                               meaningfully re-rank locations
```

**If interaction terms don't change rankings:** This is still a valid finding — report it as "the linear model is sufficient for this study period." But investigate whether this is because gamma is too small or because indicators are not actually correlated at the hex level.

**What to present:**
- Scatter plot: `ssi_linear` vs `ssi_value` (colour by city)
- Table: rho between the two, per city
- Difference map: hexes where compound SSI > linear SSI by > 1 band
- Correlation matrix of the 5 indicators (to check if interactions are even present)

**Implementation:**
```python
# src/validation/ablation.py

def compare_linear_vs_compound(
    panel: pd.DataFrame,
) -> dict:
    """
    Returns: {
        'spearman_rho': float,
        'mean_absolute_difference': float,
        'band_change_fraction': float,
        'divergent_hexes': pd.DataFrame,  # top 5% most different
    }
    """
```

---

## TIER 2: Should-Have Validations (Strengthen the Paper)

### 2.5 Spatial Agreement Validation

**Goal:** Check whether high-SSI hexes overlap with independently known vulnerable areas.

**Reference datasets (freely available):**

| Reference Layer | Source | Format | Access |
|----------------|--------|--------|--------|
| **Slum boundaries** | Tata Institute / NSDF / municipal GIS | Shapefile | Some cities via [data.gov.in](https://data.gov.in) or academic request |
| **Flood-prone zones** | NDMA / SDMA / CWC | Shapefile | [ndma.gov.in](https://ndma.gov.in) |
| **Urban heat island maps** | MOSDAC / ISRO | Raster | [mosdac.gov.in](https://www.mosdac.gov.in/) |
| **CPCB air quality stations** | CPCB | Point locations | [app.cpcbccr.com](https://app.cpcbccr.com) |
| **Urban green spaces** | OSM / Google Open Buildings | Polygon | Already in your pipeline |

**Method:**
1. Classify hexes as "High SSI" if `ssi_value >= 0.50` (High + Extreme bands)
2. Overlay with reference vulnerability layer
3. Compute spatial agreement:

```
Spatial Agreement = (High-SSI hexes AND Reference vulnerable hexes) / Total High-SSI hexes * 100
```

Also compute the reverse:

```
Detection Rate = (High-SSI hexes AND Reference vulnerable hexes) / Total Reference vulnerable hexes * 100
```

**Practical note:** Getting spatially resolved reference data for Indian cities is challenging. **Prioritize OSM-derived validation** (you already have OSM data) and CPCB station locations.

**Minimum feasible approach:**
```
1. Download CPCB station coordinates for Mumbai/Coimbatore
2. For each station, find the H3 hex it falls in
3. Compare station monthly PM2.5 with the hex's pollution_idx
   -> point-to-hex validation
4. Repeat for IMD weather stations if available
```

### 2.6 Cross-City Construct Validity

**Goal:** Confirm that SSI behaves according to design across different city types.

**Expected patterns (from your config city_weights):**

| City | Expected Dominant Stress | Check |
|------|------------------------|-------|
| Delhi | Pollution + Heat | `pollution_idx` and `heat_stress_idx` should have highest PCA weights |
| Mumbai | Water + Urban vulnerability | `water_stress_idx` and `urban_vulnerability_idx` should dominate |
| Bengaluru | Water | `water_stress_idx` should have highest mean |
| Bikaner | Heat + Water (arid) | `heat_stress_idx` and `water_stress_idx` should dominate; `vegetation_idx` high |
| Coimbatore | Heat + Water (moderate) | Balanced profile |

**Validation:**
```
For each city:
  1. Rank the 5 indicator means
  2. Compare with the expected ranking above
  3. Report Kendall's tau between expected and observed rank orderings
```

**If Bikaner has high heat and water stress, while Delhi has high pollution** -> your model has construct validity  
**If all cities look the same** -> the model is not discriminating between city contexts

**Implementation:**
```python
# src/validation/cross_city.py

def validate_construct_validity(
    city_panels: dict[str, pd.DataFrame],  # {city: panel_df}
    expected_rankings: dict[str, list[str]],  # {city: [indicator ranked by importance]}
) -> pd.DataFrame:
    """Compare observed indicator rankings with expected ones per city."""
```

### 2.7 Comparison with Established Indices

**Goal:** Correlate SSI components with independently computed standard indices.

| SSI Component | Compare With | How to Compute | Source |
|---------------|-------------|----------------|--------|
| `water_stress_idx` | **SPEI-3** (Standardized Precipitation Evapotranspiration Index) | `spei` Python package or `climate_indices` package from NOAA, using the same ERA5 P/T data | Self-computed from ERA5 |
| `heat_stress_idx` | **WBGT** (Wet-Bulb Globe Temperature) or **UTCI** | `pythermalcomfort` package using ERA5 T/RH/wind/radiation | Self-computed from ERA5 |
| `pollution_idx` | **AQI** (Air Quality Index) | Indian NAQI formula from PM2.5 breakpoints | Self-computed from PM2.5 column |
| `vegetation_idx` | **VCI** (Vegetation Condition Index) | `VCI = (NDVI - NDVI_min) / (NDVI_max - NDVI_min)` | Self-computed from NDVI column |

**Why this works:** You're using the SAME raw data but a DIFFERENT formula to derive the reference index. If your indicator correlates well with the established index, it demonstrates that your approach captures the same signal as the established method.

**Statistical test:**

```
rho = Spearman(SSI_component, EstablishedIndex)
```

**Implementation:**
```python
# src/validation/external_indices.py

def compute_spei3(panel: pd.DataFrame) -> pd.Series:
    """Compute SPEI-3 from precip_sum_mm and temp_mean_c columns."""

def compute_aqi_from_pm25(panel: pd.DataFrame) -> pd.Series:
    """Compute Indian NAQI from pm25 column."""

def compute_vci(panel: pd.DataFrame) -> pd.Series:
    """Compute Vegetation Condition Index from ndvi column."""
```

### 2.8 Weight Validation (PCA vs Equal vs Expert)

**Goal:** Show that SSI rankings are not an artefact of the weighting method.

**Protocol:**
1. Compute SSI with **PCA weights** (current default)
2. Compute SSI with **equal weights** (0.2 each)
3. Compute SSI with **expert-defined weights** (from `config.yml` city_weights)
4. Compute Spearman rho between all three rankings

**Present as:**

| Comparison | Spearman rho |
|------------|-----------|
| PCA vs Equal | ? |
| PCA vs City-Adapted | ? |
| Equal vs City-Adapted | ? |

**If rho > 0.90 for all pairs:** The ranking is robust to weight choice — PCA adds refinement but doesn't fundamentally change the picture.

---

## TIER 3: Nice-to-Have Validations (Bonus for Strong Paper)

### 2.9 Known Event Detection

**Goal:** Show that SSI correctly identifies documented stress events.

**Known events for validation (publicly documented):**

| Event | City | Period | Expected SSI Response |
|-------|------|--------|----------------------|
| COVID-19 lockdown | All | Mar-May 2020 | PM2.5 drop -> lower SSI (pollution component) |
| Cyclone Tauktae | Mumbai | May 2021 | Rainfall spike -> water balance shift |
| Delhi winter smog | Delhi | Nov 2021, Nov 2022 | PM2.5 > 300 ug/m3 -> extreme pollution_idx |
| 2020 monsoon (above-normal) | Mumbai | Jun-Sep 2020 | High rainfall -> low water stress |
| Heat wave 2022 | Delhi, Bikaner | Mar-May 2022 | Temperature > 45 C -> high heat stress |
| Bengaluru water crisis | Bengaluru | 2022 | Groundwater depletion -> high water stress |

**Event Detection Rate (EDR):**

```
EDR = Events where SSI correctly elevates / Total known events
```

**"Correctly elevates"** = the relevant SSI component exceeds its 75th percentile during the event month.

### 2.10 Health-Impact Association (If Data Available)

**Goal:** Check whether high-SSI areas/months correspond to health outcomes.

**Possible data sources:**

| Data | Source | Availability |
|------|--------|-------------|
| Heat-related mortality | Municipal death records | Difficult to obtain |
| Respiratory illness admissions | HMIS (Health Management Information System) | [hmis.nhp.gov.in](https://hmis.nhp.gov.in/) — district-level monthly |
| Dengue/vector-borne disease | NVBDCP | [nvbdcp.gov.in](https://nvbdcp.gov.in) |

**Method:** Poisson regression or simple Spearman correlation between monthly SSI and monthly health outcome counts.

> [!NOTE]
> You do NOT need to claim causation. Simply demonstrating **association**
> (e.g., "months with higher SSI correspond to more respiratory admissions")
> is sufficient for an engineering conference paper.

### 2.11 Lag Correlation Analysis

**Goal:** Test whether SSI leads, lags, or is contemporaneous with reference variables.

**Method:** Cross-correlation function (CCF) with lags from -3 to +3 months.

```python
from scipy.stats import spearmanr

def lag_correlation(ssi_series, reference_series, max_lag=3):
    results = {}
    for lag in range(-max_lag, max_lag + 1):
        if lag > 0:
            rho, p = spearmanr(ssi_series[:-lag], reference_series[lag:])
        elif lag < 0:
            rho, p = spearmanr(ssi_series[-lag:], reference_series[:lag])
        else:
            rho, p = spearmanr(ssi_series, reference_series)
        results[lag] = {'rho': rho, 'p_value': p}
    return results
```

**If SSI leads health outcomes by 1 month** -> evidence of predictive utility.

---

## 3. Implementation Roadmap

### File Structure

```
src/validation/
    __init__.py
    temporal_coherence.py       # Tier 1: Section 2.1
    component_plausibility.py   # Tier 1: Section 2.2
    sensitivity.py              # Tier 1: Section 2.3
    ablation.py                 # Tier 1: Section 2.4
    spatial_agreement.py        # Tier 2: Section 2.5
    cross_city.py               # Tier 2: Section 2.6
    external_indices.py         # Tier 2: Section 2.7
    weight_validation.py        # Tier 2: Section 2.8
    event_detection.py          # Tier 3: Section 2.9
    health_association.py       # Tier 3: Section 2.10
    utils.py                    # Shared helpers (plotting, statistics)

run_validation.py               # CLI runner for all validation scripts
```

### Phase Plan

```
Phase 1: Fix Inputs (Week 1)
    1a. Download Census 2011 ward-level data for Mumbai + Coimbatore
    1b. Download CPCB PM2.5 station data (2020-2022)
    1c. Update vulnerability_ingest.py for real Census data
    1d. Update pm25_ingest.py to use station interpolation
    1e. Re-run pipeline for all 5 cities

Phase 2: Tier 1 Validation (Week 2)
    2a. Temporal coherence analysis
    2b. Component plausibility checks
    2c. Sensitivity analysis (gamma, kappa, weights, normalization)
    2d. Ablation study (linear vs compound)

Phase 3: Tier 2 Validation (Week 3)
    3a. Spatial agreement (CPCB stations, known hotspots)
    3b. Cross-city construct validity
    3c. External index comparison (SPEI, AQI, VCI)
    3d. Weight validation

Phase 4: Paper Writing (Week 4)
    4a. Compile validation results into tables and figures
    4b. Write validation section of the paper
    4c. Prepare supplementary material
```

---

## 4. What to Report in the Paper

### Required Tables

**Table 1: Data Sources and Quality**

| Data Layer | Source | Temporal Res. | Spatial Res. | Coverage | Known Limitations |
|------------|--------|---------------|--------------|----------|-------------------|
| Temperature, humidity, precipitation, wind, radiation, soil moisture | ERA5 Reanalysis | Monthly | ~11 km -> H3 res-8 via bilinear interpolation | Complete | Coarse resolution; no urban heat island effect |
| NDVI | Sentinel-2 L2A | Monthly composite | 10 m -> H3 agg | ~85% (cloud gaps) | Cloud contamination in monsoon months |
| LST | MODIS MOD11A2 | 8-day -> monthly | 1 km -> H3 agg | ~90% | Gap-filled with ERA5 T + 5 C proxy |
| PM2.5 | CPCB stations (interpolated) | Monthly | Station -> H3 via IDW | Depends on station density | Sparse stations in some cities |
| Building/road density, green space | OpenStreetMap | Static (2024) | Polygon -> H3 | Complete | OSM completeness varies by area |
| BPL, slum, elderly, literacy | Census 2011 | Static | Ward -> H3 | Complete | 2011 data (10+ years old) |

**Table 2: Sensitivity Analysis Results**
(As described in Section 2.3)

**Table 3: Component Validation Correlations**

| Component | Reference | Spearman rho | p-value | n |
|-----------|-----------|-----------|---------|---|
| `heat_stress_idx` | ERA5 temp_mean_c | ? | ? | ? |
| `water_stress_idx` | SPEI-3 | ? | ? | ? |
| `pollution_idx` | CPCB PM2.5 | ? | ? | ? |
| `vegetation_idx` | MODIS VCI | ? | ? | ? |

**Table 4: Cross-City Construct Validity**
(As described in Section 2.6)

### Required Figures

1. **36-month time series** — SSI + 5 components for each city (line plots)
2. **SSI spatial map** — H3 choropleth for each city, peak stress month
3. **Sensitivity spider plot** — rho vs baseline for each parameter variation
4. **Linear vs Compound scatter** — `ssi_linear` vs `ssi_value` coloured by archetype
5. **Indicator correlation matrix** — heatmap of inter-indicator Pearson r (justifies interaction terms)
6. **Monthly indicator profiles** — grouped bar chart of indicator means by month and city

---

## 5. Statistical Methods Reference

### Tests to Use

| Purpose | Test | When to Use | Python Function |
|---------|------|-------------|-----------------|
| Rank correlation | **Spearman rho** | SSI vs reference rankings | `scipy.stats.spearmanr` |
| Linear correlation | **Pearson r** | Indicator vs raw variable | `scipy.stats.pearsonr` |
| Rank agreement | **Kendall tau** | Cross-city rank order validation | `scipy.stats.kendalltau` |
| Distribution comparison | **KS test** | SSI distribution across configurations | `scipy.stats.ks_2samp` |
| Confidence intervals | **Bootstrap** | CI for Spearman rho | `scipy.stats.bootstrap` |
| Band agreement | **Cohen's kappa** | SSI band classification agreement | `sklearn.metrics.cohen_kappa_score` |

### Reporting Standards

For each validation test, report:
- Test statistic value (rho, r, tau, or kappa)
- p-value
- Sample size (n)
- 95% confidence interval (via bootstrap with 1000 resamples)
- Effect size interpretation (e.g., rho > 0.7 = strong, 0.4-0.7 = moderate)

---

## 6. Honest Limitations Section for the Paper

Even after validation, acknowledge these in your paper:

1. **Temporal resolution:** Monthly aggregation smooths sub-monthly events (e.g., a 3-day heatwave disappears in a monthly mean)
2. **ERA5 spatial coarseness:** ~11 km ERA5 grid cannot resolve intra-urban microclimates; H3 res-8 hexes within the same ERA5 pixel receive identical climate values
3. **NDVI cloud gaps:** Monsoon months have fewer clear-sky observations; gap-filled composites may underestimate vegetation stress during the wettest (and greenest) period
4. **Census data age:** 2011 Census is 10+ years old; actual socioeconomic conditions may have changed significantly
5. **No ground-truth SSI:** There is no single "correct" SSI value; all validation is indirect comparison against proxy variables and domain knowledge
6. **Short study period:** 3 years (2020-2022) includes COVID-19 anomalies that may not represent normal stress patterns
7. **PCA on 3-year data:** PCA weights derived from a 36-month window may not generalise to longer periods or different climate phases

---

## 7. Minimum Viable Validation (If Time is Limited)

If you cannot complete all tiers before the deadline, this is the **absolute minimum** for a credible paper:

> [!IMPORTANT]
> **Do at least these 4 things:**
> 
> 1. **Temporal coherence** (Section 2.1) — plot monthly SSI vs reference
>    for at least 2 cities
> 2. **Sensitivity analysis** (Section 2.3) — vary gamma and weighting scheme,
>    show Spearman rho > 0.85
> 3. **Ablation study** (Section 2.4) — compare `ssi_linear` vs `ssi_value`
> 4. **Acknowledge limitations** (Section 6) — be transparent about synthetic
>    socioeconomic data and imposed PM2.5 seasonality
> 
> This takes approximately 1 week including coding and figure generation.

---

## 8. Key References for Validation Methods

These are peer-reviewed references you can cite to justify your validation approach:

| Method | Reference |
|--------|-----------|
| Composite index validation framework | OECD (2008). *Handbook on Constructing Composite Indicators*. JRC-OECD. |
| Sensitivity analysis for indices | Saisana, M., Saltelli, A., & Tarantola, S. (2005). *Uncertainty and sensitivity analysis as tools for the quality assessment of composite indicators*. J. Royal Statistical Society A, 168(2), 307-323. |
| Spearman rank correlation | Spearman, C. (1904). *The proof and measurement of association between two things*. Amer. J. Psychology, 15(1), 72-101. |
| Social Vulnerability Index validation | Cutter, S.L., Boruff, B.J., & Shirley, W.L. (2003). *Social vulnerability to environmental hazards*. Social Science Quarterly, 84(2), 242-261. |
| SPEI methodology | Vicente-Serrano, S.M. et al. (2010). *A Multiscalar Drought Index Sensitive to Global Warming: The SPEI*. J. Climate, 23, 1696-1718. |
| Compound event analysis | Zscheischler, J. et al. (2018). *Future climate risk from compound events*. Nature Climate Change, 8(6), 469-477. |
| Index robustness testing | Greco, S. et al. (2019). *On the methodological framework of composite indices*. Social Indicators Research, 141(1), 61-78. |
