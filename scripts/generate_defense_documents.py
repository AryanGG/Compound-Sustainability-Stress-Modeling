"""
scripts/generate_defense_documents.py
──────────────────────────────────────
Generates both:
  1. Project_Defense_Guide_4_Members.pdf (via ReportLab, perfectly balanced across 4 pages)
  2. Project_Defense_Guide_4_Members.docx (via python-docx with styled tables & callouts)
"""

from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUT_DIR = Path("reports/presentation")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUT_DIR / "Project_Defense_Guide_4_Members.pdf"
DOCX_PATH = OUT_DIR / "Project_Defense_Guide_4_Members.docx"

# ══════════════════════════════════════════════════════════════════════════════
# 1. REPORTLAB NUMBERED CANVAS WITH CLEAN RUNNING HEADERS & FOOTERS
# ══════════════════════════════════════════════════════════════════════════════
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (Pages > 1)
        if self._pageNumber > 1:
            self.drawString(1.8 * cm, 28.3 * cm, "Compound Sustainability Stress Index (SSI) — 4-Member Defense Master Reference")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(1.8 * cm, 28.1 * cm, 19.2 * cm, 28.1 * cm)

        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19.2 * cm, 1.2 * cm, footer_text)
        self.drawString(1.8 * cm, 1.2 * cm, "Confidential — Academic Panel Defense Material | Canonical N = 334,332")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(1.8 * cm, 1.5 * cm, 19.2 * cm, 1.5 * cm)
        self.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
# 2. GENERATE PDF VIA REPORTLAB (EXACTLY 4 BALANCED PAGES)
# ══════════════════════════════════════════════════════════════════════════════
def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm
    )

    base = getSampleStyleSheet()
    
    C_PRIMARY = colors.HexColor("#0F172A")
    C_SECONDARY = colors.HexColor("#1E293B")
    C_ACCENT = colors.HexColor("#4338CA") # Indigo
    C_TEXT = colors.HexColor("#1E293B")
    C_MUTED = colors.HexColor("#64748B")
    C_BORDER = colors.HexColor("#E2E8F0")
    
    styles = {
        "title": ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=C_PRIMARY, spaceAfter=2),
        "subtitle": ParagraphStyle("SubTitle", fontName="Helvetica", fontSize=9.5, leading=13, textColor=C_MUTED, spaceAfter=8),
        "h1": ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=C_ACCENT, spaceBefore=8, spaceAfter=4, keepWithNext=True),
        "h2": ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=C_SECONDARY, spaceBefore=6, spaceAfter=3, keepWithNext=True),
        "body": ParagraphStyle("Body", fontName="Helvetica", fontSize=8.5, leading=12, textColor=C_TEXT, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", fontName="Helvetica", fontSize=8.5, leading=11.8, textColor=C_TEXT, leftIndent=10, firstLineIndent=-7, spaceAfter=2.5),
        "callout": ParagraphStyle("Callout", fontName="Helvetica-Oblique", fontSize=8.5, leading=11.5, textColor=colors.HexColor("#312E81")),
        "table_header": ParagraphStyle("TH", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=colors.white, alignment=TA_LEFT),
        "table_cell": ParagraphStyle("TD", fontName="Helvetica", fontSize=8, leading=10.5, textColor=C_TEXT),
        "table_cell_bold": ParagraphStyle("TDB", fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=C_TEXT)
    }

    story = []

    # ─────────────────────────────────────────────────────────────
    # PAGE 1: ARCHITECTURE OVERVIEW + MEMBER 1
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Compound Sustainability Stress Index (SSI)", styles["title"]))
    story.append(Paragraph("<b>4-Member Presentation Defense Master Guide</b> — End-to-End Division, Data, Formulas &amp; Q&amp;A Strategy", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=C_ACCENT, spaceBefore=0, spaceAfter=6))

    # Compact Meta Box
    meta_table = Table([
        [
            Paragraph("<b>Target:</b> Academic Panel Defense", styles["body"]),
            Paragraph("<b>Canonical Dataset:</b> 7 Cities (334,332 Panel Observations)", styles["body"])
        ],
        [
            Paragraph("<b>Spatial Grid:</b> 9,287 Uber H3 Res-8 Hexagons (~0.74 km²)", styles["body"]),
            Paragraph("<b>Longitudinal Span:</b> 36 Months (2020–2022 Balanced)", styles["body"])
        ]
    ], colWidths=[8.7 * cm, 8.7 * cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.75, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Presentation Architecture & Role Division", styles["h1"]))
    flow_table_data = [
        [Paragraph("Member", styles["table_header"]), Paragraph("Assigned Domain", styles["table_header"]), Paragraph("Core Indexes & Key Responsibilities", styles["table_header"])],
        [
            Paragraph("<b>Member 1</b>", styles["table_cell_bold"]),
            Paragraph("Environmental Physics & Atmospheric Drivers", styles["table_cell"]),
            Paragraph("• Problem framing & single-domain index critique<br/>• Uber H3 Res-8 spatial grid design (9,287 cells)<br/>• <b>S_heat</b> (LST + Wet-Bulb via Stull's equation)<br/>• <b>S_poll</b> (NASA SEDAC PM2.5 + surface inversion)", styles["table_cell"])
        ],
        [
            Paragraph("<b>Member 2</b>", styles["table_cell_bold"]),
            Paragraph("Surface Hydrology, Ecology & Built Exposure", styles["table_cell"]),
            Paragraph("• <b>S_water</b> (Soil moisture + NDWI + precip deficit)<br/>• <b>S_veg</b> (Sentinel-2 canopy deficit / inverted NDVI)<br/>• <b>S_exp</b> (Census slums, BPL, OSM built density)<br/>• Cloud-mask audit flags & spatiotemporal interpolation", styles["table_cell"])
        ],
        [
            Paragraph("<b>Member 3</b>", styles["table_cell_bold"]),
            Paragraph("Mathematical Engine & Aggregation Dynamics", styles["table_cell"]),
            Paragraph("• Linear weighted sum flaws & boundary clipping<br/>• Smooth asymptotic SSI formula (damped by 1 - SSI_lin)<br/>• 4 Weighting schemes (Equal, EWM, CRITIC, PCA)<br/>• Rank invariance (rho > 0.94) & Decile 10 synergy (+25.3%)", styles["table_cell"])
        ],
        [
            Paragraph("<b>Member 4</b>", styles["table_cell_bold"]),
            Paragraph("Empirical Validation, Archetypes & Policy", styles["table_cell"]),
            Paragraph("• 8/8 Validation battery & disaster ground-truthing<br/>• Two-way variance decomposition (seasonality vs. spatial)<br/>• 6 Urban typologies (k-means radar profiles)<br/>• Leaflet interactive H3 atlas & municipal policy matrix", styles["table_cell"])
        ],
    ]
    flow_table = Table(flow_table_data, colWidths=[2.2 * cm, 4.8 * cm, 10.4 * cm])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_ACCENT),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 6))

    # MEMBER 1 CONTENT (Fits completely on Page 1)
    story.append(Paragraph("Member 1: Environmental Physics, Spatial Grid & Atmospheric Stress", styles["h1"]))
    story.append(Paragraph("<b>Primary Pitch:</b> Why single-domain indices fail, why hexagons eliminate boundary bias, and how atmospheric heat and toxic air pollution are physically derived.", styles["callout"]))
    story.append(Spacer(1, 3))
    
    m1_points = [
        "<b>1. The Core Scientific Motivation:</b> Most urban indices evaluate environmental risk in isolation (e.g., heat hazard alone or air pollution alone). In reality, Indian metropolises experience coupled crises (e.g., extreme heatwaves exacerbating photochemical smog in summer, or boundary-layer temperature inversions trapping particulate matter in winter). We build a unified compound metric.",
        "<b>2. Spatial Framework (Uber H3 Res-8):</b> Administrative wards suffer from arbitrary boundaries and unequal areas. H3 Resolution 8 provides 9,287 regular hexagons (~0.737 km² each, ~461 m spacing) across 6,844 km² over 7 biomes, ensuring uniform spatial topology and eliminating edge bias.",
        "<b>3. Heat Stress Index (S_heat):</b> Merges Land Surface Temperature (MODIS LST) with ERA5 2m air temperature and relative humidity. Uses <b>Stull's Wet-Bulb Temperature (Tw)</b> equation to calculate human physiological survivability and thermal comfort thresholds.",
        "<b>4. Air Pollution Index (S_poll):</b> Derived from NASA SEDAC Global Annual Surface PM2.5 cross-referenced with CPCB ground telemetry. Captures boundary-layer subsidence (e.g., Delhi winter PM2.5 mean: 355.3 µg/m³).",
        "<b>Key Numbers to Memorize:</b> Total observations: 334,332; Delhi hex count: 3,398; Heat-pollution correlation: r = 0.428 (moderate baseline correlation that surges into lethal synergy during peak episodes)."
    ]
    for pt in m1_points:
        story.append(Paragraph(pt, styles["bullet"]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # PAGE 2: MEMBER 2 & MEMBER 3
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Member 2: Surface Hydrology, Ecological Canopy & Built Exposure", styles["h1"]))
    story.append(Paragraph("<b>Primary Pitch:</b> How Earth observation satellites quantify drought and urban tree canopy loss, and how census infrastructure data is downscaled into micro-scale exposure.", styles["callout"]))
    story.append(Spacer(1, 3))
    
    m2_points = [
        "<b>1. Water Scarcity / Hydrological Stress (S_water):</b> Fuses ERA5 Volumetric Soil Moisture (Layer 1: 0–7 cm depth), precipitation anomalies, and satellite Normalized Difference Water Index (NDWI = (Green - NIR) / (Green + NIR)). Inverted so that 1.0 represents severe desiccation, depleted soil moisture, or surface water absence.",
        "<b>2. Vegetation Deficit Index (S_veg):</b> Derived from Sentinel-2 & MODIS Normalized Difference Vegetation Index (NDVI = (NIR - Red) / (NIR + Red)). Inverted as <b>S_veg = 1.0 - NDVI_normalized</b>. Directly quantifies the loss of urban tree canopy buffers, cooling evapotranspiration, and vegetative sinks.",
        "<b>3. Socio-Demographic & Built Exposure (S_exp):</b> Integrates OpenStreetMap building footprints and road densities with Indian Census tract metrics (slum household share, Below Poverty Line (BPL) concentration, illiteracy, and elderly dependency). Dasymetrically downscaled into each H3 cell.",
        "<b>4. Optical Data Preprocessing & Cloud-Mask Audit:</b> Explicit cloud audit: coastal Mumbai & Coimbatore had 0.00% missing records; Delhi's 70.63% winter optical haze was imputed using spatiotemporal spline interpolation without injecting artificial variance.",
        "<b>Key Numbers to Memorize:</b> Built exposure is strictly orthogonal to physical drivers (|r| = 0.012 to 0.083), proving that human vulnerability forms an independent structural dimension that cannot be inferred from satellite temperatures alone."
    ]
    for pt in m2_points:
        story.append(Paragraph(pt, styles["bullet"]))

    story.append(Spacer(1, 8))

    # MEMBER 3 CONTENT
    story.append(Paragraph("Member 3: Mathematical Formulation & Aggregation Engine", styles["h1"]))
    story.append(Paragraph("<b>Primary Pitch:</b> Why linear weighted averages fail, the mathematical derivation of smooth asymptotic SSI, and statistical proof of rank invariance across weighting schemes.", styles["callout"]))
    story.append(Spacer(1, 3))
    
    m3_points = [
        "<b>1. Fatal Flaws of Linear Indices:</b> Standard indices compute SSI = sum(w_j * S_j). This assumes perfect substitutability and additive independence. If an ad-hoc multiplier is added, scores exceed 1.0, forcing artificial truncation (boundary clipping) that erases variation exactly where risk is highest.",
        "<b>2. Mathematical Formulation of Smooth Compound SSI:</b><br/>"
        "&nbsp;&nbsp;• <b>Linear Base:</b> SSI_lin = sum(w_j * S_j) where w_j = 0.2000 (Equal baseline)<br/>"
        "&nbsp;&nbsp;• <b>Multi-Hazard Trigger:</b> Omega_compound = I(S_heat >= q_90) * I(S_poll >= q_90)<br/>"
        "&nbsp;&nbsp;• <b>Asymptotic Damped Formulation:</b> SSI = SSI_lin + gamma * Omega_compound * (1.0 - SSI_lin)<br/>"
        "&nbsp;&nbsp;• Parameters: Coupling intensity gamma = 0.30, threshold quantile q = 0.90.",
        "<b>3. The Role of the Damping Factor (1.0 - SSI_lin):</b> As linear stress approaches 1.0, the marginal amplification decelerates smoothly. Result: <b>0.00% ceiling truncation</b> (exactly 0 out of 334,332 records clamped at 1.000).",
        "<b>4. Weight Sensitivity & Spatial Rank Invariance:</b> Tested Equal vs. Entropy Weight Method (EWM), CRITIC, and Principal Component Analysis (PCA). Spearman rank correlations exceed rho = 0.89 to 0.985 (p < 0.001). Spatial priorities remain robust regardless of the weighting philosophy.",
        "<b>Key Numbers to Memorize:</b> Decile 10 Compound Synergy Amplification is <b>+25.3%</b> over the linear baseline; boundary clipping rate is strictly <b>0.00%</b>."
    ]
    for pt in m3_points:
        story.append(Paragraph(pt, styles["bullet"]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # PAGE 3: MEMBER 4 + SYNTHESIS & CARTOGRAPHY
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Member 4: Empirical Validation Battery, Typologies & Policy Translation", styles["h1"]))
    story.append(Paragraph("<b>Primary Pitch:</b> Real-world disaster ground-truthing (heatwaves, cloudbursts, winter smog), the 6 urban typologies, and translating indices into municipal adaptation policy.", styles["callout"]))
    story.append(Spacer(1, 3))
    
    m4_points = [
        "<b>1. The 8/8 Pre-Registered Validation Battery:</b> The index underwent 8 rigorous construct tests (orthogonality |r| <= 0.58, ceiling truncation 0.00%, weight stability rho > 0.89, variance decomposition, and disaster alerts). All 8 passed.",
        "<b>2. Historical Ground-Truthing of Real Climate Shocks:</b><br/>"
        "&nbsp;&nbsp;• <b>Spring 2022 Mega-Heatwave:</b> Temperatures exceeded 46°C in Rajasthan/MP. Model triggered a <b>96.5% anomaly alert rate</b> in Bikaner (SSI jumped 0.596 -> 0.751, t = 3.46, p = 0.0008).<br/>"
        "&nbsp;&nbsp;• <b>October 2021 Hyderabad Deluge:</b> Cloudburst triggered lake breaches. Model generated a <b>100.0% city-wide alert</b> across all 1,505 cells, matching emergency declarations.<br/>"
        "&nbsp;&nbsp;• <b>Delhi Winter Smog Inversion:</b> Continuous <b>+16.2% seasonal stress lift</b> captured during severe post-monsoon subsidence.",
        "<b>3. Two-Way Variance Decomposition:</b> Total variance decomposes into <b>76.5% Temporal Seasonality</b>, <b>20.4% Spatial Morphology</b>, and <b>3.1% Residual Synergy</b>. Continental inland cities (Delhi, Bikaner) are >80% seasonality-driven, whereas coastal Mumbai and plateau Coimbatore are dominated by micro-spatial morphology.",
        "<b>4. Pan-India Urban Typologies (k = 6 Archetypes):</b> Unsupervised k-means clustering (Silhouette s = 0.147, ARI = 0.812) categorizes cells into 6 operational archetypes (A1: Coastal Marine Sinks, A2: Industrial Plumes, A3: Water-Stressed Arid Cores, A4: Densifying Plateaus, A5: Severe Inversion Hubs, A6: Dense Slum/Built Exposure).",
        "<b>5. Municipal Policy Action & Cartography:</b> Replaces blanket nationwide programs with targeted interventions (e.g., cool-roof mandates for A3, regional airshed controls for A5, and decentralized rainwater retention for A4). Illustrated via our 300 DPI publication cartography (Figure 1) and Leaflet H3 interactive atlas."
    ]
    for pt in m4_points:
        story.append(Paragraph(pt, styles["bullet"]))

    story.append(Spacer(1, 8))

    # Synthesis Table for the 7 Cities
    story.append(Paragraph("Synthesis of Empirical Findings Across 7 Metropolises", styles["h1"]))
    city_summary_data = [
        [Paragraph("City", styles["table_header"]), Paragraph("Köppen Biome", styles["table_header"]), Paragraph("Hex Count", styles["table_header"]), Paragraph("Mean SSI", styles["table_header"]), Paragraph("Dominant Hazard", styles["table_header"]), Paragraph("Extreme Risk %", styles["table_header"])],
        [Paragraph("<b>Delhi NCR</b>", styles["table_cell_bold"]), Paragraph("Subtropical Semi-Arid", styles["table_cell"]), Paragraph("3,398", styles["table_cell"]), Paragraph("0.514", styles["table_cell"]), Paragraph("Heat & PM2.5", styles["table_cell"]), Paragraph("48.2%", styles["table_cell"])],
        [Paragraph("<b>Kolkata</b>", styles["table_cell_bold"]), Paragraph("Tropical Wet-and-Dry", styles["table_cell"]), Paragraph("992", styles["table_cell"]), Paragraph("0.536", styles["table_cell"]), Paragraph("Heat & Humidity", styles["table_cell"]), Paragraph("52.1%", styles["table_cell"])],
        [Paragraph("<b>Mumbai</b>", styles["table_cell_bold"]), Paragraph("Tropical Coastal Monsoon", styles["table_cell"]), Paragraph("707", styles["table_cell"]), Paragraph("0.462", styles["table_cell"]), Paragraph("Water & Exposure", styles["table_cell"]), Paragraph("38.4%", styles["table_cell"])],
        [Paragraph("<b>Bikaner</b>", styles["table_cell_bold"]), Paragraph("Hot Arid Desert", styles["table_cell"]), Paragraph("959", styles["table_cell"]), Paragraph("0.501", styles["table_cell"]), Paragraph("Water & Veg Deficit", styles["table_cell"]), Paragraph("46.8%", styles["table_cell"])],
        [Paragraph("<b>Hyderabad</b>", styles["table_cell_bold"]), Paragraph("Tropical Semi-Arid Plateau", styles["table_cell"]), Paragraph("1,505", styles["table_cell"]), Paragraph("0.458", styles["table_cell"]), Paragraph("Water Deficit", styles["table_cell"]), Paragraph("36.5%", styles["table_cell"])],
        [Paragraph("<b>Indore</b>", styles["table_cell_bold"]), Paragraph("Central Semi-Arid Inland", styles["table_cell"]), Paragraph("731", styles["table_cell"]), Paragraph("0.472", styles["table_cell"]), Paragraph("Veg Deficit", styles["table_cell"]), Paragraph("41.0%", styles["table_cell"])],
        [Paragraph("<b>Coimbatore</b>", styles["table_cell_bold"]), Paragraph("Rain-Shadow Semi-Arid", styles["table_cell"]), Paragraph("995", styles["table_cell"]), Paragraph("0.441", styles["table_cell"]), Paragraph("Water Deficit", styles["table_cell"]), Paragraph("32.8%", styles["table_cell"])],
    ]
    city_table = Table(city_summary_data, colWidths=[2.8 * cm, 4.2 * cm, 2.2 * cm, 2.2 * cm, 3.5 * cm, 2.5 * cm])
    city_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#334155")),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(city_table)

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────────
    # PAGE 4: PANEL Q&A DEFENSE MATRIX (FULL DEDICATED PAGE)
    # ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Panel Q&amp;A Defense Matrix (Expected Tough Questions)", styles["title"]))
    story.append(Paragraph("<b>Rapid-Fire Rehearsal Sheet</b> — Direct answers, statistical defenses, and appointed leads for panel cross-examination.", styles["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=C_ACCENT, spaceBefore=0, spaceAfter=8))

    qa_data = [
        [Paragraph("Expected Panel Question", styles["table_header"]), Paragraph("Lead", styles["table_header"]), Paragraph("Model Defense Answer", styles["table_header"])],
        [
            Paragraph("<i>'Why use hexagons instead of municipal ward boundaries?'</i>", styles["table_cell_bold"]),
            Paragraph("Member 1", styles["table_cell"]),
            Paragraph("Wards suffer from the Modifiable Areal Unit Problem (MAUP)—irregular geometries, arbitrary gerrymandering, and unequal populations. Uber H3 Res-8 gives uniform ~0.74 km² areas, identical spatial resolution across all 7 cities, and isotropic spatial lag calculations without administrative distortions.", styles["table_cell"])
        ],
        [
            Paragraph("<i>'If Sentinel-2 has cloud cover during monsoons, isn't your vegetation data corrupted?'</i>", styles["table_cell_bold"]),
            Paragraph("Member 2", styles["table_cell"]),
            Paragraph("We audited cloud-mask flags explicitly. In coastal cities like Mumbai and Coimbatore, complete optical coverage was 100% verified. Where winter haze or localized monsoons occurred, we applied longitudinal spline interpolation across our balanced 36-month panel, preserving seasonal physics without injecting synthetic noise.", styles["table_cell"])
        ],
        [
            Paragraph("<i>'Why did you choose Equal Weighting over PCA or machine learning?'</i>", styles["table_cell_bold"]),
            Paragraph("Member 3", styles["table_cell"]),
            Paragraph("PCA weights maximize variance along multicollinear axes; because socio-demographic exposure is largely orthogonal to atmospheric drivers, PCA collapsed built exposure to w=0.0189, effectively erasing human vulnerability! Our sensitivity battery proved 98.6% rank concordance between Equal and CRITIC schemes, confirming equal weighting is robust and policy-transparent.", styles["table_cell"])
        ],
        [
            Paragraph("<i>'How do you prove your compound index is better than a simple average?'</i>", styles["table_cell_bold"]),
            Paragraph("Member 3 / Member 4", styles["table_cell"]),
            Paragraph("Simple averages fail to capture threshold-triggered mortality. In Decile 10 multi-hazard conditions, our smooth asymptotic formulation reveals a +25.3% risk amplification that linear models completely miss. Furthermore, our 8/8 validation battery demonstrated 96.5% to 100% disaster alert detection during actual ground-truth events.", styles["table_cell"])
        ],
        [
            Paragraph("<i>'What is the practical policy value of having 6 archetypes?'</i>", styles["table_cell_bold"]),
            Paragraph("Member 4", styles["table_cell"]),
            Paragraph("Cities cannot use a one-size-fits-all climate budget. Bikaner (Archetype 3) requires groundwater replenishment and shade infrastructure, whereas Delhi (Archetype 5) requires regional inter-state airshed anti-smog regulation. Archetypes allow municipal commissioners to target specific capital expenditures.", styles["table_cell"])
        ],
        [
            Paragraph("<i>'Is your index applicable to other global cities outside India?'</i>", styles["table_cell_bold"]),
            Paragraph("All Members", styles["table_cell"]),
            Paragraph("Yes. Because our foundational inputs rely on globally accessible Earth Observation grids (ERA5 reanalysis, MODIS, Sentinel-2, NASA SEDAC, and OpenStreetMap), the entire analytical pipeline is globally transferable to any urbanizing Global South metropolis without bespoke local sensors.", styles["table_cell"])
        ]
    ]

    qa_table = Table(qa_data, colWidths=[4.2 * cm, 2.0 * cm, 11.2 * cm])
    qa_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
    ]))
    story.append(qa_table)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"✓ PDF successfully generated at: {PDF_PATH.resolve()}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. GENERATE WORD DOCX VIA PYTHON-DOCX
# ══════════════════════════════════════════════════════════════════════════════
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def build_docx():
    doc = docx.Document()

    for s in doc.sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.75)
        s.right_margin = Inches(0.75)

    # Document Title
    p_title = doc.add_paragraph()
    run_title = p_title.add_run("Compound Sustainability Stress Index (SSI)")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(22)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)
    p_title.paragraph_format.space_after = Pt(2)

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run("4-Member Panel Defense Master Guide — End-to-End Division, Formulas, Calculations & Q&A Strategy")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(11)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)
    p_sub.paragraph_format.space_after = Pt(12)

    # Overview Metadata Table
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_data = [
        ("Target Audience: Academic Panel Defense", "Canonical Dataset: 7 Cities (334,332 Observations)"),
        ("Spatial Grid: 9,287 Uber H3 Res-8 Hexagons (~0.74 km²)", "Longitudinal Span: 36 Months (2020–2022 Balanced)")
    ]
    for r_idx, (c1, c2) in enumerate(meta_data):
        row = meta_table.rows[r_idx]
        row.cells[0].text = c1
        row.cells[1].text = c2
        for cell in row.cells:
            set_cell_background(cell, "F1F5F9")
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            for p in cell.paragraphs:
                p.runs[0].font.size = Pt(9.5)
                p.runs[0].font.name = "Calibri"
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(30, 41, 59)
    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 1: Presentation Flow
    h1 = doc.add_heading("1. Presentation Architecture & Role Division", level=1)
    h1.paragraph_format.space_before = Pt(10)
    h1.paragraph_format.space_after = Pt(4)

    flow_p = doc.add_paragraph(
        "To ensure a seamless, non-repetitive narrative for the evaluation panel, the project is structured as an end-to-end scientific pipeline. "
        "Each member owns specific foundational sub-indices, their data pipelines, and their respective mathematical or empirical validation chapters."
    )
    flow_p.paragraph_format.space_after = Pt(8)

    roles_table = doc.add_table(rows=5, cols=3)
    roles_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Member", "Assigned Domain", "Core Indexes & Key Responsibilities"]
    for i, h in enumerate(headers):
        cell = roles_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, "4338CA")
        p = cell.paragraphs[0]
        p.runs[0].font.name = "Calibri"
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    roles_content = [
        ("Member 1", "Environmental Physics & Atmospheric Drivers", "• Problem framing & single-domain index critique\n• Uber H3 Res-8 spatial grid design (9,287 cells)\n• S_heat (LST + Wet-Bulb via Stull's equation)\n• S_poll (NASA SEDAC PM2.5 + surface inversion)"),
        ("Member 2", "Surface Hydrology, Ecology & Built Exposure", "• S_water (Soil moisture + NDWI + precip deficit)\n• S_veg (Sentinel-2 canopy deficit / inverted NDVI)\n• S_exp (Census slums, BPL, OSM built density)\n• Cloud-mask audit flags & spatiotemporal interpolation"),
        ("Member 3", "Mathematical Engine & Aggregation Dynamics", "• Linear weighted sum flaws & boundary clipping\n• Smooth asymptotic SSI formula (damped by 1 - SSI_lin)\n• 4 Weighting schemes (Equal, EWM, CRITIC, PCA)\n• Rank invariance (rho > 0.94) & Decile 10 synergy (+25.3%)"),
        ("Member 4", "Empirical Validation, Archetypes & Policy", "• 8/8 Validation battery & disaster ground-truthing\n• Two-way variance decomposition (seasonality vs. spatial)\n• 6 Urban typologies (k-means radar profiles)\n• Leaflet interactive H3 atlas & municipal policy matrix")
    ]

    for r_idx, row_data in enumerate(roles_content, start=1):
        for c_idx, text in enumerate(row_data):
            cell = roles_table.cell(r_idx, c_idx)
            cell.text = text
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(8.5)
            p.runs[0].font.name = "Calibri"

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Individual Member Sections
    sections_content = [
        (
            "Member 1: Environmental Physics, Spatial Grid & Atmospheric Stress",
            "Role: The Environmental Physicist & Climatologist | Primary Focus: Problem framing, H3 grid, Heat stress & Air pollution.",
            [
                ("The Scientific Problem:", "Traditional urban indices evaluate environmental hazards in silos (e.g., heat alone or air pollution alone). In reality, Indian metropolises experience coupled crises where high temperatures exacerbate ground-level ozone and smog, or boundary-layer inversions trap particulates in winter. We provide a compound metric."),
                ("Uber H3 Res-8 Hexagonal Mesh:", "Administrative ward boundaries suffer from the Modifiable Areal Unit Problem (MAUP) due to irregular geometries, gerrymandering, and unequal populations. H3 Resolution 8 partitions 7 cities into 9,287 regular hexagons (~0.737 km² each, ~461m spacing) across 6,844 km², enabling isotropic spatial modeling."),
                ("Heat Stress Index (S_heat):", "Integrates Land Surface Temperature (LST from MODIS Terra/Aqua) with 2m ambient air temperature and relative humidity from ERA5 reanalysis. Uses Stull's Wet-Bulb Temperature (Tw) formula to quantify human physiological survivability limits."),
                ("Air Pollution Index (S_poll):", "Derived from NASA SEDAC Global Annual Surface PM2.5 cross-calibrated against CPCB ground telemetry. Captures boundary-layer subsidence and winter stagnation (e.g., Delhi winter PM2.5 mean: 355.3 µg/m³)."),
                ("Key Numbers to Quote:", "Total observations: 334,332; Delhi hex count: 3,398; Heat-Pollution correlation: r = 0.428.")
            ]
        ),
        (
            "Member 2: Surface Hydrology, Ecological Canopy & Built Exposure",
            "Role: The Remote Sensing & Micro-Urban Geography Specialist | Primary Focus: Water scarcity, vegetation loss & human exposure.",
            [
                ("Water Scarcity Index (S_water):", "Combines ERA5 Volumetric Soil Moisture (Layer 1: 0–7 cm depth), monthly precipitation anomalies, and satellite Normalized Difference Water Index (NDWI = (Green - NIR) / (Green + NIR)). Inverted so that 1.0 represents extreme drought, desiccation, or surface water depletion."),
                ("Vegetation Deficit Index (S_veg):", "Derived from Sentinel-2 & MODIS Normalized Difference Vegetation Index (NDVI = (NIR - Red) / (NIR + Red)). Inverted as S_veg = 1.0 - NDVI_normalized to measure urban canopy depletion and cooling loss."),
                ("Built & Socio-Demographic Exposure (S_exp):", "Integrates OpenStreetMap building footprints and road densities with Indian Census tract metrics (slum household share, BPL density, elderly concentration). Dasymetrically downscaled into each H3 cell."),
                ("Cloud-Mask Audit & Preprocessing:", "Strict audit flags: coastal Mumbai and Coimbatore had 0.00% missing records; Delhi's 70.63% winter haze was imputed via spatiotemporal spline interpolation without artificial noise."),
                ("Key Numbers to Quote:", "Built exposure is orthogonal to physical drivers (|r| = 0.012 to 0.083), proving that human vulnerability is an independent structural dimension.")
            ]
        ),
        (
            "Member 3: Mathematical Formulation & Aggregation Engine",
            "Role: The Applied Mathematician & Index Architect | Primary Focus: Aggregation flaws, smooth asymptotic coupling & weighting invariance.",
            [
                ("Flaws of Standard Linear Sums:", "Linear weighted sums (sum w_j * S_j) assume additive independence. Adding ad-hoc multipliers causes scores to exceed 1.0, forcing artificial truncation (boundary clipping) that erases variation where risk is most extreme."),
                ("Smooth Asymptotic Formula:", "Linear Base: SSI_lin = sum(w_j * S_j) with equal weights w_j = 0.2000.\nCompound Trigger: Omega_compound = I(S_heat >= q_90) * I(S_poll >= q_90) with threshold quantile q = 0.90.\nSmooth Damped SSI: SSI = SSI_lin + gamma * Omega_compound * (1.0 - SSI_lin) where gamma = 0.30."),
                ("The Endogenous Damping Factor:", "The term (1.0 - SSI_lin) smoothly decelerates marginal compound amplification as linear stress approaches 1.0. Result: exactly 0.00% boundary clipping (0 out of 334,332 records clamped)."),
                ("Weight Sensitivity & Spatial Rank Invariance:", "Tested Equal vs. Entropy Weight Method (EWM), CRITIC, and PCA. Spearman rank correlations exceed rho = 0.89 to 0.985 (p < 0.001), proving spatial priorities are invariant to weighting methodology."),
                ("Key Numbers to Quote:", "Decile 10 Compound Synergy Amplification: +25.3% over linear models; 0.00% boundary clipping.")
            ]
        ),
        (
            "Member 4: Empirical Validation Battery, Typologies & Policy Translation",
            "Role: The Validation Scientist & Urban Policy Strategist | Primary Focus: 8/8 validation tests, disaster ground-truthing & 6 archetypes.",
            [
                ("8/8 Validation Battery:", "Pre-registered construct validation: Orthogonality (|r| <= 0.58), Ceiling truncation (0.00%), Weight stability (rho > 0.89), Two-way variance decomposition, and Historical disaster alert triggers."),
                ("Historical Ground-Truthing of Real Disasters:", "Spring 2022 Mega-Heatwave: Triggered a 96.5% anomaly alert rate in Bikaner (SSI spiked 0.596 -> 0.751, t = 3.46, p = 0.0008).\nOctober 2021 Hyderabad Deluge: Triggered 100.0% city-wide alert (all 1,505 cells flagged), matching emergency declarations.\nDelhi Winter Smog Inversion: Continuous +16.2% seasonal stress lift captured during post-monsoon subsidence."),
                ("Two-Way Variance Decomposition:", "Decomposes into 76.5% Temporal Seasonality vs. 20.4% Spatial Urban Morphology vs. 3.1% Residual Synergy. Inland continental cities (Delhi/Bikaner) are >80% seasonal, whereas coastal Mumbai and plateau Coimbatore are driven by micro-spatial morphology."),
                ("Pan-India Urban Typologies (k = 6 Archetypes):", "Unsupervised k-means clustering (Silhouette s = 0.147, ARI = 0.812) identifies 6 operational archetypes (A1: Coastal Marine Sinks, A2: Industrial Plumes, A3: Water-Stressed Arid Cores, A4: Densifying Plateaus, A5: Severe Inversion Hubs, A6: Dense Slum/Built Exposure)."),
                ("Municipal Adaptation Policy:", "Replaces blanket nationwide programs with targeted interventions (e.g., cool-roof mandates for A3, regional airshed controls for A5, and stormwater detention for A4).")
            ]
        )
    ]

    for title, subtitle, bullets in sections_content:
        h = doc.add_heading(title, level=1)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(2)

        sub_p = doc.add_paragraph(subtitle)
        sub_p.runs[0].font.name = "Calibri"
        sub_p.runs[0].font.size = Pt(9.5)
        sub_p.runs[0].font.italic = True
        sub_p.runs[0].font.color.rgb = RGBColor(79, 70, 229)
        sub_p.paragraph_format.space_after = Pt(4)

        for b_title, b_desc in bullets:
            bp = doc.add_paragraph(style='List Bullet')
            run_b = bp.add_run(b_title + " ")
            run_b.font.name = "Calibri"
            run_b.font.bold = True
            run_b.font.size = Pt(9)
            run_d = bp.add_run(b_desc)
            run_d.font.name = "Calibri"
            run_d.font.size = Pt(9)
            bp.paragraph_format.space_after = Pt(3)

    # Q&A Matrix Table
    h_qa = doc.add_heading("5. Panel Q&A Defense Matrix (Expected Tough Questions)", level=1)
    h_qa.paragraph_format.space_before = Pt(14)
    h_qa.paragraph_format.space_after = Pt(4)

    qa_table = doc.add_table(rows=7, cols=3)
    qa_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    qa_headers = ["Expected Panel Question", "Lead", "Model Defense Answer"]
    for i, h in enumerate(qa_headers):
        cell = qa_table.cell(0, i)
        cell.text = h
        set_cell_background(cell, "1E293B")
        p = cell.paragraphs[0]
        p.runs[0].font.name = "Calibri"
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)

    qa_rows = [
        ("Why use hexagons instead of municipal ward boundaries?", "Member 1", "Wards suffer from the Modifiable Areal Unit Problem (MAUP)—irregular geometries, arbitrary gerrymandering, and unequal populations. Uber H3 Res-8 gives uniform ~0.74 km² areas, identical spatial resolution across all 7 cities, and isotropic spatial lag calculations."),
        ("If Sentinel-2 has cloud cover during monsoons, isn't your vegetation data corrupted?", "Member 2", "We audited cloud-mask flags explicitly. In coastal cities like Mumbai and Coimbatore, complete optical coverage was 100% verified. Where winter haze or localized monsoons occurred, we applied longitudinal spline interpolation across our 36-month panel, preserving seasonal physics without injecting synthetic noise."),
        ("Why did you choose Equal Weighting over PCA or machine learning?", "Member 3", "PCA weights maximize variance along multicollinear axes; because socio-demographic exposure is largely orthogonal to atmospheric drivers, PCA collapsed built exposure to w=0.0189, effectively erasing human vulnerability! Our sensitivity battery proved 98.6% rank concordance between Equal and CRITIC schemes, confirming equal weighting is robust and policy-transparent."),
        ("How do you prove your compound index is better than a simple average?", "Member 3 / 4", "Simple averages fail to capture threshold-triggered mortality. In Decile 10 multi-hazard conditions, our smooth asymptotic formulation reveals a +25.3% risk amplification that linear models completely miss. Furthermore, our 8/8 validation battery demonstrated 96.5% to 100% disaster alert detection during actual ground-truth events."),
        ("What is the practical policy value of having 6 archetypes?", "Member 4", "Cities cannot use a one-size-fits-all climate budget. Bikaner (Archetype 3) requires groundwater replenishment and shade infrastructure, whereas Delhi (Archetype 5) requires regional inter-state airshed anti-smog regulation. Archetypes allow municipal commissioners to target specific capital expenditures."),
        ("Is your index applicable to other global cities outside India?", "All Members", "Yes. Because our foundational inputs rely on globally accessible Earth Observation grids (ERA5 reanalysis, MODIS, Sentinel-2, NASA SEDAC, and OpenStreetMap), the entire analytical pipeline is globally transferable to any urbanizing Global South metropolis without bespoke local sensors.")
    ]

    for r_idx, row_data in enumerate(qa_rows, start=1):
        for c_idx, text in enumerate(row_data):
            cell = qa_table.cell(r_idx, c_idx)
            cell.text = text
            if r_idx % 2 == 1:
                set_cell_background(cell, "F8FAFC")
            set_cell_margins(cell, top=70, bottom=70, left=90, right=90)
            p = cell.paragraphs[0]
            p.runs[0].font.size = Pt(8.5)
            p.runs[0].font.name = "Calibri"

    doc.save(str(DOCX_PATH))
    print(f"✓ Word document successfully generated at: {DOCX_PATH.resolve()}")

if __name__ == "__main__":
    build_pdf()
    build_docx()
