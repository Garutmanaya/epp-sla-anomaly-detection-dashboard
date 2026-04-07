# EPP SLA Anomaly UI

Temporary standalone home for the Streamlit dashboard while it is being split out
from the main project.

## Run locally

```bash
cd epp-sla-anomaly-ui
pip install -e .
PYTHONPATH=src streamlit run src/dashboard/app.py
```

## Environment variables

- `INFERENCE_TRANSPORT` defaults to `fastapi`
- `API_BASE_URL` defaults to `http://localhost:8000`
- `API_HEALTH_PATH` defaults to `/`
- `API_PREDICT_PATH` defaults to `/predict`
- `SAGEMAKER_ENDPOINT_NAME` must be set for direct SageMaker mode
- `SAGEMAKER_REGION` defaults to `AWS_REGION`, `AWS_DEFAULT_REGION`, or `us-east-1`
- `MLFLOW_TRACKING_URI` defaults to the sibling backend database at `../mlflow.db`
- `MLFLOW_EXPERIMENT_NAME` defaults to `anomaly-detection`
- `MLFLOW_MAX_RUNS` defaults to `200`
