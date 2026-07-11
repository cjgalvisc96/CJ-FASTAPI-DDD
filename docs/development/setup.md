# Development Setup

## Prerequisites

- **Python 3.14**
- **[uv](https://docs.astral.sh/uv/)** — environment & dependency manager
- **[go-task](https://taskfile.dev/)** — the task runner (`Taskfile.yml`)
- **Docker** + Docker Compose — for Postgres, Redis, Keycloak, and the app

## Bootstrap

```bash
task env:create      # uv venv + uv sync + copy .env.example → .env (if missing)
```

This creates the virtualenv, installs the `dev`/`test` dependency groups, and seeds a `.env`. Edit
`.env` to override any [`Settings`](../architecture/persistence.md) values (DB, Redis, Keycloak,
rate limits, CORS).

## Run it

=== "Full stack (recommended)"

    ```bash
    task docker:up      # postgres + redis + keycloak + atlas(migrate) + app
    ```

    - API docs: <http://localhost:8000/docs>
    - Keycloak: <http://localhost:8080>

    See [Docker Stack](../operations/docker.md) for service details and bring-up order.

=== "API only (local process)"

    ```bash
    task api            # runs ddd-api with reload; needs Postgres + Redis reachable
    ```

## Exercise the API without a token

With `DEBUG=true`, the `X-Dev-Roles` header fabricates an authenticated caller (see
[Auth & RBAC](../architecture/auth-rbac.md)):

```bash
curl -s -X POST localhost:8000/api/v1/users \
  -H 'X-Dev-Roles: admin' -H 'content-type: application/json' \
  -d '{"email":"a@b.com","full_name":"Ada Lovelace","role":"member"}'
```

## Entry points

Two console scripts are defined in `pyproject.toml`:

| Script | Task | Purpose |
| --- | --- | --- |
| `ddd-api` | `task api` | Run the FastAPI app (Uvicorn). |
| `ddd-seed` | `task seed:demo` | Idempotently seed demo users. |

## Taskfile targets

| Target | What it does |
| --- | --- |
| `env:create` | venv + deps + `.env` |
| `check:linter` | Ruff lint + format check |
| `check:types` | Pyright |
| `check:architecture` | `import-linter` contracts |
| `check:deadcode` | Vulture |
| `check:all` | Quality gate (lint, types, architecture, deadcode, bandit) |
| `remove:cache` | Remove tool caches |
| `test:all` / `test:coverage` | Run tests / with coverage |
| `docker:up` / `down` / `prune` / `logs` / `smoke` | Manage the stack |
| `atlas:migrate` / `status` / `hash` | Atlas migrations |
| `seed:demo` | Seed demo users |
| `api` | Run the API with reload |
| `docs:serve` / `docs:build` | MkDocs Material site |

## Inner loop

Before pushing, run the full gate:

```bash
task check:all        # lint, types, architecture, dead code, bandit
task test:coverage    # tests + coverage gate (>= 97%)
task trivy            # dependency CVEs + secrets + Dockerfile misconfig
```

See [Testing](testing.md) and [Governance](governance.md) for what that gate enforces.
