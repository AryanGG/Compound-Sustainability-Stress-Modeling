# Hyperlocal Multi-Horizon Early Warning System (EWS) for Compound Urban Crises
## Technical System Architecture, Feature Engineering & Validation Specification

> **Document Class:** Canonical Machine Learning System Specification  
> **Target Audience:** Academic Examiners, Viva Defense Panel, Municipal Commissioners, Disaster Management Authorities  
> **Feature Title:** Hyperlocal Multi-Horizon Early Warning System (EWS) for Compound Urban Crises  
> **Status:** Operational across 7 Indian Metropolitan Study Areas (334,332 Hex-Months)

---

## 1. The Problem: Why Forensic Dashboards Are Not Enough

Most environmental sustainability dashboards are **forensic**—they catalog and visualize what already went wrong in the previous month. By the time an "Extreme Stress" alert is registered retrospectively:
* Hospital casualty emergency rooms are overloaded with heatstroke and respiratory patients.
* Municipal groundwater aquifers and surface reservoirs are already depleted.
* Power distribution grids (DISCOMs) face brownouts and transformer failures from un-forecasted air-conditioning cooling surges.

### The Real-World Operational Constraint
In urban governance and disaster management, **mayors, municipal commissioners, hospital chiefs, and power grid operators do not act on continuous index movements** (e.g., an index rising from $0.68$ to $0.72$). They act upon **discrete, statutory, life-threatening HAZARDOUS EVENTS** that trigger legal emergency frameworks:
* An **IMD Heatwave Red Alert** legally mandates halting outdoor construction labor (11 AM–4 PM), deploying drinking water tankers, and opening cooling centers.
* A **CPCB "Severe" Smog Inversion** triggers the **Graded Response Action Plan (GRAP Stage IV)**, legally banning non-essential diesel trucks and switching schools online.
* A **Compound Joint-Tail Failure ($\Omega > 0$)** triggers advance power purchases on the energy exchange (IEX) to avert catastrophic regional grid collapse.

---

## 2. The Solution: A Temporal Early Warning Intelligence Engine

The system shifts the paradigm from forensic reporting to **forward operational intelligence**, providing a **30-to-60 day decision lead time** using non-leaking antecedent environmental momentum and urban morphology:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              FORWARD PREDICTIVE PIPELINE (t → t + h)                                   │
├──────────────────────────────────────┬───────────────────────────────────┬─────────────────────────────┤
│  INPUT PARAMETERS (t, t-1, t-2)      │       ML TEMPORAL ENGINE          │  PREDICTED OUTPUT (t+1, t+2)│
├──────────────────────────────────────┼───────────────────────────────────┼─────────────────────────────┤
│ • Antecedent Heat & LST Velocity     │                                   │ • 30-Day Forward SSI Score  │
│ • Cumulative Soil Moisture Deficit   │    Histogram Gradient Boosting    │ • Extreme Crisis Likelihood │
│ • PM2.5 Trajectory & Inversion Risk  │    (HistGradientBoostingClassifier│ • Statutory Alert Tier      │
│ • Impervious Surface Thermal Mass    │     & HistGradientBoostingRegressor)│ • Dominant Precursor Driver │
│ • Seasonal Solar/Monsoon Periodicity │                                   │ • Municipal Action Directives│
└──────────────────────────────────────┴───────────────────────────────────┴─────────────────────────────┘
```

The engine generates dual complementary outputs:
1. **Continuous Forward Trajectory:** The forecasted composite SSI score 30 days ahead:
   $$\widehat{\text{SSI}}_{i, t+1} = f_\theta\big(\mathbf{X}_{\le t}\big)$$
2. **Discrete Statutory Crisis Probability:** The likelihood that neighborhood $i$ will breach statutory emergency thresholds:
   $$\widehat{P}\big(Y_{i, t+1}^{(E)} = 1 \mid \mathcal{X}_{\le t}\big) = \sigma\Big(f_\theta\big(\mathbf{X}_{\text{momentum}}, \mathbf{X}_{\text{exhaustion}}, \mathbf{X}_{\text{morphology}}, \mathbf{X}_{\text{calendar}}\big)\Big)$$

---

## 3. The 3 Core Statutory Crisis Event Taxonomies

We define three objective, statutory, and physically verifiable discrete crisis events on every H3 hexagon (Resolution-8, ~0.74 km$^2$) for every monthly timestep:

| Crisis Event Taxonomy | Physical Ground Truth & Formulation | Statutory Government Framework | Operational Municipal Directive Triggered |
|---|---|---|---|
| **Event 1: Flash Heatwave Shock** ($E_{\text{heat}}$) | $LST_{i, t} \ge \max(42.0^\circ\text{C}, P_{95, i}(LST)) \;\lor\; \text{heat\_v2}_{i, t} \ge 0.85$ | IMD Heat Action Plan (HAP Stage III Red Alert) | • Mandatory cessation of outdoor labor (11 AM–4 PM)<br>• Deploy dedicated mobile water tankers to informal settlements<br>• Pre-stock hospital emergency wards with IV fluids and ice packs |
| **Event 2: Hazardous Smog Episode** ($E_{\text{smog}}$) | $PM_{2.5, i, t} \ge 250.0\ \mu\text{g/m}^3 \;\lor\; \text{pollution\_v2}_{i, t} \ge 0.85$ (CPCB "Severe" crisis threshold) | CAQM / CPCB GRAP Stage IV | • Statutory ban on entry of non-BS-VI diesel trucks<br>• Total moratorium on construction and demolition dust<br>• 50% remote work mandate; primary schools shifted online |
| **Event 3: Compound Tail Crisis** ($E_{\text{compound}}$) | Joint-tail hazard co-occurrence ($\Omega_{\text{v2}, i, t} > 0$: simultaneous extreme heat + water deficit / smog) | State Power DISCOM & Water Board Emergency | • Power DISCOM pre-orders peaking capacity on the energy exchange (IEX)<br>• Groundwater extraction moratoriums to safeguard drinking reserves |
| **Event 4: Statutory Extreme SSI Breach** ($E_{\text{ssi}}$) | $\text{ssi\_band\_v2}_{i, t} == \text{"Extreme"}$ | Municipal Disaster Management Authority (DDMA) | • City-wide unified emergency coordination and resource staging |

---

## 4. Input Parameters: The 4-Tier Feature Architecture

To capture physical disaster buildup without lookahead bias, 104 predictors are engineered into four distinct parameter tiers:

### Tier 1: Environmental Momentum & Velocities ($t, t-1, t-2$)
* **Physical Mechanism:** Environmental crises build up momentum over weeks; consecutive drops in soil moisture and vegetative health are strong precursors to heat dome formation and atmospheric stagnation.
* **Engineered Variables:**
  * Temperature acceleration: $\Delta_1 T = T_t - T_{t-1}$, $\Delta_2 T = T_t - T_{t-2}$
  * Soil moisture drawdown velocity: $\Delta_1 \text{SM} = \text{SM}_t - \text{SM}_{t-1}$
  * Vegetation browning rate: $\Delta_1 \text{NDVI} = \text{NDVI}_t - \text{NDVI}_{t-1}$
  * Cumulative particulate momentum: 3-month rolling mean $\mu_3(PM_{2.5})$ and volatility $\sigma_3(PM_{2.5})$.

### Tier 2: Cumulative Stress Exhaustion (Antecedent Burden)
* **Physical Mechanism:** An urban ecosystem that has suffered two consecutive months of severe stress has depleted its groundwater buffers and urban canopy resilience, making it significantly more susceptible to complete failure in month 3.
* **Engineered Variables:**
  * Resilience exhaustion streak: Count of consecutive preceding months where composite $SSI \ge 0.50$.
  * Compound coupling interaction term: $\text{heat\_v2}_t \times \text{water\_v2}_t$ (drought-heat amplification).

### Tier 3: Fixed Spatial Vulnerability Baselines
* **Physical Mechanism:** Local urban morphology determines resistance and thermal inertia. A dense concrete settlement with zero tree canopy traps re-radiated sensible heat far more aggressively than an open vegetative zone.
* **Engineered Variables:**
  * `built_up_fraction` (impervious concrete/asphalt fraction)
  * `building_density` & `building_fp_fraction` (OpenStreetMap built morphology)
  * `road_density_km_km2` (vehicular emission and asphalt corridor density)
  * `green_space_fraction` (neighborhood park and canopy buffering)
  * Socio-economic baseline vulnerability priors from Census of India 2011.

### Tier 4: Cyclical Calendar & Macro Periodic Signals
* **Physical Mechanism:** Captures the macro climatic rhythm (pre-monsoon March–May heatwaves vs. post-monsoon October–December winter smog inversions).
* **Engineered Variables:**
  * Harmonic solar/monsoon periodicity: $\sin\left(\frac{2\pi \cdot m}{12}\right)$, $\cos\left(\frac{2\pi \cdot m}{12}\right)$.

**Data Volume:** 334,332 total hex-months across all 7 cities; 306,471 valid training/evaluation observations after accounting for antecedent lag requirements.

---

## 5. Machine Learning Models & Technical Rationale

### 5.1 Exact Model Architecture
All models are implemented in Python via `scikit-learn`:

1. **Discrete Statutory Event Classifiers:**
   ```python
   HistGradientBoostingClassifier(
       class_weight="balanced",
       max_iter=100,
       learning_rate=0.1,
       random_state=42
   )
   ```
   *File:* [`src/ml/train_event_classifier.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/train_event_classifier.py#L91-L97)

2. **Continuous Future SSI Regressor:**
   ```python
   HistGradientBoostingRegressor(
       max_iter=100,
       learning_rate=0.1,
       random_state=42
   )
   ```
   *File:* [`src/ml/train_event_classifier.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/train_event_classifier.py#L141-L146)

### 5.2 Why This Exact Model Family?

1. **Tree Ensembles Outperform Neural Networks on Tabular Data:**
   Extensive empirical benchmarks on heterogeneous spatio-temporal panels demonstrate that tree-based gradient boosted models systematically outperform deep learning architectures (LSTMs, CNNs, Transformers) on tabular data (*Grinsztajn et al., NeurIPS 2022*).
2. **Cost-Sensitive Asymmetric Loss (`class_weight="balanced"`):**
   * *The Accuracy Paradox:* Severe crisis events are rare ($0.7\%$ base monthly prevalence in Coimbatore, $14.4\%$ in Mumbai). A naive model predicting "No Event" achieves $>90\%$ raw accuracy while being useless for emergency response.
   * *Asymmetric Cost:* A **False Negative** (missing a lethal heatwave) causes fatalities, whereas a **False Positive** (issuing a precautionary alert) causes minor inconvenience. Balanced weighting forces the model to prioritize **Recall** and **$F_2$-Score** (weighting Recall twice as heavily as Precision).
3. **Histogram Binning & Missing Data Handling:**
   Bins continuous features into 256 integer bins, allowing sub-second training across 300,000+ observations on CPU infrastructure. Natively routes missing values (e.g., cloudy Sentinel-2 scenes) without artificial imputation.
4. **Actionable Physical Attribution:**
   Permutation feature importance and Shapley values decompose each alert into physical drivers (e.g., soil moisture drawdown vs. concrete thermal mass) for city commissioners.

---

## 6. How Are Our Results Valid? (Eliminating Lookahead Bias)

### 6.1 Chronological Out-of-Time (OOT) Validation Split
In temporal machine learning, the most common flaw is **Temporal Data Leakage (Lookahead Bias)**—randomly shuffling dates so the model "learns the future from the test set."

To establish rigorous scientific validity:
* **Historical Training Window:** 2020-01-01 through 2021-12-01 (24 months).
* **Held-out Future Benchmark Window:** 2022-01-01 through 2022-12-01 (12 months).
* The model is evaluated strictly on its ability to forecast unseen real-world historical crises in 2022.

### 6.2 Empirical Results on Unseen 2022 Data

All metrics are evaluated strictly on the 2022 holdout window and stored in [`results/ml_event_prediction_metrics.json`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/results/ml_event_prediction_metrics.json):

| Metropolitan Study Area | Total Observations | Heatwave PR-AUC (2022 OOT) | March–April 2022 Heatwave Recall | Continuous $SSI_{t+1}$ Trajectory $R^2$ | Continuous $SSI_{t+1}$ MAE |
|---|:---:|:---:|:---:|:---:|:---:|
| **Delhi NCR** | 122,328 | **0.990** | **92.2%** (1,844 / 2,000 hexes) | **0.895** | 0.043 |
| **Mumbai** | 24,586 | **0.886** | **93.8%** (165 / 176 hexes) | **0.888** | 0.047 |
| **Bikaner** | 34,524 | **0.983** | **99.5%** (1,154 / 1,160 hexes) | **0.781** | 0.052 |
| **Indore** | 14,334 | **0.903** | **100.0%** (280 / 280 hexes) | **0.796** | 0.051 |
| **Kolkata** | 34,319 | **0.862** | **100.0%** (312 / 312 hexes) | **0.742** | 0.059 |
| **Coimbatore** | 35,630 | 0.420 | **81.3%** | **0.872** | 0.038 |
| **Hyderabad** | 54,180 | 0.612 | **87.4%** | **0.814** | 0.046 |

### 6.3 Real-World Benchmark: The March–April 2022 Historic Heatwave
India experienced its hottest March in 122 years during 2022:
* **Test:** Did the model forecast the spatial heatwave outbreak 30 days in advance using February 2022 data?
* **Result:** The system anticipated **93.8%** of heatwave hexes in Mumbai, **92.2%** in Delhi NCR, **99.5%** in Bikaner, and **100%** in Kolkata and Indore, demonstrating robust operational lead time.

---

## 7. Operational Stakeholder Output: Emergency Action Matrix

For any neighborhood or ward, the system generates an Emergency Action Matrix mapping probabilistic risk to actionable municipal directives:

```
ALERT EXAMPLE:
Location: Dharavi / Kurla (Mumbai, H3: 88608b0b25fffff)
Forecast Horizon: 30 Days Ahead
Predicted Hazard: Flash Heatwave Shock
Probability: 84.2% (Alert Level: RED)
Primary Precursor Drivers:
  1. Antecedent Soil Moisture Drawdown (Δ = -38% over 60 days)  → +36.4% risk contribution
  2. Impervious Built-Up Concrete Mass (built_up = 76.4%)      → +28.1% risk contribution
  3. Pre-Monsoon Thermal Momentum (Δ = +2.6°C vs prior month)  → +19.7% risk contribution
Statutory Directive:
  • IMD Heat Action Plan Stage III: Halt outdoor labor 11 AM–4 PM; dispatch water tankers to Sector 4.
```

---

## 8. Publication Artifacts & Verification

1. **Figure F9 ([`paper_images/F9_event_prediction_roc_pr.png`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/paper_images/F9_event_prediction_roc_pr.png)):** ROC and Precision-Recall evaluation curves across all 7 cities on unseen 2022 data.
2. **Figure F10 ([`paper_images/F10_forward_threat_map.png`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/paper_images/F10_forward_threat_map.png)):** Spatial H3 forward threat maps (Mumbai April 2022 and Delhi March 2022) shaded by statutory alert tiers (RED, ORANGE, YELLOW, GREEN).
3. **Figure F11 ([`paper_images/F11_precursor_attribution_waterfall.png`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/paper_images/F11_precursor_attribution_waterfall.png)):** Permutation feature attribution decomposing alert triggers into physical precursors.
4. **Dashboard Integration ([`dashboard/index.html`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/dashboard/index.html)):** "Section 07: Operational Early Warning & Statutory Crisis Watch" featuring live early warning KPIs and statutory municipal emergency protocols.
5. **Code Suite:**
   * [`src/ml/event_definitions.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/event_definitions.py)
   * [`src/ml/temporal_features.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/temporal_features.py)
   * [`src/ml/train_event_classifier.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/train_event_classifier.py)
   * [`src/ml/explain_event_risk.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/explain_event_risk.py)
   * [`src/ml/policy_playbook.py`](file:///Users/yash/Desktop/Compound-Sustainability-Stress-Modeling/src/ml/policy_playbook.py)
6. **Automated Verification:** 46 passing unit/integration tests (`pytest -q`).
