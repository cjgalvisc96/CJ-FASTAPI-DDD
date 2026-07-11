# Prod environment: locals consumed by _envcommon files and root.hcl.
locals {
  environment = "prod"
  region      = "us-east-1"

  # FinOps ownership
  owner       = "cjgalvisc@unal.edu.co"
  cost_center = "engineering"

  # Sizing / cost knobs (prod = HA + protection, higher ceilings)
  aurora_min_capacity  = 0.5 # still scale-to-low when idle
  aurora_max_capacity  = 8   # room to scale under load
  deletion_protection  = true
  skip_final_snapshot  = false
  single_nat_gateway   = false # one NAT per AZ for HA in prod
  reserved_concurrency = null
  log_retention_days   = 30

  # Mandatory tag keys — align to the org tagging policy.
  default_tags = {
    Project     = "cj-fastapi-ddd"
    Environment = "prod"
    ManagedBy   = "terraform"
    Owner       = "cjgalvisc@unal.edu.co"
    CostCenter  = "engineering"
  }
}
