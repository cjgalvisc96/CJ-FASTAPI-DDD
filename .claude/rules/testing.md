# Rule: Testing

Enforced via `task test:all` / `task test:coverage` and the coverage gate. See
`docs/development/testing.md` for the full strategy.

## Coverage gate

- Overall coverage must be **≥ 97%** (`fail_under = 97` in `pyproject.toml`), measured on every run.
- A change that drops coverage below the threshold fails the gate. Do not lower the threshold to pass.

## Parallel + random by default

- Tests run in **parallel** (`pytest-xdist`, `-n auto --dist loadscope`) and in **randomized order**
  (`pytest-randomly`). Tests must be independent and order-agnostic — no shared mutable state, no
  reliance on execution order.

## Test tiers

- **Unit** (`tests/unit/`) — the bulk. Domain logic, use cases, serializers, middleware, and auth.
  Use cases are tested against **in-memory fakes** of repository/port interfaces, injected via the
  constructor — no DB, no network. The Keycloak verifier is tested by generating an RSA key and
  faking the JWKS endpoint (no live Keycloak).
- **Integration** (`tests/integration/`) — repositories, the cross-context contract, and the API
  (via `httpx` + `asgi-lifespan`) against a **SQLite-backed** DI container (`tests/conftest.py`).
  SQLite is **test-only**; production/dev persistence is Postgres.
- **Architecture** (`tests/architecture/test_boundaries.py`) — runs the `import-linter` contracts.

## Fakes for ports

- Unit-test use cases against in-memory fakes of the repository/port interfaces, never a real DB.

## When adding code

- Add tests in the same change as the code. A new use case ships with unit tests (happy/edge/error)
  using fakes; a new repository ships with an integration test. Keep coverage ≥ 97%.
