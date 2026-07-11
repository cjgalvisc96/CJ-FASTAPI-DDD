# Agent Harness

This project uses a **harness engineering** approach: work is carried out by a small team of
role-specialized agents, coordinated by a **Lead**. Each role has a charter in its `role.md` defining
its mission, responsibilities, inputs, outputs, and — importantly — its **boundaries** (what it must
not do).

## The team

| Role | File | Owns |
|------|------|------|
| **Lead** | [`lead/role.md`](lead/role.md) | Coordination, sequencing, final decisions |
| **Developer** | [`developer/role.md`](developer/role.md) | Implementation within the layering/context rules |
| **Architect** | [`architect/role.md`](architect/role.md) | DDD/architecture compliance, import-linter contracts |
| **Tester** | [`tester/role.md`](tester/role.md) | Test pyramid, parallel/random, coverage ≥ 97% |
| **DevOps** | [`devops/role.md`](devops/role.md) | Docker stack, CI/CD, Terraform/Terragrunt |

## How to use the roles

1. **Start with the Lead.** The Lead reads the request, breaks it into tasks, and delegates to the
   relevant role(s).
2. **Each role stays in its lane.** When a task crosses a boundary (e.g. a Developer change that would
   alter an import-linter contract), the role hands off to the owner (the Architect).
3. **The Architect guards the boundaries.** Any change touching layer direction, context isolation, or
   the cross-context contract mechanism goes through the Architect.
4. **The Tester gates correctness.** No change merges without the test pyramid passing and coverage
   ≥ 97% (parallel + random).
5. **DevOps owns the runtime.** Docker Compose, CI/CD, and the Terraform/Terragrunt AWS deployment.

## Shared conventions every role enforces

Documented in detail in `docs/` (`task docs:serve`) and `.claude/rules/`:

- **Dependency direction**: `domain → application → infrastructure`, never reversed. Only
  `container.py` may import across all three layers.
- **Context isolation via `shared.contracts`**: `users` and `shared` never import each other's
  internals as siblings; cross-context communication is through contracts declared in the shared
  kernel and wired at the root `ApplicationContainer`.
- **Presentation purity**: routers call `application/` use cases only; serializers map to/from DTOs,
  not ORM models.
- **CQRS, no Unit of Work**: explicit transactions on write routes (`async with session.begin()`).
- **Deliberate simplicity**: entities only (no value objects/aggregates/events); no speculative
  abstraction (KISS/YAGNI). Overengineering is a defect.
- **Auth/RBAC via Keycloak**; single-tenant (no RLS).
