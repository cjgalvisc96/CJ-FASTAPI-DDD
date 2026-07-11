variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "vpc_id" {
  description = "VPC id the cluster lives in."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids for the DB subnet group."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "App/Lambda security group allowed to reach the database on 5432."
  type        = string
}

variable "database_name" {
  description = "Initial database name."
  type        = string
  default     = "app"
}

variable "master_username" {
  description = "Master username (kept in sync with the credentials secret)."
  type        = string
}

variable "master_password" {
  description = "Master password, sourced from the secrets module. Never hardcoded."
  type        = string
  sensitive   = true
}

variable "engine_version" {
  description = "Aurora PostgreSQL engine version."
  type        = string
  default     = "16.4"
}

variable "min_capacity" {
  description = "Serverless v2 minimum ACUs. 0.5 is the floor; scale-to-low keeps dev cheap."
  type        = number
  default     = 0.5
}

variable "max_capacity" {
  description = "Serverless v2 maximum ACUs. Keep small in dev (1), larger in prod."
  type        = number
  default     = 1
}

variable "deletion_protection" {
  description = "Block accidental cluster deletion. false in dev, true in prod."
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip the final snapshot on destroy. true in dev, false in prod."
  type        = bool
  default     = true
}

variable "backup_retention_period" {
  description = "Automated backup retention in days."
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
