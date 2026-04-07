import streamlit as st

from dashboard.components.header import render_header
from dashboard.components.inference_selector import render_inference_transport_selector

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebarNav"] ul li:first-child {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_inference_transport_selector()
render_header()

st.subheader("📊 Welcome")
st.info("Select a dashboard from the sidebar.")

st.markdown(
    """
    ### Available Dashboards

    - 📊 **Single Model** -> Analyze one model
    - 🧠 **Compare Models** -> Compare multiple models
    - 📈 **MLflow Metrics** -> Review training, validation, and threshold runs
    """
)
