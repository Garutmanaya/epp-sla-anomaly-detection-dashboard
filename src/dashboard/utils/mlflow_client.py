from __future__ import annotations

import re

import mlflow
import pandas as pd
import streamlit as st
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient


def configure_tracking_uri(tracking_uri: str) -> str:
    normalized_uri = tracking_uri.strip()
    if not normalized_uri:
        raise ValueError("MLFLOW_TRACKING_URI is not configured.")

    mlflow.set_tracking_uri(normalized_uri)
    return normalized_uri


@st.cache_data(ttl=30, show_spinner=False)
def fetch_experiments(tracking_uri: str) -> pd.DataFrame:
    client = MlflowClient(tracking_uri=configure_tracking_uri(tracking_uri))
    experiments = client.search_experiments(view_type=ViewType.ACTIVE_ONLY)

    rows = [
        {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "artifact_location": experiment.artifact_location,
            "lifecycle_stage": experiment.lifecycle_stage,
        }
        for experiment in experiments
    ]

    return pd.DataFrame(rows)


@st.cache_data(ttl=30, show_spinner=False)
def fetch_runs(tracking_uri: str, experiment_ids: tuple[str, ...], max_results: int) -> pd.DataFrame:
    configure_tracking_uri(tracking_uri)
    if not experiment_ids:
        return pd.DataFrame()

    return mlflow.search_runs(
        experiment_ids=list(experiment_ids),
        max_results=max_results,
        order_by=["attributes.start_time DESC"],
        output_format="pandas",
    )


def clear_cached_mlflow_data() -> None:
    fetch_experiments.clear()
    fetch_runs.clear()


def _classify_model_family(run_name: str) -> str:
    normalized = run_name.lower()
    if "isolationforest" in normalized:
        return "isolationforest"
    if "xgboost" in normalized or normalized.startswith(("train_", "validate_", "thresholds_")):
        return "xgboost"
    return "unknown"


def _classify_run_stage(run_name: str) -> str:
    normalized = run_name.lower()
    if normalized.startswith("train_"):
        return "train"
    if normalized.startswith("validate_"):
        return "validate"
    if normalized.startswith("thresholds_"):
        return "thresholds"
    return "other"


def _extract_version(run_name: str) -> str:
    match = re.search(r"\b(v\d+)\b", run_name.lower())
    return match.group(1) if match else "unknown"


def prepare_runs_dataframe(runs_df: pd.DataFrame, experiments_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return runs_df

    prepared = runs_df.copy()
    experiment_lookup = (
        experiments_df.set_index("experiment_id")["name"].astype(str).to_dict()
        if not experiments_df.empty
        else {}
    )

    prepared["experiment_id"] = prepared["experiment_id"].astype(str)
    prepared["experiment_name"] = prepared["experiment_id"].map(experiment_lookup).fillna(prepared["experiment_id"])
    prepared["run_name"] = prepared.get("tags.mlflow.runName", prepared["run_id"].str[:8]).fillna(
        prepared["run_id"].str[:8]
    )
    prepared["model_family"] = prepared["run_name"].apply(_classify_model_family)
    prepared["run_stage"] = prepared["run_name"].apply(_classify_run_stage)
    prepared["version"] = prepared["run_name"].apply(_extract_version)
    prepared["start_time"] = pd.to_datetime(prepared["start_time"], errors="coerce")
    prepared["end_time"] = pd.to_datetime(prepared["end_time"], errors="coerce")
    prepared["duration_seconds"] = (
        (prepared["end_time"] - prepared["start_time"]).dt.total_seconds().round(2)
    )

    return prepared


def get_metric_columns(runs_df: pd.DataFrame) -> list[str]:
    return sorted(column.replace("metrics.", "") for column in runs_df.columns if column.startswith("metrics."))


def build_recent_runs_table(runs_df: pd.DataFrame, metric_columns: list[str]) -> pd.DataFrame:
    base_columns = [
        "run_name",
        "experiment_name",
        "model_family",
        "run_stage",
        "version",
        "status",
        "start_time",
        "duration_seconds",
    ]

    preferred_metrics = [
        "precision",
        "recall",
        "alert_rate",
        "best_factor",
        "adjusted_threshold",
        "raw_threshold",
        "score_mean",
        "score_std",
        "training_rows",
        "feature_count",
    ]

    metric_display_columns = []
    for metric in preferred_metrics:
        column_name = f"metrics.{metric}"
        if column_name in runs_df.columns:
            metric_display_columns.append(column_name)

    if not metric_display_columns:
        metric_display_columns = [f"metrics.{metric}" for metric in metric_columns[:5]]

    available_columns = [column for column in base_columns + metric_display_columns if column in runs_df.columns]
    return runs_df[available_columns].copy()
