# =============================================================================
# Root Terragrunt config — included by every child via:
#   include "root" { path = find_in_parent_folders("root.hcl") }
#
# Responsibilities:
#   - State backend: S3 + DynamoDB for real envs (dev/prod); a LOCAL file backend for the
#     floci-emulated `local` env (env.hcl sets use_floci = true).
#   - Generate the AWS provider (region + default_tags). For `local`, the provider is pointed at
#     floci (http://localhost:4566) with test credentials and the usual skip flags.
#   - Generate a versions.tf pinning Terraform + provider constraints.
#
# For dev/prod the S3 state bucket + DynamoDB lock table must EXIST first (see infra/README.md).
# For `local`, floci must be running (`task floci:up`) — no bucket bootstrap needed.
# =============================================================================

locals {
  env    = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  region = local.env.locals.region

  # floci (local AWS emulator) mode — set in local/env.hcl. Host port is offset to 4567 so this
  # stack's floci coexists with sibling projects (override with AWS_ENDPOINT_URL if needed).
  use_floci      = try(local.env.locals.use_floci, false)
  floci_endpoint = get_env("AWS_ENDPOINT_URL", "http://localhost:14566")

  # State backend names (real envs). Override via env vars if your bucket/table differ.
  state_bucket = get_env("TG_STATE_BUCKET", "cj-fastapi-ddd-tfstate")
  lock_table   = get_env("TG_LOCK_TABLE", "cj-fastapi-ddd-tflock")
  default_tags = local.env.locals.default_tags

  # Provider body for real AWS (dev/prod).
  provider_aws = <<-EOF
    provider "aws" {
      region = "${local.region}"

      default_tags {
        tags = ${jsonencode(local.default_tags)}
      }
    }
  EOF

  # Provider body for floci: every service endpoint resolves to floci; credential/metadata checks
  # are skipped and path-style S3 is used.
  provider_floci = <<-EOF
    provider "aws" {
      region                      = "${local.region}"
      access_key                  = "test"
      secret_key                  = "test"
      skip_credentials_validation = true
      skip_metadata_api_check     = true
      skip_requesting_account_id  = true
      skip_region_validation      = true
      s3_use_path_style           = true

      default_tags {
        tags = ${jsonencode(local.default_tags)}
      }

      endpoints {
        apigateway     = "${local.floci_endpoint}"
        apigatewayv2   = "${local.floci_endpoint}"
        cloudwatch     = "${local.floci_endpoint}"
        cognitoidp     = "${local.floci_endpoint}"
        dynamodb       = "${local.floci_endpoint}"
        ec2            = "${local.floci_endpoint}"
        ecr            = "${local.floci_endpoint}"
        elasticache    = "${local.floci_endpoint}"
        iam            = "${local.floci_endpoint}"
        kms            = "${local.floci_endpoint}"
        lambda         = "${local.floci_endpoint}"
        logs           = "${local.floci_endpoint}"
        rds            = "${local.floci_endpoint}"
        s3             = "${local.floci_endpoint}"
        secretsmanager = "${local.floci_endpoint}"
        sts            = "${local.floci_endpoint}"
      }
    }
  EOF
}

# Retry transient AWS/API throttling on apply — inherited by every unit via `include "root"`.
# These are read-safe retries on rate-limit / throttle errors only; nothing here masks a real
# resource error. Useful on wide `stack run apply` fan-outs that briefly exceed API rate limits.
errors {
  retry "aws_transient_throttling" {
    retryable_errors = [
      "(?s).*Throttling.*",
      "(?s).*ThrottlingException.*",
      "(?s).*RequestLimitExceeded.*",
      "(?s).*TooManyRequestsException.*",
      "(?s).*Rate exceeded.*",
      "(?s).*ServiceUnavailable.*",
      "(?s).*operation error.*timeout.*",
    ]
    max_attempts       = 3
    sleep_interval_sec = 8
  }
}

# One state file per component. floci → local file backend (no bucket bootstrap); else S3 + DynamoDB.
remote_state {
  backend = local.use_floci ? "local" : "s3"

  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }

  config = local.use_floci ? {
    path = "${get_terragrunt_dir()}/terraform.tfstate"
    } : {
    bucket         = local.state_bucket
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = local.region
    encrypt        = true
    dynamodb_table = local.lock_table
  }
}

# AWS provider with default_tags — every resource inherits the mandatory FinOps tags even if a
# module forgets to merge them. Keep provider blocks OUT of modules.
#
# NOTE: we do NOT generate a versions.tf here. Each module already ships its own versions.tf with the
# required_version + required_providers it uses; generating another would produce a duplicate
# required_providers block at `terraform init`.
generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = local.use_floci ? local.provider_floci : local.provider_aws
}
