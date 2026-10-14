# Pre-Registered Validation Hypotheses (SSI v2)

This document pre-registers the empirical evaluation hypotheses, metrics, and passing criteria for Step 11 **prior to executing the validation harness**. Pre-registering prevents post-hoc justification of unexpected results and guarantees scientific integrity.

---

## Pre-Registered Hypotheses Matrix

| ID | Empirical Event / Benchmark | Hypothesis Statement | Expected Direction | Quantitative Metric | Pre-Declared Pass Criterion |
|---|---|---|---|---|---|
| **V1** | **National COVID-19 Lockdown (Apr–May 2020)** | Industrial and vehicular cessation during the nationwide lockdown reduced particulate air pollution compared to post-lockdown normal activity (Apr–May 2022). | $\Delta \text{Pollution} < 0$ | Difference in mean `pollution_v2` between Apr–May 2020 and Apr–May 2022. | Apr–May 2020 mean strictly less than Apr–May 2022 mean (`diff < 0`). |
| **V2** | **Record Heatwave (Mar–Apr 2022)** | North-Central and Western India suffered record-breaking early summer heatwaves in Mar–Apr 2022 exceeding historical averages. | $\Delta \text{Heat} > 0$ | Difference in mean `heat_v2` for Mar–Apr 2022 vs. baseline Mar–Apr of 2020–2021; also change in compound trigger share $\Delta \Omega$. | Mar–Apr 2022 mean `heat_v2` exceeds 2020–2021 average by at least $+0.05$ (5% index span). |
| **V3** | **Construct Validity vs. Independent MODIS LST** | Meteorological heat index (`heat_v2`, computed from ambient air temperature and humidity) correlates positively with independent satellite Land Surface Temperature (`lst_c`). | $\rho > 0$ | Average within-month Spearman correlation ($\rho$) across all 36 observation dates with spatial block-bootstrap 95% CI. | Mean within-month $\rho > 0$ and $> 50\%$ of months show positive correlation. (Modest correlation expected due to canopy/built emissivity decoupling). |
| **V4** | **Spatial Autocorrelation / Coherence** | Hex-level mean composite stress `ssi_v2` exhibits continuous spatial structure (hotspots and cold corridors) rather than white noise. | Moran's $I > 0$ | Global Moran's $I$ using H3 topological 1-ring neighbors (`grid_disk(1)`), row-standardized weights, 999 permutations. | Moran's $I > 0.30$ with pseudo $p$-value $< 0.001$. |
| **V5** | **Exposure Construct vs. Held-Out Census Deprivation** | Structural built environment exposure (`exposure_v2`) correlates with independent ward/district poverty and slum concentration. | $\rho > 0$ | Spearman rank correlation of `exposure_v2` against held-out `slum_pct` / `bpl_pct` (in cities where census mapping is available). | Spearman $\rho > 0.10$ ($p < 0.05$). |
| **V6** | **Greenery–Exposure Decoupling Across Climatic Regimes** | The spatial relationship between vegetative canopy (`veg_v2`) and built exposure (`exposure_v2`) varies by urban morphology and climatic zone (coastal vs. semi-arid inland). | Heterogeneous sign across cities | City-specific Spearman rank correlation between hex-mean `veg_v2` and `exposure_v2`. | Sign and magnitude reported transparently per city; sign flip acknowledged without narrative bias. |

---

## Statistical Protocol: Spatial Block Bootstrap

To account for heavy spatial autocorrelation across contiguous H3 Resolution 8 cells (~0.74 km²), naive independent identically distributed (i.i.d.) variance estimators are prohibited. 
All confidence intervals are estimated via **Spatial Block Bootstrapping**:
- **Spatial Blocks:** H3 Resolution 6 parent cells (~36 km² clusters, parent offset = 2).
- **Resampling:** Entire geographic clusters resampled with replacement ($B = 500$ draws).
- **Confidence Intervals:** Empirical 2.5% and 97.5% quantiles of the cluster bootstrap distribution.
