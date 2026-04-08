# EPP Hourly SLA Anomaly Detection Dashboard

Lightweight Streamlit-based dashboard for EPP SLA  anomaly detection insights, model comparison, and ML experiment tracking.

---

## Available Dashboards

* 📊 **Single Model** → Analyze predictions, thresholds, and anomalies for a single model
* 🧠 **Compare Models** → Compare performance across multiple models
* 📈 **MLflow Metrics** → Review training runs, validation metrics, and thresholds

---

## Run Locally

```bash
cd epp-sla-anomaly-detection-dashboard
uv sync 
PYTHONPATH=src streamlit run src/dashboard/app.py
```

---

## Environment Variables

* `INFERENCE_TRANSPORT` → default: `fastapi`
* `API_BASE_URL` → default: `http://localhost:8000`
* `API_HEALTH_PATH` → default: `/`
* `API_PREDICT_PATH` → default: `/predict`
* `SAGEMAKER_ENDPOINT_NAME` → required for direct SageMaker mode
* `SAGEMAKER_REGION` → default: `us-east-1`
* `MLFLOW_TRACKING_URI` → default: `../mlflow.db`
* `MLFLOW_EXPERIMENT_NAME` → default: `anomaly-detection`
* `MLFLOW_MAX_RUNS` → default: `200`

---

## Streamlit Cloud Deployment

App URL:
https://epp-sla-anomaly-detection-dashboard-demo.streamlit.app/

Steps:

1. Push code to **GitHub**
2. Deploy via **Streamlit Community Cloud**
3. Set Secrets:

```toml
API_BASE_URL="https://xxxxxx.us-east-1.amazonaws.com/prod/"
```

4. Use in code:

```python
API_BASE_URL = st.secrets["API_BASE_URL"]
```

---

## System Architecture Flow

```
Streamlit App
     ↓
API Gateway
     ↓
Lambda
     ↓
SageMaker Serverless Endpoint
     ↓
Docker (FastAPI + Models)
```

---

## Notes

* UI is stateless; all inference handled via API
* Supports both FastAPI and SageMaker backends
* Designed for modular separation from core ML pipeline

