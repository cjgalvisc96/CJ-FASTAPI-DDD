# Shared inputs for the aurora component.
# Module: ../../terraform/modules/aurora
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix   = local.name_prefix
  database_name = "app"
  # Must match the username stored in the secrets module.
  master_username     = "app_admin"
  min_capacity        = local.env.locals.aurora_min_capacity
  max_capacity        = local.env.locals.aurora_max_capacity
  deletion_protection = local.env.locals.deletion_protection
  skip_final_snapshot = local.env.locals.skip_final_snapshot
  tags                = local.env.locals.default_tags
}
