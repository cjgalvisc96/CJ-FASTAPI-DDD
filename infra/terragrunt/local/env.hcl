# Local environment — the full AWS stack emulated by floci (http://localhost:4566).
# Run `task docker:up` to start floci, then `task terragrunt:apply ENV=local`.
locals {
  environment = "local"
  region      = "us-east-1"

  # Point Terraform's AWS provider at floci and use a local state backend (see root.hcl).
  use_floci = true

  # FinOps ownership
  owner       = "cjgalvisc@unal.edu.co"
  cost_center = "engineering"

  # Sizing / cost knobs — smallest possible; floci does not bill, this just mirrors dev shape.
  aurora_min_capacity  = 0.5
  aurora_max_capacity  = 1
  deletion_protection  = false
  skip_final_snapshot  = true
  single_nat_gateway   = true
  reserved_concurrency = null
  log_retention_days   = 1

  # Mandatory tag keys — align to the org tagging policy.
  default_tags = {
    Project     = "cj-fastapi-ddd"
    Environment = "local"
    ManagedBy   = "terraform"
    Owner       = "cjgalvisc@unal.edu.co"
    CostCenter  = "engineering"
  }
}
