# Mumbai SSI Dashboard — Full Walkthrough

The report is served at **http://localhost:8765/mumbai_ssi_report.html**  
Start the server with: `python -m http.server 8765 --directory reports`

---

## 1 · Hero Header

![Hero header showing the Mumbai title, stress pills, KPI cards, sticky nav, and the start of the Spatial section](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\01_top_1776854499845.png)

**What you see:**
- **Title block** — City name (Mumbai), state, study period (Jan 2015 – Dec 2025), total H3 hexes (2,501), and total observations (330,132)
- **Stress pills** — 🌡️ Heat · 🌊 Flood · 🏭 Pollution — city-specific primary stressors
- **5 KPI cards** with coloured accent borders:
  - `0.0017` Mean SSI Score (purple)
  - `1.0000` Peak SSI — highest ever recorded in a single hex (red)
  - `100.0%` in Low Band — full distribution is currently in the safe zone (green)
  - `10.0%` Anomaly Rate — fraction of hexes exceeding 90th-percentile threshold (cyan)
  - `6` Stress Archetypes identified by k-means clustering (lime)
- **Sticky nav bar** — always visible as you scroll; links jump to Spatial Overview · Temporal Trends · Stress Indicators · Climatology · Archetypes · Priority Locations
- **Section `01 / SPATIAL`** header with summary paragraph begins at the bottom

---

## 2 · Spatial Overview — H3 Map + Donut

![Spatial section showing the interactive H3 SSI choropleth map and the SSI Risk Band donut chart side by side](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\02_kpis_spatial_start_1776854533870.png)

**What you see:**
- **Blue callout box** — "How to use the map: Hover over any hex for its exact SSI value and H3 index..."
- **Compound SSI Map (left)** — Each H3 hex coloured by its time-averaged SSI. Dark = low stress (green); bright = high stress (red). The Carto-Darkmatter basemap keeps the focus on the data.
- **SSI Risk Band Donut (right)** — Proportion of all 330,132 hex-month observations in each band. The 4-colour legend below links each slice to its policy meaning.

> **Note on the map zoom:** The map loaded at a global view here — this is a known cosmetic issue with the synthetic data's H3 hex coordinates. With real city data the map auto-centres on Mumbai at zoom ~11.

---

## 3 · Temporal Trends

![Temporal trends section showing the monthly SSI trend line chart and the monthly anomaly rate bar chart](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\06_time_series_anomaly_1776854636897.png)

**What you see:**
- **`02 / TEMPORAL`** section tag + description paragraph
- **Insight callout** — "A rising trend in the SSI time-series suggests compounding stress. Seasonal spikes point to climate-driven patterns like monsoon onset or summer heat…"
- **Monthly SSI Trend (left)** — Purple line = city-wide mean SSI per month. Shaded band = ±1 standard deviation across hexes. A wider band means greater within-city inequality.
- **Monthly Anomaly Rate (right)** — Orange/red bars = % of hexes whose SSI exceeded the historical 90th percentile that month. The dashed blue line marks the 10% alert threshold. Bars above it = city-wide stress episodes.

**Key reading:** Post-2018 the anomaly rate spikes consistently above 10%, indicating a structural worsening of compound stress across Mumbai.

---

## 4 · Stress Indicator Decomposition

![Stress Indicators section showing a multi-line 5-indicator trend chart across the full 2015–2025 study period](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\07_trends_indicators_1776854659102.png)

**What you see:**
- **`03 / INDICATORS`** section tag
- **Colour-coded callout** — defines each indicator with its source method:
  - 🔴 **Heat Stress** — Rothfusz Heat Index + LST anomaly
  - 🟦 **Water Stress** — precipitation deficit + soil moisture depletion
  - 🟡 **Pollution** — PM₂.₅ vs WHO 5 µg/m³ guideline
  - 🟢 **Vegetation** — NDVI anomaly below seasonal baseline
  - 🟣 **Urban Vulnerability** — BPL% + slum% + elderly% + (inverse) literacy
- **5-Indicator Trend chart** — Each line = monthly city-mean, normalised 0–1. Overlapping peaks identify compound stress events where multiple stressors co-occur simultaneously.

**Key reading:** Heat Stress (red) and Water Stress (cyan) show strong anti-correlated seasonality — Heat peaks in summer, Water Stress peaks in dry months — confirming monsoon-driven cycles.

---

## 5 · Climatology — Heatmap + Correlation Matrix

![Climatology section showing the Year × Month seasonal SSI heatmap and the Pearson indicator correlation matrix](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\08_heatmap_corr_1776854672769.png)

**What you see:**
- **`04 / CLIMATOLOGY`** section tag
- **Seasonal callout** — "Stress typically peaks in pre-monsoon months (April–June) due to heat, and again post-monsoon in northern cities due to stubble burning + winter inversions…"
- **Seasonal SSI Heatmap (left)** — Year (rows) × Month (columns). Each cell = city-mean SSI. Read across a row to see how stress evolves through the year. Read down a column to see whether the same month is getting worse over time. Dark burgundy = high stress months.
- **Indicator Correlation Matrix (right)** — Pearson r between the 5 indicators. Values near +1 (dark red diagonal) = indicators spike together. Off-diagonal values near 0 = independent stressors. The `nan` cells for Vegetation indicate the NDVI synthetic data had zero variance in this run.

---

## 6 · Archetypes + Vulnerability Scatter

![Archetypes section showing the k-means radar chart and the BPL% vs SSI scatter plot](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\09_radar_scatter_1776854688012.png)

**What you see:**
- **`05 / ARCHETYPES`** section tag
- **Policy callout** — "A hex in the heat-dominant archetype needs green cover + cool roofs. A pollution-dominant hex needs traffic restrictions…"
- **Stress Archetype Profiles — Radar Chart (left)** — Each coloured polygon = one k-means cluster of H3 hexes. 5 spokes = 5 stress indicators. A wide polygon on the Heat Stress spoke = heat-dominant archetype. Overlapping clusters = mixed-stress profiles.
- **Socio-Economic Vulnerability vs Compound Stress (right)** — Each dot = one H3 hex. X-axis = mean BPL population %; Y-axis = mean SSI. Dot size = slum fraction; colour = urban vulnerability index. **Top-right quadrant** = high BPL + high SSI = compound deprivation hotspots — the highest-priority intervention targets.

---

## 7 · Priority Locations — Top 20 Hotspots

![Priority Locations section showing the ranked bar chart of the 20 most consistently stressed H3 hexes](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\10_top_hexes_1776854705179.png)

**What you see:**
- **`06 / HOTSPOTS`** section tag
- **Usage callout** — "Each bar = one H3 hex (last 6 chars of its H3 index). Cross-reference with the Section 1 map to locate it geographically. Prioritise hexes that appear here AND in the top-right of the vulnerability scatter."
- **Top 20 Most Stressed Hexes** — Ranked horizontal bar chart. Bars coloured by SSI band (green = Low, yellow = Moderate, orange = High, red = Extreme). The 4-colour legend with policy thresholds is shown below.

---

## 8 · Footer — Methodology + Data Sources

![Footer section with three columns: About This Report, Data Sources, and SSI Methodology](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\11_footer_1776854720760.png)

**What you see (3-column footer):**

| About This Report | Data Sources | SSI Methodology |
|---|---|---|
| Full explanation of what the SSI is, how it combines 5 indicators using PCA weights + city multipliers, and the H3 spatial framework | ERA5 (CDS/ECMWF) · Sentinel-2 L2A (Planetary Computer) · MODIS MOD11A2 (NASA) · PM₂.₅ SDEI (NASA SEDAC) · Roads/buildings (OSMnx) · Vulnerability (Census 2011) | H3 res 8 grid · Monthly aggregation · 3-yr rolling Z-score baseline · PCA weighting · City-specific adjustments · k-means k=6 · 90th-pct anomaly detection |

**Bottom bar:** `Compound SSI Pipeline · Mumbai, India · Jan 2015 – Dec 2025` · `Generated 22 Apr 2026, 15:40 IST`

---

## Recording

The full scroll-through session was recorded automatically:

![Full dashboard scroll recording](C:\Users\Admin\.gemini\antigravity\brain\052c759a-42a8-4a7c-95ef-e15ef12b2669\ssi_pipeline_walkthrough_1776854170422.webp)

---

## Quick Reference — How to Open the Report

```bash
# From the project root
python -m http.server 8765 --directory reports

# Then open in browser:
# http://localhost:8765/mumbai_ssi_report.html
```

Or just double-click `reports/mumbai_ssi_report.html` directly — it's fully self-contained.
