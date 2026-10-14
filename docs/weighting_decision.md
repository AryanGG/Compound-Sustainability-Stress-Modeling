# Decision Memo: Selection of Primary Weighting Scheme for SSI v2

**Decision:** Primary weighting scheme is **Equal Weighting (`equal`)**.  
**Alternatives retained for sensitivity analysis:** Entropy Weight Method (`ewm`), CRITIC (`critic`), and Principal Component Analysis (`pca`).  
**Reference Data:** Pooled reference panel (Mumbai & Coimbatore, $N = 61,272$ hex-months).  
**Output Configuration:** `config.yml → v2.primary_scheme = equal`

---

## 1. Fitted Weights Comparison

| Dimension | Equal | EWM | CRITIC | PCA | Note on Behavior |
|---|:---:|:---:|:---:|:---:|---|
| **Heat (`heat_v2`)** | **0.2000** | 0.1947 | 0.1956 | 0.3538 | Balanced across Equal, EWM, and CRITIC; elevated in PCA. |
| **Water Deficit (`water_v2`)** | **0.2000** | 0.1299 | 0.1627 | 0.3687 | Driven strongly by seasonal monsoon cycles; dominates PC1 alongside heat. |
| **Vegetation Loss (`veg_v2`)** | **0.2000** | 0.0708 | 0.1586 | 0.1723 | Penalized by EWM due to concentrated urban canopy distribution. |
| **Pollution (`pollution_v2`)** | **0.2000** | 0.3234 | 0.2617 | 0.0294 | Inflated in EWM/CRITIC due to massive winter-monsoon swings; collapsed in PCA. |
| **Urban Exposure (`exposure_v2`)** | **0.2000** | 0.2811 | 0.2214 | 0.0758 | Static spatial structure heavily distorted by time-series variance models. |
| **Sum** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | All schemes satisfy non-negativity and unit simplex sum. |

---

## 2. Rationales for Selecting Equal Weighting as Primary

Under the project governance standards and scientific audit recommendations, **Equal Weighting** is adopted as the primary composite baseline based on four key empirical and methodological grounds:

1. **Dispersion Artifacts in EWM and CRITIC:**  
   Both the Entropy Weight Method and CRITIC systematically assign higher weights to variables with higher sample dispersion. In this spatio-temporal panel, atmospheric PM2.5 and water deficit exhibit dramatic city-wide winter-to-monsoon fluctuations, which artificially inflates their information entropy ($w_{\text{pollution}} = 0.323$ in EWM). Rewarding raw temporal swings biases the composite index toward acting as a seasonal calendar tracker rather than a balanced multi-hazard risk diagnostic.

2. **Weak Dimensional Summary by PCA ($R^2 < 50\%$):**  
   PC1 accounts for only **$34.56\%$** of the total variance across the five standardized indicators. Because the underlying stress hazards represent distinct, partially orthogonal environmental dimensions (e.g. built-environment density vs. photochemical atmospheric stagnation), a single linear component cannot adequately summarize the system. Furthermore, PCA loadings collapse pollution weight down to $0.029$ simply because PM2.5 does not co-vary linearly with the primary heat-water axis across all seasons.

3. **Time-Invariance Distortion of Exposure:**  
   The built-environment exposure indicators (`built_up_fraction`, `building_density`, `road_density`) are static within each hex across the 36-month observation period (zero temporal variance, $100\%$ spatial variance). Variance-driven algorithms conflate spatial heterogeneity with temporal variability, penalizing or distorting static structural vulnerability relative to dynamic weather variables.

4. **Viva Defensibility and Principle of Insufficient Reason:**  
   In the absence of calibrated ground-truth compound mortality, economic loss, or infrastructure failure response data, assigning empirical weights based on arbitrary mathematical variance criteria introduces spurious precision. Equal weighting represents the most defensible, transparent, and reproducible formulation (OECD Handbook on Constructing Composite Indicators, 2008), ensuring that each sustainability hazard contributes equitably to the base diagnostic.

---

## 3. Role of Alternative Schemes

The alternative schemes are **not discarded or hidden**. Instead, they are explicitly integrated into Step 10 (**Sensitivity and Robustness Testing**):
- Every v2 panel record stores `ssi_lin_equal`, `ssi_lin_ewm`, `ssi_lin_critic`, and `ssi_lin_pca`.
- Step 10 and Step 13 systematically evaluate whether spatial cell rankings and policy prioritizations remain invariant under these alternative weighting philosophies.
