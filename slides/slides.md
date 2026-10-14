# Slide Deck: Compound Sustainability Stress Index (SSI v2)
**A Reproducible Geospatial Framework for Multi-Hazard Urban Climate Stress**

---

## Slide 1: Question and Scope
- **Core Research Question:** How can urban planners systematically quantify and prioritize compounding environmental hazards (heat, water deficit, air pollution, vegetation loss) across dense metropolitan landscapes without distorting physical seasonality or collapsing spatial variation?
- **Spatial Unit:** Uber H3 hexagonal discrete global grid at resolution 8 (~0.74 km² per cell).
- **Temporal Window:** 36 monthly timesteps across a 3-year study period (January 2020 to December 2022).
- **Reference Geographies:** Coastal megacity (Mumbai: 707 hexes) and inland industrial plateau (Coimbatore: 995 hexes).
- **Composite Framework:** 5 physical stress indicators combined via an unweighted equal baseline with non-linear compound coupling for joint-tail extremes.

---

## Slide 2: Limitations and What This Study Does Not Claim (Upfront Disclosures)
- **CAMS PM₂.₅ has coarse spatial resolution:** Atmospheric pollution data from CAMS EAC4 (~80 km grid) acts as a city-wide monthly signal and does not provide intra-urban neighborhood spatial discrimination across individual H3 cells.
- **Hydrological water stress is predominantly temporal:** ERA5 total precipitation and soil moisture vary primarily across seasons (~98% between-month variance), reflecting regional dry spells rather than local street drainage differences.
- **Exposure indicators are time-invariant:** Census 2011 poverty, slum, and elderly demographics are static priors that act as spatial vulnerability multipliers without monthly variation.
- **November 2022 contains an imputed observation:** Missing satellite and reanalysis feeds in November 2022 are handled via forward-fill from October 2022 as documented in the data dictionary.
- **Heat stress shows modest spatial rank correlation with independent LST:** Heat index exhibits modest within-month spatial agreement with held-out satellite MODIS LST (mean within-month $\rho \approx 0.17$ in the audit; pooled $\rho = 0.22$ in Mumbai and $\rho = 0.59$ in Coimbatore).
- **Compound coupling parameters are deliberate modeling choices:** The coupling intensity ($\gamma = 0.30$) and joint threshold ($q = 0.90$) govern activation levels, while spatial rankings remain stable across the sensitivity grid.
- **Anomaly flags identify metropolitan stress periods:** The 90th percentile anomaly threshold identifies city-wide acute climate episodes rather than isolating isolated individual hexes.
- **The index is not calibrated against health outcomes:** SSI measures environmental hazard exposure and is not calibrated against empirical mortality, hospital admissions, or insurance claim records.
- **Risk classification bands are relative quantiles:** Low, Moderate, High, and Extreme bands represent empirical quartiles across the pooled reference cities, not absolute physiological danger thresholds.
- **Cross-city ranking is descriptive:** With two reference cities evaluated under unified parameters, city rankings are compared descriptively without computing small-sample rank correlation statistics.

---

## Slide 3: Data and Drivers — What Varies in Space vs. Time
- **Component Decomposition:**
  - **Heat (`heat_v2`):** ERA5 2m temperature + dewpoint Heat Index (°C). 98.6% temporal variance in Mumbai.
  - **Water (`water_v2`):** ERA5 precipitation deficit + root-zone volumetric soil moisture. 98.2% temporal variance in Mumbai.
  - **Pollution (`pollution_v2`):** CAMS EAC4 surface PM₂.₅ ($\mu\text{g/m}^3$). 100% temporal variance across hexes.
  - **Vegetation (`veg_v2`):** Sentinel-2 NDVI canopy deficit. High spatial discrimination (54.1% between-hex variance).
  - **Exposure (`exposure_v2`):** Static Census BPL/slum/elderly + OSM building density. 100% spatial variance.
- **Evidence:** Figure F1 (`figures/F1_variance_shares.png`) illustrates the variance decomposition shift from v1 to v2.

---

## Slide 4: Index Construction — One Frozen Global Baseline
- **The v1 Flaw:** Per-month z-score normalization mathematically forced every monthly city mean to 0.50, erasing seasonal temperature swings and monsoon relief.
- **The v2 Solution:** One global frozen baseline fitted on the pooled reference panel across all months and cities, scaling the 2nd to 98th empirical percentiles to $[0, 1]$.
- **Physical Seasonality Restored:**
  - Heat stress peaks in May (pre-monsoon summer) and drops in July–August.
  - Water stress plummets during monsoon precipitation and surges during pre-monsoon dry months.
  - PM₂.₅ shows pronounced winter inversion peaks (December–January) and monsoon washouts.
- **Evidence:** Figure F2 (`figures/F2_seasonality_profiles.png`) confirms distinct annual cycles in all physical indicators.

---

## Slide 5: Indicator Weighting — Four Schemes, One Primary
- **Evaluated Schemes:**
  - **Equal Weighting (Primary):** $w_j = 0.2000$. Pre-registered primary scheme.
  - **Entropy Weight Method (EWM):** $w = [0.170, 0.170, 0.210, 0.222, 0.228]$.
  - **CRITIC:** $w = [0.187, 0.211, 0.206, 0.187, 0.209]$.
  - **PCA (First Principal Component):** $w = [0.263, 0.177, 0.339, 0.117, 0.103]$ (PC1 explains 34.56% variance [C01]).
- **Why Equal Weights Win:** Dispersion-based schemes (EWM/PCA) over-penalize spatial components or reward seasonal atmospheric swings. Equal weighting provides maximum transparency and policy neutrality.
- **Rank Agreement:** Spatial hex-mean rank correlation between Equal and all alternatives remains $\ge 0.9425$ [C10].
- **Evidence:** Figure F3 (`figures/F3_weights_and_correlation.png`) and `docs/weighting_decision.md`.

---

## Slide 6: Compound Risk Formulation — Non-Linear Joint Hazards
- **Linear Index:** $ssi_{lin} = \sum_{j=1}^5 w_j Z_j$.
- **Coupling Formulation:** Smooth interactive enhancement:
  $$ssi_{v2} = ssi_{lin} + \gamma \Omega (1 - ssi_{lin})$$
  where $\Omega = \mathbb{I}(Z_{heat} \ge q) \times \mathbb{I}(Z_{water} \ge q)$.
- **Default Parameters:** $\gamma = 0.30$, $q = 0.90$.
  - Joint hazard co-occurrence rate: $\Omega = 14.43\%$ in Mumbai [C06], $0.68\%$ in Coimbatore [C07].
  - Prevents score explosion: monotonic saturation bounded strictly in $[0, 1]$.
- **Evidence:** Figure F4 (`figures/F4_gamma_q_sensitivity.png`) sweeps $\gamma \in [0.1, 0.5]$ and $q \in [0.75, 0.95]$.

---

## Slide 7: What Changed from v1 to v2
- **Elimination of Artificial Compression:**
  - v1 composite was artificially centered at 0.50 for every month.
  - v2 allows city-wide mean SSI to float freely: Mumbai mean shift = -0.1745 [C04]; Coimbatore shift = -0.2320 [C05].
- **Spatial Rank Consistency:**
  - Spatial hex-mean Spearman $\rho = 0.8634$ in Mumbai [C02] and $\rho = 0.9272$ in Coimbatore [C03].
  - Top-decile hex overlap (Jaccard) is 0.2613 in Mumbai and 0.7217 in Coimbatore, reflecting re-ranking of seasonally vulnerable hexes.
- **Evidence:** Step 09 comparative ledger in `results/compare_mumbai.json` and `results/compare_coimbatore.json`.

---

## Slide 8: Sensitivity and Robustness Testing
- **Perturbation Testing Against Real Failure Modes:**
  - **S1 (Weighting Schemes):** Min hex-mean $\rho = 0.9425$ [C10], min Kendall $\tau = 0.8007$. Stable.
  - **S2 ($\gamma$ Coupling Sweeps 0.1 to 0.5):** Min hex-mean $\rho = 0.9988$ [C11]. Stable.
  - **S3 ($q$ Threshold Sweeps 0.75 to 0.90):** Min hex-mean $\rho = 0.9989$ [C12]. Stable.
  - **S4 (Leave-One-Index-Out):** Min hex-mean $\rho = 0.8870$ [C13] (dropping exposure causes lowest rank agreement). Moderately sensitive.
  - **S5 (Baseline Bounds 1/99% to 5/95%):** Min hex-mean $\rho = 0.9989$. Stable.
- **Takeaway:** Spatial rankings are highly insensitive to compound parameters $\gamma$ and $q$, and move primarily with weighting scheme and exposure components.
- **Evidence:** `results/sensitivity_summary.csv` and Figure F4.

---

## Slide 9: Validation Against Real Events and Independent Data
- **V1 (April–May 2020 Lockdown):** Evaluated [V1]. CAMS PM₂.₅ dropped by 0.1259 in Mumbai and 0.0604 in Coimbatore compared to post-lockdown 2022.
- **V2 (March–April 2022 Heatwave):** Evaluated [V2]. Heat index surged by +0.0572 in Mumbai, expanding the compound activation share from 36.6% to 43.4%.
- **V3 (Held-Out Satellite MODIS LST):** Evaluated [V3]. Modest within-month correlation (mean within-month $\rho = -0.1345$ in Mumbai; $+0.2436$ in Coimbatore). Spatial block bootstrap shows positive pooled association ($\rho = 0.2176$ in Mumbai, $\rho = 0.5915$ in Coimbatore).
- **V4 (Spatial Structure):** Evaluated [V4]. High spatial coherence confirmed via Moran's $I = 0.7285$ in Mumbai [C14] and $I = 0.7947$ in Coimbatore [C15] ($p = 0.002$).
- **V5 (Held-Out Built Morphology):** Evaluated [V5]. Significant association between exposure and held-out green space fraction ($\rho = -0.1903$ in Mumbai, $p < 10^{-6}$).
- **V6 (Vegetation-Exposure Coupling):** Evaluated [V6]. Sign and magnitude reported transparently with block-bootstrap 95% CIs: positive in Mumbai ($\rho = 0.6595$) and Coimbatore ($\rho = 0.5912$).
- **Evidence:** Figure F6 (`figures/F6_event_validation.png`) and `results/validation.json`.

---

## Slide 10: Spatial Results and Hex-Level Typology
- **Spatial Distribution:**
  - 45.03% of Mumbai hex-months fall in the Extreme risk band [C08] vs. 10.77% in Coimbatore [C09].
  - Persistent hot-spots concentrate in high-exposure, low-canopy industrial/dense corridors.
- **Stationary Hex Typology ($k=2$ Archetypes) [C16]:**
  - **Cluster 0 (41.5% of hexes):** Suburban/Open, Low Canopy, High Heat.
  - **Cluster 1 (58.5% of hexes):** Dense Urban Core, Low Canopy, Moderate Heat.
  - **Clustering Stability:** Mean Adjusted Rand Index (ARI) = 1.000 across 50 bootstrap resamples; silhouette score = 0.5054.
  - **Spatial Coherence:** 100% adjacent hex pairs share cluster assignment (vs. 51.3% in 500-permutation null).
- **Evidence:** Figure F5 (`figures/F5_spatial_ssi_bands.png`), Figure F7 (`figures/F7_archetype_profiles.png`), and `results/archetypes.json`.

---

## Slide 11: Cross-City Comparative Analysis
- **Unified Parameter Benchmark:** Both cities scored using frozen pooled reference parameters (no city-specific curve fitting).
- **Rank Invariance Across Schemes:**
  - Mumbai exhibits higher mean composite stress than Coimbatore under all 4 weighting schemes:
    - Equal: Mumbai 0.4719 > Coimbatore 0.3317
    - EWM: Mumbai 0.4549 > Coimbatore 0.2822
    - CRITIC: Mumbai 0.4687 > Coimbatore 0.3115
    - PCA: Mumbai 0.4804 > Coimbatore 0.3533
  - All 4 schemes preserve identical city ranking order [C08/C09].
- **Driver Profile Differences:**
  - Mumbai stress is driven by elevated heat index, high PM₂.₅, and coastal humidity.
  - Coimbatore stress is buffered by lower atmospheric PM₂.₅ and lower demographic density.
- **Evidence:** Figure F8 (`figures/F8_crosscity_comparison.png`) and `results/crosscity__table.csv`.

---

## Slide 12: Future Work and Roadmap
- **High-Resolution Air Quality:** Integrate neighborhood-scale low-cost sensor networks (e.g., CAAQMS ground monitors) or downscaled satellite aerosol optical depth (AOD at 1 km) to replace coarse 0.75° CAMS reanalysis.
- **Empirical Calibration Against Outcome Data:** Cross-validate composite hazard exposure against municipal hospital heat-stroke admissions, dengue incidence, and infrastructure flood reports.
- **Dynamic Exposure Surrogates:** Incorporate dynamic mobile positioning data or seasonal night-time lights to replace decennial Census demographic static layers.
- **National Metropolitan Expansion:** Extend the frozen global baseline pipeline to 30 Tier-1 and Tier-2 Indian cities with diverse agro-climatic zones.
