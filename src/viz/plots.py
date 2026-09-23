"""
src/viz/plots.py
─────────────────
All non-map Plotly chart builders for the SSI dashboard.

Charts:
    plot_ssi_timeseries      — monthly city-level SSI trend + confidence band
    plot_indicator_trends    — all 5 indicators as multi-line chart over time
    plot_ssi_band_donut      — donut chart of Low/Moderate/High/Extreme distribution
    plot_archetype_radar     — spider/radar chart for each stress archetype
    plot_indicator_heatmap   — Pearson correlation matrix of the 5 indicators
    plot_seasonal_heatmap    — month × year SSI heatmap (climatology grid)
    plot_anomaly_timeline    — fraction of flagged hexes per month
    plot_top_stressed        — top-N hexes by mean SSI (horizontal bar)
    plot_vulnerability_scatter — BPL% vs mean SSI coloured by city zone
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─── Shared style constants ───────────────────────────────────────────────────

_BG        = "rgba(15,17,23,0)"        # transparent (card bg supplied by HTML)
_GRID      = "rgba(255,255,255,0.07)"
_FONT_COL  = "#e0e0e0"
_FONT_FAM  = "Inter, system-ui, sans-serif"

_INDICATOR_COLOURS = {
    "heat_stress_idx":         "#FF6B6B",
    "water_stress_idx":        "#4ECDC4",
    "pollution_idx":           "#FFE66D",
    "vegetation_idx":          "#6BCB77",
    "urban_vulnerability_idx": "#C084FC",
}
_INDICATOR_LABELS = {
    "heat_stress_idx":         "Heat Stress",
    "water_stress_idx":        "Water Stress",
    "pollution_idx":           "Pollution",
    "vegetation_idx":          "Vegetation",
    "urban_vulnerability_idx": "Urban Vulnerability",
}

_BAND_COLOURS = {
    "Low":      "#4ade80",
    "Moderate": "#facc15",
    "High":     "#fb923c",
    "Extreme":  "#ef4444",
}

_LAYOUT_BASE = dict(
    paper_bgcolor=_BG,
    plot_bgcolor=_BG,
    font={"color": _FONT_COL, "family": _FONT_FAM, "size": 12},
    margin={"r": 24, "t": 50, "l": 24, "b": 24},
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _axis(title: str = "", **kw) -> dict:
    return dict(
        title=title,
        gridcolor=_GRID,
        zerolinecolor=_GRID,
        tickfont={"color": "#a0a0a0"},
        title_font={"color": _FONT_COL},
        **kw,
    )


# ─── 1. SSI Time Series ───────────────────────────────────────────────────────

def plot_ssi_timeseries(df: pd.DataFrame, city: str) -> go.Figure:
    """
    Monthly city-level mean SSI with ±1 std band.

    Shows the overall compound stress trajectory over time.
    """
    ts = (
        df.groupby("date")["ssi_value"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "ssi_mean", "std": "ssi_std"})
    )
    ts["date"]    = pd.to_datetime(ts["date"])
    ts["ssi_std"] = ts["ssi_std"].fillna(0)
    ts["upper"]   = (ts["ssi_mean"] + ts["ssi_std"]).clip(0, 1)
    ts["lower"]   = (ts["ssi_mean"] - ts["ssi_std"]).clip(0, 1)

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=pd.concat([ts["date"], ts["date"][::-1]]),
        y=pd.concat([ts["upper"], ts["lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(139,92,246,0.15)",
        line={"color": "rgba(0,0,0,0)"},
        hoverinfo="skip",
        showlegend=False,
    ))

    # Main line
    fig.add_trace(go.Scatter(
        x=ts["date"],
        y=ts["ssi_mean"],
        mode="lines",
        line={"color": "#8b5cf6", "width": 2.5},
        name="Mean SSI",
        hovertemplate="%{x|%b %Y}: <b>%{y:.4f}</b><extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": f"<b>SSI Monthly Trend</b> — {city.title()}", "font": {"size": 15}},
        xaxis=_axis(""),
        yaxis=_axis("SSI Score", range=[0, max(ts["upper"].max() * 1.1, 0.01)]),
        hovermode="x unified",
        height=320,
    )
    return fig


# ─── 2. Five-Indicator Trend ─────────────────────────────────────────────────

def plot_indicator_trends(df: pd.DataFrame) -> go.Figure:
    """
    Monthly city-level mean for all 5 stress indicators on one chart.
    """
    indicator_cols = [c for c in _INDICATOR_LABELS if c in df.columns]
    ts = df.groupby("date")[indicator_cols].mean().reset_index()
    ts["date"] = pd.to_datetime(ts["date"])

    fig = go.Figure()
    for col in indicator_cols:
        fig.add_trace(go.Scatter(
            x=ts["date"],
            y=ts[col],
            mode="lines",
            name=_INDICATOR_LABELS[col],
            line={"color": _INDICATOR_COLOURS[col], "width": 2},
            hovertemplate=f"{_INDICATOR_LABELS[col]}: <b>%{{y:.3f}}</b><extra></extra>",
        ))

    layout = dict(_LAYOUT_BASE)
    layout["legend"] = {"orientation": "h", "y": -0.18, "bgcolor": "rgba(0,0,0,0)", "font": {"color": _FONT_COL}}
    fig.update_layout(
        **layout,
        title={"text": "<b>5 Stress Indicator Trends</b>", "font": {"size": 15}},
        xaxis=_axis(""),
        yaxis=_axis("Normalized Index"),
        hovermode="x unified",
        height=340,
    )
    return fig


# ─── 3. SSI Band Donut ────────────────────────────────────────────────────────

def plot_ssi_band_donut(df: pd.DataFrame) -> go.Figure:
    """
    Donut chart showing the fraction of hex × time observations in each SSI band.
    """
    counts = df["ssi_band"].value_counts()
    order  = ["Low", "Moderate", "High", "Extreme"]
    labels = [b for b in order if b in counts.index]
    values = [counts[b] for b in labels]
    colors = [_BAND_COLOURS[b] for b in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.58,
        marker={"colors": colors, "line": {"color": "#1a1d27", "width": 2}},
        textfont={"color": _FONT_COL, "size": 12},
        hovertemplate="<b>%{label}</b><br>%{value:,} obs (%{percent})<extra></extra>",
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>SSI Band Distribution</b>", "font": {"size": 15}},
        showlegend=True,
        annotations=[{
            "text": "SSI<br>Bands",
            "x": 0.5, "y": 0.5,
            "font_size": 13,
            "font_color": _FONT_COL,
            "showarrow": False,
        }],
        height=340,
    )
    fig.update_layout(legend={"orientation": "v", "font": {"color": _FONT_COL}})
    return fig


# ─── 4. Archetype Radar ───────────────────────────────────────────────────────

def _hex_to_rgba(hex_color: str, alpha: float = 0.15) -> str:
    """Convert '#RRGGBB' hex string to 'rgba(r,g,b,alpha)'."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def plot_archetype_radar(df: pd.DataFrame) -> go.Figure:
    """
    Radar / spider chart showing the mean indicator profile for each stress archetype.
    """
    indicator_cols = [c for c in _INDICATOR_LABELS if c in df.columns]
    if "archetype_id" not in df.columns or not indicator_cols:
        return go.Figure()

    profiles = df.groupby("archetype_id")[indicator_cols].mean()
    categories = [_INDICATOR_LABELS[c] for c in indicator_cols]
    categories_closed = categories + [categories[0]]   # close the polygon

    palette = [
        "#FF6B6B", "#4ECDC4", "#FFE66D",
        "#6BCB77", "#C084FC", "#60A5FA",
    ]

    fig = go.Figure()
    for idx, (archetype_id, row) in enumerate(profiles.iterrows()):
        vals = row[indicator_cols].tolist()
        vals_closed = vals + [vals[0]]
        color = palette[idx % len(palette)]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=categories_closed,
            fill="toself",
            name=f"Archetype {archetype_id}",
            line={"color": color, "width": 2},
            fillcolor=_hex_to_rgba(color, 0.15),
            hovertemplate="<b>%{theta}</b>: %{r:.3f}<extra>Archetype " + str(archetype_id) + "</extra>",
        ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>Stress Archetype Profiles</b>", "font": {"size": 15}},
        polar={
            "bgcolor": "rgba(255,255,255,0.03)",
            "radialaxis": {
                "visible": True,
                "gridcolor": _GRID,
                "tickfont": {"color": "#808080", "size": 9},
                "range": [0, profiles[indicator_cols].values.max() * 1.15 + 0.01],
            },
            "angularaxis": {
                "gridcolor": _GRID,
                "tickfont": {"color": "#c0c0c0", "size": 10},
            },
        },
        showlegend=True,
        height=400,
    )
    fig.update_layout(legend={"orientation": "h", "y": -0.12, "bgcolor": "rgba(0,0,0,0)"})
    return fig


# ─── 5. Indicator Correlation Heatmap ────────────────────────────────────────

def plot_indicator_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Pearson correlation matrix of the 5 stress indicators.
    """
    indicator_cols = [c for c in _INDICATOR_LABELS if c in df.columns]
    if len(indicator_cols) < 2:
        return go.Figure()

    corr = df[indicator_cols].corr()
    labels = [_INDICATOR_LABELS[c] for c in indicator_cols]

    z     = corr.values
    ztext = [[f"{v:.2f}" for v in row] for row in z]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        text=ztext,
        texttemplate="%{text}",
        textfont={"size": 12, "color": _FONT_COL},
        colorscale="RdBu_r",
        zmin=-1, zmax=1,
        showscale=True,
        colorbar={
            "title": {"text": "r", "font": {"color": _FONT_COL}},
            "tickfont": {"color": "#a0a0a0"},
            "thickness": 14,
        },
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>Indicator Correlation Matrix</b>", "font": {"size": 15}},
        xaxis={"tickfont": {"color": _FONT_COL, "size": 10}, "side": "bottom"},
        yaxis={"tickfont": {"color": _FONT_COL, "size": 10}, "autorange": "reversed"},
        height=340,
    )
    return fig


# ─── 6. Seasonal Heatmap ─────────────────────────────────────────────────────

def plot_seasonal_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    SSI as a month × year heatmap. Reveals seasonal climatology patterns.
    """
    df = df.copy()
    df["date"]  = pd.to_datetime(df["date"])
    df["year"]  = df["date"].dt.year
    df["month"] = df["date"].dt.month

    pivot = (
        df.groupby(["year", "month"])["ssi_value"]
        .mean()
        .unstack(level="month")
    )

    month_names = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[month_names[m - 1] for m in pivot.columns],
        y=[str(y) for y in pivot.index],
        colorscale="RdYlGn_r",
        zmin=0, zmax=pivot.values.max(),
        showscale=True,
        hovertemplate="<b>%{y} %{x}</b><br>SSI: %{z:.4f}<extra></extra>",
        colorbar={
            "title": {"text": "SSI", "font": {"color": _FONT_COL}},
            "tickfont": {"color": "#a0a0a0"},
            "thickness": 14,
        },
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>Seasonal SSI Heatmap</b> — Year × Month", "font": {"size": 15}},
        xaxis=_axis("Month"),
        yaxis=_axis("Year", autorange="reversed"),
        height=380,
    )
    return fig


# ─── 7. Anomaly Timeline ─────────────────────────────────────────────────────

def plot_anomaly_timeline(df: pd.DataFrame) -> go.Figure:
    """
    Fraction of hexes flagged as anomalies per month (bar chart).
    """
    if "anomaly_flag" not in df.columns:
        return go.Figure()

    ts = (
        df.groupby("date")["anomaly_flag"]
        .mean()
        .reset_index()
        .rename(columns={"anomaly_flag": "anomaly_rate"})
    )
    ts["date"]         = pd.to_datetime(ts["date"])
    ts["anomaly_pct"]  = ts["anomaly_rate"] * 100
    ts["colour"]       = ts["anomaly_pct"].apply(
        lambda v: "#ef4444" if v >= 15 else ("#fb923c" if v >= 10 else "#facc15")
    )

    fig = go.Figure(go.Bar(
        x=ts["date"],
        y=ts["anomaly_pct"],
        marker_color=ts["colour"],
        hovertemplate="%{x|%b %Y}: <b>%{y:.1f}%</b> flagged<extra></extra>",
        name="Anomaly %",
    ))

    fig.add_hline(
        y=10,
        line={"dash": "dash", "color": "#60A5FA", "width": 1},
        annotation_text="90th pct threshold",
        annotation_font={"color": "#60A5FA", "size": 10},
    )

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>Monthly Anomaly Rate</b> (% hexes &gt; 90th pct SSI)", "font": {"size": 15}},
        xaxis=_axis(""),
        yaxis=_axis("% Anomaly Hexes", ticksuffix="%"),
        height=300,
        bargap=0.2,
    )
    return fig


# ─── 8. Top Stressed Hexes ───────────────────────────────────────────────────

def plot_top_stressed(df: pd.DataFrame, n: int = 20) -> go.Figure:
    """
    Horizontal bar chart of the top-N hexes ranked by mean SSI across all time.
    """
    top = (
        df.groupby("h3_index")["ssi_value"]
        .mean()
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
    )
    top["h3_short"] = top["h3_index"].str[-6:]   # Last 6 chars for readability
    top["colour"] = top["ssi_value"].apply(
        lambda v: "#ef4444" if v >= 0.75 else (
            "#fb923c" if v >= 0.50 else (
            "#facc15" if v >= 0.25 else "#4ade80"
        ))
    )

    fig = go.Figure(go.Bar(
        x=top["ssi_value"],
        y=top["h3_short"],
        orientation="h",
        marker_color=top["colour"],
        hovertemplate="Hex …%{y}<br>Mean SSI: <b>%{x:.4f}</b><extra></extra>",
        text=top["ssi_value"].round(4),
        textposition="outside",
        textfont={"color": _FONT_COL, "size": 10},
    ))

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": f"<b>Top {n} Most Stressed Hexes</b> (time-averaged)", "font": {"size": 15}},
        xaxis=_axis("Mean SSI Score", range=[0, top["ssi_value"].max() * 1.18]),
        yaxis=_axis("H3 Index (last 6 chars)", autorange="reversed"),
        height=max(300, n * 18),
    )
    return fig


# ─── 9. Vulnerability vs SSI Scatter ─────────────────────────────────────────

def plot_vulnerability_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot: mean BPL% (x-axis) vs mean SSI (y-axis) per H3 hex.
    Point size = slum%, colour = urban_vulnerability_idx.
    """
    vuln_cols = ["bpl_pct", "slum_pct", "ssi_value", "urban_vulnerability_idx"]
    available = [c for c in vuln_cols if c in df.columns]
    if len(available) < 2:
        return go.Figure()

    hex_df = df.groupby("h3_index")[available].mean().reset_index()

    x_col    = "bpl_pct"   if "bpl_pct"   in hex_df.columns else available[0]
    y_col    = "ssi_value" if "ssi_value"  in hex_df.columns else available[1]
    size_col = "slum_pct"  if "slum_pct"  in hex_df.columns else None
    col_col  = "urban_vulnerability_idx" if "urban_vulnerability_idx" in hex_df.columns else None

    fig = px.scatter(
        hex_df,
        x=x_col,
        y=y_col,
        size=size_col,
        color=col_col,
        color_continuous_scale="Purples",
        opacity=0.65,
        size_max=14,
        hover_data={"h3_index": True},
        labels={
            x_col:   "Mean BPL Population (%)",
            y_col:   "Mean SSI Score",
            col_col: "Urban Vulnerability",
        },
        height=360,
    )

    fig.update_layout(
        **_LAYOUT_BASE,
        title={"text": "<b>Vulnerability vs Stress</b> — Per-hex averages", "font": {"size": 15}},
        xaxis=_axis("Mean BPL Population (%)"),
        yaxis=_axis("Mean SSI Score"),
        coloraxis_colorbar={
            "title": {"text": "Urban Vuln.", "font": {"color": _FONT_COL}},
            "tickfont": {"color": "#a0a0a0"},
            "thickness": 14,
        },
    )
    return fig
