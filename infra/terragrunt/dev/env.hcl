# Dev environment: locals consumed by _envcommon files and root.hcl.
locals {
  environment = "dev"
  region      = "us-east-1"

  # FinOps ownership
  owner       = "cjgalvisc@unal.edu.co"
  cost_center = "engineering"

  # Sizing / cost knobs (dev = cheapest safe defaults)
  aurora_min_capacity  = 0.5 # ACU floor
  aurora_max_capacity  = 1   # small ceiling in dev
  deletion_protection  = false
  skip_final_snapshot  = true
  single_nat_gateway   = true # one shared NAT in dev — avoids one-per-AZ cost
  reserved_concurrency = null
  log_retention_days   = 14

  # Mandatory tag keys — align to the org tagging policy. default_tags on the provider
  # applies these to every taggable resource; modules also merge them for belt-and-braces.
  default_tags = {
    Project     = "cj-fastapi-ddd"
    Environment = "dev"
    ManagedBy   = "terraform"
    Owner       = "cjgalvisc@unal.edu.co"
    CostCenter  = "engineering"
  }
}
