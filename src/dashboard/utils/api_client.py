import json
import os

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from dashboard.settings import (
    TRANSPORT_FASTAPI,
    TRANSPORT_SAGEMAKER,
    get_fastapi_settings,
    get_inference_settings,
    get_sagemaker_settings,
    normalize_transport,
)

DEFAULT_TIMEOUT = 30
HEALTH_TIMEOUT = 2
SAGEMAKER_TIMEOUT = 60


def build_api_url(path: str) -> str:
    settings = get_fastapi_settings()
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{settings.base_url}{normalized_path}"


def build_sagemaker_runtime_client():
    settings = get_sagemaker_settings()
    return boto3.client(
        "sagemaker-runtime",
        region_name=settings.region_name,
        config=Config(connect_timeout=HEALTH_TIMEOUT, read_timeout=SAGEMAKER_TIMEOUT),
    )


def build_sagemaker_client():
    settings = get_sagemaker_settings()
    return boto3.client(
        "sagemaker",
        region_name=settings.region_name,
        config=Config(connect_timeout=HEALTH_TIMEOUT, read_timeout=DEFAULT_TIMEOUT),
    )


def check_fastapi_health() -> bool:
    settings = get_fastapi_settings()

    try:
        response = requests.get(build_api_url(settings.health_path), timeout=HEALTH_TIMEOUT)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_sagemaker_health() -> bool:
    settings = get_sagemaker_settings()
    if not settings.endpoint_name:
        return False

    try:
        response = build_sagemaker_client().describe_endpoint(EndpointName=settings.endpoint_name)
        return response.get("EndpointStatus") == "InService"
    except (BotoCoreError, ClientError):
        return False


def check_backend_health(transport: str | None = None) -> bool:
    selected_transport = normalize_transport(transport or get_inference_settings().default_transport)
    if selected_transport == TRANSPORT_SAGEMAKER:
        return check_sagemaker_health()
    return check_fastapi_health()


#def call_fastapi_inference(payload: dict) -> dict:
#    settings = get_fastapi_settings()
#    response = requests.post(
#        build_api_url(settings.predict_path),
#        json=payload,
#        headers={"Content-Type": "application/json"},
#        timeout=DEFAULT_TIMEOUT,
#    )
#    response.raise_for_status()
#
#    data = response.json()
#    if "results" not in data:
#        raise ValueError("Invalid response format: missing 'results'")
#
#    return data

def call_fastapi_inference(payload: dict) -> dict:
    settings = get_fastapi_settings()

    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("Missing API_KEY environment variable")

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,   # ✅ THIS FIXES 403
    }

    response = requests.post(
        build_api_url(settings.predict_path),
        json=payload,
        headers=headers,
        timeout=DEFAULT_TIMEOUT,
    )

    if response.status_code == 403:
        raise RuntimeError("Forbidden: API key missing or invalid")

    response.raise_for_status()

    data = response.json()
    if "results" not in data:
        raise ValueError("Invalid response format: missing 'results'")

    return data

def call_sagemaker_inference(payload: dict) -> dict:
    settings = get_sagemaker_settings()
    if not settings.endpoint_name:
        raise ValueError("SAGEMAKER_ENDPOINT_NAME is not configured.")

    response = build_sagemaker_runtime_client().invoke_endpoint(
        EndpointName=settings.endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    body = response["Body"].read()
    data = json.loads(body.decode("utf-8"))
    if "results" not in data:
        raise ValueError("Invalid response format: missing 'results'")

    return data


def call_inference(payload: dict, transport: str | None = None) -> dict:
    selected_transport = normalize_transport(transport or get_inference_settings().default_transport)
    if selected_transport == TRANSPORT_SAGEMAKER:
        return call_sagemaker_inference(payload)
    return call_fastapi_inference(payload)
