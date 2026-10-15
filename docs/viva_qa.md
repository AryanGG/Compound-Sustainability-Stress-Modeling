# Defense Examination Q&A (Viva Voce)

This document provides structured, defensible answers to expected examination questions regarding the Compound Sustainability Stress Index (SSI v2) methodology. Every answer is structured as:
$$\text{\textbf{Claim}} \longrightarrow \text{\textbf{Evidence File \& Numbers}} \longrightarrow \text{\textbf{Explicit Limitation}}$$
All numerical figures are extracted live from artifacts in `results/`. No number is estimated from memory.

---

### Question 1: Where do your weights come from, and why not use the Entropy Weight Method (EWM) or PCA?

- **Claim:** We use an equal weighting scheme ($w_j = 0.2000$ for all five indicators) as our pre-registered primary formulation. Dispersion-based weighting schemes (such as EWM, CRITIC, and PCA) mathematically penalize stationary spatial indicators and over-reward city-wide temporal swings in water deficit and atmospheric pollution. Furthermore, the spatial ranking of urban hexes is highly insensitive to the choice of weighting scheme.
- **Evidence:**
  - `results/weights_preview.json`: EWM assigns $w = [0.1702, 0.1704, 0.2096, 0.2215, 0.2283]$; CRITIC assigns $w = [0.1866, 0.2114, 0.2057, 0.1873, 0.2090]$; PCA first component assigns $w = [0.2630, 0.1774, 0.3392, 0.1171, 0.1032]$ (PC1 explains 34.56% of total variance [C01]).
  - `results/sensitivity_summary.csv` (Family S1): Comparing the primary equal-weight index against EWM, CRITIC, and PCA yields a minimum spatial hex-mean rank correlation of $\rho = 0.9425$ [C10] and minimum Kendall $\tau = 0.8007$ (classified as "stable").
  - Technical justification memo: `docs/weighting_decision.md`.
- **Limitation:** Equal weighting makes an explicit, normative policy assumption that each environmental dimension carries equal societal importance. In the absence of empirical damage or economic loss valuation functions, equal weighting provides a transparent, defensible, and un-manipulated baseline.

---

### Question 2: Your v1 heat and water stress indices showed almost no seasonality. Why?

- **Claim:** The v1 pipeline applied per-month z-score normalization ($z = \frac{x - \mu_{month}}{\sigma_{month}}$). This mathematically forced every monthly city-wide mean to 0.50, completely subtracting out the physical annual cycle (summer heat waves, monsoon precipitation relief, winter inversions). In v2, we replaced this with a single global frozen baseline fitted on the pooled multi-city reference panel across all 36 months, restoring true physical seasonality.
- **Evidence:**
  - `results/diagnostics_variance.json`:
    - **Heat stress (`heat_v2`):** In Mumbai, monthly-mean spread expanded from 0.4649 in v1 to 0.9948 in v2 (between-month variance share = 98.63%). In Coimbatore, monthly-mean spread expanded from 0.3056 in v1 to 0.6507 in v2 (between-month variance share = 87.62%).
    - **Water stress (`water_v2`):** In Mumbai, monthly-mean spread expanded from 0.7639 in v1 to 0.9918 in v2 (between-month variance share = 98.16%). In Coimbatore, monthly-mean spread expanded from 0.3268 in v1 to 0.8316 in v2 (between-month variance share = 92.99%).
  - Figure F2 (`figures/F2_seasonality_profiles.png`): Confirms that summer pre-monsoon heat peaks in May and drops sharply during monsoon precipitation.
- **Limitation:** Baseline normalisation depends on the empirical boundaries of the 2020–2022 observation period. Extreme events that exceed the 98th percentile of this reference window are clamped at 1.0 (affecting 4.82% of heat hex-months in Mumbai).

---

### Question 3: Why was the correlation between vulnerability and building density removed as a validation check?

- **Claim:** The v1 validation claim ($R^2 \approx 0.97$ between urban vulnerability and building density) was entirely circular. Building density from OpenStreetMap was already an input variable used to construct the vulnerability index. We removed this circular check completely and replaced it with six pre-registered, independent validation hypotheses (V1–V6) that test the index against real physical events and held-out layers.
- **Evidence:**
  - `docs/validation_hypotheses.md`: Pre-registered hypotheses committed prior to running validation code.
  - `audit/provenance.md`: Line-by-line documentation of the v1 circularity.
  - `results/validation.json`: Independent validation battery (V1–V6) using real events and held-out data.
- **Limitation:** Independent validation checks cannot produce artificial $R^2 \approx 0.97$ correlations. Real-world comparisons against independent satellite data exhibit modest correlations (e.g., V3 MODIS LST $\rho \approx 0.22$), which honestly reflect sensor and atmospheric differences.

---

### Question 4: Why choose a compound coupling intensity of $\gamma = 0.30$ and the 90th percentile threshold ($q = 0.90$)?

- **Claim:** The v1 default choices ($\gamma = 0.30$, 75th percentile) were selected without sensitivity testing. In v2, we pre-registered $\gamma = 0.30$ and $q = 0.90$ for the heat-drought compound hazard pair, and conducted exhaustive grid sweeps across $\gamma \in [0.1, 0.5]$ and $q \in \{0.75, 0.90, 0.95\}$. Spatial prioritization is robust to these choices: altering $\gamma$ and $q$ smoothly scales absolute index levels and activation frequencies, but leaves spatial hex rankings virtually unchanged.
- **Evidence:**
  - `results/sensitivity_summary.csv`:
    - Sweeping $\gamma$ from 0.1 to 0.5 (Family S2) produces a minimum spatial hex-mean rank correlation of $\rho = 0.9988$ [C11] and min $\tau = 0.9777$.
    - Sweeping $q$ from 0.75 to 0.90 (Family S3) produces a minimum spatial hex-mean rank correlation of $\rho = 0.9989$ [C12] and min $\tau = 0.9734$.
  - `results/crosscity__table.csv`: Compound activation rate ($\Omega$) at $q = 0.90$ is 14.43% in Mumbai [C06] and 0.68% in Coimbatore [C07].
  - Figure F4 (`figures/F4_gamma_q_sensitivity.png`): Demonstrates monotonic level shifts without rank disorder.
- **Limitation:** Because $\gamma$ and $q$ alter composite index magnitude rather than spatial order, intervention priority thresholds based on absolute score cutoffs must be treated as relative hazard categories rather than fixed biophysical limits.

---

### Question 5: Is the Compound Sustainability Stress Index (SSI) validated against external evidence [V1..V6]?

- **Claim:** Validity evidence is partial, specific to physical proxies, and pre-registered [V1–V6]. The index successfully tracks major historical shocks and exhibits strong spatial coherence, but it has not been calibrated or verified against human health outcomes, mortality, or financial asset loss.
- **Evidence:**
  - `results/validation.json`:
    - **V1 (2020 Lockdown):** CAMS PM₂.₅ fell by 0.1259 in Mumbai and 0.0604 in Coimbatore during April–May 2020 relative to post-lockdown 2022.
    - **V2 (2022 Heatwave):** Pre-monsoon Heat Index surged by +0.0572 in Mumbai, expanding the compound activation rate to 43.35%.
    - **V3 (Held-Out Satellite LST):** Modest within-month spatial correlation with MODIS LST (mean within-month $\rho = -0.1345$ in Mumbai, $+0.2436$ in Coimbatore; pooled spatial block-bootstrap $\rho = 0.2176$ [95% CI 0.1951, 0.2501] in Mumbai and $\rho = 0.5915$ [95% CI 0.5071, 0.6681] in Coimbatore).
    - **V4 (Spatial Structure):** Global Moran's $I = 0.7285$ in Mumbai [C14] and $I = 0.7947$ in Coimbatore [C15] ($p = 0.002$).
    - **V5 (Held-Out Layer):** Significant correlation between exposure and held-out green space fraction ($\rho = -0.1903$ in Mumbai, $p < 10^{-6}$).
- **Limitation:** The index models multi-hazard environmental exposure. It does not model epidemiological dose-response curves or localized disaster damage functions.

---

### Question 6: Why does the green-space correlation flip sign between cities?

- **Claim:** In validation check V5, the correlation between exposure and green space fraction is negative in Mumbai ($\rho = -0.1903$, $p = 3.44 \times 10^{-7}$) and positive in Coimbatore ($\rho = +0.2291$, $p = 2.55 \times 10^{-13}$). When evaluating the relationship between vegetation stress and exposure (check V6), the Spearman rank correlation is positive in both cities: $\rho = 0.6595$ (95% CI [0.5404, 0.7560]) in Mumbai and $\rho = 0.5912$ (95% CI [0.4236, 0.7354]) in Coimbatore. We report these empirical findings as observed, rejecting simplistic narratives that green space acts uniformly across diverse metropolitan morphologies.
- **Evidence:** `results/validation.json` (sections V5 and V6) with spatial block-bootstrap confidence intervals computed at H3 resolution 6 parent clusters.
- **Limitation:** In dense coastal Mumbai, informal settlements and impoverished neighborhoods lack tree canopy and park access. In semi-arid, sprawling Coimbatore, rural-urban fringe settlements overlap with peri-urban agricultural vegetation, producing different spatial associations.

---

### Question 7: How many archetypes did you find, and are they actionable for urban planners?

- **Claim:** We resolved the v1 artifact where every hex cycled through 6 transient monthly regimes. In v2, we establish a stationary, hex-level typology using time-averaged feature vectors. Evaluating $k = 2 \dots 8$ across 50 bootstrap resamples identified exactly $k = 2$ stable archetypes [C16] with an Adjusted Rand Index (ARI) of 1.000 and silhouette score of 0.5054.
- **Evidence:**
  - `results/archetypes.json`:
    - **Cluster 0 (41.54% of hexes):** Suburban/Open, Low Canopy, High Heat.
    - **Cluster 1 (58.46% of hexes):** Dense Urban Core, Low Canopy, Moderate Heat.
    - **Spatial Coherence:** 100% of adjacent hex pairs share the same cluster assignment (compared to a 500-permutation null mean of 51.35%).
  - Figure F7 (`figures/F7_archetype_profiles.png`) and `results/archetypes__hex_assignments.csv`.
- **Limitation:** A 2-cluster macro-typology provides high-level zoning guidance (identifying thermal suburban expansion vs. dense urban core exposure), but planners requiring localized micro-interventions should examine the continuous multi-indicator profiles.

---

### Question 8: Beyond forensic SSI index calculation, how does the Hyperlocal Early Warning System predict statutory crisis events, and how was it evaluated out-of-time on unseen historical benchmarks?

- **Claim:** Retrospective environmental dashboards report historical degradation after emergency wards have already flooded with heatstroke patients and water reserves are depleted. To address the fundamental need for actionable foresight, we formulated a temporal predictive early warning system (EWS) trained strictly on 2020–2021 historical panels (104 non-leaking temporal predictors) and evaluated out-of-time on the unseen 2022 historical benchmark. Evaluated against real historical crises—specifically the devastating March–April 2022 pan-Indian heatwave—the system achieved 93.8% recall in Mumbai, 92.2% recall in Delhi NCR, 99.5% recall in Bikaner, and 100% recall in Kolkata and Indore, with continuous forward SSI trajectory prediction reaching $R^2 = 0.895$ in Delhi and $R^2 = 0.888$ in Mumbai.
- **Evidence:**
  - `results/ml_event_prediction_metrics.json` and `results/ml_event_prevalence.json`:
    - **Heatwave Event PR-AUC (Unseen 2022):** 0.990 in Delhi NCR, 0.886 in Mumbai, 0.983 in Bikaner, 0.903 in Indore, and 0.862 in Kolkata.
    - **March–April 2022 Pan-Indian Heatwave Holdout Recall:** Correctly flagged 93.8% of acute heatwave hex-months in Mumbai (165 of 176 alert cells), 92.2% in Delhi (1,844 of 2,000 alert cells), 99.5% in Bikaner (1,154 of 1,160 alert cells), and 100% in Kolkata and Indore.
    - **Continuous Future Stress ($t+1$ SSI):** $R^2 = 0.895$ in Delhi, $R^2 = 0.888$ in Mumbai, $R^2 = 0.872$ in Coimbatore.
    - **Permutation Risk Attribution:** Identifies leading physical precursors: rolling 90-day temperature anomalies, heat stress momentum ($\Delta \text{heat}$ velocity), cumulative 3-month precipitation deficits, and dry soil moisture exhaustions.
  - `results/ml_policy_playbook_summary.json`: Direct mapping of forecasted probabilities into statutory action tiers: IMD Heat Action Plan (HAP Stage II Amber & Stage III Red alerts) and CAQM Graded Response Action Plan (GRAP Stage III & IV directives).
  - Figures F9, F10, F11 (`paper_images/`): ROC/PR curves, spatial hex threat maps (Mumbai April 2022 and Delhi March 2022), and precursor attribution waterfalls.
- **Limitation:** Model predictions rely on precursor environmental signals and accumulated biophysical stress. Sudden exogenous shocks (such as localized industrial chemical fires or unannounced cross-border power transmission failures) that lack multi-week environmental precursory signals cannot be anticipated by sensor-lag models.


