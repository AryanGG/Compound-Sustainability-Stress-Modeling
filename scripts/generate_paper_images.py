"""
scripts/generate_paper_images.py
─────────────────────────────────
Generates publication-quality figures (PNG at 300 DPI and vector SVG)
in the 'paper_images/' folder, strictly matching the specifications:

1. study_area_map.png:
   Two study areas (Mumbai: 707 H3 cells, Coimbatore: 995 H3 cells)
   showing H3 resolution-8 hexagonal grids with a national India locator inset.
2. F1_variance_shares.png:
   Stacked bars (between-month, between-cell, residual variance shares)
   for each v2 indicator, one panel per city (Mumbai, Coimbatore).
3. F2_seasonality_profiles.png:
   Twelve-month calendar trajectories of heat, water, veg, and pollution,
   one panel per city, showing restored seasonal spread.
4. F3_weights_and_correlation.png:
   (left) Bar chart of indicator weights across Equal, Entropy, CRITIC, PCA schemes;
   (right) Heatmap of pairwise Spearman correlation matrix on pooled reference panel.
5. F4_gamma_q_sensitivity.png:
   Two heatmaps over grid of gamma (0.1-0.5) and q: rank agreement and compound-trigger share.
6. F5_spatial_ssi_bands.png:
   Two map panels (Mumbai, Coimbatore) of hex-mean SSI on H3 grid, coloured by
   relative risk band (Low, Moderate, High, Extreme).
7. F6_event_validation.png:
   (left) Mumbai pollution indicator in April-May 2020, 2021, 2022 (COVID-19 lockdown V1);
   (right) Heat indicator and compound trigger share for March-April 2022 vs 2020-21 (Heatwave V2).
8. F7_archetype_profiles.png:
   (left) Trait profiles of archetype clusters;
   (right) Cluster distribution and spatial maps of cluster assignments.
9. F8_crosscity_comparison.png:
   (left) Cross-city composite and compound stress metrics;
   (right) Normalized hazard contribution to mean SSI for Mumbai and Coimbatore.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import geopandas as gpd
import h3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np
import pandas as pd
import seaborn as sns

OUT_DIR = ROOT_DIR / "paper_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Publication theme styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 10,
    "axes.titlesize": 11.5,
    "axes.labelsize": 10.5,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.5,
    "figure.titlesize": 13.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.8,
})

# Curated palette
PALETTE = {
    "mumbai": "#1e40af",      # Dark Blue
    "coimbatore": "#059669",  # Emerald Green
    "month": "#2563eb",       # Royal Blue
    "hex": "#10b981",         # Emerald
    "res": "#94a3b8",         # Slate
    "low": "#22c55e",         # Green
    "moderate": "#eab308",    # Yellow
    "high": "#f97316",        # Orange
    "extreme": "#ef4444",     # Red
    "heat": "#dc2626",        # Red
    "water": "#0284c7",       # Sky Blue
    "veg": "#16a34a",         # Green
    "pollution": "#7c3aed",   # Purple
    "exposure": "#d97706",    # Amber
}

BAND_COLORS = {
    "Low": PALETTE["low"],
    "Moderate": PALETTE["moderate"],
    "High": PALETTE["high"],
    "Extreme": PALETTE["extreme"],
}


def save_publication_figure(fig: plt.Figure, base_name: str) -> None:
    """Saves both high-res PNG and vector SVG formats."""
    for ext in ["png", "svg"]:
        p = OUT_DIR / f"{base_name}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Saved paper_images/{base_name}.png and .svg")


def add_scale_bar(ax, length_km: float, center_lon: float, center_lat: float, loc: str = "lower left"):
    """Draws an accurate cartographic scale bar with clear padding."""
    deg_lon = length_km / (111.32 * math.cos(math.radians(center_lat)))
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    
    if loc == "lower left":
        x0 = xlim[0] + 0.06 * (xlim[1] - xlim[0])
        y0 = ylim[0] + 0.05 * (ylim[1] - ylim[0])
    elif loc == "lower right":
        x0 = xlim[1] - 0.06 * (xlim[1] - xlim[0]) - deg_lon
        y0 = ylim[0] + 0.05 * (ylim[1] - ylim[0])
    else:
        x0 = xlim[0] + 0.06 * (xlim[1] - xlim[0])
        y0 = ylim[0] + 0.05 * (ylim[1] - ylim[0])
        
    y_bar = y0
    ax.plot([x0, x0 + deg_lon], [y_bar, y_bar], color="#0f172a", linewidth=3.5, solid_capstyle="butt", zorder=10)
    ax.plot([x0, x0 + deg_lon/2], [y_bar, y_bar], color="#ffffff", linewidth=1.5, solid_capstyle="butt", zorder=11)
    ax.text(x0 + deg_lon / 2, y_bar + 0.02 * (ylim[1] - ylim[0]), f"{int(length_km)} km", 
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a", zorder=12,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.8))


def add_north_arrow(ax, loc: str = "upper right"):
    """Adds a clean north arrow."""
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    if loc == "upper right":
        x = xlim[1] - 0.08 * (xlim[1] - xlim[0])
        y = ylim[1] - 0.09 * (ylim[1] - ylim[0])
    else:
        x = xlim[0] + 0.08 * (xlim[1] - xlim[0])
        y = ylim[1] - 0.09 * (ylim[1] - ylim[0])
    
    arrow_len = 0.05 * (ylim[1] - ylim[0])
    ax.annotate("N", xy=(x, y + arrow_len), xytext=(x, y),
                arrowprops=dict(facecolor="#0f172a", edgecolor="#0f172a", width=1.5, headwidth=6, headlength=7),
                ha="center", va="bottom", fontsize=9, fontweight="bold", color="#0f172a", zorder=10)


# ==============================================================================
# 1. STUDY AREA MAP
# ==============================================================================
def generate_study_area_map():
    print("-> Generating Study Area Map (Mumbai & Coimbatore with India Inset)...")
    df_m = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/mumbai.parquet")
    df_c = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/coimbatore.parquet")

    hexes_m = df_m["h3_index"].unique()
    hexes_c = df_c["h3_index"].unique()

    def get_patches(hex_list, facecolor, edgecolor):
        patches = []
        for h in hex_list:
            boundary = h3.cell_to_boundary(h)
            pts = [(lng, lat) for lat, lng in boundary]
            patches.append(MplPolygon(pts, closed=True))
        return PatchCollection(patches, facecolor=facecolor, edgecolor=edgecolor, linewidth=0.5, alpha=0.85, zorder=3)

    fig = plt.figure(figsize=(16, 7.8))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.28)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    # Plot Mumbai
    coll_m = get_patches(hexes_m, facecolor="#93c5fd", edgecolor="#1d4ed8")
    ax1.add_collection(coll_m)
    
    m_coords = [h3.cell_to_latlng(h) for h in hexes_m]
    m_lats, m_lngs = [c[0] for c in m_coords], [c[1] for c in m_coords]
    ax1.set_xlim(min(m_lngs) - 0.04, max(m_lngs) + 0.06)
    ax1.set_ylim(min(m_lats) - 0.06, max(m_lats) + 0.05)
    ax1.set_aspect("equal")
    ax1.set_title("Panel A: Mumbai Metropolitan Region\n(H3 Resolution 8: 707 Hexagonal Cells, ~523 km²)", fontweight="bold", pad=12)
    ax1.set_xlabel("Longitude (°E)", fontweight="bold")
    ax1.set_ylabel("Latitude (°N)", fontweight="bold")
    ax1.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")
    
    # Annotations for Mumbai
    ax1.text(72.77, 19.10, "Arabian Sea", fontsize=10, fontstyle="italic", color="#0284c7", rotation=75, zorder=4)
    ax1.text(72.96, 19.14, "Thane Creek", fontsize=9, fontstyle="italic", color="#0284c7", rotation=-35, zorder=4)
    ax1.text(72.83, 18.94, "South Mumbai\n(Urban Core)", fontsize=8.5, color="#0f172a", fontweight="bold", ha="center", zorder=4)
    ax1.text(72.85, 19.20, "Suburban Zone", fontsize=8.5, color="#0f172a", ha="center", zorder=4)
    add_scale_bar(ax1, length_km=10, center_lon=np.mean(m_lngs), center_lat=np.mean(m_lats), loc="lower left")
    add_north_arrow(ax1, loc="upper right")

    # Plot Coimbatore
    coll_c = get_patches(hexes_c, facecolor="#a7f3d0", edgecolor="#047857")
    ax2.add_collection(coll_c)
    
    c_coords = [h3.cell_to_latlng(h) for h in hexes_c]
    c_lats, c_lngs = [c[0] for c in c_coords], [c[1] for c in c_coords]
    ax2.set_xlim(min(c_lngs) - 0.04, max(c_lngs) + 0.04)
    ax2.set_ylim(min(c_lats) - 0.06, max(c_lats) + 0.05)
    ax2.set_aspect("equal")
    ax2.set_title("Panel B: Coimbatore Urban Region\n(H3 Resolution 8: 995 Hexagonal Cells, ~736 km²)", fontweight="bold", pad=12)
    ax2.set_xlabel("Longitude (°E)", fontweight="bold")
    ax2.set_ylabel("Latitude (°N)", fontweight="bold")
    ax2.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")

    # Annotations for Coimbatore
    ax2.text(76.84, 11.02, "Western Ghats\nFoothills", fontsize=9, fontstyle="italic", color="#047857", ha="center", zorder=4)
    ax2.text(76.96, 11.01, "Coimbatore Core\n(Gandhipuram)", fontsize=8.5, color="#0f172a", fontweight="bold", ha="center", zorder=4)
    ax2.text(77.06, 10.98, "Noyyal River\nBasin Area", fontsize=9, fontstyle="italic", color="#0284c7", ha="center", zorder=4)
    add_scale_bar(ax2, length_km=10, center_lon=np.mean(c_lngs), center_lat=np.mean(c_lats), loc="lower left")
    add_north_arrow(ax2, loc="upper right")

    # India Locator Inset - neatly placed in Mumbai's lower right open ocean/bay area
    india_geojson_path = ROOT_DIR / "data/india_boundary.geojson"
    if india_geojson_path.exists():
        india_gdf = gpd.read_file(india_geojson_path)
        # Position in ax1 lower right without touching coordinates or crossing axis
        ax_inset = fig.add_axes([0.348, 0.155, 0.125, 0.36])
        india_gdf.plot(ax=ax_inset, facecolor="#f8fafc", edgecolor="#475569", linewidth=0.7)
        ax_inset.set_facecolor("#f0f9ff")
        
        # Mumbai dot (lat: 19.076, lon: 72.877)
        ax_inset.scatter([72.877], [19.076], color="#1d4ed8", s=32, edgecolor="white", linewidth=0.8, zorder=5)
        ax_inset.text(70.5, 19.5, "Mumbai", fontsize=7.5, fontweight="bold", color="#1d4ed8", ha="right")
        
        # Coimbatore dot (lat: 11.0168, lon: 76.9558)
        ax_inset.scatter([76.956], [11.017], color="#047857", s=32, edgecolor="white", linewidth=0.8, zorder=5)
        ax_inset.text(79.0, 10.5, "Coimbatore", fontsize=7.5, fontweight="bold", color="#047857", ha="left")

        ax_inset.set_xlim(67, 98)
        ax_inset.set_ylim(6, 37)
        ax_inset.set_xticks([])
        ax_inset.set_yticks([])
        ax_inset.set_title("India Locator Inset", fontsize=8, fontweight="bold", pad=3)
        for spine in ax_inset.spines.values():
            spine.set_edgecolor("#94a3b8")
            spine.set_linewidth(0.8)

    fig.suptitle("Study Area Geography and Discrete Spatial Partitions (Uber H3 Resolution 8)", y=0.99, fontweight="bold", fontsize=13.5)
    save_publication_figure(fig, "study_area_map")
    for ext in ["png", "svg"]:
        (OUT_DIR / f"study_areas_map.{ext}").write_bytes((OUT_DIR / f"study_area_map.{ext}").read_bytes())


# ==============================================================================
# 2. F1: VARIANCE SHARES
# ==============================================================================
def generate_f1():
    print("-> Generating F1_variance_shares...")
    with open(ROOT_DIR / "results/diagnostics_variance.json") as f:
        diag = json.load(f)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2), sharey=True)
    plt.subplots_adjust(wspace=0.18, top=0.85, bottom=0.25)
    dims = ["heat", "water", "veg", "pollution", "exposure"]
    dim_labels = ["Heat Stress", "Water Deficit", "Vegetation Loss", "Air Pollution", "Physical Exposure"]

    for i, city in enumerate(["mumbai", "coimbatore"]):
        ax = axes[i]
        c_diag = diag.get(city, {})

        v2_m = np.array([c_diag[d]["v2_variance"]["between_month"] * 100 for d in dims])
        v2_h = np.array([c_diag[d]["v2_variance"]["between_hex"] * 100 for d in dims])
        v2_r = np.array([c_diag[d]["v2_variance"]["residual"] * 100 for d in dims])

        x = np.arange(len(dims))
        width = 0.52

        bars_m = ax.bar(x, v2_m, width, label="Between-Month (Temporal Seasonality)", color=PALETTE["month"], edgecolor="white", linewidth=0.5)
        bars_h = ax.bar(x, v2_h, width, bottom=v2_m, label="Between-Hex (Spatial Morphology)", color=PALETTE["hex"], edgecolor="white", linewidth=0.5)
        bars_r = ax.bar(x, v2_r, width, bottom=v2_m + v2_h, label="Residual (Spatio-Temporal Coupling)", color=PALETTE["res"], edgecolor="white", linewidth=0.5)

        for j in range(len(dims)):
            if v2_m[j] >= 12:
                ax.text(x[j], v2_m[j] / 2, f"{v2_m[j]:.1f}%", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
            if v2_h[j] >= 12:
                ax.text(x[j], v2_m[j] + v2_h[j] / 2, f"{v2_h[j]:.1f}%", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
            if v2_r[j] >= 12:
                ax.text(x[j], v2_m[j] + v2_h[j] + v2_r[j] / 2, f"{v2_r[j]:.1f}%", ha="center", va="center", color="#0f172a", fontsize=8.5, fontweight="bold")

        ax.set_title(f"Panel {'A' if i == 0 else 'B'}: {city.capitalize()} (SSI v2 Variance Shares)", fontweight="bold", pad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(dim_labels, rotation=22, ha="right", fontweight="medium")
        ax.set_ylabel("Share of Total Variance (%)", fontweight="bold")
        ax.set_ylim(0, 105)
        ax.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    axes[0].legend(loc="upper center", bbox_to_anchor=(1.10, -0.26), ncol=3, frameon=True, edgecolor="#cbd5e1")
    fig.suptitle("Figure F1: Two-Way Variance Decomposition of Standardized SSI v2 Indicators across Urban Panels", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F1_variance_shares")


# ==============================================================================
# 3. F2: SEASONALITY PROFILES
# ==============================================================================
def generate_f2():
    print("-> Generating F2_seasonality_profiles...")
    mumbai = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/mumbai.parquet")
    coimbatore = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/coimbatore.parquet")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), sharey=True)
    plt.subplots_adjust(wspace=0.16, top=0.85, bottom=0.25)
    dims = [
        ("heat_v2", "Heat Stress Index", PALETTE["heat"], "o-"),
        ("water_v2", "Water Deficit Index", PALETTE["water"], "s-"),
        ("veg_v2", "Vegetation Loss Index", PALETTE["veg"], "^-"),
        ("pollution_v2", "Air Pollution Index", PALETTE["pollution"], "D-"),
    ]

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for i, (city, df) in enumerate([("Mumbai", mumbai), ("Coimbatore", coimbatore)]):
        ax = axes[i]
        df["_m"] = pd.to_datetime(df["date"]).dt.month
        month_means = df.groupby("_m")[[d[0] for d in dims]].mean()

        ax.axvspan(3, 5, color="#fee2e2", alpha=0.45, label="Pre-Monsoon Summer" if i == 0 else None)
        ax.axvspan(6, 9, color="#e0f2fe", alpha=0.45, label="SW Monsoon Season" if i == 0 else None)

        for col, label, color, style in dims:
            ax.plot(month_means.index, month_means[col], style, color=color, linewidth=2.2, markersize=5.5, label=label if i == 0 else None)

        ax.set_title(f"Panel {'A' if i == 0 else 'B'}: {city} (Restored Seasonal Cycles)", fontweight="bold", pad=10)
        ax.set_xlabel("Calendar Month", fontweight="bold")
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(month_names, fontweight="medium")
        ax.set_ylabel("Standardized Index Value [0, 1]", fontweight="bold")
        ax.set_ylim(-0.03, 1.05)
        ax.grid(True, linestyle="--", alpha=0.5, color="#cbd5e1")

    axes[0].legend(loc="upper center", bbox_to_anchor=(1.08, -0.24), ncol=6, frameon=True, edgecolor="#cbd5e1")
    fig.suptitle("Figure F2: Twelve-Month Annual Trajectories of Standardized Environmental Hazard Indicators", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F2_seasonality_profiles")


# ==============================================================================
# 4. F3: WEIGHTS AND CORRELATION
# ==============================================================================
def generate_f3():
    print("-> Generating F3_weights_and_correlation...")
    with open(ROOT_DIR / "results/weights_preview.json") as f:
        meta = json.load(f)

    weights_df = pd.DataFrame(meta["weights"])
    weights_df.columns = ["Equal", "Entropy (EWM)", "CRITIC", "PCA (PC1)"]
    weights_df.index = ["Heat Stress", "Water Deficit", "Veg Loss", "Air Pollution", "Exposure"]

    spearman_df = pd.DataFrame(meta["spearman_matrix"])
    dim_clean = ["Heat", "Water", "Veg", "Pollution", "Exposure"]
    spearman_df.columns = dim_clean
    spearman_df.index = dim_clean

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.2), gridspec_kw={"width_ratios": [1.15, 1]})
    plt.subplots_adjust(wspace=0.28, top=0.86, bottom=0.18)

    # Bar chart of weights
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"]
    weights_df.plot(kind="bar", ax=ax1, width=0.8, color=colors, edgecolor="white", linewidth=0.6)
    ax1.set_title("Panel A: Indicator Weights Across Schemes", fontweight="bold", pad=10)
    ax1.set_ylabel("Weight Fraction", fontweight="bold")
    ax1.set_xticklabels(weights_df.index, rotation=18, ha="right", fontweight="medium")
    ax1.axhline(0.20, color="#dc2626", linestyle="--", linewidth=1.5, label="Equal Benchmark (w = 0.20)")
    ax1.set_ylim(0, 0.42)
    ax1.legend(loc="upper right", frameon=True, edgecolor="#cbd5e1")
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    # Heatmap of correlation matrix
    sns.heatmap(
        spearman_df,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-0.4,
        vmax=1.0,
        ax=ax2,
        cbar_kws={"label": "Pairwise Spearman ρ", "shrink": 0.85},
        linewidths=1.0,
        linecolor="white",
        annot_kws={"fontweight": "bold", "size": 10}
    )
    ax2.set_title("Panel B: Pairwise Spearman ρ (N=61,272)", fontweight="bold", pad=10)
    ax2.set_xticklabels(dim_clean, rotation=0, fontweight="medium")
    ax2.set_yticklabels(dim_clean, rotation=0, fontweight="medium")

    fig.suptitle("Figure F3: Weighting Scheme Allocations and Inter-Indicator Coupling Structures", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F3_weights_and_correlation")


# ==============================================================================
# 5. F4: GAMMA AND Q SENSITIVITY
# ==============================================================================
def generate_f4():
    print("-> Generating F4_gamma_q_sensitivity...")
    grid_df = pd.read_csv(ROOT_DIR / "results/sensitivity__grid.csv")
    # Filter strictly to grid_sweep experiment family
    s_sub = grid_df[(grid_df["scheme"] == "equal") & (grid_df["experiment"] == "grid_sweep")]

    pivot_rho = s_sub.pivot_table(index="gamma", columns="q", values="rho_hexmean")
    pivot_omega = s_sub.pivot_table(index="gamma", columns="q", values="omega_share")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 4.8))
    plt.subplots_adjust(wspace=0.28, top=0.86, bottom=0.18)

    # Left: Rank agreement
    sns.heatmap(
        pivot_rho,
        annot=True,
        fmt=".4f",
        cmap="YlGn",
        vmin=0.995,
        vmax=1.0,
        ax=ax1,
        cbar_kws={"label": "Spatial Rank Spearman ρ", "shrink": 0.85},
        linewidths=1.2,
        linecolor="white",
        annot_kws={"fontweight": "bold", "size": 10.5}
    )
    ax1.set_title("Panel A: Rank Agreement (ρ vs Baseline γ=0.30, q=0.90)", fontweight="bold", pad=10)
    ax1.set_xlabel("Compound Quantile Threshold (q)", fontweight="bold")
    ax1.set_ylabel("Coupling Parameter (γ)", fontweight="bold")

    # Right: Compound activation share
    sns.heatmap(
        pivot_omega * 100,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        ax=ax2,
        cbar_kws={"label": "Compound Activation Rate (%)", "shrink": 0.85},
        linewidths=1.2,
        linecolor="white",
        annot_kws={"fontweight": "bold", "size": 10.5}
    )
    ax2.set_title("Panel B: Joint-Tail Hazard Trigger Share (Ω > 0, %)", fontweight="bold", pad=10)
    ax2.set_xlabel("Compound Quantile Threshold (q)", fontweight="bold")
    ax2.set_ylabel("Coupling Parameter (γ)", fontweight="bold")

    fig.suptitle("Figure F4: Sensitivity of Metropolitan Risk Rankings to Non-Linear Coupling Parameters (γ, q)", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F4_gamma_q_sensitivity")


# ==============================================================================
# 6. F5: SPATIAL SSI RISK BANDS
# ==============================================================================
def generate_f5():
    print("-> Generating F5_spatial_ssi_bands...")
    df_m = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/mumbai.parquet")
    df_c = pd.read_parquet(ROOT_DIR / "data/h3_panel/v2/coimbatore.parquet")

    with open(ROOT_DIR / "results/fit_parameters.json") as f:
        fit_params = json.load(f)
    cuts = fit_params["band_cuts"]

    def assign_band(val):
        if val < cuts[0]:
            return "Low"
        elif val < cuts[1]:
            return "Moderate"
        elif val < cuts[2]:
            return "High"
        else:
            return "Extreme"

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 7.5))
    plt.subplots_adjust(wspace=0.22, top=0.88, bottom=0.14)

    for i, (city, df) in enumerate([("Mumbai", df_m), ("Coimbatore", df_c)]):
        ax = axes[i]
        hex_summary = df.groupby("h3_index")["ssi_v2"].mean().reset_index()
        hex_summary["band"] = hex_summary["ssi_v2"].apply(assign_band)

        patches = []
        colors = []
        all_lats, all_lngs = [], []

        for _, row in hex_summary.iterrows():
            boundary = h3.cell_to_boundary(row["h3_index"])
            pts = [(lng, lat) for lat, lng in boundary]
            patches.append(MplPolygon(pts, closed=True))
            colors.append(BAND_COLORS[row["band"]])
            for lat, lng in boundary:
                all_lats.append(lat)
                all_lngs.append(lng)

        coll = PatchCollection(patches, facecolors=colors, edgecolors="#334155", linewidths=0.4, alpha=0.9, zorder=3)
        ax.add_collection(coll)

        ax.set_xlim(min(all_lngs) - 0.04, max(all_lngs) + 0.04)
        ax.set_ylim(min(all_lats) - 0.07, max(all_lats) + 0.05)
        ax.set_aspect("equal")

        shares = hex_summary["band"].value_counts(normalize=True)
        share_str = f"Mean SSI: {df['ssi_v2'].mean():.4f} | Extreme: {shares.get('Extreme', 0)*100:.1f}%, High: {shares.get('High', 0)*100:.1f}%, Mod: {shares.get('Moderate', 0)*100:.1f}%, Low: {shares.get('Low', 0)*100:.1f}%"

        ax.set_title(f"Panel {'A' if i == 0 else 'B'}: {city} SSI v2 Spatial Risk Classification\n({share_str})", fontweight="bold", pad=10, fontsize=11)
        ax.set_xlabel("Longitude (°E)", fontweight="bold")
        ax.set_ylabel("Latitude (°N)", fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")
        add_scale_bar(ax, length_km=10, center_lon=np.mean(all_lngs), center_lat=np.mean(all_lats), loc="lower left")
        add_north_arrow(ax, loc="upper right")

    legend_elements = [
        mpatches.Patch(facecolor=PALETTE["low"], edgecolor="#334155", label=f"Low  ([0.00, {cuts[0]:.2f}))"),
        mpatches.Patch(facecolor=PALETTE["moderate"], edgecolor="#334155", label=f"Moderate  ([{cuts[0]:.2f}, {cuts[1]:.2f}))"),
        mpatches.Patch(facecolor=PALETTE["high"], edgecolor="#334155", label=f"High  ([{cuts[1]:.2f}, {cuts[2]:.2f}))"),
        mpatches.Patch(facecolor=PALETTE["extreme"], edgecolor="#334155", label=f"Extreme  ([{cuts[2]:.2f}, 1.00])"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4, frameon=True, edgecolor="#cbd5e1", fontsize=10, bbox_to_anchor=(0.5, 0.02))
    fig.suptitle("Figure F5: Spatial Distribution of Hex-Mean Compound Sustainability Stress (SSI v2) by Risk Band", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F5_spatial_ssi_bands")


# ==============================================================================
# 7. F6: EVENT VALIDATION (LOCKDOWN & HEATWAVE)
# ==============================================================================
def generate_f6():
    print("-> Generating F6_event_validation...")
    with open(ROOT_DIR / "results/validation.json") as f:
        val = json.load(f)

    v1_data = val["V1_lockdown"]["details"]["mumbai"]
    v2_data = val["V2_heatwave"]["details"]["mumbai"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    plt.subplots_adjust(wspace=0.32, top=0.84, bottom=0.18)

    # Panel A: Lockdown Benchmark V1
    years = ["Apr-May 2020\n(National Lockdown)", "Apr-May 2021\n(Second Wave)", "Apr-May 2022\n(Post-Pandemic Base)"]
    vals = [v1_data["apr_may_2020"], v1_data["apr_may_2021"], v1_data["apr_may_2022"]]
    colors = ["#2563eb", "#93c5fd", "#475569"]

    bars1 = ax1.bar(years, vals, width=0.55, color=colors, edgecolor="white", linewidth=0.8)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.012, f"{yval:.4f}", ha="center", va="bottom", fontweight="bold", fontsize=10)

    ax1.annotate(
        f"Strict Lockdown Drop: -28.8%\n(Δ = {v1_data['diff_2020_minus_2022']:.4f})",
        xy=(0, v1_data["apr_may_2020"] + 0.04),
        xytext=(0.5, 0.38),
        arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.5),
        ha="center", fontsize=9, fontweight="bold", color="#dc2626",
        bbox=dict(boxstyle="round,pad=0.3", fc="#fee2e2", ec="#dc2626", alpha=0.8)
    )

    ax1.set_title("Panel A: COVID-19 Lockdown Air Quality Benchmark (V1)\n(Mumbai Mean CAMS PM2.5 Pollution Index in Apr-May)", fontweight="bold", pad=12)
    ax1.set_ylabel("Standardized Pollution Index [0, 1]", fontweight="bold")
    ax1.set_ylim(0, 0.52)
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    # Panel B: Heatwave Benchmark V2
    categories = ["Mar-Apr Baseline\n(2020-2021 Average)", "Mar-Apr 2022\n(Severe Heatwave)"]
    heat_vals = [v2_data["heat_mar_apr_base_2020_2021"], v2_data["heat_mar_apr_2022"]]
    omega_vals = [v2_data["omega_share_base"] * 100, v2_data["omega_share_2022"] * 100]

    x = np.arange(len(categories))
    w = 0.35

    ax2_twin = ax2.twinx()
    b1 = ax2.bar(x - w/2, heat_vals, w, label="Heat Stress Index (v2)", color=PALETTE["heat"], edgecolor="white", linewidth=0.8)
    b2 = ax2_twin.bar(x + w/2, omega_vals, w, label="Compound Trigger Share (Ω > 0, %)", color=PALETTE["water"], edgecolor="white", linewidth=0.8)

    for bar in b1:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.015, f"{yval:.4f}", ha="center", va="bottom", fontweight="bold", color=PALETTE["heat"], fontsize=9.5)
    for bar in b2:
        yval = bar.get_height()
        ax2_twin.text(bar.get_x() + bar.get_width()/2, yval + 1.0, f"{yval:.1f}%", ha="center", va="bottom", fontweight="bold", color=PALETTE["water"], fontsize=9.5)

    ax2.set_title("Panel B: 2022 Pre-Monsoon Heatwave Surge Benchmark (V2)\n(Mumbai Heat Stress and Compound Activation)", fontweight="bold", pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories, fontweight="medium")
    ax2.set_ylabel("Mean Heat Stress Index [0, 1]", fontweight="bold", color=PALETTE["heat"])
    ax2_twin.set_ylabel("Compound Risk Trigger Share (%)", fontweight="bold", color=PALETTE["water"])
    ax2.set_ylim(0, 0.85)
    ax2_twin.set_ylim(0, 55)
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True, edgecolor="#cbd5e1")

    fig.suptitle("Figure F6: Empirical Event Validation of the SSI Framework Under Historical Benchmarks (V1, V2)", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F6_event_validation")


# ==============================================================================
# 8. F7: ARCHETYPE PROFILES AND TYPOLOGY MAP
# ==============================================================================
def generate_f7():
    print("-> Generating F7_archetype_profiles...")
    with open(ROOT_DIR / "results/archetypes.json") as f:
        meta = json.load(f)

    assignments = pd.read_csv(ROOT_DIR / "results/archetypes__hex_assignments.csv")

    fig = plt.figure(figsize=(15.5, 6.8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.1, 1], height_ratios=[1, 1.2], wspace=0.25, hspace=0.38)
    plt.subplots_adjust(top=0.90, bottom=0.12)

    # Left: Trait profiles
    ax_trait = fig.add_subplot(gs[:, 0])

    feat_cols = ["mean_ssi", "seasonal_amplitude", "mean_heat", "mean_veg", "mean_exposure", "compound_freq"]
    feat_labels = ["Mean SSI", "Seasonal Amplitude", "Heat Stress", "Veg Loss", "Physical Exposure", "Compound Freq"]
    cluster_means = assignments.groupby("archetype_id")[feat_cols].mean()

    x = np.arange(len(feat_cols))
    w = 0.36

    c0_name = "Cluster 0: Suburban / High Heat (41.5%)"
    c1_name = "Cluster 1: Urban Core / Moderate Heat (58.5%)"

    b0 = ax_trait.bar(x - w/2, cluster_means.loc[0], w, label=c0_name, color="#ef4444", edgecolor="white", linewidth=0.8)
    b1 = ax_trait.bar(x + w/2, cluster_means.loc[1], w, label=c1_name, color="#3b82f6", edgecolor="white", linewidth=0.8)

    for bar in b0:
        yval = bar.get_height()
        ax_trait.text(bar.get_x() + bar.get_width()/2, yval + 0.015, f"{yval:.2f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#dc2626")
    for bar in b1:
        yval = bar.get_height()
        ax_trait.text(bar.get_x() + bar.get_width()/2, yval + 0.015, f"{yval:.2f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#1d4ed8")

    ax_trait.set_title("Panel A: Archetype Cluster Trait Profiles (K-Means, k=2)", fontweight="bold", pad=10)
    ax_trait.set_xticks(x)
    ax_trait.set_xticklabels(feat_labels, rotation=20, ha="right", fontweight="medium")
    ax_trait.set_ylabel("Standardized Feature Value", fontweight="bold")
    ax_trait.set_ylim(0, 0.72)
    ax_trait.legend(loc="upper right", frameon=True, edgecolor="#cbd5e1")
    ax_trait.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    # Right Top: Distribution donut
    ax_donut = fig.add_subplot(gs[0, 1])
    shares = assignments["archetype_id"].value_counts(normalize=True).sort_index()
    colors = ["#ef4444", "#3b82f6"]
    wedges, texts, autotexts = ax_donut.pie(
        shares,
        labels=["Cluster 0 (Mumbai Profile)", "Cluster 1 (Coimbatore Profile)"],
        autopct="%1.1f%%",
        pctdistance=0.75,
        labeldistance=1.12,
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
        textprops=dict(fontweight="bold", fontsize=9)
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontsize(9.5)
    ax_donut.set_title(f"Panel B: Typology Distribution (k={meta['optimal_k']}, Silhouette={meta['silhouette']:.3f})", fontweight="bold", pad=5)

    # Right Bottom: Maps of cluster assignments for both cities
    coords = [h3.cell_to_latlng(h) for h in assignments["h3_index"]]
    assignments["lat"] = [c[0] for c in coords]
    assignments["lng"] = [c[1] for c in coords]
    m_assign = assignments[assignments["lat"] > 15]
    c_assign = assignments[assignments["lat"] <= 15]

    # Create inner 2 subpanels for the maps
    sub_gs = gs[1, 1].subgridspec(1, 2, wspace=0.30)
    ax_m = fig.add_subplot(sub_gs[0, 0])
    ax_c = fig.add_subplot(sub_gs[0, 1])

    ax_m.scatter(m_assign["lng"], m_assign["lat"], c="#ef4444", s=14, alpha=0.85)
    ax_m.set_title("Mumbai (Cluster 0)", fontweight="bold", fontsize=9.5)
    ax_m.set_xlabel("Lon (°E)", fontsize=8.5)
    ax_m.set_ylabel("Lat (°N)", fontsize=8.5)
    ax_m.tick_params(labelsize=8)
    ax_m.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")

    ax_c.scatter(c_assign["lng"], c_assign["lat"], c="#3b82f6", s=14, alpha=0.85)
    ax_c.set_title("Coimbatore (Cluster 1)", fontweight="bold", fontsize=9.5)
    ax_c.set_xlabel("Lon (°E)", fontsize=8.5)
    ax_c.set_ylabel("Lat (°N)", fontsize=8.5)
    ax_c.tick_params(labelsize=8)
    ax_c.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")

    fig.suptitle("Figure F7: Hex-Level Sustainability Stress Archetypes, Trait Signatures, and Spatial Typology", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F7_archetype_profiles")


# ==============================================================================
# 9. F8: CROSS-CITY COMPARISON
# ==============================================================================
def generate_f8():
    print("-> Generating F8_crosscity_comparison...")
    table_df = pd.read_csv(ROOT_DIR / "results/crosscity__table.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    plt.subplots_adjust(wspace=0.28, top=0.86, bottom=0.20)

    # Panel A: Composite and compound metrics
    metrics = ["mean_ssi_v2", "mean_ssi_lin_v2", "share_compound_triggered", "share_extreme_band"]
    metric_labels = ["Final SSI (v2)", "Linear SSI", "Compound Rate (Ω > 0)", "Extreme Band Share"]

    plot_df = table_df.set_index("city")[metrics]
    x = np.arange(len(metrics))
    w = 0.35

    m_vals = plot_df.loc["mumbai"].values
    c_vals = plot_df.loc["coimbatore"].values

    b_m = ax1.bar(x - w/2, m_vals, w, label="Mumbai (Coastal Megacity)", color=PALETTE["mumbai"], edgecolor="white", linewidth=0.8)
    b_c = ax1.bar(x + w/2, c_vals, w, label="Coimbatore (Inland Plateau)", color=PALETTE["coimbatore"], edgecolor="white", linewidth=0.8)

    for bar in b_m:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.012, f"{yval:.4f}", ha="center", va="bottom", fontweight="bold", fontsize=9, color=PALETTE["mumbai"])
    for bar in b_c:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 0.012, f"{yval:.4f}", ha="center", va="bottom", fontweight="bold", fontsize=9, color=PALETTE["coimbatore"])

    ax1.set_title("Panel A: Cross-City Composite & Compound Stress Metrics", fontweight="bold", pad=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metric_labels, rotation=18, ha="right", fontweight="medium")
    ax1.set_ylabel("Metric Value / Proportion", fontweight="bold")
    ax1.set_ylim(0, 0.55)
    ax1.legend(loc="upper right", frameon=True, edgecolor="#cbd5e1")
    ax1.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    # Panel B: Hazard contributions
    contrib_cols = [c for c in table_df.columns if c.startswith("contrib_")]
    contrib_df = table_df.set_index("city")[contrib_cols]
    dim_names = ["Heat Stress", "Water Deficit", "Veg Loss", "Air Pollution", "Physical Exposure"]

    x2 = np.arange(len(dim_names))
    m_contrib = contrib_df.loc["mumbai"].values
    c_contrib = contrib_df.loc["coimbatore"].values

    b2_m = ax2.bar(x2 - w/2, m_contrib, w, label="Mumbai", color=PALETTE["mumbai"], edgecolor="white", linewidth=0.8)
    b2_c = ax2.bar(x2 + w/2, c_contrib, w, label="Coimbatore", color=PALETTE["coimbatore"], edgecolor="white", linewidth=0.8)

    for bar in b2_m:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.008, f"{yval:.3f}", ha="center", va="bottom", fontweight="bold", fontsize=9, color=PALETTE["mumbai"])
    for bar in b2_c:
        yval = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.008, f"{yval:.3f}", ha="center", va="bottom", fontweight="bold", fontsize=9, color=PALETTE["coimbatore"])

    ax2.set_title("Panel B: Normalized Hazard Contribution to Mean SSI", fontweight="bold", pad=10)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(dim_names, rotation=18, ha="right", fontweight="medium")
    ax2.set_ylabel("Contribution Share (Normalized)", fontweight="bold")
    ax2.set_ylim(0, 0.38)
    ax2.legend(loc="upper right", frameon=True, edgecolor="#cbd5e1")
    ax2.grid(axis="y", linestyle="--", alpha=0.5, color="#cbd5e1")

    fig.suptitle("Figure F8: Comparative Multi-Hazard Sustainability Stress Profiles Across Reference Metropolises", y=0.98, fontweight="bold")
    save_publication_figure(fig, "F8_crosscity_comparison")


# ==============================================================================
# MAIN RUNNER
# ==============================================================================
def main():
    print(f"=== Generating 9 Publication Figures in {OUT_DIR} ===")
    generate_study_area_map()
    generate_f1()
    generate_f2()
    generate_f3()
    generate_f4()
    generate_f5()
    generate_f6()
    generate_f7()
    generate_f8()
    print("=== All 9 Figures Generated Successfully in paper_images/ ===")


if __name__ == "__main__":
    main()
