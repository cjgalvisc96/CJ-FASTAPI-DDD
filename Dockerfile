# syntax=docker/dockerfile:1
FROM python:3.14-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
WORKDIR /app

FROM base AS builder
# README.md is required by hatchling (pyproject `readme = "README.md"`) when the project wheel builds.
COPY pyproject.toml uv.lock* README.md ./
# Runtime venv only: project deps + `observability` (OTel is imported at startup) + `aws` (Lambda
# stage). `--no-default-groups` keeps dev/test tooling (pytest, ruff, …) OUT of the shipped images.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-default-groups --group aws --group observability
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable --no-default-groups --group aws --group observability

FROM base AS dev
COPY --from=builder /opt/venv /opt/venv
COPY . .
ENV API_RELOAD=1
EXPOSE 8000
CMD ["ddd-api"]

FROM base AS prod
COPY --from=builder /opt/venv /opt/venv
COPY src ./src
COPY migrations ./migrations
RUN useradd --uid 1000 --create-home appuser
USER appuser
EXPOSE 8000
CMD ["ddd-api"]

# AWS Lambda container image: awslambdaric (runtime interface client) drives the Mangum-wrapped app
# (ddd_app.presentation.api.lambda_handler). The venv already contains the project wheel plus the
# `aws` dependency group (mangum, boto3, awslambdaric) from the builder.
FROM base AS lambda
COPY --from=builder /opt/venv /opt/venv
RUN useradd --uid 1000 --create-home appuser
USER appuser
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["ddd_app.presentation.api.lambda_handler.handler"]
