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
    # Namespaced State
    # -------------------------
    ns = st.session_state.setdefault("compare", {
        "df": None,
        "results": None,
        "metadata": {},
        "models_used": [],
        "transport_used": None,
    })

    transport = st.session_state.get("inference_transport", "fastapi")

    st.subheader("🧠 Advanced Model Comparison")

    # -------------------------
    # Controls FIRST (defines `file`)
    # -------------------------
    controls = render_compare_controls()
    models = controls["models"]
    mode = controls["mode"]
    hours = controls["hours"]
    prob = controls["prob"]
    file = controls["file"]

    # -------------------------
    # 🔥 TOP ACTION BAR
    # -------------------------
    col1, col2, col3, col4 = st.columns([1, 6, 2, 2])

    with col1:
        if st.button("⬅ Home", key="compare_back"):
            st.session_state.page = "home"
            st.rerun()
    with col3:
        generate_clicked = st.button("🧪 Generate Data", key="compare_generate_btn")

    # derive availability using current click + namespace
    data_exists = (ns["df"] is not None) or generate_clicked or (file is not None)

    with col4:
        run_clicked = st.button(
            "🚀 Run Analysis",
            key="compare_run_btn",
            disabled=not data_exists
        )

    # -------------------------
    # Data Input
    # -------------------------
    if mode == "Generate Data":
        if generate_clicked:
            ns["df"] = generate_test_data(
                start_date=pd.Timestamp("2026-05-01"),
                hours=hours,
                anomaly_prob=prob,
            )
            ns["results"] = None
            ns["metadata"] = {}
            ns["models_used"] = []
            ns["transport_used"] = None

    elif mode == "Upload CSV":
        if file:
            try:
                ns["df"] = load_uploaded_csv(file)
                ns["results"] = None
                ns["metadata"] = {}
                ns["models_used"] = []
                ns["transport_used"] = None
            except Exception as e:
                st.error(f"CSV error: {e}")

    df = ns["df"]

    # -------------------------
    # UX Guidance
    # -------------------------
    #if df is None:
    #    st.info("👉 Step 1: Generate data or upload CSV to begin.")
    #    return
    #elif ns["results"] is None:
    #    st.success("✅ Data ready. Click 'Run Analysis' to proceed.")

    # -------------------------
    # UX Guidance (FIXED)
    # -------------------------
    if df is None:
        st.info("👉 Step 1: Generate data or upload CSV to begin.")
        return

    # Only show "ready" BEFORE run is clicked
    if ns["results"] is None and not run_clicked:
        st.success("✅ Data ready. Click 'Run Analysis' to proceed.")

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

        ns["results"] = {
            m: pd.DataFrame(response["results"][m]) for m in models
        }
        ns["metadata"] = response["metadata"]
        ns["models_used"] = list(models)
        ns["transport_used"] = transport

    # -------------------------
    # Preview ONLY before results
    # -------------------------
    if ns["results"] is None:
        st.subheader("📄 Input Data Preview")
        st.dataframe(df.head(50), width="stretch")
        return

    # -------------------------
    # Validation checks
    # -------------------------
    if ns["models_used"] != models:
        st.info("Model changed. Run again.")
        return

    if ns["transport_used"] != transport:
        st.info("Transport changed. Run again.")
        return

    results = ns["results"]
    metadata = ns["metadata"]

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