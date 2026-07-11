# =============================================================================
# Unit template: migrate (one-off ECS Fargate task — Atlas DB migrations).
# Module (frozen): terraform/modules/migrate
# Dependencies: network, aurora, secrets.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/migrate"
}

dependency "network" {
  config_path = "../network"

  mock_outputs = {
    private_subnet_ids    = ["subnet-000000000000000001", "subnet-000000000000000002"]
    app_security_group_id = "sg-00000000000000000"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "aurora" {
  config_path = "../aurora"

  mock_outputs = {
    cluster_endpoint = "mock.aurora.local"
    port             = 5432
    database_name    = "ddd"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "secrets" {
  config_path = "../secrets"

  mock_outputs = {
    db_secret_arn = "arn:aws:secretsmanager:us-east-1:000000000000:secret:mock-db"
    db_username   = "app_admin"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

inputs = {
  name_prefix        = values.name_prefix
  tags               = values.tags
  log_retention_days = values.log_retention_days
  image_tag          = values.image_tag

  private_subnet_ids    = dependency.network.outputs.private_subnet_ids
  app_security_group_id = dependency.network.outputs.app_security_group_id

  aurora_endpoint = dependency.aurora.outputs.cluster_endpoint
  aurora_port     = dependency.aurora.outputs.port
  database_name   = dependency.aurora.outputs.database_name

  db_username   = dependency.secrets.outputs.db_username
  db_secret_arn = dependency.secrets.outputs.db_secret_arn
}
