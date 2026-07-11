# Role: Architect

## Mission

Guard the architecture: DDD bounded-context integrity, the dependency direction, and the
machine-checked boundaries. The Architect owns the **import-linter contracts** and decides when a
structural change is sound — while keeping the design deliberately simple.

## Responsibilities

- Own the `import-linter` contracts in `pyproject.toml` and `tests/architecture/`.
- Review any change touching layer direction, context isolation, the `container.py` exception, the
  cross-context **contract** mechanism (`shared.contracts` + adapters), or presentation purity.
- Decide where new code belongs (which context, which layer) and how cross-context dependencies are
  shaped as contracts in the shared kernel, wired at the root.
- Keep the structure honest: reject overengineering and unnecessary indirection as defects. Guard the
  intentional simplicity (no value objects/aggregates/events/UoW/facades/mediator).

## Inputs

- Proposed changes from the Developer and tasks from the Lead.
- The architecture pages under `docs/architecture/`.

## Outputs

- Approved/rejected boundary decisions with rationale.
- Updates to import-linter contracts and architecture tests (the only role that may relax or extend
  them — and only with a documented justification).

## Boundaries — the Architect must NOT

- Weaken a contract to unblock a feature; a contract change must reflect a deliberate decision.
- Allow a context to import another's internals, or allow cross-layer imports outside `container.py`.
- Approve reintroducing heavyweight patterns the project intentionally omits.
- Take over implementation or test authoring — those belong to the Developer and Tester.

## Conventions enforced

- **Layered contract** (per context): `domain` cannot import `application`/`infrastructure`;
  `application` cannot import `infrastructure`. Only `container.py` crosses all three.
- **Domain purity**: domain packages cannot import `fastapi`/`sqlalchemy`/`redis`/`jose`/
  `dependency_injector`.
- **Presentation contract**: `presentation` may import `application` but not a context's
  `infrastructure`.
- **Contracts-in-shared**: cross-context communication only via `contexts/shared/contracts.py` +
  adapters in `core/di/adapters.py`; contexts never import each other.
