# CJ FastAPI DDD

A deliberately **simple** Domain-Driven Design **modular monolith** built with **FastAPI**, fully
`async/await` over **PostgreSQL**. It keeps the good structural practices (per-context DI containers,
strict layering, clean route → use-case → serializer flow, domain-exception → HTTP mapping, a
namespaced Redis cache) while dropping the heavyweight tactical patterns.

## What it is — and isn't

- **Two bounded contexts**: `users` (business context) + `shared` (kernel). Nothing else.
- **Entities only** — no value objects, no aggregate roots, no domain events. Entities hold plain
  primitives (`UUID`, `str`, `bool`).
- **CQRS, no Unit of Work** — commands (writes) and queries (reads) are the only use-case types. A
  per-request async session is opened by a dependency; **write routes** wrap the command in an
  explicit transaction (`async with session.begin()`), **read routes** don't.
- **Contracts live in the shared kernel** — bounded contexts never import each other; they depend only
  on `contexts/shared/contracts.py`. See [Cross-Context Contracts](architecture/contracts.md).
- **Auth + RBAC via Keycloak** — OIDC access tokens verified against the realm JWKS; roles from
  `realm_access.roles`. See [Auth & RBAC](architecture/auth-rbac.md).
- **Redis cache** in `shared` — namespaced, read-through, invalidated on writes.
- **Single-tenant** — no `tenant_id`, no row-level security.

## Read next

- [Architecture Overview](architecture/overview.md) — the big picture + a diagram.
- [Bounded Contexts](architecture/bounded-contexts.md) and [Layering](architecture/layering.md).
- [Cross-Context Contracts](architecture/contracts.md) — how contexts talk without importing each other.
- [Persistence & CQRS](architecture/persistence.md) — async sessions and transactions.
- [Development Setup](development/setup.md) — get it running.

## Quick start

```bash
task env:create      # uv venv + deps + .env
task docker:up       # postgres + redis + keycloak + atlas(migrate) + app
open http://localhost:18000/docs
```

With `DEBUG=true`, exercise the API locally without a token via the `X-Dev-Roles` header:

```bash
curl -s -X POST localhost:18000/api/v1/users \
  -H 'X-Dev-Roles: admin' -H 'content-type: application/json' \
  -d '{"email":"a@b.com","full_name":"Ada Lovelace","role":"member"}'
```

## Key constraints (enforced by tooling)

- **Dependency direction**: `domain → application → infrastructure`, never reversed
  (enforced by `import-linter`).
- **Context isolation**: contexts never import each other; they talk only through `shared.contracts`.
- **Presentation purity**: routes call `application/` use cases only; serializers map to/from DTOs,
  never ORM models.
- **Coverage**: the test suite runs in parallel + random order and gates at **≥ 97%**.

Stack: Python 3.14 · uv · FastAPI · SQLAlchemy 2.0 (async, asyncpg) · PostgreSQL · Redis · Keycloak ·
dependency-injector · Atlas · pytest · ruff · pyright · import-linter · Docker.
