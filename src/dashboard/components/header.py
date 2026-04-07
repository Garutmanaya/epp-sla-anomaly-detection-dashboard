import streamlit as st

from dashboard.components.inference_selector import get_selected_transport
from dashboard.settings import get_transport_label
from dashboard.theme import get_active_theme
from dashboard.utils.api_client import check_backend_health


def render_header() -> None:
    active_theme = get_active_theme()

    st.markdown(
        """
        <style>
        .topbar {
            background: linear-gradient(
                135deg,
                var(--dashboard-surface-highlight),
                var(--dashboard-surface)
            );
            padding: 18px 22px;
            border-radius: 18px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border: 1px solid var(--dashboard-border);
            box-shadow: var(--dashboard-shadow);
        }

        .logo {
            font-size: 22px;
            font-weight: 800;
            color: var(--dashboard-accent);
            letter-spacing: 0.08em;
        }

        .title {
            font-size: 19px;
            font-weight: 700;
            color: var(--dashboard-text);
        }

        .subtitle {
            font-size: 13px;
            margin-top: 4px;
            color: var(--dashboard-muted);
        }

        .theme-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            background: var(--dashboard-surface);
            border: 1px solid var(--dashboard-border);
            color: var(--dashboard-text);
            font-size: 12px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.markdown('<div class="logo">S9S</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(
            (
                '<div class="title">EPP SLA Anomaly Detection</div>'
                f'<div class="subtitle"><span class="theme-pill">{active_theme.label}</span></div>'
            ),
            unsafe_allow_html=True,
        )

    with col3:
        transport = get_selected_transport()
        transport_label = get_transport_label(transport)
        if check_backend_health(transport):
            st.success(f"{transport_label} OK")
        else:
            st.error(f"{transport_label} DOWN")

    st.divider()
