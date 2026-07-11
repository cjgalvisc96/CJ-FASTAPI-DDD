# Shared inputs for the secrets component.
# Module: ../../terraform/modules/secrets
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix = local.name_prefix
  db_username = "app_admin"
  # Short recovery window in dev so re-creates don't hit "secret scheduled for deletion".
  recovery_window_in_days = local.environment == "prod" ? 30 : 0
  tags                    = local.env.locals.default_tags
}
