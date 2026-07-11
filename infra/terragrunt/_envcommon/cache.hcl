# Shared inputs for the cache component.
# Module: ../../terraform/modules/cache
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix = local.name_prefix
  engine      = "valkey"
  # Usage limits cap ElastiCache Serverless spend for a dev-scale cache.
  max_data_storage_gb = 1
  max_ecpu_per_second = 5000
  tags                = local.env.locals.default_tags
}
