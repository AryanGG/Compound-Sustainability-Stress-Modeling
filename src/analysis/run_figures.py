"""
src/analysis/run_figures.py
───────────────────────────
Step 14.1: Production-grade figure generator.
Produces 8 publication figures in PNG (300 dpi) and SVG formats:
  - F1_variance_shares: v1 vs v2 variance decomposition
  - F2_seasonality_profiles: 12-month calendar trajectories showing restored physical spread
  - F3_weights_and_correlation: Weights across schemes and inter-indicator correlation
  - F4_gamma_q_sensitivity: Sensitivity heatmap across gamma and q
  - F5_spatial_ssi_bands: Spatial map of hex-mean SSI v2 and risk bands
  - F6_event_validation: Empirical event validation (Lockdown & Heatwave)
  - F7_archetype_profiles: Hex-level archetype spatial typology and cluster profiles
  - F8_crosscity_comparison: Cross-city risk and hazard contribution profile
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import h3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Clean, professional styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
})

PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "accent": "#2ca02c",
    "danger": "#d62728",
    "month": "#3b82f6",
    "hex": "#10b981",
    "res": "#9ca3af",
}

OUT_DIR = Path("figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def save_fig(fig: plt.Figure, name: str) -> None:
    for ext in ["png", "svg"]:
        p = OUT_DIR / f"{name}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Saved {name}.png and .svg")


def generate_f1():
    # F1: Variance Shares v1 vs v2
    with open("results/diagnostics_variance.json") as f:
        diag = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for i, city in enumerate(["mumbai", "coimbatore"]):
        ax = axes[i]
        c_diag = diag.get(city, {})
        dims = ["heat", "water", "veg", "pollution", "exposure"]

        v2_m = [c_diag[d]["v2_variance"]["between_month"] * 100 for d in dims]
        v2_h = [c_diag[d]["v2_variance"]["between_hex"] * 100 for d in dims]
        v2_r = [c_diag[d]["v2_variance"]["residual"] * 100 for d in dims]

        x = np.arange(len(dims))
        width = 0.55

        ax.bar(x, v2_m, width, label="Between-Month (Temporal)", color=PALETTE["month"])
        ax.bar(x, v2_h, width, bottom=v2_m, label="Between-Hex (Spatial)", color=PALETTE["hex"])
        ax.bar(x, v2_r, width, bottom=np.array(v2_m) + np.array(v2_h), label="Residual Spatio-Temporal", color=PALETTE["res"])

        ax.set_title(f"{city.capitalize()} (SSI v2 Variance Shares)")
        ax.set_xticks(x)
        ax.set_xticklabels([d.capitalize() for d in dims])
        ax.set_ylabel("Share of Total Variance (%)")
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        if i == 0:
            ax.legend(loc="upper right")

    fig.suptitle("F1: Two-Way Variance Decomposition of v2 Indicators", y=1.02)
    save_fig(fig, "F1_variance_shares")


def generate_f2():
    # F2: Calendar-Month Profiles
    mumbai = pd.read_parquet("data/h3_panel/v2/mumbai.parquet")
    coimbatore = pd.read_parquet("data/h3_panel/v2/coimbatore.parquet")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    dims = [("heat_v2", "Heat"), ("water_v2", "Water Deficit"), ("veg_v2", "Veg Loss"), ("pollution_v2", "Pollution")]

    for i, (city, df) in enumerate([("Mumbai", mumbai), ("Coimbatore", coimbatore)]):
        ax = axes[i]
        df["_m"] = pd.to_datetime(df["date"]).dt.month
        month_means = df.groupby("_m")[[d[0] for d in dims]].mean()

        for col, label in dims:
            ax.plot(month_means.index, month_means[col], marker="o", linewidth=2, label=label)

        ax.set_title(f"{city} (Seasonality Preserved)")
        ax.set_xlabel("Calendar Month")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        ax.set_ylabel("Index Value [0, 1]")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, linestyle="--", alpha=0.5)
        if i == 0:
            ax.legend(loc="upper left")

    fig.suptitle("F2: 12-Month Calendar Trajectories of v2 Stress Dimensions", y=1.02)
    save_fig(fig, "F2_seasonality_profiles")


def generate_f3():
    # F3: Weights by scheme + correlation matrix
    with open("results/weights_preview.json") as f:
        meta = json.load(f)

    weights_df = pd.DataFrame(meta["weights"])
    spearman_df = pd.DataFrame(meta["spearman_matrix"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    weights_df.plot(kind="bar", ax=ax1, width=0.8, colormap="viridis")
    ax1.set_title("Weights Across Alternative Schemes")
    ax1.set_ylabel("Weight Fraction")
    ax1.set_xticklabels([c.replace("_v2", "").capitalize() for c in weights_df.index], rotation=0)
    ax1.axhline(0.20, color="red", linestyle=":", label="Equal (0.20)")
    ax1.legend(loc="upper right")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    sns.heatmap(spearman_df, annot=True, fmt=".2f", cmap="coolwarm", vmin=-0.5, vmax=1.0, ax=ax2, cbar_kws={"label": "Spearman ρ"})
    ax2.set_title("Pairwise Indicator Correlation (Pooled Reference)")
    ax2.set_xticklabels([c.replace("_v2", "").capitalize() for c in spearman_df.columns], rotation=45)
    ax2.set_yticklabels([c.replace("_v2", "").capitalize() for c in spearman_df.index], rotation=0)

    fig.suptitle("F3: Weighting Scheme Allocations and Inter-Indicator Coupling", y=1.02)
    save_fig(fig, "F3_weights_and_correlation")


def generate_f4():
    # F4: Gamma x q sensitivity
    grid_df = pd.read_csv("results/sensitivity__grid.csv")
    s_sub = grid_df[grid_df["scheme"] == "equal"]

    pivot_rho = s_sub.pivot_table(index="gamma", columns="q", values="rho_hexmean")
    pivot_omega = s_sub.pivot_table(index="gamma", columns="q", values="omega_share")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    sns.heatmap(pivot_rho, annot=True, fmt=".4f", cmap="YlGn", vmin=0.98, vmax=1.0, ax=ax1, cbar_kws={"label": "Spatial Rank ρ"})
    ax1.set_title("Rank Agreement (ρ vs. Baseline γ=0.3, q=0.9)")
    ax1.set_xlabel("Compound Quantile Threshold q")
    ax1.set_ylabel("Coupling Parameter γ")

    sns.heatmap(pivot_omega * 100, annot=True, fmt=".2f", cmap="Blues", ax=ax2, cbar_kws={"label": "Compound Activation (%)"})
    ax2.set_title("Compound Risk Trigger Share (%)")
    ax2.set_xlabel("Compound Quantile Threshold q")
    ax2.set_ylabel("Coupling Parameter γ")

    fig.suptitle("F4: Sensitivity of Composite Stress to Joint-Tail Coupling Parameters", y=1.02)
    save_fig(fig, "F4_gamma_q_sensitivity")


def generate_f5():
    # F5: Spatial map: hex-mean ssi_v2 with bands
    mumbai = pd.read_parquet("data/h3_panel/v2/mumbai.parquet")
    coimbatore = pd.read_parquet("data/h3_panel/v2/coimbatore.parquet")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for i, (city, df) in enumerate([("Mumbai", mumbai), ("Coimbatore", coimbatore)]):
        ax = axes[i]
        hex_summary = df.groupby("h3_index").agg(
            lat=("latitude", "first") if "latitude" in df.columns else ("h3_index", lambda h: h3.cell_to_latlng(h.iloc[0])[0]),
            lng=("longitude", "first") if "longitude" in df.columns else ("h3_index", lambda h: h3.cell_to_latlng(h.iloc[0])[1]),
            ssi=("ssi_v2", "mean"),
        )
        sc = ax.scatter(hex_summary["lng"], hex_summary["lat"], c=hex_summary["ssi"], cmap="Spectral_r", s=25, alpha=0.9, vmin=0.1, vmax=0.8)
        ax.set_title(f"{city} (Hex-Mean SSI v2)")
        ax.set_xlabel("Longitude (°E)")
        ax.set_ylabel("Latitude (°N)")
        plt.colorbar(sc, ax=ax, label="Mean SSI Score")
        ax.grid(True, linestyle=":", alpha=0.4)

    fig.suptitle("F5: Spatial Distribution of Compound Sustainability Stress (SSI v2)", y=1.02)
    save_fig(fig, "F5_spatial_ssi_bands")


def generate_f6():
    # F6: Event checks V1 / V2
    mumbai = pd.read_parquet("data/h3_panel/v2/mumbai.parquet")
    mumbai["date_dt"] = pd.to_datetime(mumbai["date"])
    monthly = mumbai.groupby("date_dt")[["pollution_v2", "heat_v2"]].mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)

    # V1: Lockdown PM2.5
    ax1.plot(monthly.index, monthly["pollution_v2"], color=PALETTE["danger"], linewidth=2, label="Pollution Index (v2)")
    ax1.axvspan(pd.Timestamp("2020-03-24"), pd.Timestamp("2020-05-31"), color="blue", alpha=0.2, label="National Lockdown (Apr-May 2020)")
    ax1.axvspan(pd.Timestamp("2022-04-01"), pd.Timestamp("2022-05-31"), color="gray", alpha=0.2, label="Comparison Period (Apr-May 2022)")
    ax1.set_title("V1 Benchmark: National COVID-19 Lockdown (Mumbai Air Quality)")
    ax1.set_ylabel("Pollution Index [0, 1]")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle="--", alpha=0.4)

    # V2: Heatwave 2022
    ax2.plot(monthly.index, monthly["heat_v2"], color=PALETTE["secondary"], linewidth=2, label="Heat Stress Index (v2)")
    ax2.axvspan(pd.Timestamp("2022-03-01"), pd.Timestamp("2022-04-30"), color="red", alpha=0.2, label="Record Heatwave (Mar-Apr 2022)")
    ax2.set_title("V2 Benchmark: Western India Early Summer Heatwave")
    ax2.set_xlabel("Observation Month")
    ax2.set_ylabel("Heat Index [0, 1]")
    ax2.legend(loc="upper left")
    ax2.grid(True, linestyle="--", alpha=0.4)

    fig.suptitle("F6: Empirical Event Benchmarks and Diagnostic Validity", y=1.02)
    save_fig(fig, "F6_event_validation")


def generate_f7():
    # F7: Archetypes map and profiles
    with open("results/archetypes.json") as f:
        meta = json.load(f)

    assignments = pd.read_csv("results/archetypes__hex_assignments.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

    # Profiles
    feat_cols = ["mean_ssi", "seasonal_amplitude", "mean_heat", "mean_veg", "mean_exposure", "compound_freq"]
    cluster_means = assignments.groupby("archetype_id")[feat_cols].mean()

    cluster_means.T.plot(kind="bar", ax=ax1, colormap="tab10", width=0.7)
    ax1.set_title("Archetype Cluster Trait Profiles")
    ax1.set_ylabel("Mean Feature Value")
    ax1.set_xticklabels([c.replace("mean_", "").capitalize() for c in feat_cols], rotation=30)
    ax1.legend([meta["cluster_names"][str(k)] for k in cluster_means.index], loc="upper right")
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # Cluster size breakdown
    shares = assignments["archetype_id"].value_counts(normalize=True)
    labels = [meta["cluster_names"][str(k)] for k in shares.index]
    ax2.pie(shares, labels=labels, autopct="%1.1f%%", startangle=140, colors=plt.cm.tab10.colors[:len(shares)])
    ax2.set_title(f"Typology Cluster Distribution (k={meta['optimal_k']})")

    fig.suptitle("F7: Hex-Level Stress Archetype Profiles and Typology", y=1.02)
    save_fig(fig, "F7_archetype_profiles")


def generate_f8():
    # F8: Cross-city comparison
    table_df = pd.read_csv("results/crosscity__table.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Metric comparison
    metrics = ["mean_ssi_v2", "mean_ssi_lin_v2", "share_compound_triggered", "share_extreme_band"]
    plot_df = table_df.set_index("city")[metrics]

    plot_df.T.plot(kind="bar", ax=ax1, width=0.6, color=[PALETTE["primary"], PALETTE["secondary"]])
    ax1.set_title("Cross-City Composite & Compound Stress Metrics")
    ax1.set_ylabel("Score / Share")
    ax1.set_xticklabels(["Final SSI (v2)", "Linear SSI", "Compound Rate (Ω)", "Extreme Band %"], rotation=20)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)
    ax1.legend(["Mumbai", "Coimbatore"])

    # Indicator contributions
    contrib_cols = [c for c in table_df.columns if c.startswith("contrib_")]
    contrib_df = table_df.set_index("city")[contrib_cols]
    contrib_df.columns = [c.replace("contrib_", "").replace("_v2", "").capitalize() for c in contrib_cols]

    contrib_df.T.plot(kind="bar", ax=ax2, width=0.6, color=[PALETTE["primary"], PALETTE["secondary"]])
    ax2.set_title("Normalized Hazard Contribution to Mean SSI")
    ax2.set_ylabel("Contribution Share")
    ax2.set_xticklabels(contrib_df.columns, rotation=20)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    ax2.legend(["Mumbai", "Coimbatore"])

    fig.suptitle("F8: Comparative Multi-Hazard Sustainability Stress Profile", y=1.02)
    save_fig(fig, "F8_crosscity_comparison")


def main():
    print("Generating 8 publication figures in figures/ ...")
    generate_f1()
    generate_f2()
    generate_f3()
    generate_f4()
    generate_f5()
    generate_f6()
    generate_f7()
    generate_f8()
    print("All 8 figures generated successfully.")


if __name__ == "__main__":
    main()
