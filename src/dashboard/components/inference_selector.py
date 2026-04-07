import streamlit as st

from dashboard.settings import (
    TRANSPORT_FASTAPI,
    TRANSPORT_OPTIONS,
    get_inference_settings,
    get_transport_label,
)
from dashboard.theme import render_theme_selector


def get_selected_transport() -> str:
    settings = get_inference_settings()
    if "inference_transport" not in st.session_state:
        st.session_state.inference_transport = settings.default_transport
    return st.session_state.inference_transport


def render_inference_transport_selector() -> str:
    settings = get_inference_settings()
    current_transport = get_selected_transport()

    if current_transport not in TRANSPORT_OPTIONS:
        st.session_state.inference_transport = settings.default_transport

    st.sidebar.subheader("🚀 Inference Route")
    st.sidebar.radio(
        "Choose backend",
        options=TRANSPORT_OPTIONS,
        format_func=get_transport_label,
        key="inference_transport",
    )

    selected_transport = st.session_state.inference_transport

    if selected_transport == TRANSPORT_FASTAPI:
        st.sidebar.caption(f"FastAPI URL: {settings.fastapi.base_url}{settings.fastapi.predict_path}")
    else:
        if settings.sagemaker.endpoint_name:
            st.sidebar.caption(
                f"SageMaker endpoint: {settings.sagemaker.endpoint_name} ({settings.sagemaker.region_name})"
            )
        else:
            st.sidebar.warning("Set SAGEMAKER_ENDPOINT_NAME to use direct SageMaker mode.")

    st.sidebar.divider()
    render_theme_selector()

    return selected_transport
