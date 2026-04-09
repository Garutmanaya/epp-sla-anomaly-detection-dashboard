def render_compare_controls():
    import streamlit as st
    from shared.data_dictionary import MODEL_OPTIONS

    st.sidebar.header("⚙️ Controls")

    # --- Models
    models = st.sidebar.multiselect(
        "Select Models",
        MODEL_OPTIONS,
        default=MODEL_OPTIONS,
        key="compare_models",
    )

    # --- Mode
    mode = st.sidebar.radio("Mode", ["Generate Data", "Upload CSV"], key="compare_mode")

    # --- Data Input
    if mode == "Generate Data":
        hours = st.sidebar.slider("Hours", 24, 200, 48, key="compare_hours")
        prob = st.sidebar.slider("Anomaly Probability", 0.0, 0.5, 0.2, key="compare_prob")
        file = None
    else:
        file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="compare_upload")
        hours = prob = None

    # NOTE: No buttons here
    return {
        "models": models,
        "mode": mode,
        "hours": hours,
        "prob": prob,
        "file": file,
    }