# SSI Data Sources, Formulas & Parameter Deep Analysis

> This document provides a rigorous, citable accounting of every data source, every parameter extracted, every formula applied, the approximate data volumes, and whether 3 years of data is sufficient — for all 5 sub-indexes and the final Compound SSI.

---

## Architecture Overview

```
4 cities × ~2,500 H3 hexes/city × 36 months (3 years) = ~360,000 observation rows
Each row: 1 hex, 1 month, ~20 raw variables → 5 sub-indexes → 1 SSI score
```

---

## Index 1: Heat Stress Index

### Data Source: ERA5 Reanalysis (ECMWF/Copernicus)

| Parameter | ERA5 Variable | Unit | Aggregation |
|:---|:---|:---|:---|
| 2m Air Temperature | `t2m` | K → °C | Monthly mean |
| 2m Dewpoint Temperature | `d2m` | K → °C | Monthly mean |

**Why ERA5?**
- ERA5 is the gold standard global reanalysis dataset produced by ECMWF under the Copernicus Climate Change Service (C3S).
- It provides hourly gridded climate variables at **0.25° (~31 km)** resolution globally, from 1940 to present.
- We request it at **0.1° (~11 km)** resolution (ERA5 dynamically interpolates).
- It is **freely available** via the CDS API with a free Copernicus account.
- No other open dataset provides this combination of temporal coverage, spatial resolution, and variable breadth for climate reanalysis.
- **Source**: Hersbach, H. et al. (2020). "The ERA5 global reanalysis." *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999–2049. DOI: [10.1002/qj.3803](https://doi.org/10.1002/qj.3803)

### Data Source: MODIS Land Surface Temperature (NASA/USGS)

| Parameter | Product | Unit | Resolution |
|:---|:---|:---|:---|
| Land Surface Temperature (daytime) | MOD11A2 (8-day composite) | K → °C | 1 km |

**Why MODIS LST?**
- Air temperature (ERA5) measures atmospheric heat. LST measures the actual **skin temperature of the urban surface** — asphalt, rooftops, bare soil.
- This captures the **Urban Heat Island (UHI)** effect that ERA5 at 11 km resolution cannot resolve within a city.
- MODIS MOD11A2 provides 8-day composites since 2000, accessed freely via **Microsoft Planetary Computer STAC**.
- **Source**: Wan, Z. (2014). "New refinements and validation of the collection-6 MODIS land-surface temperature/emissivity product." *Remote Sensing of Environment*, 140, 36–45.

### Formula Chain

**Step 1 — Relative Humidity** (August-Roche-Magnus approximation):

```
RH = 100 × exp(17.625 × Td / (243.04 + Td)) / exp(17.625 × T / (243.04 + T))
```

- **Source**: Alduchov, O.A. & Eskridge, R.E. (1996). "Improved Magnus Form Approximation of Saturation Vapor Pressure." *Journal of Applied Meteorology*, 35(4), 601–609. DOI: [10.1175/1520-0450(1996)035<0601:IMFAOS>2.0.CO;2](https://doi.org/10.1175/1520-0450(1996)035%3C0601:IMFAOS%3E2.0.CO;2)

**Step 2 — Heat Index** (Rothfusz regression, US NWS formulation):

```
HI = −8.78469 + 1.61139411×T + 2.338549×RH − 0.14611605×T×RH
     − 0.01230809×T² − 0.01642482×RH² + 0.002211732×T²×RH
     + 0.00072546×T×RH² − 0.000003582×T²×RH²
```

Valid when T > 26°C and RH > 40%. Below that, HI = T (no amplification).

- **Source**: Rothfusz, L.P. (1990). "The Heat Index Equation (or, More Than You Ever Wanted to Know About Heat Index)." *NWS Technical Attachment SR 90-23*, NWS Southern Region, Fort Worth, TX.
- **Why this formula?** It is the internationally adopted standard for human-perceived heat danger. Used by NOAA, NWS, IMD (India Meteorological Department), and WMO for heat-wave warnings. It captures the non-linear amplification of humidity on perceived temperature.

**Step 3 — Composite blending with LST** (PCA-weighted):

```
Heat_raw = w_HI × HI + w_LST × LST
```

Where `w_HI` and `w_LST` are derived from PC1 loadings of a PCA on [HI, LST]. Fallback: 0.7 / 0.3.

**Step 4 — Baseline normalization**:

```
heat_stress_idx = max(0, (Heat_raw − μ_baseline) / σ_baseline)
```

Baseline = per-hex, per-calendar-month mean and std from the first N years.

### Approximate Data Size (per city, 3 years)

| Dataset | Per Month | 36 Months |
|:---|:---|:---|
| ERA5 NetCDF (8 vars, 0.1° grid) | ~2–5 MB | ~70–180 MB |
| MODIS LST GeoTIFF (1 km, city bbox) | ~0.5–2 MB | ~18–72 MB |

---

## Index 2: Water Stress Index

### Data Source: ERA5 Reanalysis (same download as Heat Stress)

| Parameter | ERA5 Variable | Unit | Aggregation |
|:---|:---|:---|:---|
| Total Precipitation | `tp` | m → mm | Monthly sum |
| 2m Temperature (for PET) | `t2m` | K → °C | Monthly mean |
| Volumetric Soil Water Layer 1 | `swvl1` | m³/m³ | Monthly mean |
| Volumetric Soil Water Layer 2 | `swvl2` | m³/m³ | Monthly mean |

**Why these parameters?**
- Precipitation and soil moisture together capture **both atmospheric water supply and ground water availability**.
- Soil moisture layers 1 (0–7 cm) and 2 (7–28 cm) represent root-zone moisture relevant for vegetation and urban drainage capacity.
- All come from the **same ERA5 NetCDF download** — no additional data cost.

### Formula Chain

**Primary method — SPEI (Standardised Precipitation-Evapotranspiration Index)**:

**Step 1 — Thornthwaite PET** (Potential Evapotranspiration):

```
PET = 16 × (10 × T / I)^a   (mm/month, adjusted for day length)
```

Where:
- `I` = annual heat index = Σ(T_monthly / 5)^1.514 over 12 months
- `a` = 6.75×10⁻⁷ × I³ − 7.71×10⁻⁵ × I² + 0.01792 × I + 0.49239
- Day-length adjustment via solar declination and latitude

- **Source**: Thornthwaite, C.W. (1948). "An Approach toward a Rational Classification of Climate." *Geographical Review*, 38(1), 55–94.
- **Why Thornthwaite?** It requires only temperature and latitude (both available from ERA5 and H3 coordinates). It is the standard PET method used in SPEI computation when full radiation/wind data is not being directly consumed for PET. More complex methods (Penman-Monteith) require additional variables that would add complexity without proportional accuracy gain for a monthly urban stress index.

**Step 2 — Climatic Water Deficit**:

```
D = P − PET   (mm/month)
```

**Step 3 — 3-month rolling sum** (SPEI-3 equivalent):

```
D_rolled = rolling_sum(D, window=3 months, per hex)
```

**Step 4 — Baseline z-score normalization**:

```
water_stress_idx = max(0, −(D_rolled − μ_baseline) / σ_baseline)
```

Inverted so that drier conditions (lower D) produce higher stress.

- **Source**: Vicente-Serrano, S.M. et al. (2010). "A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index." *Journal of Climate*, 23(7), 1696–1718. DOI: [10.1175/2009JCLI2909.1](https://doi.org/10.1175/2009JCLI2909.1)
- **Why SPEI over SPI?** SPI (Standardised Precipitation Index) only uses precipitation. SPEI adds evapotranspiration demand, making it sensitive to warming-driven drought — critical for Indian cities where rising temperatures increase water demand even if rainfall is stable.

**Fallback method** (when PET cannot be computed): Weighted blend of precipitation deficit z-score (60%) and soil moisture deficit below 25th percentile (40%).

### Approximate Data Size

No additional download — uses the same ERA5 NetCDF files as Heat Stress.

---

## Index 3: Pollution Exposure Index

### Data Source: NASA SEDAC PM2.5 Annual Mean

| Parameter | Product | Unit | Resolution |
|:---|:---|:---|:---|
| Annual mean PM2.5 concentration | SEDAC Global Annual PM2.5 (V5.GL.04) | µg/m³ | ~1 km (~0.01°) |

**Why SEDAC?**
- NASA SEDAC (Socioeconomic Data and Applications Center) provides the most widely cited, peer-reviewed, satellite-derived annual mean PM2.5 dataset.
- It fuses satellite Aerosol Optical Depth (AOD) from MODIS/MISR/SeaWiFS with chemical transport model simulations (GEOS-Chem), calibrated by ground-based PM2.5 monitors.
- Available from 2001–2022, freely downloadable (requires free EarthData login).
- **Source**: van Donkelaar, A. et al. (2021). "Monthly Global Estimates of Fine Particulate Matter and Their Uncertainty." *Environmental Science & Technology*, 55(22), 15287–15300. DOI: [10.1021/acs.est.1c05309](https://doi.org/10.1021/acs.est.1c05309)

**Monthly derivation**: Since SEDAC provides annual means, monthly values are derived by scaling with India-specific seasonality indices based on CPCB (Central Pollution Control Board) observational climatology:

| Month | Seasonality Factor | Rationale |
|:---|:---|:---|
| Jan | 1.65 | Winter inversion + fog |
| Jun–Aug | 0.60–0.70 | Monsoon washout |
| Nov–Dec | 1.45–1.70 | Stubble burning + winter |

> [!IMPORTANT]
> This is the weakest data source in the pipeline. The seasonality factors are static approximations. For a production system, switching to **Copernicus CAMS** (real monthly reanalysis PM2.5) or **Sentinel-5P TROPOMI** (real monthly NO₂/AOD) would be a significant upgrade. However, for a proof-of-concept with 4 cities, the SEDAC approach is defensible because the annual spatial pattern (which hexes are more polluted) is the primary signal, and the seasonality modulation captures the dominant first-order monthly variation.

### Formula Chain

**Step 1 — WHO exceedance** (absolute health threshold):

```
exceedance = max(0, (PM2.5 − 15) / 15)
```

Where 15 µg/m³ is the WHO 2021 annual guideline value.

- **Source**: WHO (2021). "WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide." ISBN 978-92-4-003422-8.

**Step 2 — Temporal anomaly** (relative to city baseline):

```
temporal_z = max(0, (PM2.5 − μ_baseline) / σ_baseline)
```

**Step 3 — Composite**:

```
pollution_idx = 0.5 × normalize(exceedance) + 0.5 × temporal_z
```

**Why this dual approach?** Pure z-score would make a city with universally terrible air quality (e.g., Delhi at 100+ µg/m³ year-round) show "no stress" because it's always bad. The WHO exceedance component ensures that absolute health danger is always captured, while the temporal z-score captures anomalous spikes (e.g., Diwali, stubble burning season).

### Approximate Data Size

| Dataset | Per Year | 3 Years |
|:---|:---|:---|
| SEDAC annual GeoTIFF (global, ~1 km) | ~500 MB (global); ~2–5 MB clipped to city | ~6–15 MB per city |
| Monthly derived rasters | ~2 MB each × 12 | ~72 MB per city |

---

## Index 4: Vegetation Degradation Index

### Data Source: Sentinel-2 L2A NDVI (ESA/Copernicus)

| Parameter | Product | Unit | Resolution |
|:---|:---|:---|:---|
| NDVI (Normalized Difference Vegetation Index) | Sentinel-2 L2A (B04, B08) | −1 to +1 | 10 m |

**Why Sentinel-2?**
- Sentinel-2 provides the highest freely available optical resolution (10 m) for vegetation monitoring.
- Its 5-day revisit cycle enables robust monthly median composites even after cloud filtering.
- Accessed freely via **Microsoft Planetary Computer STAC** — no login required for data access (SAS token auto-generated).
- **Source**: Drusch, M. et al. (2012). "Sentinel-2: ESA's Optical High-Resolution Mission for GMES Operational Services." *Remote Sensing of Environment*, 120, 25–36. DOI: [10.1016/j.rse.2011.11.026](https://doi.org/10.1016/j.rse.2011.11.026)

### Formula Chain

**Step 1 — NDVI computation** (standard remote sensing formula):

```
NDVI = (NIR − Red) / (NIR + Red) = (B08 − B04) / (B08 + B04)
```

Monthly median composite across all cloud-free (<20% cloud cover) Sentinel-2 scenes in the month.

- **Source**: Rouse, J.W. et al. (1974). "Monitoring vegetation systems in the Great Plains with ERTS." *Proceedings of the Third ERTS-1 Symposium*, NASA SP-351, 309–317.
- **Why NDVI?** It is the most widely validated vegetation health indicator in remote sensing literature. Values near 0 indicate bare soil/concrete; values near 0.6–0.8 indicate dense healthy vegetation. It directly measures photosynthetic activity.

**Step 2 — Baseline anomaly (degradation detection)**:

```
vegetation_idx = max(0, −(NDVI − μ_baseline_month) / σ_baseline_month)
```

Inverted: lower NDVI than the baseline for that calendar month → higher degradation stress.

### Approximate Data Size

| Dataset | Per Month | 36 Months |
|:---|:---|:---|
| Sentinel-2 NDVI GeoTIFF (10 m, city bbox) | ~5–20 MB | ~180–720 MB |

> [!NOTE]
> This is the largest data layer by volume due to 10 m resolution. However, it is streamed and processed on-the-fly via Planetary Computer — no persistent global storage needed.

---

## Index 5: Urban Vulnerability Index

### Data Source: OpenStreetMap (OSM) via OSMnx

| Parameter | OSM Feature | Unit | Type |
|:---|:---|:---|:---|
| Road density | Road network edges | km road / km² | Static |
| Building density | Building footprint polygons | count / km² | Static |
| Building footprint fraction | Building polygon areas | fraction (0–1) | Static |
| Green space fraction | Parks, forests, gardens | fraction (0–1) | Static |

**Why OSM?**
- OpenStreetMap is the most complete, freely available, globally consistent source of urban morphology data.
- For Indian cities, OSM has excellent coverage of road networks and building footprints (contributed by large mapping campaigns by HOT, Mapbox, and local communities).
- Accessed via **OSMnx** (Python library by Geoff Boeing), which provides a clean API for downloading and processing OSM features within bounding boxes.
- **Source**: Boeing, G. (2017). "OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks." *Computers, Environment and Urban Systems*, 65, 126–139. DOI: [10.1016/j.compenvurbsys.2017.05.004](https://doi.org/10.1016/j.compenvurbsys.2017.05.004)

### Data Source: Socio-Economic Vulnerability (Census/NFHS)

| Parameter | Source | Unit | Type |
|:---|:---|:---|:---|
| Below Poverty Line % | Census 2011 / NITI Aayog | fraction (0–1) | Static |
| Slum household % | Census 2011 | fraction (0–1) | Static |
| Elderly population % (age >60) | Census 2011 | fraction (0–1) | Static |
| Literacy rate | Census 2011 / NFHS-5 | fraction (0–1) | Static (inverted) |

> [!WARNING]
> Currently, socio-economic data defaults to **synthetic priors** (city-level averages with Gaussian noise per hex) because real district-level CSVs are not bundled. For proof-of-concept this is acceptable — the spatial variation within a city is simulated. For production, real Census 2011 ward-level or NFHS-5 district-level data must be provided as a CSV.

### Formula Chain

**Physical sub-component** (PCA-weighted, fallback equal):

```
physical = w₁×norm(building_density) + w₂×norm(building_fp_fraction)
         + w₃×norm(road_density) + w₄×(1 − norm(green_space_fraction))
```

**Socio-economic sub-component** (PCA-weighted, fallback 0.30/0.30/0.20/0.20):

```
socio = w₁×bpl_pct + w₂×slum_pct + w₃×elderly_pct + w₄×(1 − literacy_pct)
```

**Composite** (PCA-weighted, fallback 0.4 physical / 0.6 socio):

```
urban_vulnerability_idx = normalize_zscore(w_phys × physical + w_socio × socio)
```

- **Conceptual source**: Cutter, S.L. et al. (2003). "Social Vulnerability to Environmental Hazards." *Social Science Quarterly*, 84(2), 242–261. DOI: [10.1111/1540-6237.8402002](https://doi.org/10.1111/1540-6237.8402002)
- **Why this approach?** The Social Vulnerability Index (SoVI) framework by Cutter is the foundational methodology for combining physical exposure with socio-economic susceptibility. PCA-based weighting is standard practice in composite index construction (OECD Handbook on Constructing Composite Indicators, 2008).

### Approximate Data Size

| Dataset | Per City | Notes |
|:---|:---|:---|
| OSM Roads GeoPackage | ~5–30 MB | Downloaded once (static) |
| OSM Buildings GeoPackage | ~10–100 MB | Varies heavily by city |
| OSM Green Space GeoPackage | ~1–10 MB | Downloaded once |
| Vulnerability CSV | <1 MB | Manual input or synthetic |

---

## Final SSI Composition

### Formula

**Linear component**:

```
SSI_linear = Σ(wᵢ × Indexᵢ)   for i = 1..5
```

**Compound interaction component** (captures co-occurring stresses):

```
SSI_compound = SSI_linear + γ × Σ(αᵢⱼ × Indexᵢ × Indexⱼ)
```

Where:
- `γ = 0.5` (interaction scaling factor)
- `αᵢⱼ = max(0, Pearson_corr(Indexᵢ, Indexⱼ))` — only positive correlations amplify compound stress
- Interaction pairs: (Heat × Water), (Heat × Pollution), (Water × Vegetation), (Pollution × Vulnerability)

**Normalization to [0, 1]**:

```
ssi_value = (SSI_compound − min) / (max − min)
```

**Weight derivation**:
1. Base weights from **PCA PC1 loadings** across the 5 indicators
2. City-specific adjustment: `w_adjusted = w_base × (1 + κ × (P_city_rank − 0.5))` where `P_city_rank` is the city's percentile rank on each indicator across all cities, and `κ = 1.0`.

- **Source for compound interaction approach**: Zscheischler, J. et al. (2018). "Future climate risk from compound events." *Nature Climate Change*, 8, 469–477. DOI: [10.1038/s41558-018-0156-3](https://doi.org/10.1038/s41558-018-0156-3)
- **Source for PCA weighting**: OECD/JRC (2008). *Handbook on Constructing Composite Indicators: Methodology and User Guide*. OECD Publishing. DOI: [10.1787/9789264043466-en](https://doi.org/10.1787/9789264043466-en)

---

## Total Data Volume Summary (4 Cities × 3 Years)

| Data Layer | Per City (3 yrs) | 4 Cities Total |
|:---|:---|:---|
| ERA5 NetCDF (climate) | ~70–180 MB | ~280–720 MB |
| MODIS LST GeoTIFF | ~18–72 MB | ~72–288 MB |
| SEDAC PM2.5 + monthly derived | ~80 MB | ~320 MB |
| Sentinel-2 NDVI GeoTIFF | ~180–720 MB | ~720 MB–2.8 GB |
| OSM GeoPackages (static) | ~20–140 MB | ~80–560 MB |
| Vulnerability CSV | <1 MB | <4 MB |
| **Total raw data** | **~370 MB–1.1 GB** | **~1.5–4.7 GB** |
| Final Parquet output (per city) | ~5–15 MB | ~20–60 MB |

---

## Is 3 Years Enough?

### Short answer: **Yes, for proof-of-concept. No, for robust trend detection.**

### Detailed reasoning:

| Aspect | 3 Years | Recommendation |
|:---|:---|:---|
| **Seasonal cycle capture** | ✅ Captures 3 full monsoon cycles, 3 winters, 3 summers. Sufficient to establish monthly climatological baselines. | 3 years is the minimum for seasonal baseline statistics (mean + std per calendar month). |
| **SPEI / drought detection** | ⚠️ SPEI-3 (3-month rolling) works but with only 3 years the "baseline" and "evaluation" periods overlap heavily. | Ideally 5+ years so the first 3 are pure baseline and years 4–5 are evaluation. |
| **Inter-annual variability** | ⚠️ 3 years may not capture rare events (e.g., once-in-5-year heatwave, unusual monsoon failure). | For trend detection, 5–10 years minimum. For proof-of-concept, 3 years demonstrates methodology. |
| **PCA stability** | ✅ With ~2,500 hexes × 36 months = ~90,000 data points, PCA loadings will be statistically stable. | Sufficient. |
| **Anomaly detection** | ⚠️ 90th percentile threshold computed from only 3 years is sensitive to outliers. | Acceptable for PoC; document the limitation. |
| **Vegetation degradation** | ⚠️ 3 years may not distinguish seasonal phenology from actual degradation (tree removal). | Acceptable if baseline comparison is month-to-month (same calendar month across years). |

### Recommended time window for proof-of-concept:

> **January 2020 – December 2022 (3 years)**
>
> **Why this window?**
> - 2020 includes COVID lockdown effects (dramatic pollution drop, visible in PM2.5 and NDVI)
> - 2021 is a recovery year (return to baseline)
> - 2022 is a "normal" post-pandemic year
> - This 3-year window naturally creates a compelling narrative for compound stress analysis
> - All data sources (ERA5, Sentinel-2, MODIS, SEDAC) have complete coverage for this period

### If extending to 5 years (recommended for publication):

> **January 2018 – December 2022 (5 years)**
>
> - First 3 years (2018–2020) serve as pure baseline
> - Last 2 years (2021–2022) serve as evaluation period
> - Captures pre-COVID, COVID, and post-COVID dynamics
> - SPEI and anomaly detection become statistically robust

---

## Summary: Minimum Required Data for 4 Cities × 3 Years

| # | Data Source | Access | Auth Required? | Parameters Used |
|:--|:---|:---|:---|:---|
| 1 | **ERA5 Reanalysis** (Copernicus CDS) | Free API | Yes (free CDS account) | t2m, d2m, tp, u10, v10, ssrd, swvl1, swvl2 |
| 2 | **MODIS MOD11A2 LST** (Planetary Computer) | Free STAC | No | LST_Day_1km |
| 3 | **Sentinel-2 L2A** (Planetary Computer) | Free STAC | No | B04, B08 → NDVI |
| 4 | **NASA SEDAC PM2.5** (EarthData) | Free download | Yes (free EarthData login) | Annual mean PM2.5 (µg/m³) |
| 5 | **OpenStreetMap** (Overpass API / OSMnx) | Free | No | Roads, buildings, green space |
| 6 | **Census 2011 / NFHS-5** (data.gov.in) | Free download | No | BPL%, slum%, elderly%, literacy% |

**All 6 data sources are open and free.** Only ERA5 and SEDAC require free account registrations.
