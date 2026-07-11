"""Application settings (pydantic-settings) + a flat dict for the DI Configuration provider."""

from __future__ import annotations

from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    debug: bool = True
    log_level: str = "DEBUG"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ddd"
    db_user: str = "ddd"
    db_password: str = "ddd"  # noqa: S105 — local-dev default, overridden by DB_PASSWORD env in real envs
    db_pool_size: int = 10
    db_pool_max_overflow: int = 20
    db_echo: bool = False

    # Cache / Redis
    cache_enable: bool = True
    cache_namespaces: str = "users"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Rate limiting (Redis fixed window, per client IP) + request body size cap
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    max_request_body_bytes: int = 1_048_576  # 1 MiB

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "ddd"
    keycloak_client_id: str = "ddd-api"
    keycloak_verify_audience: bool = False

    # Optional explicit OIDC overrides (e.g. AWS Cognito, which has no /realms/<x> URL shape).
    # When empty, the effective values below are derived from the Keycloak settings.
    oidc_issuer: str = ""
    oidc_jwks_url: str = ""
    oidc_client_id: str = ""

    # CORS
    cors_allow_origins: str = "*"
    cors_allow_methods: str = "*"
    cors_allow_headers: str = "*"

    # OpenTelemetry — exports to an OTLP/HTTP collector (the compose stack ships Grafana LGTM).
    otel_enable: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:14318"
    otel_service_name: str = "cj-fastapi-ddd"

    @cached_property
    def database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @cached_property
    def redis_dsn(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cache_namespace_list(self) -> list[str]:
        return [n.strip() for n in self.cache_namespaces.split(",") if n.strip()]

    @staticmethod
    def _split(value: str) -> list[str]:
        return [v.strip() for v in value.split(",") if v.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return self._split(self.cors_allow_origins)

    @property
    def cors_method_list(self) -> list[str]:
        return self._split(self.cors_allow_methods)

    @property
    def cors_header_list(self) -> list[str]:
        return self._split(self.cors_allow_headers)

    # Effective OIDC values: explicit overrides win; otherwise derived from the Keycloak realm.
    @property
    def oidc_issuer_effective(self) -> str:
        return self.oidc_issuer or f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"

    @property
    def oidc_jwks_url_effective(self) -> str:
        return self.oidc_jwks_url or f"{self.oidc_issuer_effective}/protocol/openid-connect/certs"

    @property
    def oidc_client_id_effective(self) -> str:
        return self.oidc_client_id or self.keycloak_client_id

    def as_provider_dict(self) -> dict:
        """Flatten settings (incl. derived DSNs/lists) for the DI Configuration provider."""
        data = self.model_dump()
        data["database_dsn"] = self.database_dsn
        data["redis_dsn"] = self.redis_dsn
        data["cache_namespace_list"] = self.cache_namespace_list
        data["oidc_issuer_effective"] = self.oidc_issuer_effective
        data["oidc_jwks_url_effective"] = self.oidc_jwks_url_effective
        data["oidc_client_id_effective"] = self.oidc_client_id_effective
        return data


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
