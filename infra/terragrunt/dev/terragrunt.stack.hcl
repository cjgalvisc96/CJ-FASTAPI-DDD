# =============================================================================
# Dev environment stack.
#
# Declares the 7 units of the platform ONCE and instantiates them with dev's
# per-env knobs, all sourced from ./env.hcl (the single source of per-env truth).
# The unit WIRING (module source, dependencies, mock_outputs, input plumbing) lives
# in ../units/<component>/terragrunt.hcl and is shared by every environment.
#
# Usage (run from this directory):
#   terragrunt stack generate      # materialize .terragrunt-stack/<unit>/
#   terragrunt stack run plan       # plan the whole graph (mock_outputs let it run pre-apply)
#   terragrunt stack run apply      # gated via CD — not from a laptop
# =============================================================================
locals {
  env         = read_terragrunt_config("${get_terragrunt_dir()}/env.hcl").locals
  name_prefix = "cj-fastapi-ddd-${local.env.environment}"

  # Short recovery window outside prod so re-creates don't hit "scheduled for deletion".
  recovery_window_in_days = local.env.environment == "prod" ? 30 : 0
}

unit "network" {
  source = "${get_repo_root()}/infra/terragrunt/units/network"
  path   = "network"
  values = {
    name_prefix        = local.name_prefix
    single_nat_gateway = local.env.single_nat_gateway
    tags               = local.env.default_tags
  }
}

unit "ecr" {
  source = "${get_repo_root()}/infra/terragrunt/units/ecr"
  path   = "ecr"
  values = {
    name_prefix = local.name_prefix
    tags        = local.env.default_tags
  }
}

unit "secrets" {
  source = "${get_repo_root()}/infra/terragrunt/units/secrets"
  path   = "secrets"
  values = {
    name_prefix             = local.name_prefix
    recovery_window_in_days = local.recovery_window_in_days
    tags                    = local.env.default_tags
  }
}

unit "aurora" {
  source = "${get_repo_root()}/infra/terragrunt/units/aurora"
  path   = "aurora"
  values = {
    name_prefix         = local.name_prefix
    aurora_min_capacity = local.env.aurora_min_capacity
    aurora_max_capacity = local.env.aurora_max_capacity
    deletion_protection = local.env.deletion_protection
    skip_final_snapshot = local.env.skip_final_snapshot
    tags                = local.env.default_tags
  }
}

unit "cache" {
  source = "${get_repo_root()}/infra/terragrunt/units/cache"
  path   = "cache"
  values = {
    name_prefix = local.name_prefix
    tags        = local.env.default_tags
  }
}

unit "cognito" {
  source = "${get_repo_root()}/infra/terragrunt/units/cognito"
  path   = "cognito"
  values = {
    name_prefix = local.name_prefix
    tags        = local.env.default_tags
  }
}

unit "api" {
  source = "${get_repo_root()}/infra/terragrunt/units/api"
  path   = "api"
  values = {
    name_prefix          = local.name_prefix
    reserved_concurrency = local.env.reserved_concurrency
    log_retention_days   = local.env.log_retention_days
    tags                 = local.env.default_tags
  }
}
