include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "envcommon" {
  path           = "${dirname(find_in_parent_folders("env.hcl"))}/../_envcommon/secrets.hcl"
  merge_strategy = "deep"
}

terraform {
  source = "../../../terraform/modules/secrets"
}
