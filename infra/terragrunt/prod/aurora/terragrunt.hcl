include "root" {
  path = find_in_parent_folders("root.hcl")
}

include "envcommon" {
  path           = "${dirname(find_in_parent_folders("env.hcl"))}/../_envcommon/aurora.hcl"
  merge_strategy = "deep"
}

terraform {
  source = "../../../terraform/modules/aurora"
}

dependency "network" {
  config_path = "../network"

  mock_outputs = {
    vpc_id                = "vpc-00000000000000000"
    private_subnet_ids    = ["subnet-00000000000000001", "subnet-00000000000000002"]
    public_subnet_ids     = ["subnet-00000000000000003", "subnet-00000000000000004"]
    app_security_group_id = "sg-00000000000000000"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "secrets" {
  config_path = "../secrets"

  mock_outputs = {
    db_secret_arn         = "arn:aws:secretsmanager:us-east-1:000000000000:secret:mock-db"
    app_config_secret_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:mock-cfg"
    db_username           = "app_admin"
    db_password           = "mock-password-value"
    secret_arns           = ["arn:aws:secretsmanager:us-east-1:000000000000:secret:mock-db"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

inputs = {
  vpc_id                = dependency.network.outputs.vpc_id
  private_subnet_ids    = dependency.network.outputs.private_subnet_ids
  app_security_group_id = dependency.network.outputs.app_security_group_id

  # Master password sourced from the secrets module — never hardcoded here.
  master_password = dependency.secrets.outputs.db_password
}
