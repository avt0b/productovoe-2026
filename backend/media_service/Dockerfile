FROM python:3.12-slim

ARG SERVICE_MODULE=main:app
ARG SERVICE_PORT=8007

ENV SERVICE_MODULE=${SERVICE_MODULE} \
    SERVICE_PORT=${SERVICE_PORT} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY . .

EXPOSE ${SERVICE_PORT}

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
    CMD curl -fsS "http://localhost:${SERVICE_PORT}/health" || exit 1

CMD ["sh", "-lc", "exec /opt/venv/bin/python -m uvicorn ${SERVICE_MODULE} --host 0.0.0.0 --port ${SERVICE_PORT}"]