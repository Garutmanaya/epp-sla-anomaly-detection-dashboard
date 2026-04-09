import streamlit as st

from dashboard.components.header import render_header
from dashboard.components.inference_selector import render_inference_transport_selector
from dashboard.theme import apply_theme, initialize_theme_state

st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
/* Hide ONLY the multipage navigation (top links) */
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)
# -------------------------
# Global State
# -------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

initialize_theme_state()
apply_theme()

# -------------------------
# Top Header Bar
# -------------------------
render_header()
render_inference_transport_selector()
# -------------------------
# HOME
# -------------------------
if st.session_state.page == "home":

    st.markdown("### Available Dashboards")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Single Model"):
            st.session_state.page = "single"

    with col2:
        if st.button("🧠 Compare Models"):
            st.session_state.page = "compare"

    with col3:
        if st.button("📈 MLflow Metrics"):
            st.session_state.page = "mlflow" 


   
    st.markdown("""
    ### Dashboards Summary

    - 📊 **Single Model** → Analyze one model  
    - 🧠 **Compare Models** → Compare multiple models  

    ---
    """)


# -------------------------
# ROUTING
# -------------------------
elif st.session_state.page == "single":
    from dashboard.pages.SingleModel import render_single_model
    render_single_model()

elif st.session_state.page == "compare":
    from dashboard.pages.CompareModel import render_compare_model
    render_compare_model()

elif st.session_state.page == "mlflow":
    st.subheader("📈 MLflow Metrics")
    st.info("Implement MLflow dashboard here")
