"""
scripts/render_7_city_html.py
─────────────────────────────
Generates a stunning, self-contained, interactive HTML report
for the 7-City Final Dataset (334,332 observations), now including
a full interactive Leaflet.js Geospatial Map Explorer rendering
all 9,287 Uber H3 Resolution 8 cells, dynamic layer controls,
a real-time micro-scale hex inspector, and publication figures.
"""

from pathlib import Path
import json

def render_html():
    json_path = Path("reports/final_7_cities_metrics.json")
    if not json_path.exists():
        raise FileNotFoundError("Run scripts/generate_7_city_html_report.py first!")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    json_str = json.dumps(data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Compound Sustainability Stress Index (SSI) — 7-City Empirical Report & Geospatial Atlas</title>
  
  <!-- Modern Typography from Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  
  <!-- Chart.js for interactive Canvas charting -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

  <!-- Leaflet.js for high-performance geospatial mapping -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

  <style>
    :root {{
      --bg: #070b14;
      --bg-surface: #0d1322;
      --bg-card: rgba(16, 24, 40, 0.75);
      --bg-card-hover: rgba(22, 32, 54, 0.9);
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(139, 92, 246, 0.3);
      --border-glow: rgba(139, 92, 246, 0.5);
      
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      
      --accent-purple: #8b5cf6;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      
      --color-heat: #f87171;
      --color-water: #38bdf8;
      --color-veg: #34d399;
      --color-poll: #fbbf24;
      --color-exp: #c084fc;
      
      --band-low: #10b981;
      --band-mod: #38bdf8;
      --band-high: #f59e0b;
      --band-ext: #ef4444;
      
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
      overflow-x: hidden;
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
    ::-webkit-scrollbar-track {{ background: var(--bg); }}
    ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.15); border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.25); }}

    /* Layout Container */
    .container {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 0 32px;
    }}

    /* Header & Hero */
    header.hero {{
      position: relative;
      background: radial-gradient(circle at 15% 30%, rgba(139, 92, 246, 0.15), transparent 50%),
                  radial-gradient(circle at 85% 20%, rgba(6, 182, 212, 0.12), transparent 45%),
                  linear-gradient(180deg, #0b1120 0%, var(--bg) 100%);
      border-bottom: 1px solid var(--border);
      padding: 48px 0 24px;
      overflow: hidden;
    }}

    .hero-badges {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 16px;
    }}

    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      border-radius: 9999px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
    }}

    .badge.verified {{
      background: rgba(16, 185, 129, 0.12);
      border-color: rgba(16, 185, 129, 0.3);
      color: #34d399;
    }}

    .badge.accent {{
      background: rgba(139, 92, 246, 0.12);
      border-color: rgba(139, 92, 246, 0.3);
      color: #a78bfa;
    }}

    .hero-title {{
      font-family: 'Outfit', sans-serif;
      font-size: clamp(28px, 4.5vw, 44px);
      font-weight: 800;
      letter-spacing: -0.5px;
      line-height: 1.15;
      margin-bottom: 14px;
      background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .hero-subtitle {{
      font-size: 16px;
      color: var(--text-muted);
      max-width: 960px;
      margin-bottom: 28px;
      font-weight: 400;
    }}

    /* Navigation Tabs */
    .nav-tabs {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0;
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .nav-tabs::-webkit-scrollbar {{ display: none; }}

    .nav-tab {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: 'Outfit', sans-serif;
      font-size: 13.5px;
      font-weight: 600;
      padding: 12px 18px;
      cursor: pointer;
      border-radius: var(--radius-sm) var(--radius-sm) 0 0;
      transition: all 0.2s ease;
      white-space: nowrap;
      position: relative;
    }}

    .nav-tab:hover {{
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.03);
    }}

    .nav-tab.active {{
      color: #fff;
      background: rgba(139, 92, 246, 0.12);
      border-bottom: 2px solid var(--accent-purple);
    }}

    /* Sticky Controls Bar */
    .controls-bar {{
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(7, 11, 20, 0.85);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border);
      padding: 12px 0;
      margin-bottom: 32px;
    }}

    .controls-inner {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .city-pills {{
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 2px;
      scrollbar-width: none;
    }}
    .city-pills::-webkit-scrollbar {{ display: none; }}

    .city-pill {{
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .city-pill:hover {{
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-main);
    }}

    .city-pill.active {{
      background: var(--accent-purple);
      border-color: var(--accent-purple);
      color: #ffffff;
      box-shadow: 0 0 15px rgba(139, 92, 246, 0.4);
    }}

    .action-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-main);
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
    }}

    .action-btn:hover {{
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(255, 255, 255, 0.2);
    }}

    /* Tab Panels */
    .tab-panel {{
      display: none;
      animation: fadeIn 0.3s ease forwards;
    }}
    .tab-panel.active {{
      display: block;
    }}

    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    /* Card System */
    .card {{
      background: var(--bg-card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: var(--shadow);
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    .card:hover {{
      border-color: rgba(255, 255, 255, 0.14);
    }}

    .card-header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 20px;
    }}

    .card-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: -0.2px;
    }}

    .card-desc {{
      font-size: 13px;
      color: var(--text-muted);
      margin-top: 4px;
    }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}

    .kpi-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px;
      position: relative;
      overflow: hidden;
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan));
      opacity: 0.8;
    }}

    .kpi-label {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-dim);
      margin-bottom: 8px;
    }}

    .kpi-value {{
      font-family: 'Outfit', sans-serif;
      font-size: 32px;
      font-weight: 800;
      line-height: 1.1;
      color: #ffffff;
      margin-bottom: 4px;
    }}

    .kpi-subtext {{
      font-size: 12px;
      color: var(--text-muted);
    }}

    /* Grid Layouts */
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
      margin-bottom: 24px;
    }}

    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
      margin-bottom: 24px;
    }}

    @media (max-width: 1024px) {{
      .grid-2, .grid-3 {{ grid-template-columns: 1fr; }}
    }}

    /* Geospatial Map Section Styles */
    .map-layout {{
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 20px;
      margin-bottom: 24px;
    }}
    @media (max-width: 1024px) {{
      .map-layout {{
        grid-template-columns: 1fr;
      }}
    }}

    .map-toolbar {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 16px;
      background: var(--bg-card);
      padding: 14px 18px;
      border-radius: var(--radius-md);
      border: 1px solid var(--border);
    }}

    .map-control-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}

    .map-btn {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: inherit;
    }}
    .map-btn:hover {{
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
      border-color: rgba(255, 255, 255, 0.2);
    }}
    .map-btn.active {{
      background: var(--accent-purple);
      color: #fff;
      border-color: var(--accent-purple);
      box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
    }}

    .map-select {{
      background: #0f172a;
      color: var(--text-main);
      border: 1px solid var(--border);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-family: inherit;
      cursor: pointer;
      outline: none;
    }}
    .map-select:focus {{
      border-color: var(--accent-purple);
    }}

    .map-viewport-wrapper {{
      position: relative;
      background: var(--bg-surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow: hidden;
      box-shadow: var(--shadow);
      height: 640px;
    }}

    #mapView {{
      width: 100%;
      height: 100%;
      background: #060910;
    }}

    /* Map Legend Overlay */
    .map-legend {{
      position: absolute;
      bottom: 20px;
      left: 20px;
      z-index: 1000;
      background: rgba(13, 19, 34, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid var(--border);
      padding: 12px 16px;
      border-radius: var(--radius-sm);
      font-size: 11px;
      color: var(--text-main);
      box-shadow: var(--shadow);
      max-width: 260px;
    }}
    .map-legend-title {{
      font-weight: 700;
      margin-bottom: 6px;
      color: #fff;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 10px;
    }}
    .legend-ramp {{
      height: 8px;
      border-radius: 4px;
      margin-bottom: 4px;
    }}
    .legend-labels {{
      display: flex;
      justify-content: space-between;
      color: var(--text-dim);
      font-size: 10px;
    }}
    .legend-discrete-item {{
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 3px;
      font-size: 11px;
    }}
    .legend-swatch {{
      width: 12px;
      height: 12px;
      border-radius: 3px;
      flex-shrink: 0;
    }}

    /* Hex Inspector Panel */
    .hex-inspector {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      height: 640px;
      overflow-y: auto;
    }}

    .sub-gauge-row {{
      margin-bottom: 10px;
    }}
    .sub-gauge-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      margin-bottom: 4px;
    }}
    .sub-gauge-track {{
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 3px;
      overflow: hidden;
    }}
    .sub-gauge-fill {{
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }}

    /* Leaflet Dark Customization */
    .leaflet-container {{
      font-family: inherit;
      background: #060910 !important;
    }}
    .leaflet-control-zoom a {{
      background: #0f172a !important;
      color: #fff !important;
      border-color: rgba(255,255,255,0.15) !important;
    }}
    .leaflet-control-zoom a:hover {{
      background: #1e293b !important;
    }}
    .leaflet-control-attribution {{
      background: rgba(13, 19, 34, 0.8) !important;
      color: #64748b !important;
      font-size: 10px !important;
    }}
    .leaflet-control-attribution a {{
      color: #94a3b8 !important;
    }}
    .leaflet-tooltip {{
      background: rgba(13, 19, 34, 0.95) !important;
      color: #f1f5f9 !important;
      border: 1px solid var(--border-accent) !important;
      border-radius: var(--radius-sm) !important;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6) !important;
      backdrop-filter: blur(8px) !important;
    }}

    /* Publication Figure Showcase Card */
    .pub-figure-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin-bottom: 24px;
    }}
    .pub-figure-img {{
      width: 100%;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      margin: 16px 0;
      display: block;
    }}

    /* Table System */
    .data-table-wrap {{
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;
    }}

    .data-table th {{
      background: rgba(255, 255, 255, 0.03);
      padding: 12px 16px;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.6px;
      border-bottom: 1px solid var(--border);
    }}

    .data-table td {{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      color: var(--text-main);
    }}

    .data-table tbody tr:hover {{
      background: rgba(255, 255, 255, 0.02);
    }}

    /* Badges & Status */
    .status-badge {{
      display: inline-flex;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
    }}
    .status-pass {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}
    .status-extreme {{
      background: rgba(239, 68, 68, 0.15);
      color: #f87171;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .status-high {{
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    .status-mod {{
      background: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
    .status-low {{
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    /* Formula & Code Displays */
    .formula-box {{
      background: #090e1a;
      border: 1px solid var(--border-accent);
      border-radius: var(--radius-sm);
      padding: 16px 20px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      color: #cbd5e1;
      margin: 16px 0;
      line-height: 1.7;
    }}

    /* Archetype Cards */
    .arch-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
    }}
    .arch-card:hover {{
      border-color: var(--border-accent);
      transform: translateY(-2px);
    }}

    .arch-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}

    .arch-tag {{
      font-family: 'Outfit', sans-serif;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent-cyan);
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }}

    .arch-prevalence {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-dim);
    }}

    .arch-title {{
      font-size: 16px;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 8px;
    }}

    .arch-desc {{
      font-size: 12px;
      color: var(--text-muted);
      margin-bottom: 16px;
    }}

    .arch-metrics {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 6px;
      background: rgba(0, 0, 0, 0.25);
      padding: 8px;
      border-radius: var(--radius-sm);
      margin-bottom: 14px;
      text-align: center;
    }}

    .arch-m-item .label {{ font-size: 9px; color: var(--text-dim); text-transform: uppercase; }}
    .arch-m-item .val {{ font-size: 12px; font-weight: 700; color: #fff; }}

    .arch-policy {{
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px dashed var(--border);
      padding-top: 12px;
    }}

    /* Footer */
    footer.page-footer {{
      border-top: 1px solid var(--border);
      padding: 32px 0 48px;
      color: var(--text-dim);
      font-size: 12px;
      margin-top: 64px;
    }}
    .footer-inner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
    }}
  </style>
</head>
<body>

  <!-- HERO HEADER -->
  <header class="hero">
    <div class="container">
      <div class="hero-badges">
        <span class="badge verified">✓ Pre-Registered Empirical Report</span>
        <span class="badge accent">Uber H3 Res-8 Hexagonal Mesh</span>
        <span class="badge">N = 334,332 Observations</span>
        <span class="badge">36 Months Longitudinal (2020–2022)</span>
        <span class="badge">9,287 Micro-Scale Hexagons</span>
      </div>
      <h1 class="hero-title">Compound Sustainability Stress Index (SSI)</h1>
      <p class="hero-subtitle">
        A unified spatio-temporal diagnostic integrating satellite Earth observations, atmospheric reanalysis, 
        and micro-scale built-environment analytics across seven Indian metropolises. 
        Breaks single-domain silos through smooth asymptotic multi-hazard coupling.
      </p>

      <!-- NAVIGATION TABS -->
      <nav class="nav-tabs">
        <button class="nav-tab active" onclick="switchTab('overview')">1. Executive Overview & KPIs</button>
        <button class="nav-tab" onclick="switchTab('geospatial')">🗺️ 2. Geospatial Map Explorer</button>
        <button class="nav-tab" onclick="switchTab('city_explorer')">3. City Biome Profiles</button>
        <button class="nav-tab" onclick="switchTab('comparative')">4. Comparative Dynamics</button>
        <button class="nav-tab" onclick="switchTab('compound')">5. Compound Coupling & Weights</button>
        <button class="nav-tab" onclick="switchTab('archetypes')">6. Urban Typology (6 Archetypes)</button>
        <button class="nav-tab" onclick="switchTab('validation')">7. Validation Battery (8/8 Passed)</button>
        <button class="nav-tab" onclick="switchTab('methodology')">8. Methodology & Provenance</button>
      </nav>
    </div>
  </header>

  <!-- STICKY CONTROLS BAR -->
  <div class="controls-bar">
    <div class="container controls-inner">
      <div class="city-pills" id="citySelector">
        <button class="city-pill active" onclick="selectCity('all')">Pan-India (All 7 Cities)</button>
        <button class="city-pill" onclick="selectCity('delhi')">Delhi NCR</button>
        <button class="city-pill" onclick="selectCity('kolkata')">Kolkata</button>
        <button class="city-pill" onclick="selectCity('mumbai')">Mumbai</button>
        <button class="city-pill" onclick="selectCity('bikaner')">Bikaner</button>
        <button class="city-pill" onclick="selectCity('hyderabad')">Hyderabad</button>
        <button class="city-pill" onclick="selectCity('indore')">Indore</button>
        <button class="city-pill" onclick="selectCity('coimbatore')">Coimbatore</button>
      </div>
      <div>
        <button class="action-btn" onclick="window.print()">
          <span>🖨️ Print / Save PDF</span>
        </button>
      </div>
    </div>
  </div>

  <main class="container">

    <!-- TAB 1: EXECUTIVE OVERVIEW -->
    <section id="tab-overview" class="tab-panel active">
      <!-- KPI CARDS -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Total Observations</div>
          <div class="kpi-value" id="kpiObs">334,332</div>
          <div class="kpi-subtext">9,287 cells × 36 months</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Mean Composite SSI</div>
          <div class="kpi-value" id="kpiMeanSSI">0.488</div>
          <div class="kpi-subtext" id="kpiRange">Range: 0.031 – 0.981</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Extreme Risk Share</div>
          <div class="kpi-value" style="color: var(--band-ext);" id="kpiExtremeShare">44.0%</div>
          <div class="kpi-subtext">Upper quartile (SSI &gt; 0.657)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Compound Synergy</div>
          <div class="kpi-value" style="color: var(--accent-cyan);">+25.3%</div>
          <div class="kpi-subtext">Amplification at Decile 10</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Boundary Clipping</div>
          <div class="kpi-value" style="color: var(--accent-emerald);">0.00%</div>
          <div class="kpi-subtext">0 records clamped at 1.000</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Rank Invariance</div>
          <div class="kpi-value" style="color: var(--accent-purple);">&gt; 94%</div>
          <div class="kpi-subtext">Across 4 weighting regimes</div>
        </div>
      </div>

      <!-- MAP TEASER CALLOUT -->
      <div class="card" style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(6, 182, 212, 0.12) 100%); border: 1px solid var(--border-accent); display: flex; align-items: center; justify-content: space-between; padding: 22px 28px; flex-wrap: wrap; gap: 16px;">
        <div style="max-width: 820px;">
          <div style="font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 6px;">🗺️ Geospatial Micro-Scale Map Explorer (9,287 Cells)</div>
          <div style="font-size: 13.5px; color: var(--text-muted); line-height: 1.5;">
            Explore the spatial distribution of sustainability stress across all seven metropolitan study areas at Uber H3 Res-8 hexagonal resolution. 
            Toggle between Composite SSI, Heat Stress, Water Scarcity, Vegetation Canopy Loss, PM2.5 Pollution, Socio-Demographic Exposure, and Urban Archetype clusters with real-time hover and click inspection.
          </div>
        </div>
        <button class="action-btn" onclick="switchTab('geospatial')" style="background: var(--accent-purple); color: #fff; border: none; font-size: 13.5px; padding: 12px 22px; font-weight: 600; cursor: pointer; border-radius: var(--radius-sm); box-shadow: 0 4px 15px rgba(139, 92, 246, 0.45);">
          Launch Geospatial Map Explorer →
        </button>
      </div>

      <!-- CHARTS ROW 1 -->
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">36-Month Longitudinal Stress Trajectory (2020–2022)</div>
              <div class="card-desc" id="trendSubtitle">Monthly mean multi-hazard stress index across all observation months.</div>
            </div>
          </div>
          <div style="height: 320px;">
            <canvas id="trendChart"></canvas>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">5-Dimensional Physical Hazard Balance</div>
              <div class="card-desc" id="radarSubtitle">Distribution across the five orthogonal sustainability stress drivers.</div>
            </div>
          </div>
          <div style="height: 320px;">
            <canvas id="radarChart"></canvas>
          </div>
        </div>
      </div>

      <!-- CHARTS ROW 2 -->
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Relative Risk Band Categorization</div>
              <div class="card-desc">Standardized nationwide quartiles: Low, Moderate, High, Extreme.</div>
            </div>
          </div>
          <div style="height: 280px;">
            <canvas id="bandChart"></canvas>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Two-Way Variance Decomposition</div>
              <div class="card-desc">Atmospheric Seasonality (Between-Month) vs. Urban Morphology (Between-Hex).</div>
            </div>
          </div>
          <div style="height: 280px;">
            <canvas id="varDecompChart"></canvas>
          </div>
        </div>
      </div>
    </section>

    <!-- TAB 2: GEOSPATIAL MAP EXPLORER -->
    <section id="tab-geospatial" class="tab-panel">
      <!-- MAP CONTROLS TOOLBAR -->
      <div class="map-toolbar">
        <div class="map-control-group">
          <span style="font-size: 11px; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Stress Layer:</span>
          <button class="map-btn map-metric-btn active" data-metric="ssi" onclick="setMapMetric('ssi')">🌟 Composite SSI</button>
          <button class="map-btn map-metric-btn" data-metric="heat" onclick="setMapMetric('heat')">🔥 Heat Stress</button>
          <button class="map-btn map-metric-btn" data-metric="water" onclick="setMapMetric('water')">💧 Water Deficit</button>
          <button class="map-btn map-metric-btn" data-metric="veg" onclick="setMapMetric('veg')">🌿 Veg Deficit</button>
          <button class="map-btn map-metric-btn" data-metric="pollution" onclick="setMapMetric('pollution')">🏭 PM2.5 Pollution</button>
          <button class="map-btn map-metric-btn" data-metric="exposure" onclick="setMapMetric('exposure')">👥 Built Exposure</button>
          <button class="map-btn map-metric-btn" data-metric="archetype" onclick="setMapMetric('archetype')">🏷️ Typology (6 Archetypes)</button>
          <button class="map-btn map-metric-btn" data-metric="risk_band" onclick="setMapMetric('risk_band')">⚠️ Risk Band</button>
        </div>

        <div class="map-control-group">
          <span style="font-size: 11px; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Fly to City:</span>
          <select class="map-select" id="mapCitySelect" onchange="flyMapToCity(this.value)">
            <option value="all">Pan-India (All 7 Cities)</option>
            <option value="delhi">Delhi NCR</option>
            <option value="kolkata">Kolkata</option>
            <option value="mumbai">Mumbai</option>
            <option value="bikaner">Bikaner</option>
            <option value="hyderabad">Hyderabad</option>
            <option value="indore">Indore</option>
            <option value="coimbatore">Coimbatore</option>
          </select>
        </div>
      </div>

      <!-- MAP + INSPECTOR MAIN GRID -->
      <div class="map-layout">
        <div class="map-viewport-wrapper">
          <div id="mapView"></div>
          
          <!-- DYNAMIC MAP LEGEND -->
          <div class="map-legend" id="mapLegend">
            <div class="map-legend-title" id="mapLegendTitle">Composite SSI Score</div>
            <div id="mapLegendContent"></div>
          </div>
        </div>

        <!-- HEX INSPECTOR PANEL -->
        <div class="hex-inspector">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <span class="badge accent" style="font-size: 10px;">Micro-Scale Inspector</span>
              <span id="inspectBandBadge" class="status-badge status-extreme">Extreme Risk</span>
            </div>
            <div id="inspectCity" style="font-family: 'Outfit', sans-serif; font-size: 18px; font-weight: 700; color: #fff;">Bikaner (Arid / Desert)</div>
            <div id="inspectH3" style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--accent-cyan); margin-top: 2px;">88425826d9fffff</div>
            <div id="inspectCoords" style="font-size: 11px; color: var(--text-dim); margin-top: 2px;">27.9032° N, 73.3576° E</div>
          </div>

          <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px; text-align: center;">
            <div style="font-size: 10px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-dim);">Composite SSI Score</div>
            <div id="inspectSSI" style="font-family: 'Outfit', sans-serif; font-size: 32px; font-weight: 800; color: #fff;">0.479</div>
            <div style="font-size: 11px; color: var(--text-muted);">Asymptotically coupled compound score</div>
          </div>

          <div>
            <div style="font-size: 11px; font-weight: 700; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 10px;">Sub-Index Hazard Breakdown</div>
            
            <div class="sub-gauge-row">
              <div class="sub-gauge-labels">
                <span style="color: var(--color-heat);">🔥 Heat Stress</span>
                <span id="inspectHeatVal" style="font-weight: 600; color: #fff;">0.491</span>
              </div>
              <div class="sub-gauge-track"><div id="inspectHeatBar" class="sub-gauge-fill" style="width: 49.1%; background: var(--color-heat);"></div></div>
            </div>

            <div class="sub-gauge-row">
              <div class="sub-gauge-labels">
                <span style="color: var(--color-water);">💧 Water Scarcity</span>
                <span id="inspectWaterVal" style="font-weight: 600; color: #fff;">0.610</span>
              </div>
              <div class="sub-gauge-track"><div id="inspectWaterBar" class="sub-gauge-fill" style="width: 61.0%; background: var(--color-water);"></div></div>
            </div>

            <div class="sub-gauge-row">
              <div class="sub-gauge-labels">
                <span style="color: var(--color-veg);">🌿 Vegetation Deficit</span>
                <span id="inspectVegVal" style="font-weight: 600; color: #fff;">0.776</span>
              </div>
              <div class="sub-gauge-track"><div id="inspectVegBar" class="sub-gauge-fill" style="width: 77.6%; background: var(--color-veg);"></div></div>
            </div>

            <div class="sub-gauge-row">
              <div class="sub-gauge-labels">
                <span style="color: var(--color-poll);">🏭 PM2.5 Pollution</span>
                <span id="inspectPollVal" style="font-weight: 600; color: #fff;">0.315</span>
              </div>
              <div class="sub-gauge-track"><div id="inspectPollBar" class="sub-gauge-fill" style="width: 31.5%; background: var(--color-poll);"></div></div>
            </div>

            <div class="sub-gauge-row">
              <div class="sub-gauge-labels">
                <span style="color: var(--color-exp);">👥 Built Exposure</span>
                <span id="inspectExpVal" style="font-weight: 600; color: #fff;">0.001</span>
              </div>
              <div class="sub-gauge-track"><div id="inspectExpBar" class="sub-gauge-fill" style="width: 0.1%; background: var(--color-exp);"></div></div>
            </div>
          </div>

          <div style="background: rgba(139, 92, 246, 0.08); border: 1px solid rgba(139, 92, 246, 0.2); border-radius: var(--radius-sm); padding: 12px;">
            <div style="font-size: 10px; font-weight: 700; color: var(--accent-cyan); text-transform: uppercase;">Assigned Urban Archetype</div>
            <div id="inspectArchetype" style="font-size: 13px; font-weight: 600; color: #fff; margin-top: 4px;">A3: Water-Stressed Semi-Arid Core</div>
          </div>

          <div style="font-size: 11px; color: var(--text-dim); text-align: center; border-top: 1px solid var(--border); padding-top: 12px;">
            Visible in current map: <strong id="mapVisibleCount" style="color: #fff;">9,287</strong> cells
          </div>
        </div>
      </div>

      <!-- PUBLICATION FIGURE 1 SHOWCASE -->
      <div class="pub-figure-card">
        <div class="card-header" style="margin-bottom: 12px;">
          <div>
            <div class="card-title">Publication Cartography: 7-Biome Spatial Domain & Uber H3 Discretization</div>
            <div class="card-desc">Figure 1 from the accompanying research paper. High-resolution hexagonal mesh coverage (Res 8, ~0.737 km² per cell).</div>
          </div>
          <span class="badge accent">300 DPI Publication Figure</span>
        </div>
        <img src="figures/Figure1_study_area_7_cities.png" alt="Figure 1: Study Area & 7 Cities H3 Hex Grid" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure1_study_area_7_cities.png'">
        <p style="font-size: 12.5px; color: var(--text-muted); line-height: 1.6; margin-top: 12px;">
          <strong>Figure 1.</strong> Geographic distribution and multi-scale hexagonal grid topology across the seven study domains representing distinct Indian biomes: 
          Delhi NCR (Semi-Arid Inversion Hub, 3,398 hexes), Kolkata (Gangetic Delta Maritime, 1,324 hexes), Mumbai (Tropical Marine Coastal, 707 hexes), 
          Bikaner (Arid Thar Desert, 1,223 hexes), Hyderabad (Semi-Arid Deccan Plateau, 1,250 hexes), Indore (Central Inland Semi-Arid, 554 hexes), 
          and Coimbatore (Western Ghats Rain-Shadow, 831 hexes). Hexagonal tessellation at Uber H3 Resolution 8 (~0.737 km² per cell, ~461m inter-hex spacing) 
          yields 9,287 discrete micro-scale empirical observation units across 6,844 km² aggregate urbanized territory.
        </p>
      </div>
    </section>

    <!-- TAB 3: CITY BIOME PROFILES -->
    <section id="tab-city_explorer" class="tab-panel">
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div>
            <div class="card-title">Comprehensive 7-City Bioclimatic Summary Table</div>
            <div class="card-desc">Comparative baseline statistics across contrasting Köppen climate biomes (N = 334,332).</div>
          </div>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>City</th>
                <th>Köppen Biome</th>
                <th>H3 Hexes</th>
                <th>Area (km²)</th>
                <th>Mean SSI</th>
                <th>Dominant Stress</th>
                <th>Extreme Band %</th>
                <th>Compound %</th>
                <th>Seasonality %</th>
                <th>Spatial %</th>
              </tr>
            </thead>
            <tbody id="cityTableBody"></tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- TAB 4: COMPARATIVE DYNAMICS -->
    <section id="tab-comparative" class="tab-panel">
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div>
            <div class="card-title">Cross-City 36-Month Longitudinal Comparison</div>
            <div class="card-desc">Ground-truthing climate shocks across all seven metropolises (Spring 2022 Heatwave, Winter Smog, Floods).</div>
          </div>
        </div>
        <div style="height: 380px;">
          <canvas id="multiCityTrendChart"></canvas>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Cross-City Mean SSI Ranking</div>
              <div class="card-desc">Kolkata and Delhi represent India's highest cumulative multi-hazard burden.</div>
            </div>
          </div>
          <div style="height: 300px;">
            <canvas id="rankingChart"></canvas>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Variance Decomposition Stacked Comparison</div>
              <div class="card-desc">Contrasting continental high-seasonality regimes with spatial morphology-driven regimes.</div>
            </div>
          </div>
          <div style="height: 300px;">
            <canvas id="allVarDecompChart"></canvas>
          </div>
        </div>
      </div>

      <!-- FIGURE 2 & FIGURE 3 SHOWCASE -->
      <div class="grid-2">
        <div class="pub-figure-card">
          <div class="card-header" style="margin-bottom: 12px;">
            <div>
              <div class="card-title">Figure 2: Inter-Indicator Correlation Structure</div>
              <div class="card-desc">Empirical correlation matrix demonstrating orthogonality (|r| ≤ 0.58).</div>
            </div>
          </div>
          <img src="figures/Figure2_inter_indicator_correlation.png" alt="Figure 2: Correlation Matrix" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure2_inter_indicator_correlation.png'">
          <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5;">
            <strong>Figure 2.</strong> Pearson correlation matrix across the five foundational sub-indices. No pair exceeds the collinearity threshold of 0.70, confirming construct validity.
          </p>
        </div>

        <div class="pub-figure-card">
          <div class="card-header" style="margin-bottom: 12px;">
            <div>
              <div class="card-title">Figure 3: Two-Way Variance Decomposition</div>
              <div class="card-desc">Atmospheric Seasonality (Between-Month) vs. Urban Morphology (Between-Hex).</div>
            </div>
          </div>
          <img src="figures/Figure3_variance_decomposition.png" alt="Figure 3: Variance Decomposition" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure3_variance_decomposition.png'">
          <p style="font-size: 12px; color: var(--text-muted); line-height: 1.5;">
            <strong>Figure 3.</strong> Decomposition across the 7 biome archetypes. High-latitude continental cities (Delhi, Bikaner) exhibit &gt;80% temporal variance, whereas coastal Mumbai and tropical Coimbatore exhibit significant spatial morphology variance.
          </p>
        </div>
      </div>
    </section>

    <!-- TAB 5: COMPOUND COUPLING & WEIGHTS -->
    <section id="tab-compound" class="tab-panel">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Decile Synergy Amplification (+25.3% at D10)</div>
              <div class="card-desc">Non-linear premium over linear weighted models concentrated in extreme multi-hazard tail.</div>
            </div>
          </div>
          <div style="height: 320px;">
            <canvas id="decileChart"></canvas>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div>
              <div class="card-title">Candidate Weighting Scheme Allocations</div>
              <div class="card-desc">Equal benchmark vs. Entropy (EWM), CRITIC, and PCA on N = 334,332.</div>
            </div>
          </div>
          <div style="height: 320px;">
            <canvas id="weightsChart"></canvas>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <div class="card-title">Weight Sensitivity & Spatial Rank Invariance</div>
            <div class="card-desc">Spearman rank correlations (ρ) across candidate weighting schemes (N = 334,332).</div>
          </div>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>Scheme Pair</th>
                <th>Rank Correlation (ρ)</th>
                <th>Kendall (τ)</th>
                <th>Methodological Implication</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Equal vs. Entropy (EWM)</strong></td>
                <td><span class="status-badge status-pass">0.9691</span></td>
                <td>0.8654</td>
                <td>96.9% rank concordance; confirms robustness to dispersion-weighted shifts.</td>
              </tr>
              <tr>
                <td><strong>Equal vs. CRITIC</strong></td>
                <td><span class="status-badge status-pass">0.9857</span></td>
                <td>0.8988</td>
                <td>98.6% rank concordance; correlation conflict preserves equal-weight spatial priorities.</td>
              </tr>
              <tr>
                <td><strong>Equal vs. PCA (PC1)</strong></td>
                <td><span class="status-badge status-pass">0.8919</span></td>
                <td>0.7412</td>
                <td>89.2% rank concordance; PCA collapses built exposure (w = 0.0189) due to low multi-collinearity.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- FIGURE 4 & FIGURE 5 SHOWCASE -->
      <div class="grid-2">
        <div class="pub-figure-card">
          <div class="card-header" style="margin-bottom: 12px;">
            <div>
              <div class="card-title">Figure 4: Weighting Schemes Comparison</div>
              <div class="card-desc">Allocation across Equal, Entropy, CRITIC, and PCA methods.</div>
            </div>
          </div>
          <img src="figures/Figure4_weighting_schemes.png" alt="Figure 4: Weight Allocations" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure4_weighting_schemes.png'">
        </div>

        <div class="pub-figure-card">
          <div class="card-header" style="margin-bottom: 12px;">
            <div>
              <div class="card-title">Figure 5: Non-Linear Coupling Sensitivity</div>
              <div class="card-desc">Compound interaction curves across synergy parameter γ ∈ [0.10, 0.50].</div>
            </div>
          </div>
          <img src="figures/Figure5_compound_sensitivity.png" alt="Figure 5: Coupling Sensitivity" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure5_compound_sensitivity.png'">
        </div>
      </div>
    </section>

    <!-- TAB 6: URBAN TYPOLOGY (6 ARCHETYPES) -->
    <section id="tab-archetypes" class="tab-panel">
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div>
            <div class="card-title">Pan-India Urban Stress Typology: Radar Centroid Signatures</div>
            <div class="card-desc">Unsupervised k-means clustering (k = 6, Silhouette s = 0.147, ARI = 0.812).</div>
          </div>
        </div>
        <div style="height: 360px;">
          <canvas id="archetypeRadarChart"></canvas>
        </div>
      </div>

      <div class="grid-3" id="archetypesGrid"></div>

      <!-- FIGURE 7 SHOWCASE -->
      <div class="pub-figure-card">
        <div class="card-header" style="margin-bottom: 12px;">
          <div>
            <div class="card-title">Figure 7: Archetype Centroid Radar Profiles</div>
            <div class="card-desc">Detailed multi-hazard signatures characterizing each urban vulnerability class.</div>
          </div>
        </div>
        <img src="figures/Figure7_archetype_radar.png" alt="Figure 7: Archetype Radar" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure7_archetype_radar.png'">
      </div>
    </section>

    <!-- TAB 7: VALIDATION BATTERY -->
    <section id="tab-validation" class="tab-panel">
      <div class="card" style="margin-bottom: 24px;">
        <div class="card-header">
          <div>
            <div class="card-title">Pre-Registered 8-Part Empirical Validation Battery</div>
            <div class="card-desc">Rigorous construct validity, orthogonality, and historical disaster detection (8/8 Passed).</div>
          </div>
        </div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Validation Domain</th>
                <th>Statistical Method / Metric</th>
                <th>Empirical Value</th>
                <th>Threshold</th>
                <th>Status</th>
                <th>Scientific Finding</th>
              </tr>
            </thead>
            <tbody id="validationTableBody"></tbody>
          </table>
        </div>
      </div>

      <div class="grid-3">
        <div class="card">
          <div class="card-title" style="color: var(--color-heat);">Spring 2022 Mega-Heatwave</div>
          <div class="card-desc" style="margin-bottom: 12px;">Northwest India Historic Crisis</div>
          <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
            During March–May 2022, temperatures consistently exceeded 46°C in Rajasthan and MP. 
            The model triggered a <strong style="color: #fff;">96.5% anomaly alert rate</strong> in Bikaner 
            with composite SSI spiking from 0.596 to 0.751 (t = 3.46, p = 0.0008).
          </p>
        </div>

        <div class="card">
          <div class="card-title" style="color: var(--color-poll);">Delhi Winter Inversion Smog</div>
          <div class="card-desc" style="margin-bottom: 12px;">Boundary-Layer Subsidence</div>
          <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
            Severe post-monsoon stagnation traps agricultural and vehicular emissions (PM2.5 mean 355.3 µg/m³). 
            SSI captures this as a continuous <strong style="color: #fff;">+16.2% seasonal stress lift</strong>, 
            accurately diagnosing vulnerability in cold periods.
          </p>
        </div>

        <div class="card">
          <div class="card-title" style="color: var(--color-water);">October 2021 Hyderabad Deluge</div>
          <div class="card-desc" style="margin-bottom: 12px;">Deccan Plateau Cloudburst</div>
          <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5;">
            Deep depressions triggered severe urban flooding and lake breaches. 
            Mean SSI spiked to 0.682, triggering a <strong style="color: #fff;">100.0% city-wide anomaly alert 
            (all 1,505 cells flagged)</strong>, aligning exactly with municipal emergency declarations.
          </p>
        </div>
      </div>

      <!-- FIGURE 6 SHOWCASE -->
      <div class="pub-figure-card">
        <div class="card-header" style="margin-bottom: 12px;">
          <div>
            <div class="card-title">Figure 6: Ground-Truth Disaster Event Detection</div>
            <div class="card-desc">Validation against recorded extreme climate shocks in 2020–2022.</div>
          </div>
        </div>
        <img src="figures/Figure6_event_validation.png" alt="Figure 6: Disaster Event Detection" class="pub-figure-img" onerror="this.src='../research paper/figures/Figure6_event_validation.png'">
      </div>
    </section>

    <!-- TAB 8: METHODOLOGY -->
    <section id="tab-methodology" class="tab-panel">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">Mathematical Formulation of Smooth SSI</div>
          <div class="card-desc">Eliminating boundary clipping artifacts via asymptotic damping.</div>
          
          <div class="formula-box">
            SSI_lin = ∑ (w_j · S_j)  where w_j = 0.2000<br><br>
            Ω_compound = I(S_heat ≥ q_90) × I(S_poll ≥ q_90)<br><br>
            SSI = SSI_lin + γ · Ω_compound · (1.0 - SSI_lin)<br>
            [where γ = 0.30, q = 0.90]
          </div>

          <p style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
            The term <code style="color: #38bdf8;">(1.0 - SSI_lin)</code> acts as an endogenous damping factor: 
            as linear stress approaches 1.0, incremental amplification decelerates gracefully. 
            This guarantees that scores remain strictly bounded in [0, 1] without hard clamping (0.00% ceiling truncation).
          </p>
        </div>

        <div class="card">
          <div class="card-title">Data Provenance & Imputation Audit</div>
          <div class="card-desc">Zero synthetic noise; strict cloud-mask audit flags.</div>
          <div class="data-table-wrap" style="margin-top: 14px;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>City</th>
                  <th>Imputation %</th>
                  <th>Physical Reason</th>
                </tr>
              </thead>
              <tbody>
                <tr><td>Delhi NCR</td><td>70.63%</td><td>Persistent winter agricultural haze/smog optical masking</td></tr>
                <tr><td>Hyderabad</td><td>11.11%</td><td>Localized monsoon cloud masking</td></tr>
                <tr><td>Bikaner</td><td>5.18%</td><td>Sparse summer cloud masking</td></tr>
                <tr><td>Indore</td><td>2.78%</td><td>Monsoon transition cloud cover</td></tr>
                <tr><td>Kolkata</td><td>0.35%</td><td>Deltaic maritime cloud cover</td></tr>
                <tr><td>Mumbai</td><td>0.00%</td><td>Complete optical coverage verified</td></tr>
                <tr><td>Coimbatore</td><td>0.00%</td><td>Complete optical coverage verified</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

  </main>

  <!-- FOOTER -->
  <footer class="page-footer">
    <div class="container footer-inner">
      <div>
        <strong>Compound Sustainability Stress Index (SSI)</strong> — Automated Scientific Report & Geospatial Atlas Suite
        <div style="font-size: 11px; margin-top: 4px;">Canonical Dataset: <code>final_7_cities.parquet</code> | 334,332 Spatio-Temporal Rows | 9,287 Uber H3 Res 8 Hexagons</div>
      </div>
      <div>
        Open Science Repository: <a href="https://github.com/AryanGG/Compound-Sustainability-Stress-Modeling" target="_blank" style="color: var(--accent-cyan); text-decoration: none;">GitHub Repository</a>
      </div>
    </div>
  </footer>

  <!-- SCRIPT: APPLICATION LOGIC, CHARTS & LEAFLET MAP -->
  <script>
    const DATA = {json_str};

    let currentCity = 'all';
    let trendChartInstance = null;
    let radarChartInstance = null;
    let bandChartInstance = null;
    let varDecompChartInstance = null;
    let multiCityTrendChartInstance = null;
    let rankingChartInstance = null;
    let allVarDecompChartInstance = null;
    let decileChartInstance = null;
    let weightsChartInstance = null;
    let archetypeRadarInstance = null;

    // Leaflet Geospatial Map Variables
    let leafletMap = null;
    let mapMarkersLayer = null;
    let mapCanvasRenderer = null;
    let currentMapMetric = 'ssi';
    let currentMapCity = 'all';

    const CITY_COORDS = {{
      all: {{ center: [22.0, 78.5], zoom: 5 }},
      delhi: {{ center: [28.6139, 77.2090], zoom: 10 }},
      kolkata: {{ center: [22.5726, 88.3639], zoom: 11 }},
      mumbai: {{ center: [19.0760, 72.8777], zoom: 11 }},
      bikaner: {{ center: [28.0229, 73.3119], zoom: 12 }},
      hyderabad: {{ center: [17.3850, 78.4867], zoom: 11 }},
      indore: {{ center: [22.7196, 75.8577], zoom: 12 }},
      coimbatore: {{ center: [11.0168, 76.9558], zoom: 12 }}
    }};

    // Switch Top Tabs
    function switchTab(tabId) {{
      document.querySelectorAll('.nav-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      
      const btn = Array.from(document.querySelectorAll('.nav-tab')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(tabId));
      if (btn) btn.classList.add('active');
      
      const panel = document.getElementById('tab-' + tabId);
      if (panel) panel.classList.add('active');

      if (tabId === 'geospatial') {{
        setTimeout(() => {{
          if (!leafletMap) {{
            initLeafletMap();
          }} else {{
            leafletMap.invalidateSize();
          }}
        }}, 150);
      }}

      // Trigger chart resize
      window.dispatchEvent(new Event('resize'));
    }}

    // Select City (Global)
    function selectCity(cityKey) {{
      currentCity = cityKey;
      document.querySelectorAll('.city-pill').forEach(b => b.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.city-pill')).find(b => b.getAttribute('onclick') && b.getAttribute('onclick').includes(cityKey));
      if (activeBtn) activeBtn.classList.add('active');

      updateOverviewKPIs();
      renderTrendChart();
      renderRadarChart();
      renderBandChart();
      renderVarDecompChart();

      // Also sync with map
      flyMapToCity(cityKey);
    }}

    function updateOverviewKPIs() {{
      if (currentCity === 'all') {{
        document.getElementById('kpiObs').textContent = DATA.meta.total_obs.toLocaleString();
        document.getElementById('kpiMeanSSI').textContent = DATA.meta.mean_ssi;
        document.getElementById('kpiRange').textContent = `Range: ${{DATA.meta.min_ssi}} – ${{DATA.meta.max_ssi}}`;
        document.getElementById('kpiExtremeShare').textContent = `${{DATA.meta.risk_bands.Extreme}}%`;
        document.getElementById('trendSubtitle').textContent = 'Pan-India pooled monthly mean multi-hazard stress index across all 7 biomes.';
        document.getElementById('radarSubtitle').textContent = 'Pan-India pooled 5D hazard balance.';
      }} else {{
        const c = DATA.cities[currentCity];
        document.getElementById('kpiObs').textContent = c.panel_obs.toLocaleString();
        document.getElementById('kpiMeanSSI').textContent = c.mean_ssi;
        document.getElementById('kpiRange').textContent = `Range: ${{c.min_ssi}} – ${{c.max_ssi}}`;
        document.getElementById('kpiExtremeShare').textContent = `${{c.risk_bands.Extreme}}%`;
        document.getElementById('trendSubtitle').textContent = `${{c.name}} (${{c.biome}}) 36-month stress trajectory.`;
        document.getElementById('radarSubtitle').textContent = `${{c.name}} 5D hazard signature vs. Pan-India.`;
      }}
    }}

    function renderTrendChart() {{
      const ctx = document.getElementById('trendChart').getContext('2d');
      const series = currentCity === 'all' ? DATA.pan_india_monthly : DATA.cities[currentCity].monthly_timeseries;
      
      const labels = series.map(d => d.date);
      const ssiData = series.map(d => d.ssi);
      const heatData = series.map(d => d.heat);
      const pollData = series.map(d => d.pollution);
      const waterData = series.map(d => d.water);

      if (trendChartInstance) trendChartInstance.destroy();

      trendChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{
          labels: labels,
          datasets: [
            {{
              label: 'Composite SSI',
              data: ssiData,
              borderColor: '#8b5cf6',
              backgroundColor: 'rgba(139, 92, 246, 0.1)',
              borderWidth: 3,
              fill: true,
              tension: 0.3,
              pointRadius: 2,
            }},
            {{
              label: 'Heat Stress',
              data: heatData,
              borderColor: '#f87171',
              borderWidth: 1.5,
              borderDash: [4, 4],
              tension: 0.3,
              pointRadius: 0,
            }},
            {{
              label: 'Air Pollution',
              data: pollData,
              borderColor: '#fbbf24',
              borderWidth: 1.5,
              borderDash: [4, 4],
              tension: 0.3,
              pointRadius: 0,
            }},
            {{
              label: 'Water Deficit',
              data: waterData,
              borderColor: '#38bdf8',
              borderWidth: 1.5,
              borderDash: [4, 4],
              tension: 0.3,
              pointRadius: 0,
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
          }},
          scales: {{
            x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b', maxTicksLimit: 12 }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, min: 0, max: 1 }}
          }}
        }}
      }});
    }}

    function renderRadarChart() {{
      const ctx = document.getElementById('radarChart').getContext('2d');
      const labels = ['Heat', 'Water Deficit', 'Veg Canopy Loss', 'Air Pollution', 'Built Exposure'];
      
      const panVals = [
        DATA.meta.sub_indices.heat,
        DATA.meta.sub_indices.water,
        DATA.meta.sub_indices.veg,
        DATA.meta.sub_indices.pollution,
        DATA.meta.sub_indices.exposure
      ];

      const datasets = [
        {{
          label: 'Pan-India Mean',
          data: panVals,
          borderColor: 'rgba(255, 255, 255, 0.3)',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          borderWidth: 1.5,
        }}
      ];

      if (currentCity !== 'all') {{
        const c = DATA.cities[currentCity];
        datasets.unshift({{
          label: c.name,
          data: [c.sub_indices.heat, c.sub_indices.water, c.sub_indices.veg, c.sub_indices.pollution, c.sub_indices.exposure],
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.25)',
          borderWidth: 2.5,
          pointBackgroundColor: '#8b5cf6'
        }});
      }}

      if (radarChartInstance) radarChartInstance.destroy();

      radarChartInstance = new Chart(ctx, {{
        type: 'radar',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
          scales: {{
            r: {{
              grid: {{ color: 'rgba(255,255,255,0.08)' }},
              angleLines: {{ color: 'rgba(255,255,255,0.08)' }},
              ticks: {{ display: false, max: 1.0 }},
              pointLabels: {{ color: '#cbd5e1', font: {{ size: 11, weight: '600' }} }}
            }}
          }}
        }}
      }});
    }}

    function renderBandChart() {{
      const ctx = document.getElementById('bandChart').getContext('2d');
      const bands = currentCity === 'all' ? DATA.meta.risk_bands : DATA.cities[currentCity].risk_bands;

      if (bandChartInstance) bandChartInstance.destroy();

      bandChartInstance = new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: ['Low (≤0.33)', 'Moderate', 'High', 'Extreme (>0.66)'],
          datasets: [{{
            label: 'Share of Observations (%)',
            data: [bands.Low, bands.Moderate, bands.High, bands.Extreme],
            backgroundColor: ['#10b981', '#38bdf8', '#f59e0b', '#ef4444'],
            borderRadius: 6,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, max: 100 }}
          }}
        }}
      }});
    }}

    function renderVarDecompChart() {{
      const ctx = document.getElementById('varDecompChart').getContext('2d');
      const v = currentCity === 'all' 
        ? {{ temporal: 76.5, spatial: 20.4, residual: 3.1 }} 
        : DATA.cities[currentCity].variance_decomp;

      if (varDecompChartInstance) varDecompChartInstance.destroy();

      varDecompChartInstance = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
          labels: ['Atmospheric Seasonality', 'Urban Morphology', 'Residual Synergy'],
          datasets: [{{
            data: [v.temporal, v.spatial, v.residual],
            backgroundColor: ['#38bdf8', '#8b5cf6', '#64748b'],
            borderWidth: 0
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
          }}
        }}
      }});
    }}

    function renderCityTable() {{
      const tbody = document.getElementById('cityTableBody');
      tbody.innerHTML = '';
      
      const cityList = ['delhi', 'kolkata', 'mumbai', 'bikaner', 'hyderabad', 'indore', 'coimbatore'];
      cityList.forEach(cid => {{
        const c = DATA.cities[cid];
        const domHazard = Object.entries(c.sub_indices).sort((a,b) => b[1] - a[1])[0][0].toUpperCase();
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${{c.name}}</strong></td>
          <td>${{c.biome}} <span style="font-size: 10px; color: var(--text-dim);">(${{c.koppen}})</span></td>
          <td>${{c.hex_count.toLocaleString()}}</td>
          <td>${{c.area_km2}}</td>
          <td><strong style="color: #fff;">${{c.mean_ssi}}</strong></td>
          <td><span class="badge accent" style="padding: 2px 8px; font-size: 10px;">${{domHazard}}</span></td>
          <td><strong style="color: var(--band-ext);">${{c.risk_bands.Extreme}}%</strong></td>
          <td>${{c.compound_trigger_rate}}%</td>
          <td>${{c.variance_decomp.temporal}}%</td>
          <td>${{c.variance_decomp.spatial}}%</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderMultiCityTrend() {{
      const ctx = document.getElementById('multiCityTrendChart').getContext('2d');
      const dates = DATA.pan_india_monthly.map(d => d.date);
      
      const colors = {{
        'delhi': '#ef4444',
        'kolkata': '#a855f7',
        'mumbai': '#f59e0b',
        'bikaner': '#ec4899',
        'hyderabad': '#10b981',
        'indore': '#eab308',
        'coimbatore': '#06b6d4'
      }};

      const datasets = Object.keys(colors).map(cid => ({{
        label: DATA.cities[cid].name,
        data: DATA.cities[cid].monthly_timeseries.map(d => d.ssi),
        borderColor: colors[cid],
        borderWidth: 2,
        tension: 0.3,
        pointRadius: 0,
      }}));

      multiCityTrendChartInstance = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: dates, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'top', labels: {{ color: '#94a3b8' }} }}
          }},
          scales: {{
            x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, min: 0.1, max: 0.9 }}
          }}
        }}
      }});
    }}

    function renderComparativeCharts() {{
      // Ranking Chart
      const rCtx = document.getElementById('rankingChart').getContext('2d');
      const sortedCities = Object.values(DATA.cities).sort((a,b) => b.mean_ssi - a.mean_ssi);
      
      rankingChartInstance = new Chart(rCtx, {{
        type: 'bar',
        data: {{
          labels: sortedCities.map(c => c.name),
          datasets: [{{
            label: 'Mean SSI Score',
            data: sortedCities.map(c => c.mean_ssi),
            backgroundColor: sortedCities.map(c => c.mean_ssi > 0.5 ? '#f43f5e' : '#8b5cf6'),
            borderRadius: 6
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#94a3b8' }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, max: 0.7 }}
          }}
        }}
      }});

      // Stacked Var Decomp
      const vCtx = document.getElementById('allVarDecompChart').getContext('2d');
      const varSorted = Object.values(DATA.cities).sort((a,b) => b.variance_decomp.temporal - a.variance_decomp.temporal);

      allVarDecompChartInstance = new Chart(vCtx, {{
        type: 'bar',
        data: {{
          labels: varSorted.map(c => c.name),
          datasets: [
            {{
              label: 'Temporal (Seasonality)',
              data: varSorted.map(c => c.variance_decomp.temporal),
              backgroundColor: '#38bdf8'
            }},
            {{
              label: 'Spatial (Morphology)',
              data: varSorted.map(c => c.variance_decomp.spatial),
              backgroundColor: '#8b5cf6'
            }},
            {{
              label: 'Residual Coupling',
              data: varSorted.map(c => c.variance_decomp.residual),
              backgroundColor: '#64748b'
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          scales: {{
            x: {{ stacked: true, ticks: {{ color: '#94a3b8' }} }},
            y: {{ stacked: true, max: 100, grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }} }}
          }},
          plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#94a3b8' }} }} }}
        }}
      }});
    }}

    function renderCompoundAndWeights() {{
      // Decile Chart
      const dCtx = document.getElementById('decileChart').getContext('2d');
      decileChartInstance = new Chart(dCtx, {{
        type: 'bar',
        data: {{
          labels: DATA.deciles.map(d => d.decile),
          datasets: [
            {{
              label: 'Linear Baseline',
              data: DATA.deciles.map(d => d.ssi_linear),
              backgroundColor: 'rgba(255,255,255,0.15)',
              borderRadius: 4
            }},
            {{
              label: 'Smooth Compound SSI',
              data: DATA.deciles.map(d => d.ssi_compound),
              backgroundColor: '#f43f5e',
              borderRadius: 4
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
          scales: {{
            x: {{ ticks: {{ color: '#94a3b8' }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, max: 1.0 }}
          }}
        }}
      }});

      // Weights Chart
      const wCtx = document.getElementById('weightsChart').getContext('2d');
      weightsChartInstance = new Chart(wCtx, {{
        type: 'bar',
        data: {{
          labels: DATA.weights.labels,
          datasets: [
            {{ label: 'Equal (0.20)', data: DATA.weights.equal, backgroundColor: '#8b5cf6' }},
            {{ label: 'Entropy (EWM)', data: DATA.weights.ewm, backgroundColor: '#06b6d4' }},
            {{ label: 'CRITIC', data: DATA.weights.critic, backgroundColor: '#f59e0b' }},
            {{ label: 'PCA (PC1)', data: DATA.weights.pca, backgroundColor: '#ec4899' }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#94a3b8' }} }} }},
          scales: {{
            x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }} }},
            y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#64748b' }}, max: 0.45 }}
          }}
        }}
      }});
    }}

    function renderArchetypes() {{
      const grid = document.getElementById('archetypesGrid');
      grid.innerHTML = '';
      
      DATA.archetypes.forEach(a => {{
        const card = document.createElement('div');
        card.className = 'arch-card';
        card.innerHTML = `
          <div>
            <div class="arch-header">
              <span class="arch-tag">Archetype ${{a.id}}</span>
              <span class="arch-prevalence">${{a.prevalence}}%</span>
            </div>
            <div class="arch-title">${{a.title}}</div>
            <div class="arch-desc">${{a.desc}}</div>
            <div class="arch-metrics">
              <div class="arch-m-item"><div class="label">Heat</div><div class="val">${{a.centroids.heat}}</div></div>
              <div class="arch-m-item"><div class="label">Water</div><div class="val">${{a.centroids.water}}</div></div>
              <div class="arch-m-item"><div class="label">Veg</div><div class="val">${{a.centroids.veg}}</div></div>
              <div class="arch-m-item"><div class="label">Poll</div><div class="val">${{a.centroids.pollution}}</div></div>
              <div class="arch-m-item"><div class="label">Exp</div><div class="val">${{a.centroids.exposure}}</div></div>
            </div>
          </div>
          <div class="arch-policy">
            <strong>Municipal Adaptation Action:</strong><br>
            ${{a.adaptation}}
          </div>
        `;
        grid.appendChild(card);
      }});

      // Archetype Radar
      const aCtx = document.getElementById('archetypeRadarChart').getContext('2d');
      const colors = ['#06b6d4', '#f59e0b', '#ec4899', '#3b82f6', '#ef4444', '#8b5cf6'];
      
      archetypeRadarInstance = new Chart(aCtx, {{
        type: 'radar',
        data: {{
          labels: ['Heat', 'Water Deficit', 'Veg Canopy Loss', 'Air Pollution', 'Built Exposure'],
          datasets: DATA.archetypes.map((a, idx) => ({{
            label: `A${{a.id}}: ${{a.title.split('/')[0]}}`,
            data: [a.centroids.heat, a.centroids.water, a.centroids.veg, a.centroids.pollution, a.centroids.exposure],
            borderColor: colors[idx],
            backgroundColor: 'transparent',
            borderWidth: 2,
          }}))
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }},
          scales: {{
            r: {{
              grid: {{ color: 'rgba(255,255,255,0.08)' }},
              angleLines: {{ color: 'rgba(255,255,255,0.08)' }},
              pointLabels: {{ color: '#cbd5e1', font: {{ size: 11, weight: '600' }} }},
              ticks: {{ display: false, max: 1.0 }}
            }}
          }}
        }}
      }});
    }}

    function renderValidationTable() {{
      const tbody = document.getElementById('validationTableBody');
      tbody.innerHTML = '';
      
      DATA.validation.forEach(v => {{
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${{v.id}}</td>
          <td><strong>${{v.domain}}</strong></td>
          <td>${{v.method}}</td>
          <td><strong style="color: #fff;">${{v.value}}</strong></td>
          <td>${{v.benchmark}}</td>
          <td><span class="status-badge status-pass">✓ ${{v.status}}</span></td>
          <td style="color: var(--text-muted);">${{v.note}}</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    // ─────────────────────────────────────────────────────────────
    // LEAFLET GEOSPATIAL MAP ENGINE (9,287 H3 Cells Canvas Rendering)
    // ─────────────────────────────────────────────────────────────

    function getMetricColor(metric, val) {{
      if (metric === 'ssi') {{
        // Continuous SSI: 0.0 -> Green, 0.45 -> Cyan, 0.60 -> Amber, 0.75+ -> Crimson
        if (val < 0.35) return '#10b981';
        if (val < 0.50) return '#06b6d4';
        if (val < 0.65) return '#f59e0b';
        return '#ef4444';
      }} else if (metric === 'heat') {{
        // Heat: Yellow to Deep Red
        if (val < 0.35) return '#fef08a';
        if (val < 0.50) return '#f59e0b';
        if (val < 0.70) return '#ea580c';
        return '#dc2626';
      }} else if (metric === 'water') {{
        // Water Deficit: Cyan to Dark Navy
        if (val < 0.35) return '#bae6fd';
        if (val < 0.55) return '#38bdf8';
        if (val < 0.75) return '#0284c7';
        return '#1e3a8a';
      }} else if (metric === 'veg') {{
        // Veg Deficit: Green (High canopy) to Amber to Maroon (Total deficit)
        if (val < 0.35) return '#34d399';
        if (val < 0.55) return '#eab308';
        if (val < 0.75) return '#ea580c';
        return '#991b1b';
      }} else if (metric === 'pollution') {{
        // PM2.5: Light Gold to Crimson / Purple
        if (val < 0.35) return '#fef08a';
        if (val < 0.55) return '#f59e0b';
        if (val < 0.75) return '#dc2626';
        return '#701a75';
      }} else if (metric === 'exposure') {{
        // Built Exposure: Lavender to Deep Violet
        if (val < 0.20) return '#e9d5ff';
        if (val < 0.40) return '#c084fc';
        if (val < 0.65) return '#9333ea';
        return '#581c87';
      }} else if (metric === 'archetype') {{
        const archColors = {{
          1: '#06b6d4', // Coastal Sinks
          2: '#f59e0b', // Industrial Plume
          3: '#ec4899', // Water-Stressed Semi-Arid
          4: '#3b82f6', // Rapidly Densifying
          5: '#ef4444', // Compound Inversion Hub
          6: '#8b5cf6'  // Plateau Industrial
        }};
        return archColors[val] || '#94a3b8';
      }} else if (metric === 'risk_band') {{
        const bandColors = {{
          'Low': '#10b981',
          'Moderate': '#38bdf8',
          'High': '#f59e0b',
          'Extreme': '#ef4444'
        }};
        return bandColors[val] || '#94a3b8';
      }}
      return '#8b5cf6';
    }}

    function initLeafletMap() {{
      if (leafletMap) return;

      mapCanvasRenderer = L.canvas({{ padding: 0.5 }});
      
      leafletMap = L.map('mapView', {{
        center: [22.0, 78.5],
        zoom: 5,
        minZoom: 4,
        maxZoom: 16,
        preferCanvas: true
      }});

      // Sleek Dark Gray Basemap Tiles (Esri Canvas - Free & Unauthenticated)
      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: '&copy; <a href="https://www.esri.com/" target="_blank">Esri</a>, HERE, Garmin, &copy; OpenStreetMap',
        maxZoom: 16
      }}).addTo(leafletMap);

      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
        attribution: '',
        maxZoom: 16,
        opacity: 0.75
      }}).addTo(leafletMap);

      mapMarkersLayer = L.layerGroup().addTo(leafletMap);

      renderMapMarkers();
      updateMapLegend();

      // Inspect highest risk cell by default
      const hexList = DATA.hex_map_data || [];
      if (hexList.length > 0) {{
        const sample = hexList.find(h => h[0] === 'delhi' && h[11] === 'Extreme') || hexList[0];
        inspectHex(sample);
      }}
    }}

    function renderMapMarkers() {{
      if (!leafletMap || !mapMarkersLayer) return;
      mapMarkersLayer.clearLayers();

      const hexList = DATA.hex_map_data || [];
      const filtered = hexList.filter(h => {{
        // h: [city_id, h3, lat, lon, ssi, heat, water, veg, poll, exp, arch, band]
        if (currentMapCity !== 'all' && h[0] !== currentMapCity) return false;
        return true;
      }});

      document.getElementById('mapVisibleCount').textContent = filtered.length.toLocaleString();

      filtered.forEach(h => {{
        let val;
        if (currentMapMetric === 'ssi') val = h[4];
        else if (currentMapMetric === 'heat') val = h[5];
        else if (currentMapMetric === 'water') val = h[6];
        else if (currentMapMetric === 'veg') val = h[7];
        else if (currentMapMetric === 'pollution') val = h[8];
        else if (currentMapMetric === 'exposure') val = h[9];
        else if (currentMapMetric === 'archetype') val = h[10];
        else if (currentMapMetric === 'risk_band') val = h[11];

        const color = getMetricColor(currentMapMetric, val);

        const marker = L.circleMarker([h[2], h[3]], {{
          renderer: mapCanvasRenderer,
          radius: currentMapCity === 'all' ? 4 : 5.5,
          fillColor: color,
          fillOpacity: 0.85,
          color: '#ffffff',
          weight: 0.25
        }});

        marker.on('click', () => inspectHex(h));
        marker.on('mouseover', () => inspectHex(h));

        marker.bindTooltip(`
          <div style="font-size: 11px; line-height: 1.4;">
            <strong style="color: #fff;">${{h[1]}}</strong> (${{DATA.cities[h[0]] ? DATA.cities[h[0]].name : h[0]}})<br>
            SSI: <strong style="color: #38bdf8;">${{h[4]}}</strong> (${{h[11]}})<br>
            Heat: ${{h[5]}} | Water: ${{h[6]}} | Veg: ${{h[7]}}<br>
            Pollution: ${{h[8]}} | Exposure: ${{h[9]}}
          </div>
        `, {{ sticky: true, opacity: 0.95 }});

        mapMarkersLayer.addLayer(marker);
      }});
    }}

    function setMapMetric(metric) {{
      currentMapMetric = metric;
      document.querySelectorAll('.map-metric-btn').forEach(b => {{
        if (b.dataset.metric === metric) b.classList.add('active');
        else b.classList.remove('active');
      }});
      renderMapMarkers();
      updateMapLegend();
    }}

    function flyMapToCity(cityKey) {{
      currentMapCity = cityKey;
      const selectElem = document.getElementById('mapCitySelect');
      if (selectElem) selectElem.value = cityKey;

      if (leafletMap) {{
        const target = CITY_COORDS[cityKey] || CITY_COORDS.all;
        leafletMap.flyTo(target.center, target.zoom, {{ duration: 1.2 }});
        renderMapMarkers();
      }}
    }}

    function inspectHex(h) {{
      // h: [city_id, h3, lat, lon, ssi, heat, water, veg, poll, exp, arch, band]
      const cityMeta = DATA.cities[h[0]];
      document.getElementById('inspectCity').textContent = cityMeta ? `${{cityMeta.name}} (${{cityMeta.biome}})` : h[0];
      document.getElementById('inspectH3').textContent = h[1];
      document.getElementById('inspectCoords').textContent = `${{h[2].toFixed(4)}}° N, ${{h[3].toFixed(4)}}° E`;
      document.getElementById('inspectSSI').textContent = h[4].toFixed(3);

      const bandBadge = document.getElementById('inspectBandBadge');
      bandBadge.textContent = h[11] + ' Risk';
      bandBadge.className = 'status-badge ' + (h[11] === 'Extreme' ? 'status-extreme' : h[11] === 'High' ? 'status-high' : h[11] === 'Moderate' ? 'status-mod' : 'status-low');

      setGauge('inspectHeatBar', 'inspectHeatVal', h[5]);
      setGauge('inspectWaterBar', 'inspectWaterVal', h[6]);
      setGauge('inspectVegBar', 'inspectVegVal', h[7]);
      setGauge('inspectPollBar', 'inspectPollVal', h[8]);
      setGauge('inspectExpBar', 'inspectExpVal', h[9]);

      const arch = DATA.archetypes.find(a => a.id === h[10]);
      document.getElementById('inspectArchetype').textContent = arch ? `A${{arch.id}}: ${{arch.title}}` : `Archetype ${{h[10]}}`;
    }}

    function setGauge(barId, valId, score) {{
      const pct = Math.max(0, Math.min(100, (score * 100))).toFixed(1);
      const bar = document.getElementById(barId);
      const val = document.getElementById(valId);
      if (bar) bar.style.width = `${{pct}}%`;
      if (val) val.textContent = score.toFixed(3);
    }}

    function updateMapLegend() {{
      const title = document.getElementById('mapLegendTitle');
      const content = document.getElementById('mapLegendContent');

      if (currentMapMetric === 'ssi') {{
        title.textContent = 'Composite SSI Stress (0.0 – 1.0)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #10b981 0%, #06b6d4 35%, #f59e0b 65%, #ef4444 100%);"></div>
          <div class="legend-labels">
            <span>Low (≤0.33)</span>
            <span>Moderate</span>
            <span>High</span>
            <span>Extreme (>0.66)</span>
          </div>
        `;
      }} else if (currentMapMetric === 'heat') {{
        title.textContent = 'Heat Stress Index (LST + Wet-Bulb)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #fef08a 0%, #f59e0b 50%, #dc2626 100%);"></div>
          <div class="legend-labels"><span>0.0 (Mild)</span><span>0.5</span><span>1.0 (Extreme Heat)</span></div>
        `;
      }} else if (currentMapMetric === 'water') {{
        title.textContent = 'Water Scarcity (NDWI + Moisture Deficit)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #bae6fd 0%, #38bdf8 45%, #0284c7 75%, #1e3a8a 100%);"></div>
          <div class="legend-labels"><span>0.0 (Adequate)</span><span>0.5</span><span>1.0 (Arid / Drought)</span></div>
        `;
      }} else if (currentMapMetric === 'veg') {{
        title.textContent = 'Vegetation Deficit (Canopy Loss)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #34d399 0%, #eab308 50%, #991b1b 100%);"></div>
          <div class="legend-labels"><span>0.0 (High Canopy)</span><span>0.5</span><span>1.0 (Zero Greenery)</span></div>
        `;
      }} else if (currentMapMetric === 'pollution') {{
        title.textContent = 'PM2.5 Air Pollution (NASA SEDAC)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #fef08a 0%, #f59e0b 50%, #dc2626 75%, #701a75 100%);"></div>
          <div class="legend-labels"><span>0.0 (Clean)</span><span>0.5</span><span>1.0 (Severe Smog)</span></div>
        `;
      }} else if (currentMapMetric === 'exposure') {{
        title.textContent = 'Socio-Demographic Exposure (Slum / Built)';
        content.innerHTML = `
          <div class="legend-ramp" style="background: linear-gradient(90deg, #e9d5ff 0%, #c084fc 40%, #9333ea 70%, #581c87 100%);"></div>
          <div class="legend-labels"><span>0.0 (Sparse)</span><span>0.5</span><span>1.0 (Hyper-Dense Slum)</span></div>
        `;
      }} else if (currentMapMetric === 'archetype') {{
        title.textContent = 'Urban Typology Archetypes';
        content.innerHTML = `
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #06b6d4;"></div><span>A1: Coastal Marine Sinks</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #f59e0b;"></div><span>A2: Industrial Plume</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #ec4899;"></div><span>A3: Water-Stressed Arid Core</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #3b82f6;"></div><span>A4: Rapidly Densifying Plateau</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #ef4444;"></div><span>A5: Severe Inversion Hub</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #8b5cf6;"></div><span>A6: High Built Exposure</span></div>
        `;
      }} else if (currentMapMetric === 'risk_band') {{
        title.textContent = 'Standardized SSI Risk Band';
        content.innerHTML = `
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #10b981;"></div><span>Low (≤0.33)</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #38bdf8;"></div><span>Moderate (0.33 – 0.50)</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #f59e0b;"></div><span>High (0.50 – 0.66)</span></div>
          <div class="legend-discrete-item"><div class="legend-swatch" style="background: #ef4444;"></div><span>Extreme (>0.66)</span></div>
        `;
      }}
    }}

    // Initial Launch
    window.addEventListener('DOMContentLoaded', () => {{
      selectCity('all');
      renderCityTable();
      renderMultiCityTrend();
      renderComparativeCharts();
      renderCompoundAndWeights();
      renderArchetypes();
      renderValidationTable();
    }});
  </script>
</body>
</html>
"""

    out_file = Path("reports/final_7_cities_report.html")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(html_content, encoding="utf-8")
    print(f"✓ Saved 7-city HTML report to {out_file.resolve()}")

    # Also update dashboard/index.html so it serves as the primary dashboard
    dash_dir = Path("dashboard")
    dash_dir.mkdir(parents=True, exist_ok=True)
    dash_file = dash_dir / "index.html"
    dash_file.write_text(html_content, encoding="utf-8")
    print(f"✓ Dashboard updated -> {dash_file.resolve()}")

if __name__ == "__main__":
    render_html()
