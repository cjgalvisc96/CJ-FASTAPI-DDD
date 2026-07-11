from __future__ import annotations

from ddd_app.core.config import Settings, get_settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_database_dsn() -> None:
    s = _settings(db_user="u", db_password="p", db_host="h", db_port=1234, db_name="d")
    assert s.database_dsn == "postgresql+asyncpg://u:p@h:1234/d"


def test_redis_dsn_without_password() -> None:
    s = _settings(redis_host="h", redis_port=6380, redis_db=2, redis_password="")
    assert s.redis_dsn == "redis://h:6380/2"


def test_redis_dsn_with_password() -> None:
    s = _settings(redis_host="h", redis_port=6380, redis_db=0, redis_password="secret")
    assert s.redis_dsn == "redis://:secret@h:6380/0"


def test_cache_namespace_list() -> None:
    s = _settings(cache_namespaces=" users, tasks ,, ")
    assert s.cache_namespace_list == ["users", "tasks"]


def test_cors_lists() -> None:
    s = _settings(cors_allow_origins="a,b", cors_allow_methods="GET,POST", cors_allow_headers="X")
    assert s.cors_origin_list == ["a", "b"]
    assert s.cors_method_list == ["GET", "POST"]
    assert s.cors_header_list == ["X"]


def test_oidc_effective_derived_from_keycloak() -> None:
    s = _settings(
        keycloak_url="http://kc:8080/", keycloak_realm="ddd", keycloak_client_id="ddd-api"
    )
    assert s.oidc_issuer_effective == "http://kc:8080/realms/ddd"
    assert s.oidc_jwks_url_effective == "http://kc:8080/realms/ddd/protocol/openid-connect/certs"
    assert s.oidc_client_id_effective == "ddd-api"


def test_oidc_explicit_overrides_win() -> None:
    issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Abc123"
    s = _settings(
        oidc_issuer=issuer,
        oidc_jwks_url=f"{issuer}/.well-known/jwks.json",
        oidc_client_id="cognito-client",
    )
    assert s.oidc_issuer_effective == issuer
    assert s.oidc_jwks_url_effective == f"{issuer}/.well-known/jwks.json"
    assert s.oidc_client_id_effective == "cognito-client"


def test_as_provider_dict_has_derived_values() -> None:
    data = _settings().as_provider_dict()
    assert data["database_dsn"].startswith("postgresql+asyncpg://")
    assert data["oidc_issuer_effective"].endswith("/realms/ddd")
    assert data["redis_dsn"].startswith("redis://")
    assert isinstance(data["cache_namespace_list"], list)


def test_get_settings_is_singleton() -> None:
    assert get_settings() is get_settings()
