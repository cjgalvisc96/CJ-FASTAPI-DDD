# =============================================================================
# Unit template: api (Lambda container behind HTTP API — the compute tier).
# Module (frozen): terraform/modules/api
# Dependencies: network, ecr, secrets, aurora, cache, cognito.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/api"
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

dependency "ecr" {
  config_path = "../ecr"

  mock_outputs = {
    repository_url  = "000000000000.dkr.ecr.us-east-1.amazonaws.com/${values.name_prefix}-api"
    repository_arn  = "arn:aws:ecr:us-east-1:000000000000:repository/${values.name_prefix}-api"
    repository_name = "${values.name_prefix}-api"
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

dependency "aurora" {
  config_path = "../aurora"

  mock_outputs = {
    cluster_endpoint = "mock-aurora.cluster-xxxx.us-east-1.rds.amazonaws.com"
    reader_endpoint  = "mock-aurora.cluster-ro-xxxx.us-east-1.rds.amazonaws.com"
    port             = 5432
    database_name    = "app"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "cache" {
  config_path = "../cache"

  mock_outputs = {
    endpoint_address = "mock-cache.serverless.use1.cache.amazonaws.com"
    endpoint_port    = 6379
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

dependency "cognito" {
  config_path = "../cognito"

  mock_outputs = {
    user_pool_id  = "us-east-1_mockpool"
    app_client_id = "mockclientid0000000000"
    issuer_url    = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_mockpool"
    jwks_url      = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_mockpool/.well-known/jwks.json"
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
}

inputs = {
  name_prefix          = values.name_prefix
  lambda_handler       = "app.main.handler"
  memory_size          = 512
  timeout              = 30
  reserved_concurrency = values.reserved_concurrency
  log_retention_days   = values.log_retention_days
  db_port              = 5432
  redis_port           = 6379
  tags                 = values.tags

  vpc_id                = dependency.network.outputs.vpc_id
  private_subnet_ids    = dependency.network.outputs.private_subnet_ids
  app_security_group_id = dependency.network.outputs.app_security_group_id

  # Image tag is injected by the CD pipeline (IMAGE_TAG); defaults to latest for plan.
  image_uri = "${dependency.ecr.outputs.repository_url}:${get_env("IMAGE_TAG", "latest")}"

  secret_arns   = dependency.secrets.outputs.secret_arns
  db_host       = dependency.aurora.outputs.cluster_endpoint
  db_name       = dependency.aurora.outputs.database_name
  db_secret_arn = dependency.secrets.outputs.db_secret_arn

  redis_host = dependency.cache.outputs.endpoint_address
  redis_port = dependency.cache.outputs.endpoint_port

  oidc_issuer    = dependency.cognito.outputs.issuer_url
  oidc_client_id = dependency.cognito.outputs.app_client_id
  oidc_jwks_url  = dependency.cognito.outputs.jwks_url
}
