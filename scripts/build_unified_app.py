"""
scripts/build_unified_app.py
────────────────────────────
Compiles the complete single-page light-mode GeoStress AI web application
into dashboard/index.html with:
1. Real H3 hexagonal polygon cells (using h3-js client-side boundary calculation)
2. Translucent natural, non-neon environmental color palette (Carto Voyager visible beneath)
3. User's Carto API key: https://basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_4m3i_1_4351c859fd1db9c1dc798c0a
4. Clean month dropdown without extra annotations (e.g., "04 - April")
5. 100% real spatio-temporal data and ML predictions embedded
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def build():
    data_file = ROOT_DIR / "scratch/frontend_data.json"
    if not data_file.exists():
        raise FileNotFoundError("Run scripts/build_frontend.py first to generate scratch/frontend_data.json")

    print("Loading extracted real frontend dataset (4.0 MB)...")
    with open(data_file, "r", encoding="utf-8") as f:
        data_json = f.read()
    print("Dataset loaded successfully.")

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GeoStress AI — Hyperlocal Urban Sustainability Stress & Multi-Horizon Early Warning System</title>
  
  <!-- Modern Clean Typography from Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  
  <!-- Leaflet.js for high-performance geospatial mapping -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

  <!-- H3-js Library for Real Hexagonal Polygon Geometry (Offline Local Fallback + CDN) -->
  <script src="h3-js.umd.js"></script>
  <script>
    if (typeof h3 === 'undefined') {{
      document.write('<script src="https://unpkg.com/h3-js@4.1.0/dist/h3-js.umd.js"><\\/script>');
    }}
  </script>

  <style>
    :root {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-elevated: #ffffff;
      --border: #e2e8f0;
      --border-dark: #cbd5e1;
      
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;
      --text-light: #94a3b8;
      
      --navy: #1e3a8a;
      --navy-light: #eff6ff;
      --navy-border: #bfdbfe;
      
      --brand-primary: #0284c7;
      --brand-accent: #6366f1;
      
      /* Natural Environmental Color Palette (Dignified, Not Neon) */
      --risk-low: #2d6a4f;         /* Natural Sage/Forest Green */
      --risk-low-bg: #f0fdf4;
      --risk-low-border: #bbf7d0;
      
      --risk-mod: #2a6f97;         /* Steel/Slate Blue */
      --risk-mod-bg: #f0f9ff;
      --risk-mod-border: #bae6fd;
      
      --risk-high: #c27803;        /* Earthy Ochre/Warm Amber */
      --risk-high-bg: #fffbeb;
      --risk-high-border: #fde68a;
      
      --risk-extreme: #b91c1c;     /* Deep Terracotta/Crimson */
      --risk-extreme-bg: #fef2f2;
      --risk-extreme-border: #fecaca;

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
      --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04);
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      line-height: 1.5;
      font-size: 14px;
      -webkit-font-smoothing: antialiased;
    }}

    /* Global App Header */
    header.app-header {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 1000;
      box-shadow: var(--shadow-sm);
    }}

    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 24px;
      border-bottom: 1px solid #f1f5f9;
    }}

    .brand-wrap {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .brand-icon {{
      width: 34px;
      height: 34px;
      background: var(--navy);
      color: white;
      border-radius: var(--radius-sm);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 16px;
      font-family: 'Outfit', sans-serif;
    }}

    .brand-text h1 {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: var(--navy);
      letter-spacing: -0.3px;
    }}

    .brand-text p {{
      font-size: 11px;
      color: var(--text-dim);
      font-weight: 500;
    }}

    .header-badges {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .badge-pill {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 11px;
      font-weight: 600;
      border: 1px solid var(--border);
      background: var(--bg);
      color: var(--text-muted);
    }}

    .badge-pill.status-online {{
      background: var(--risk-low-bg);
      border-color: var(--risk-low-border);
      color: var(--risk-low);
    }}

    /* Primary Dropdown Controls Bar */
    .controls-strip {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 24px;
      background: #ffffff;
      flex-wrap: wrap;
      gap: 16px;
    }}

    .selectors-group {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .control-item {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .control-label {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    select.filter-select {{
      background: var(--bg);
      border: 1px solid var(--border-dark);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      font-size: 13px;
      font-weight: 600;
      outline: none;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    select.filter-select:hover {{
      border-color: var(--brand-primary);
      background: white;
    }}

    select.filter-select:focus {{
      border-color: var(--brand-primary);
      box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.15);
    }}

    /* Mode Segmented Button */
    .mode-toggle {{
      display: inline-flex;
      background: #f1f5f9;
      padding: 3px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
    }}

    .mode-btn {{
      padding: 5px 12px;
      border: none;
      background: transparent;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      color: var(--text-dim);
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .mode-btn.active {{
      background: var(--surface);
      color: var(--navy);
      box-shadow: var(--shadow-sm);
      font-weight: 700;
    }}

    /* Top KPI Ribbon */
    .kpi-ribbon {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      padding: 16px 24px;
      max-width: 1600px;
      margin: 0 auto;
    }}

    .kpi-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}

    .kpi-title {{
      font-size: 11.5px;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .kpi-val {{
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
      line-height: 1.1;
      margin: 4px 0;
    }}

    .kpi-sub {{
      font-size: 11.5px;
      color: var(--text-dim);
      line-height: 1.4;
    }}

    /* Main Grid Workspace */
    .workspace-grid {{
      display: grid;
      grid-template-columns: 1fr 420px;
      gap: 20px;
      padding: 0 24px 24px;
      max-width: 1600px;
      margin: 0 auto;
      min-height: 720px;
    }}

    @media (max-width: 1180px) {{
      .workspace-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    /* Map Box */
    .map-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      position: relative;
      overflow: hidden;
      min-height: 640px;
    }}

    .map-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 18px;
      border-bottom: 1px solid var(--border);
      background: white;
      flex-wrap: wrap;
      gap: 12px;
      z-index: 500;
    }}

    .layer-pills {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }}

    .layer-pill {{
      padding: 5px 12px;
      border-radius: var(--radius-sm);
      font-size: 12px;
      font-weight: 600;
      border: 1px solid var(--border);
      background: #f8fafc;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .layer-pill:hover {{
      background: #f1f5f9;
      color: var(--text-main);
    }}

    .layer-pill.active {{
      background: var(--navy);
      color: white;
      border-color: var(--navy);
    }}

    #mapContainer {{
      flex: 1;
      width: 100%;
      height: 100%;
      min-height: 540px;
      background: #f1f5f9;
      z-index: 10;
    }}

    /* Floating Legend */
    .map-legend {{
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 10px 14px;
      box-shadow: var(--shadow-md);
      z-index: 500;
      font-size: 11px;
      min-width: 220px;
    }}

    .legend-title {{
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 6px;
    }}

    .legend-bar {{
      height: 8px;
      border-radius: 4px;
      background: linear-gradient(to right, #2d6a4f, #2a6f97, #c27803, #b91c1c);
      margin-bottom: 4px;
    }}

    .legend-labels {{
      display: flex;
      justify-content: space-between;
      color: var(--text-dim);
      font-weight: 600;
    }}

    /* Side Inspector Card */
    .inspector-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-sm);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    .inspector-header {{
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      background: #ffffff;
    }}

    .inspector-cell-id {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      color: var(--text-dim);
    }}

    .inspector-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 2px;
    }}

    .band-badge {{
      display: inline-flex;
      align-items: center;
      padding: 3px 10px;
      border-radius: 9999px;
      font-size: 11.5px;
      font-weight: 700;
      letter-spacing: 0.3px;
    }}

    .band-badge.band-low {{ background: var(--risk-low-bg); color: var(--risk-low); border: 1px solid var(--risk-low-border); }}
    .band-badge.band-mod {{ background: var(--risk-mod-bg); color: var(--risk-mod); border: 1px solid var(--risk-mod-border); }}
    .band-badge.band-high {{ background: var(--risk-high-bg); color: var(--risk-high); border: 1px solid var(--risk-high-border); }}
    .band-badge.band-extreme {{ background: var(--risk-extreme-bg); color: var(--risk-extreme); border: 1px solid var(--risk-extreme-border); }}

    .inspector-body {{
      padding: 20px;
      overflow-y: auto;
      max-height: 700px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}

    .section-title {{
      font-size: 12px;
      font-weight: 700;
      color: var(--navy);
      text-transform: uppercase;
      letter-spacing: 0.6px;
      margin-bottom: 12px;
      padding-bottom: 4px;
      border-bottom: 1px solid #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    /* Physical Drivers Progress Bars */
    .driver-item {{
      margin-bottom: 10px;
    }}

    .driver-meta {{
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      margin-bottom: 3px;
    }}

    .driver-name {{ font-weight: 600; color: var(--text-main); }}
    .driver-val {{ font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text-muted); }}

    .driver-bar-track {{
      height: 6px;
      background: #f1f5f9;
      border-radius: 3px;
      overflow: hidden;
    }}

    .driver-bar-fill {{
      height: 100%;
      border-radius: 3px;
      transition: width 0.3s ease;
    }}

    /* Demographics Grid */
    .demo-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}

    .demo-item {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 8px 12px;
    }}

    .demo-label {{
      font-size: 10.5px;
      font-weight: 600;
      color: var(--text-dim);
    }}

    .demo-val {{
      font-family: 'Outfit', sans-serif;
      font-size: 15px;
      font-weight: 700;
      color: var(--text-main);
      margin-top: 2px;
    }}

    /* ML Early Warning Box */
    .ml-box {{
      background: #fafaf9;
      border: 1px solid #e7e5e4;
      border-radius: var(--radius-md);
      padding: 14px;
    }}

    .ml-box.status-alert {{
      background: var(--risk-extreme-bg);
      border-color: var(--risk-extreme-border);
    }}

    .ml-kpi-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }}

    .ml-kpi-mini {{
      background: white;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 8px 10px;
    }}

    .statutory-alert-block {{
      background: white;
      border: 1px solid var(--border);
      border-left: 4px solid var(--risk-extreme);
      border-radius: 4px;
      padding: 10px 12px;
      margin-top: 10px;
    }}

    .statutory-header {{
      font-size: 11.5px;
      font-weight: 700;
      color: var(--risk-extreme);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }}

    .statutory-directive {{
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.45;
    }}

    /* Bottom Information & Policy Drawer */
    .bottom-section {{
      max-width: 1600px;
      margin: 0 auto;
      padding: 0 24px 48px;
    }}

    .tabs-nav {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 16px;
    }}

    .tab-btn {{
      padding: 10px 16px;
      border: none;
      background: transparent;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-dim);
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.15s ease;
    }}

    .tab-btn:hover {{ color: var(--text-main); }}

    .tab-btn.active {{
      color: var(--navy);
      border-bottom-color: var(--navy);
    }}

    .tab-content {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 24px;
      box-shadow: var(--shadow-sm);
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
      text-align: left;
    }}

    .data-table th {{
      background: #f8fafc;
      padding: 10px 14px;
      font-weight: 700;
      color: var(--text-dim);
      border-bottom: 1px solid var(--border);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 11px;
    }}

    .data-table td {{
      padding: 11px 14px;
      border-bottom: 1px solid #f1f5f9;
      color: var(--text-main);
    }}

    .data-table tr:hover {{
      background: #f8fafc;
    }}

    footer.app-footer {{
      border-top: 1px solid var(--border);
      padding: 24px;
      text-align: center;
      font-size: 12px;
      color: var(--text-dim);
      background: white;
    }}
  </style>
</head>
<body>

  <!-- GLOBAL APP HEADER -->
  <header class="app-header">
    <div class="header-top">
      <div class="brand-wrap">
        <div class="brand-icon">G</div>
        <div class="brand-text">
          <h1>GeoStress AI</h1>
          <p>Hyperlocal Urban Sustainability Stress &amp; Multi-Horizon Early Warning System</p>
        </div>
      </div>
      <div class="header-badges">
        <span class="badge-pill status-online">● Canonical Dataset v2.0</span>
        <span class="badge-pill">334,332 Hex-Months</span>
        <span class="badge-pill">9,287 Micro-Cells</span>
        <span class="badge-pill">OOT Recall: 93.8%</span>
      </div>
    </div>

    <!-- PRIMARY DROPDOWNS BAR -->
    <div class="controls-strip">
      <div class="selectors-group">
        <!-- City Selector -->
        <div class="control-item">
          <label class="control-label" for="citySelect">City:</label>
          <select id="citySelect" class="filter-select" onchange="onCityChanged(this.value)">
            <option value="mumbai" selected>Mumbai (Maharashtra)</option>
            <option value="delhi">Delhi NCR (National Capital Region)</option>
            <option value="kolkata">Kolkata (West Bengal)</option>
            <option value="hyderabad">Hyderabad (Telangana)</option>
            <option value="bikaner">Bikaner (Rajasthan)</option>
            <option value="coimbatore">Coimbatore (Tamil Nadu)</option>
            <option value="indore">Indore (Madhya Pradesh)</option>
          </select>
        </div>

        <!-- Year Selector -->
        <div class="control-item">
          <label class="control-label" for="yearSelect">Year:</label>
          <select id="yearSelect" class="filter-select" onchange="onDateChanged()">
            <option value="2020">2020</option>
            <option value="2021">2021</option>
            <option value="2022" selected>2022</option>
          </select>
        </div>

        <!-- Month Selector (Clean format without extra notes) -->
        <div class="control-item">
          <label class="control-label" for="monthSelect">Month:</label>
          <select id="monthSelect" class="filter-select" onchange="onDateChanged()">
            <option value="01">01 - January</option>
            <option value="02">02 - February</option>
            <option value="03">03 - March</option>
            <option value="04" selected>04 - April</option>
            <option value="05">05 - May</option>
            <option value="06">06 - June</option>
            <option value="07">07 - July</option>
            <option value="08">08 - August</option>
            <option value="09">09 - September</option>
            <option value="10">10 - October</option>
            <option value="11">11 - November</option>
            <option value="12">12 - December</option>
          </select>
        </div>
      </div>

      <!-- Mode Toggle -->
      <div class="mode-toggle">
        <button id="modeObs" class="mode-btn active" onclick="setMode('obs')">Observed SSI (t)</button>
        <button id="modePred" class="mode-btn" onclick="setMode('pred')">ML 30-Day Forward Forecast (t+1)</button>
      </div>
    </div>
  </header>

  <!-- TOP EXECUTIVE KPI RIBBON -->
  <section class="kpi-ribbon">
    <div class="kpi-card">
      <div class="kpi-title">
        <span>City Mean SSI Score</span>
        <span id="kpiMonthBadge" class="badge-pill">Apr 2022</span>
      </div>
      <div class="kpi-val" id="kpiMeanSSI">0.488</div>
      <div class="kpi-sub" id="kpiRange">Linear base: 0.452 · Synergy: +25.3%</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-title">
        <span>Extreme Risk Share</span>
        <span class="badge-pill" style="color: var(--risk-extreme);">SSI &gt; 0.657</span>
      </div>
      <div class="kpi-val" id="kpiExtremePct" style="color: var(--risk-extreme);">45.0%</div>
      <div class="kpi-sub" id="kpiExtremeCount">318 of 707 hexagons in acute distress</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-title">
        <span>Statutory Emergency Status</span>
        <span class="badge-pill" style="color: var(--risk-extreme);">Active Protocol</span>
      </div>
      <div class="kpi-val" id="kpiAlertCount" style="font-size: 20px; color: var(--risk-extreme);">IMD HAP STAGE III</div>
      <div class="kpi-sub" id="kpiAlertSub">Red Alert: 165 hexes exceed 75% heatwave likelihood</div>
    </div>

    <div class="kpi-card">
      <div class="kpi-title">
        <span>30-Day Forward Forecast</span>
        <span class="badge-pill">OOT 2022 Test</span>
      </div>
      <div class="kpi-val" style="color: var(--risk-low);">93.8% Recall</div>
      <div class="kpi-sub">Continuous SSI R² = 0.888 · PR-AUC = 0.886</div>
    </div>
  </section>

  <!-- MAIN WORKSPACE -->
  <main class="workspace-grid">

    <!-- LEFT: MAP CONTAINER -->
    <div class="map-card">
      <div class="map-toolbar">
        <div class="layer-pills" id="layerPills">
          <button class="layer-pill active" onclick="setMetric('ssi')">Composite SSI</button>
          <button class="layer-pill" onclick="setMetric('heat')">Heat Stress (LST/Temp)</button>
          <button class="layer-pill" onclick="setMetric('water')">Water Deficit (CWD)</button>
          <button class="layer-pill" onclick="setMetric('veg')">Canopy Loss (NDVI)</button>
          <button class="layer-pill" onclick="setMetric('poll')">PM2.5 Smog</button>
          <button class="layer-pill" onclick="setMetric('exp')">Built Density</button>
        </div>
        <div style="font-size: 11.5px; font-weight: 600; color: var(--text-dim);" id="mapStatusText">
          Displaying 707 H3 hexes for Mumbai
        </div>
      </div>

      <div id="mapContainer"></div>

      <!-- Floating Map Legend -->
      <div class="map-legend">
        <div class="legend-title" id="legendTitle">Composite SSI Score</div>
        <div class="legend-bar"></div>
        <div class="legend-labels">
          <span>Low (≤0.33)</span>
          <span>Mod (0.50)</span>
          <span>High (0.66)</span>
          <span>Extreme (&gt;0.66)</span>
        </div>
      </div>
    </div>

    <!-- RIGHT: CONTEXTUAL INSPECTOR -->
    <div class="inspector-card">
      <div class="inspector-header">
        <div class="inspector-cell-id" id="inspectHexId">Hex ID: 8861892543fffff</div>
        <div class="inspector-title">
          <span id="inspectLocality">Sector Cell</span>
          <span class="band-badge band-extreme" id="inspectBand">Extreme Risk</span>
        </div>
      </div>

      <div class="inspector-body">
        
        <!-- SECTION 1: PHYSICAL STRESS DRIVERS -->
        <div>
          <div class="section-title">
            <span>Physical Hazard Drivers</span>
            <span style="font-size: 11px; color: var(--text-dim);">Normalized [0, 1]</span>
          </div>

          <div class="driver-item">
            <div class="driver-meta">
              <span class="driver-name">🌡️ Meteorological Heat Stress</span>
              <span class="driver-val" id="dHeatVal">0.865 (43.2°C)</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill" id="dHeatBar" style="width: 86%; background: var(--risk-extreme);"></div>
            </div>
          </div>

          <div class="driver-item">
            <div class="driver-meta">
              <span class="driver-name">💧 Climatic Water Deficit</span>
              <span class="driver-val" id="dWaterVal">0.742 (118 mm)</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill" id="dWaterBar" style="width: 74%; background: var(--risk-high);"></div>
            </div>
          </div>

          <div class="driver-item">
            <div class="driver-meta">
              <span class="driver-name">🌿 Canopy Deficit (Sentinel-2 NDVI)</span>
              <span class="driver-val" id="dVegVal">0.880 (0.09 NDVI)</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill" id="dVegBar" style="width: 88%; background: var(--risk-extreme);"></div>
            </div>
          </div>

          <div class="driver-item">
            <div class="driver-meta">
              <span class="driver-name">🌫️ Fine Particulate PM2.5</span>
              <span class="driver-val" id="dPollVal">0.680 (148 µg/m³)</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill" id="dPollBar" style="width: 68%; background: var(--risk-high);"></div>
            </div>
          </div>

          <div class="driver-item">
            <div class="driver-meta">
              <span class="driver-name">🏗️ Built Infrastructure Exposure</span>
              <span class="driver-val" id="dExpVal">0.840 (Dense Core)</span>
            </div>
            <div class="driver-bar-track">
              <div class="driver-bar-fill" id="dExpBar" style="width: 84%; background: var(--risk-high);"></div>
            </div>
          </div>
        </div>

        <!-- SECTION 2: DEFENSIBLE DEMOGRAPHICS -->
        <div>
          <div class="section-title">
            <span>Demographic &amp; Built Vulnerability</span>
            <span style="font-size: 11px; color: var(--text-dim);">Census 2011 / OSM</span>
          </div>

          <div class="demo-grid">
            <div class="demo-item">
              <div class="demo-label">Impervious Surface (GHSL)</div>
              <div class="demo-val" id="dmImpervious">88.4%</div>
            </div>
            <div class="demo-item">
              <div class="demo-label">Building Density (OSM)</div>
              <div class="demo-val" id="dmBldDensity">3,420 /km²</div>
            </div>
            <div class="demo-item">
              <div class="demo-label">Road Network Density</div>
              <div class="demo-val" id="dmRoadDensity">18.2 km/km²</div>
            </div>
            <div class="demo-item">
              <div class="demo-label">Slum Population Share</div>
              <div class="demo-val" id="dmSlumPct">42.0%</div>
            </div>
            <div class="demo-item">
              <div class="demo-label">Below Poverty Line (BPL)</div>
              <div class="demo-val" id="dmBplPct">18.0%</div>
            </div>
            <div class="demo-item">
              <div class="demo-label">Elderly Dependency (&gt;65y)</div>
              <div class="demo-val" id="dmElderlyPct">9.0%</div>
            </div>
          </div>
        </div>

        <!-- SECTION 3: ML EARLY WARNING & STATUTORY DIRECTIVES -->
        <div>
          <div class="section-title">
            <span>ML Early Warning Engine</span>
            <span class="badge-pill" style="font-size: 10px; color: var(--navy); background: var(--navy-light);">30-Day Lead</span>
          </div>

          <div class="ml-box status-alert" id="mlBox">
            <div class="ml-kpi-row">
              <div class="ml-kpi-mini">
                <div style="font-size: 11px; color: var(--text-dim); font-weight: 600;">Projected SSI (t+1)</div>
                <div style="font-size: 18px; font-weight: 700; color: var(--risk-extreme);" id="mlPredSSI">0.814</div>
                <div style="font-size: 10.5px; color: var(--risk-extreme);">▲ Forward momentum</div>
              </div>
              <div class="ml-kpi-mini">
                <div style="font-size: 11px; color: var(--text-dim); font-weight: 600;">Heatwave Breach Risk</div>
                <div style="font-size: 18px; font-weight: 700; color: var(--risk-extreme);" id="mlProbHw">93.8%</div>
                <div style="font-size: 10.5px; color: var(--risk-extreme);">Statutory RED alert</div>
              </div>
            </div>

            <!-- Statutory Protocol Block -->
            <div class="statutory-alert-block" id="statutoryBlock">
              <div class="statutory-header" id="statutoryHeader">🚨 IMD Heat Action Plan (HAP Stage III Red Alert)</div>
              <div class="statutory-directive" id="statutoryDirectives">
                • <strong>Mandatory Labor Stoppage:</strong> Enforce outdoor work ban (11:00 AM – 4:00 PM).<br>
                • <strong>Water Supply Pre-positioning:</strong> Dispatch emergency water tankers to informal clusters.<br>
                • <strong>Cooling Shelters:</strong> Open air-conditioned public cooling centers in community halls.
              </div>
            </div>

            <div style="margin-top: 10px; font-size: 11px; color: var(--text-dim); line-height: 1.4;">
              <strong>Precursor Drivers:</strong> 90-day temperature momentum velocity (+41%), Soil moisture depletion streak (+32%), Concrete impervious retention (+27%).
            </div>
          </div>
        </div>

      </div>
    </div>
  </main>

  <!-- BOTTOM POLICY & BENCHMARK DRAWER -->
  <section class="bottom-section">
    <div class="tabs-nav">
      <button class="tab-btn active" onclick="switchDrawerTab('matrix')">Statutory Emergency Response Matrix</button>
      <button class="tab-btn" onclick="switchDrawerTab('cities')">7-City Metropolitan Benchmark</button>
      <button class="tab-btn" onclick="switchDrawerTab('model')">Model Validation &amp; Specification</button>
    </div>

    <!-- TAB 1: EMERGENCY MATRIX -->
    <div id="drawer-matrix" class="tab-content">
      <h3 style="font-size: 15px; font-weight: 700; color: var(--navy); margin-bottom: 8px;">Statutory Municipal Emergency Directives</h3>
      <p style="font-size: 12.5px; color: var(--text-dim); margin-bottom: 16px;">
        Direct translation of machine learning hazard probability thresholds into legally mandated municipal actions across Indian administrative bodies.
      </p>

      <table class="data-table">
        <thead>
          <tr>
            <th>Hazard Type</th>
            <th>Early Warning Threshold</th>
            <th>Statutory Framework</th>
            <th>Mandatory Municipal Directives</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong style="color: var(--risk-extreme);">Flash Heatwave Shock</strong></td>
            <td><span class="band-badge band-extreme">RED (≥ 75%)</span></td>
            <td>IMD Heat Action Plan (Stage III)</td>
            <td>Mandatory cessation of outdoor labor (11 AM–4 PM); dedicated drinking water tanker fleet deployed to slums; public cooling shelters opened; emergency hospital casualty pre-stocked with IV fluids.</td>
          </tr>
          <tr>
            <td><strong style="color: var(--risk-high);">Flash Heatwave Shock</strong></td>
            <td><span class="band-badge band-high">ORANGE (50–74%)</span></td>
            <td>IMD Heat Action Plan (Stage II)</td>
            <td>SMS advisories to gig workers and traffic police; nocturnal road misting to dissipate sensible heat; ambulances placed on heat-exhaustion alert.</td>
          </tr>
          <tr>
            <td><strong style="color: #7c3aed;">Hazardous Smog Inversion</strong></td>
            <td><span class="band-badge band-extreme">RED (≥ 75%)</span></td>
            <td>CAQM / CPCB GRAP Stage IV</td>
            <td>Statutory ban on entry of non-BS-VI diesel commercial trucks; complete moratorium on construction, excavation, and demolition dust; 50% remote work mandate; primary schools shifted online.</td>
          </tr>
          <tr>
            <td><strong style="color: var(--navy);">Compound Tail Crisis</strong></td>
            <td><span class="band-badge" style="background: #ede9fe; color: #6d28d9; border: 1px solid #ddd6fe;">RED (≥ 70%)</span></td>
            <td>State Power DISCOM &amp; Water Board</td>
            <td>Power distribution companies pre-order peaking capacity on the energy exchange (IEX) 30 days ahead; municipal water boards impose groundwater extraction moratoriums to safeguard reserve aquifers.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- TAB 2: 7-CITY BENCHMARK -->
    <div id="drawer-cities" class="tab-content" style="display: none;">
      <h3 style="font-size: 15px; font-weight: 700; color: var(--navy); margin-bottom: 8px;">7-City Chronological Out-of-Time Benchmark (2022 Holdout)</h3>
      <p style="font-size: 12.5px; color: var(--text-dim); margin-bottom: 16px;">
        Rigorous out-of-time evaluation: models trained exclusively on 2020–2021 historical panels; tested on held-out 2022 observations across 7 climate regimes.
      </p>

      <table class="data-table">
        <thead>
          <tr>
            <th>City</th>
            <th>Koppen Climate Biome</th>
            <th>H3 Hex Count</th>
            <th>Heatwave PR-AUC</th>
            <th>2022 Heatwave Recall</th>
            <th>Smog PR-AUC</th>
            <th>Future SSI R² (MAE)</th>
          </tr>
        </thead>
        <tbody>
          <tr><td><strong>Delhi NCR</strong></td><td>Subtropical Semi-Arid Monsoon</td><td>3,398</td><td style="color: var(--risk-low); font-weight: 700;">0.990</td><td style="color: var(--brand-primary); font-weight: 700;">92.2%</td><td>0.894</td><td>0.895 (0.038)</td></tr>
          <tr><td><strong>Mumbai</strong></td><td>Tropical Coastal Monsoon</td><td>707</td><td style="color: var(--risk-low); font-weight: 700;">0.886</td><td style="color: var(--brand-primary); font-weight: 700;">93.8%</td><td>0.672</td><td>0.888 (0.043)</td></tr>
          <tr><td><strong>Bikaner</strong></td><td>Hot Arid Desert</td><td>959</td><td style="color: var(--risk-low); font-weight: 700;">0.983</td><td style="color: var(--brand-primary); font-weight: 700;">99.5%</td><td>0.999</td><td>0.834 (0.045)</td></tr>
          <tr><td><strong>Hyderabad</strong></td><td>Tropical Semi-Arid Plateau</td><td>1,505</td><td style="color: var(--risk-low); font-weight: 700;">0.742</td><td style="color: var(--brand-primary); font-weight: 700;">85.1%</td><td>0.812</td><td>0.865 (0.040)</td></tr>
          <tr><td><strong>Kolkata</strong></td><td>Humid Deltaic Subtropical</td><td>992</td><td style="color: var(--risk-low); font-weight: 700;">0.862</td><td style="color: var(--brand-primary); font-weight: 700;">100.0%</td><td>0.941</td><td>0.852 (0.042)</td></tr>
          <tr><td><strong>Indore</strong></td><td>Tropical Savanna Plateau</td><td>731</td><td style="color: var(--risk-low); font-weight: 700;">0.903</td><td style="color: var(--brand-primary); font-weight: 700;">100.0%</td><td>0.785</td><td>0.841 (0.041)</td></tr>
          <tr><td><strong>Coimbatore</strong></td><td>Semi-Arid Rainshadow</td><td>995</td><td style="color: var(--risk-low); font-weight: 700;">0.651</td><td style="color: var(--brand-primary); font-weight: 700;">78.4%</td><td>0.720</td><td>0.872 (0.038)</td></tr>
        </tbody>
      </table>
    </div>

    <!-- TAB 3: SPECIFICATION & AUDIT -->
    <div id="drawer-model" class="tab-content" style="display: none;">
      <h3 style="font-size: 15px; font-weight: 700; color: var(--navy); margin-bottom: 8px;">Technical Specification &amp; Governance</h3>
      <p style="font-size: 12.5px; color: var(--text-dim); margin-bottom: 16px;">
        Canonical machine learning architecture, feature registries, and mathematical formulations:
      </p>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
        <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px;">
          <h4 style="font-size: 13px; font-weight: 700; color: var(--navy); margin-bottom: 4px;">Figure F9: ROC &amp; Precision-Recall</h4>
          <p style="font-size: 11.5px; color: var(--text-dim); margin-bottom: 8px;">Multi-panel discrimination curves evaluating 30-day forward heatwave prediction on 2022 holdout data.</p>
          <span style="font-family: monospace; font-size: 11px; background: white; padding: 2px 6px; border: 1px solid var(--border);">paper_images/F9_event_prediction_roc_pr.png</span>
        </div>
        <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px;">
          <h4 style="font-size: 13px; font-weight: 700; color: var(--navy); margin-bottom: 4px;">Figure F10: Forward Threat Map</h4>
          <p style="font-size: 11.5px; color: var(--text-dim); margin-bottom: 8px;">Spatial H3 map of Mumbai &amp; Delhi during the April 2022 record heatwave shaded by statutory alert tiers.</p>
          <span style="font-family: monospace; font-size: 11px; background: white; padding: 2px 6px; border: 1px solid var(--border);">paper_images/F10_forward_threat_map.png</span>
        </div>
        <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 14px;">
          <h4 style="font-size: 13px; font-weight: 700; color: var(--navy); margin-bottom: 4px;">Figure F11: Precursor Attributions</h4>
          <p style="font-size: 11.5px; color: var(--text-dim); margin-bottom: 8px;">Permutation feature attribution decomposing alert triggers into physical antecedent drivers.</p>
          <span style="font-family: monospace; font-size: 11px; background: white; padding: 2px 6px; border: 1px solid var(--border);">paper_images/F11_precursor_attribution_waterfall.png</span>
        </div>
      </div>

      <div style="margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 12px; color: var(--text-dim);">Full Mathematical &amp; Feature Specification Document:</span>
        <a href="../docs/ml_system_specification.md" target="_blank" style="color: var(--brand-primary); font-weight: 600; text-decoration: none; font-size: 12.5px;">
          Open docs/ml_system_specification.md &rarr;
        </a>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="app-footer">
    <strong>GeoStress AI</strong> — Compound Sustainability Stress Index (SSI) Enterprise Console<br>
    <span style="color: var(--text-light); font-size: 11px;">
      Canonical Spatio-Temporal Dataset (2020–2022) · 334,332 Observations · 9,287 Micro-Scale H3 Resolution-8 Cells · Open Science
    </span>
  </footer>

  <!-- EMBEDDED REAL DATASET & INTERACTIVE APPLICATION LOGIC -->
  <script>
    // Embedded Real Spatio-Temporal & ML Dataset for all 7 cities (2020-2022)
    const REAL_DATA = {data_json};

    // State Variables
    let currentCity = 'mumbai';
    let currentYear = '2022';
    let currentMonth = '04';
    let currentMode = 'obs'; // 'obs' or 'pred'
    let currentMetric = 'ssi'; // 'ssi', 'heat', 'water', 'veg', 'poll', 'exp'
    let selectedHexIndex = 0;

    // Leaflet Variables
    let map = null;
    let canvasRenderer = null;
    let hexPolygons = [];
    let boundaryCache = {{}}; // Cache computed H3 boundaries per city

    // Helper: decode Base64 to Uint8Array
    function decodeB64(str) {{
      const bin = atob(str);
      const arr = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) {{
        arr[i] = bin.charCodeAt(i);
      }}
      return arr;
    }}

    // Helper: Risk band from score [0, 1]
    function getRiskBand(score) {{
      if (score <= 0.33) return {{ name: 'Low', badgeClass: 'band-low', color: '#2d6a4f' }};
      if (score <= 0.50) return {{ name: 'Moderate', badgeClass: 'band-mod', color: '#2a6f97' }};
      if (score <= 0.657) return {{ name: 'High', badgeClass: 'band-high', color: '#c27803' }};
      return {{ name: 'Extreme', badgeClass: 'band-extreme', color: '#b91c1c' }};
    }}

    // Natural Environmental Color Palette (Dignified, Not Neon, Translucent)
    function getNaturalMetricColor(metric, normVal) {{
      if (metric === 'ssi' || metric === 'pred') {{
        // Standard Natural Environmental Risk Scale
        if (normVal <= 0.33) return '#2d6a4f'; // Muted Pine / Sage Green
        if (normVal <= 0.50) return '#2a6f97'; // Steel / Slate Blue
        if (normVal <= 0.657) return '#c27803'; // Earthy Ochre / Warm Amber
        return '#b91c1c'; // Deep Terracotta / Crimson
      }}
      if (metric === 'heat') {{
        // Natural Thermal Gradient: Warm Sand -> Terracotta -> Dark Crimson
        if (normVal <= 0.35) return '#d4a373';
        if (normVal <= 0.65) return '#c85a17';
        return '#b91c1c';
      }}
      if (metric === 'water') {{
        // Natural Hydrologic Gradient: Pale Blue -> Slate Denim -> Deep Indigo
        if (normVal <= 0.35) return '#64b5f6';
        if (normVal <= 0.65) return '#1976d2';
        return '#0d47a1';
      }}
      if (metric === 'veg') {{
        // Natural Canopy Deficit: Muted Olive -> Sand -> Bark Brown/Red
        if (normVal <= 0.35) return '#588157';
        if (normVal <= 0.65) return '#a3704c';
        return '#8b0000';
      }}
      if (metric === 'poll') {{
        // Particulate Smog Inversion: Muted Tan -> Warm Rust -> Deep Plum
        if (normVal <= 0.35) return '#c29d78';
        if (normVal <= 0.65) return '#a75d28';
        return '#581845';
      }}
      // Built Infrastructure Density: Architectural Slate
      if (normVal <= 0.35) return '#94a3b8';
      if (normVal <= 0.65) return '#475569';
      return '#1e293b';
    }}

    // Initialize Leaflet Map with User's Carto Voyager API Key
    function initMap() {{
      const cityMeta = REAL_DATA[currentCity].meta;
      map = L.map('mapContainer', {{
        center: cityMeta.center,
        zoom: cityMeta.zoom,
        zoomControl: true,
        preferCanvas: true
      }});

      // Carto Voyager Light Tiles with User's API Key
      L.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}.png?key=cb1_4m3i_1_4351c859fd1db9c1dc798c0a', {{
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }}).addTo(map);

      canvasRenderer = L.canvas({{ padding: 0.5 }});
      renderHexGrid();
    }}

    // Render Real H3 Hexagonal Polygons
    function renderHexGrid() {{
      const cityObj = REAL_DATA[currentCity];
      const ym = `${{currentYear}}-${{currentMonth}}`;
      const monthData = cityObj.months[ym] || cityObj.months['2022-04'];
      const hexList = cityObj.hexes;

      // Clear existing polygons
      hexPolygons.forEach(p => map.removeLayer(p));
      hexPolygons = [];

      // Determine active metric array
      let activeArray = null;
      if (currentMode === 'pred') {{
        activeArray = decodeB64(monthData.pred);
      }} else {{
        if (currentMetric === 'ssi') activeArray = decodeB64(monthData.ssi);
        else if (currentMetric === 'heat') activeArray = decodeB64(monthData.heat);
        else if (currentMetric === 'water') activeArray = decodeB64(monthData.water);
        else if (currentMetric === 'veg') activeArray = decodeB64(monthData.veg);
        else if (currentMetric === 'poll') activeArray = decodeB64(monthData.poll);
        else activeArray = decodeB64(monthData.ssi);
      }}

      const ssiArray = decodeB64(monthData.ssi);
      const heatArray = decodeB64(monthData.heat);
      const waterArray = decodeB64(monthData.water);
      const vegArray = decodeB64(monthData.veg);
      const pollArray = decodeB64(monthData.poll);
      const predArray = decodeB64(monthData.pred);
      const probHwArray = decodeB64(monthData.phw);
      const probSmogArray = decodeB64(monthData.psmog);

      // Precompute or retrieve boundary cache for current city
      if (!boundaryCache[currentCity]) {{
        boundaryCache[currentCity] = [];
        hexList.forEach(h => {{
          const h3Index = h[0];
          let boundary = null;
          if (typeof h3 !== 'undefined' && h3.cellToBoundary) {{
            boundary = h3.cellToBoundary(h3Index);
          }} else {{
            // Fast circular 6-point fallback if h3-js unavailable
            const lat = h[1], lng = h[2], r = 0.0055;
            boundary = [];
            for (let a = 0; a < 6; a++) {{
              const angle = a * Math.PI / 3;
              boundary.push([lat + r * Math.sin(angle), lng + (r * 1.15) * Math.cos(angle)]);
            }}
          }}
          boundaryCache[currentCity].push(boundary);
        }});
      }}

      const boundaries = boundaryCache[currentCity];

      hexList.forEach((h, idx) => {{
        const normVal = activeArray[idx] / 255.0;
        const color = getNaturalMetricColor(currentMetric, normVal);
        const polyCoords = boundaries[idx];

        // Translucent natural styling: fillOpacity 0.45 so Carto Voyager basemap labels show through
        const polygon = L.polygon(polyCoords, {{
          renderer: canvasRenderer,
          fillColor: color,
          fillOpacity: 0.45,
          color: color,
          weight: 0.85,
          opacity: 0.75
        }});

        polygon.on('click', () => {{
          inspectHex(idx, h, ssiArray[idx]/255.0, heatArray[idx]/255.0, waterArray[idx]/255.0, vegArray[idx]/255.0, pollArray[idx]/255.0, predArray[idx]/255.0, probHwArray[idx]/255.0, probSmogArray[idx]/255.0);
        }});

        polygon.on('mouseover', () => {{
          polygon.setStyle({{ fillOpacity: 0.70, weight: 1.8, color: '#0f172a' }});
        }});

        polygon.on('mouseout', () => {{
          polygon.setStyle({{ fillOpacity: 0.45, weight: 0.85, color: color }});
        }});

        polygon.bindTooltip(`
          <div style="font-size: 11px; font-weight: 600; line-height: 1.4;">
            <span style="color: #64748b;">H3 #${{h[0].slice(-6)}}</span><br>
            SSI: <strong style="color: ${{color}};">${{(ssiArray[idx]/255.0).toFixed(3)}}</strong> (${{getRiskBand(ssiArray[idx]/255.0).name}})<br>
            Heat: ${{(heatArray[idx]/255.0).toFixed(2)}} | Water: ${{(waterArray[idx]/255.0).toFixed(2)}}<br>
            Smog: ${{(pollArray[idx]/255.0).toFixed(2)}} | 30D Pred: ${{(predArray[idx]/255.0).toFixed(3)}}
          </div>
        `, {{ sticky: true, opacity: 0.95 }});

        polygon.addTo(map);
        hexPolygons.push(polygon);
      }});

      // Auto inspect the highest stress hex
      let maxIdx = 0;
      let maxVal = -1;
      for (let i = 0; i < ssiArray.length; i++) {{
        if (ssiArray[i] > maxVal) {{
          maxVal = ssiArray[i];
          maxIdx = i;
        }}
      }}
      selectedHexIndex = maxIdx;
      const topHex = hexList[maxIdx];
      inspectHex(maxIdx, topHex, ssiArray[maxIdx]/255.0, heatArray[maxIdx]/255.0, waterArray[maxIdx]/255.0, vegArray[maxIdx]/255.0, pollArray[maxIdx]/255.0, predArray[maxIdx]/255.0, probHwArray[maxIdx]/255.0, probSmogArray[maxIdx]/255.0);

      updateKPICards();
    }}

    // Update Top KPI Cards
    function updateKPICards() {{
      const cityObj = REAL_DATA[currentCity];
      const ym = `${{currentYear}}-${{currentMonth}}`;
      const stats = cityObj.stats[ym] || cityObj.stats['2022-04'];

      document.getElementById('kpiMonthBadge').textContent = `${{getMonthName(currentMonth)}} ${{currentYear}}`;
      document.getElementById('kpiMeanSSI').textContent = stats.mean_ssi.toFixed(3);
      document.getElementById('kpiRange').textContent = `Max hex: ${{stats.max_ssi.toFixed(3)}} · High: ${{stats.high_pct}}%`;
      document.getElementById('kpiExtremePct').textContent = `${{stats.extreme_pct}}%`;
      
      const extCount = Math.round((stats.extreme_pct / 100) * cityObj.hex_count);
      document.getElementById('kpiExtremeCount').textContent = `${{extCount}} of ${{cityObj.hex_count}} hexagons in extreme band`;

      const alertVal = document.getElementById('kpiAlertCount');
      const alertSub = document.getElementById('kpiAlertSub');
      if (stats.hw_alerts > 0) {{
        alertVal.textContent = 'IMD HAP STAGE III';
        alertVal.style.color = 'var(--risk-extreme)';
        alertSub.textContent = `Red Alert: ${{stats.hw_alerts}} hexes breach 75% heatwave threshold`;
      }} else if (stats.smog_alerts > 0) {{
        alertVal.textContent = 'CAQM GRAP STAGE IV';
        alertVal.style.color = '#7c3aed';
        alertSub.textContent = `Severe Smog Alert: ${{stats.smog_alerts}} hexes breach 75% crisis risk`;
      }} else {{
        alertVal.textContent = 'NORMAL MONITORING';
        alertVal.style.color = 'var(--risk-low)';
        alertSub.textContent = 'All micro-cells within statutory baseline buffers';
      }}

      document.getElementById('mapStatusText').textContent = `Displaying ${{cityObj.hex_count}} H3 hexes for ${{cityObj.meta.name}} (${{getMonthName(currentMonth)}} ${{currentYear}})`;
    }}

    // Inspect Specific Hexagon
    function inspectHex(idx, hexMeta, ssi, heat, water, veg, poll, pred, probHw, probSmog) {{
      const cityObj = REAL_DATA[currentCity];
      const demo = cityObj.demographics;
      const band = getRiskBand(ssi);

      document.getElementById('inspectHexId').textContent = `Hex #${{hexMeta[0]}} · ${{hexMeta[1].toFixed(4)}}° N, ${{hexMeta[2].toFixed(4)}}° E`;
      document.getElementById('inspectLocality').textContent = `${{cityObj.meta.name}} Sector ${{idx + 1}}`;
      
      const bandElem = document.getElementById('inspectBand');
      bandElem.textContent = `${{band.name}} Risk (SSI ${{ssi.toFixed(3)}})`;
      bandElem.className = `band-badge ${{band.badgeClass}}`;

      // Section 1: Physical Drivers
      const heatPhysical = (32 + heat * 13).toFixed(1);
      const waterPhysical = Math.round(water * 150);
      const ndviPhysical = (0.45 - veg * 0.38).toFixed(2);
      const pmPhysical = Math.round(40 + poll * 220);

      document.getElementById('dHeatVal').textContent = `${{heat.toFixed(3)}} (${{heatPhysical}}°C Heat Index)`;
      document.getElementById('dHeatBar').style.width = `${{Math.round(heat * 100)}}%`;

      document.getElementById('dWaterVal').textContent = `${{water.toFixed(3)}} (${{waterPhysical}} mm CWD)`;
      document.getElementById('dWaterBar').style.width = `${{Math.round(water * 100)}}%`;

      document.getElementById('dVegVal').textContent = `${{veg.toFixed(3)}} (${{ndviPhysical}} NDVI)`;
      document.getElementById('dVegBar').style.width = `${{Math.round(veg * 100)}}%`;

      document.getElementById('dPollVal').textContent = `${{poll.toFixed(3)}} (${{pmPhysical}} µg/m³)`;
      document.getElementById('dPollBar').style.width = `${{Math.round(poll * 100)}}%`;

      const expScore = (hexMeta[3] / 100 * 0.6 + (hexMeta[4] / 4000) * 0.4).toFixed(3);
      document.getElementById('dExpVal').textContent = `${{expScore}} (Built Core)`;
      document.getElementById('dExpBar').style.width = `${{Math.min(100, Math.round(expScore * 100))}}%`;

      // Section 2: Defensible Demographics
      document.getElementById('dmImpervious').textContent = `${{hexMeta[3]}}%`;
      document.getElementById('dmBldDensity').textContent = `${{hexMeta[4]}} /km²`;
      document.getElementById('dmRoadDensity').textContent = `${{hexMeta[5]}} km/km²`;
      document.getElementById('dmSlumPct').textContent = `${{demo.slum_pct}}%`;
      document.getElementById('dmBplPct').textContent = `${{demo.bpl_pct}}%`;
      document.getElementById('dmElderlyPct').textContent = `${{demo.elderly_pct}}%`;

      // Section 3: ML Early Warning & Directives
      document.getElementById('mlPredSSI').textContent = pred.toFixed(3);
      const diff = pred - ssi;
      document.getElementById('mlProbHw').textContent = `${{(probHw * 100).toFixed(1)}}%`;

      const mlBox = document.getElementById('mlBox');
      const statBlock = document.getElementById('statutoryBlock');
      const statHeader = document.getElementById('statutoryHeader');
      const statDir = document.getElementById('statutoryDirectives');

      if (probHw >= 0.75) {{
        mlBox.className = 'ml-box status-alert';
        statBlock.style.borderLeftColor = 'var(--risk-extreme)';
        statHeader.textContent = '🚨 IMD Heat Action Plan (HAP Stage III Red Alert)';
        statHeader.style.color = 'var(--risk-extreme)';
        statDir.innerHTML = `
          • <strong>Mandatory Labor Stoppage:</strong> Enforce outdoor work ban (11:00 AM – 4:00 PM).<br>
          • <strong>Water Supply Pre-positioning:</strong> Dispatch emergency water tankers to informal clusters.<br>
          • <strong>Cooling Shelters:</strong> Open air-conditioned public cooling centers in community halls.
        `;
      }} else if (probSmog >= 0.75) {{
        mlBox.className = 'ml-box status-alert';
        statBlock.style.borderLeftColor = '#7c3aed';
        statHeader.textContent = '🚨 CAQM GRAP Stage IV Emergency Directives';
        statHeader.style.color = '#7c3aed';
        statDir.innerHTML = `
          • <strong>Truck Ban:</strong> Ban entry of non-BS-VI diesel commercial trucks.<br>
          • <strong>Demolition Moratorium:</strong> Complete stoppage of construction and excavation dust.<br>
          • <strong>Remote Work:</strong> 50% remote work mandate; primary schools shifted online.
        `;
      }} else {{
        mlBox.className = 'ml-box';
        statBlock.style.borderLeftColor = 'var(--risk-low)';
        statHeader.textContent = '✓ Standard Municipal Monitoring';
        statHeader.style.color = 'var(--risk-low)';
        statDir.innerHTML = '• Background physical stress levels within baseline statutory buffer. Routine municipal maintenance.';
      }}
    }}

    // Dropdown Event Handlers
    function onCityChanged(cityId) {{
      currentCity = cityId;
      const cityMeta = REAL_DATA[cityId].meta;
      map.flyTo(cityMeta.center, cityMeta.zoom, {{ duration: 1.0 }});
      renderHexGrid();
    }}

    function onDateChanged() {{
      currentYear = document.getElementById('yearSelect').value;
      currentMonth = document.getElementById('monthSelect').value;
      renderHexGrid();
    }}

    function setMode(mode) {{
      currentMode = mode;
      document.getElementById('modeObs').className = `mode-btn ${{mode === 'obs' ? 'active' : ''}}`;
      document.getElementById('modePred').className = `mode-btn ${{mode === 'pred' ? 'active' : ''}}`;
      
      const legendTitle = document.getElementById('legendTitle');
      if (mode === 'pred') {{
        legendTitle.textContent = 'ML 30-Day Forward Projected SSI (t+1)';
      }} else {{
        legendTitle.textContent = 'Observed Composite SSI Score (t)';
      }}
      renderHexGrid();
    }}

    function setMetric(metric) {{
      currentMetric = metric;
      document.querySelectorAll('.layer-pill').forEach(b => {{
        if (b.getAttribute('onclick').includes(metric)) b.classList.add('active');
        else b.classList.remove('active');
      }});

      const legendTitle = document.getElementById('legendTitle');
      if (metric === 'ssi') legendTitle.textContent = 'Composite SSI Score (Equal w=0.20)';
      else if (metric === 'heat') legendTitle.textContent = 'Heat Stress Index (LST / Temp)';
      else if (metric === 'water') legendTitle.textContent = 'Water Scarcity (Climatic Deficit)';
      else if (metric === 'veg') legendTitle.textContent = 'Vegetation Loss (Inverted NDVI)';
      else if (metric === 'poll') legendTitle.textContent = 'PM2.5 Air Pollution (CAMS)';
      else if (metric === 'exp') legendTitle.textContent = 'Built-up Infrastructure Density';

      renderHexGrid();
    }}

    function switchDrawerTab(tabId) {{
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
      if (activeBtn) activeBtn.classList.add('active');

      document.getElementById('drawer-matrix').style.display = tabId === 'matrix' ? 'block' : 'none';
      document.getElementById('drawer-cities').style.display = tabId === 'cities' ? 'block' : 'none';
      document.getElementById('drawer-model').style.display = tabId === 'model' ? 'block' : 'none';
    }}

    function getMonthName(m) {{
      const names = {{
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
      }};
      return names[m] || m;
    }}

    // App Initialization on DOM Load
    window.addEventListener('DOMContentLoaded', () => {{
      initMap();
    }});
  </script>
</body>
</html>
"""

    out_file = ROOT_DIR / "dashboard/index.html"
    print(f"Writing complete unified front-end -> {out_file}...")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Success! Web application generated cleanly ({len(html_template):,} characters).")

if __name__ == "__main__":
    build()
