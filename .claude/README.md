# Claude Code Harness

This directory configures Claude Code for ongoing work on **CJ FastAPI DDD** — a deliberately simple
DDD modular monolith (FastAPI, async Postgres, Keycloak RBAC, Redis cache). It encodes the project's
hard rules, reusable skills, and the quality-gate command so an agent can contribute without
re-deriving the architecture each session.

## Contents

```
.claude/
├── rules/
│   ├── architecture.md     # layering, context isolation, contracts-in-shared, auth
│   ├── coding-style.md     # ruff/typing/naming, KISS/YAGNI (this project stays simple on purpose)
│   └── testing.md          # parallel + random, coverage ≥ 97%, fakes for ports
├── skills/
│   ├── add-use-case/SKILL.md          # add a command/query to the users context
│   └── add-bounded-context/SKILL.md   # add a new bounded context (+ a shared contract)
└── commands/
    └── quality-gate.md     # run the full quality + architecture + coverage gate
```

## How it is used

- **Rules** are always-on constraints. Before writing or changing code, read
  `rules/architecture.md`, `rules/coding-style.md`, and `rules/testing.md` and treat them as
  non-negotiable. They mirror the boundaries enforced by `import-linter` and the coverage gate.
- **Skills** are step-by-step procedures for recurring structural tasks. They keep new code
  consistent with the existing `users`/`shared` contexts.
- **Commands** are runnable workflows. `quality-gate` is the pre-merge check that mirrors CI.

## Deliberate simplicity

This project intentionally omits heavyweight DDD tactical patterns: **entities only** (no value
objects, aggregates, or domain events), **CQRS without a Unit of Work** (explicit transactions on
write routes), and **cross-context contracts in the `shared` kernel** (not facades/mediator). Do not
reintroduce those patterns "for completeness" — see `rules/coding-style.md` (KISS/YAGNI).

## Relationship to the agent harness

The role-based agent team lives under `.agents/` (Lead, Developer, Architect, Tester, DevOps). The
`.claude/` rules and skills are the concrete conventions those roles enforce — the Architect owns the
architecture rules and import-linter contracts, the Developer follows the skills, the Tester owns the
testing rule.

## Source of truth

These files operationalize the design in the `docs/` MkDocs site (`task docs:serve`). Where this
directory and the docs disagree, the docs win and these files should be updated.
