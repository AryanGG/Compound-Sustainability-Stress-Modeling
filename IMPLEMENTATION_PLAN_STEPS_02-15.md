# SSI v2 — Implementation Plan, Steps 02–15

Continues from **Step 01 (repo audit)**. Each step is self-contained so an agent can run it in a fresh session.

---

## 0. How to run this with Antigravity

1. **One step per session.** Paste *Section 1 (Global rules)* + *Section 2 (Status report)* + **one** step. Nothing else.
2. Tell the agent: *"Execute only Step NN. Do not start the next step. Finish by running the acceptance checks and printing the Status Report."*
3. Paste the Status Report back to me before starting the next step. If a step says **STOP**, do not let the agent improvise.
4. Commit after every passing step: `git commit -m "step NN: <title>"`.

> **Provenance of this plan.** File paths, module names and column names come from the commands and outputs in your earlier chat (`run_v2.py`, `src/v2/*`, `results/fit_parameters.json`, `data/h3_panel/{final,v2_raw,v2}`, `ssi_value`, `heat_stress_idx`, …). Step 02 verifies they match your real repo. Code snippets here were run on synthetic data and behave as described, but **none of it has touched your real data yet**. The acceptance checks are what tell you if it works.

---

## 1. Global rules (apply to every step)

| # | Rule |
|---|---|
| G1 | **v1 is frozen.** Never write to `data/h3_panel/final/`, `archive/v1/`, or any v1 result. v1 is read-only comparison material. |
| G2 | **No within-date normalization** (rank, percentile, min-max or z-score computed per month) anywhere in v2. Normalization parameters are fitted **once**, on the pooled reference panel, saved to `results/fit_parameters.json`, and applied unchanged to every city. |
| G3 | **No per-city refitting** of weights, thresholds or band cuts. |
| G4 | **All randomness seeded** from `config.yml → v2.seed`. |
| G5 | **Every result goes through `save_result()`** (Step 03) so it carries git SHA, config hash and timestamp. |
| G6 | **No number is typed by hand** into slides, the dashboard, or markdown. Every number comes from a file in `results/`. |
| G7 | **If an acceptance check fails: STOP and report.** Do not loosen a threshold, skip a test, or "fix" data to make it pass. |
| G8 | **Do not touch files outside the step's "Files" list.** |
| G9 | Keep functions small and pure. One module = one responsibility. Add a pytest for each module. |
| G10 | Forbidden wording in any output text: `100% verified`, `zero-hallucination`, `guarantee`, `proves`, `proven`, `completely robust`. |

---

## 2. Status report (agent pastes this at the end of every step)

```
STEP: NN — <title>
STATUS: PASS | FAIL | BLOCKED
FILES CREATED: <list>
FILES MODIFIED: <list>
COMMANDS RUN: <list>
ACCEPTANCE CHECKS: <each check → PASS/FAIL + the actual number>
SURPRISES: <anything that differed from the plan>
OPEN QUESTIONS: <anything you need from me>
```

---

## 3. Target repo layout

```
config.yml                          # v2: section (Step 03)
run_v2.py                           # --stage fit | score  (Step 08)
archive/v1/                         # frozen copy of v1 + MANIFEST.sha256 (Step 02)
audit/{provenance.md, schema_check.py}
docs/{data_dictionary.md, weighting_decision.md, validation_hypotheses.md, limitations.md}
src/ingest/cams_pm25_ingest.py      # Step 05
src/utils/results_io.py             # Step 03
src/v2/{raw_drivers,indices,weighting,ssi}.py
src/analysis/{diagnostics,run_compare,run_sensitivity,run_validation,run_archetypes,run_crosscity,run_figures}.py
scripts/{check_claims.py,lint_wording.py}
tests/
data/h3_panel/{final (v1, read-only), v2_raw, v2}/
results/
figures/
```

---

# STEP 02 — Provenance audit and v1 freeze

**Goal.** Settle the audit's top question: *which code produced `mumbai.csv`, and is the EWM/validation code actually wired into the index?* Freeze v1.

**Depends on:** Step 01. **Writes code:** none (one throwaway script).
**Files:** `archive/v1/*`, `audit/provenance.md`, `audit/fit_check.py`

**Instructions**

1. `git status` must be clean (commit or stash first). Create branch `v2-defense`. Tag the current commit `v1-frozen`.
2. Copy `data/h3_panel/final/`, the existing `results/`, and the dashboard build output into `archive/v1/`. Generate `archive/v1/MANIFEST.sha256` (`sha256sum` of every file). Do not modify anything under `archive/v1/` afterwards.
3. Find the producer of the v1 index:
   - `grep -rn "ssi_linear\|ssi_value\|entropy\|ewm" --include=*.py .`
   - `git log -S"ssi_linear" --oneline`
   - List every script that writes `ssi_value`, with last-modified date.
4. Reproduce the v1 weights from the CSV. In `audit/fit_check.py`, regress `ssi_linear` on `heat_stress_idx, water_stress_idx, vegetation_idx, pollution_idx, urban_vulnerability_idx` using `numpy.linalg.lstsq` (no intercept). Record coefficients and R².
   *Reference from the audit:* **0.45 heat, 0.45 vegetation, 0.08 pollution, 0.02 vulnerability, 0.005 water**. Your coefficients should match to about 2 decimals.
5. Check whether the entropy-weight (EWM) code and `run_validation_and_novelty.py` are imported by the script that produced the CSV. Answer **yes/no with the file and line**.
6. Write `audit/provenance.md` with four answers: (a) producing script path; (b) last-modified/commit; (c) fitted weights; (d) is EWM wired in (yes/no, evidence).
7. Verify the layout in Section 3 against the real repo. Record every path/column-name difference in `provenance.md` under **"Name map"** — later steps use this map.

**Acceptance**
- [ ] Branch `v2-defense` and tag `v1-frozen` exist.
- [ ] `sha256sum -c archive/v1/MANIFEST.sha256` passes.
- [ ] `provenance.md` answers (a)–(d) with file paths, not guesses.
- [ ] Regression R² ≥ 0.999 (the audit says the fit is exact).

**STOP if:** you cannot identify the producing script. List candidates and wait.

---

# STEP 03 — Scaffolding, config, results I/O, test harness, schema check

**Goal.** Create the skeleton every later step plugs into.
**Files:** `config.yml` (add `v2:`), `src/utils/results_io.py`, `audit/schema_check.py`, `tests/test_results_io.py`, empty package `__init__.py` files.

**3.1 `config.yml`: add (do not replace existing keys)**

```yaml
v2:
  seed: 20260101
  cities: [mumbai, coimbatore]
  reference_cities: [mumbai, coimbatore]      # fit pool. Never add synthetic/test cities here.
  expected_months: {start: "2020-01-01", end: "2022-12-01"}   # CONFIRM in Step 04 (the audit says Nov 2022 is missing)
  baseline: {lo_q: 0.02, hi_q: 0.98}          # pooled, all months, all reference cities
  primary_scheme: equal                        # decided in Step 07
  compound: {pair: [heat_v2, pollution_v2], q: 0.90, gamma: 0.30,
             sweep_q: [0.75, 0.90], sweep_gamma: [0.1, 0.2, 0.3, 0.4, 0.5]}
  bands: {quantiles: [0.25, 0.50, 0.75], labels: [Low, Moderate, High, Extreme]}
  h3: {parent_offset: 2}                       # block-bootstrap blocks = cell_to_parent(res - 2)
  paths: {raw: data/h3_panel/v2_raw, v2: data/h3_panel/v2, v1: data/h3_panel/final, results: results}
```

If the real compound pair in v1 was not heat × pollution (check `provenance.md`), use the v1 pair and note the reason.

**3.2 `src/utils/results_io.py`**

```python
import hashlib, json, os, subprocess, datetime as dt
import pandas as pd, numpy as np

def _sha(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()

def save_result(name: str, payload: dict, config: dict, out_dir="results") -> str:
    """DataFrames -> {name}__{key}.csv ; everything else -> {name}.json with provenance header."""
    os.makedirs(out_dir, exist_ok=True)
    meta = {"git_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
            "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest(),
            "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "seed": config.get("seed")}
    body = {}
    for k, v in payload.items():
        if isinstance(v, pd.DataFrame):
            p = f"{out_dir}/{name}__{k}.csv"; v.to_csv(p, index=False); body[k] = {"csv": p, "rows": len(v)}
        elif isinstance(v, pd.Series):
            body[k] = v.to_dict()
        elif isinstance(v, np.generic):
            body[k] = v.item()
        else:
            body[k] = v
    path = f"{out_dir}/{name}.json"
    json.dump({"_meta": meta, **body}, open(path, "w"), indent=2, default=str)
    return path
```

**3.3 `audit/schema_check.py`.** For each city in `v2.cities`, read `data/h3_panel/v2/{city}.parquet` and assert:
- columns include `h3_index, date, heat_v2, water_v2, veg_v2, pollution_v2, exposure_v2, ssi_lin_v2, omega_v2, ssi_v2, ssi_band_v2`
- no duplicate `(h3_index, date)`
- `rows == n_hex × n_months` (balanced panel)
- no NaN in index and SSI columns
- `date` is month-start
- `0 ≤ ssi_v2 ≤ 1`

Print a table `city, rows, hexes, months, ok` and exit non-zero on failure. (It will fail until Step 08. That is expected.)

**Acceptance**
- [ ] `pytest tests/test_results_io.py` passes (writes a dict + a DataFrame, reads back, checks `_meta` keys).
- [ ] `python -c "import yaml; print(yaml.safe_load(open('config.yml'))['v2']['seed'])"` prints the seed.
- [ ] `config.yml` still loads for the legacy v1 code (run any v1 entry point with `--help`).

---

# STEP 04 — Raw driver panels (`v2_raw`)

**Goal.** Rebuild the inputs in **physical units, un-normalized**, per hex per month. This is the foundation of the seasonality fix.
**Files:** `src/v2/raw_drivers.py`, `docs/data_dictionary.md`, `tests/test_raw_drivers.py`
**Output:** `data/h3_panel/v2_raw/{city}.parquet`

**Output schema (one row per hex-month)**

| column | meaning | rule |
|---|---|---|
| `h3_index`, `date` | keys | `date` = first day of month |
| `heat_raw` | heat driver in physical units (e.g. LST °C) | higher = more stress |
| `water_raw` | water-stress driver (e.g. precipitation deficit) | higher = more stress. Flip if your variable is *availability* |
| `veg_raw` | vegetation greenness (e.g. NDVI) | higher = more green (flipped in Step 06) |
| `pollution_raw` | PM2.5 µg/m³ | filled in Step 05; placeholder NaN now is acceptable |
| `exposure_raw` | static exposure/vulnerability composite | time-invariant |
| `exp_*` | each exposure component stored separately | needed so validation can exclude them |
| `is_imputed` | bool, any driver filled for this row | never silently interpolate |

**Instructions**

1. Read the Step 02 name map. Identify, for each of `heat/water/veg`, the **source** (raster/CSV/GEE export) that existed **before** v1 normalization.
2. **If only v1 normalized sub-indices exist (no raw source recoverable): STOP.** Report which drivers lack raw data. Rank-normalized values cannot be un-normalized.
3. Implement `build_raw(city: str, cfg: dict) -> pd.DataFrame`.
4. Resolve the month window against `expected_months`. For known gaps (the audit flags **November 2022**): either drop that month for every city or fill it from the same source with `is_imputed=True`. Choose one, record it in `data_dictionary.md`, apply it identically to all cities.
5. `exposure_raw`: combine only static inputs (e.g. built density, population density, slum/informal share, whatever v1's `urban_vulnerability_idx` used). Store every component as `exp_<name>`. Combine by mean of pooled-min-max components, then document it.
6. Write `docs/data_dictionary.md`: one table row per column with **definition, unit, source file, time resolution, spatial resolution, direction, known issues**. Explicitly record: *PM2.5 has ≈3 distinct values per month; exposure inputs are constant in time.*
7. **Circularity rule.** Create `docs/data_dictionary.md → "Held-out variables"`: list any dataset you intend to use for validation in Step 11 (independent LST product, transit layer, informal-settlement layer…). None of them may appear in `heat_raw`, `veg_raw` or `exposure_raw`.

**Acceptance (`tests/test_raw_drivers.py`)**
- [ ] Balanced panel: `rows == n_hex × n_months` for each city.
- [ ] Monthly means are **not constant**: for `heat_raw`, `water_raw`, `veg_raw`, `max(month_mean) − min(month_mean) > 1 %` of the variable's overall range. (The v1 bug was a monthly mean of exactly 0.50 everywhere.)
- [ ] Values in physical range (e.g. if °C: 10–60; NDVI: −1–1). Report min/max.
- [ ] `exposure_raw` has zero within-hex variance across months.
- [ ] No column is rank/percentile transformed. Test: the number of distinct values per month is close to the number of hexes, not tied.

---

# STEP 05 — Pollution driver (CAMS reanalysis, same source for every city)

**Goal.** Put pollution on a consistent, documented source across cities. Cross-city comparison requires identical sources.
**Files:** `src/ingest/cams_pm25_ingest.py`, `tests/test_cams_units.py`, update `raw_drivers.py` to fill `pollution_raw`.

**Verify before coding (do not skip, do not trust this text):**
- CAMS datasets are served by the **Atmosphere Data Store (ADS)**, not the Climate Data Store. `~/.cdsapirc` must point to the ADS endpoint and hold your key. Confirm on the dataset page.
- Confirm on the **Download tab**: dataset id (expected `cams-global-reanalysis-eac4-monthly`), variable name (expected `particulate_matter_2.5um`), `product_type`, `data_format`, area ordering `[north, west, south, east]`.
- Run a **1-month, 1-year test request** first.

**Instructions**

1. Implement `request_city(city, bbox, years, out_dir)` → NetCDF; `to_city_series(nc)` → monthly Series in **µg m⁻³** (file unit is kg m⁻³, so multiply by 1e9). Pad the bbox by ~0.5° because the grid is ≈0.75°; at least one cell centre must fall inside.
2. Read bounding boxes from `cities_bbox.json` (adapt to its actual key layout; record the mapping).
3. Output `data/processed/cams_pm25_monthly_{city}.csv`.
4. In `build_raw`, set `pollution_raw` = the city's monthly value, broadcast to every hex that month. **Document that this adds zero spatial variance by design**, so pollution acts as a temporal modulator, not a spatial discriminator.
5. Write the CAMS-vs-existing-PM2.5 monthly correlation (Spearman) to `results/pm25_source_check.json`. Report it, don't gate on it.
6. Fallback if ADS access fails: keep the existing PM2.5 series, set `pollution_source="legacy"` in the data dictionary, and state in `limitations.md` that cross-city pollution is not source-consistent.

**Acceptance**
- [ ] Unit test: a 1×1 fake NetCDF with value `2.5e-8` → `25.0`.
- [ ] Mumbai CAMS series has 36 values (or the window from Step 04), no NaN.
- [ ] Monsoon months (Jun–Sep) have lower mean PM2.5 than Dec–Feb. **If not: STOP**, since units, region or variable are probably wrong.

---

# STEP 06 — Global-baseline indices (the seasonality fix) + variance diagnostics

**Goal.** Replace per-month normalization with one frozen baseline so seasonality survives.
**Files:** `src/v2/indices.py`, `src/analysis/diagnostics.py`, `scripts/step6_diagnostics.py`, `tests/test_indices.py`

**Method.** For each raw driver, bounds are the pooled reference quantiles (default 2nd/98th, all months, all reference cities). Index = `clip((x − lo)/(hi − lo), 0, 1)`; vegetation is inverted (`1 − z`) so all indices mean *more stress = higher*.

```python
import numpy as np, pandas as pd
IDX_COLS = ["heat_v2", "water_v2", "veg_v2", "pollution_v2", "exposure_v2"]
RAW_MAP = {"heat_raw": ("heat_v2", +1), "water_raw": ("water_v2", +1), "veg_raw": ("veg_v2", -1),
           "pollution_raw": ("pollution_v2", +1), "exposure_raw": ("exposure_v2", +1)}

def fit_baseline(ref: pd.DataFrame, lo=0.02, hi=0.98) -> dict:
    return {c: {"lo": float(ref[c].quantile(lo)), "hi": float(ref[c].quantile(hi))} for c in RAW_MAP}

def apply_baseline(df: pd.DataFrame, base: dict) -> pd.DataFrame:
    out = df.copy()
    for raw, (name, sign) in RAW_MAP.items():
        z = ((df[raw] - base[raw]["lo"]) / (base[raw]["hi"] - base[raw]["lo"])).clip(0, 1)
        out[name] = z if sign > 0 else 1 - z
    return out
```

```python
# diagnostics.py: two-way additive variance decomposition on a balanced panel
def variance_shares(df, col, hexc="h3_index", datec="date"):
    mu = df[col].mean(); tot = ((df[col] - mu) ** 2).sum()
    m = df.groupby(datec)[col].agg(["mean", "size"]); h = df.groupby(hexc)[col].agg(["mean", "size"])
    sm = (m["size"] * (m["mean"] - mu) ** 2).sum() / tot
    sh = (h["size"] * (h["mean"] - mu) ** 2).sum() / tot
    return {"between_month": float(sm), "between_hex": float(sh), "residual": float(1 - sm - sh)}
```

**Instructions**
1. Implement the two functions in `indices.py`. Baseline fitting happens only in `run_v2.py --stage fit` (Step 08). Here, test with a baseline fitted on the Mumbai panel.
2. `step6_diagnostics.py <city>`: print variance shares for **v1 sub-indices** (from `final/`) and **v2 indices** side by side, plus the **monthly-mean spread** (`max − min` of monthly means) per index.
3. Save to `results/diagnostics_variance.json`.

**Reference values from the earlier Mumbai dry run (indicative, yours may differ):**

| index (v2) | between-month | between-hex | residual | monthly-mean spread |
|---|---|---|---|---|
| heat | 0.51 | 0.37 | 0.12 | 0.36 |
| water | 0.995 | 0.001 | 0.004 | 0.88 |
| veg | 0.23 | 0.61 | 0.15 | 0.14 |
| pollution | 0.96 | 0.03 | 0.005 | 0.73 |
| exposure | 0.00 | 1.00 | 0.00 | 0.00 |

**What this table already tells you (write it into `limitations.md` in Step 15):** water and pollution are almost purely *city-wide monthly signals*. They contribute time variation but essentially no spatial discrimination. Spatial ranking of hexes is carried by heat, vegetation and exposure.

**Acceptance**
- [ ] All indices within [0, 1].
- [ ] `heat_v2` monthly-mean spread > 0.15 (v1 was ≈0 by construction).
- [ ] Fraction of values exactly 0 or exactly 1 is < 5 % per index (checks the quantile bounds aren't clipping).
- [ ] `pytest tests/test_indices.py`: (a) monotonic in raw; (b) veg inverted; (c) applying a baseline fitted elsewhere leaves a city's monthly means unchanged by city-specific data.

---

# STEP 07 — Weighting schemes and the decision memo

**Goal.** Fit four schemes on the pooled reference panel and decide which one is primary, with a written reason.
**Files:** `src/v2/weighting.py`, `scripts/step7_weights.py`, `docs/weighting_decision.md`, `tests/test_weighting.py`

```python
import numpy as np, pandas as pd

def w_equal(X): return pd.Series(1 / X.shape[1], index=X.columns)

def w_ewm(X, eps=1e-12):                      # entropy weight method
    P = (X + eps) / (X + eps).sum()
    e = -(P * np.log(P)).sum() / np.log(len(X)); d = 1 - e
    return d / d.sum()

def w_critic(X):                              # std × (1 − correlation) conflict
    s = X.std(ddof=0); r = X.corr().fillna(0); c = s * (1 - r).sum()
    return c / c.sum()

def w_pca(X):                                 # |PC1 loadings|, returns (weights, PC1 explained variance)
    Z = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    _, S, Vt = np.linalg.svd(Z.values, full_matrices=False)
    l = np.abs(Vt[0]); return pd.Series(l / l.sum(), index=X.columns), float(S[0] ** 2 / (S ** 2).sum())

def composite(df, w): return (df[list(w.index)] * w).sum(axis=1)
```

**Instructions**
1. Fit all four on the pooled **reference panel** indices (`IDX_COLS`), all months.
2. Save weights, PC1 explained variance, and the **pairwise Spearman matrix** of the five indices to `results/weights_preview.json`.
3. Rank agreement between schemes is computed in Step 10. Here only report weights.
4. Write `docs/weighting_decision.md` using this decision rule:
   - **Primary = `equal`** unless there is a stated, defensible reason otherwise.
   - Reasons to document: (i) EWM and CRITIC reward dispersion, and water/pollution have the largest dispersion only because of city-wide monthly swings; (ii) PC1 explains well under half the variance (≈0.41 in the dry run), so PC1 loadings are a weak summary; (iii) exposure is time-invariant, which distorts any dispersion-based scheme; (iv) equal weights are the easiest to defend in a viva.
   - EWM, CRITIC and PCA are reported as **sensitivity alternatives**, not hidden.
5. Set `config.yml → v2.primary_scheme`.

**Dry-run reference (indicative; extra reference cities in that run were synthetic copies of Mumbai):**

| | equal | EWM | CRITIC | PCA |
|---|---|---|---|---|
| heat | 0.20 | 0.12 | 0.15 | 0.24 |
| water | 0.20 | 0.25 | 0.24 | 0.26 |
| veg | 0.20 | 0.08 | 0.16 | 0.17 |
| pollution | 0.20 | 0.34 | 0.25 | 0.21 |
| exposure | 0.20 | 0.21 | 0.21 | 0.12 |

Pairwise Spearman worth flagging: **water–pollution ≈ 0.67**. Both follow the monsoon, so the composite counts the monsoon twice. Step 10 tests this by dropping each index.

**Acceptance**
- [ ] Each weight vector sums to 1 (±1e-9) and is non-negative.
- [ ] No weight > 0.5 (flag it in the report if so).
- [ ] `weighting_decision.md` states primary scheme and ≥3 reasons.

---

# STEP 08 — Compound term, SSI v2, bands, and the fit/score runner

**Goal.** Build the final index and the one canonical pipeline: `fit` once, `score` every city.
**Files:** `src/v2/ssi.py`, `run_v2.py`, `tests/test_ssi.py`, `tests/test_pipeline.py`

**Design changes from v1**
- **Compound trigger** Ω = 1 when *both* indices in `compound.pair` are at or above their pooled-reference `q`-quantile. Default `q = 0.90`. The 75th percentile is **not** a standard extreme threshold (typical extremes use the 90th/95th); 0.75 is kept only as a sensitivity setting.
- **γ is a parameter, not a finding.** Default 0.30; swept in Step 10. Do not cite any paper as justifying a 30 % amplification.
- **No hard clip.** `ssi_v2 = ssi_lin + γ·Ω·(1 − ssi_lin)` stays inside [0, 1] smoothly, so the v1 `min(1, …)` artifact disappears.
- **Bands** are pooled-reference quantiles (25/50/75). They are *relative* labels (≈25 % of reference hex-months per band by construction). Say so wherever bands appear.

```python
import numpy as np, pandas as pd

def fit_compound(ref, pair=("heat_v2", "pollution_v2"), q=0.90):
    return {c: float(ref[c].quantile(q)) for c in pair}

def apply_ssi(df, w, thr, gamma=0.30):
    out = df.copy()
    out["ssi_lin_v2"] = (df[list(w.index)] * w).sum(axis=1)
    out["omega_v2"] = np.logical_and.reduce([df[c] >= t for c, t in thr.items()]).astype(int)
    out["ssi_v2"] = out.ssi_lin_v2 + gamma * out.omega_v2 * (1 - out.ssi_lin_v2)
    return out

def fit_cuts(ref_ssi, qs=(0.25, 0.5, 0.75)): return [float(ref_ssi.quantile(q)) for q in qs]
def band(s, cuts, labels=("Low", "Moderate", "High", "Extreme")):
    return pd.cut(s, [-np.inf, *cuts, np.inf], labels=list(labels))
```

**`run_v2.py` contract**

`--stage fit`
1. Load `v2_raw` for `reference_cities`, concatenate.
2. `fit_baseline` → `apply_baseline` → fit four weight schemes → `fit_compound` (primary scheme) → `fit_cuts`.
3. Write `results/fit_parameters.json` with keys: `baseline`, `weights` (all schemes), `primary_scheme`, `primary_weights`, `pc1_explained`, `compound` (`pair`, `q`, `gamma`, `thresholds`), `band_cuts`, `reference_cities`, plus `_meta` from `save_result`.

`--stage score --city <name|all>`
1. Load **frozen** params (never refit).
2. Write `data/h3_panel/v2/{city}.parquet` with: keys, raw columns, `IDX_COLS`, `ssi_lin_<scheme>` for every scheme (so Step 13 needs no refit), `ssi_lin_v2`, `omega_v2`, `ssi_v2`, `ssi_band_v2`, `is_imputed`.
3. Print `[score] city: shape, NaN ssi_v2 = 0`.

**Acceptance**
- [ ] `python run_v2.py --stage fit && python run_v2.py --stage score --city all` runs clean.
- [ ] `python -m audit.schema_check` prints `ok=True` for every city (this is where Step 03's check finally passes).
- [ ] `0 ≤ ssi_v2 ≤ 1`; `ssi_v2 ≥ ssi_lin_v2` everywhere; equality exactly where `omega_v2 == 0`.
- [ ] **Compound share `mean(omega_v2)` is between 0.02 and 0.40.** If 0 or > 0.5, there is a threshold or alignment bug. **STOP** (with q = 0.90 and two indices, independence would give ≈1 %; a real heat–pollution co-seasonality gives more; 0 means they never co-occur and you must report that honestly).
- [ ] Band shares on the reference pool are ≈25 % each (±1 pp).
- [ ] **Determinism:** run `score` twice → `pd.read_parquet(a).equals(pd.read_parquet(b))`.
- [ ] No `ctest*` city appears anywhere in `config.yml`, `fit_parameters.json`, or `data/`.

---

# STEP 09 — v1 vs v2 comparison (and fix the broken script)

**Goal.** Show exactly what changed and why, with numbers.
**Files:** `src/analysis/run_compare.py` (replaces `scripts/step7_compare.py`), `tests/test_compare.py`

**Known bug to fix.** The old script crashed with `'DataFrameGroupBy' object has no attribute 'ssi_value'… Did you mean: 'ssi_value_x'?`. A merge produced duplicate `ssi_value` columns. **Cause:** both frames carried the same column name.
**Fix:** select keys + one column from each side and rename *before* merging; assert no `_x/_y` columns afterwards.

```python
v1 = pd.read_parquet(f"{p['v1']}/{city}.parquet")[["h3_index", "date", "ssi_value"]].rename(columns={"ssi_value": "ssi_v1"})
v2 = pd.read_parquet(f"{p['v2']}/{city}.parquet")[["h3_index", "date", "ssi_v2"]]
m = v2.merge(v1, on=["h3_index", "date"], how="inner", validate="one_to_one")
assert not any(c.endswith(("_x", "_y")) for c in m.columns)
```

**Metrics per city (saved via `save_result("compare_<city>", …)`)**
- Spearman and Kendall on **hex-means** (spatial ranking).
- Mean within-month Spearman (average over dates).
- Pooled Spearman, reported **only with the caveat** that pooled ranks are dominated by month effects.
- Top-decile hex overlap (Jaccard).
- Mean SSI shift (v2 − v1) and its monthly profile.
- Table of the 20 hexes with the largest rank change, with their raw driver values.
- Variance shares for `ssi_v1` vs `ssi_v2`.

**Acceptance**
- [ ] Script runs for every city with a v1 panel.
- [ ] Merge row count equals the v2 row count (report any loss).
- [ ] `test_compare.py` fails if suffix columns appear.

---

# STEP 10 — Sensitivity and robustness

**Goal.** Replace the weak Monte-Carlo test with tests that can actually fail.
**Files:** `src/analysis/run_sensitivity.py`, `tests/test_sensitivity.py`

**Why the old test was weak.** Jittering near-equal weights by ±20 % gives ρ ≈ 0.999 almost by construction. The audit found ρ ≈ 0.47 when you swap *schemes*. That is the informative comparison.

**Experiments** (reference = primary scheme, γ = 0.30, q = 0.90):

| id | what varies | values |
|---|---|---|
| S1 | weighting scheme | equal, EWM, CRITIC, PCA |
| S2 | γ | 0.1, 0.2, 0.3, 0.4, 0.5 |
| S3 | q | 0.75, 0.90 (also 0.95 as an extra row) |
| S4 | leave-one-index-out | drop each of 5 indices, renormalise weights |
| S5 | baseline bounds | (0.01, 0.99), (0.02, 0.98), (0.05, 0.95): refit baseline each time |

For S2/S3 **refit the compound thresholds** for each q. For S5 re-run the whole fit.

```python
import itertools, numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau

def rank_agreement(df, a, b, hexc="h3_index", datec="date"):
    hm = df.groupby(hexc)[[a, b]].mean()
    wm = [spearmanr(g[a], g[b])[0] for _, g in df.groupby(datec) if g[a].nunique() > 1 and g[b].nunique() > 1]
    k = max(1, int(0.1 * len(hm))); ta, tb = set(hm[a].nlargest(k).index), set(hm[b].nlargest(k).index)
    return {"rho_hexmean": float(spearmanr(hm[a], hm[b])[0]), "tau_hexmean": float(kendalltau(hm[a], hm[b])[0]),
            "rho_withinmonth_mean": float(np.nanmean(wm)), "top_decile_jaccard": len(ta & tb) / len(ta | tb)}

def run_grid(Z, schemes, primary, gammas, qs, pair=("heat_v2", "pollution_v2")):
    def score(w, g, q): return apply_ssi(Z, w, fit_compound(Z, pair, q), g)
    ref = score(schemes[primary], 0.30, 0.90); rows = []
    for s, g, q in itertools.product(schemes, gammas, qs):
        S = score(schemes[s], g, q)
        T = ref[["h3_index", "date", "ssi_v2"]].assign(alt=S.ssi_v2.values)
        rows.append({"scheme": s, "gamma": g, "q": q, **rank_agreement(T, "ssi_v2", "alt"),
                     "omega_share": float(S.omega_v2.mean()), "mean_ssi": float(S.ssi_v2.mean())})
    for c in IDX_COLS:                                           # S4
        w = schemes[primary].drop(c); w = w / w.sum(); S = score(w, 0.30, 0.90)
        T = ref[["h3_index", "date", "ssi_v2"]].assign(alt=S.ssi_v2.values)
        rows.append({"scheme": f"drop_{c}", "gamma": 0.30, "q": 0.90, **rank_agreement(T, "ssi_v2", "alt"),
                     "omega_share": float(S.omega_v2.mean()), "mean_ssi": float(S.ssi_v2.mean())})
    return pd.DataFrame(rows)
```

**Reporting rules**
- Report **hex-mean** and **within-month** agreement. Do not headline pooled Spearman.
- Report the **minimum** across each experiment family, not just the average.
- Pre-declare a reading rule and keep it: hex-mean ρ ≥ 0.90 → "stable", 0.70–0.90 → "moderately sensitive", < 0.70 → "sensitive". Print which bucket each family lands in.
- **Expect γ and q to change levels and the compound share much more than ranks.** On synthetic data, γ ∈ [0.1, 0.5] and q ∈ {0.75, 0.90} left hex-mean ρ ≥ 0.998, while swapping to PCA dropped it to ≈0.76. If your real result looks like that, say it plainly: *ranking is robust to γ, q and moves with the weighting scheme and the exposure/vegetation components.*
- Optional: keep the ±20 % jitter, labelled "local perturbation, close to 1 by construction".

**Acceptance**
- [ ] `results/sensitivity.json` + `sensitivity__grid.csv` contain every experiment: 40 rows for scheme × γ × q (4 × 5 × 2), 5 leave-one-out rows, and 3 baseline-bound rows.
- [ ] The reference row (primary, 0.3, 0.9) has ρ = 1.0 against itself (self-consistency test).
- [ ] Summary table in `results/sensitivity_summary.csv`: family → min ρ, min τ, min Jaccard, bucket.

---

# STEP 11 — Validation that can fail

**Goal.** Replace circular checks (vulnerability vs building density, ρ = 0.97) with checks against events and independent data.
**Files:** `docs/validation_hypotheses.md` (**written and committed BEFORE any validation code runs**), `src/analysis/run_validation.py`, `tests/test_validation.py`

**11.1 Pre-registration.** Commit `validation_hypotheses.md` first. For each check state: hypothesis, expected direction, metric, pass criterion. This lets you say in the viva that the criteria were fixed before looking.

**11.2 Checks**

| id | check | metric | notes |
|---|---|---|---|
| V1 | **Lockdown, Apr–May 2020** | `pollution_v2` city mean for Apr–May 2020 vs Apr–May 2022 (and 2021 shown separately) | Expect lower in 2020. **2021 is a poor baseline**: Maharashtra had strict second-wave restrictions in Apr–Jun 2021. CAMS reanalysis uses emission inventories that may not reflect 2020 activity cuts (verify in the EAC4 documentation), so the signal enters only via assimilated observations. A weak or null result is possible and must be reported as is. |
| V2 | **Heatwave, Mar–Apr 2022** | `heat_v2` city mean for Mar–Apr 2022 minus the mean for the same months of 2020–2021; also change in compound share | Single event, so describe, don't attach a p-value. |
| V3 | **Within-month spatial agreement with independent LST** | Spearman of `heat_v2` vs held-out LST per month → mean, min, max, share of months > 0, with block-bootstrap CI | Run **only if** the held-out LST is not an input to `heat_raw`. Otherwise drop V3 and say why. The audit's mean was ≈ 0.17 (range −0.34 to +0.71), so pre-register that you expect a modest value. |
| V4 | **Spatial structure** | Moran's I of hex-mean `ssi_v2` using H3 `grid_disk(h, 1)` neighbours, row-standardised, 999 permutations | Checks that the index is spatially coherent. High I alone does not validate it. |
| V5 | **Exposure against a held-out layer** | Spearman of `exposure_v2` vs a layer **not used** in `exposure_raw` (e.g. an informal-settlement layer or a transit-access layer) | Delete the vulnerability-vs-building-density check from all slides. It is circular. |
| V6 | **Green-space relationships by city** | Spearman of `veg_v2` / green fraction vs `exposure_v2`, reported per city with sign | Mumbai −0.30 vs Coimbatore +0.22 in the audit: report the sign flip. No "protective shield" narrative. |

**11.3 Statistics rules**
- **No naive p-values** on hex-months (they are autocorrelated). Use a **spatial block bootstrap**: blocks = `h3.cell_to_parent(h, res − parent_offset)` (H3 v4 API; older `h3` v3 uses `h3_to_parent`). Resample whole blocks, 500–1000 draws, seeded.
- Report effect sizes with 95 % CIs. A ρ of 0.25 explains ≈ 6 % of variance; write that next to it.
- If V3 is weak, the sentence is "heat_v2 has modest within-month spatial agreement with independent LST", not "validated".

**Acceptance**
- [ ] `validation_hypotheses.md` has a git commit timestamp **earlier** than `run_validation.py`'s first commit (`git log --follow`).
- [ ] `results/validation.json` has V1–V6 each with `hypothesis_met: true | false | not_run (reason)`.
- [ ] Block-bootstrap CI function unit-tested on synthetic autocorrelated data (CI wider than the naive CI).
- [ ] No check in the file uses a variable listed as an input to the index it validates.

---

# STEP 12 — Archetypes: redo as hex-level typology

**Goal.** Fix the archetype slide. The CSV had 6 labels, not 4, and every hex cycled through all 6 across months. Those were **monthly regimes**, not zones a planner can act on.
**Files:** `src/analysis/run_archetypes.py`, `tests/test_archetypes.py`

**Instructions**
1. Features **per hex** (not per hex-month): mean `ssi_v2`; seasonal amplitude (`max − min` of the 12 calendar-month means); mean `heat_v2`; mean `veg_v2`; `exposure_v2`; compound frequency. Standardise (z-score across hexes).
2. KMeans for `k = 2…8` (`n_init=20`, seeded). Compute silhouette per k.
3. **Stability:** 50 bootstrap resamples of hexes → refit → assign all hexes by nearest centroid → Adjusted Rand Index vs the full-data labels. Mean ARI per k.
4. **Selection rule:** highest silhouette among k with mean ARI ≥ 0.70 and smallest cluster ≥ 3 % of hexes. **If no k qualifies, write "no robust typology found" and remove the archetype slide.** Do not force it.
5. Spatial coherence: share of adjacent hex pairs (H3 k = 1) with the same label, against a 500-permutation null.
6. Keep monthly regimes separate. Call them **"temporal regimes"**, report them as a city-month series, never map them as zones.
7. Label clusters by their feature profile (e.g. "high exposure / low green / high heat"), generated from the cluster means in the result file.

**Acceptance**
- [ ] Number of archetypes in the result file equals the number on the slide (checked in Step 14).
- [ ] Each hex has exactly one archetype.
- [ ] `results/archetypes.json` includes silhouette, mean ARI, cluster sizes, coherence statistic, and the null.

---

# STEP 13 — Cross-city comparison (Mumbai ↔ Coimbatore)

**Goal.** Compare cities with the same frozen parameters and sources.
**Files:** `src/analysis/run_crosscity.py`, `tests/test_crosscity.py`

**Instructions**
1. Preconditions: Step 05 done for both cities (same pollution source) and `score` run for both.
2. Per city, table columns: `n_hex, n_months, mean_ssi_v2, mean_ssi_lin_v2, share_compound_triggered, share_extreme_band, var_between_month, var_between_hex, var_residual`, plus the **contribution of each index** to mean SSI (`mean(index) × weight`, normalised).
3. Scheme robustness: for each scheme `s`, city mean of `ssi_lin_<scheme>` (already in the v2 panels). **With only two cities, report whether the city order flips under any scheme.** Kendall τ between city rankings is meaningful only for ≥ 3 cities; skip it otherwise and say so.
4. Band shares are relative to the pooled reference (≈25 % each in aggregate), so "share extreme" differences between cities are meaningful only because the cuts are shared. State this.
5. Side-by-side relationships (V6) with sign and CI per city.
6. Caveats to print: different climates and data availability per city; compound trigger depends on the shared thresholds.

**Acceptance**
- [ ] `results/crosscity.json` + `crosscity__table.csv`.
- [ ] The test asserts that the parameters used are byte-identical to `fit_parameters.json` for every city (no per-city refit).

---

# STEP 14 — Figures, claims ledger, wording lint, dashboard regeneration

**Goal.** Everything shown is generated from `results/`, and every claim is traceable.
**Files:** `src/analysis/run_figures.py`, `scripts/check_claims.py`, `scripts/lint_wording.py`, `results/claims_ledger.csv`

**14.1 Figures (PNG + SVG, 300 dpi, same palette, axis labels with units)**

| id | content | source |
|---|---|---|
| F1 | Variance shares v1 vs v2 (stacked bars per index) | Step 06 |
| F2 | Calendar-month profile of each v2 index (shows seasonality now exists) | v2 panels |
| F3 | Weights by scheme + rank-agreement matrix | Steps 07, 10 |
| F4 | γ × q sensitivity heatmap (ρ and compound share) | Step 10 |
| F5 | Map: hex-mean `ssi_v2` with bands | v2 panel |
| F6 | Event checks V1/V2 (monthly series with the event window shaded) | Step 11 |
| F7 | Archetype map + feature profiles | Step 12 |
| F8 | Cross-city table plot | Step 13 |

**14.2 Claims ledger.** `results/claims_ledger.csv` with columns: `claim_id, statement, number, unit, source_file, json_key, script, status`. `status` ∈ `reproduced | weakened | dropped`. Every number on any slide must appear here. `check_claims.py` fails if a slide/dashboard number is not in the ledger, or if a ledger `number` differs from the value read live from `source_file[json_key]`.

**14.3 Wording lint.** `lint_wording.py` scans slides, dashboard text and docs for the Global-rules G10 list, plus `standard threshold` and `validated` (the latter allowed only if the sentence cites a ledger id). Exit non-zero on any hit. Remove the "100 % verified / zero-hallucination guarantee" header everywhere.

**14.4 Dashboard.** Rebuild from `data/h3_panel/v2/` and `results/` only (no v1 files). Add a footer with the git SHA, `fit_parameters.json` hash, and build date. Add a visible "Limitations" panel linked to `docs/limitations.md`.

**Acceptance**
- [ ] All eight figures exist, named `F1_…` to `F8_…`.
- [ ] `python scripts/check_claims.py` and `python scripts/lint_wording.py` exit 0.
- [ ] `grep -r "archive/v1\|data/h3_panel/final" src dashboard` finds nothing except `run_compare.py`.

---

# STEP 15 — Defense package

**Goal.** A defensible, honest talk and a reproducible repo. A paper draft is out of scope for now.
**Files:** `docs/limitations.md`, `slides/` (or your deck source), `docs/viva_qa.md`, `Makefile`

**15.1 `docs/limitations.md`.** One short paragraph each, with a pointer to evidence:
1. Pollution is a city-month value (CAMS ≈ 0.75° grid), so it adds no spatial discrimination.
2. Water stress is also almost entirely a city-wide monthly signal (between-month share ≈ 0.99).
3. Exposure inputs are static (time-invariant).
4. November 2022 is missing and handled as stated in the data dictionary.
5. Heat vs independent LST agreement is modest (within-month ρ ≈ 0.17 on average in the audit).
6. γ and q are modelling choices; the sensitivity table shows their effect on levels and ranks.
7. Anomaly flags catch whole months, not hexes.
8. No health-outcome or loss data to validate against.
9. Bands are relative (quantile-based), not absolute risk thresholds.
10. Two cities: no cross-city ranking statistics.

**15.2 Slide structure** (your 11 slides + the upfront limitations slide you were told to add; slides 9–10 rebuilt):

| # | slide | evidence |
|---|---|---|
| 1 | Question and scope | n/a |
| 2 | **Limitations and what this study does not claim** (upfront) | `limitations.md` |
| 3 | Data and drivers (what varies in space vs time) | F1, data dictionary |
| 4 | Index construction: one global baseline | F2 |
| 5 | Weighting: four schemes, one primary, why | F3, `weighting_decision.md` |
| 6 | Compound term: γ and q as parameters | F4 |
| 7 | What changed v1 → v2 | Step 09 |
| 8 | Sensitivity and robustness | F3, F4 |
| 9 | **Validation (rebuilt):** events, within-month LST, held-out layer | F6, `validation.json` |
| 10 | **Spatial results and typology (rebuilt)** | F5, F7 |
| 11 | Cross-city and conclusions | F8 |
| 12 | Future work (spatially resolved PM2.5, health-outcome validation, more cities) | n/a |

**15.3 Viva Q&A (`docs/viva_qa.md`)**: write each answer as *claim → evidence file → limitation*. Fill the numbers from `results/`, never from memory.

| Likely question | Answer skeleton |
|---|---|
| Where do your weights come from, and why not EWM? | Four schemes fitted on the pooled reference. Primary is equal because dispersion-based schemes reward city-wide monthly swings in water/pollution. Rank agreement between schemes: `{sensitivity_summary}`. |
| Your v1 heat/water show no seasonality. | Correct: per-month normalization removed it. v2 uses one frozen pooled baseline. Monthly-mean spread went from ≈0 to `{F2/diagnostics}`. |
| Why is vulnerability vs building density a validation? | It isn't; it was circular and was removed. Replaced by V1–V6. |
| Why γ = 0.3 and the 75th percentile? | They were arbitrary. Current defaults are γ = 0.3, q = 0.90; swept over γ 0.1–0.5, q 0.75/0.90/0.95. Effect on rank: `{S2,S3}`. Effect on levels: `{omega_share}`. |
| Is the SSI validated? | Evidence is partial: event checks `{V1,V2}`, modest within-month LST agreement `{V3}`, held-out exposure layer `{V5}`. Not validated against outcomes. |
| Why does the green-space correlation flip sign between cities? | Reported as is: Mumbai `{ρ}`, Coimbatore `{ρ}`. I make no protective-effect claim. |
| How many archetypes, and are they actionable? | `{k}` hex-level archetypes (stability ARI `{x}`) or "no robust typology". Monthly regimes are a separate temporal result, not zones. |

**15.4 Rehearsal checklist**
- [ ] Deliver slides 2, 5, 9 aloud in under 3 min each.
- [ ] Practice the two hardest answers: *"is it validated?"* and *"why equal weights?"*.
- [ ] Have `results/claims_ledger.csv` open during the talk.

**15.5 Reproducibility.** `Makefile` target `reproduce`:
```
python run_v2.py --stage fit
python run_v2.py --stage score --city all
python -m audit.schema_check
python -m src.analysis.run_compare && python -m src.analysis.run_sensitivity
python -m src.analysis.run_validation && python -m src.analysis.run_archetypes
python -m src.analysis.run_crosscity --cities mumbai coimbatore
python -m src.analysis.run_figures && python scripts/check_claims.py && python scripts/lint_wording.py
pytest -q
```
Tag the result `v2-final`.

**Acceptance**
- [ ] `make reproduce` finishes from a clean checkout with exit 0.
- [ ] Every sentence on slide 2 maps to a line in `limitations.md`.
- [ ] `docs/viva_qa.md` has no unfilled `{…}` placeholder.

---

## Appendix A. Suggested 2-day schedule

| Day | Steps | Gate at end of day |
|---|---|---|
| **Day 1** | 02 → 11 | `make reproduce` runs through Step 11; `validation.json` exists |
| **Day 2** | 12 → 15 | Slides rebuilt, ledger and lint pass, rehearsal done |

If Step 02 shows the v1 CSV came from different code than assumed, or Step 04 shows raw drivers can't be recovered, **Day 1 becomes a rebuild**. Stop and tell me; don't improvise.

## Appendix B. Things I could not verify

- Real column names and paths, which come from your chat logs. Step 02's name map settles this.
- CAMS dataset id, variable and ADS endpoint, which depend on current Copernicus documentation.
- Whether `heat_raw` derives from the same LST product you'd use for V3.
- Whether the v1 compound trigger used heat × pollution.
