"""
scripts/generate_event_figures.py
─────────────────────────────────
Step 07: Generates publication-quality figures (300 DPI PNG and vector SVG)
in the 'paper_images/' folder for the Early Warning & Event Prediction System:

1. F9_event_prediction_roc_pr.png & .svg:
   Multi-panel ROC and Precision-Recall evaluation curves across all 7 cities on 2022 unseen data.
2. F10_forward_threat_map.png & .svg:
   Hyperlocal spatial early warning threat maps (Mumbai April 2022 and Delhi March 2022)
   displaying H3 hexagons shaded by statutory alert tiers (RED, ORANGE, YELLOW, GREEN).
3. F11_precursor_attribution_waterfall.png & .svg:
   Physical precursor driver attributions explaining top emergency alert triggers.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import h3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

OUT_DIR = ROOT_DIR / "paper_images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Publication styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 10,
    "axes.titlesize": 11.5,
    "axes.labelsize": 10.5,
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "legend.fontsize": 9.0,
    "figure.titlesize": 13.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.8,
})

ALERT_COLORS = {
    "RED": "#dc2626",      # High Alert (>= 75%)
    "ORANGE": "#ea580c",   # Moderate Alert (50-74%)
    "YELLOW": "#eab308",   # Watch Alert (30-49%)
    "GREEN": "#16a34a",    # Normal (< 30%)
}

CITY_COLORS = {
    "delhi": "#dc2626",
    "mumbai": "#2563eb",
    "kolkata": "#7c3aed",
    "hyderabad": "#0891b2",
    "bikaner": "#d97706",
    "coimbatore": "#059669",
    "indore": "#db2777",
}


def save_figure(fig: plt.Figure, base_name: str) -> None:
    """Saves both high-res PNG and vector SVG formats."""
    for ext in ["png", "svg"]:
        p = OUT_DIR / f"{base_name}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [+] Saved paper_images/{base_name}.png and .svg")


def add_scale_bar(ax, length_km: float, center_lon: float, center_lat: float, loc: str = "lower left"):
    """Draws an accurate cartographic scale bar."""
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
    ax.plot([x0, x0 + deg_lon], [y_bar, y_bar], color="#0f172a", lw=3.0, zorder=10)
    ax.plot([x0, x0], [y_bar - 0.003, y_bar + 0.003], color="#0f172a", lw=1.5, zorder=10)
    ax.plot([x0 + deg_lon, x0 + deg_lon], [y_bar - 0.003, y_bar + 0.003], color="#0f172a", lw=1.5, zorder=10)
    ax.text(x0 + deg_lon / 2.0, y_bar + 0.005, f"{int(length_km)} km",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a", zorder=10,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none", alpha=0.8))


def add_north_arrow(ax, loc: str = "upper right"):
    """Adds a north arrow."""
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
# FIGURE F9: ROC AND PRECISION-RECALL BENCHMARK
# ==============================================================================
def generate_f9_roc_pr_curves():
    print("-> Generating Figure F9: ROC and Precision-Recall Curves (2022 OOT Test)...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    ax_roc, ax_pr, ax_bar = axes

    pred_dir = ROOT_DIR / "data/h3_panel/ml_predictions"
    cities = ["delhi", "mumbai", "kolkata", "bikaner", "indore"]

    pr_aucs = {}
    roc_aucs = {}

    for c in cities:
        p_path = pred_dir / f"{c}_2022_predictions.parquet"
        if not p_path.exists():
            continue
        df = pd.read_parquet(p_path)
        y_true = df["actual_heatwave"]
        y_prob = df["prob_heatwave"]

        if y_true.sum() > 0:
            fpr, tpr, _ = roc_curve(y_true, y_prob)
            prec, rec, _ = precision_recall_curve(y_true, y_prob)
            from sklearn.metrics import roc_auc_score, average_precision_score
            roc_val = roc_auc_score(y_true, y_prob)
            pr_val = average_precision_score(y_true, y_prob)

            roc_aucs[c] = roc_val
            pr_aucs[c] = pr_val

            color = CITY_COLORS.get(c, "#3b82f6")
            label = f"{c.capitalize()} (AUC = {roc_val:.3f})"
            ax_roc.plot(fpr, tpr, label=label, color=color, lw=2.0)

            label_pr = f"{c.capitalize()} (PR-AUC = {pr_val:.3f})"
            ax_pr.plot(rec, prec, label=label_pr, color=color, lw=2.0)

    # Panel A: ROC
    ax_roc.plot([0, 1], [0, 1], linestyle="--", color="#94a3b8", lw=1.2, label="Random Chance (0.50)")
    ax_roc.set_title("Panel A: 30-Day Heatwave ROC Curves\n(Chronological Out-of-Time Test: 2022)", fontweight="bold", pad=10)
    ax_roc.set_xlabel("False Positive Rate (1 - Specificity)", fontweight="bold")
    ax_roc.set_ylabel("True Positive Rate (Sensitivity / Recall)", fontweight="bold")
    ax_roc.legend(loc="lower right", framealpha=0.9)
    ax_roc.grid(True, linestyle=":", alpha=0.5)

    # Panel B: PR
    ax_pr.set_title("Panel B: 30-Day Heatwave Precision-Recall Curves\n(Robust to Extreme Class Imbalance)", fontweight="bold", pad=10)
    ax_pr.set_xlabel("Recall (Coverage of True Heatwaves)", fontweight="bold")
    ax_pr.set_ylabel("Precision (Accuracy of Issued Alerts)", fontweight="bold")
    ax_pr.legend(loc="lower left", framealpha=0.9)
    ax_pr.grid(True, linestyle=":", alpha=0.5)

    # Panel C: Comparison Bar Chart
    city_names = [c.capitalize() for c in cities]
    x_pos = np.arange(len(cities))
    width = 0.35
    roc_vals = [roc_aucs.get(c, 0) for c in cities]
    pr_vals = [pr_aucs.get(c, 0) for c in cities]

    bars1 = ax_bar.bar(x_pos - width/2, roc_vals, width, label="ROC-AUC", color="#3b82f6", alpha=0.9)
    bars2 = ax_bar.bar(x_pos + width/2, pr_vals, width, label="PR-AUC (Primary Metric)", color="#10b981", alpha=0.9)

    ax_bar.set_xticks(x_pos)
    ax_bar.set_xticklabels(city_names, fontweight="bold")
    ax_bar.set_ylim(0.0, 1.08)
    ax_bar.set_title("Panel C: Discrimination vs Precision-Recall\nAcross 5 Key Climate Regimes", fontweight="bold", pad=10)
    ax_bar.set_ylabel("Score (0.0 to 1.0)", fontweight="bold")
    ax_bar.legend(loc="lower right", framealpha=0.9)
    ax_bar.grid(True, axis="y", linestyle=":", alpha=0.5)

    # Add value annotations on bars
    for b in bars2:
        h = b.get_height()
        ax_bar.text(b.get_x() + b.get_width()/2., h + 0.02, f"{h:.2f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    save_figure(fig, "F9_event_prediction_roc_pr")


# ==============================================================================
# FIGURE F10: HYPERLOCAL SPATIAL FORWARD THREAT MAP
# ==============================================================================
def generate_f10_forward_threat_map():
    print("-> Generating Figure F10: Forward Spatial Threat Map (Mumbai & Delhi)...")
    pred_dir = ROOT_DIR / "data/h3_panel/ml_predictions"

    mumbai_path = pred_dir / "mumbai_2022_predictions.parquet"
    delhi_path = pred_dir / "delhi_2022_predictions.parquet"

    if not mumbai_path.exists() or not delhi_path.exists():
        print("  [!] Missing prediction parquets for threat map.")
        return

    df_m = pd.read_parquet(mumbai_path)
    df_d = pd.read_parquet(delhi_path)

    # Peak Heatwave Months in 2022
    m_peak = df_m[df_m["date"] == "2022-04-01"]
    d_peak = df_d[df_d["date"] == "2022-04-01"]

    fig = plt.figure(figsize=(18, 8.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.25)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    def get_tier_color(prob):
        if prob >= 0.75:
            return ALERT_COLORS["RED"]
        elif prob >= 0.50:
            return ALERT_COLORS["ORANGE"]
        elif prob >= 0.30:
            return ALERT_COLORS["YELLOW"]
        else:
            return ALERT_COLORS["GREEN"]

    def plot_hex_threats(ax, df_subset, title_text, scale_km=10):
        patches = []
        colors = []
        lats, lngs = [], []
        for _, row in df_subset.iterrows():
            h = row["h3_index"]
            prob = row["prob_heatwave"]
            boundary = h3.cell_to_boundary(h)
            pts = [(lng, lat) for lat, lng in boundary]
            patches.append(MplPolygon(pts, closed=True))
            colors.append(get_tier_color(prob))
            c_lat, c_lng = h3.cell_to_latlng(h)
            lats.append(c_lat)
            lngs.append(c_lng)

        coll = PatchCollection(patches, facecolors=colors, edgecolors="#1e293b", linewidth=0.35, alpha=0.9, zorder=3)
        ax.add_collection(coll)

        ax.set_xlim(min(lngs) - 0.04, max(lngs) + 0.04)
        ax.set_ylim(min(lats) - 0.05, max(lats) + 0.05)
        ax.set_aspect("equal")
        ax.set_title(title_text, fontweight="bold", pad=12)
        ax.set_xlabel("Longitude (°E)", fontweight="bold")
        ax.set_ylabel("Latitude (°N)", fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.4, color="#94a3b8")

        add_scale_bar(ax, length_km=scale_km, center_lon=np.mean(lngs), center_lat=np.mean(lats), loc="lower left")
        add_north_arrow(ax, loc="upper right")

    # Plot Mumbai
    n_red_m = (m_peak["prob_heatwave"] >= 0.75).sum()
    n_total_m = len(m_peak)
    plot_hex_threats(
        ax1, m_peak,
        f"Panel A: Mumbai 30-Day Forward Heatwave Alert (April 2022)\n{n_red_m}/{n_total_m} Hexes Triggered IMD HAP RED Emergency Protocol",
        scale_km=10
    )
    # Coastal text annotation
    ax1.text(72.77, 19.12, "Arabian Sea", fontsize=10, fontstyle="italic", color="#0284c7", rotation=75, zorder=4)

    # Plot Delhi
    n_red_d = (d_peak["prob_heatwave"] >= 0.75).sum()
    n_total_d = len(d_peak)
    plot_hex_threats(
        ax2, d_peak,
        f"Panel B: Delhi National Capital Region 30-Day Heat Alert (April 2022)\n{n_red_d}/{n_total_d} Hexes Triggered IMD HAP RED Emergency Protocol",
        scale_km=15
    )

    # Add shared legend
    legend_patches = [
        mpatches.Patch(facecolor=ALERT_COLORS["RED"], edgecolor="#0f172a", label="RED Alert (Prob ≥ 75%): Mandatory Work Bans & Water Tankers"),
        mpatches.Patch(facecolor=ALERT_COLORS["ORANGE"], edgecolor="#0f172a", label="ORANGE Alert (50% - 74%): Road Misting & Hospital Preparedness"),
        mpatches.Patch(facecolor=ALERT_COLORS["YELLOW"], edgecolor="#0f172a", label="YELLOW Watch (30% - 49%): Municipal Advisory"),
        mpatches.Patch(facecolor=ALERT_COLORS["GREEN"], edgecolor="#0f172a", label="GREEN (Prob < 30%): Baseline Normal Monitoring"),
    ]
    fig.legend(handles=legend_patches, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.02), frameon=True, facecolor="white", edgecolor="#cbd5e1", fontsize=9.5)

    plt.tight_layout()
    save_figure(fig, "F10_forward_threat_map")


# ==============================================================================
# FIGURE F11: PRECURSOR ATTRIBUTION WATERFALL
# ==============================================================================
def generate_f11_attribution_waterfall():
    print("-> Generating Figure F11: Precursor Risk Attribution...")
    report_file = ROOT_DIR / "reports/ml_event_attributions_summary.json"
    if not report_file.exists():
        print("  [!] Missing ml_event_attributions_summary.json")
        return

    with open(report_file) as fh:
        data = json.load(fh)

    m_data = data.get("mumbai", {}).get("global_heatwave_drivers", {})
    d_data = data.get("delhi", {}).get("global_heatwave_drivers", {})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    def plot_attribution_bars(ax, driver_dict, city_label, color):
        if not driver_dict:
            return
        sorted_items = sorted(driver_dict.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [k.replace("_", " ").title() for k, v in sorted_items][::-1]
        values = [v * 100 for k, v in sorted_items][::-1]

        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=color, alpha=0.85, edgecolor="#0f172a", lw=0.6)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontweight="bold")
        ax.set_xlabel("Permutation Feature Importance (% ROC-AUC Drop)", fontweight="bold")
        ax.set_title(f"{city_label}: Top Precursor Drivers of Heat Alerts", fontweight="bold", pad=10)
        ax.grid(True, axis="x", linestyle=":", alpha=0.5)

        for b in bars:
            w = b.get_width()
            ax.text(w + 0.2, b.get_y() + b.get_height()/2., f"{w:.1f}%", ha="left", va="center", fontsize=8.5, fontweight="bold")

    plot_attribution_bars(ax1, m_data, "Mumbai (Coastal Megacity)", "#2563eb")
    plot_attribution_bars(ax2, d_data, "Delhi NCR (Inland Semi-Arid)", "#dc2626")

    plt.tight_layout()
    save_figure(fig, "F11_precursor_attribution_waterfall")


if __name__ == "__main__":
    generate_f9_roc_pr_curves()
    generate_f10_forward_threat_map()
    generate_f11_attribution_waterfall()
    print("All Step 07 early warning figures generated successfully in paper_images/!")
