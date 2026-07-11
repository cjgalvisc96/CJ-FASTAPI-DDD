# =============================================================================
# Unit template: ecr (container image repository).
# Module (frozen): terraform/modules/ecr
# Dependencies: none.
# =============================================================================
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "${get_repo_root()}/infra/terraform/modules/ecr"
}

inputs = {
  repository_name      = "${values.name_prefix}-api"
  image_tag_mutability = "IMMUTABLE"
  scan_on_push         = true
  max_image_count      = 10
  tags                 = values.tags
}
