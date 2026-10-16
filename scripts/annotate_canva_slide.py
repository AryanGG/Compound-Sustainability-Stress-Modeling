"""
scripts/annotate_canva_slide.py
───────────────────────────────
Overlays clean, highly polished, color-coded member assignments onto the Canva
architecture flowchart slide with exact alignment and zero text occlusion:
  - Member 1 (Cyan #00D2FF): Atmosphere (Temp/Dewpoint/PM2.5), H3 Mesh (9287 cells), Heat & Smog
  - Member 2 (Emerald Green #10B981): Hydrology, Sentinel-2, Built Exposure, 7-City Normalization
  - Member 3 (Electric Purple #C084FC): Linear Baseline, Smooth Damped SSI Formulation
  - Member 4 (Vibrant Amber #F59E0B): Decoupled Validation Battery (8/8) & Output Typologies
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC_IMG = Path("/Users/aryan/.gemini/antigravity-ide/brain/513699d4-4af2-4952-a87f-23103d18c845/.user_uploaded/media_1792158361900.jpg")
OUT_DIR = Path("reports/presentation")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_IMG = OUT_DIR / "presentation_flowchart_assigned_members.png"

def draw_pill(draw, text, xy, bg_color, text_color, font, pad_x=5, pad_y=2, radius=4, outline=(255, 255, 255, 220)):
    x, y = xy
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    w = tw + pad_x * 2
    h = th + pad_y * 2
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=bg_color, outline=outline, width=1)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, fill=text_color, font=font)
    return w, h

def annotate_slide():
    base_img = Image.open(SRC_IMG).convert("RGBA")
    w, h = base_img.size

    # Transparent overlay for highlight fills and subtle glowing borders
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    draw_solid = ImageDraw.Draw(base_img)

    # Standard macOS TrueType Fonts
    font_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    font_reg = "/System/Library/Fonts/Supplemental/Arial.ttf"
    
    font_header = ImageFont.truetype(font_bold, 13.5)
    font_sub = ImageFont.truetype(font_reg, 9.5)
    font_badge = ImageFont.truetype(font_bold, 9)
    font_badge_sm = ImageFont.truetype(font_bold, 8)
    font_tag = ImageFont.truetype(font_bold, 8)
    font_leg_bold = ImageFont.truetype(font_bold, 8.5)
    font_leg_reg = ImageFont.truetype(font_reg, 7.8)

    # Color Palette
    # Member 1: Cyan
    C_M1_STROKE = (0, 210, 255, 255)
    C_M1_FILL   = (0, 210, 255, 28)
    C_M1_BADGE  = (7, 89, 133, 252)

    # Member 2: Emerald Green
    C_M2_STROKE = (16, 185, 129, 255)
    C_M2_FILL   = (16, 185, 129, 28)
    C_M2_BADGE  = (6, 95, 70, 252)

    # Member 3: Electric Purple
    C_M3_STROKE = (192, 132, 252, 255)
    C_M3_FILL   = (192, 132, 252, 24)
    C_M3_BADGE  = (107, 33, 168, 252)

    # Member 4: Vibrant Amber
    C_M4_STROKE = (245, 158, 11, 255)
    C_M4_FILL   = (245, 158, 11, 28)
    C_M4_BADGE  = (146, 64, 14, 252)

    # ─────────────────────────────────────────────────────────────
    # 1. TOP TITLE BANNER (Replaces Canva top bar with clean header)
    # ─────────────────────────────────────────────────────────────
    draw_solid.rounded_rectangle([195, 16, 829, 78], radius=8, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
    
    t_text = "COMPOUND SUSTAINABILITY STRESS INDEX (SSI) — ARCHITECTURE DEFENSE"
    t_bbox = font_header.getbbox(t_text)
    draw_solid.text((w/2 - (t_bbox[2]-t_bbox[0])/2, 26), t_text, fill=(248, 250, 252), font=font_header)

    s_text = "4-Member Panel Role Allocation • Data & Algorithmic Pipeline Flow: Left to Right"
    s_bbox = font_sub.getbbox(s_text)
    draw_solid.text((w/2 - (s_bbox[2]-s_bbox[0])/2, 51), s_text, fill=(148, 163, 184), font=font_sub)

    # ─────────────────────────────────────────────────────────────
    # 2. DATA SOURCES COLUMN (x: 20 to 140)
    # ─────────────────────────────────────────────────────────────
    # Member 1: Temp & Dewpoint (ERA5) [y: 118 to 171]
    draw_ov.rounded_rectangle([20, 118, 139, 171], radius=4, fill=C_M1_FILL, outline=C_M1_STROKE, width=2)
    draw_pill(draw_solid, "M1", (142, 134), C_M1_BADGE, (255, 255, 255), font_tag)

    # Member 2: Precip & Sentinel-2 (B04, B08, NDVI) [y: 175 to 285]
    draw_ov.rounded_rectangle([20, 175, 139, 285], radius=4, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2", (142, 218), C_M2_BADGE, (255, 255, 255), font_tag)

    # Member 1: PM2.5 (CAMS) [y: 289 to 314]
    draw_ov.rounded_rectangle([20, 289, 139, 314], radius=4, fill=C_M1_FILL, outline=C_M1_STROKE, width=2)
    draw_pill(draw_solid, "M1", (142, 292), C_M1_BADGE, (255, 255, 255), font_tag)

    # Member 2: Built Infrastructure (GHSL, OSM Roads, Buildings) [y: 318 to 399]
    draw_ov.rounded_rectangle([20, 318, 139, 399], radius=4, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2", (142, 348), C_M2_BADGE, (255, 255, 255), font_tag)

    # Clean top badge for Data Sources
    draw_pill(draw_solid, "DATA SOURCES (M1 & M2)", (18, 96), (30, 41, 59, 240), (226, 232, 240), font_tag, outline=(100, 116, 139, 200))

    # ─────────────────────────────────────────────────────────────
    # 3. SPATIAL MESH: UBER H3 GRID (MEMBER 1)
    # ─────────────────────────────────────────────────────────────
    # Container box [x: 166 to 292, y: 204 to 348]
    draw_ov.rounded_rectangle([166, 204, 292, 348], radius=6, fill=C_M1_FILL, outline=C_M1_STROKE, width=2)
    draw_pill(draw_solid, "MEMBER 1: H3 Grid Mesh (9287 × 36)", (166, 185), C_M1_BADGE, (255, 255, 255), font_badge)

    # ─────────────────────────────────────────────────────────────
    # 4. FIVE STRESS DIMENSIONS (M1 & M2)
    # ─────────────────────────────────────────────────────────────
    # Heat Stress [y: 121 to 146] -> Member 1
    draw_ov.rounded_rectangle([321, 121, 440, 146], radius=4, fill=C_M1_FILL, outline=C_M1_STROKE, width=2)
    draw_pill(draw_solid, "M1", (445, 126), C_M1_BADGE, (255, 255, 255), font_tag)

    # Water Stress CWD [y: 157 to 182] -> Member 2
    draw_ov.rounded_rectangle([321, 157, 440, 182], radius=4, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2", (445, 162), C_M2_BADGE, (255, 255, 255), font_tag)

    # Vegetation Stress [y: 197 to 222] -> Member 2
    draw_ov.rounded_rectangle([321, 197, 440, 222], radius=4, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2", (445, 202), C_M2_BADGE, (255, 255, 255), font_tag)

    # Pollution Stress [y: 237 to 262] -> Member 1
    draw_ov.rounded_rectangle([321, 237, 440, 262], radius=4, fill=C_M1_FILL, outline=C_M1_STROKE, width=2)
    draw_pill(draw_solid, "M1", (445, 242), C_M1_BADGE, (255, 255, 255), font_tag)

    # Built Exposure [y: 276 to 301] -> Member 2
    draw_ov.rounded_rectangle([321, 276, 440, 301], radius=4, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2", (445, 281), C_M2_BADGE, (255, 255, 255), font_tag)

    # ─────────────────────────────────────────────────────────────
    # 5. FROZEN BASELINE NORMALIZATION (MEMBER 2)
    # ─────────────────────────────────────────────────────────────
    # Box [x: 453 to 556, y: 176 to 226]
    draw_ov.rounded_rectangle([453, 176, 556, 226], radius=6, fill=C_M2_FILL, outline=C_M2_STROKE, width=2)
    draw_pill(draw_solid, "M2: 7-City Normalization", (449, 155), C_M2_BADGE, (255, 255, 255), font_badge_sm)

    # ─────────────────────────────────────────────────────────────
    # 6. MATHEMATICAL AGGREGATION ENGINE (MEMBER 3)
    # ─────────────────────────────────────────────────────────────
    # Grand Bounding Zone enclosing Linear Path, Compound Path, Equation Arrow, and Compound SSI
    draw_ov.rounded_rectangle([566, 88, 866, 440], radius=10, fill=C_M3_FILL, outline=C_M3_STROKE, width=2)
    
    draw_pill(draw_solid, "MEMBER 3: Linear & Compound Formulation Engine", (568, 68), C_M3_BADGE, (255, 255, 255), font_badge)
    draw_pill(draw_solid, "M3: Equal Linear Baseline (w = 0.20)", (574, 93), C_M3_BADGE, (255, 255, 255), font_badge_sm)
    draw_pill(draw_solid, "M3: Compound SSI (Synergy +25.3%)", (738, 212), C_M3_BADGE, (255, 255, 255), font_badge_sm)
    draw_pill(draw_solid, "M3: Smooth Asymptotic Equation (0.00% Clipping)", (630, 444), C_M3_BADGE, (255, 255, 255), font_badge_sm)

    # ─────────────────────────────────────────────────────────────
    # 7. DECOUPLED VALIDATION BATTERY (MEMBER 4)
    # ─────────────────────────────────────────────────────────────
    # Bottom container enclosing Census, Disaster, VIF, MODIS, and Validation Battery
    draw_ov.rounded_rectangle([132, 466, 630, 595], radius=8, fill=C_M4_FILL, outline=C_M4_STROKE, width=2)
    draw_pill(draw_solid, "MEMBER 4: Decoupled Validation Battery (8/8 Passed)", (132, 446), C_M4_BADGE, (255, 255, 255), font_badge)

    # ─────────────────────────────────────────────────────────────
    # 8. OUTPUT TYPOLOGIES & DECISION PRODUCTS (MEMBER 4)
    # ─────────────────────────────────────────────────────────────
    # Far Right Column enclosing Risk Bands, Final Parquet, and Six Archetypes [x: 872 to 988, y: 164 to 410]
    draw_ov.rounded_rectangle([872, 164, 988, 410], radius=8, fill=C_M4_FILL, outline=C_M4_STROKE, width=2)
    draw_pill(draw_solid, "MEMBER 4: Typologies & Outputs", (860, 144), C_M4_BADGE, (255, 255, 255), font_badge_sm)
    draw_pill(draw_solid, "M4: Six Archetypes (k=6)", (876, 414), C_M4_BADGE, (255, 255, 255), font_badge_sm)

    # Alpha composite highlight layers
    base_img = Image.alpha_composite(base_img, overlay).convert("RGB")
    draw_final = ImageDraw.Draw(base_img)

    # ─────────────────────────────────────────────────────────────
    # 9. SLEEK BOTTOM LEGEND BAR (Four evenly spaced columns)
    # ─────────────────────────────────────────────────────────────
    draw_final.rectangle([0, 622, w, h], fill=(11, 17, 32))
    draw_final.line([(0, 622), (w, 622)], fill=(51, 65, 85), width=1)

    legend_cols = [
        (14, "● MEMBER 1 (Atmosphere & Grid):", "H3 Mesh (9287 cells), Temp, PM2.5, Heat & Smog", (0, 210, 255)),
        (266, "● MEMBER 2 (Hydrology & Built):", "Sentinel-2, Water, Veg Deficit, Built Exposure, Normalization", (16, 185, 129)),
        (526, "● MEMBER 3 (Mathematical Engine):", "Linear SSI (0.20), Joint Tail Trigger, Damped SSI", (192, 132, 252)),
        (780, "● MEMBER 4 (Validation & Policy):", "8/8 Battery, Ground-Truth, 6 Archetypes, Risk Bands", (245, 158, 11))
    ]

    for col_x, title, desc, color in legend_cols:
        draw_final.text((col_x, 629), title, fill=color, font=font_leg_bold)
        draw_final.text((col_x, 644), desc, fill=(203, 213, 225), font=font_leg_reg)

    base_img.save(OUT_IMG, quality=95)
    print(f"✓ Cleanly annotated flowchart saved to: {OUT_IMG.resolve()}")

if __name__ == "__main__":
    annotate_slide()
