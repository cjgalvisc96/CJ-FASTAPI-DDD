"""OpenTelemetry wiring: logs, metrics, and traces exported over OTLP/HTTP.

Opt-in via ``OTEL_ENABLE`` (default off) so local runs and tests need no collector. When enabled,
`setup_telemetry` is called once from the entrypoint (after `create_app`), keeping app assembly
transport-pure. View the data ("reports") in Grafana at :13000 (ships with `task docker:up`).
"""

from ddd_app.core.telemetry.otel import setup_telemetry

__all__ = ["setup_telemetry"]
