# =============================================================================
# Unit template: aurora (Aurora Serverless v2 PostgreSQL).
# Module (frozen): terraform/modules/aurora
# Dependencies: network (VPC/subnets/SG), secrets (master password).
# Sibling units are generated next to this one under .terragrunt-stack/, so the
# dependency config_paths are simple "../<unit>" references.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/aurora"
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
  name_prefix   = values.name_prefix
  database_name = "app"
  # Must match the username stored in the secrets module.
  master_username     = "app_admin"
  min_capacity        = values.aurora_min_capacity
  max_capacity        = values.aurora_max_capacity
  deletion_protection = values.deletion_protection
  skip_final_snapshot = values.skip_final_snapshot
  tags                = values.tags

  vpc_id                = dependency.network.outputs.vpc_id
  private_subnet_ids    = dependency.network.outputs.private_subnet_ids
  app_security_group_id = dependency.network.outputs.app_security_group_id

  # Master password sourced from the secrets module — never hardcoded here.
  master_password = dependency.secrets.outputs.db_password
}
