"""The AWS Lambda entrypoint: Mangum wrapping + Secrets Manager credential loading."""

from __future__ import annotations

import json
import sys
import types

import pytest

from ddd_app.presentation.api import lambda_handler

_ARN = "arn:aws:secretsmanager:us-east-1:000000000000:secret:test-db"


class _FakeSecretsClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.requested: list[str] = []

    def get_secret_value(self, SecretId: str) -> dict:  # noqa: N803 — boto3 API shape
        self.requested.append(SecretId)
        return {"SecretString": json.dumps(self._payload)}


def _install_fake_boto3(monkeypatch: pytest.MonkeyPatch, client: _FakeSecretsClient) -> None:
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.client = lambda service: client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)


def test_loads_credentials_from_secrets_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeSecretsClient({"username": "app_admin", "password": "s3cret-Pw_9"})
    _install_fake_boto3(monkeypatch, client)
    monkeypatch.setenv("DB_SECRET_ARN", _ARN)
    monkeypatch.setenv("DB_USER", "overwritten")
    monkeypatch.setenv("DB_PASSWORD", "overwritten")

    lambda_handler.load_db_credentials_from_secret()

    assert client.requested == [_ARN]
    import os

    assert os.environ["DB_USER"] == "app_admin"
    assert os.environ["DB_PASSWORD"] == "s3cret-Pw_9"


def test_noop_without_secret_arn(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DB_SECRET_ARN", raising=False)
    monkeypatch.setenv("DB_USER", "unchanged")

    lambda_handler.load_db_credentials_from_secret()

    import os

    assert os.environ["DB_USER"] == "unchanged"


def test_handler_is_mangum_wrapped_app() -> None:
    from mangum import Mangum

    assert isinstance(lambda_handler.handler, Mangum)
    assert callable(lambda_handler.handler)
    # The wrapped ASGI app is the FastAPI instance built by create_app().
    assert lambda_handler.handler.app is lambda_handler.app
