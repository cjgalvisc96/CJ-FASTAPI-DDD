# Command: quality-gate

Run the full pre-merge gate. This mirrors CI and must pass before any change is merged.

## Run

```bash
task check:all        # quality gates
task test:coverage    # tests + coverage gate
task trivy            # dependency CVEs + secrets + Dockerfile misconfig
```

`check:all` runs, in order: `check:linter` → `check:types` → `check:architecture` → `check:deadcode`
→ `bandit`. These mirror the CI `quality`, `test`, and `trivy` jobs respectively.

## What each step checks

| Step | Checks |
|------|--------|
| `check:linter` | ruff lint (incl. `S`/bandit rules) + `ruff format --check` (line length 100) |
| `check:types` | pyright (standard mode, Python 3.14) — no new type errors |
| `check:architecture` | `import-linter` contracts: layering per context, domain framework-free, presentation ↛ infrastructure |
| `check:deadcode` | vulture — no unreferenced code |
| `bandit` | Python SAST — no security findings in `src/` |
| `test:coverage` | full `pytest` run, parallel + random, **coverage gate ≥ 97%** |
| `trivy` | dependency CVEs, secrets, and Dockerfile misconfig |

## Pass criteria

- ruff: no lint errors, formatted.
- pyright: no new type errors.
- import-linter: all 4 contracts satisfied.
- vulture: no dead-code findings.
- coverage: **≥ 97%**.

## If it fails

- **Lint/type/dead-code** → fix the code; do not relax ruff/pyright/vulture config.
- **Architecture contract** → the violation is a real boundary break. Fix the imports/structure;
  changing a contract is the Architect's decision.
- **Coverage** → add the missing tests; do not lower the threshold.

Do not merge on a red gate.
