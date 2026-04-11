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

st.markdown("""
<style>

/* Global font size */
html, body, [class*="css"] {
    font-size: 13px;
}

/* Sidebar */
section[data-testid="stSidebar"] * {
    font-size: 12px !important;
}

/* Buttons */
button {
    font-size: 12px !important;
    padding: 0.25rem 0.5rem !important;
}

/* Headers */
h1 { font-size: 20px !important; }
h2 { font-size: 18px !important; }
h3 { font-size: 16px !important; }

/* Metrics */
[data-testid="stMetric"] {
    font-size: 12px;
}

/* Dataframe text */
[data-testid="stDataFrame"] {
    font-size: 12px;
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📊 Single Model"):
            st.session_state.page = "single"

    with col2:
        if st.button("🧠 Compare Models"):
            st.session_state.page = "compare"

    with col3:
        if st.button("📈 MLflow Metrics"):
            st.session_state.page = "mlflow" 

    with col4:
        if st.button("⏱️ Realtime Simulation"):
            st.session_state.page = "realtime"
   
    
    st.markdown("""
    ### 📊 Dashboards Overview

    - 📊 **Single Model** → Deep dive into a single model’s behavior with alert analysis, performance metrics, and root cause insights  

    - 🧠 **Compare Models** → Compare multiple models to understand performance differences, agreement patterns, and alert distribution  

    - 📈 **MLflow Metrics** → Track experiments, monitor model performance over time, and review training, validation, and threshold runs  

    - ⏱️ **Realtime Simulation** → Experience live alert streaming with configurable intervals to simulate real-world anomaly detection scenarios  

    ---

    ### 🏗️ Architecture

    Streamlit UI → API Gateway → AWS Lambda → SageMaker Serverless → Docker (FastAPI + Models)

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
    from dashboard.pages.MLflow_Metrics import render_mlflow_metrics
    render_mlflow_metrics()

elif st.session_state.page == "realtime":
    from dashboard.pages.RealtimeSimulation import render_realtime_simulation
    render_realtime_simulation()