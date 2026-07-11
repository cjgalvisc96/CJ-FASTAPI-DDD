# =============================================================================
# Unit template: secrets (Secrets Manager — DB creds + app config).
# Module (frozen): terraform/modules/secrets
# Dependencies: none.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/secrets"
}

inputs = {
  name_prefix = values.name_prefix
  db_username = "app_admin"
  # Short recovery window outside prod so re-creates don't hit
  # "secret scheduled for deletion" (value computed per-env in the stack file).
  recovery_window_in_days = values.recovery_window_in_days
  tags                    = values.tags
}
