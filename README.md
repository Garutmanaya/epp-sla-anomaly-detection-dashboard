# EPP SLA Anomaly Detection Dashboard

Interactive Streamlit dashboard for anomaly detection, model evaluation, and real-time alert simulation. This UI integrates with AWS backend services (API Gateway → Lambda → SageMaker Serverless) and supports MLflow-based experiment tracking.

---

## 🚀 Live Demo
https://epp-sla-anomaly-detection-dashboard-demo.streamlit.app/

---

## 🧩 Features
- Multi-model anomaly detection visualization  
- Real-time alert simulation  
- Model comparison and agreement analysis  
- MLflow experiment tracking and metrics insights  
- AWS-integrated inference pipeline  

---

## 📊 Dashboards

### 📊 Single Model
Analyze a single model’s behavior:
- Generate or upload data  
- Run inference  
- View anomalies, KPIs, trends, and root cause signals  

### 🧠 Compare Models
Compare multiple models side-by-side:
- Evaluate performance differences  
- Analyze overlap and agreement  
- Identify conflicting alerts  
- Compare alert distributions  

### 📈 MLflow Metrics
Explore experiment tracking data:
- View training, validation, and threshold runs  
- Filter by experiment, model, and run status  
- Track metrics over time  
- Identify best-performing models  

### ⏱️ Realtime Simulation
Simulate live alert streaming:
- Configurable number of records  
- Fixed or random alert intervals  
- Incremental alert display (latest on top)  
- Useful for demoing production-like behavior  

---

## 🏗️ Architecture
Streamlit UI → API Gateway → AWS Lambda → SageMaker Serverless → Docker (FastAPI + Models)

---

## ⚙️ Run Locally
cd epp-sla-anomaly-ui  
pip install -e .  
PYTHONPATH=src streamlit run src/dashboard/app.py  

---

## 🌐 Environment Variables
INFERENCE_TRANSPORT = fastapi (default) or sagemaker  
API_BASE_URL = API Gateway endpoint  
API_HEALTH_PATH = /  
API_PREDICT_PATH = /predict  
SAGEMAKER_ENDPOINT_NAME = required for direct mode  
SAGEMAKER_REGION = us-east-1 (default)  
MLFLOW_TRACKING_URI = local or remote MLflow  
MLFLOW_EXPERIMENT_NAME = anomaly-detection  
MLFLOW_MAX_RUNS = 200  

---

## ☁️ Streamlit Cloud Deployment
1. Push code to GitHub  
2. Go to https://share.streamlit.io  
3. Select repo and branch  
4. Main file path: src/dashboard/app.py  
5. Add environment variable:  
   API_BASE_URL=https://<api-id>.execute-api.<region>.amazonaws.com/prod/  
6. Deploy  

---

## 🧠 Backend Modes
- FastAPI (via API Gateway)  
- SageMaker Direct  

Switch using sidebar control.

---

## 📌 Notes
- Realtime simulation is UI-driven (not continuous backend calls)  
- MLflow can be local (mlflow.db) or remote server  
- Designed for demo + production-style monitoring  

---

## 📈 Future Enhancements
- Alert severity visualization  
- Live alert rate charts  
- Model drift detection  
- Automated best model selection  

---

## 👤 Author
SamNine
