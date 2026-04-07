from dataclasses import dataclass
import os
from pathlib import Path

TRANSPORT_FASTAPI = "fastapi"
TRANSPORT_SAGEMAKER = "sagemaker"
TRANSPORT_OPTIONS = [TRANSPORT_FASTAPI, TRANSPORT_SAGEMAKER]


@dataclass(frozen=True)
class FastApiSettings:
    base_url: str
    health_path: str
    predict_path: str


@dataclass(frozen=True)
class SageMakerSettings:
    endpoint_name: str
    region_name: str


@dataclass(frozen=True)
class InferenceSettings:
    default_transport: str
    fastapi: FastApiSettings
    sagemaker: SageMakerSettings


@dataclass(frozen=True)
class MlflowSettings:
    tracking_uri: str
    default_experiment_name: str
    default_max_runs: int


def normalize_transport(value: str | None) -> str:
    normalized = (value or TRANSPORT_FASTAPI).strip().lower()
    if normalized in TRANSPORT_OPTIONS:
        return normalized
    return TRANSPORT_FASTAPI


def get_transport_label(transport: str) -> str:
    labels = {
        TRANSPORT_FASTAPI: "FastAPI",
        TRANSPORT_SAGEMAKER: "SageMaker Direct",
    }
    return labels.get(normalize_transport(transport), "FastAPI")


def get_inference_settings() -> InferenceSettings:
    return InferenceSettings(
        default_transport=normalize_transport(os.getenv("INFERENCE_TRANSPORT", TRANSPORT_FASTAPI)),
        fastapi=FastApiSettings(
            base_url=os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/"),
            health_path=os.getenv("API_HEALTH_PATH", "/"),
            predict_path=os.getenv("API_PREDICT_PATH", "/predict"),
        ),
        sagemaker=SageMakerSettings(
            endpoint_name=os.getenv("SAGEMAKER_ENDPOINT_NAME", "").strip(),
            region_name=(
                os.getenv("SAGEMAKER_REGION")
                or os.getenv("AWS_REGION")
                or os.getenv("AWS_DEFAULT_REGION")
                or "us-east-1"
            ),
        ),
    )


def _build_sqlite_uri(path: Path) -> str:
    return f"sqlite:///{path.resolve()}"


def _get_default_mlflow_tracking_uri() -> str:
    configured_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()
    if configured_uri:
        return configured_uri

    ui_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        ui_root.parent / "mlflow.db",
        ui_root / "mlflow.db",
    ]

    existing_path = next((path for path in candidate_paths if path.exists()), candidate_paths[0])
    return _build_sqlite_uri(existing_path)


def get_mlflow_settings() -> MlflowSettings:
    return MlflowSettings(
        tracking_uri=_get_default_mlflow_tracking_uri(),
        default_experiment_name=os.getenv("MLFLOW_EXPERIMENT_NAME", "anomaly-detection"),
        default_max_runs=int(os.getenv("MLFLOW_MAX_RUNS", "200")),
    )


def get_fastapi_settings() -> FastApiSettings:
    return get_inference_settings().fastapi


def get_sagemaker_settings() -> SageMakerSettings:
    return get_inference_settings().sagemaker


def get_api_settings() -> FastApiSettings:
    return FastApiSettings(
        base_url=os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/"),
        health_path=os.getenv("API_HEALTH_PATH", "/"),
        predict_path=os.getenv("API_PREDICT_PATH", "/predict"),
    )
