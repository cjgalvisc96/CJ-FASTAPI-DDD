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

This stack ships a **Cognito** user pool as the serverless-native OIDC IdP. The application
currently ships a **Keycloak-specific** token verifier that reads roles from
`realm_access.roles`. Cognito instead issues roles via the **`cognito:groups`** claim.

To use Cognito, add a small claims adapter mapping `cognito:groups` → the roles the app
expects. Until that lands, you can point `oidc_issuer`/`oidc_jwks_url` at a Keycloak realm
instead — the `api` module takes them as plain variables, so no code change is needed to
switch IdPs. The `cognito` module is kept here to document the serverless-native option
(no Keycloak servers to run or patch). See the header comment in
`terraform/modules/cognito/main.tf`.

## App container contract

- Listens on port **8000**, exposes `GET /health`.
- Console script `ddd-api` runs uvicorn locally; the image CMD is overridable.
- On Lambda it runs behind **Mangum**; the handler is passed as the `LAMBDA_HANDLER` env
  var (default `app.main.handler`) and the CMD can be overridden via `image_command`.
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

## Terragrunt layout

```
terragrunt/
  root.hcl                 # remote_state (S3 + DynamoDB lock) + generated provider/versions
  _envcommon/              # shared inputs per component (reference ../../terraform/modules/<x>)
  dev/  env.hcl + <component>/terragrunt.hcl
  prod/ env.hcl + <component>/terragrunt.hcl
```

Dependency graph (via Terragrunt `dependency` blocks, all with `mock_outputs` so `plan`
works before anything is applied):

```
network ─┬─▶ aurora ─┐
         ├─▶ cache ──┤
secrets ─┴───────────┼─▶ api
ecr ─────────────────┤
cognito ─────────────┘
```

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

## Running

```bash
# Plan the whole dev environment (respects the dependency graph; mock_outputs let it run
# before any apply):
cd terragrunt/dev
terragrunt run-all init
terragrunt run-all plan

# A single component:
cd terragrunt/dev/network
terragrunt init
terragrunt plan
```

`prod` is identical: `cd terragrunt/prod && terragrunt run-all plan`.

> **Apply is intentionally gated through the CD pipeline.** Do not `terragrunt run-all apply`
> from a laptop. The pipeline builds/pushes the image to ECR, injects the immutable tag via
> `IMAGE_TAG`, and applies with the required approvals. Local usage is plan/review only.

## Validating the Terraform modules locally

```bash
terraform fmt -recursive terraform terragrunt
cd terraform/modules/network && terraform init -backend=false && terraform validate
# ...repeat per module
```
