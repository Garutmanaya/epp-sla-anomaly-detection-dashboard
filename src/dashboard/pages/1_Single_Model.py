import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components.inference_selector import render_inference_transport_selector
from dashboard.theme import apply_theme, initialize_theme_state, style_plotly_figure
from dashboard.utils.api_client import call_inference
from dashboard.utils.dataframe_utils import build_inference_payload, load_uploaded_csv
from shared.data_dictionary import COMMAND_OPTIONS, MODEL_OPTIONS, NORMAL_STATUS, STATUS_OPTIONS
from shared.demo_data import generate_test_data


def init_state() -> None:
    defaults = {
        "single_df": None,
        "single_results": None,
        "single_meta": {},
        "single_last_model": None,
        "single_last_transport": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()
initialize_theme_state()
apply_theme()

st.subheader("🚨 Single Model Inference & Analysis")

st.sidebar.header("⚙️ Controls")
transport = render_inference_transport_selector()

model = st.sidebar.selectbox("Select Model", MODEL_OPTIONS, key="single_model_select")
mode = st.sidebar.radio("Mode", ["Generate Data", "Upload CSV"], key="single_mode")

st.sidebar.subheader("🔍 Filters")
selected_command = st.sidebar.multiselect("Command", COMMAND_OPTIONS, key="single_command_filter")
selected_status = st.sidebar.multiselect("Status", STATUS_OPTIONS, key="single_status_filter")

if mode == "Generate Data":
    hours = st.sidebar.slider("Hours", 24, 200, 48, key="single_hours")
    anomaly_prob = st.sidebar.slider("Anomaly Probability", 0.0, 0.5, 0.2, key="single_prob")

    if st.sidebar.button("Generate Data", key="single_generate"):
        st.session_state.single_df = generate_test_data(
            start_date=pd.Timestamp("2026-05-01"),
            hours=hours,
            anomaly_prob=anomaly_prob,
        )
        st.session_state.single_results = None
        st.session_state.single_meta = {}
        st.session_state.single_last_model = None
        st.session_state.single_last_transport = None

elif mode == "Upload CSV":
    file = st.sidebar.file_uploader("Upload CSV", type=["csv"], key="single_upload")
    if file is not None:
        try:
            st.session_state.single_df = load_uploaded_csv(file)
            st.session_state.single_results = None
            st.session_state.single_meta = {}
            st.session_state.single_last_model = None
            st.session_state.single_last_transport = None
        except Exception as exc:
            st.sidebar.error(f"Could not read CSV: {exc}")

df = st.session_state.single_df

if df is None:
    st.info("Generate or upload data to begin.")
    st.stop()

st.subheader("📄 Input Data Preview")
st.dataframe(df.head(50), width="stretch")

if st.sidebar.button("Run Analysis", key="single_run"):
    payload = build_inference_payload(df, [model])

    try:
        with st.spinner("Running inference..."):
            response = call_inference(payload, transport=transport)
    except Exception as exc:
        st.error(f"Inference call failed: {exc}")
        st.stop()

    st.session_state.single_results = pd.DataFrame(response["results"][model])
    st.session_state.single_meta = response["metadata"].get(model, {})
    st.session_state.single_last_model = model
    st.session_state.single_last_transport = transport

if st.session_state.single_results is None:
    st.info("Click Run Analysis to view results.")
    st.stop()

if st.session_state.single_last_model != model:
    st.info("Model selection changed. Click Run Analysis to refresh results.")
    st.stop()

if st.session_state.single_last_transport != transport:
    st.info("Inference route changed. Click Run Analysis to refresh results.")
    st.stop()

results = st.session_state.single_results.copy()
meta = st.session_state.single_meta

if selected_command:
    results = results[results["Command"].isin(selected_command)]

if selected_status:
    results = results[results["Status"].isin(selected_status)]

alerts_df = results[results["Status"] != NORMAL_STATUS]
total = len(results)
alerts = len(alerts_df)
alert_pct = (alerts / total * 100) if total else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Model", model.upper())
c2.metric("Total", total)
c3.metric("Alerts", alerts)
c4.metric("Alert %", f"{alert_pct:.2f}%")
c5.metric("Latency (ms)", meta.get("latency_ms", 0))

st.divider()

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
else:
    st.info("No anomalies")

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

st.subheader("🚨 Alerts")
st.dataframe(alerts_df.sort_values("Severity", ascending=False), width="stretch")

with st.expander("📄 Raw Input Data"):
    st.dataframe(df.head(100), width="stretch")

with st.expander("📄 Full Results"):
    st.dataframe(results.head(100), width="stretch")
