def render_mlflow_controls():
    import streamlit as st
    from dashboard.settings import get_mlflow_settings

    settings = get_mlflow_settings()

    st.sidebar.header("📈 MLflow")

    tracking_uri = st.sidebar.text_input(
        "Tracking URI",
        value=settings.tracking_uri,
        key="mlflow_tracking_uri",
    )

    max_runs = st.sidebar.slider(
        "Max Runs",
        min_value=25,
        max_value=1000,
        value=settings.default_max_runs,
        step=25,
        key="mlflow_max_runs",
    )

    st.sidebar.subheader("🔎 Filters")

    # placeholders (populated after data load)
    selected_experiments = st.sidebar.multiselect("Experiments", options=[], key="mlflow_exp")
    selected_status = st.sidebar.multiselect("Run Status", options=[], key="mlflow_status")
    selected_stage = st.sidebar.multiselect("Run Stage", options=[], key="mlflow_stage")
    selected_model = st.sidebar.multiselect("Model Family", options=[], key="mlflow_model")

    return {
        "tracking_uri": tracking_uri,
        "max_runs": max_runs,
        "selected_experiments": selected_experiments,
        "selected_status": selected_status,
        "selected_stage": selected_stage,
        "selected_model": selected_model,
    }
