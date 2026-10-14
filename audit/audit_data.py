"""Step 1 data audit. Read-only. Usage:
python audit/audit_data.py --panel <path.csv|.parquet> --city mumbai --out docs/audit
Writes: <out>/data_audit_<city>.json and <out>/data_audit_<city>.md
"""
import argparse, json, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr

p = argparse.ArgumentParser()
p.add_argument("--panel", required=True)
p.add_argument("--city", required=True)
p.add_argument("--out", default="docs/audit")
a = p.parse_args()
os.makedirs(a.out, exist_ok=True)

df = pd.read_parquet(a.panel) if a.panel.endswith(".parquet") else pd.read_csv(a.panel)
df["date"] = pd.to_datetime(df["date"])
R = {"city": a.city, "file": a.panel}
has = lambda *c: all(x in df.columns for x in c)

# 1. structure
R["shape"] = list(df.shape)
R["columns"] = list(df.columns)
R["date_min"], R["date_max"] = str(df.date.min().date()), str(df.date.max().date())
R["n_months"], R["n_hexes"] = int(df.date.nunique()), int(df.h3_index.nunique())
R["balanced_panel"] = bool(len(df) == R["n_months"] * R["n_hexes"])

# 2. missingness
miss = df.isna().sum()
R["missing_cols"] = {c: int(v) for c, v in miss.items() if v}
R["missing_by_date_top3"] = {
    c: {str(k.date()): int(v) for k, v in df[df[c].isna()].date.value_counts().head(3).items()}
    for c in R["missing_cols"]}

# 3. column structure: constant / static per hex / constant per date
num = df.select_dtypes("number").columns
R["constant_cols"] = [c for c in num if df[c].nunique(dropna=True) <= 1]
R["static_per_hex_cols"] = [c for c in num if df.groupby("h3_index")[c].nunique().max() == 1 and c not in R["constant_cols"]]
R["distinct_per_date_avg"] = {c: round(float(df.groupby("date")[c].nunique().mean()), 1) for c in num}
R["city_scale_cols(<=5 distinct per date)"] = [c for c, v in R["distinct_per_date_avg"].items() if v <= 5]

# 4. index scale diagnostics (detect per-month normalisation)
idx = [c for c in df.columns if c.endswith("_idx")]
R["index_cols"] = idx
R["index_summary"] = {c: {k: round(float(v), 5) for k, v in df[c].describe()[["min", "max", "mean", "std"]].items()} for c in idx}
R["monthly_mean_spread"] = {}
for c in idx:
    mm = df.groupby(df.date.dt.month)[c].mean()
    R["monthly_mean_spread"][c] = round(float(mm.max() - mm.min()), 5)
R["flag_per_month_normalised(spread<0.01)"] = [c for c, v in R["monthly_mean_spread"].items() if v < 0.01 and c not in R["static_per_hex_cols"]]
R["flag_identical_range_indices"] = []
rng = {c: np.array([df[c].min(), df[c].max(), df[c].std()]) for c in idx}
for i, c1 in enumerate(idx):
    for c2 in idx[i + 1:]:
        if np.allclose(rng[c1], rng[c2], atol=1e-3):
            R["flag_identical_range_indices"].append([c1, c2])

# 5. implied linear weights
if has("ssi_linear") and idx:
    d = df.dropna(subset=idx + ["ssi_linear"])
    X = np.c_[d[idx].values, np.ones(len(d))]
    w, res, *_ = np.linalg.lstsq(X, d.ssi_linear.values, rcond=None)
    ss = ((d.ssi_linear - d.ssi_linear.mean()) ** 2).sum()
    R["implied_linear_weights"] = {c: round(float(x), 4) for c, x in zip(idx, w[:-1])}
    R["implied_weights_intercept"] = round(float(w[-1]), 5)
    R["implied_weights_R2"] = round(float(1 - res[0] / ss), 6) if len(res) else None

# 6. compound term
if has("ssi_linear", "omega_compound", "ssi_value"):
    m = df.omega_compound > 0
    R["omega_positive_share"] = round(float(m.mean()), 4)
    R["omega_max"] = round(float(df.omega_compound.max()), 4)
    unclipped = m & (df.ssi_value < 0.9999)
    g = ((df.ssi_value - df.ssi_linear)[unclipped] / df.omega_compound[unclipped])
    R["implied_gamma_median"], R["implied_gamma_std"] = round(float(g.median()), 5), round(float(g.std()), 6)
    R["share_clipped_at_1"] = round(float((df.ssi_value >= 0.9999).mean()), 4)
    R["additive_formula_exact"] = bool(np.allclose(np.minimum(1, df.ssi_linear + g.median() * df.omega_compound), df.ssi_value, atol=1e-6))

# 7. variance decomposition of ssi_value
if "ssi_value" in df:
    tot = df.ssi_value.var()
    vd = df.groupby("date").ssi_value.mean().var() / tot
    vh = df.groupby("h3_index").ssi_value.mean().var() / tot
    R["ssi_var_share"] = {"between_month": round(float(vd), 4), "between_hex": round(float(vh), 4), "hex_x_month_residual": round(float(1 - vd - vh), 4)}

# 8. raw inputs vs indices (Spearman, pooled and within-month mean)
raw = [c for c in ["temp_mean_c", "dewpoint_mean_c", "precip_sum_mm", "wind_speed", "radiation", "soil_moisture", "ndvi", "lst_c", "pm25", "built_up_fraction", "building_density", "green_space_fraction"] if c in df]
R["spearman_pooled_idx_vs_raw"] = {}
for c in idx:
    R["spearman_pooled_idx_vs_raw"][c] = {}
    for r in raw:
        s = df[[c, r]].dropna()
        R["spearman_pooled_idx_vs_raw"][c][r] = round(float(spearmanr(s[c], s[r])[0]), 3)
if has("heat_stress_idx", "lst_c"):
    vals = []
    for _, g in df.groupby("date"):
        s = g[["heat_stress_idx", "lst_c"]].dropna()
        if len(s) > 100:
            vals.append(spearmanr(s.heat_stress_idx, s.lst_c)[0])
    R["heat_vs_lst_within_month"] = {"mean": round(float(np.mean(vals)), 3), "min": round(float(np.min(vals)), 3), "max": round(float(np.max(vals)), 3), "n_months": len(vals)}

# 9. anomaly + archetypes
if "anomaly_flag" in df:
    f = df.groupby("date").anomaly_flag.mean()
    R["anomaly_overall_share"] = round(float(df.anomaly_flag.mean()), 4)
    R["anomaly_top_months"] = {str(k.date()): round(float(v), 3) for k, v in f.sort_values(ascending=False).head(5).items()}
if "archetype_id" in df:
    R["n_archetypes"] = int(df.archetype_id.nunique())
    R["archetypes_per_hex_avg"] = round(float(df.groupby("h3_index").archetype_id.nunique().mean()), 2)

json.dump(R, open(f"{a.out}/data_audit_{a.city}.json", "w"), indent=2, default=str)
with open(f"{a.out}/data_audit_{a.city}.md", "w") as fh:
    fh.write(f"# Data audit: {a.city}\n\n```json\n{json.dumps(R, indent=2, default=str)}\n```\n")
print(f"OK: wrote {a.out}/data_audit_{a.city}.json and .md")
