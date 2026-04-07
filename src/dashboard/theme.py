from dataclasses import dataclass
import os

import plotly.graph_objects as go
import streamlit as st

THEME_SESSION_KEY = "dashboard_theme"
DEFAULT_THEME_KEY = "midnight"


@dataclass(frozen=True)
class DashboardTheme:
    key: str
    label: str
    description: str
    mode: str
    background: str
    surface: str
    surface_alt: str
    surface_highlight: str
    sidebar_background: str
    text: str
    muted_text: str
    accent: str
    accent_soft: str
    accent_text: str
    border: str
    shadow: str
    chart_colors: tuple[str, ...]


THEMES = {
    "midnight": DashboardTheme(
        key="midnight",
        label="Midnight Pulse",
        description="Dark navy with electric cyan accents for low-light monitoring.",
        mode="dark",
        background="#06111f",
        surface="#0f1c2f",
        surface_alt="#15263d",
        surface_highlight="#1c3150",
        sidebar_background="#081629",
        text="#e2ecff",
        muted_text="#9db0cc",
        accent="#38bdf8",
        accent_soft="#0ea5e9",
        accent_text="#031525",
        border="#234166",
        shadow="0 16px 40px rgba(3, 10, 24, 0.30)",
        chart_colors=("#38bdf8", "#f97316", "#22c55e", "#a855f7", "#facc15"),
    ),
    "sage": DashboardTheme(
        key="sage",
        label="Sage Signal",
        description="Clean light surfaces with green highlights for everyday analysis.",
        mode="light",
        background="#f4f8f1",
        surface="#ffffff",
        surface_alt="#eef6e7",
        surface_highlight="#dcefd1",
        sidebar_background="#edf6e9",
        text="#1c2a1f",
        muted_text="#5d715f",
        accent="#2f855a",
        accent_soft="#68d391",
        accent_text="#f5fff8",
        border="#c6dcc7",
        shadow="0 14px 35px rgba(39, 65, 45, 0.10)",
        chart_colors=("#2f855a", "#2b6cb0", "#dd6b20", "#805ad5", "#d53f8c"),
    ),
    "sunrise": DashboardTheme(
        key="sunrise",
        label="Sunrise Ops",
        description="Warm sand tones with coral accents for a brighter control room feel.",
        mode="light",
        background="#fff8f1",
        surface="#ffffff",
        surface_alt="#fff1df",
        surface_highlight="#ffe0bc",
        sidebar_background="#fff3e4",
        text="#41251c",
        muted_text="#7a5a4e",
        accent="#dd6b20",
        accent_soft="#f6ad55",
        accent_text="#fff7ef",
        border="#f3cfb0",
        shadow="0 16px 35px rgba(131, 71, 23, 0.12)",
        chart_colors=("#dd6b20", "#3182ce", "#38a169", "#d53f8c", "#805ad5"),
    ),
}


def _normalize_theme_key(value: str | None) -> str:
    normalized = (value or DEFAULT_THEME_KEY).strip().lower()
    if normalized in THEMES:
        return normalized
    return DEFAULT_THEME_KEY


def initialize_theme_state() -> None:
    st.session_state.setdefault(
        THEME_SESSION_KEY,
        _normalize_theme_key(os.getenv("DASHBOARD_THEME", DEFAULT_THEME_KEY)),
    )


def get_active_theme() -> DashboardTheme:
    initialize_theme_state()
    theme_key = _normalize_theme_key(st.session_state.get(THEME_SESSION_KEY))
    return THEMES[theme_key]


def render_theme_selector() -> DashboardTheme:
    initialize_theme_state()

    st.sidebar.subheader("🎨 Theme")
    st.sidebar.selectbox(
        "Dashboard Theme",
        options=list(THEMES.keys()),
        format_func=lambda key: THEMES[key].label,
        key=THEME_SESSION_KEY,
    )

    active_theme = get_active_theme()
    st.sidebar.caption(active_theme.description)
    return active_theme


def apply_theme() -> DashboardTheme:
    theme = get_active_theme()

    st.markdown(
        f"""
        <style>
        :root {{
            --dashboard-bg: {theme.background};
            --dashboard-surface: {theme.surface};
            --dashboard-surface-alt: {theme.surface_alt};
            --dashboard-surface-highlight: {theme.surface_highlight};
            --dashboard-sidebar-bg: {theme.sidebar_background};
            --dashboard-text: {theme.text};
            --dashboard-muted: {theme.muted_text};
            --dashboard-accent: {theme.accent};
            --dashboard-accent-soft: {theme.accent_soft};
            --dashboard-accent-text: {theme.accent_text};
            --dashboard-border: {theme.border};
            --dashboard-shadow: {theme.shadow};
        }}

        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"] {{
            background: var(--dashboard-bg);
            color: var(--dashboard-text);
            transition: background-color 180ms ease, color 180ms ease;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        .block-container {{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--dashboard-sidebar-bg), var(--dashboard-surface)) !important;
            border-right: 1px solid var(--dashboard-border);
        }}

        [data-testid="stSidebar"] * {{
            color: var(--dashboard-text);
        }}

        [data-testid="stSidebarNav"] ul li:first-child {{
            display: none;
        }}

        [data-testid="stSidebarNav"] a {{
            border-radius: 14px;
            border: 1px solid transparent;
            transition: background-color 180ms ease, border-color 180ms ease, transform 180ms ease;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background: var(--dashboard-surface-alt);
            border-color: var(--dashboard-border);
            transform: translateX(2px);
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: linear-gradient(135deg, var(--dashboard-accent), var(--dashboard-accent-soft));
            border-color: transparent;
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] *,
        [data-testid="stSidebarNav"] a[aria-current="page"] span {{
            color: var(--dashboard-accent-text) !important;
            font-weight: 700;
        }}

        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        p,
        label,
        [data-testid="stMarkdownContainer"],
        [data-testid="stCaptionContainer"] {{
            color: var(--dashboard-text);
        }}

        .stCaption,
        [data-testid="stCaptionContainer"] p {{
            color: var(--dashboard-muted) !important;
        }}

        [data-testid="stMetric"],
        [data-testid="stDataFrame"],
        [data-testid="stTable"],
        [data-testid="stFileUploader"],
        [data-testid="stPlotlyChart"],
        [data-testid="stExpander"] details {{
            background: var(--dashboard-surface);
            border: 1px solid var(--dashboard-border);
            border-radius: 18px;
            box-shadow: var(--dashboard-shadow);
        }}

        [data-testid="stMetric"] {{
            padding: 0.9rem 1rem;
        }}

        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"],
        [data-testid="stMetricDelta"] {{
            color: var(--dashboard-text) !important;
        }}

        .stAlert {{
            border-radius: 18px;
        }}

        .stButton > button,
        [data-testid="baseButton-primary"],
        [data-testid="baseButton-secondary"] {{
            background: linear-gradient(135deg, var(--dashboard-accent), var(--dashboard-accent-soft)) !important;
            color: var(--dashboard-accent-text) !important;
            border: 0 !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
            box-shadow: var(--dashboard-shadow);
        }}

        .stButton > button:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="baseButton-secondary"]:hover {{
            filter: brightness(1.05);
        }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] > div,
        div[data-baseweb="base-input"] {{
            background: var(--dashboard-surface) !important;
            border-color: var(--dashboard-border) !important;
            border-radius: 14px !important;
        }}

        div[data-baseweb="select"] input,
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {{
            color: var(--dashboard-text) !important;
        }}

        div[data-baseweb="tag"] {{
            background: var(--dashboard-surface-highlight) !important;
            color: var(--dashboard-text) !important;
            border-radius: 999px !important;
            border: 1px solid var(--dashboard-border) !important;
        }}

        [data-testid="stCheckbox"] label,
        [data-testid="stRadio"] label,
        [data-testid="stSelectbox"] label,
        [data-testid="stMultiSelect"] label,
        [data-testid="stSlider"] label,
        [data-testid="stTextInput"] label {{
            color: var(--dashboard-text) !important;
        }}

        [data-testid="stToolbar"] {{
            right: 1rem;
        }}

        hr {{
            border-color: var(--dashboard-border);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    return theme


def style_plotly_figure(fig: go.Figure) -> go.Figure:
    theme = get_active_theme()
    template = "plotly_dark" if theme.mode == "dark" else "plotly_white"

    fig.update_layout(
        template=template,
        paper_bgcolor=theme.surface,
        plot_bgcolor=theme.surface,
        font={"color": theme.text},
        title_font={"color": theme.text},
        colorway=list(theme.chart_colors),
        margin={"l": 16, "r": 16, "t": 56, "b": 16},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(0, 0, 0, 0)",
            "font": {"color": theme.text},
        },
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=theme.border,
        linecolor=theme.border,
        tickfont={"color": theme.text},
        title_font={"color": theme.text},
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=theme.border,
        linecolor=theme.border,
        tickfont={"color": theme.text},
        title_font={"color": theme.text},
        zeroline=False,
    )

    return fig
