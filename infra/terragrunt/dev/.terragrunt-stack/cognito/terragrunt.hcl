# =============================================================================
# Unit template: cognito (user pool + app client + hosted-UI domain).
# Module (frozen): terraform/modules/cognito
# Dependencies: none.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/cognito"
}

inputs = {
  name_prefix = values.name_prefix
  # Cognito hosted-UI domain prefix must be globally unique across AWS.
  domain_prefix = values.name_prefix
  tags          = values.tags
}
