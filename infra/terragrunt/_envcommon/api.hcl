# Shared inputs for the api (compute) component.
# Module: ../../terraform/modules/api
# Dependency wiring (image_uri, db/redis/oidc endpoints, secret ARNs) lives in the child
# terragrunt.hcl where the dependency blocks are declared.
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix          = local.name_prefix
  lambda_handler       = "app.main.handler"
  memory_size          = 512
  timeout              = 30
  reserved_concurrency = local.env.locals.reserved_concurrency
  log_retention_days   = local.env.locals.log_retention_days
  db_port              = 5432
  redis_port           = 6379
  tags                 = local.env.locals.default_tags
}
