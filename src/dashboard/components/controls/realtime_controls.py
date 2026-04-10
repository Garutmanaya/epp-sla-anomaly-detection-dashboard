def render_realtime_controls():
    import streamlit as st
    from shared.data_dictionary import MODEL_OPTIONS

    st.sidebar.header("⏱️ Realtime Simulation")

    num_records = st.sidebar.selectbox(
        "Number of Records",
        options=[100, 200, 300, 400, 500],
        index=1,
        key="rt_num_records",
    )

    interval_mode = st.sidebar.radio(
        "Interval Mode",
        options=["Fixed", "Random"],
        key="rt_interval_mode",
    )

    if interval_mode == "Fixed":
        interval_seconds = st.sidebar.selectbox(
            "Interval",
            options=[60, 120, 180, 240, 300],  # 1m–5m
            format_func=lambda x: f"{x//60} min",
            key="rt_interval_fixed",
        )
        random_min = random_max = None
    else:
        random_min = st.sidebar.slider(
            "Min Interval (sec)",
            10, 300, 10,
            key="rt_interval_min",
        )
        random_max = st.sidebar.slider(
            "Max Interval (sec)",
            10, 300, 60,
            key="rt_interval_max",
        )
        interval_seconds = None

    model = st.sidebar.selectbox(
        "Model",
        MODEL_OPTIONS,
        key="rt_model",
    )

    max_rows = st.sidebar.selectbox(
        "Max Alerts on Screen",
        options=[10, 25, 50, 100],
        index=2,
        key="rt_max_rows",
    )

    return {
        "num_records": num_records,
        "interval_mode": interval_mode,
        "interval_seconds": interval_seconds,
        "random_min": random_min,
        "random_max": random_max,
        "model": model,
        "max_rows": max_rows,
    }
