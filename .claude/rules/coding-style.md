# Rule: Coding Style

Enforced by `task check:linter`, `check:types`, `check:deadcode` (ruff, pyright, vulture). Style is
checked, not optional.

## Formatting & imports

- **ruff** for linting and formatting; **line length 100**. Imports sorted by `ruff.lint.isort`
  (`known-first-party = ["ddd_app"]`). No unused imports. Rule set: `E,F,I,N,UP,B,C4,SIM,RUF`.

## Typing

- Type hints on public functions/methods. **pyright** (standard mode, Python 3.14) must pass with no
  new errors. Prefer precise types.

## Naming

- Modules/packages `snake_case`, classes `PascalCase`, functions/vars `snake_case`.
- Use cases are named for intent: `RegisterUserCommand`, `ChangeUserRoleCommand`, `ListUsersQuery`,
  `GetUserByIdQuery`. Ports read as capabilities: `UserRepository`, `UserDirectory`.

## Dead code

- **vulture** must not flag unreferenced code. Delete dead code rather than commenting it out.

## Design discipline — KISS, YAGNI (this project stays simple)

- This codebase deliberately uses the **lightest** pattern that keeps clean layering. Do **not**
  reintroduce value objects, aggregate roots, domain events, a Unit of Work, facades, or a mediator —
  their removal is intentional.
- Do not add abstraction, indirection, or a pattern for a hypothetical future need. Overengineering is
  treated as a **defect**, not sophistication. If a function does the job of a class, write the
  function.
- Constructor-inject dependencies (repositories, ports) — never instantiate an adapter inside a use
  case.
- Keep DTOs (application boundary) and serializers (HTTP boundary) as distinct objects that map
  cleanly, not the same class.
- Keep `domain/` free of framework concerns; if you reach for SQLAlchemy or Pydantic in `domain/`, it
  belongs in `infrastructure/` or the serializer layer instead.
