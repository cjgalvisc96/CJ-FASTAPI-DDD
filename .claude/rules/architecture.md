# Rule: Architecture

Hard rules, enforced by `import-linter` (`task check:architecture`) and `tests/architecture/`. Do not
weaken a contract to make a change pass — fix the change.

## Dependency direction

Within every bounded context (`shared`, `users`):

```
domain → application → infrastructure   (never reversed)
```

- `domain/` is pure Python: entities (plain dataclasses with primitives — **no value objects, no
  aggregates, no domain events**), repository **interfaces** (ABCs), domain services, exceptions. No
  ORM, no Pydantic, no framework imports (`fastapi`/`sqlalchemy`/`redis`/`jose`/`dependency_injector`).
- `application/` depends only on `domain/` interfaces. Use cases are `commands/` (writes) and
  `queries/` (reads) — one class, constructor injection, a single `async execute(...)`, returning a
  DTO. **CQRS, and there is no Unit of Work.**
- `infrastructure/` implements the domain ports: SQLAlchemy models, repositories, mappers, external
  adapters (Keycloak for `users`).

## Only `container.py` crosses layers

Each context's `container.py` is the **only** module allowed to import across all three layers. It is
a **sibling** to `domain/`, `application/`, `infrastructure/` — never nested inside `infrastructure/`.

## Context isolation — contracts live in `shared`

- `users` and any future context must **not** import each other's internals. `shared` is the only
  common kernel.
- Cross-context communication goes through **contracts declared in `contexts/shared/contracts.py`**
  (ABCs + DTOs). The provider is exposed by an adapter in `core/di/adapters.py` — the only place
  allowed to import a context's internals — and wired into the root `ApplicationContainer`. Consumers
  receive it via `providers.Dependency()`. **No facades, no mediator, no direct cross-context import.**

## Transactions, not a Unit of Work

- A per-request `AsyncSession` is opened by the `get_session` dependency
  (`presentation/api/runtime.py`), which also sets the scoped-session contextvar. Repositories resolve
  it via `current_session()` and take no session argument.
- **Write routes** wrap the command in an explicit transaction: `async with session.begin(): ...`.
  **Read routes** just query. Never add a `UnitOfWork` class.

## Presentation purity

- `presentation/api/` calls `application/` use cases only — no business logic in routers.
- **Serializers map to/from application DTOs, never ORM models.**
- Domain exceptions are mapped to HTTP status in one place (`presentation/api/errors.py`); the domain
  stays framework-free.

## Auth & RBAC (Keycloak)

- Access tokens are verified against the realm JWKS (RS256) in
  `users/infrastructure/auth/keycloak.py`; roles come from `realm_access.roles`. Authorization is the
  `require_role(...)` dependency. Never put token parsing in the domain or a router body.

## Single-tenant

- There is no `tenant_id` and no row-level security. Do not add multi-tenancy speculatively (YAGNI).

See `docs/architecture/` for the full narrative.
