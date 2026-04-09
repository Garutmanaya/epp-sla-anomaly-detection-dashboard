def render_compare_model():
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    from dashboard.theme import style_plotly_figure
    from dashboard.utils.api_client import call_inference
    from dashboard.utils.dataframe_utils import (
        add_alert_flags,
        build_inference_payload,
        build_status_comparison_table,
        load_uploaded_csv,
    )
    from dashboard.components.controls.compare_controls import render_compare_controls

    from shared.data_dictionary import NORMAL_STATUS
    from shared.demo_data import generate_test_data

    # -------------------------
    # Init state
    # -------------------------
    defaults = {
        "compare_df": None,
        "compare_results": None,
        "compare_metadata": {},
        "compare_models_used": [],
        "compare_transport_used": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

    transport = st.session_state.get("inference_transport", "fastapi")

    st.subheader("🧠 Advanced Model Comparison")

    # -------------------------
    # 🔥 TOP ACTION BAR (NEW)
    # -------------------------
    col1, col2, col3 = st.columns([1, 2, 2])

    with col1:
        if st.button("⬅ Back", key="compare_back"):
            st.session_state.page = "home"

    with col2:
        generate_clicked = st.button("🧪 Generate Data", key="compare_generate_btn")

    with col3:
        run_clicked = st.button(
            "🚀 Run Analysis",
            key="compare_run_btn",
            disabled=st.session_state.get("compare_df") is None
        )

    # -------------------------
    # Controls (sidebar inputs only)
    # -------------------------
    controls = render_compare_controls()

    models = controls["models"]
    mode = controls["mode"]
    hours = controls["hours"]
    prob = controls["prob"]
    file = controls["file"]

    # -------------------------
    # Data Input
    # -------------------------
    if mode == "Generate Data":
        if generate_clicked:
            st.session_state.compare_df = generate_test_data(
                start_date=pd.Timestamp("2026-05-01"),
                hours=hours,
                anomaly_prob=prob,
            )
            st.session_state.compare_results = None

    elif mode == "Upload CSV":
        if file:
            try:
                st.session_state.compare_df = load_uploaded_csv(file)
                st.session_state.compare_results = None
            except Exception as e:
                st.error(f"CSV error: {e}")

    df = st.session_state.compare_df

    if df is None:
        st.warning("Generate or upload data")
        return

    # -------------------------
    # Run (BEFORE preview)
    # -------------------------
    if run_clicked:
        if not models:
            st.warning("Select at least one model")
            return

        payload = build_inference_payload(df, models)

        try:
            with st.spinner("Running comparison..."):
                response = call_inference(payload, transport=transport)
        except Exception as e:
            st.error(f"Inference failed: {e}")
            return

        st.session_state.compare_results = {
            m: pd.DataFrame(response["results"][m]) for m in models
        }
        st.session_state.compare_metadata = response["metadata"]
        st.session_state.compare_models_used = list(models)
        st.session_state.compare_transport_used = transport

    # -------------------------
    # Preview ONLY before results
    # -------------------------
    if st.session_state.compare_results is None:
        st.subheader("📄 Input Data Preview")
        st.dataframe(df.head(50), width="stretch")
        st.info("Click Run Analysis.")
        return

    if st.session_state.compare_models_used != models:
        st.info("Model changed. Run again.")
        return

    if st.session_state.compare_transport_used != transport:
        st.info("Transport changed. Run again.")
        return

    results = st.session_state.compare_results
    metadata = st.session_state.compare_metadata

    # -------------------------
    # KPIs
    # -------------------------
    st.subheader("📊 Model KPIs")

    cols = st.columns(len(models))
    for i, m in enumerate(models):
        df_m = results[m]
        total = len(df_m)
        alerts = (df_m["Status"] != NORMAL_STATUS).sum()
        pct = (alerts / total * 100) if total else 0

        cols[i].metric(
            m.upper(),
            alerts,
            f"{pct:.2f}% | {metadata[m]['latency_ms']} ms",
        )

    st.divider()

    # -------------------------
    # Overlap
    # -------------------------
    st.subheader("🔗 Overlap & Agreement")

    status_table = build_status_comparison_table(results, models)
    status_table, alert_cols = add_alert_flags(status_table, models)

    st.dataframe(status_table.head(100), width="stretch")

    # -------------------------
    # Charts
    # -------------------------
    st.subheader("📈 Alerts Over Time")

    frames = []
    for m in models:
        temp = results[m].copy()
        temp["Timestamp"] = pd.to_datetime(temp["Timestamp"], errors="coerce")
        temp = temp[temp["Status"] != NORMAL_STATUS]
        grouped = temp.groupby("Timestamp").size().reset_index(name="alerts")
        grouped["model"] = m
        frames.append(grouped)

    if frames:
        ts = pd.concat(frames)
        fig = px.line(ts, x="Timestamp", y="alerts", color="model")
        st.plotly_chart(style_plotly_figure(fig), width="stretch")