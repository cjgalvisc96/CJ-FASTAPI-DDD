"""Telemetry wiring: disabled is a true no-op; enabled wires providers + instrumentation."""

from __future__ import annotations

from typing import ClassVar

import pytest
from fastapi import FastAPI

from ddd_app.core.config import Settings
from ddd_app.core.telemetry import otel as otel_module
from ddd_app.core.telemetry import setup_telemetry


def test_disabled_is_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    """With OTEL_ENABLE=false nothing is constructed — no exporter, no instrumentation."""

    def boom(*args, **kwargs):  # pragma: no cover — must never run
        raise AssertionError("exporter constructed although telemetry is disabled")

    monkeypatch.setattr(otel_module, "OTLPSpanExporter", boom)
    monkeypatch.setattr(otel_module, "OTLPMetricExporter", boom)
    monkeypatch.setattr(otel_module, "OTLPLogExporter", boom)

    setup_telemetry(FastAPI(), Settings(_env_file=None, otel_enable=False))


def test_enabled_wires_instrumentation(monkeypatch: pytest.MonkeyPatch) -> None:
    """With OTEL_ENABLE=true the app gets instrumented and exporters point at the endpoint."""
    constructed: list[str] = []

    class _FakeExporter:
        def __init__(self, endpoint: str) -> None:
            constructed.append(endpoint)

        # Satisfy the exporter interfaces enough for provider construction.
        def export(self, *args, **kwargs):  # pragma: no cover
            return None

        def shutdown(self, *args, **kwargs):  # pragma: no cover
            return None

        def force_flush(self, *args, **kwargs):  # pragma: no cover
            return True

        # Metric exporter protocol attributes.
        _preferred_temporality: ClassVar[dict] = {}
        _preferred_aggregation: ClassVar[dict] = {}

    monkeypatch.setattr(otel_module, "OTLPSpanExporter", _FakeExporter)
    monkeypatch.setattr(otel_module, "OTLPLogExporter", _FakeExporter)
    monkeypatch.setattr(otel_module, "OTLPMetricExporter", _FakeExporter)

    # Swap the periodic reader (background export thread) for an in-memory one.
    from opentelemetry.sdk.metrics.export import InMemoryMetricReader

    monkeypatch.setattr(
        otel_module, "PeriodicExportingMetricReader", lambda exporter: InMemoryMetricReader()
    )

    class _FakeInstrumentor:
        calls: ClassVar[list[str]] = []

        def instrument(self, **kwargs) -> None:
            _FakeInstrumentor.calls.append(type(self).__name__)

    class _FakeSqla(_FakeInstrumentor): ...

    class _FakeRedis(_FakeInstrumentor): ...

    class _FakeHttpx(_FakeInstrumentor): ...

    class _FakeLogging(_FakeInstrumentor): ...

    monkeypatch.setattr(otel_module, "SQLAlchemyInstrumentor", _FakeSqla)
    monkeypatch.setattr(otel_module, "RedisInstrumentor", _FakeRedis)
    monkeypatch.setattr(otel_module, "HTTPXClientInstrumentor", _FakeHttpx)
    monkeypatch.setattr(otel_module, "LoggingInstrumentor", _FakeLogging)

    app = FastAPI()
    settings = Settings(
        _env_file=None, otel_enable=True, otel_exporter_otlp_endpoint="http://collector:4318"
    )
    setup_telemetry(app, settings)

    # Span/metric/log exporters constructed against the configured endpoint.
    assert "http://collector:4318/v1/traces" in constructed
    assert "http://collector:4318/v1/metrics" in constructed
    assert "http://collector:4318/v1/logs" in constructed
    # Global instrumentors invoked.
    assert {"_FakeSqla", "_FakeRedis", "_FakeHttpx", "_FakeLogging"} <= set(_FakeInstrumentor.calls)
    # FastAPI app instrumented (the instrumentation flags the app instance).
    assert getattr(app, "_is_instrumented_by_opentelemetry", False)
