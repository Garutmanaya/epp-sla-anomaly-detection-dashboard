# =====================================
# STAGE 1: BUILDER
# =====================================
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        && rm -rf /var/lib/apt/lists/*


# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies globally (NO .venv)
RUN uv pip install --system --no-cache -r pyproject.toml

# =====================================
# STAGE 2: RUNTIME
# =====================================
FROM python:3.12-slim

WORKDIR /app/epp-sla-anomaly/

COPY --from=builder /usr/local /usr/local

# Copy app code
COPY src ./src/

ENV PYTHONPATH=/app/epp-sla-anomaly/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]


#================================================================================
# docker build -f docker/ui.Dockerfile -t epp-sla-hourly-anomaly-dashboard .
# run
# docker run -it  -p 8501:8501 epp-sla-hourly-anomaly-dashboard:latest
#=====================================================================================
