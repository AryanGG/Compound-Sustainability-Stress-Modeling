# Proper SSI Calculation & Multi-City Modeling Plan

> **Scope:** Complete Architectural Redesign & Execution for 7 Indian Megacities  
> **Study Period:** 2020-01 to 2022-12 (36 months continuous panel)  
> **Cities:** Bikaner, Coimbatore, Delhi, Hyderabad, Indore, Kolkata, Mumbai  
> **Total Empirical Observations:** **334,332 hex-months** at Uber H3 Resolution 8 (~0.74 km²)

---

## 1. Problem Audit: Why the Previous Calculation Failed

Prior audits of the initial pipeline ([SSI_VALIDATION_PLAN.md](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/SSI_VALIDATION_PLAN.md) & [docs/AUDIT.md](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/docs/AUDIT.md)) revealed four critical flaws:

| Flaw | Mathematical Root Cause | Physical Failure |
|:---|:---|:---|
| **1. The 0.5 Normalization Trap** | Baseline z-scores were computed per calendar month over 3 years ($N=3$). Subtracting the calendar-month mean forced every month's mean z-score to 0.0, mapping `(z+3)/6` to **0.5000**. | May summer heatwaves (38°C) and January winters (14°C) both had an identical heat score of **0.50**. Monsoons (110mm rain) and dry seasons (0mm) both had water stress of **0.50**. Seasonal climate cycles were completely erased. |
| **2. PCA Weight Collapse** | PC1 explained only 25% of variance across orthogonal climate dimensions. | Water stress received a weight of **0.0054** (0.5%), rendering droughts invisible in the composite score. |
| **3. Pollution Monopoly** | Because PM2.5 was the only indicator with active seasonal spread (0.778), the composite SSI tracked only air pollution. | The compound index was effectively just a PM2.5 proxy with random noise. |
| **4. Lack of Compound Tail Coupling** | Linear combinations ($w_i v_i$) assumed hazards are additive. | Failed to capture compound concurrent shocks (heatwaves co-occurring with water deficits or stagnation smog). |

---

## 2. The Redesigned Proper SSI Formulation

### 2.1 Physical Climatological Normalization (Restoring Ground Truth Dynamics)

Each indicator is normalized against **absolute physical, epidemiological, and ecological bounds** rather than per-month sample deviations:

#### A. Heat Stress Index ($v_{\text{heat}} \in [0, 1]$)
Combines ambient humid heat (Heat Index via Rothfusz regression) with satellite radiometric surface heat (MODIS LST):
$$\text{HI} = f_{\text{Rothfusz}}(T_{\text{air}}, \text{RH}) \quad [^\circ\text{C}]$$
$$v_{\text{heat}} = 0.70 \cdot \left[ \frac{\text{HI} - 20^\circ\text{C}}{25^\circ\text{C}} \right]_{[0,1]} + 0.30 \cdot \left[ \frac{\text{LST} - 15^\circ\text{C}}{30^\circ\text{C}} \right]_{[0,1]}$$
* **Physical Justification:** Aligns with NOAA / IMD heat warning thresholds (Caution at 27°C, Danger at 41°C). Captures both macro-atmospheric sultriness and localized micro-Urban Heat Islands.

#### B. Water Stress Index ($v_{\text{water}} \in [0, 1]$)
Combines volumetric soil moisture deficit and precipitation deficit:
$$\text{Deficit}_{\text{soil}} = \left[ \frac{0.28 - \theta_{\text{soil}}}{0.22} \right]_{[0,1]}, \quad \text{Deficit}_{\text{precip}} = \left[ 1 - \frac{P}{150\,\text{mm}} \right]_{[0,1]}$$
$$v_{\text{water}} = 0.60 \cdot \text{Deficit}_{\text{soil}} + 0.40 \cdot \text{Deficit}_{\text{precip}}$$
* **Physical Justification:** During the Indian Summer Monsoon ($P > 150\,\text{mm}, \theta > 0.25$), water stress drops to $\approx 0.10$. During pre-monsoon summer droughts ($P \approx 0, \theta < 0.08$), water stress surges to $\approx 0.95$.

#### C. Air Pollution Index ($v_{\text{poll}} \in [0, 1]$)
Logarithmic scaling anchored to the Indian National Ambient Air Quality Standard (NAAQS, $60\,\mu\text{g/m}^3$) and severe smog episodes ($350\,\mu\text{g/m}^3$):
$$v_{\text{poll}} = \left[ \frac{\ln(1 + \text{PM}_{2.5})}{\ln(1 + 350\,\mu\text{g/m}^3)} \right]_{[0,1]}$$

#### D. Vegetation Degradation Index ($v_{\text{veg}} \in [0, 1]$)
Inverted photosynthetic canopy density from Sentinel-2 L2A:
$$v_{\text{veg}} = \left[ 1 - \frac{\text{NDVI} - 0.05}{0.65} \right]_{[0,1]}$$
Dense canopy/wetlands $\to 0.0$; degraded urban core/barren ground $\to 1.0$.

#### E. Urban Structural Vulnerability ($v_{\text{vuln}} \in [0, 1]$)
Impervious built footprint and lack of urban cooling green space:
$$v_{\text{vuln}} = 0.70 \cdot f_{\text{built}} + 0.30 \cdot (1 - f_{\text{greenspace}})$$

---

### 2.2 Objective Information Weighting (Entropy Weight Method)

To avoid PCA collapse, weights are derived using Shannon Information Entropy ($EWM$):
$$p_{ij} = \frac{x_{ij}}{\sum_{i} x_{ij}}, \quad e_j = -\frac{1}{\ln N} \sum_{i} p_{ij} \ln p_{ij}, \quad d_j = 1 - e_j, \quad w_j = \frac{d_j}{\sum_k d_k}$$
Dimensions with genuine spatial and temporal variance receive their exact mathematically justified weights without human bias.

---

### 2.3 Non-Linear Joint-Tail Coupling (JT-SSI)

$$\text{SSI}_{\text{JT}} = \sum_{i=1}^{5} w_i v_i + \gamma \cdot \Omega_{\text{compound}}$$
$$\Omega_{\text{compound}} = \sum_{(i,j) \in \mathcal{P}} \mathbb{I}(v_i > q_{i,0.75}) \cdot \mathbb{I}(v_j > q_{j,0.75}) \cdot \sqrt{v_i \cdot v_j}$$
With $\gamma = 0.30$, and $\mathcal{P}$ representing the 4 physical coupling pairs:
1. `(Heat, Water)` $\to$ Compound Heatwave-Drought
2. `(Heat, Pollution)` $\to$ Stagnation-Photochemical Smog Episode
3. `(Water, Vegetation)` $\to$ Eco-Hydrological Drought
4. `(Pollution, Built Vulnerability)` $\to$ Socio-Environmental Injustice Trap

---

## 3. Multi-City Implementation Matrix (7 Cities, 334,332 Observations)

| City | Climatic Regime | Hex Count ($N$) | Total Records ($N \times 36$) | Primary Climate Driver |
|:---|:---|:---:|:---:|:---|
| **Bikaner** | Thar Desert / Hot Arid (*BWh*) | 959 | 34,524 | Chronic water scarcity + barren terrain |
| **Coimbatore** | Semi-Arid Rainshadow (*BSh*) | 995 | 35,820 | Western Ghats thermal-moisture moderation |
| **Delhi** | Indo-Gangetic Plain (*Cwa*) | 3,398 | 122,328 | Extreme winter smog + severe summer heatwaves |
| **Hyderabad** | Deccan Plateau Semi-Arid (*BSh*) | 1,505 | 54,180 | Pre-monsoon drying + high built density |
| **Indore** | Malwa Central Plateau (*Aw*) | 731 | 26,316 | Moderate thermal swings + lower baseline pollution |
| **Kolkata** | Gangetic Delta Tropical Wet (*Aw*) | 992 | 35,712 | High humidity sultriness + winter particulate smog |
| **Mumbai** | Konkan Coastal Megacity (*Am*) | 707 | 25,452 | Maritime humidity + intense monsoon deluge |
| **TOTAL** | **Pan-India Multi-Climatic Coverage** | **9,287** | **334,332** | **Full Geographical Representation** |

---

## 4. Execution Roadmap

1. **Implement `src/features/proper_ssi.py`**: A vectorized module executing the physical normalization, EWM weighting, and JT-SSI calculation.
2. **Update `config.yml`**: Register all 7 cities and update global configuration parameters.
3. **Execute Batch Recomputation**: Run across all 7 cities in `data/h3_panel/final/` to generate synchronized Parquet and CSV files.
4. **Regenerate Visualization Dashboards**: Run `generate_report.py` for all 7 cities.
5. **Update Verification Metrics**: Run `run_validation_and_novelty.py` across the 7-city dataset.
