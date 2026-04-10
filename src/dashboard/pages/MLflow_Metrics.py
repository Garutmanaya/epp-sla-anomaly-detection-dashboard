def render_mlflow_metrics():
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    from dashboard.theme import style_plotly_figure
    from dashboard.components.controls.mlflow_controls import render_mlflow_controls

    from dashboard.utils.mlflow_client import (
        build_recent_runs_table,
        clear_cached_mlflow_data,
        fetch_experiments,
        fetch_runs,
        get_metric_columns,
        prepare_runs_dataframe,
    )

    # -------------------------
    # Namespaced State
    # -------------------------
    ns = st.session_state.setdefault("mlflow", {
        "experiments_df": None,
        "runs_df": None,
    })

    st.subheader("📈 MLflow Metrics & Insights")

    # -------------------------
    # Controls FIRST
    # -------------------------
    controls = render_mlflow_controls()
    tracking_uri = controls["tracking_uri"]
    max_runs = controls["max_runs"]

    # -------------------------
    # 🔥 TOP ACTION BAR
    # -------------------------
    col1, col2, col3, col4 = st.columns([1, 6, 2, 2])

    with col1:
        if st.button("⬅ Home", key="mlflow_home"):
            st.session_state.page = "home"
            st.rerun()

    with col3:
        refresh_clicked = st.button("🔄 Refresh", key="mlflow_refresh_btn")

    # -------------------------
    # Load Data
    # -------------------------
    if refresh_clicked or ns["experiments_df"] is None:
        clear_cached_mlflow_data()
        try:
            ns["experiments_df"] = fetch_experiments(tracking_uri)
        except Exception as e:
            st.error(f"MLflow connection failed: {e}")
            return

    experiments_df = ns["experiments_df"]

    if experiments_df is None or experiments_df.empty:
        st.warning("No experiments found.")
        return

    # -------------------------
    # Populate sidebar options dynamically
    # -------------------------
    exp_names = experiments_df["name"].tolist()

    selected_experiment_names = st.sidebar.multiselect(
        "Experiments",
        options=exp_names,
        default=exp_names[:1],
        key="mlflow_exp_dynamic",
    )

    exp_ids = experiments_df[
        experiments_df["name"].isin(selected_experiment_names)
    ]["experiment_id"].astype(str).tolist()

    if not exp_ids:
        st.info("Select at least one experiment")
        return

    # -------------------------
    # Load Runs
    # -------------------------
    if refresh_clicked or ns["runs_df"] is None:
        try:
            raw_runs_df = fetch_runs(tracking_uri, tuple(exp_ids), max_runs)
            ns["runs_df"] = prepare_runs_dataframe(raw_runs_df, experiments_df)
        except Exception as e:
            st.error(f"Failed to fetch runs: {e}")
            return

    runs_df = ns["runs_df"]

    if runs_df.empty:
        st.warning("No runs found")
        return

    # -------------------------
    # Filters
    # -------------------------
    status_options = sorted(runs_df["status"].dropna().unique())
    stage_options = sorted(runs_df["run_stage"].dropna().unique())
    model_options = sorted(runs_df["model_family"].dropna().unique())

    selected_status = st.sidebar.multiselect("Run Status", status_options, default=status_options)
    selected_stage = st.sidebar.multiselect("Run Stage", stage_options, default=stage_options)
    selected_model = st.sidebar.multiselect("Model Family", model_options, default=model_options)

    filtered = runs_df[
        runs_df["status"].isin(selected_status)
        & runs_df["run_stage"].isin(selected_stage)
        & runs_df["model_family"].isin(selected_model)
    ].copy()

    if filtered.empty:
        st.warning("No runs match filters")
        return

    # -------------------------
    # KPI Strip
    # -------------------------
    latest_time = filtered["start_time"].max()

    best_precision = filtered["metrics.precision"].dropna().max()
    best_recall = filtered["metrics.recall"].dropna().max()
    lowest_alert = filtered["metrics.alert_rate"].dropna().min()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runs", len(filtered))
    c2.metric("Best Precision", f"{best_precision:.3f}" if pd.notna(best_precision) else "-")
    c3.metric("Best Recall", f"{best_recall:.3f}" if pd.notna(best_recall) else "-")
    c4.metric("Lowest Alert Rate", f"{lowest_alert:.3f}" if pd.notna(lowest_alert) else "-")

    st.divider()

    # -------------------------
    # Best Model Highlight
    # -------------------------
    best_model = filtered.sort_values("metrics.precision", ascending=False).iloc[0]

    st.success(
        f"🏆 Best Model: {best_model['model_family']} "
        f"(Precision={best_model.get('metrics.precision', '-')})"
    )

    # -------------------------
    # Charts
    # -------------------------
    st.subheader("📊 Model Comparison")

    fig = px.box(
        filtered,
        x="model_family",
        y="metrics.alert_rate",
        color="model_family",
    )
    st.plotly_chart(style_plotly_figure(fig), width="stretch")

    st.subheader("📈 Metric Trends")

    metric_names = get_metric_columns(filtered)
    metric = st.selectbox("Metric", metric_names)

    metric_col = f"metrics.{metric}"

    trend_df = filtered[filtered[metric_col].notna()]

    if not trend_df.empty:
        fig = px.scatter(
            trend_df.sort_values("start_time"),
            x="start_time",
            y=metric_col,
            color="model_family",
            symbol="run_stage",
        )
        st.plotly_chart(style_plotly_figure(fig), width="stretch")

    st.divider()

    # -------------------------
    # Recent Runs
    # -------------------------
    st.subheader("📄 Recent Runs")

    recent = build_recent_runs_table(filtered, metric_names)
    st.dataframe(recent.head(100), width="stretch")