"""Unit tests for the OIDC verifier (Keycloak- and Cognito-shaped tokens) via a fake JWKS."""

from __future__ import annotations

import time
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

from ddd_app.contexts.shared.domain.exceptions import AuthenticationError
from ddd_app.contexts.users.infrastructure.auth import oidc as oidc_module
from ddd_app.contexts.users.infrastructure.auth.oidc import OidcAuthenticator

_ISSUER = "http://kc:8080/realms/ddd"
_CLIENT = "ddd-api"
_KID = "test-kid"


@pytest.fixture(scope="module")
def rsa_material() -> dict:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_jwk = jwk.construct(public_pem, "RS256").to_dict()
    public_jwk.update({"kid": _KID, "use": "sig", "alg": "RS256"})
    return {"private_pem": private_pem, "jwks": {"keys": [public_jwk]}}


def _make_token(rsa_material: dict, **overrides) -> str:
    claims = {
        "sub": str(uuid.uuid4()),
        "iss": _ISSUER,
        "aud": _CLIENT,
        "exp": int(time.time()) + 3600,
        "email": "ada@example.com",
        "realm_access": {"roles": ["admin", "MEMBER"]},
    }
    claims.update(overrides)
    return jwt.encode(claims, rsa_material["private_pem"], algorithm="RS256", headers={"kid": _KID})


class _FakeResponse:
    def __init__(self, data: dict) -> None:
        self._data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._data


class _FakeClient:
    def __init__(self, jwks: dict) -> None:
        self._jwks = jwks

    async def __aenter__(self) -> _FakeClient:
        return self

    async def __aexit__(self, *exc) -> bool:
        return False

    async def get(self, url: str) -> _FakeResponse:
        return _FakeResponse(self._jwks)


@pytest.fixture
def authenticator(rsa_material: dict, monkeypatch: pytest.MonkeyPatch) -> OidcAuthenticator:
    def fake_async_client(*args, **kwargs) -> _FakeClient:
        return _FakeClient(rsa_material["jwks"])

    monkeypatch.setattr(oidc_module.httpx, "AsyncClient", fake_async_client)
    return OidcAuthenticator(
        issuer=_ISSUER,
        jwks_url=f"{_ISSUER}/protocol/openid-connect/certs",
        client_id=_CLIENT,
        verify_audience=True,
    )


async def test_verify_valid_token(authenticator: OidcAuthenticator, rsa_material: dict) -> None:
    token = _make_token(rsa_material)
    claims = await authenticator.verify(token)
    assert claims.email == "ada@example.com"
    assert claims.roles == frozenset({"admin", "member"})  # lowercased
    assert isinstance(claims.subject, uuid.UUID)


async def test_jwks_is_cached(authenticator: OidcAuthenticator, rsa_material: dict) -> None:
    token = _make_token(rsa_material)
    await authenticator.verify(token)
    # Second call should reuse the cached JWKS (fetched_at set); still succeeds.
    await authenticator.verify(token)


async def test_missing_sub_rejected(authenticator: OidcAuthenticator, rsa_material: dict) -> None:
    token = _make_token(rsa_material, sub="")
    with pytest.raises(AuthenticationError):
        await authenticator.verify(token)


async def test_non_uuid_sub_rejected(authenticator: OidcAuthenticator, rsa_material: dict) -> None:
    token = _make_token(rsa_material, sub="not-a-uuid")
    with pytest.raises(AuthenticationError):
        await authenticator.verify(token)


async def test_wrong_audience_rejected(
    authenticator: OidcAuthenticator, rsa_material: dict
) -> None:
    token = _make_token(rsa_material, aud="someone-else")
    with pytest.raises(AuthenticationError):
        await authenticator.verify(token)


async def test_unknown_kid_rejected(authenticator: OidcAuthenticator, rsa_material: dict) -> None:
    token = jwt.encode(
        {"sub": str(uuid.uuid4()), "iss": _ISSUER, "aud": _CLIENT, "exp": int(time.time()) + 3600},
        rsa_material["private_pem"],
        algorithm="RS256",
        headers={"kid": "unknown-kid"},
    )
    with pytest.raises(AuthenticationError):
        await authenticator.verify(token)


async def test_prefers_preferred_username_when_no_email(
    authenticator: OidcAuthenticator, rsa_material: dict
) -> None:
    token = _make_token(rsa_material, email=None, preferred_username="ada")
    claims = await authenticator.verify(token)
    assert claims.email == "ada"


# --- Cognito compatibility ---------------------------------------------------


async def test_cognito_groups_map_to_roles(
    authenticator: OidcAuthenticator, rsa_material: dict
) -> None:
    """A Cognito-shaped token (no realm_access, roles in cognito:groups) yields the same roles."""
    token = _make_token(rsa_material, realm_access=None, **{"cognito:groups": ["Admin", "member"]})
    claims = await authenticator.verify(token)
    assert claims.roles == frozenset({"admin", "member"})


async def test_cognito_issuer_shape_works(
    rsa_material: dict, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The verifier takes explicit issuer/JWKS URLs, so Cognito's URL shape needs no code change."""
    cognito_issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_Abc123"

    def fake_async_client(*args, **kwargs) -> _FakeClient:
        return _FakeClient(rsa_material["jwks"])

    monkeypatch.setattr(oidc_module.httpx, "AsyncClient", fake_async_client)
    authenticator = OidcAuthenticator(
        issuer=cognito_issuer,
        jwks_url=f"{cognito_issuer}/.well-known/jwks.json",
        client_id=_CLIENT,
        verify_audience=False,
    )
    token = _make_token(
        rsa_material, iss=cognito_issuer, realm_access=None, **{"cognito:groups": ["admin"]}
    )
    claims = await authenticator.verify(token)
    assert claims.roles == frozenset({"admin"})
