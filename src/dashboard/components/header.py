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

        /* -------------------------
        Top Bar
        ------------------------- */
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

        /* -------------------------
        Animated S9S Logo
        ------------------------- */
        .logo {
            font-size: 22px;
            font-weight: 800;
            color: var(--dashboard-accent);
            letter-spacing: 0.08em;
            animation: s9sPulse 3s infinite ease-in-out;
        }

        @keyframes s9sPulse {
            0% {
                opacity: 0.85;
                transform: scale(1);
                text-shadow: 0 0 5px var(--dashboard-accent);
            }
            50% {
                opacity: 1;
                transform: scale(1.05);
                text-shadow: 
                    0 0 10px var(--dashboard-accent),
                    0 0 25px var(--dashboard-accent);
            }
            100% {
                opacity: 0.85;
                transform: scale(1);
                text-shadow: 0 0 5px var(--dashboard-accent);
            }
        }

        /* -------------------------
        Title
        ------------------------- */
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

        /* -------------------------
        Status Badge
        ------------------------- */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }

        .status-ok {
            background: rgba(0, 200, 120, 0.15);
            color: #00c878;
            border: 1px solid rgba(0, 200, 120, 0.4);
        }

        .status-down {
            background: rgba(255, 80, 80, 0.15);
            color: #ff5050;
            border: 1px solid rgba(255, 80, 80, 0.4);
        }

        /* -------------------------
        Blinking LIVE dot
        ------------------------- */
        .live-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            animation: blink 1.2s infinite;
        }

        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.3; }
            100% { opacity: 1; }
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 6, 2])

    # -------------------------
    # Logo
    # -------------------------
    with col1:
        st.markdown('<div class="logo">S9S</div>', unsafe_allow_html=True)

    # -------------------------
    # Title
    # -------------------------
    with col2:
        st.markdown(
            (
                '<div class="title">EPP SLA Anomaly Detection</div>'
                f'<div class="subtitle"><span class="theme-pill">{active_theme.label}</span></div>'
            ),
            unsafe_allow_html=True,
        )

    # -------------------------
    # Status
    # -------------------------
    with col3:
        transport = get_selected_transport()
        transport_label = get_transport_label(transport)

        is_healthy = check_backend_health(transport)

        if is_healthy:
            st.markdown(
                f"""
                <div class="status-badge status-ok">
                    <span class="live-dot"></span>
                    {transport_label} LIVE
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="status-badge status-down">
                    {transport_label} DOWN
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()