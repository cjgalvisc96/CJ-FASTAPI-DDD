---
name: add-use-case
description: >-
  Add a command (write) or query (read) use case to an existing bounded context, with input/output
  DTOs, a repository method if needed, DI wiring, an API route, and tests — keeping CQRS and the
  no-Unit-of-Work transaction model.
---

# Skill: Add a Use Case

Use this to add behavior to an existing context (today: `users`). A use case lives in `application/`,
depends only on `domain/` interfaces, and is exposed through the API. Follow
`.claude/rules/architecture.md` and `.claude/rules/coding-style.md`.

## Decide: command or query?

- **Command** (`application/commands/`) — a **write** that mutates state (e.g. `RegisterUserCommand`).
- **Query** (`application/queries/`) — a **read** that returns data (e.g. `ListUsersQuery`).

## Steps

1. **DTOs** — in `application/dto/`, add the input and/or output DTOs (frozen dataclasses of
   primitives). Output DTOs get a `from_entity()` classmethod. DTOs are the application boundary,
   distinct from HTTP serializers.

2. **Repository method (if needed)** — add the abstract method to the domain ABC
   (`domain/repositories/…`) and implement it in `infrastructure/db/repositories/…`, resolving the
   session via `current_session()`. Add a fake implementation in `tests/unit/fakes.py`.

3. **Write the use case** — one class, constructor-inject its ports, a single `async execute(...)`
   returning a DTO. No DB/framework imports. Raise domain exceptions (mapped to HTTP centrally).

   ```python
   class RegisterUserCommand:
       def __init__(self, repository: UserRepository, uniqueness: EmailUniquenessChecker) -> None:
           self._repository = repository
           self._uniqueness = uniqueness

       async def execute(self, data: RegisterUserInput) -> UserOutput:
           ...
   ```

4. **Wire it** in the context `container.py` as a `providers.Factory`, injecting its repositories/
   services. If it needs another context's data, depend on a **`shared.contracts`** port (never import
   the other context) and receive the adapter via `providers.Dependency()` from the root container.

5. **Expose it** — add a route in `presentation/api/v1/<context>/routers.py`. Resolve the use case
   from the container. **Writes** wrap the call in `async with session.begin():`; **reads** call it
   directly. Map input/output via `serializers.py` (DTO-based, never ORM models). Cache reads with
   `cached(...)` and invalidate on the matching write if appropriate.

6. **Tests** — unit tests exercising the use case with in-memory fakes (happy/edge/error); an API
   test if it adds a route. Keep coverage ≥ 97%.

## Verify

```bash
task check:all   # lint, types, architecture, dead code, tests (≥ 97%)
```
