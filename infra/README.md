# Infrastructure — `cj-fastapi-ddd`

Terraform + Terragrunt IaC for deploying the FastAPI service (`ddd-api`) to AWS as a
**full serverless** stack. No always-on servers: the app runs as a container image on
AWS Lambda behind an HTTP API, with Aurora Serverless v2, ElastiCache Serverless, and
Cognito for OIDC.

```
Client ──HTTPS──▶ API Gateway (HTTP API) ──AWS_PROXY──▶ Lambda (container, arm64, Mangum)
                                                          │  (in VPC private subnets)
                                                          ├─▶ Aurora Serverless v2 (PostgreSQL)
                                                          ├─▶ ElastiCache Serverless (Valkey/Redis)
                                                          ├─▶ Secrets Manager (DB creds, app config)
                                                          └─▶ Cognito (OIDC issuer / JWKS)
```

## Modules (`terraform/modules/`)

| Module    | What it creates |
|-----------|-----------------|
| `network` | VPC (10.0.0.0/16), 2 AZs, public+private subnets, IGW, **single NAT gateway** (toggle), route tables, S3 gateway VPC endpoint, shared app/Lambda security group. |
| `ecr`     | ECR repo — scan-on-push, `IMMUTABLE` tags, lifecycle policy keeping the last 10 images. |
| `secrets` | Secrets Manager secrets for DB credentials (password via `random_password`) and app config. |
| `aurora`  | Aurora Serverless v2 PostgreSQL (`provisioned` + `serverlessv2_scaling_configuration`), one `db.serverless` writer, encrypted, private SG (5432 from app SG only). |
| `cache`   | ElastiCache Serverless for **Valkey**, private SG (6379 from app SG only), usage limits to cap spend. |
| `cognito` | Cognito user pool + app client + hosted-UI domain + `admin`/`member` groups (serverless-native OIDC). |
| `api`     | Lambda (container image, **arm64/Graviton**) in the VPC, least-privilege IAM role, HTTP API + `$default` route/stage, Lambda permission, CloudWatch log group with bounded retention. |

Each module has `variables.tf`, `main.tf`, `outputs.tf`, and its own `versions.tf`.
Provider blocks live **only** in Terragrunt-generated files, never in the modules.

## Cognito vs. Keycloak (auth note)

This stack ships a **Cognito** user pool as the serverless-native OIDC IdP, and the app's
verifier is **IdP-agnostic**: it accepts explicit `OIDC_ISSUER` / `OIDC_JWKS_URL` /
`OIDC_CLIENT_ID` (which the `api` module injects from the cognito module's outputs) and reads
roles from `realm_access.roles` (Keycloak) **and/or** `cognito:groups` (Cognito). Pointing the
same variables at a hosted Keycloak realm switches IdPs with no code change. The `cognito`
module documents the serverless-native option (no Keycloak servers to run or patch).

## App container contract

- Listens on port **8000**, exposes `GET /health`.
- Console script `ddd-api` runs uvicorn locally; the image CMD is overridable.
- On Lambda it runs behind **Mangum**: the `lambda` Docker stage bakes
  `ENTRYPOINT python -m awslambdaric` + `CMD ddd_app.presentation.api.lambda_handler.handler`;
  `image_command` / `LAMBDA_HANDLER` can override the handler if ever needed.
- Runtime env vars wired by the `api` module: `DB_HOST/DB_PORT/DB_NAME/DB_SECRET_ARN`,
  `REDIS_HOST/REDIS_PORT`, `OIDC_ISSUER/OIDC_CLIENT_ID/OIDC_JWKS_URL`, `APP_PORT`.
  DB user/password are fetched at runtime from `DB_SECRET_ARN` (not baked into env).

## Cost-conscious defaults

- **Lambda arm64/Graviton** — ~20% cheaper than x86.
- **HTTP API** (`apigatewayv2`) instead of REST API — cheaper per request.
- **Single NAT gateway** in dev (`single_nat_gateway = true`) — avoids one-NAT-per-AZ; prod
  uses one per AZ for HA.
- **S3 gateway VPC endpoint** (free) — keeps S3 traffic off the NAT.
- **Aurora Serverless v2** min **0.5 ACU** — scales to low when idle (dev max 1 ACU, prod 8).
- **ElastiCache Serverless usage limits** (≈1 GB data, capped ECPU) — bounds cache spend.
- **CloudWatch log retention** set (14d dev / 30d prod) — no indefinite retention.
- **ECR lifecycle policy** — keep only the last 10 images.

## Tagging (FinOps)

Every module takes a `tags` map and merges it onto taggable resources. The AWS provider is
also generated (by Terragrunt) with `default_tags`, so every resource inherits the mandatory
keys even if a module misses one:

`Project`, `Environment`, `ManagedBy`, `Owner`, `CostCenter`

> Align these keys/values to your organization's tagging policy before applying.
Tags are defined once per environment in `terragrunt/<env>/env.hcl` (`default_tags`).

## Terragrunt layout (modern Stacks — DRY)

The wiring for each component is defined **once** as a reusable **unit template**, and each
environment is a single `terragrunt.stack.hcl` that instantiates the 7 units with that env's
values. There are no more hand-copied per-env/per-component `terragrunt.hcl` files.

```
terragrunt/
  root.hcl                     # remote_state (S3+DynamoDB or local/floci) + generated
                               # provider/versions + errors{retry} for transient throttling.
                               # Included by every unit; single place for provider/backend.
  units/                       # reusable UNIT TEMPLATES — component wiring defined ONCE
    <component>/terragrunt.hcl #   include "root" + terraform{source} + dependency{mock_outputs}
                               #   + inputs; env-specific knobs arrive via `values.*`
  dev/   env.hcl + terragrunt.stack.hcl     # per-env knobs + 7 unit{} instances
  prod/  env.hcl + terragrunt.stack.hcl
  local/ env.hcl + terragrunt.stack.hcl     # env.hcl sets use_floci = true
```

Where things live (DRY contract):

| Concern | Defined once in |
|---------|-----------------|
| Provider / backend / versions generation, retry-on-throttle | `root.hcl` |
| A component's module source, dependency graph, mock_outputs, input plumbing | `units/<component>/terragrunt.hcl` |
| Per-env sizing / tags / `use_floci` (single source of truth) | `<env>/env.hcl` |
| Which units run in an env + the env→unit value mapping | `<env>/terragrunt.stack.hcl` |

The three `terragrunt.stack.hcl` files are structurally identical — each simply auto-loads
its own directory's `env.hcl`. No logic is copy-pasted between environments: change a knob in
`env.hcl`, change wiring in `units/`.

The `values` block on each `unit` feeds the template (generated as `terragrunt.values.hcl`
next to each unit), so the unit template reads `values.name_prefix`, `values.tags`, etc.
Constants (VPC CIDR, memory size, engine, etc.) stay hard-coded in the unit template.

Dependency graph (via Terragrunt `dependency` blocks, all with `mock_outputs` so `plan`
works before anything is applied). After `stack generate`, units are materialized as sibling
directories under `.terragrunt-stack/`, so `config_path = "../<unit>"` resolves the graph:

```
network ─┬─▶ aurora ─┐
         ├─▶ cache ──┤
secrets ─┴───────────┼─▶ api
ecr ─────────────────┤
cognito ─────────────┘
```

> `.terragrunt-stack/` is **generated** (git-ignored) — never edit or commit it. Regenerate
> with `terragrunt stack generate`; wipe with `terragrunt stack clean`.

## Bootstrap (do this once, first)

The S3 state bucket and DynamoDB lock table **must exist before** `terragrunt init`.
Terragrunt does not create them for you here. Either create them manually or add a small
`bootstrap/` Terraform config. Example (adjust names/region):

```bash
export TG_STATE_BUCKET=cj-fastapi-ddd-tfstate
export TG_LOCK_TABLE=cj-fastapi-ddd-tflock
export AWS_REGION=us-east-1

aws s3api create-bucket --bucket "$TG_STATE_BUCKET" --region "$AWS_REGION"
aws s3api put-bucket-versioning --bucket "$TG_STATE_BUCKET" \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$TG_STATE_BUCKET" \
  --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"}}]}'

aws dynamodb create-table --table-name "$TG_LOCK_TABLE" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region "$AWS_REGION"
```

`root.hcl` reads `TG_STATE_BUCKET` / `TG_LOCK_TABLE` from the environment (with defaults),
so override them to match what you created.

## Running (Terragrunt Stacks)

Each environment is a stack. From the env directory, **generate** the units, then run a
command across the whole stack (the dependency graph is respected; `mock_outputs` let `plan`
run before any apply):

```bash
cd terragrunt/dev
terragrunt stack generate     # materialize .terragrunt-stack/<unit>/ from terragrunt.stack.hcl
terragrunt stack run init
terragrunt stack run plan

# A single component (after `stack generate`):
cd terragrunt/dev/.terragrunt-stack/network
terragrunt init
terragrunt plan
```

`prod` and `local` are identical — `cd terragrunt/<env> && terragrunt stack generate && terragrunt stack run plan`.
For `local`, start floci first (`task floci:up`); its `env.hcl` sets `use_floci = true`, so
`root.hcl` generates the floci provider (endpoints → `http://localhost:14566`) and a local
state backend instead of S3/DynamoDB.

### Taskfile targets

The repo's `terragrunt:*` tasks run inside `infra/terragrunt/<env>`:

```bash
task terragrunt:plan  ENV=dev     # -> cd infra/terragrunt/dev  && terragrunt stack generate && terragrunt stack run plan
task terragrunt:apply ENV=local   # -> cd infra/terragrunt/local && terragrunt stack generate && terragrunt stack run apply
```

> **Migration note (for the Taskfile):** Stacks replace `terragrunt run-all <cmd>` with
> `terragrunt stack generate && terragrunt stack run <cmd>`. Update each `terragrunt:*` target
> accordingly. `stack generate` is idempotent and cheap, so it's safe to run before every
> command.

> **Apply is intentionally gated through the CD pipeline.** Do not `terragrunt stack run apply`
> from a laptop. The pipeline builds/pushes the image to ECR, injects the immutable tag via
> `IMAGE_TAG`, and applies with the required approvals. Local usage is plan/review only.

## Validating the Terraform modules locally

```bash
terraform fmt -recursive terraform terragrunt
cd terraform/modules/network && terraform init -backend=false && terraform validate
# ...repeat per module
```
