# Shared inputs for the cognito component.
# Module: ../../terraform/modules/cognito
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix = local.name_prefix
  # Cognito hosted-UI domain prefix must be globally unique across AWS.
  domain_prefix = "cj-fastapi-ddd-${local.environment}"
  tags          = local.env.locals.default_tags
}
