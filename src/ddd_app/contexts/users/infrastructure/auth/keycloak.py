"""Keycloak OIDC token verifier (RS256, JWKS-cached) providing auth + RBAC.

Verifies the access token's signature against the realm's published JWKS, checks issuer/expiry (and
optionally audience), then extracts the caller's identity and realm roles. Framework-agnostic: it
raises the shared `AuthenticationError` and knows nothing about HTTP.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from uuid import UUID

import httpx
from jose import jwt
from jose.exceptions import JWTError

from ddd_app.contexts.shared.domain.exceptions import AuthenticationError

_JWKS_TTL_SECONDS = 3600


@dataclass(frozen=True, slots=True)
class KeycloakClaims:
    subject: UUID
    email: str | None
    roles: frozenset[str] = field(default_factory=frozenset)


class KeycloakAuthenticator:
    def __init__(
        self,
        *,
        server_url: str,
        realm: str,
        client_id: str,
        verify_audience: bool = False,
    ) -> None:
        base = server_url.rstrip("/")
        self._issuer = f"{base}/realms/{realm}"
        self._jwks_url = f"{self._issuer}/protocol/openid-connect/certs"
        self._client_id = client_id
        self._verify_audience = verify_audience
        self._jwks: dict | None = None
        self._jwks_fetched_at = 0.0

    async def _get_jwks(self) -> dict:
        now = time.monotonic()
        jwks = self._jwks
        if jwks is None or now - self._jwks_fetched_at > _JWKS_TTL_SECONDS:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self._jwks_url)
                response.raise_for_status()
                jwks = response.json()
            self._jwks = jwks
            self._jwks_fetched_at = now
        return jwks

    @staticmethod
    def _find_key(jwks: dict, kid: str | None) -> dict:
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        raise AuthenticationError("Signing key not found in JWKS")

    async def verify(self, token: str) -> KeycloakClaims:
        try:
            header = jwt.get_unverified_header(token)
            jwks = await self._get_jwks()
            key = self._find_key(jwks, header.get("kid"))
            options = {"verify_aud": self._verify_audience}
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                issuer=self._issuer,
                audience=self._client_id if self._verify_audience else None,
                options=options,
            )
        except (JWTError, httpx.HTTPError, KeyError, ValueError) as exc:
            raise AuthenticationError(f"Invalid token: {exc}") from exc
        return self._to_claims(claims)

    @staticmethod
    def _to_claims(claims: dict) -> KeycloakClaims:
        raw_sub = claims.get("sub")
        if not raw_sub:
            raise AuthenticationError("Missing 'sub' claim")
        try:
            subject = UUID(str(raw_sub))
        except ValueError as exc:
            raise AuthenticationError(f"Non-UUID subject: {raw_sub}") from exc
        realm_roles = (claims.get("realm_access") or {}).get("roles") or []
        email = claims.get("email") or claims.get("preferred_username")
        return KeycloakClaims(
            subject=subject,
            email=email,
            roles=frozenset(str(r).lower() for r in realm_roles),
        )
