# Shared inputs for the ecr component.
# Module: ../../terraform/modules/ecr
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
}

inputs = {
  repository_name      = "cj-fastapi-ddd-${local.environment}-api"
  image_tag_mutability = "IMMUTABLE"
  scan_on_push         = true
  max_image_count      = 10
  tags                 = local.env.locals.default_tags
}
