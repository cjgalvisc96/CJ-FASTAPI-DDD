---
name: add-bounded-context
description: >-
  Add a new bounded context as a DDD vertical slice (domain → application → infrastructure →
  container.py), communicating with other contexts ONLY through a contract in the shared kernel, then
  register it in the root ApplicationContainer, extend the import-linter contracts, and add tests.
---

# Skill: Add a Bounded Context

Use this when introducing a genuinely separate domain (a peer to `users`). A context owns a full
vertical slice and obeys the layering and isolation rules in `.claude/rules/architecture.md`.

## When NOT to use this

- If the capability belongs inside an existing context, add a use case instead (`add-use-case`). A new
  context is justified only by a separate domain — do not create one speculatively (YAGNI).

## Steps

### 1. Scaffold the vertical slice

```
contexts/<name>/
├── domain/
│   ├── entities/        # plain dataclasses, primitives only (NO value objects/aggregates/events)
│   ├── repositories/    # ABC ports
│   ├── services/
│   └── exceptions.py    # subclass the shared kernel exceptions
├── application/
│   ├── commands/        # writes
│   ├── queries/         # reads
│   └── dto/
├── infrastructure/
│   ├── db/models/       # SQLAlchemy models extending shared BaseModel
│   ├── db/repositories/ # implement the domain ports via current_session()
│   └── mappers/         # entity ↔ ORM model
└── container.py         # <Name>Container (composition root, sibling to the layers)
```

### 2. Build inside-out (domain first)

1. **Domain** — entities + repository ABCs. Framework-free.
2. **Application** — commands/queries/DTOs, constructor injection, single `async execute(...)`.
3. **Infrastructure** — model (register it in `shared/infrastructure/db/registry.py`), repository,
   mapper.

### 3. Cross-context needs go through `shared.contracts`

- If the new context consumes another context's data, declare a contract (ABC + DTO) in
  `contexts/shared/contracts.py`. The **provider** context is exposed via an adapter in
  `core/di/adapters.py` (the only place that imports a context's internals). **Never import the other
  context directly.**

### 4. Compose the container

- `contexts/<name>/container.py` wires the context's repositories, services, and use cases as
  providers. Declare any cross-context contract it consumes as `providers.Dependency()`.

### 5. Register in the root ApplicationContainer

In `core/di/container.py`, add `<name> = providers.Container(<Name>Container, config=config)`. If it
consumes a contract, build the adapter there (`providers.Factory(<Adapter>, ...)`) and inject it.

### 6. Extend import-linter contracts

In `pyproject.toml`, add a **layered** contract for the new context, add it to the **domain
framework-free** `source_modules`, and add its `infrastructure` to the presentation `forbidden_modules`.

### 7. Presentation (if exposed)

- Add `presentation/api/v1/<name>/{routers.py,serializers.py}` calling application use cases only.
  Writes wrap `async with session.begin()`; reads don't. Serializers map to/from DTOs.

### 8. Tests

- `tests/unit/` for domain + use cases with fakes; `tests/integration/` for repositories (SQLite);
  ensure `tests/architecture/` still passes. Keep coverage ≥ 97%.

## Verify

```bash
task check:architecture   # contracts pass (incl. the new context)
task check:all            # full gate
```
