DESIGN = {
    "color_brand":           "#2563EB",
    "color_brand_light":     "#EFF6FF",
    "color_brand_dark":      "#1D4ED8",
    "color_bg":              "#F7F7F7",
    "color_surface":         "#FFFFFF",
    "color_border":          "#E5E5E5",
    "color_border_strong":   "#D0D0D0",
    "color_text_primary":    "#1A1A1A",
    "color_text_secondary":  "#666666",
    "color_text_muted":      "#999999",
    "color_success":         "#42C366",
    "color_warning":         "#ECB730",
    "color_error":           "#EB3424",
    "accent_amethyst":       "#9061FF",
    "accent_bluetron":       "#2A6DFB",
    "accent_forest":         "#42C366",
    "accent_honey":          "#ECB730",
    "accent_crimson":        "#EB3424",
    "space_1": 4,  "space_2": 8,  "space_3": 12,
    "space_4": 16, "space_5": 20, "space_6": 24,
    "space_8": 32, "space_10": 40, "space_12": 48,
    "radius_sm": 6, "radius_md": 10, "radius_lg": 16, "radius_full": 9999,
    "shadow_xs": "0 1px 2px rgba(0,0,0,0.05)",
    "shadow_sm": "0 2px 8px rgba(0,0,0,0.08)",
    "shadow_md": "0 4px 20px rgba(0,0,0,0.10)",
    "font_sans": "Inter, ui-sans-serif, system-ui, sans-serif",
    "font_mono": "'Fira Code', 'Roboto Mono', monospace",
}

CLUSTER_COLORS = {
    "technology_ict":         "#2A6DFB",
    "financial_services":     "#5B8FFC",
    "wholesale_distribution": "#1A4FBF",
    "consulting_professional":"#9061FF",
    "media_marketing":        "#B08AFF",
    "education_research":     "#6A3FD4",
    "healthcare_pharma":      "#42C366",
    "food_hospitality":       "#7DD99A",
    "energy_utilities":       "#2A8A46",
    "manufacturing_industrial":"#ECB730",
    "construction_real_estate":"#F5D060",
    "transport_logistics":    "#C48A10",
    "retail_ecommerce":       "#EB3424",
    "other":                  "#A0A0A0",
    "unknown":                "#D0D0D0",
}

CLUSTER_LABELS = {
    "technology_ict":           "Tech & ICT",
    "financial_services":       "Financial Services",
    "wholesale_distribution":   "Wholesale",
    "consulting_professional":  "Consulting",
    "media_marketing":          "Media & Marketing",
    "education_research":       "Education",
    "healthcare_pharma":        "Healthcare",
    "food_hospitality":         "Food & Hospitality",
    "energy_utilities":         "Energy",
    "manufacturing_industrial": "Manufacturing",
    "construction_real_estate": "Construction",
    "transport_logistics":      "Logistics",
    "retail_ecommerce":         "Retail & E-Commerce",
    "other":                    "Other",
    "unknown":                  "Unknown",
}

PLOTLY_TEMPLATE = "plotly_white"

PLOTLY_LAYOUT = {
    "template":          PLOTLY_TEMPLATE,
    "font_family":       "Inter, ui-sans-serif, system-ui, sans-serif",
    "font_color":        "#1A1A1A",
    "paper_bgcolor":     "#FFFFFF",
    "plot_bgcolor":      "#F7F7F7",
    "title_font_size":   15,
    "title_font_color":  "#1A1A1A",
    "legend_bgcolor":    "#FFFFFF",
    "legend_bordercolor":"#E5E5E5",
    "legend_borderwidth": 1,
    "margin": dict(l=24, r=24, t=40, b=24),
    "colorway": [
        "#2A6DFB", "#9061FF", "#42C366",
        "#ECB730", "#EB3424", "#5B8FFC",
        "#B08AFF", "#7DD99A", "#F5D060", "#C48A10"
    ],
}


def apply_design(fig, title=None):
    updates = dict(PLOTLY_LAYOUT)
    if title:
        updates["title_text"] = title
    fig.update_layout(**updates)
    fig.update_xaxes(
        gridcolor="#E5E5E5",
        linecolor="#D0D0D0",
        tickfont_color="#666666",
    )
    fig.update_yaxes(
        gridcolor="#E5E5E5",
        linecolor="#D0D0D0",
        tickfont_color="#666666",
    )
    return fig


def data_coverage_note(df_filtered, col):
    n     = df_filtered[col].notna().sum()
    total = len(df_filtered)
    return f"Data available for {n} of {total} companies"


def format_kpi(value, prefix="", suffix=""):
    import math
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "–"
    if math.isnan(v):
        return "–"
    if abs(v) >= 1e9:
        return f"{prefix}{v/1e9:.1f}B{(' ' + suffix) if suffix else ''}"
    if abs(v) >= 1e6:
        return f"{prefix}{v/1e6:.1f}M{(' ' + suffix) if suffix else ''}"
    if abs(v) >= 1e3:
        return f"{prefix}{v/1e3:.0f}K{(' ' + suffix) if suffix else ''}"
    return f"{prefix}{v:,.0f}{(' ' + suffix) if suffix else ''}"


GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }

/* ── Metric cards ─────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background:#FFFFFF; border:1px solid #E5E5E5; border-radius:10px;
    padding:16px 20px; box-shadow:0 1px 2px rgba(0,0,0,0.05);
    transition:box-shadow 0.2s; overflow:visible;
}
[data-testid="metric-container"]:hover { box-shadow:0 2px 8px rgba(0,0,0,0.08); }
[data-testid="metric-container"] label {
    font-size:11px !important; font-weight:600 !important;
    letter-spacing:0.06em !important; text-transform:uppercase !important;
    color:#666666 !important; white-space:nowrap !important;
}
[data-testid="stMetricValue"] {
    font-size:22px !important; font-weight:700 !important;
    color:#1A1A1A !important; white-space:nowrap !important;
    overflow:visible !important; line-height:1.2 !important;
}
[data-testid="stMetricDelta"] > div {
    font-size:11px !important; white-space:nowrap !important;
    overflow:visible !important;
}

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid #E5E5E5; }
[data-testid="stSidebar"] label { font-size:12px !important; font-weight:500 !important; color:#1A1A1A !important; }
/* Multiselect tag styling */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background:#EFF6FF !important; color:#1D4ED8 !important;
    border:1px solid #BFDBFE !important; border-radius:4px !important;
    font-size:11px !important;
}
/* Cap tag area height so it doesn't push other filters off screen */
[data-testid="stSidebar"] [data-baseweb="select"] > div:first-child {
    max-height:90px !important; overflow-y:auto !important;
}

/* ── Logo + nav ───────────────────────────────────────────────── */
#essen-logo { position:fixed !important; top:0 !important; left:0 !important; z-index:999 !important; background:#FFFFFF !important; padding:16px 20px 13px !important; border-bottom:1px solid #E5E5E5 !important; width:17rem !important; }
[data-testid="stSidebarNav"] { margin-top:74px !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background:#EFF6FF !important; border-left:3px solid #2563EB !important;
    font-weight:600 !important; color:#1D4ED8 !important;
}

/* ── Buttons ──────────────────────────────────────────────────── */
.stButton > button {
    background:#FFFFFF; color:#1A1A1A; border:1px solid #E5E5E5;
    border-radius:6px; font-family:Inter,sans-serif; font-size:12px;
    font-weight:500; padding:6px 10px; transition:all 0.15s;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.stButton > button:hover { background:#F7F7F7; border-color:#D0D0D0; box-shadow:0 1px 2px rgba(0,0,0,0.05); }
.stButton > button[kind="primary"] { background:#2563EB !important; color:#FFFFFF !important; border-color:#2563EB !important; }
.stButton > button[kind="primary"]:hover { background:#1D4ED8 !important; }

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid #E5E5E5; background:transparent; }
.stTabs [data-baseweb="tab"] { font-family:Inter,sans-serif; font-size:12px; font-weight:500; color:#666666; padding:8px 12px; border-radius:0; border-bottom:2px solid transparent; white-space:nowrap; }
.stTabs [aria-selected="true"] { color:#2563EB !important; border-bottom:2px solid #2563EB !important; background:transparent !important; }

/* ── Expanders ────────────────────────────────────────────────── */
.streamlit-expanderHeader { font-family:Inter,sans-serif; font-size:13px; font-weight:600; color:#1A1A1A; background:#FFFFFF; border:1px solid #E5E5E5; border-radius:6px; }

/* ── Misc ─────────────────────────────────────────────────────── */
hr { border-color:#E5E5E5; }
.stAlert { border-radius:6px; font-family:Inter,sans-serif; font-size:13px; }

/* ── Page header ──────────────────────────────────────────────── */
.page-header { padding-bottom:16px; border-bottom:1px solid #E5E5E5; margin-bottom:24px; }
.page-title { font-size:24px; font-weight:700; color:#1A1A1A; margin:0; letter-spacing:-0.5px; }
.page-subtitle { font-size:13px; color:#999999; margin-top:4px; font-weight:400; }

/* ── Cards & containers ───────────────────────────────────────── */
.insight-card { background:#FFFFFF; border:1px solid #E5E5E5; border-radius:10px; padding:16px 20px; box-shadow:0 1px 2px rgba(0,0,0,0.05); }
.insight-card-accent { background:#EFF6FF; border:1px solid #BFDBFE; border-radius:10px; padding:16px 20px; }
.chart-container { background:#FFFFFF; border:1px solid #E5E5E5; border-radius:10px; padding:20px; box-shadow:0 1px 2px rgba(0,0,0,0.05); }
</style>
"""


def inject_global_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
