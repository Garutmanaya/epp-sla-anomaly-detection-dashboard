def render_realtime_simulation():
    import streamlit as st
    import pandas as pd
    import time
    import random

    from dashboard.components.controls.realtime_controls import render_realtime_controls
    from dashboard.utils.api_client import call_inference
    from dashboard.utils.dataframe_utils import build_inference_payload
    from shared.demo_data import generate_test_data
    from shared.data_dictionary import NORMAL_STATUS

    # -------------------------
    # Namespaced State
    # -------------------------
    ns = st.session_state.setdefault("realtime", {
        "data": None,
        "results": None,
        "pointer": 0,
        "running": False,
        "last_update": None,
        "current_interval": 0,
    })

    transport = st.session_state.get("inference_transport", "fastapi")

    st.subheader("🚨 Realtime Alert Simulation")

    # -------------------------
    # Controls FIRST
    # -------------------------
    controls = render_realtime_controls()

    # -------------------------
    # 🔥 TOP ACTION BAR
    # -------------------------
    col1, col2, col3, col4, col5 = st.columns([1, 4, 2, 2, 2])

    with col1:
        if st.button("⬅ Home", key="rt_home"):
            st.session_state.page = "home"
            st.rerun()

    with col3:
        start_clicked = st.button("▶ Start", key="rt_start")

    with col4:
        pause_clicked = st.button("⏸ Pause", key="rt_pause")

    with col5:
        reset_clicked = st.button("🔄 Reset", key="rt_reset")

    # -------------------------
    # Handle Actions
    # -------------------------
    if reset_clicked:
        ns.update({
            "data": None,
            "results": None,
            "pointer": 0,
            "running": False,
            "last_update": None,
            "current_interval": 0,
        })
        st.rerun()

    if start_clicked:
        # Generate + infer ONCE
        df = generate_test_data(
            start_date=pd.Timestamp("2026-05-01"),
            hours=controls["num_records"] // 2,
            anomaly_prob=0.2,
        )

        payload = build_inference_payload(df, [controls["model"]])

        try:
            with st.spinner("Preparing simulation..."):
                response = call_inference(payload, transport=transport)
        except Exception as e:
            st.error(f"Inference failed: {e}")
            return

        ns["data"] = df
        ns["results"] = pd.DataFrame(response["results"][controls["model"]])
        ns["pointer"] = 0
        ns["running"] = True
        ns["last_update"] = time.time()
        ns["current_interval"] = 0

        st.rerun()

    if pause_clicked:
        ns["running"] = False

    results = ns["results"]

    # -------------------------
    # Status Panel
    # -------------------------
    if results is None:
        st.info("👉 Click Start to begin simulation.")
        return

    total = len(results)
    processed = ns["pointer"]

    status = "Running" if ns["running"] else "Paused"

    s1, s2, s3 = st.columns(3)
    s1.metric("Status", status)
    s2.metric("Processed", f"{processed} / {total}")
    s3.metric("Interval (sec)", int(ns["current_interval"]))

    # -------------------------
    # Interval Logic
    # -------------------------
    now = time.time()

    if ns["running"] and processed < total:

        # Determine interval
        if controls["interval_mode"] == "Fixed":
            interval = controls["interval_seconds"]
        else:
            interval = random.randint(controls["random_min"], controls["random_max"])

        ns["current_interval"] = interval

        if ns["last_update"] is None:
            ns["last_update"] = now

        if now - ns["last_update"] >= interval:
            ns["pointer"] += 1
            ns["last_update"] = now

            # Alert feedback
            latest_row = results.iloc[ns["pointer"] - 1]
            if latest_row["Status"] != NORMAL_STATUS:
                st.toast("🚨 New Alert!", icon="⚠️")

            st.rerun()

    # -------------------------
    # Display Data (latest first)
    # -------------------------
    display_df = results.head(ns["pointer"]).copy()

    if not display_df.empty:
        display_df = display_df.sort_values("Timestamp", ascending=False)

        # Limit rows
        display_df = display_df.head(controls["max_rows"])

        st.subheader("📡 Live Alerts")
        st.dataframe(display_df, width="stretch")
    else:
        st.info("Waiting for first alert...")
