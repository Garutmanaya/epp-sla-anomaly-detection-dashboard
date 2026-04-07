import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.settings import get_mlflow_settings
from dashboard.theme import apply_theme, initialize_theme_state, render_theme_selector, style_plotly_figure
from dashboard.utils.mlflow_client import (
    build_recent_runs_table,
    clear_cached_mlflow_data,
    fetch_experiments,
    fetch_runs,
    get_metric_columns,
    prepare_runs_dataframe,
)

initialize_theme_state()
apply_theme()


def _get_default_experiments(experiments_df, default_name: str) -> list[str]:
    if experiments_df.empty:
        return []
    if default_name in experiments_df["name"].tolist():
        return [default_name]
    return experiments_df["name"].head(1).tolist()


def _safe_latest_metric(runs_df: pd.DataFrame, stage: str, metric: str):
    stage_runs = runs_df[runs_df["run_stage"] == stage].sort_values("start_time", ascending=False)
    metric_column = f"metrics.{metric}"
    if stage_runs.empty or metric_column not in stage_runs.columns:
        return None

    valid_runs = stage_runs[stage_runs[metric_column].notna()]
    if valid_runs.empty:
        return None

    return valid_runs.iloc[0][metric_column]


def _build_model_summary(filtered_runs_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for model_name, model_runs in filtered_runs_df.groupby("model_family"):
        model_runs = model_runs.sort_values("start_time", ascending=False)
        latest_run = model_runs.iloc[0]

        rows.append(
            {
                "model_family": model_name,
                "total_runs": len(model_runs),
                "finished_runs": int((model_runs["status"] == "FINISHED").sum()),
                "failed_runs": int((model_runs["status"] == "FAILED").sum()),
                "latest_run": latest_run["run_name"],
                "latest_stage": latest_run["run_stage"],
                "latest_version": latest_run["version"],
                "latest_start_time": latest_run["start_time"],
                "latest_precision": _safe_latest_metric(model_runs, "validate", "precision"),
                "latest_recall": _safe_latest_metric(model_runs, "validate", "recall"),
                "latest_alert_rate": _safe_latest_metric(model_runs, "validate", "alert_rate"),
                "latest_threshold": _safe_latest_metric(model_runs, "train", "adjusted_threshold"),
                "latest_best_factor": _safe_latest_metric(model_runs, "thresholds", "best_factor"),
            }
        )

    return pd.DataFrame(rows).sort_values("model_family").reset_index(drop=True)


def _build_stage_summary(filtered_runs_df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for stage_name, stage_runs in filtered_runs_df.groupby("run_stage"):
        stage_runs = stage_runs.sort_values("start_time", ascending=False)
        latest_run = stage_runs.iloc[0]
        finished_runs = int((stage_runs["status"] == "FINISHED").sum())
        total_runs = len(stage_runs)

        rows.append(
            {
                "run_stage": stage_name,
                "total_runs": total_runs,
                "finished_runs": finished_runs,
                "failed_runs": int((stage_runs["status"] == "FAILED").sum()),
                "success_rate_pct": round((finished_runs / total_runs) * 100, 2) if total_runs else 0,
                "models_covered": stage_runs["model_family"].nunique(),
                "avg_duration_seconds": round(stage_runs["duration_seconds"].dropna().mean(), 2)
                if "duration_seconds" in stage_runs.columns and stage_runs["duration_seconds"].notna().any()
                else None,
                "latest_run": latest_run["run_name"],
                "latest_model": latest_run["model_family"],
                "latest_start_time": latest_run["start_time"],
                "avg_precision": round(stage_runs["metrics.precision"].dropna().mean(), 4)
                if "metrics.precision" in stage_runs.columns and stage_runs["metrics.precision"].notna().any()
                else None,
                "avg_recall": round(stage_runs["metrics.recall"].dropna().mean(), 4)
                if "metrics.recall" in stage_runs.columns and stage_runs["metrics.recall"].notna().any()
                else None,
                "avg_alert_rate": round(stage_runs["metrics.alert_rate"].dropna().mean(), 4)
                if "metrics.alert_rate" in stage_runs.columns and stage_runs["metrics.alert_rate"].notna().any()
                else None,
            }
        )

    return pd.DataFrame(rows).sort_values("run_stage").reset_index(drop=True)


def _build_run_highlights(filtered_runs_df: pd.DataFrame) -> pd.DataFrame:
    highlights = []

    candidates = [
        ("Best Precision", "validate", "metrics.precision", False),
        ("Best Recall", "validate", "metrics.recall", False),
        ("Lowest Alert Rate", "validate", "metrics.alert_rate", True),
        ("Latest Training Run", "train", "start_time", False),
        ("Latest Threshold Run", "thresholds", "start_time", False),
    ]

    for label, stage_name, sort_column, ascending in candidates:
        stage_runs = filtered_runs_df[filtered_runs_df["run_stage"] == stage_name].copy()
        if stage_runs.empty or sort_column not in stage_runs.columns:
            continue

        valid_runs = stage_runs[stage_runs[sort_column].notna()].copy()
        if valid_runs.empty:
            continue

        best_run = valid_runs.sort_values(sort_column, ascending=ascending).iloc[0]
        highlights.append(
            {
                "highlight": label,
                "run_name": best_run["run_name"],
                "model_family": best_run["model_family"],
                "version": best_run["version"],
                "stage": best_run["run_stage"],
                "status": best_run["status"],
                "value": best_run[sort_column],
                "start_time": best_run["start_time"],
            }
        )

    return pd.DataFrame(highlights)


st.subheader("📈 MLflow Metrics & Insights")
st.caption("Review training, thresholding, and validation runs from MLflow inside the dashboard.")

settings = get_mlflow_settings()

st.sidebar.header("📈 MLflow")
tracking_uri = st.sidebar.text_input("Tracking URI", value=settings.tracking_uri, key="mlflow_tracking_uri")
max_runs = st.sidebar.slider("Max Runs", min_value=25, max_value=1000, value=settings.default_max_runs, step=25)

if st.sidebar.button("Refresh MLflow Data", key="refresh_mlflow"):
    clear_cached_mlflow_data()

st.sidebar.divider()
render_theme_selector()

try:
    experiments_df = fetch_experiments(tracking_uri)
except Exception as exc:
    st.error(f"Could not connect to MLflow: {exc}")
    st.info(
        "Set `MLFLOW_TRACKING_URI` for the UI, or migrate existing `mlruns/` data into `mlflow.db` first."
    )
    st.stop()

if experiments_df.empty:
    st.warning("No MLflow experiments were found for the configured tracking URI.")
    st.stop()

default_experiments = _get_default_experiments(experiments_df, settings.default_experiment_name)
selected_experiment_names = st.sidebar.multiselect(
    "Experiments",
    options=experiments_df["name"].tolist(),
    default=default_experiments,
)

selected_experiment_ids = tuple(
    experiments_df.loc[experiments_df["name"].isin(selected_experiment_names), "experiment_id"]
    .astype(str)
    .tolist()
)

if not selected_experiment_ids:
    st.info("Select at least one MLflow experiment from the sidebar.")
    st.stop()

try:
    raw_runs_df = fetch_runs(tracking_uri, selected_experiment_ids, max_runs)
except Exception as exc:
    st.error(f"Could not load MLflow runs: {exc}")
    st.stop()

if raw_runs_df.empty:
    st.warning("No runs found for the selected experiments.")
    st.stop()

runs_df = prepare_runs_dataframe(raw_runs_df, experiments_df)
metric_names = get_metric_columns(runs_df)

status_options = sorted(runs_df["status"].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect("Run Status", options=status_options, default=status_options)

stage_options = sorted(runs_df["run_stage"].dropna().unique().tolist())
selected_stages = st.sidebar.multiselect("Run Stage", options=stage_options, default=stage_options)

model_options = sorted(runs_df["model_family"].dropna().unique().tolist())
selected_models = st.sidebar.multiselect("Model Family", options=model_options, default=model_options)

filtered_runs_df = runs_df[
    runs_df["status"].isin(selected_statuses)
    & runs_df["run_stage"].isin(selected_stages)
    & runs_df["model_family"].isin(selected_models)
].copy()

if filtered_runs_df.empty:
    st.warning("No runs matched the current filters.")
    st.stop()

st.caption(f"Tracking URI: `{tracking_uri}`")

latest_start_time = filtered_runs_df["start_time"].max()
finished_runs = int((filtered_runs_df["status"] == "FINISHED").sum())
failed_runs = int((filtered_runs_df["status"] == "FAILED").sum())
latest_run_label = latest_start_time.strftime("%Y-%m-%d %H:%M") if str(latest_start_time) != "NaT" else "-"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Filtered Runs", len(filtered_runs_df))
c2.metric("Finished", finished_runs)
c3.metric("Failed", failed_runs)
c4.metric("Latest Run", latest_run_label)

st.divider()

st.subheader("Summary By Model")
model_summary_df = _build_model_summary(filtered_runs_df)
st.dataframe(model_summary_df, width="stretch")

model_mix_fig = px.bar(
    model_summary_df,
    x="model_family",
    y=["finished_runs", "failed_runs"],
    barmode="group",
)
st.plotly_chart(style_plotly_figure(model_mix_fig), width="stretch")

st.divider()

st.subheader("Summary By Run Stage")
stage_summary_df = _build_stage_summary(filtered_runs_df)
st.dataframe(stage_summary_df, width="stretch")

stage_duration_df = stage_summary_df.dropna(subset=["avg_duration_seconds"])
if not stage_duration_df.empty:
    stage_duration_fig = px.bar(stage_duration_df, x="run_stage", y="avg_duration_seconds", color="run_stage")
    st.plotly_chart(style_plotly_figure(stage_duration_fig), width="stretch")

st.divider()

st.subheader("Run Highlights")
run_highlights_df = _build_run_highlights(filtered_runs_df)
if run_highlights_df.empty:
    st.info("No run highlights are available for the current filter.")
else:
    st.dataframe(run_highlights_df, width="stretch")

st.divider()

st.subheader("Run Mix")
run_mix_df = (
    filtered_runs_df.groupby(["run_stage", "model_family"])
    .size()
    .reset_index(name="runs")
    .sort_values(["run_stage", "model_family"])
)
run_mix_fig = px.bar(
    run_mix_df,
    x="run_stage",
    y="runs",
    color="model_family",
    barmode="group",
)
st.plotly_chart(style_plotly_figure(run_mix_fig), width="stretch")

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Latest Training Snapshot")
    training_runs_df = filtered_runs_df[filtered_runs_df["run_stage"] == "train"].copy()
    if training_runs_df.empty:
        st.info("No training runs in the current filter.")
    else:
        latest_training_df = (
            training_runs_df.sort_values("start_time", ascending=False)
            .drop_duplicates(["model_family"], keep="first")
        )
        training_columns = [
            column
            for column in [
                "run_name",
                "model_family",
                "version",
                "start_time",
                "metrics.training_rows",
                "metrics.feature_count",
                "metrics.adjusted_threshold",
                "metrics.score_mean",
                "metrics.score_std",
            ]
            if column in latest_training_df.columns
        ]
        st.dataframe(latest_training_df[training_columns], width="stretch")

with right_col:
    st.subheader("Latest Validation Snapshot")
    validation_runs_df = filtered_runs_df[filtered_runs_df["run_stage"] == "validate"].copy()
    if validation_runs_df.empty:
        st.info("No validation runs in the current filter.")
    else:
        latest_validation_df = (
            validation_runs_df.sort_values("start_time", ascending=False)
            .drop_duplicates(["model_family"], keep="first")
        )
        validation_columns = [
            column
            for column in [
                "run_name",
                "model_family",
                "version",
                "start_time",
                "metrics.precision",
                "metrics.recall",
                "metrics.alert_rate",
            ]
            if column in latest_validation_df.columns
        ]
        st.dataframe(latest_validation_df[validation_columns], width="stretch")

st.divider()

st.subheader("Metric Trends")
if not metric_names:
    st.info("No metric columns were found in the selected runs.")
else:
    default_metric = "alert_rate" if "alert_rate" in metric_names else metric_names[0]
    selected_metric = st.selectbox("Metric", options=metric_names, index=metric_names.index(default_metric))
    metric_column = f"metrics.{selected_metric}"

    metric_trend_df = filtered_runs_df[filtered_runs_df[metric_column].notna()].copy()
    if metric_trend_df.empty:
        st.info("The selected metric is not present in the current filtered runs.")
    else:
        trend_fig = px.scatter(
            metric_trend_df.sort_values("start_time"),
            x="start_time",
            y=metric_column,
            color="model_family",
            symbol="run_stage",
            hover_data=["run_name", "version", "status", "experiment_name"],
        )
        st.plotly_chart(style_plotly_figure(trend_fig), width="stretch")

st.divider()

st.subheader("Recent Runs")
recent_runs_table = build_recent_runs_table(filtered_runs_df.sort_values("start_time", ascending=False), metric_names)
st.dataframe(recent_runs_table.head(100), width="stretch")
