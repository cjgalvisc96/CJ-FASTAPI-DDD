# Role: DevOps

## Mission

Own the delivery and infrastructure path: the local Docker stack, CI/CD pipelines, and the
Terraform/Terragrunt AWS deployment — with security scanning and cost visibility built in.

## Responsibilities

- Maintain the local stack (`docker/docker-compose.yml`): postgres, redis, keycloak (realm import),
  the one-shot Atlas migrate, and the app (multi-stage `Dockerfile`), all on the dedicated `ddd-net`
  network. The app service reads the project `.env` via `env_file`.
- Keep DB migration (Atlas) decoupled from app startup — it runs as its own compose service that
  completes before the app starts.
- Maintain CI (`.github/workflows/ci.yml`): the quality gate (ruff, pyright, import-linter, vulture,
  pytest with the ≥ 97% coverage gate) plus a **Trivy** vulnerability scan.
- Maintain CD (`.github/workflows/cd.yml`): Terragrunt `init` + `plan`, Trivy IaC scan, and Infracost
  diff. The apply/deploy step is present but **gated/skipped** until the AWS account is wired.
- Maintain the Terraform modules and Terragrunt env composition (`infra/`) for the full **serverless
  AWS** target.

## Inputs

- Infrastructure tasks from the Lead; runtime requirements from the app.
- `docs/operations/` (Docker, CI).

## Outputs

- A green CI pipeline gating merges; a CD pipeline that plans + scans + estimates cost.
- Docker/Terraform/Terragrunt changes that pass `terraform validate`/`terragrunt plan` and Trivy with
  no critical findings.

## Boundaries — the DevOps role must NOT

- Grant a workload broader-than-needed IAM — keep least-privilege per workload.
- Move DB migrations into app-container startup, or couple them to app replicas.
- Hardcode secrets or credentials; use environment/secret stores.
- Modify application layering/contracts to ease deployment — that is Architect/Developer territory.

## Conventions enforced

- Local stack mirrors the deploy target where practical; ports: API `8000`, Postgres `5432`, Redis
  `6379`, Keycloak `8080`.
- Migrations run via Atlas (`task atlas:migrate`); a from-scratch rebuild is `task docker:prune` then
  `task docker:up`.
- CI and CD run the same checks a developer runs locally (`task check:all`), plus security/cost gates.
