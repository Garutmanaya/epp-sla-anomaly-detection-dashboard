import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.inference_selector import render_inference_transport_selector
from dashboard.theme import apply_theme, initialize_theme_state, style_plotly_figure
from dashboard.utils.api_client import call_inference
from dashboard.utils.dataframe_utils import (
    add_alert_flags,
    build_inference_payload,
    build_status_comparison_table,
    load_uploaded_csv,
)
from shared.data_dictionary import MODEL_OPTIONS, NORMAL_STATUS
from shared.demo_data import generate_test_data


def init_state() -> None:
    defaults = {
        "compare_df": None,
        "compare_results": None,
        "compare_metadata": {},
        "compare_models_used": [],
        "compare_transport_used": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()
initialize_theme_state()
apply_theme()

st.subheader("🧠 Advanced Model Comparison")

st.sidebar.header("⚙️ Controls")
transport = render_inference_transport_selector()

models = st.sidebar.multiselect(
    "Select Models",
    MODEL_OPTIONS,
    default=MODEL_OPTIONS,
    key="compare_models_select",
)
mode = st.sidebar.radio("Mode", ["Generate Data", "Upload CSV"], key="compare_mode")

if mode == "Generate Data":
    hours = st.sidebar.slider("Hours", 24, 200, 48, key="compare_hours")
    anomaly_prob = st.sidebar.slider("Anomaly Probability", 0.0, 0.5, 0.2, key="compare_prob")

    if st.sidebar.button("Generate Data", key="compare_generate"):
        st.session_state.compare_df = generate_test_data(
            start_date=pd.Timestamp("2026-05-01"),
            hours=hours,
            anomaly_prob=anomaly_prob,
        )
        st.session_state.compare_results = None
        st.session_state.compare_metadata = {}
        st.session_state.compare_models_used = []
        st.session_state.compare_transport_used = None

elif mode == "Upload CSV":
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="compare_upload")
    if file is not None:
        try:
            st.session_state.compare_df = load_uploaded_csv(file)
            st.session_state.compare_results = None
            st.session_state.compare_metadata = {}
            st.session_state.compare_models_used = []
            st.session_state.compare_transport_used = None
        except Exception as exc:
            st.sidebar.error(f"Could not read CSV: {exc}")

df = st.session_state.compare_df

if df is None:
    st.warning("Generate or upload data")
    st.stop()

st.subheader("📄 Input Data Preview")
st.dataframe(df.head(50), width="stretch")

if st.sidebar.button("Run Analysis", key="compare_run"):
    if not models:
        st.warning("Select at least one model")
        st.stop()

    payload = build_inference_payload(df, models)

    try:
        with st.spinner("Running comparison..."):
            response = call_inference(payload, transport=transport)
    except Exception as exc:
        st.error(f"Inference call failed: {exc}")
        st.stop()

    st.session_state.compare_results = {
        model_name: pd.DataFrame(response["results"][model_name])
        for model_name in models
    }
    st.session_state.compare_metadata = response["metadata"]
    st.session_state.compare_models_used = list(models)
    st.session_state.compare_transport_used = transport

if st.session_state.compare_results is None:
    st.info("Click Run Analysis to compare the selected models.")
    st.stop()

if st.session_state.compare_models_used != models:
    st.info("Model selection changed. Click Run Analysis to refresh the comparison.")
    st.stop()

if st.session_state.compare_transport_used != transport:
    st.info("Inference route changed. Click Run Analysis to refresh the comparison.")
    st.stop()

results = st.session_state.compare_results
metadata = st.session_state.compare_metadata

st.subheader("📊 Model KPIs")
columns = st.columns(len(models))
for index, model_name in enumerate(models):
    model_results = results[model_name]
    total = len(model_results)
    alerts = (model_results["Status"] != NORMAL_STATUS).sum()
    alert_pct = (alerts / total * 100) if total else 0
    columns[index].metric(
        model_name.upper(),
        alerts,
        f"{alert_pct:.2f}% | {metadata[model_name]['latency_ms']} ms",
    )

st.divider()

st.subheader("⚙️ Model Metadata")
st.dataframe(pd.DataFrame(metadata).T, width="stretch")

st.subheader("🔗 Overlap & Agreement")
status_table = build_status_comparison_table(results, models)
status_table, alert_columns = add_alert_flags(status_table, models)

all_alert = int(status_table[alert_columns].all(axis=1).sum())
any_alert = int(status_table[alert_columns].any(axis=1).sum())
no_alert = int((~status_table[alert_columns].any(axis=1)).sum())
mixed_alert = any_alert - all_alert
agreement_count = int(status_table["Agreement"].sum())

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("All Alert", all_alert)
c2.metric("Mixed Alert", mixed_alert)
c3.metric("Any Alert", any_alert)
c4.metric("No Alert", no_alert)
c5.metric("Agreement Rows", agreement_count)

overlap_df = pd.DataFrame(
    {
        "Category": ["All Alert", "Mixed Alert", "Any Alert", "No Alert"],
        "Count": [all_alert, mixed_alert, any_alert, no_alert],
    }
)
fig = px.bar(overlap_df, x="Category", y="Count")
st.plotly_chart(style_plotly_figure(fig), width="stretch")

st.divider()

st.subheader("📈 Alerts Over Time")
timeseries_frames = []
for model_name in models:
    temp = results[model_name].copy()
    temp["Timestamp"] = pd.to_datetime(temp["Timestamp"], errors="coerce")
    temp = temp[temp["Status"] != NORMAL_STATUS]
    grouped = temp.groupby("Timestamp").size().reset_index(name="alerts")
    grouped["model"] = model_name
    timeseries_frames.append(grouped)

if timeseries_frames:
    ts_df = pd.concat(timeseries_frames, ignore_index=True)
    if not ts_df.empty:
        fig = px.line(ts_df, x="Timestamp", y="alerts", color="model")
        st.plotly_chart(style_plotly_figure(fig), width="stretch")
    else:
        st.info("No alerts detected across the selected models.")

st.divider()

st.subheader("📊 Root Cause Comparison")
columns = st.columns(len(models))
for index, model_name in enumerate(models):
    alerts_df = results[model_name][results[model_name]["Status"] != NORMAL_STATUS]
    if not alerts_df.empty:
        root_causes = alerts_df["Root_Cause"].value_counts().reset_index()
        root_causes.columns = ["Root_Cause", "Count"]
        fig = px.bar(root_causes, x="Root_Cause", y="Count", title=model_name)
        columns[index].plotly_chart(style_plotly_figure(fig), width="stretch")
    else:
        columns[index].info(f"No alerts for {model_name}.")

st.divider()

st.subheader("⚠️ Severity Distribution")
severity_frames = []
for model_name in models:
    temp = results[model_name].copy()
    temp["model"] = model_name
    severity_frames.append(temp)

severity_df = pd.concat(severity_frames, ignore_index=True)
fig = px.histogram(
    severity_df,
    x="Severity",
    color="model",
    nbins=30,
    barmode="overlay",
)
st.plotly_chart(style_plotly_figure(fig), width="stretch")

st.divider()

st.subheader("🧾 Agreement Table")
st.dataframe(status_table.head(100), width="stretch")

with st.expander("📄 Raw Results"):
    for model_name in models:
        st.subheader(model_name.upper())
        st.dataframe(results[model_name].head(50), width="stretch")
