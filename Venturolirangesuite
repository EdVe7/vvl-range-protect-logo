

"""
Zanardelli Range Suite — tracking allenamento (range, gioco corto, putting).
UI mobile-first, persistenza Google Sheets (stesse colonne e secrets dell'originale).
"""

from __future__ import annotations

import datetime
import time
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:  # pragma: no cover
    from streamlit_gsheets_connection import GSheetsConnection  # type: ignore

# =============================================================================
# Config pagina
# =============================================================================
APP_NAME = "Zanardelli Range Suite"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stDeployButton {{display:none;}}
    [data-testid="stToolbar"] {{visibility: hidden !important;}}
    .stApp {{background: linear-gradient(180deg, #FFFFFF 0%, #FFFBEF 75%, #F8EFCF 100%);}}
    </style>
    """, unsafe_allow_html=True)
    

BLACK = "#141414"
BLACK_SOFT = "#2A2A2A"
GOLD = "#C9A227"       # ocra
GOLD_LIGHT = "#E8D48A"
GOLD_DARK = "#7A5B12"
WHITE = "#FFFFFF"
OFF_WHITE = "#FFFCF7"
TEXT = "#1A1A1A"
MUTED = "#6B5B4A"
ACCENT_BLUE = "#5A8DEE"
ACCENT_BLUE_SOFT = "#EEF4FF"
SUCCESS_GREEN = "#17A673"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#F1DCC7"
ORANGE = "#F08A24"
ORANGE_SOFT = "#FFE7CF"
ORANGE_LIGHT = "#FFF1E3"

PASSWORD_DEFAULT = "supernova.analytics"

CATEGORIES = {
    "RANGE": "Gioco lungo / Range",
    "SHORT": "Gioco corto (<50 m)",
    "PUTT": "Putting",
}

# Schema colonne foglio (ordine stabile per concat/update)
DATA_COLUMNS = [
    "User",
    "Date",
    "SessionName",
    "Time",
    "Category",
    "Club",
    "Impact",
    "Curvature",
    "Trajectory",
    "Lie_Start",
    "Lie_End",
    "Direction_LR",
    "Proximity_Lateral_m",
    "Proximity_Depth_m",
    "Start_Dist_m",
    "End_Dist_m",
    "Hole_Dist_Start_m",
    "Hole_Dist_End_m",
    "Lie_Long",
    "Rating",
    "Mental_Reaction",
    "Strokes_Gained",
]

LONG_IMPACT = ["Centro", "Punta", "Tacco", "Shank", "Top", "Flappa"]
LONG_CURVE = ["Dritta", "Fade", "Draw", "Slice", "Hook", "Push", "Pull"]
LONG_DIR = ["Esattamente in linea", "A destra del bersaglio", "A sinistra del bersaglio"]

SHORT_IMPACT = ["Dritta", "Punta", "Tacco", "Shank", "Top", "Flappa"]
SHORT_LIE_START = [
    "Fairway",
    "First cut",
    "Rough",
    "Semi-rough",
    "Bunker",
    "Fringe",
    "Green",
    "Bare lie / Terra dura",
    "Pine straw",
]
SHORT_LIE_END = [
    "Fairway",
    "First cut",
    "Rough",
    "Semi-rough",
    "Bunker",
    "Fringe",
    "Green",
    "Fuori limite area target",
]
SHORT_DIR = ["Esattamente in linea", "A destra della buca", "A sinistra della buca"]

PUTT_IMPACT = ["Centro", "Punta", "Tacco", "Flappa"]
PUTT_TRAJ = ["Dritta", "Pull", "Push"]

MENTAL_OPTIONS = [
    "Molto negativa",
    "Negativa",
    "Neutra",
    "Positiva",
    "Molto positiva",
]

CLUBS_LONG = [
    "DR",
    "3W",
    "5W",
    "7W",
    "3H",
    "3i",
    "4i",
    "5i",
    "6i",
    "7i",
    "8i",
    "9i",
    "PW",
    "AW",
    "GW",
    "SW",
    "LW",
]
CLUBS_SHORT = ["LW", "SW", "GW", "AW", "PW", "9i", "8i", "7i"]

PERIOD_LABELS = [
    "Sessione corrente",
    "Ultimi 7 giorni",
    "Ultimo mese",
    "Ultimi 6 mesi",
    "Ultimo anno",
    "Lifelong",
]

# Griglie distanza — solo tap, passo 5 m (putting: passo fine)
DIST_5M_0_50 = [float(x) for x in range(0, 55, 5)]
DIST_5M_5_50 = [float(x) for x in range(5, 55, 5)]
DIST_5M_0_80 = [float(x) for x in range(0, 85, 5)]
DIST_5M_0_250 = [float(x) for x in range(0, 255, 5)]
DIST_5M_5_500 = [float(x) for x in range(5, 505, 5)]
DIST_LAT_SHORT = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0]
DIST_LAT_RANGE = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 80.0]
PUTT_START_DIST = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0]
PUTT_END_DIST = [0.0, 0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 8.0, 10.0, 15.0]
LIE_AFTER_RANGE = ["Fairway", "First cut", "Semi-rough", "Rough", "Bunker", "Fringe", "Green"]

CHART_PALETTE = [ORANGE, GOLD, BLACK_SOFT, ACCENT_BLUE, SUCCESS_GREEN, GOLD_DARK, "#D96E0A", "#8A6F55"]


def inject_styles() -> None:
    st.markdown(
        f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&family=IBM+Plex+Sans:wght@600;700&display=swap');
    #MainMenu {{visibility: hidden; height: 0;}}
    footer {{visibility: hidden; height: 0;}}
    header [data-testid="stHeader"] {{background: transparent;}}
    html, body, [class*="css"] {{
        font-family: 'Source Sans 3', 'Segoe UI', sans-serif;
        color: {TEXT};
    }}
    .stApp {{
        background:
            radial-gradient(ellipse 90% 40% at 100% 0%, {ORANGE_SOFT} 0%, transparent 55%),
            radial-gradient(ellipse 70% 35% at 0% 0%, {GOLD_LIGHT}33 0%, transparent 50%),
            linear-gradient(180deg, {OFF_WHITE} 0%, {WHITE} 45%, #FAF6EF 100%);
        color: {TEXT};
    }}
    .block-container {{
        padding-top: 0.6rem;
        padding-bottom: 4.5rem;
        max-width: 920px;
    }}
    h1, h2, h3 {{
        color: {BLACK};
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    h3 {{
        margin-top: 0.25rem;
    }}
    p, span, label {{
        color: {TEXT};
    }}
    [data-testid="stTabs"] button[role="tab"] {{
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        color: {MUTED} !important;
        border: 1px solid transparent !important;
        background: transparent !important;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: {TEXT} !important;
        border-color: #efc79e !important;
        background: {WHITE} !important;
        box-shadow: 0 6px 20px rgba(240, 138, 36, 0.18) !important;
    }}
    div[data-testid="stSelectbox"], div[data-testid="stTextInput"], div[data-testid="stNumberInput"] {{
        background: transparent;
    }}
    div[data-baseweb="select"] > div,
    .stTextInput input,
    .stNumberInput input {{
        border-radius: 10px !important;
        border: 1.5px solid #D4C4B0 !important;
        background: #fff !important;
        min-height: 3.1rem !important;
        font-size: 1.05rem !important;
        box-shadow: inset 0 1px 2px rgba(20,20,20,0.05) !important;
    }}
    .stTextInput input:focus,
    .stNumberInput input:focus {{
        border-color: {ORANGE} !important;
        box-shadow: 0 0 0 2px rgba(240, 138, 36, 0.18) !important;
    }}
    [data-testid="stMetric"] {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 8px 10px;
        box-shadow: 0 8px 20px rgba(240, 138, 36, 0.08);
    }}
    [data-testid="stMetricLabel"] {{
        color: {MUTED} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricValue"] {{
        color: {TEXT} !important;
        font-family: 'Manrope', sans-serif !important;
        font-weight: 800 !important;
    }}
    div[data-testid="stHorizontalBlock"] > div .stButton > button {{
        min-height: 4rem !important;
        font-size: 1.08rem !important;
        border-radius: 12px !important;
        border: 1.5px solid #D8D0C4 !important;
        background: linear-gradient(180deg, {WHITE} 0%, #FAF8F4 100%) !important;
        color: {BLACK} !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 0 #E8E0D4, 0 6px 16px rgba(20,20,20,0.07) !important;
        transition: transform 0.12s ease, box-shadow 0.12s ease !important;
    }}
    div[data-testid="stHorizontalBlock"] > div .stButton > button:hover {{
        border-color: {ORANGE} !important;
        color: #D96E0A !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 0 #E8E0D4, 0 10px 22px rgba(240,138,36,0.22) !important;
    }}
    .sn-big-btn > button {{
        width: 100%;
        min-height: 3.5rem;
        font-size: 1.05rem;
        border-radius: 16px;
        background: {WHITE};
        border: 1px solid #d7ddeb;
        font-weight: 700;
    }}
    .stButton > button[kind="primary"], .stDownloadButton > button {{
        min-height: 3.5rem !important;
        border-radius: 12px !important;
        border: 0 !important;
        color: #fff !important;
        font-weight: 700 !important;
        background: linear-gradient(180deg, {ORANGE} 0%, #D96E0A 100%) !important;
        box-shadow: 0 3px 0 {GOLD_DARK}, 0 10px 24px rgba(240,138,36,0.32) !important;
    }}
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {{
        filter: brightness(1.04);
        transform: translateY(-1px);
    }}
    .stRadio > div {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 8px 10px;
        box-shadow: 0 4px 14px rgba(28,40,64,0.05);
    }}
    .stCaption {{
        color: {MUTED} !important;
    }}
    .sn-footer {{
        text-align: center;
        color: #9A9A9A;
        font-size: 0.84rem;
        margin-top: 2rem;
        padding: 0.9rem;
        border-top: 1px solid #E0E0E0;
        line-height: 1.6;
    }}
    .sn-footer strong {{
        color: #888888;
        font-weight: 600;
    }}
    .sn-footer a {{
        color: #9A9A9A !important;
    }}
    .sn-logo-caption {{
        font-style: italic;
        color: {MUTED};
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0;
    }}
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #fff7ef, #fffefc);
        border-right: 1px solid #e8ecf3;
    }}
    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {{
        color: {TEXT} !important;
    }}
    [data-testid="stSidebar"] div[data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stTextInput input {{
        background: #fff !important;
        color: {TEXT} !important;
    }}
    [data-testid="stSidebar"] .block-container {{
        padding-top: 1rem;
    }}
    .sn-hero {{
        background: linear-gradient(135deg, {WHITE} 0%, {ORANGE_LIGHT} 100%);
        border: 1.5px solid {CARD_BORDER};
        border-left: 5px solid {ORANGE};
        border-radius: 14px;
        padding: 16px 18px;
        margin: 8px 0 16px 0;
        box-shadow: 0 8px 24px rgba(20,20,20,0.08);
    }}
    .sn-hero-title {{
        font-size: 1.08rem;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 4px;
    }}
    .sn-hero-sub {{
        color: {MUTED};
        font-size: 0.9rem;
        margin: 0;
    }}
    .sn-chip {{
        display: inline-block;
        background: {BLACK};
        color: {WHITE};
        border-radius: 6px;
        padding: 5px 11px;
        margin-right: 6px;
        margin-top: 8px;
        font-size: 0.78rem;
        font-weight: 700;
    }}
    .sn-chip-alt {{
        background: {GOLD};
        color: {BLACK};
    }}
    .sn-panel {{
        background: {CARD_BG};
        border: 1.5px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 14px;
        box-shadow: 0 6px 20px rgba(20,20,20,0.06);
    }}
    .zrs-dist-grid .stButton > button {{
        min-height: 2.75rem !important;
        font-size: 0.88rem !important;
        padding: 2px 4px !important;
    }}
    .zrs-chart-box {{
        background: {CARD_BG};
        border: 1.5px solid {CARD_BORDER};
        border-radius: 12px;
        padding: 12px 14px 4px 14px;
        margin: 10px 0 16px 0;
        box-shadow: 0 4px 16px rgba(20,20,20,0.05);
    }}
    .zrs-chart-caption {{
        color: {MUTED};
        font-size: 0.84rem;
        margin: 0 0 8px 0;
        border-left: 3px solid {ORANGE};
        padding-left: 10px;
    }}
    .sn-panel-title {{
        font-family: 'Manrope', sans-serif;
        font-size: 0.98rem;
        color: {TEXT};
        font-weight: 800;
        margin-bottom: 2px;
    }}
    .sn-panel-sub {{
        color: {MUTED};
        font-size: 0.86rem;
        margin: 0;
    }}
</style>
""",
        unsafe_allow_html=True,
    )


def brand_header(title: str | None = None) -> None:
    c1, c2 = st.columns([1, 3])
    with c1:
        try:
            st.image("logo.png", use_container_width=True)
        except Exception:
            st.markdown(
                f"<div style='font-size:1.6rem;font-weight:800;color:{GOLD};'>{APP_NAME}</div>",
                unsafe_allow_html=True,
            )
    with c2:
        if title:
            st.markdown(f"### {title}")
        st.markdown(
            "<p class='sn-logo-caption'>Range Data Suite · Data over talent</p>",
            unsafe_allow_html=True,
        )


def brand_footer() -> None:
    st.markdown(
        (
            "<div class='sn-footer'>"
            f"© {datetime.date.today().year} Andrea Zanardelli · "
            "Co-designed by Andrea Zanardelli and Edoardo Venturoli<br>"
            '<a href="https://www.zanardelligolf.com" target="_blank">www.zanardelligolf.com</a>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str, chips: list[str] | None = None) -> None:
    chips_html = ""
    if chips:
        for i, c in enumerate(chips):
            cls = "sn-chip sn-chip-alt" if i % 2 else "sn-chip"
            chips_html += f"<span class='{cls}'>{c}</span>"
    st.markdown(
        (
            "<div class='sn-hero'>"
            f"<div class='sn-hero-title'>{title}</div>"
            f"<p class='sn-hero-sub'>{subtitle}</p>"
            f"{chips_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_panel(title: str, subtitle: str) -> None:
    st.markdown(
        (
            "<div class='sn-panel'>"
            f"<div class='sn-panel-title'>{title}</div>"
            f"<p class='sn-panel-sub'>{subtitle}</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_command_header(page: str) -> None:
    st.markdown(
        (
            "<div class='sn-panel'>"
            f"<div class='sn-panel-title'>{APP_NAME} — Command Center</div>"
            f"<p class='sn-panel-sub'>Sezione attiva: <b>{page}</b> · "
            "UI ottimizzata per lettura rapida coach-atleta in campo.</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def help_icon(text: str) -> None:
    with st.popover("❓"):
        st.markdown(text)


def section_heading(title: str, help_text: str | None = None) -> None:
    c1, c2 = st.columns([11, 1])
    with c1:
        st.markdown(f"#### {title}")
    with c2:
        if help_text:
            help_icon(help_text)


def eng_chart_layout(fig: go.Figure, title: str, xlab: str = "", ylab: str = "") -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=BLACK)),
        font=dict(family="Source Sans 3", size=12, color=TEXT),
        paper_bgcolor=OFF_WHITE,
        plot_bgcolor=WHITE,
        margin=dict(t=52, b=44, l=52, r=28),
        legend=dict(
            title=dict(text="Legenda"),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=CARD_BORDER,
            borderwidth=1,
        ),
        xaxis=dict(title=xlab, gridcolor="#E8E0D4", zerolinecolor=GOLD, linecolor="#D4C4B0"),
        yaxis=dict(title=ylab, gridcolor="#E8E0D4", zerolinecolor=GOLD, linecolor="#D4C4B0"),
    )
    return fig


def chart_block(caption: str) -> None:
    st.markdown(f"<p class='zrs-chart-caption'>{caption}</p>", unsafe_allow_html=True)


def tap_grid(
    options: list[Any],
    key_prefix: str,
    cols_n: int,
    shot: dict[str, Any],
    field: str,
    next_step: int,
    fmt: str | None = None,
) -> None:
    """Un tap = scelta + avanzamento step. Nessun input manuale."""
    st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
    cols = st.columns(cols_n)
    for i, opt in enumerate(options):
        if fmt == "m":
            label = f"{float(opt):g} m"
        else:
            label = str(opt)
        if cols[i % cols_n].button(label, key=f"{key_prefix}_{i}", use_container_width=True):
            shot[field] = float(opt) if isinstance(opt, (int, float)) and fmt == "m" else opt
            st.session_state["wz_step"] = next_step
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def tap_grid_action(
    options: list[Any],
    key_prefix: str,
    cols_n: int,
    on_pick: Any,
) -> None:
    st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
    cols = st.columns(cols_n)
    for i, opt in enumerate(options):
        label = f"{float(opt):g} m" if isinstance(opt, float) and opt != int(opt) else (
            f"{int(opt)} m" if isinstance(opt, (int, float)) else str(opt)
        )
        if cols[i % cols_n].button(label, key=f"{key_prefix}_{i}", use_container_width=True):
            on_pick(opt)
            return
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# Strokes gained (modello semplificato da practice — coerente tra settori)
# =============================================================================
def _interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]


def expected_putts(distance_m: float) -> float:
    """Colpi attesi PGA-style (approssimazione) da distanza in metri."""
    if distance_m <= 0:
        return 0.0
    xs = [0.5, 1, 1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30]
    ys = [1.02, 1.06, 1.10, 1.15, 1.23, 1.30, 1.38, 1.45, 1.58, 1.72, 1.85, 2.05, 2.25, 2.42, 2.55]
    return float(_interp(distance_m, xs, ys))


def expected_short_hole(dist_m: float, lie: str) -> float:
    """Colpi attesi fino alla buca dal gioco corto (non green)."""
    if dist_m <= 0:
        return 0.0
    lie_adj = {
        "Fairway": 0.0,
        "First cut": 0.10,
        "Semi-rough": 0.14,
        "Rough": 0.20,
        "Bunker": 0.55,
        "Fringe": 0.05,
        "Green": 0.0,
        "Bare lie / Terra dura": 0.12,
        "Pine straw": 0.18,
        "Fuori limite area target": 0.30,
    }
    base = 2.08 + (dist_m / 45.0) * 0.95
    return float(base + lie_adj.get(lie, 0.0))


def expected_long_hole(dist_m: float, from_tee: bool) -> float:
    """Approccio / tee: colpi attesi verso la buca prima/dopo il colpo."""
    if dist_m <= 0:
        return 0.0
    if from_tee:
        xs = [120, 160, 200, 240, 280, 320, 380, 440]
        ys = [3.05, 3.25, 3.45, 3.62, 3.78, 3.92, 4.08, 4.22]
        return float(_interp(dist_m, xs, ys))
    xs = [30, 60, 90, 120, 150, 180, 210]
    ys = [2.35, 2.72, 3.02, 3.28, 3.48, 3.65, 3.78]
    return float(_interp(dist_m, xs, ys))


def compute_sg_putt(start_m: float, end_m: float) -> float:
    exp_before = expected_putts(start_m)
    exp_after = expected_putts(end_m)
    return float(exp_before - exp_after - 1.0)


def compute_sg_short(start_m: float, end_m: float, lie_s: str, lie_e: str) -> float:
    def exp_at(d: float, lie: str) -> float:
        if lie == "Green":
            return expected_putts(d)
        return expected_short_hole(d, lie)

    exp_before = exp_at(start_m, lie_s)
    exp_after = exp_at(end_m, lie_e)
    return float(exp_before - exp_after - 1.0)


def compute_sg_long(start_before_m: float, start_after_m: float, from_tee: bool, lie_after: str) -> float:
    exp_before = expected_long_hole(start_before_m, from_tee)
    use_fairway = lie_after.lower() == "fairway"
    exp_after = expected_long_hole(start_after_m, from_tee=False) if use_fairway else expected_short_hole(start_after_m, lie_after)
    return float(exp_before - exp_after - 1.0)


# =============================================================================
# Dati
# =============================================================================
@st.cache_data(ttl=10)
def load_data() -> pd.DataFrame:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame(columns=DATA_COLUMNS)
        for c in DATA_COLUMNS:
            if c not in df.columns:
                df[c] = np.nan
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        for num in [
            "Proximity_Lateral_m",
            "Proximity_Depth_m",
            "Start_Dist_m",
            "End_Dist_m",
            "Hole_Dist_Start_m",
            "Hole_Dist_End_m",
            "Rating",
            "Strokes_Gained",
        ]:
            df[num] = pd.to_numeric(df[num], errors="coerce")
        return df[DATA_COLUMNS]
    except Exception:
        return pd.DataFrame(columns=DATA_COLUMNS)


def align_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in DATA_COLUMNS:
        if c not in out.columns:
            out[c] = np.nan
    return out[DATA_COLUMNS]


def save_shot(row: dict[str, Any]) -> None:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing = load_data()
    new = pd.DataFrame([row])
    merged = align_dataframe(pd.concat([existing, new], ignore_index=True))
    conn.update(data=merged)
    st.cache_data.clear()


# =============================================================================
# Splash & login
# =============================================================================
def run_splash_sequence() -> None:
    holder = st.empty()
    with holder.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        cc1, cc2, cc3 = st.columns([1, 3, 1])
        with cc2:
            try:
                st.image("logo.png", use_container_width=True)
            except Exception:
                st.markdown(
                    f"<h1 style='text-align:center;color:{GOLD};'>SUPERNOVA</h1>",
                    unsafe_allow_html=True,
                )
    time.sleep(3.0)
    holder.empty()


def login_screen() -> None:
    brand_header("Accesso")
    st.caption("Inserisci le credenziali per salvare i tuoi colpi sul foglio collegato.")
    u = st.text_input("Username / ID atleta", key="login_user").strip()
    p = st.text_input("Password", type="password", key="login_pass")
    privacy = st.checkbox(
        "Ho letto e accetto l'informativa privacy e il trattamento dei dati.",
        key="privacy_ok",
    )
    if st.button("Entra nella suite", type="primary", use_container_width=True):
        if not privacy:
            st.error("È necessario accettare la privacy policy.")
            return
        if not u:
            st.error("Inserisci uno username.")
            return
        pwd_ok = p == PASSWORD_DEFAULT
        env_p = None
        try:
            env_p = st.secrets.get("APP_PASSWORD")
        except Exception:
            env_p = None
        if env_p:
            pwd_ok = pwd_ok or (p == str(env_p))
        if pwd_ok:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u.upper()
            st.session_state["post_auth_logo_pending"] = True
            st.rerun()
        else:
            st.error("Credenziali non valide.")
    brand_footer()
    st.stop()


def run_post_auth_logo() -> None:
    holder = st.empty()
    with holder.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 3, 1])
        with c2:
            try:
                st.image("logo.png", use_container_width=True)
            except Exception:
                st.markdown(
                    f"<h1 style='text-align:center;color:{GOLD};'>{APP_NAME}</h1>",
                    unsafe_allow_html=True,
                )
    time.sleep(2.0)
    holder.empty()


# =============================================================================
# Helpers UI wizard
# =============================================================================
def reset_wizard() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith("wz_"):
            del st.session_state[k]
    st.session_state["wz_cat"] = None
    st.session_state["wz_step"] = 0


def lat_sign(direction: str, lateral_abs: float) -> float:
    if direction.startswith("A destra"):
        return float(abs(lateral_abs))
    if direction.startswith("A sinistra"):
        return -float(abs(lateral_abs))
    return 0.0


def depth_sign(depth_m: float, label: str) -> float:
    """Profondità: positivo = lungo, negativo = corto (optional convention)."""
    if label == "Corto del bersaglio":
        return -abs(depth_m)
    if label == "Lungo del bersaglio":
        return abs(depth_m)
    return 0.0


def filter_period(df: pd.DataFrame, session_name: str, period: str) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    today = datetime.date.today()
    if period == "Sessione corrente":
        return d[d["SessionName"] == session_name]
    if period == "Ultimi 7 giorni":
        return d[d["Date"] >= today - datetime.timedelta(days=7)]
    if period == "Ultimo mese":
        return d[d["Date"] >= today - datetime.timedelta(days=30)]
    if period == "Ultimi 6 mesi":
        return d[d["Date"] >= today - datetime.timedelta(days=182)]
    if period == "Ultimo anno":
        return d[d["Date"] >= today - datetime.timedelta(days=365)]
    return d


def plot_pie(df: pd.DataFrame, column: str, title: str, legend_help: str) -> None:
    if df.empty or column not in df.columns:
        st.info("Nessun dato per questo grafico.")
        return
    if column == "Rating":
        s = pd.to_numeric(df[column], errors="coerce").dropna().astype(int).astype(str)
    else:
        s = df[column].astype(str)
    s = s.replace("nan", "(vuoto)").replace("", "(vuoto)")
    vc = s.value_counts()
    if vc.empty:
        st.info("Nessuna categoria disponibile.")
        return
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block(legend_help)
    fig = px.pie(
        values=vc.values,
        names=vc.index,
        title=title,
        hole=0.38,
        color_discrete_sequence=CHART_PALETTE,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    eng_chart_layout(fig, title)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def plot_dispersion(df: pd.DataFrame, title: str) -> None:
    if df.empty:
        return
    d = df.copy()
    d["x_lateral_m"] = pd.to_numeric(d["Proximity_Lateral_m"], errors="coerce")
    d["y_depth_m"] = pd.to_numeric(d["Proximity_Depth_m"], errors="coerce")
    d = d.dropna(subset=["x_lateral_m", "y_depth_m"])
    if d.empty:
        st.info("Aggiungi errore laterale e profondità per vedere la dispersione dall'alto.")
        return
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block(
        "Vista planimetrica: incrocio assi = bersaglio/buca. "
        "Asse X = errore laterale (m); asse Y = errore profondità (m). Colore = bastone."
    )
    fig = px.scatter(
        d,
        x="x_lateral_m",
        y="y_depth_m",
        color="Club",
        hover_data=["Impact", "Rating", "Date"],
        title=title,
        labels={
            "x_lateral_m": "Laterale (m): sin ← 0 → des",
            "y_depth_m": "Profondità (m): corto ← 0 → lungo",
        },
        color_discrete_sequence=CHART_PALETTE,
    )
    fig.add_vline(x=0, line_dash="dash", line_color=GOLD, line_width=2)
    fig.add_hline(y=0, line_dash="dash", line_color=GOLD, line_width=2)
    eng_chart_layout(fig, title, "Errore laterale (m)", "Errore profondità (m)")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def putting_make_table(df_putt: pd.DataFrame) -> None:
    """Bucket da 15 m in giù ogni 2 m."""
    if df_putt.empty:
        st.info("Nessun putt nel periodo.")
        return
    d = df_putt.copy()
    d["sd"] = pd.to_numeric(d["Start_Dist_m"], errors="coerce")
    d["ed"] = pd.to_numeric(d["End_Dist_m"], errors="coerce")
    d = d.dropna(subset=["sd"])
    rows = []
    for hi in range(15, 0, -2):
        lo = max(hi - 2, 0)
        sub = d[(d["sd"] > lo) & (d["sd"] <= hi)]
        n = len(sub)
        made = int((sub["ed"].fillna(999) <= 0).sum())
        pct = (made / n * 100.0) if n else 0.0
        rows.append({"Fascia di partenza": f"{lo}–{hi} m", "Putt": n, "Realizzati": made, "% Made": pct})
    out = pd.DataFrame(rows)
    st.markdown("#### Tabella realizzazione putt per distanza di partenza")
    st.caption(
        "Percentuale di putt chiusi in buca al primo tentativo (distanza finale = 0 m), "
        "raggruppati per ampiezza di 2 metri fino a 15 m."
    )
    st.dataframe(
        out.style.format({"% Made": "{:.1f}%"}),
        use_container_width=True,
        hide_index=True,
    )


def sg_summary_table(df: pd.DataFrame, cat_key: str) -> None:
    sub = df[df["Category"] == cat_key]
    if sub.empty:
        st.info("Nessuno strokes gained: dati assenti per questo settore.")
        return
    sg = pd.to_numeric(sub["Strokes_Gained"], errors="coerce").dropna()
    if sg.empty:
        st.info("Colonna strokes gained vuota per questo periodo.")
        return
    st.markdown("#### Riepilogo Strokes Gained (modello practice)")
    st.caption(
        "Valori positivi indicano un colpo migliore della media di riferimento usata dal modello "
        "(approssimazione didattica, non ufficiale PGA)."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Media SG", f"{sg.mean():+.3f}")
    c2.metric("Totale SG", f"{sg.sum():+.3f}")
    c3.metric("Colpi", f"{len(sg)}")
    c4.metric("Migliore", f"{sg.max():+.3f}")
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block(
        "Istogramma della distribuzione SG per colpo. "
        "Barre a destra dello zero = colpi sopra il benchmark del modello practice."
    )
    hist = px.histogram(
        sg,
        nbins=20,
        title="Distribuzione SG colpo per colpo",
        labels={"value": "Strokes gained per colpo", "count": "Numero di colpi"},
        color_discrete_sequence=[ORANGE],
    )
    hist.add_vline(x=0, line_dash="dash", line_color=BLACK_SOFT)
    eng_chart_layout(hist, "Distribuzione SG colpo per colpo", "SG per colpo", "Frequenza")
    hist.update_layout(showlegend=False)
    st.plotly_chart(hist, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def satisfaction_breakdown(df: pd.DataFrame, cat_key: str) -> None:
    sub = df[df["Category"] == cat_key]
    if sub.empty:
        return
    plot_pie(
        sub,
        "Rating",
        "Distribuzione voto colpo (1–5)",
        "Legenda: percentuale di colpi per ogni voto di qualità auto-valutata.",
    )
    plot_pie(
        sub,
        "Mental_Reaction",
        "Reazione mentale",
        "Legenda: mix delle reazioni emotive/cognitive dichiarate dopo il colpo.",
    )


def trend_panel(df_sector: pd.DataFrame, sector_label: str) -> None:
    if df_sector.empty:
        return
    d = df_sector.copy()
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    d = d.dropna(subset=["Date"])
    if d.empty:
        return
    d["Rating"] = pd.to_numeric(d["Rating"], errors="coerce")
    d["Strokes_Gained"] = pd.to_numeric(d["Strokes_Gained"], errors="coerce")
    grp = (
        d.groupby("Date", as_index=False)
        .agg(
            rating_mean=("Rating", "mean"),
            sg_mean=("Strokes_Gained", "mean"),
            shots=("Category", "count"),
        )
        .sort_values("Date")
    )
    grp["Day"] = grp["Date"].dt.strftime("%d/%m/%Y")
    st.markdown("#### Trend giornaliero")
    st.caption(
        "Linea oro = voto medio; linea scura = strokes gained medio per giorno. "
        "Serve a capire se la qualità sale o scende nel tempo."
    )
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block(
        "Andamento giornaliero: linea ocra = voto medio (1–5); linea scura = SG medio. "
        "Due assi Y per confrontare qualità percepita ed efficienza statistica."
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=grp["Date"],
            y=grp["rating_mean"],
            mode="lines+markers",
            name="Voto medio",
            line=dict(color=GOLD, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=grp["Date"],
            y=grp["sg_mean"],
            mode="lines+markers",
            name="SG medio",
            line=dict(color="#5c4a12", width=2),
            yaxis="y2",
        )
    )
    eng_chart_layout(
        fig,
        f"Andamento performance — {sector_label}",
        "Giorno",
        "Voto medio (1-5)",
    )
    fig.update_layout(
        yaxis2=dict(title="SG medio", overlaying="y", side="right", gridcolor="#E8E0D4"),
    )
    fig.update_xaxes(tickformat="%d/%m/%Y", hoverformat="%d/%m/%Y")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def club_breakdown_table(df_sector: pd.DataFrame) -> None:
    d = df_sector.copy()
    if d.empty:
        return
    d["Rating"] = pd.to_numeric(d["Rating"], errors="coerce")
    d["Strokes_Gained"] = pd.to_numeric(d["Strokes_Gained"], errors="coerce")
    g = (
        d.groupby("Club", as_index=False)
        .agg(
            Colpi=("Club", "count"),
            Voto_medio=("Rating", "mean"),
            SG_medio=("Strokes_Gained", "mean"),
        )
        .sort_values(["Colpi", "Voto_medio"], ascending=[False, False])
    )
    if g.empty:
        return
    st.markdown("#### Ranking bastoni (nel filtro scelto)")
    st.caption(
        "Tabella sintetica per bastone: volume, voto medio e strokes gained medio."
    )
    st.dataframe(
        g.style.format({"Voto_medio": "{:.2f}", "SG_medio": "{:+.3f}"}),
        use_container_width=True,
        hide_index=True,
    )


def sg_distance_table(df_sector: pd.DataFrame) -> None:
    d = df_sector.copy()
    d["Start_Dist_m"] = pd.to_numeric(d["Start_Dist_m"], errors="coerce")
    d["Strokes_Gained"] = pd.to_numeric(d["Strokes_Gained"], errors="coerce")
    d = d.dropna(subset=["Start_Dist_m", "Strokes_Gained"])
    if d.empty:
        return
    bins = [0, 2, 5, 10, 20, 35, 50, 80, 130, 200, 600]
    labels = ["0-2", "2-5", "5-10", "10-20", "20-35", "35-50", "50-80", "80-130", "130-200", "200+"]
    d["Distance_Bucket"] = pd.cut(d["Start_Dist_m"], bins=bins, labels=labels, include_lowest=True, right=False)
    g = (
        d.groupby("Distance_Bucket", as_index=False)
        .agg(Colpi=("Strokes_Gained", "count"), SG_medio=("Strokes_Gained", "mean"))
        .dropna()
    )
    if g.empty:
        return
    st.markdown("#### Strokes gained per fascia distanza")
    st.caption("Aiuta a capire in quali distanze perdi o guadagni colpi rispetto al benchmark usato.")
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block("SG medio per fascia di distanza iniziale. Verde = guadagno; rosso = perdita vs benchmark.")
    fig = px.bar(
        g,
        x="Distance_Bucket",
        y="SG_medio",
        color="SG_medio",
        color_continuous_scale="RdYlGn",
        labels={"Distance_Bucket": "Fascia metri", "SG_medio": "SG medio"},
        title="Efficienza SG per distanza iniziale",
    )
    fig.add_hline(y=0, line_dash="dash", line_color=BLACK_SOFT, line_width=2)
    eng_chart_layout(fig, "Efficienza SG per distanza iniziale", "Fascia metri", "SG medio")
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(g.style.format({"SG_medio": "{:+.3f}"}), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def directional_bias_panel(df_sector: pd.DataFrame) -> None:
    d = df_sector.copy()
    d["x"] = pd.to_numeric(d["Proximity_Lateral_m"], errors="coerce")
    d = d.dropna(subset=["x"])
    if d.empty:
        return
    left = int((d["x"] < 0).sum())
    right = int((d["x"] > 0).sum())
    center = int((d["x"] == 0).sum())
    total = len(d)
    st.markdown("#### Directional bias")
    st.caption("Distribuzione colpi a sinistra/destra/centrali rispetto alla linea target.")
    bias = pd.DataFrame(
        {
            "Direzione": ["Sinistra", "In linea", "Destra"],
            "Colpi": [left, center, right],
            "Percentuale": [left / total * 100, center / total * 100, right / total * 100],
        }
    )
    st.markdown("<div class='zrs-chart-box'>", unsafe_allow_html=True)
    chart_block("Percentuale colpi a sinistra, in linea o a destra rispetto al target.")
    fig = px.bar(
        bias,
        x="Direzione",
        y="Percentuale",
        text=bias["Percentuale"].map(lambda v: f"{v:.1f}%"),
        color="Direzione",
        color_discrete_map={"Sinistra": "#d45858", "In linea": SUCCESS_GREEN, "Destra": ACCENT_BLUE},
        title="Bias laterale medio",
    )
    eng_chart_layout(fig, "Bias laterale medio", "Direzione", "% colpi")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# Wizard inserimento colpo — solo tap, nessun input manuale
# =============================================================================
def _save_and_reset(row: dict[str, Any], msg: str) -> None:
    save_shot(row)
    st.success(msg)
    reset_wizard()
    st.rerun()


def wizard_range(session_name: str, user: str) -> None:
    st.session_state.setdefault("wz_step", 0)
    step = st.session_state["wz_step"]
    shot: dict[str, Any] = st.session_state.setdefault("wz_payload", {})

    if step == 0:
        section_heading("Bastone", "Tap sul bastone usato. Griglia ampia per scelta rapida.")
        tap_grid(CLUBS_LONG, "cl", 6, shot, "Club", 1)
    elif step == 1:
        section_heading("Impatto", "Zona di contatto dichiarata sul colpo.")
        tap_grid(LONG_IMPACT, "im", 3, shot, "Impact", 2)
    elif step == 2:
        section_heading("Curvatura", "Forma di volo della palla.")
        cols = st.columns(3)
        for i, opt in enumerate(LONG_CURVE):
            if cols[i % 3].button(opt, key=f"cv{i}", use_container_width=True):
                shot["Curvature"] = opt
                shot["Trajectory"] = ""
                st.session_state["wz_step"] = 3
                st.rerun()
    elif step == 3:
        section_heading("Direzione vs bersaglio", "Posizione rispetto alla linea di punteria.")
        tap_grid(LONG_DIR, "dir", 1, shot, "Direction_LR", 4)
    elif step == 4:
        section_heading("Errore laterale (m)", "Metri assoluti a destra/sinistra. Il segno segue la direzione scelta.")
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(6)
        for i, val in enumerate(DIST_LAT_RANGE):
            if cols[i % 6].button(f"{val:g} m", key=f"rlat{i}", use_container_width=True):
                shot["Proximity_Lateral_m"] = lat_sign(str(shot.get("Direction_LR", "")), val)
                st.session_state["wz_step"] = 5
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 5:
        section_heading("Profondità — senso", "In linea, corto o lungo rispetto al bersaglio.")
        for i, opt in enumerate(["In linea col bersaglio", "Corto del bersaglio", "Lungo del bersaglio"]):
            if st.button(opt, key=f"rds{i}", use_container_width=True):
                shot["_depth_sense"] = opt
                st.session_state["wz_step"] = 6
                st.rerun()
    elif step == 6:
        section_heading("Profondità — metri", "Tap sui metri di errore in profondità.")
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(6)
        for i, val in enumerate(DIST_LAT_RANGE):
            if cols[i % 6].button(f"{val:g} m", key=f"rdp{i}", use_container_width=True):
                shot["Proximity_Depth_m"] = depth_sign(val, str(shot.get("_depth_sense", "In linea col bersaglio")))
                st.session_state["wz_step"] = 7
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 7:
        section_heading("Voto colpo (1–5)", "Autovalutazione qualità esecuzione.")
        cols = st.columns(5)
        for v in range(1, 6):
            if cols[v - 1].button(str(v), key=f"rrt{v}", use_container_width=True):
                shot["Rating"] = v
                st.session_state["wz_step"] = 8
                st.rerun()
    elif step == 8:
        section_heading("Reazione mentale", "Come ti sei sentito subito dopo il colpo.")
        tap_grid(MENTAL_OPTIONS, "rmn", 2, shot, "Mental_Reaction", 9)
    elif step == 9:
        section_heading("Lie di partenza", "Tee o fairway per il modello SG.")
        c1, c2 = st.columns(2)
        for i, opt in enumerate(["Tee", "Fairway"]):
            if (c1 if i == 0 else c2).button(opt, key=f"rlie{i}", use_container_width=True):
                shot["Lie_Long"] = opt
                st.session_state["wz_step"] = 10
                st.rerun()
    elif step == 10:
        section_heading("Distanza dalla buca PRIMA del colpo", "Griglia ogni 5 m — tap per selezionare.")
        tap_grid(DIST_5M_5_500, "rhss", 6, shot, "Hole_Dist_Start_m", 11, fmt="m")
    elif step == 11:
        section_heading("Distanza dalla buca DOPO il colpo", "Griglia ogni 5 m — tap per selezionare.")
        tap_grid(DIST_5M_0_250, "rhse", 6, shot, "Hole_Dist_End_m", 12, fmt="m")
    elif step == 12:
        section_heading("Lie dopo il colpo", "Tap per salvare — ultimo passo.")
        cols = st.columns(3)
        for i, opt in enumerate(LIE_AFTER_RANGE):
            if cols[i % 3].button(opt, key=f"rla{i}", use_container_width=True):
                hole_start = float(shot["Hole_Dist_Start_m"])
                hole_end = float(shot["Hole_Dist_End_m"])
                from_tee = shot.get("Lie_Long") == "Tee"
                sg = compute_sg_long(hole_start, hole_end, from_tee, opt)
                _save_and_reset(
                    {
                        "User": user,
                        "Date": datetime.date.today(),
                        "SessionName": session_name,
                        "Time": datetime.datetime.now().strftime("%H:%M"),
                        "Category": "RANGE",
                        "Club": shot.get("Club", ""),
                        "Impact": shot.get("Impact", ""),
                        "Curvature": shot.get("Curvature", ""),
                        "Trajectory": "",
                        "Lie_Start": shot.get("Lie_Long", ""),
                        "Lie_End": opt,
                        "Direction_LR": shot.get("Direction_LR", ""),
                        "Proximity_Lateral_m": shot.get("Proximity_Lateral_m", np.nan),
                        "Proximity_Depth_m": shot.get("Proximity_Depth_m", np.nan),
                        "Start_Dist_m": hole_start,
                        "End_Dist_m": hole_end,
                        "Hole_Dist_Start_m": hole_start,
                        "Hole_Dist_End_m": hole_end,
                        "Lie_Long": shot.get("Lie_Long", ""),
                        "Rating": shot.get("Rating", np.nan),
                        "Mental_Reaction": shot.get("Mental_Reaction", ""),
                        "Strokes_Gained": sg,
                    },
                    "Colpo RANGE salvato.",
                )
    if st.button("Annulla inserimento", key="cancel_r"):
        reset_wizard()
        st.rerun()


def wizard_short(session_name: str, user: str) -> None:
    st.session_state.setdefault("wz_step", 0)
    step = st.session_state["wz_step"]
    shot: dict[str, Any] = st.session_state.setdefault("wz_payload", {})

    if step == 0:
        section_heading("Bastone", "Tap sul wedge/ferro usato.")
        tap_grid(CLUBS_SHORT, "scl", 4, shot, "Club", 1)
    elif step == 1:
        section_heading("Distanza iniziale dalla buca", "Ogni 5 m — tap per avanzare.")
        tap_grid(DIST_5M_5_50, "sds", 6, shot, "Start_Dist_m", 2, fmt="m")
    elif step == 2:
        section_heading("Lie iniziale", "Da dove parte la palla.")
        tap_grid(SHORT_LIE_START, "sls", 3, shot, "Lie_Start", 3)
    elif step == 3:
        section_heading("Distanza finale dalla buca", "Ogni 5 m — 0 = in buca.")
        tap_grid(DIST_5M_0_80, "sde", 6, shot, "End_Dist_m", 4, fmt="m")
    elif step == 4:
        section_heading("Lie finale", "Dove finisce la palla.")
        tap_grid(SHORT_LIE_END, "sle", 3, shot, "Lie_End", 5)
    elif step == 5:
        section_heading("Impatto", "Qualità di contatto.")
        cols = st.columns(3)
        for i, opt in enumerate(SHORT_IMPACT):
            if cols[i % 3].button(opt, key=f"sim{i}", use_container_width=True):
                shot["Impact"] = opt
                shot["Curvature"] = ""
                st.session_state["wz_step"] = 6
                st.rerun()
    elif step == 6:
        section_heading("Direzione vs buca", "Linea rispetto alla bandiera.")
        tap_grid(SHORT_DIR, "sdir", 1, shot, "Direction_LR", 7)
    elif step == 7:
        section_heading("Errore laterale (m)", "Metri assoluti dx/sx dalla buca.")
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(6)
        for i, val in enumerate(DIST_LAT_SHORT):
            if cols[i % 6].button(f"{val:g} m", key=f"slat{i}", use_container_width=True):
                shot["Proximity_Lateral_m"] = lat_sign(str(shot.get("Direction_LR", "")), val)
                st.session_state["wz_step"] = 8
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 8:
        section_heading("Profondità — senso", "Corto, lungo o in linea.")
        for i, opt in enumerate(["In linea", "Corto", "Lungo"]):
            if st.button(opt, key=f"sdsn{i}", use_container_width=True):
                shot["_depth_sense"] = opt
                st.session_state["wz_step"] = 9
                st.rerun()
    elif step == 9:
        section_heading("Profondità — metri", "Tap metri corto/lungo.")
        conv = {"In linea": "In linea col bersaglio", "Corto": "Corto del bersaglio", "Lungo": "Lungo del bersaglio"}
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(6)
        for i, val in enumerate(DIST_LAT_SHORT):
            if cols[i % 6].button(f"{val:g} m", key=f"sdp{i}", use_container_width=True):
                sense = conv.get(str(shot.get("_depth_sense", "In linea")), "In linea col bersaglio")
                shot["Proximity_Depth_m"] = depth_sign(val, sense)
                st.session_state["wz_step"] = 10
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 10:
        section_heading("Voto (1–5)", "Qualità percepita del colpo.")
        cols = st.columns(5)
        for v in range(1, 6):
            if cols[v - 1].button(str(v), key=f"sv{v}", use_container_width=True):
                shot["Rating"] = v
                st.session_state["wz_step"] = 11
                st.rerun()
    elif step == 11:
        section_heading("Reazione mentale", "Tap per salvare il colpo.")
        cols = st.columns(2)
        for i, opt in enumerate(MENTAL_OPTIONS):
            if cols[i % 2].button(opt, key=f"smn{i}", use_container_width=True):
                start_m = float(shot["Start_Dist_m"])
                end_m = float(shot["End_Dist_m"])
                sg = compute_sg_short(start_m, end_m, str(shot["Lie_Start"]), str(shot["Lie_End"]))
                _save_and_reset(
                    {
                        "User": user,
                        "Date": datetime.date.today(),
                        "SessionName": session_name,
                        "Time": datetime.datetime.now().strftime("%H:%M"),
                        "Category": "SHORT",
                        "Club": shot.get("Club", ""),
                        "Impact": shot.get("Impact", ""),
                        "Curvature": "",
                        "Trajectory": "",
                        "Lie_Start": shot.get("Lie_Start", ""),
                        "Lie_End": shot.get("Lie_End", ""),
                        "Direction_LR": shot.get("Direction_LR", ""),
                        "Proximity_Lateral_m": shot.get("Proximity_Lateral_m", np.nan),
                        "Proximity_Depth_m": shot.get("Proximity_Depth_m", np.nan),
                        "Start_Dist_m": start_m,
                        "End_Dist_m": end_m,
                        "Hole_Dist_Start_m": start_m,
                        "Hole_Dist_End_m": end_m,
                        "Lie_Long": "",
                        "Rating": shot.get("Rating", np.nan),
                        "Mental_Reaction": opt,
                        "Strokes_Gained": sg,
                    },
                    "Gioco corto salvato.",
                )
    if st.button("Annulla inserimento", key="cancel_s"):
        reset_wizard()
        st.rerun()


def wizard_putt(session_name: str, user: str) -> None:
    st.session_state.setdefault("wz_step", 0)
    step = st.session_state["wz_step"]
    shot: dict[str, Any] = st.session_state.setdefault("wz_payload", {})

    if step == 0:
        section_heading("Distanza iniziale putt", "Tap distanza dalla buca.")
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(5)
        for i, val in enumerate(PUTT_START_DIST):
            if cols[i % 5].button(f"{val:g} m", key=f"ps{i}", use_container_width=True):
                shot["Start_Dist_m"] = float(val)
                st.session_state["wz_step"] = 1
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 1:
        section_heading("Distanza finale", "0 m = putt chiuso in buca.")
        st.markdown('<div class="zrs-dist-grid">', unsafe_allow_html=True)
        cols = st.columns(6)
        for i, val in enumerate(PUTT_END_DIST):
            if cols[i % 6].button(f"{val:g} m", key=f"pe{i}", use_container_width=True):
                shot["End_Dist_m"] = float(val)
                st.session_state["wz_step"] = 2
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    elif step == 2:
        section_heading("Impatto sulla faccia", "Zona di contatto sul putter.")
        tap_grid(PUTT_IMPACT, "pi", 2, shot, "Impact", 3)
    elif step == 3:
        section_heading("Traiettoria", "Rotazione della palla.")
        cols = st.columns(3)
        for i, opt in enumerate(PUTT_TRAJ):
            if cols[i].button(opt, key=f"pt{i}", use_container_width=True):
                shot["Trajectory"] = opt
                shot["Curvature"] = opt
                st.session_state["wz_step"] = 4
                st.rerun()
    elif step == 4:
        section_heading("Voto (1–5)", "Qualità del putt.")
        cols = st.columns(5)
        for v in range(1, 6):
            if cols[v - 1].button(str(v), key=f"pv{v}", use_container_width=True):
                shot["Rating"] = v
                st.session_state["wz_step"] = 5
                st.rerun()
    elif step == 5:
        section_heading("Reazione mentale", "Tap per salvare il putt.")
        cols = st.columns(2)
        for i, opt in enumerate(MENTAL_OPTIONS):
            if cols[i % 2].button(opt, key=f"pmn{i}", use_container_width=True):
                start_m = float(shot["Start_Dist_m"])
                end_m = float(shot["End_Dist_m"])
                sg = compute_sg_putt(start_m, end_m)
                _save_and_reset(
                    {
                        "User": user,
                        "Date": datetime.date.today(),
                        "SessionName": session_name,
                        "Time": datetime.datetime.now().strftime("%H:%M"),
                        "Category": "PUTT",
                        "Club": "Putter",
                        "Impact": shot.get("Impact", ""),
                        "Curvature": shot.get("Curvature", ""),
                        "Trajectory": shot.get("Trajectory", ""),
                        "Lie_Start": "Green",
                        "Lie_End": "Green",
                        "Direction_LR": "",
                        "Proximity_Lateral_m": np.nan,
                        "Proximity_Depth_m": np.nan,
                        "Start_Dist_m": start_m,
                        "End_Dist_m": end_m,
                        "Hole_Dist_Start_m": start_m,
                        "Hole_Dist_End_m": end_m,
                        "Lie_Long": "",
                        "Rating": shot.get("Rating", np.nan),
                        "Mental_Reaction": opt,
                        "Strokes_Gained": sg,
                    },
                    "Putt salvato.",
                )
    if st.button("Annulla inserimento", key="cancel_p"):
        reset_wizard()
        st.rerun()

# =============================================================================
# Review
# =============================================================================
def review_panel(user: str, session_name: str) -> None:
    df_all = load_data()
    df_u = df_all[df_all["User"] == user]
    c_h1, c_h2 = st.columns([10, 1])
    with c_h1:
        render_hero(
            "Review performance",
            "Tabelle in alto (dati grezzi) + grafici analitici sotto. Usa i ? per leggere ogni sezione.",
            ["Tabelle", "Grafici", "Strokes Gained", "Trend"],
        )
    with c_h2:
        help_icon(
            "**Come leggere la review:** filtra periodo e settore. "
            "Le tabelle mostrano i dati colpo per colpo; i grafici evidenziano pattern e bias."
        )
    st.markdown("### Review — statistiche")
    render_panel(
        "Filtro analisi",
        "Scegli prima periodo e settore. La dashboard sotto si aggiorna in tempo reale.",
    )
    period = st.selectbox("Periodo", PERIOD_LABELS, key="rev_period")
    df_f = filter_period(df_u, session_name, period)
    sector = st.radio(
        "Settore",
        ["RANGE", "SHORT", "PUTT"],
        format_func=lambda x: CATEGORIES[x],
        horizontal=True,
        key="rev_sector",
    )
    dsec = df_f[df_f["Category"] == sector]
    st.caption(
        f"Utente **{user}** · periodo **{period}** · settore **{CATEGORIES[sector]}** · "
        f"n = **{len(dsec)}** colpi."
    )

    if dsec.empty:
        st.info("Nessun colpo in questo filtro.")
        brand_footer()
        return

    m1, m2, m3 = st.columns(3)
    m1.metric("Colpi registrati", len(dsec))
    rmean = pd.to_numeric(dsec["Rating"], errors="coerce").mean()
    m2.metric("Voto medio", f"{rmean:.2f}" if pd.notna(rmean) else "—")
    sg_series = pd.to_numeric(dsec["Strokes_Gained"], errors="coerce").dropna()
    m3.metric("SG medio", f"{sg_series.mean():+.3f}" if len(sg_series) else "—")

    st.markdown("#### Tabelle schematiche di review")
    shots_cols = [
        "Date",
        "Time",
        "SessionName",
        "Category",
        "Club",
        "Impact",
        "Curvature",
        "Trajectory",
        "Direction_LR",
        "Proximity_Lateral_m",
        "Proximity_Depth_m",
        "Rating",
        "Strokes_Gained",
    ]
    shots_table = (
        dsec[[c for c in shots_cols if c in dsec.columns]]
        .sort_values(by=["Date", "Time"], ascending=False)
        .reset_index(drop=True)
    )
    st.caption("Dettaglio colpo per colpo (settore selezionato).")
    st.dataframe(shots_table, use_container_width=True, hide_index=True)

    avg_by_cat = (
        df_f.groupby("Category", dropna=False)
        .agg(
            Colpi=("Rating", "count"),
            Media_Voto=("Rating", "mean"),
            Media_SG=("Strokes_Gained", "mean"),
        )
        .reset_index()
    )
    avg_by_cat["Category"] = avg_by_cat["Category"].map(CATEGORIES).fillna(avg_by_cat["Category"])
    avg_by_cat["Media_Voto"] = pd.to_numeric(avg_by_cat["Media_Voto"], errors="coerce").round(2)
    avg_by_cat["Media_SG"] = pd.to_numeric(avg_by_cat["Media_SG"], errors="coerce").round(3)
    st.caption("Medie per area (periodo selezionato).")
    st.dataframe(avg_by_cat, use_container_width=True, hide_index=True)

    avg_by_club = (
        dsec.groupby("Club", dropna=False)
        .agg(
            Colpi=("Rating", "count"),
            Media_Voto=("Rating", "mean"),
            Media_SG=("Strokes_Gained", "mean"),
        )
        .reset_index()
        .sort_values(by=["Colpi", "Club"], ascending=[False, True])
    )
    avg_by_club["Media_Voto"] = pd.to_numeric(avg_by_club["Media_Voto"], errors="coerce").round(2)
    avg_by_club["Media_SG"] = pd.to_numeric(avg_by_club["Media_SG"], errors="coerce").round(3)
    st.caption("Medie per colpo/bastone nel settore selezionato.")
    st.dataframe(avg_by_club, use_container_width=True, hide_index=True)

    no_short = df_f[df_f["Category"] != "SHORT"]
    comp_avg = pd.DataFrame(
        [
            {
                "Vista media": "Con SG inclusi (tutte le categorie)",
                "Colpi": len(df_f),
                "Media Voto": pd.to_numeric(df_f["Rating"], errors="coerce").mean(),
                "Media SG": pd.to_numeric(df_f["Strokes_Gained"], errors="coerce").mean(),
            },
            {
                "Vista media": "Con SG esclusi (senza SHORT)",
                "Colpi": len(no_short),
                "Media Voto": pd.to_numeric(no_short["Rating"], errors="coerce").mean(),
                "Media SG": pd.to_numeric(no_short["Strokes_Gained"], errors="coerce").mean(),
            },
        ]
    )
    comp_avg["Media Voto"] = pd.to_numeric(comp_avg["Media Voto"], errors="coerce").round(2)
    comp_avg["Media SG"] = pd.to_numeric(comp_avg["Media SG"], errors="coerce").round(3)
    st.caption("Confronto medie SG inclusi / non inclusi.")
    st.dataframe(comp_avg, use_container_width=True, hide_index=True)

    render_panel(
        "Analisi grafica",
        "Grafici in stile report tecnico: stesso filtro delle tabelle sopra. Legenda e assi annotati.",
    )
    sg_summary_table(df_f, sector)
    trend_panel(dsec, CATEGORIES[sector])
    club_breakdown_table(dsec)
    sg_distance_table(dsec)
    if sector in ("RANGE", "SHORT"):
        directional_bias_panel(dsec)

    if sector == "RANGE":
        render_panel(
            "Analisi tecnica range",
            "Impatti, curvatura, direzione e dispersione per identificare pattern e bias di traiettoria.",
        )
        plot_pie(
            dsec,
            "Impact",
            "Tipologia di impatto — percentuali",
            "Legenda: ripartizione percentuale degli impatti dichiarati.",
        )
        plot_pie(
            dsec,
            "Curvature",
            "Curvatura — percentuali",
            "Legenda: forma di volo predominante nel campione.",
        )
        plot_pie(
            dsec,
            "Direction_LR",
            "Tendenza direzionale vs bersaglio",
            "Legenda: orientamento medio rispetto alla linea di punteria.",
        )
        plot_dispersion(dsec, "Dispersione dall’alto — RANGE")
        satisfaction_breakdown(df_f, "RANGE")

    elif sector == "SHORT":
        render_panel(
            "Analisi tecnica gioco corto",
            "Confronta lie iniziale/finale, contatto e direzione per leggere conversione e qualità d'esecuzione.",
        )
        plot_pie(dsec, "Lie_Start", "Lie iniziale", "Legenda: da dove parte la palla più spesso.")
        plot_pie(dsec, "Lie_End", "Lie finale", "Legenda: dove finisce la palla dopo il colpo.")
        plot_pie(dsec, "Impact", "Impatto", "Legenda: qualità di contatto dichiarata.")
        plot_pie(dsec, "Direction_LR", "Linea vs buca", "Legenda: tendenza destra/sinistra.")
        plot_dispersion(dsec, "Dispersione dall’alto — gioco corto")
        satisfaction_breakdown(df_f, "SHORT")

    else:
        render_panel(
            "Analisi putting",
            "Contatto faccia, linea e percentuali realizzazione per fascia distanza.",
        )
        plot_pie(dsec, "Impact", "Impatto sulla faccia", "Legenda: zona di contatto sul putter.")
        plot_pie(dsec, "Trajectory", "Traiettoria di rotazione", "Legenda: pull/dritta/push.")
        putting_make_table(dsec)
        satisfaction_breakdown(df_f, "PUTT")

    brand_footer()


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    inject_styles()

    if "splash_done" not in st.session_state:
        run_splash_sequence()
        st.session_state["splash_done"] = True
        st.rerun()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "post_auth_logo_pending" not in st.session_state:
        st.session_state["post_auth_logo_pending"] = False

    if not st.session_state["logged_in"]:
        login_screen()
        return

    user = str(st.session_state["user"])
    if st.session_state.get("post_auth_logo_pending", False):
        run_post_auth_logo()
        st.session_state["post_auth_logo_pending"] = False
        st.rerun()

    brand_header("Profilo")
    st.write(f"**Atleta:** {user}")
    session_name = st.text_input(
        "Nome sessione / note",
        value=st.session_state.get("session_name_main", "Sessione Allenamento"),
        key="session_name_main",
    )
    page = st.radio(
        "Scegli sezione",
        ["Inserimento dati", "Review"],
        horizontal=True,
        key="main_page_home",
    )
    c_logout_1, c_logout_2 = st.columns([3, 1])
    with c_logout_2:
        if st.button("Logout / cambia utente", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["post_auth_logo_pending"] = False
            st.session_state.pop("user", None)
            st.rerun()

    render_command_header(page)

    if page == "Inserimento dati":
        brand_header("Inserimento rapido")
        c_i1, c_i2 = st.columns([10, 1])
        with c_i1:
            render_hero(
                "Sessione di raccolta dati",
                "Solo tap sui quadratini: nessun campo da digitare. Ogni scelta avanza automaticamente.",
                ["Range", "Short game", "Putting"],
            )
        with c_i2:
            help_icon(
                "**Inserimento corretto:** tap su ogni quadratino in ordine. "
                "Distanze buca ogni 5 m. Lie e bastoni a griglia. "
                "L'ultimo tap salva il colpo."
            )
        st.session_state.setdefault("wz_cat", None)
        if st.session_state["wz_cat"] is None:
            st.markdown("#### Scegli il settore")
            c1, c2, c3 = st.columns(3)
            if c1.button("Range\n(gioco lungo)", use_container_width=True):
                reset_wizard()
                st.session_state["wz_cat"] = "RANGE"
                st.rerun()
            if c2.button("Gioco corto\n(<50 m)", use_container_width=True):
                reset_wizard()
                st.session_state["wz_cat"] = "SHORT"
                st.rerun()
            if c3.button("Putting", use_container_width=True):
                reset_wizard()
                st.session_state["wz_cat"] = "PUTT"
                st.rerun()
            brand_footer()
        else:
            st.caption(f"Sessione: **{session_name}**")
            if st.button("Torna alla scelta settore"):
                reset_wizard()
                st.session_state["wz_cat"] = None
                st.rerun()
            cat = st.session_state["wz_cat"]
            if cat == "RANGE":
                wizard_range(session_name, user)
            elif cat == "SHORT":
                wizard_short(session_name, user)
            else:
                wizard_putt(session_name, user)
            brand_footer()

    else:
        brand_header()
        review_panel(user, session_name)


if __name__ == "__main__":
    main()
    
    
