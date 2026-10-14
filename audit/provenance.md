# Provenance Audit and v1 Freeze

**Audit Date:** 2026-10-14  
**Git Branch:** `v2-defense`  
**Git Tag:** `v1-frozen`  
**Frozen Archive:** `archive/v1/`  
**Manifest:** `archive/v1/MANIFEST.sha256` (verified with `sha256sum -c`)

---

## 1. Provenance Answers

### (a) Producing Script Path
* **Original v1 Pipeline Producer:** `run_pipeline.py` (specifically orchestrating `src/features/ssi.py:compute_ssi()`).
  - `run_pipeline.py` lines 341–358 invoke `compute_ssi()` and save outputs to `data/h3_panel/final/{city}.parquet`, `{city}.csv`, and `{city}_ssi.csv`.
  - Core math was implemented in `src/features/ssi.py:464-545`.
* **Ad-Hoc Batch Overwrite Script:** `recompute_all_cities_proper_ssi.py` (which invoked `src/features/proper_ssi.py:compute_proper_ssi()`).
  - Executed on 2026-10-13 at 21:53 to overwrite `data/h3_panel/final/*.csv` and `*.parquet`.

### (b) Last-Modified / Commit
* `run_pipeline.py`: Last modified 2026-10-04 13:44:20 (commit `1343c8d`).
* `src/features/ssi.py`: Last modified 2026-10-14 12:51:13 (commit `c064679`).
* `recompute_all_cities_proper_ssi.py`: Last modified 2026-10-13 21:53:03 (commit `c064679`).
* `src/features/proper_ssi.py`: Last modified 2026-10-13 21:52:31 (commit `c064679`).
* Base commit for freeze: `c064679` tagged as `v1-frozen`.

### (c) Fitted Weights & Regression Reproduction
* **Regression check via `audit/fit_check.py` on `archive/v1/final/mumbai.csv`:**
  - `numpy.linalg.lstsq` (no intercept) regressing `ssi_linear` on `[heat_stress_idx, water_stress_idx, vegetation_idx, pollution_idx, urban_vulnerability_idx]`.
  - **Fitted Coefficients:**
    - `heat_stress_idx`: **0.1714**
    - `water_stress_idx`: **0.1452**
    - `vegetation_idx`: **0.1260**
    - `pollution_idx`: **0.2784**
    - `urban_vulnerability_idx`: **0.2791**
  - **Regression $R^2$:** **1.000000** ($R^2 \ge 0.999$, exact linear fit).
  - **Weight Sum:** 1.0000.
* **Historical PCA Loadings (from initial audit in `docs/AUDIT.md`):**
  - The unadjusted PC1 loadings on `mumbai_features.csv` were Heat: ~0.436, Veg: ~0.426, Pollution: ~0.110, Vuln: ~0.022, Water: ~0.006. With city rank adjustment (Mumbai ranks): Heat: 0.4545, Veg: 0.4447, Pollution: 0.0762, Vuln: 0.0191, Water: 0.0054 ($R^2 = 1.000000$).
  - Overwritten on Oct 13 21:53 by `recompute_all_cities_proper_ssi.py` to entropy-based weights above.

### (d) Is EWM Wired In?
* **Answer: NO.**
* **Evidence:**
  1. `run_pipeline.py` lines 1–367: Does NOT import `compute_ewm_weights`, `compute_entropy_weights`, or `run_validation_and_novelty.py`.
  2. `src/features/ssi.py` lines 1–548: Only calls `compute_pca_weights()` (lines 51–114, 502) and `apply_city_weight_adjustments()` (lines 189–228, 505). Neither imports nor calls EWM.
  3. `run_validation_and_novelty.py` is a completely independent evaluation script that reads existing Parquet panels read-only and writes only `reports/validation_summary.json`. It was never wired into the core `run_pipeline.py` or `src/features/ssi.py`.
  4. The only script that ever wired EWM into panel calculation was the ad-hoc batch script `recompute_all_cities_proper_ssi.py`, which is not part of the standard production pipeline `run_pipeline.py`.

---

## 2. Name Map (Section 3 Target vs. Real Repo)

| Entity Type | Target Name (Section 3 / Plan) | Real Repo Name (v1) | Status / Action for v2 |
|---|---|---|---|
| **Config** | `config.yml → v2:` | `config.yml` (existing v1 keys) | Step 03 adds `v2:` block without overwriting v1 |
| **Pipeline Runner** | `run_v2.py` | `run_pipeline.py` | `run_v2.py` to be created in Step 08 |
| **v1 Archive** | `archive/v1/` | `archive/v1/` | Created & frozen in Step 02 |
| **Results Dir** | `results/` | `reports/` | Create `results/` in Step 03; keep `reports/` for HTML dashboards |
| **Raw Panel Dir** | `data/h3_panel/v2_raw/` | None (`data/processed/`, `data/features/`) | To be created in Step 04 |
| **v2 Panel Dir** | `data/h3_panel/v2/` | None (`data/h3_panel/final/` is v1) | To be created in Step 06/08 |
| **Fit Params** | `results/fit_parameters.json` | None (`reports/validation_summary.json`) | To be created in Step 06 |
| **Heat Indicator** | `heat_v2` | `heat_stress_idx` | Target normalized name for v2 |
| **Water Indicator** | `water_v2` | `water_stress_idx` | Target normalized name for v2 |
| **Veg Indicator** | `veg_v2` | `vegetation_idx` | Target normalized name for v2 |
| **Pollution Indicator** | `pollution_v2` | `pollution_idx` | Target normalized name for v2 |
| **Vuln Indicator** | `vuln_v2` | `urban_vulnerability_idx` | Target normalized name for v2 |
| **Linear SSI** | `ssi_linear` | `ssi_linear` | Identical column name |
| **Compound Trigger** | `omega_compound` | `omega_compound` | Identical column name |
| **Final SSI** | `ssi_value` | `ssi_value` | Identical column name |
| **SSI Category** | `ssi_band` | `ssi_band` | Identical column name |
| **CAMS Ingest** | `src/ingest/cams_pm25_ingest.py` | `src/ingest/pm25_ingest.py` | Step 05 will create clean CAMS ingest |
| **Results I/O** | `src/utils/results_io.py` | None | Step 03 creates with metadata stamp |
