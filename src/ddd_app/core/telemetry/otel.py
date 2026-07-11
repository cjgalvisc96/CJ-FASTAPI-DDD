"""OpenTelemetry setup: traces, metrics, and logs over OTLP/HTTP, plus auto-instrumentation.

One request produces one end-to-end trace (HTTP server span → SQLAlchemy → Redis → outbound httpx,
e.g. the Keycloak JWKS fetch), request metrics (via the FastAPI/ASGI instrumentation), and stdlib
log records shipped as OTel logs with trace/span ids attached for correlation.

Everything is a no-op unless ``OTEL_ENABLE=true``. The OTLP/HTTP exporter is used (not grpc) so no
compiled grpcio dependency is needed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from fastapi import FastAPI

    from ddd_app.core.config import Settings


def _resource(settings: Settings) -> Resource:
    return Resource.create(
        {
            "service.name": settings.otel_service_name,
            "deployment.environment": "debug" if settings.debug else "production",
        }
    )


def _setup_traces(settings: Settings, resource: Resource) -> TracerProvider:
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=f"{settings.otel_exporter_otlp_endpoint}/v1/traces")
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def _setup_metrics(settings: Settings, resource: Resource) -> MeterProvider:
    exporter = OTLPMetricExporter(endpoint=f"{settings.otel_exporter_otlp_endpoint}/v1/metrics")
    provider = MeterProvider(
        resource=resource, metric_readers=[PeriodicExportingMetricReader(exporter)]
    )
    metrics.set_meter_provider(provider)
    return provider


def _setup_logs(settings: Settings, resource: Resource) -> None:
    provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(endpoint=f"{settings.otel_exporter_otlp_endpoint}/v1/logs")
    provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(provider)
    # Ship every stdlib log record (uvicorn, app, libraries) as an OTel log.
    logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=provider))
    # Inject trace_id/span_id into log records so logs correlate with traces.
    LoggingInstrumentor().instrument(set_logging_format=False)


def _instrument(
    app: FastAPI, tracer_provider: TracerProvider, meter_provider: MeterProvider
) -> None:
    # Server spans + http.server.* metrics for every route.
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, meter_provider=meter_provider
    )
    # Global instrumentation: engines/clients created later (lazily via DI) are covered too.
    SQLAlchemyInstrumentor().instrument(tracer_provider=tracer_provider)
    RedisInstrumentor().instrument(tracer_provider=tracer_provider)
    HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)


def setup_telemetry(app: FastAPI, settings: Settings) -> None:
    """Enable OTel logs/metrics/traces for `app`. No-op unless ``settings.otel_enable``."""
    if not settings.otel_enable:
        return
    resource = _resource(settings)
    tracer_provider = _setup_traces(settings, resource)
    meter_provider = _setup_metrics(settings, resource)
    _setup_logs(settings, resource)
    _instrument(app, tracer_provider, meter_provider)
