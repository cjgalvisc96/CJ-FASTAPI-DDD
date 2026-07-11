# CJ FastAPI DDD — Simple Modular Monolith

A deliberately **simple** Domain-Driven Design modular monolith built with **FastAPI**, fully
`async/await` over **PostgreSQL**. It keeps the "nice practices" (per-context DI containers, strict
`domain → application → infrastructure` layering, clean route → use-case → serializer flow,
domain-exception → HTTP mapping, namespaced Redis cache) but drops the heavyweight tactical patterns.

## What it is (and isn't)

- **Bounded contexts**: `users` (business context) + `shared` (kernel). That's it.
- **Entities only** — no value objects, no aggregate roots, no domain events. Entities hold plain
  primitives (`UUID`, `str`, `bool`).
- **CQRS, no Unit of Work** — commands (writes) and queries (reads) are the only use-case types.
  A per-request async session is opened by the `get_session` dependency; **write routes** wrap the
  command in an explicit transaction (`async with session.begin()`), **read routes** don't.
- **Simple contracts in the shared kernel** — bounded contexts never import each other. Cross-context
  contracts (ABCs + DTOs) live in `contexts/shared/contracts.py`; a provider context is exposed through
  an adapter in `core/di/adapters.py` (the only place allowed to import a context's internals), and a
  consumer depends only on `shared.contracts`. No facades/mediator. (`users` publishes the
  `UserDirectory` contract; it's the only business context today.)
- **Auth + RBAC via Keycloak** — OIDC access tokens verified against the realm JWKS; roles read from
  `realm_access.roles`.
- **Redis cache** lives in `shared` (namespaced, read-through helper, explicit invalidation on writes).
- **Single-tenant** — no `tenant_id`, no row-level security.

## Stack

Python 3.14 · uv · FastAPI · SQLAlchemy 2.0 (async, asyncpg) · PostgreSQL · Redis · Keycloak ·
dependency-injector · Atlas (migrations) · pytest · ruff · pyright · import-linter · Docker.

## Layout

| Path | Purpose |
|---|---|
| `src/ddd_app/contexts/` | Bounded contexts — each a vertical `domain/application/infrastructure/container.py` slice |
| `src/ddd_app/core/` | Config, DI root (`ApplicationContainer`), logging |
| `src/ddd_app/presentation/` | FastAPI app (routes, serializers, middleware) — calls application use cases only |
| `src/ddd_app/scripts/` | One-shot ops entry points (demo seeder) |
| `migrations/` | Atlas versioned SQL migrations |
| `tests/` | unit / integration / architecture (parallel + random, ≥97% coverage) |
| `docker/` | docker-compose stack (postgres, redis, keycloak, app, atlas) on the `ddd-net` network |
| `docs/` | MkDocs Material documentation site (`task docs:serve`) |
| `infra/` | Terraform modules + Terragrunt (dev/prod) for a serverless AWS deployment |
| `.github/workflows/` | CI (quality gate + Trivy) and CD (Terragrunt plan + Trivy + Infracost) |
| `.claude/`, `.agents/` | Claude Code harness (rules, skills, command) + role-based agent team |

## Cross-cutting features

- **Middleware**: Redis fixed-window **rate limiting** (fail-open, exempts health/docs) and a
  **request body-size cap** (413). Configurable via `RATE_LIMIT_*` / `MAX_REQUEST_BODY_BYTES`.
- **Quality gate**: `task check:all` runs ruff, pyright, import-linter, vulture, and bandit;
  `task test:coverage` runs the parallel/random test suite (coverage ≥ 97%); `task trivy` scans the
  app for dependency CVEs, secrets, and Dockerfile misconfig.
- **Telemetry**: OpenTelemetry logs + metrics + traces (`src/ddd_app/core/telemetry/`, opt-in via
  `OTEL_ENABLE`), viewed in Grafana at http://localhost:13000 (ships with `task docker:up`).
- **Docs**: a full MkDocs Material site under `docs/` — `task docs:serve` → http://127.0.0.1:8002.

## Quick start

```bash
task env:create      # uv venv + deps + .env
task docker:up       # postgres + redis + keycloak + atlas(migrate) + app
open http://localhost:18000/docs
```

Local dev without a Keycloak token: with `DEBUG=true`, send `X-Dev-Roles: admin` to impersonate roles.

```bash
curl -s -X POST localhost:18000/api/v1/users \
  -H 'X-Dev-Roles: admin' -H 'content-type: application/json' \
  -d '{"email":"a@b.com","full_name":"Ada Lovelace","role":"member"}'
```

## Cross-context contract convention

Bounded contexts **never import each other**. They communicate only through contracts declared in the
**shared** kernel (`contexts/shared/contracts.py`):

1. The shared kernel declares a narrow contract (an ABC) + its own DTO in `shared/contracts.py`
   (e.g. `UserDirectory` / `UserRef`).
2. The **provider** context is exposed through an adapter in `core/di/adapters.py` (the only place
   allowed to import a context's internals), implementing that contract from the provider's repository.
3. The **consumer** context depends only on `shared.contracts` and receives the implementation via
   `providers.Dependency()` in its own container, wired at the root `ApplicationContainer`.

So the dependency direction is always *context → shared kernel*, never context → sibling context. The
only file that sees two contexts at once is the composition root.

## Documentation

A full MkDocs Material site lives under `docs/` (architecture, middleware, infrastructure,
development, operations):

```bash
task docs:serve   # serve locally → http://127.0.0.1:8002
task docs:build   # build the static site (--strict)
```

## Quality gate

```bash
task check:all        # ruff + pyright + import-linter + vulture + bandit
task test:coverage    # parallel + random tests, coverage >= 97%
task trivy            # dependency CVEs + secrets + Dockerfile misconfig
```
