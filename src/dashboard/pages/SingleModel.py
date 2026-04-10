def render_single_model():
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    from dashboard.theme import style_plotly_figure
    from dashboard.utils.api_client import call_inference
    from dashboard.utils.dataframe_utils import build_inference_payload, load_uploaded_csv
    from dashboard.components.controls.single_controls import render_single_controls

    from shared.data_dictionary import NORMAL_STATUS
    from shared.demo_data import generate_test_data

    # -------------------------
    # Namespaced State
    # -------------------------
    ns = st.session_state.setdefault("single", {
        "df": None,
        "results": None,
        "meta": {},
        "last_model": None,
        "last_transport": None,
    })

    transport = st.session_state.get("inference_transport", "fastapi")

    st.subheader("🚨 Single Model Inference & Analysis")

    # -------------------------
    # Controls FIRST (important for file)
    # -------------------------
    controls = render_single_controls()

    model = controls["model"]
    mode = controls["mode"]
    hours = controls["hours"]
    prob = controls["prob"]
    file = controls["file"]
    selected_command = controls["selected_command"]
    selected_status = controls["selected_status"]

    # -------------------------
    # 🔥 TOP ACTION BAR
    # -------------------------
    col1, col2, col3, col4 = st.columns([1, 6, 2, 2])

    with col1:
      
        if st.button("⬅ Home", key="single_back"):
            st.session_state.page = "home"
            st.rerun()

    with col3:
        generate_clicked = st.button("🧪 Generate Data", key="single_generate_btn")

    data_exists = (
        ns["df"] is not None
        or generate_clicked
        or file is not None
    )

    with col4:
        run_clicked = st.button(
            "🚀 Run Analysis",
            key="single_run_btn",
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
            ns["meta"] = {}
            ns["last_model"] = None
            ns["last_transport"] = None

    elif mode == "Upload CSV":
        if file:
            try:
                ns["df"] = load_uploaded_csv(file)
                ns["results"] = None
                ns["meta"] = {}
                ns["last_model"] = None
                ns["last_transport"] = None
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
    # Run
    # -------------------------
    if run_clicked:
        payload = build_inference_payload(df, [model])

        try:
            with st.spinner("Running inference..."):
                response = call_inference(payload, transport=transport)
        except Exception as e:
            st.error(f"Inference failed: {e}")
            return

        ns["results"] = pd.DataFrame(response["results"][model])
        ns["meta"] = response["metadata"].get(model, {})
        ns["last_model"] = model
        ns["last_transport"] = transport

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
    if ns["last_model"] != model:
        st.info("Model changed. Run again.")
        return

    if ns["last_transport"] != transport:
        st.info("Transport changed. Run again.")
        return

    results = ns["results"].copy()
    meta = ns["meta"]

    # -------------------------
    # Filters
    # -------------------------
    if selected_command:
        results = results[results["Command"].isin(selected_command)]

    if selected_status:
        results = results[results["Status"].isin(selected_status)]

    alerts_df = results[results["Status"] != NORMAL_STATUS]

    total = len(results)
    alerts = len(alerts_df)
    alert_pct = (alerts / total * 100) if total else 0

    # -------------------------
    # KPIs
    # -------------------------
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Model", model.upper())
    c2.metric("Total", total)
    c3.metric("Alerts", alerts)
    c4.metric("Alert %", f"{alert_pct:.2f}%")
    c5.metric("Latency (ms)", meta.get("latency_ms", 0))

    st.divider()

    # -------------------------
    # Charts
    # -------------------------
    st.subheader("📈 Alerts Over Time")

    ts = results.copy()
    ts["Timestamp"] = pd.to_datetime(ts["Timestamp"], errors="coerce")
    ts = ts[ts["Status"] != NORMAL_STATUS].groupby("Timestamp").size().reset_index(name="alerts")

    if not ts.empty:
        fig = px.line(ts, x="Timestamp", y="alerts", markers=True)
        st.plotly_chart(style_plotly_figure(fig), width="stretch")
    else:
        st.info("No alerts detected")

    st.subheader("📊 Root Cause Distribution")
    if not alerts_df.empty:
        root_causes = alerts_df["Root_Cause"].value_counts().reset_index()
        root_causes.columns = ["Root_Cause", "Count"]
        fig = px.bar(root_causes, x="Root_Cause", y="Count")
        st.plotly_chart(style_plotly_figure(fig), width="stretch")

    st.subheader("⚠️ Severity Distribution")
    if not alerts_df.empty:
        fig = px.histogram(alerts_df, x="Severity", nbins=30)
        st.plotly_chart(style_plotly_figure(fig), width="stretch")

    st.subheader("🧩 Alerts by Command")
    if not alerts_df.empty:
        command_counts = alerts_df["Command"].value_counts().reset_index()
        command_counts.columns = ["Command", "Count"]
        fig = px.bar(command_counts, x="Command", y="Count")
        st.plotly_chart(style_plotly_figure(fig), width="stretch")

    # -------------------------
    # Tables
    # -------------------------
    st.subheader("🚨 Alerts")
    st.dataframe(alerts_df.sort_values("Severity", ascending=False), width="stretch")

    with st.expander("📄 Raw Input Data"):
        st.dataframe(df.head(100), width="stretch")

    with st.expander("📄 Full Results"):
        st.dataframe(results.head(100), width="stretch")