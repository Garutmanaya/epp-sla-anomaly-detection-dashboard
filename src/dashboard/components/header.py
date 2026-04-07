import streamlit as st

from dashboard.components.inference_selector import get_selected_transport
from dashboard.settings import get_transport_label
from dashboard.utils.api_client import check_backend_health


def render_header() -> None:
    st.markdown(
        """
        <style>
        .topbar {
            background: #0f172a;
            padding: 14px 20px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 22px;
            font-weight: 800;
            color: #38bdf8;
        }

        .title {
            font-size: 18px;
            font-weight: 600;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.markdown('<div class="logo">S9S</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="title">EPP SLA Anomaly Detection</div>', unsafe_allow_html=True)

    with col3:
        transport = get_selected_transport()
        transport_label = get_transport_label(transport)
        if check_backend_health(transport):
            st.success(f"{transport_label} OK")
        else:
            st.error(f"{transport_label} DOWN")

    st.divider()
