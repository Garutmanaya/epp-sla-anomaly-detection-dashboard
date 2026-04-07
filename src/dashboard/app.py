import streamlit as st

from dashboard.components.header import render_header
from dashboard.components.inference_selector import render_inference_transport_selector
from dashboard.theme import apply_theme, initialize_theme_state

st.set_page_config(layout="wide")
initialize_theme_state()
apply_theme()

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
