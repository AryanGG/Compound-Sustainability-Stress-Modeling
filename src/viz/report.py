"""
src/viz/report.py
──────────────────
Premium HTML report assembler for the SSI pipeline.

Generates a fully self-contained, dark-theme HTML dashboard with:
  - Gradient header with KPI summary cards
  - Sticky section navigation
  - Each chart in a card with a title, interpretation guide, and chart
  - Explanatory callout boxes for each section
  - Methodology footer
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


# ─────────────────────────────────────────────────────────────────────────────
#  CSS + base HTML head
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
:root {
  --bg:       #080c14;
  --surface:  #0e1420;
  --card:     #121828;
  --card-alt: #141c2e;
  --border:   rgba(255,255,255,0.08);
  --border-hi:rgba(139,92,246,0.35);
  --accent:   #8b5cf6;
  --accent2:  #06b6d4;
  --accent3:  #f59e0b;
  --text:     #e2e8f0;
  --muted:    #94a3b8;
  --dim:      #64748b;
  --danger:   #ef4444;
  --warning:  #f59e0b;
  --safe:     #22c55e;
  --heat:     #ff6b6b;
  --water:    #4ecdc4;
  --poll:     #ffe66d;
  --veg:      #6bcb77;
  --vuln:     #c084fc;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Inter', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  min-height: 100vh;
}

/* ── Typography ── */
h1 { font-size: clamp(32px,6vw,56px); font-weight:800; line-height:1.05; }
h2 { font-size: 22px; font-weight:700; }
h3 { font-size: 16px; font-weight:600; }
h4 { font-size: 13px; font-weight:600; text-transform:uppercase; letter-spacing:1.2px; }

/* ── Header ── */
.page-header {
  position: relative;
  background: linear-gradient(135deg, #0a0220 0%, #0c1445 40%, #001625 100%);
  border-bottom: 1px solid rgba(139,92,246,0.2);
  overflow: hidden;
  padding: 48px 0 36px;
}
.page-header::before {
  content: '';
  position: absolute; inset: 0;
  background:
    radial-gradient(ellipse 60% 80% at 20% 50%, rgba(139,92,246,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 50% 60% at 80% 20%, rgba(6,182,212,0.12) 0%, transparent 55%),
    radial-gradient(ellipse 40% 40% at 60% 80%, rgba(245,158,11,0.07) 0%, transparent 50%);
  pointer-events: none;
}
.page-header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(139,92,246,0.5), rgba(6,182,212,0.4), transparent);
}
.header-inner {
  position: relative;
  max-width: 1380px;
  margin: 0 auto;
  padding: 0 40px;
}
.header-eyebrow {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px;
}
.eyebrow-badge {
  background: rgba(139,92,246,0.15);
  border: 1px solid rgba(139,92,246,0.35);
  color: #c4b5fd;
  font-size: 10px; font-weight:700;
  letter-spacing: 1.8px; text-transform: uppercase;
  padding: 4px 12px; border-radius: 20px;
}
.eyebrow-sep { color: var(--dim); font-size: 12px; }
.eyebrow-meta { color: var(--muted); font-size: 12px; }
.city-title {
  background: linear-gradient(135deg, #f8fafc 0%, #c4b5fd 50%, #67e8f9 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
}
.city-subtitle {
  color: var(--muted); font-size: 14px; margin-bottom: 16px;
}
.stress-pills {
  display: flex; flex-wrap: wrap; gap: 8px;
  margin-bottom: 32px;
}
.stress-pill {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11px; font-weight:600;
  padding: 4px 12px; border-radius: 20px; border: 1px solid;
}
.pill-heat     { background:rgba(239,68,68,0.12);  border-color:rgba(239,68,68,0.35);  color:#fca5a5; }
.pill-water    { background:rgba(6,182,212,0.12);  border-color:rgba(6,182,212,0.35);  color:#67e8f9; }
.pill-pollution{ background:rgba(245,158,11,0.12); border-color:rgba(245,158,11,0.35); color:#fcd34d; }
.pill-default  { background:rgba(139,92,246,0.12); border-color:rgba(139,92,246,0.35); color:#c4b5fd; }

/* ── KPI Cards ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}
.kpi-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  transition: border-color .2s;
}
.kpi-card:hover { border-color: rgba(139,92,246,0.3); }
.kpi-card::before {
  content: '';
  position: absolute; top:0; left:0; right:0; height:2px;
  border-radius: 12px 12px 0 0;
}
.kpi-purple::before { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.kpi-cyan::before   { background: linear-gradient(90deg, #06b6d4, #22d3ee); }
.kpi-amber::before  { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
.kpi-red::before    { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-green::before  { background: linear-gradient(90deg, #22c55e, #4ade80); }
.kpi-value {
  font-size: 26px; font-weight:800;
  color: var(--text); line-height:1;
  margin-bottom: 4px;
}
.kpi-label { font-size: 11px; color: var(--muted); font-weight:500; text-transform:uppercase; letter-spacing:.8px; }
.kpi-desc  { font-size: 11px; color: var(--dim); margin-top: 6px; line-height:1.4; }

/* ── Sticky Nav ── */
.section-nav {
  position: sticky; top: 0; z-index: 100;
  background: rgba(8,12,20,0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0;
}
.nav-inner {
  max-width: 1380px; margin: 0 auto; padding: 0 40px;
  display: flex; align-items: center; gap: 0;
  overflow-x: auto;
}
.nav-link {
  display: flex; align-items: center; gap: 6px;
  padding: 12px 18px;
  color: var(--muted); font-size: 12px; font-weight:500;
  text-decoration: none; white-space: nowrap;
  border-bottom: 2px solid transparent;
  transition: color .2s, border-color .2s;
}
.nav-link:hover { color: var(--text); border-color: var(--accent); }
.nav-dot { width:6px; height:6px; border-radius:50%; }

/* ── Main Layout ── */
.main { max-width: 1380px; margin: 0 auto; padding: 40px 40px 60px; }

/* ── Section Headers ── */
.section-wrap { margin-bottom: 56px; }
.section-header {
  display: flex; align-items: flex-start; gap: 20px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border);
}
.section-number {
  font-size: 11px; font-weight:700;
  color: var(--accent); letter-spacing: 1.5px;
  background: rgba(139,92,246,0.1);
  border: 1px solid rgba(139,92,246,0.2);
  padding: 3px 8px; border-radius: 6px;
  white-space: nowrap; margin-top: 3px;
}
.section-title-block h2 { color: var(--text); margin-bottom: 4px; }
.section-title-block p  { color: var(--muted); font-size: 13px; max-width: 700px; }

/* ── Chart Cards ── */
.chart-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow: hidden;
  transition: border-color .25s, box-shadow .25s;
}
.chart-card:hover {
  border-color: rgba(139,92,246,0.2);
  box-shadow: 0 4px 32px rgba(0,0,0,0.3);
}
.chart-header {
  padding: 20px 24px 12px;
  border-bottom: 1px solid var(--border);
}
.chart-title { font-size: 14px; font-weight:700; color: var(--text); margin-bottom: 4px; }
.chart-subtitle { font-size: 12px; color: var(--muted); line-height: 1.5; }
.chart-body { padding: 0; }

/* ── Insight callout ── */
.insight-box {
  display: flex; gap: 14px;
  background: rgba(139,92,246,0.06);
  border: 1px solid rgba(139,92,246,0.2);
  border-left: 3px solid var(--accent);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 20px;
}
.insight-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
.insight-text { font-size: 12px; color: var(--muted); line-height: 1.65; }
.insight-text strong { color: var(--text); }

/* ── Band legend ── */
.band-legend {
  display: flex; gap: 8px; flex-wrap: wrap;
  padding: 12px 24px;
  border-top: 1px solid var(--border);
}
.band-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--muted);
}
.band-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }

/* ── Indicator legend ── */
.indicator-legend {
  display: flex; gap: 16px; flex-wrap: wrap;
  padding: 12px 24px;
  border-top: 1px solid var(--border);
}
.ind-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--muted);
}
.ind-line { width:20px; height:3px; border-radius:2px; flex-shrink:0; }

/* ── Grid layouts ── */
.grid-60-40 { display:grid; grid-template-columns: 60fr 40fr; gap: 20px; }
.grid-2     { display:grid; grid-template-columns: 1fr 1fr;    gap: 20px; }
.grid-full  { display:grid; grid-template-columns: 1fr;        gap: 20px; }
.mb-20 { margin-bottom: 20px; }

/* ── How-to-read box ── */
.how-to-read {
  background: var(--card-alt);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 22px 26px;
}
.how-to-read h4 { color: var(--accent2); margin-bottom: 12px; font-size: 11px; letter-spacing:1.5px; }
.how-to-read ul { list-style: none; display: flex; flex-direction: column; gap: 8px; }
.how-to-read li {
  display: flex; gap: 10px; align-items: flex-start;
  font-size: 12px; color: var(--muted); line-height: 1.55;
}
.how-to-read li::before {
  content: '→'; color: var(--accent2); flex-shrink:0; margin-top: 1px;
}
.how-to-read li strong { color: var(--text); }

/* ── Methodology footer ── */
.page-footer {
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 40px 0 32px;
  margin-top: 20px;
}
.footer-inner {
  max-width: 1380px; margin: 0 auto; padding: 0 40px;
  display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 40px;
}
.footer-title { font-size: 11px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; color: var(--accent); margin-bottom: 12px; }
.footer-text  { font-size: 12px; color: var(--dim); line-height: 1.7; }
.footer-list  { list-style:none; display:flex; flex-direction:column; gap: 6px; }
.footer-list li { font-size: 12px; color: var(--dim); }
.footer-list li::before { content: '• '; color: var(--accent); }
.footer-copy {
  max-width: 1380px; margin: 24px auto 0; padding: 20px 40px 0;
  border-top: 1px solid var(--border);
  color: var(--dim); font-size: 11px;
  display: flex; justify-content: space-between; align-items: center;
}

/* ── Responsive ── */
@media (max-width: 1100px) {
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 800px) {
  .header-inner, .nav-inner, .main, .footer-inner, .footer-copy { padding-left: 20px; padding-right: 20px; }
  .kpi-grid { grid-template-columns: 1fr 1fr; }
  .grid-60-40, .grid-2 { grid-template-columns: 1fr; }
  .footer-inner { grid-template-columns: 1fr; gap: 24px; }
}
@media (max-width: 500px) {
  .kpi-grid { grid-template-columns: 1fr; }
}
"""

_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SSI Dashboard — {city_title}</title>
<meta name="description" content="Compound Sustainability Stress Index (SSI) report for {city_title}, India — spatial and temporal stress analysis across {n_hexes} H3 hexes.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
""".format(css=_CSS, city_title="{city_title}", n_hexes="{n_hexes}")


# ─────────────────────────────────────────────────────────────────────────────
#  City / stress metadata
# ─────────────────────────────────────────────────────────────────────────────

_CITY_META: dict[str, dict] = {
    "mumbai":    {"title": "Mumbai",    "state": "Maharashtra",    "stresses": ["heat", "flood", "pollution"]},
    "delhi":     {"title": "Delhi NCR", "state": "Delhi",          "stresses": ["extreme_heat", "pollution", "dust"]},
    "bengaluru": {"title": "Bengaluru", "state": "Karnataka",      "stresses": ["water_crisis", "urban_heat"]},
    "chennai":   {"title": "Chennai",   "state": "Tamil Nadu",     "stresses": ["heat", "flooding", "water_stress"]},
    "hyderabad": {"title": "Hyderabad", "state": "Telangana",      "stresses": ["heat", "drought", "urban_sprawl"]},
    "pune":      {"title": "Pune",      "state": "Maharashtra",    "stresses": ["heat", "water_stress", "rapid_growth"]},
    "ahmedabad": {"title": "Ahmedabad", "state": "Gujarat",        "stresses": ["extreme_heat"]},
    "kolkata":   {"title": "Kolkata",   "state": "West Bengal",    "stresses": ["heat", "flooding", "pollution"]},
    "surat":     {"title": "Surat",     "state": "Gujarat",        "stresses": ["flooding", "industrial_pollution", "heat"]},
    "indore":    {"title": "Indore",    "state": "Madhya Pradesh", "stresses": ["heat", "water_stress"]},
}

_PILL_CSS_MAP = {
    "heat": "pill-heat", "extreme_heat": "pill-heat", "flood": "pill-water",
    "flooding": "pill-water", "water_crisis": "pill-water", "water_stress": "pill-water",
    "drought": "pill-water", "pollution": "pill-pollution",
    "industrial_pollution": "pill-pollution", "dust": "pill-pollution",
}
_STRESS_ICONS = {
    "heat": "🌡️", "extreme_heat": "🔥", "flood": "🌊", "flooding": "🌊",
    "water_crisis": "💧", "water_stress": "💧", "drought": "🏜️",
    "pollution": "🌫️", "industrial_pollution": "🏭", "dust": "💨",
    "urban_heat": "🌆", "urban_sprawl": "🏙️", "rapid_growth": "📈",
}

def _stress_pills(stresses: list[str]) -> str:
    pills = []
    for s in stresses:
        css   = _PILL_CSS_MAP.get(s, "pill-default")
        icon  = _STRESS_ICONS.get(s, "⚠️")
        label = s.replace("_", " ").title()
        pills.append(f'<span class="stress-pill {css}">{icon} {label}</span>')
    return "\n".join(pills)


# ─────────────────────────────────────────────────────────────────────────────
#  Figure → HTML div
# ─────────────────────────────────────────────────────────────────────────────

def _fig_div(fig: go.Figure, include_js: bool = False) -> str:
    return pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs="cdn" if include_js else False,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "responsive": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["toImage"],
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Component builders
# ─────────────────────────────────────────────────────────────────────────────

def _kpi_card(value: str, label: str, desc: str, colour_cls: str) -> str:
    return f"""
<div class="kpi-card {colour_cls}">
  <div class="kpi-value">{value}</div>
  <div class="kpi-label">{label}</div>
  <div class="kpi-desc">{desc}</div>
</div>"""


def _section_header(number: str, title: str, description: str) -> str:
    return f"""
<div class="section-header">
  <div class="section-number">{number}</div>
  <div class="section-title-block">
    <h2>{title}</h2>
    <p>{description}</p>
  </div>
</div>"""


def _insight(icon: str, text: str) -> str:
    return f"""
<div class="insight-box">
  <div class="insight-icon">{icon}</div>
  <div class="insight-text">{text}</div>
</div>"""


def _chart_card(title: str, subtitle: str, fig_html: str,
                footer_html: str = "") -> str:
    return f"""
<div class="chart-card">
  <div class="chart-header">
    <div class="chart-title">{title}</div>
    <div class="chart-subtitle">{subtitle}</div>
  </div>
  <div class="chart-body">{fig_html}</div>
  {footer_html}
</div>"""


def _band_legend() -> str:
    items = [
        ("#4ade80", "Low  (SSI 0.00 – 0.25)", "Normal or below-baseline stress"),
        ("#facc15", "Moderate  (0.25 – 0.50)", "Elevated stress, monitor"),
        ("#fb923c", "High  (0.50 – 0.75)",     "Significant stress, action needed"),
        ("#ef4444", "Extreme  (0.75 – 1.00)",  "Critical compound stress"),
    ]
    dots = "".join(
        f'<div class="band-item"><div class="band-dot" style="background:{c}"></div>'
        f'<span><strong style="color:#e2e8f0">{label}</strong> — {desc}</span></div>'
        for c, label, desc in items
    )
    return f'<div class="band-legend">{dots}</div>'


def _indicator_legend() -> str:
    items = [
        ("#FF6B6B", "Heat Stress"),
        ("#4ECDC4", "Water Stress"),
        ("#FFE66D", "Pollution"),
        ("#6BCB77", "Vegetation Stress"),
        ("#C084FC", "Urban Vulnerability"),
    ]
    lines = "".join(
        f'<div class="ind-item">'
        f'<div class="ind-line" style="background:{c}"></div>'
        f'<span>{label}</span></div>'
        for c, label in items
    )
    return f'<div class="indicator-legend">{lines}</div>'


def _how_to_read(items: list[tuple[str, str]]) -> str:
    lis = "".join(
        f"<li><strong>{k}:</strong> {v}</li>"
        for k, v in items
    )
    return f"""
<div class="how-to-read">
  <h4>📖 How to read this chart</h4>
  <ul>{lis}</ul>
</div>"""


# ─────────────────────────────────────────────────────────────────────────────
#  Main report generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(city: str, df: pd.DataFrame, output_path: Path) -> Path:
    """
    Assemble a premium, fully explained SSI HTML dashboard for one city.
    """
    from src.viz.maps  import build_h3_map
    from src.viz.plots import (
        plot_ssi_timeseries, plot_indicator_trends,
        plot_ssi_band_donut, plot_archetype_radar,
        plot_indicator_heatmap, plot_seasonal_heatmap,
        plot_anomaly_timeline, plot_top_stressed,
        plot_vulnerability_scatter,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df["date"] = pd.to_datetime(df["date"])
    meta = _CITY_META.get(city, {"title": city.title(), "state": "", "stresses": []})

    # ── Summary stats ──────────────────────────────────────────────────────────
    n_hexes    = int(df["h3_index"].nunique())
    n_rows     = len(df)
    date_min   = df["date"].min().strftime("%b %Y")
    date_max   = df["date"].max().strftime("%b %Y")
    mean_ssi   = float(df["ssi_value"].mean()) if "ssi_value" in df.columns else 0
    max_ssi    = float(df["ssi_value"].max())  if "ssi_value" in df.columns else 0
    band_cts   = df["ssi_band"].value_counts()  if "ssi_band" in df.columns else pd.Series(dtype=int)
    dom_band   = band_cts.idxmax()  if not band_cts.empty else "Low"
    dom_pct    = band_cts[dom_band] / n_rows * 100 if not band_cts.empty else 0
    anomaly_pct= float(df["anomaly_flag"].mean() * 100) if "anomaly_flag" in df.columns else 0
    n_archetypes = int(df["archetype_id"].nunique()) if "archetype_id" in df.columns else 0

    # ── Build figures ──────────────────────────────────────────────────────────
    print("  [1/9] H3 SSI map…")
    fig_map      = build_h3_map(df, "ssi_value", agg="mean",
                                title="<b>Compound SSI</b> — Time-averaged per H3 hex")
    print("  [2/9] SSI time series…")
    fig_ts       = plot_ssi_timeseries(df, city)
    print("  [3/9] Indicator trends…")
    fig_ind      = plot_indicator_trends(df)
    print("  [4/9] Band donut…")
    fig_donut    = plot_ssi_band_donut(df)
    print("  [5/9] Archetype radar…")
    fig_radar    = plot_archetype_radar(df)
    print("  [6/9] Correlation heatmap…")
    fig_corr     = plot_indicator_heatmap(df)
    print("  [7/9] Seasonal heatmap…")
    fig_seasonal = plot_seasonal_heatmap(df)
    print("  [8/9] Anomaly timeline…")
    fig_anomaly  = plot_anomaly_timeline(df)
    print("  [9/9] Top stressed hexes…")
    fig_top      = plot_top_stressed(df, n=20)
    fig_vuln     = plot_vulnerability_scatter(df)

    # ── Convert to HTML divs ───────────────────────────────────────────────────
    d_map      = _fig_div(fig_map,      include_js=True)   # plotly.js included once here
    d_ts       = _fig_div(fig_ts)
    d_ind      = _fig_div(fig_ind)
    d_donut    = _fig_div(fig_donut)
    d_radar    = _fig_div(fig_radar)
    d_corr     = _fig_div(fig_corr)
    d_seasonal = _fig_div(fig_seasonal)
    d_anomaly  = _fig_div(fig_anomaly)
    d_top      = _fig_div(fig_top)
    d_vuln     = _fig_div(fig_vuln)

    # ── Assemble ───────────────────────────────────────────────────────────────
    band_colour = {"Low":"#4ade80","Moderate":"#facc15","High":"#fb923c","Extreme":"#ef4444"}
    dom_col     = band_colour.get(dom_band, "#e2e8f0")
    ts_now      = datetime.now().strftime("%d %b %Y, %H:%M IST")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SSI Dashboard — {meta['title']}</title>
<meta name="description" content="Compound Sustainability Stress Index for {meta['title']}, India.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&display=swap" rel="stylesheet">
<style>{_CSS}</style>
</head>
<body>

<!-- ═══════════════════ PAGE HEADER ═══════════════════ -->
<header class="page-header">
  <div class="header-inner">
    <div class="header-eyebrow">
      <span class="eyebrow-badge">Compound SSI Report</span>
      <span class="eyebrow-sep">·</span>
      <span class="eyebrow-meta">H3 Resolution 8 &nbsp;(~0.74 km² per cell)</span>
      <span class="eyebrow-sep">·</span>
      <span class="eyebrow-meta">Generated {ts_now}</span>
    </div>

    <h1 class="city-title">{meta['title']}</h1>
    <p class="city-subtitle">
      {meta['state']} &nbsp;·&nbsp;
      {date_min} – {date_max} &nbsp;·&nbsp;
      {n_hexes:,} H3 hexes &nbsp;·&nbsp;
      {n_rows:,} hex-month observations
    </p>

    <div class="stress-pills">
      {_stress_pills(meta['stresses'])}
    </div>

    <div class="kpi-grid">
      {_kpi_card(f"{mean_ssi:.4f}", "Mean SSI Score",
                 "Average compound stress across all hexes and months (0 = none, 1 = extreme)",
                 "kpi-purple")}
      {_kpi_card(f"{max_ssi:.4f}", "Peak SSI",
                 "Highest SSI recorded in any single hex during the study period",
                 "kpi-red")}
      {_kpi_card(f'<span style="color:{dom_col}">{dom_pct:.1f}%</span>',
                 f'In &ldquo;{dom_band}&rdquo; Band',
                 "Fraction of all hex-month observations classified in the dominant risk band",
                 "kpi-amber")}
      {_kpi_card(f"{anomaly_pct:.1f}%", "Anomaly Rate",
                 "Fraction of hexes exceeding the 90th-percentile SSI threshold in any given month",
                 "kpi-cyan")}
      {_kpi_card(str(n_archetypes), "Stress Archetypes",
                 "Distinct compound-stress profiles identified by k-means clustering across hexes",
                 "kpi-green")}
    </div>
  </div>
</header>

<!-- ═══════════════════ STICKY NAV ═══════════════════ -->
<nav class="section-nav" aria-label="Report sections">
  <div class="nav-inner">
    <a class="nav-link" href="#spatial">
      <div class="nav-dot" style="background:#8b5cf6"></div> Spatial Overview
    </a>
    <a class="nav-link" href="#temporal">
      <div class="nav-dot" style="background:#06b6d4"></div> Temporal Trends
    </a>
    <a class="nav-link" href="#indicators">
      <div class="nav-dot" style="background:#f59e0b"></div> Stress Indicators
    </a>
    <a class="nav-link" href="#climatology">
      <div class="nav-dot" style="background:#22c55e"></div> Climatology
    </a>
    <a class="nav-link" href="#archetypes">
      <div class="nav-dot" style="background:#c084fc"></div> Archetypes
    </a>
    <a class="nav-link" href="#hotspots">
      <div class="nav-dot" style="background:#ef4444"></div> Priority Locations
    </a>
  </div>
</nav>

<!-- ═══════════════════ MAIN CONTENT ═══════════════════ -->
<main class="main">

<!-- ──────────────── SECTION 1: SPATIAL OVERVIEW ──────────────── -->
<section id="spatial" class="section-wrap">
  {_section_header("01 / SPATIAL", "Where Does Stress Concentrate?",
    "This section shows the geographic distribution of compound stress across the city. "
    "Each hexagonal cell covers ~0.74 km² and is coloured by its average SSI over the full study period. "
    "Use this to identify the highest-risk neighbourhoods and spatial patterns.")}

  {_insight("🗺️",
    "<strong>How to use the map:</strong> Hover over any hex to see its exact SSI value and H3 index. "
    "Zoom in with the scroll wheel or pinch gesture. "
    "Dark green = low compound stress; orange/red = elevated or extreme stress. "
    "Look for clusters of red/orange hexes — these are compound hot-spots where multiple stressors overlap.")}

  <div class="grid-60-40 mb-20">
    {_chart_card(
      "Compound SSI Map — Time-averaged (2015–2025)",
      "Each H3 hex is coloured by its mean SSI score across all months in the study period. "
      "Darker red indicates persistent compound stress. The colour scale runs from 0 (green, no stress) to 1 (red, extreme stress).",
      d_map
    )}
    {_chart_card(
      "SSI Risk Band Distribution",
      "Proportion of all hex × month observations that fall into each of the four risk bands. "
      "A healthy city should show the majority in the Low band. Moderate/High/Extreme slices point to widespread or persistent stress episodes.",
      d_donut,
      _band_legend()
    )}
  </div>

  {_how_to_read([
    ("Green hexes (SSI < 0.25)", "Stress levels are within historical norms. No immediate concern."),
    ("Yellow hexes (0.25 – 0.50)", "Measurably elevated stress. Worth monitoring for compounding trends."),
    ("Orange hexes (0.50 – 0.75)", "High compound stress. Multiple indicators are simultaneously elevated. "
     "These areas need policy attention."),
    ("Red hexes (0.75 – 1.00)", "Extreme compound stress. Multiple critical stressors are co-occurring. "
     "Priority intervention zones."),
  ])}
</section>

<!-- ──────────────── SECTION 2: TEMPORAL TRENDS ──────────────── -->
<section id="temporal" class="section-wrap">
  {_section_header("02 / TEMPORAL", "How Has Stress Changed Over Time?",
    "These charts track the evolution of compound stress month-by-month across the full 10-year study window (2015–2025). "
    "They reveal whether conditions are improving, worsening, or staying the same, "
    "and flag periods of unusually elevated stress.")}

  {_insight("📈",
    "<strong>What to look for:</strong> A rising trend in the SSI time-series suggests compounding stress over the decade. "
    "Seasonal spikes (recurring at the same months each year) point to climate-driven patterns like monsoon onset or summer heat. "
    "The anomaly bars highlight which specific months had the most hexes in crisis — "
    "sustained red bars above the dashed 10% line indicate a stress episode of city-wide concern.")}

  <div class="grid-2">
    {_chart_card(
      "Monthly SSI Trend — City Average",
      "The purple line shows the city-wide mean SSI for each calendar month. "
      "The shaded band represents ±1 standard deviation across hexes — a wider band means greater "
      "within-city inequality of stress exposure. A flat or declining trend is the goal.",
      d_ts
    )}
    {_chart_card(
      "Monthly Anomaly Rate",
      "Each bar shows the percentage of H3 hexes whose SSI exceeded the 90th percentile of the "
      "historical distribution in that month. "
      "The dashed blue line marks the 10% threshold. Months above this line experienced "
      "statistically abnormal compound stress across a significant part of the city.",
      d_anomaly
    )}
  </div>
</section>

<!-- ──────────────── SECTION 3: STRESS INDICATORS ──────────────── -->
<section id="indicators" class="section-wrap">
  {_section_header("03 / INDICATORS", "Which Stressors Are Driving the SSI?",
    "The Compound SSI is built from five independent stress indicators, each normalised to a 0–1 scale. "
    "This chart decomposes the SSI into its components so you can see which specific stressors are "
    "rising, seasonal, or persistently elevated.")}

  {_insight("🔬",
    "<strong>Indicator definitions:</strong> "
    "<strong style='color:#FF6B6B'>Heat Stress</strong> — derived from temperature, dewpoint (Heat Index) and land surface temperature anomalies. "
    "<strong style='color:#4ECDC4'>Water Stress</strong> — precipitation deficit below climatological normal + soil moisture depletion. "
    "<strong style='color:#FFE66D'>Pollution</strong> — PM₂.₅ concentration relative to WHO annual guideline (5 µg/m³). "
    "<strong style='color:#6BCB77'>Vegetation Stress</strong> — NDVI anomaly below seasonal baseline (inverted: less green = more stress). "
    "<strong style='color:#C084FC'>Urban Vulnerability</strong> — composite of BPL%, slum%, elderly population%, and (inverse) literacy rate.")}

  {_chart_card(
    "5-Indicator Trend — Monthly City Averages",
    "Each line shows the monthly city-mean value for one stress indicator (0 = no stress, 1 = maximum stress). "
    "Overlapping peaks suggest compound stress events where multiple stressors co-occur simultaneously. "
    "Use this chart to understand which indicator drives the SSI at any given time.",
    d_ind,
    _indicator_legend()
  )}
</section>

<!-- ──────────────── SECTION 4: CLIMATOLOGY ──────────────── -->
<section id="climatology" class="section-wrap">
  {_section_header("04 / CLIMATOLOGY", "What Seasonal and Structural Patterns Exist?",
    "These charts reveal the underlying climatological signal in the SSI — recurring seasonal peaks, "
    "inter-annual trends, and the statistical relationships between stress indicators. "
    "Understanding these patterns is essential for anticipatory planning.")}

  {_insight("🔄",
    "<strong>Seasonal patterns:</strong> In Indian cities, stress typically peaks in pre-monsoon months (April–June) due to heat, "
    "and again in post-monsoon months in northern cities due to air pollution (stubble burning + winter inversions). "
    "The heatmap makes it easy to spot these recurring cycles year-over-year. "
    "<strong>Correlations:</strong> Strongly correlated indicators (dark red in the matrix) tend to co-spike — "
    "interventions that address one may help reduce the other.")}

  <div class="grid-2">
    {_chart_card(
      "Seasonal SSI Heatmap — Year × Month",
      "Each cell shows the city-mean SSI for a specific year and month. "
      "Read across a row to see how stress evolves through the calendar year. "
      "Read down a column to see whether the same month is getting worse or better over time. "
      "Consistently dark columns point to chronically stressful seasons.",
      d_seasonal
    )}
    {_chart_card(
      "Indicator Correlation Matrix",
      "Pearson correlation coefficients between the five stress indicators computed across all hex-month observations. "
      "Values near +1 (dark red) mean the two indicators tend to spike together — a compound risk signal. "
      "Values near 0 (white) indicate independent stressors. "
      "Values near −1 (dark blue) are rare and suggest opposite seasonal patterns.",
      d_corr
    )}
  </div>
</section>

<!-- ──────────────── SECTION 5: ARCHETYPES & VULNERABILITY ──────────────── -->
<section id="archetypes" class="section-wrap">
  {_section_header("05 / ARCHETYPES", "What Types of Stress Profiles Exist?",
    "Not all stressed areas suffer the same way. K-means clustering groups the city's H3 hexes into "
    "distinct compound-stress archetypes based on their indicator profiles. "
    "Each archetype represents a different combination of stressors and calls for a tailored policy response.")}

  {_insight("🎯",
    "<strong>Using archetypes for policy:</strong> "
    "A hex in the <em>heat-dominant</em> archetype needs green cover, cool roofs, and mist cooling. "
    "A <em>pollution-dominant</em> hex needs traffic restrictions and industrial monitoring. "
    "A <em>high-vulnerability</em> hex needs social protection regardless of environmental stress. "
    "The scatter plot (right) identifies hexes that face both high socio-economic vulnerability AND "
    "high environmental stress — the most critical targets for compound interventions.")}

  <div class="grid-2">
    {_chart_card(
      "Stress Archetype Profiles — Radar Chart",
      "Each polygon represents the average indicator profile of one stress archetype. "
      "Larger polygons indicate overall higher stress. "
      "A polygon that extends far on the Heat Stress spoke but not Water Stress indicates "
      "a heat-dominant archetype. Overlapping archetypes share similar risk profiles.",
      d_radar
    )}
    {_chart_card(
      "Socio-Economic Vulnerability vs. Compound Stress",
      "Each point is one H3 hex plotted by mean BPL population share (x-axis) vs. mean SSI (y-axis). "
      "Point size reflects the slum household fraction; colour indicates urban vulnerability index. "
      "The top-right quadrant — high BPL% and high SSI — represents the most at-risk locations "
      "where environmental and social stresses compound each other.",
      d_vuln
    )}
  </div>
</section>

<!-- ──────────────── SECTION 6: PRIORITY LOCATIONS ──────────────── -->
<section id="hotspots" class="section-wrap">
  {_section_header("06 / PRIORITY LOCATIONS", "Which Specific Areas Need Urgent Attention?",
    "This chart ranks individual H3 hexes by their time-averaged SSI — the locations that have experienced "
    "the most persistent compound stress over the full 10-year study period. "
    "These are the highest-priority areas for targeted resilience interventions.")}

  {_insight("📍",
    "<strong>How to use this list:</strong> Each bar represents one H3 hex (identified by the last 6 characters of its H3 index). "
    "The colour reflects the risk band — green (Low), yellow (Moderate), orange (High), red (Extreme). "
    "Cross-reference these hex IDs with the map in Section 1 to locate them geographically. "
    "Prioritise hexes that are both high on this chart <em>and</em> in the top-right of the vulnerability scatter.")}

  {_chart_card(
    "Top 20 Most Stressed H3 Hexes — Time-averaged SSI",
    "Ranked by mean SSI across all months in the study period. "
    "H3 hex identifiers are truncated to the last 6 characters for readability; "
    "use the map above to locate any hex geographically by hovering over it. "
    "Bars are coloured by risk band: green &lt; 0.25, yellow 0.25–0.50, orange 0.50–0.75, red ≥ 0.75.",
    d_top,
    _band_legend()
  )}
</section>

</main>

<!-- ═══════════════════ FOOTER ═══════════════════ -->
<footer class="page-footer">
  <div class="footer-inner">
    <div>
      <div class="footer-title">About This Report</div>
      <p class="footer-text">
        The <strong style="color:#e2e8f0">Compound Sustainability Stress Index (SSI)</strong> is a composite,
        spatio-temporal measure of environmental stress computed for Indian cities using multi-source geospatial data.
        It combines five independently normalised stress indicators — heat, water, pollution, vegetation, and urban
        vulnerability — into a single 0–1 score using PCA-derived weights adjusted by city-specific risk multipliers.
        The H3 hexagonal grid at resolution 8 (~0.74 km² per cell) provides a uniform spatial framework for all
        computations. All indicators use a rolling 3-year baseline for temporal normalisation.
      </p>
    </div>
    <div>
      <div class="footer-title">Data Sources</div>
      <ul class="footer-list">
        <li>ERA5 Reanalysis — Copernicus CDS (ECMWF)</li>
        <li>Sentinel-2 L2A NDVI — Microsoft Planetary Computer</li>
        <li>MODIS MOD11A2 LST — NASA / Planetary Computer</li>
        <li>PM₂.₅ Annual Mean — NASA SEDAC SDEI</li>
        <li>Road &amp; buildings — OpenStreetMap via OSMnx</li>
        <li>Vulnerability priors — Census of India 2011</li>
      </ul>
    </div>
    <div>
      <div class="footer-title">SSI Methodology</div>
      <ul class="footer-list">
        <li>H3 resolution 8 spatial grid</li>
        <li>Monthly temporal aggregation</li>
        <li>Z-score normalisation (3-yr rolling baseline)</li>
        <li>PCA-based composite weighting</li>
        <li>City-specific weight adjustments</li>
        <li>k-means archetype clustering (k=6)</li>
        <li>90th-percentile anomaly detection</li>
      </ul>
    </div>
  </div>
  <div class="footer-copy">
    <span>Compound SSI Pipeline &nbsp;·&nbsp; {meta['title']}, India &nbsp;·&nbsp; {date_min} – {date_max}</span>
    <span style="color:#475569">Generated {ts_now}</span>
  </div>
</footer>

</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"\n  Report saved -> {output_path}  ({size_mb:.1f} MB)")
    return output_path
