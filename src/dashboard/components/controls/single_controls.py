def render_single_controls():
    import streamlit as st
    from shared.data_dictionary import COMMAND_OPTIONS, MODEL_OPTIONS, STATUS_OPTIONS

    st.sidebar.header("⚙️ Controls")

    # --- Model
    model = st.sidebar.selectbox("Select Model", MODEL_OPTIONS, key="single_model")

    # --- Mode
    mode = st.sidebar.radio("Mode", ["Generate Data", "Upload CSV"], key="single_mode")

    # --- Data Input
    if mode == "Generate Data":
        hours = st.sidebar.slider("Hours", 24, 200, 48, key="single_hours")
        prob = st.sidebar.slider("Anomaly Probability", 0.0, 0.5, 0.2, key="single_prob")
        file = None
    else:
        file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="single_upload")
        hours = prob = None

    # --- Filters
    st.sidebar.subheader("🔍 Filters")
    selected_command = st.sidebar.multiselect("Command", COMMAND_OPTIONS, key="single_cmd")
    selected_status = st.sidebar.multiselect("Status", STATUS_OPTIONS, key="single_status")

    # NOTE: No buttons here anymore
    return {
        "model": model,
        "mode": mode,
        "hours": hours,
        "prob": prob,
        "file": file,
        "selected_command": selected_command,
        "selected_status": selected_status,
    }