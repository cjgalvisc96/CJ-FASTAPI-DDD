# =============================================================================
# Unit template: network (VPC, subnets, NAT, app SG).
# Instantiated once per environment by each <env>/terragrunt.stack.hcl via a
# `unit "network"` block. Env-specific knobs arrive through `values.*`; everything
# below is either a project-wide constant or wired from those values. Defined ONCE here.
#
# Module (frozen): terraform/modules/network
# Dependencies: none.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/network"
}

inputs = {
  name_prefix        = values.name_prefix
  vpc_cidr           = "10.0.0.0/16"
  az_count           = 2
  single_nat_gateway = values.single_nat_gateway
  tags               = values.tags
}
