# Shared inputs for the network component.
# Module: ../../terraform/modules/network
locals {
  env         = read_terragrunt_config(find_in_parent_folders("env.hcl"))
  environment = local.env.locals.environment
  name_prefix = "cj-fastapi-ddd-${local.environment}"
}

inputs = {
  name_prefix        = local.name_prefix
  vpc_cidr           = "10.0.0.0/16"
  az_count           = 2
  single_nat_gateway = local.env.locals.single_nat_gateway
  tags               = local.env.locals.default_tags
}
