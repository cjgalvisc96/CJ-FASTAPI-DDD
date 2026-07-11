# Docker Stack

The whole system runs from one Compose file, `docker/docker-compose.yml`, on a dedicated bridge
network **`ddd-net`** so every service resolves the others by name and nothing leaks onto the host
default bridge.

## Services

| Service | Image | Host → container port | Role |
| --- | --- | --- | --- |
| `postgres` | `postgres:16` | **15432** → 5432 | Primary database (`ddd`/`ddd`/`ddd`), health-checked with `pg_isready`. |
| `redis` | `redis:7` | **16379** → 6379 | Cache + rate-limit store, health-checked with `redis-cli ping`. |
| `keycloak` | `quay.io/keycloak/keycloak:26.0` | **18080** → 8080 | OIDC provider; imports realm `ddd` on start (`--import-realm`). |
| `atlas` | `arigaio/atlas:latest` | — | **One-shot** migration runner. |
| `app` | multi-stage `Dockerfile` (`dev` target) | **18000** → 8000 | The FastAPI application. |
| `lgtm` | `grafana/otel-lgtm:latest` | **13000** → 3000, **14317/14318** → 4317/4318 | Observability backend (Grafana + Tempo + Loki + Prometheus); receives the app's [OpenTelemetry data](telemetry.md). |
| `floci` | `floci/floci:latest` (`infra` profile) | **14566** → 4566 | On-demand local AWS emulator for `ENV=local`. |

!!! note "Host ports are offset (+10000) so this stack coexists with sibling projects"
    Container-internal ports stay standard (5432/6379/8080/8000) — services reach each other by name
    over `ddd-net`. Only the **host-published** ports are offset, so a sibling stack (e.g.
    `CJ-DJANGO-MVC`) can run at the same time with no conflict. Each is overridable via
    `POSTGRES_HOST_PORT` / `REDIS_HOST_PORT` / `KEYCLOAK_HOST_PORT` / `APP_HOST_PORT` / `FLOCI_HOST_PORT`.

The `Dockerfile` is multi-stage with `base`, `builder`, `dev`, and `prod` targets; Compose builds
the `dev` target.

## Configuration

The `app` service reads the project `.env` via `env_file`, then overrides only the host names so it
reaches siblings by service name instead of `localhost`:

```yaml
env_file:
  - ../.env
environment:
  DB_HOST: postgres
  REDIS_HOST: redis
  KEYCLOAK_URL: http://keycloak:8080
```

## Bring-up order

`depends_on` conditions sequence startup so the app never boots against an unmigrated database:

```mermaid
flowchart LR
    PG[postgres<br/>healthy] --> AT[atlas<br/>migrate apply] --> APP[app]
    RD[redis<br/>healthy] --> APP
    KC[keycloak] --> APP
```

`atlas` waits for Postgres to be **healthy**, applies migrations from
`migrations/versions`, then exits; `app` waits for Postgres + Redis healthy **and** the atlas
migration to have `completed_successfully`.

## Everyday commands

```bash
task docker:up      # up -d --build; API → :18000/docs, Keycloak → :18080
task docker:down    # down -v (removes volumes, keeps images)
task docker:prune   # down -v --rmi local --remove-orphans + drop ddd-net
task docker:logs    # tail the app logs
task docker:smoke   # curl /health
```

`GET /health` pings both Postgres and Redis and returns 503 if either is down.

## Migrations (Atlas)

Beyond the one-shot container, Atlas commands run against the live Postgres via
[Atlas](../architecture/persistence.md):

```bash
task atlas:migrate   # apply pending migrations
task atlas:status    # show migration status
task atlas:hash      # recompute atlas.sum after editing versions
```

See [Setup](../development/setup.md) to get here from a clean checkout, and [CI](ci.md) for the
automated pipeline.
