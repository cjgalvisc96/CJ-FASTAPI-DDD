variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}

variable "private_subnet_ids" {
  description = "Private subnet ids the migration task runs in."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "App security group reused by the migration task (Aurora already allows ingress from it)."
  type        = string
}

variable "aurora_endpoint" {
  description = "Aurora writer endpoint the migration connects to."
  type        = string
}

variable "aurora_port" {
  description = "Aurora port."
  type        = number
  default     = 5432
}

variable "database_name" {
  description = "Database name migrations are applied to."
  type        = string
}

variable "db_username" {
  description = "DB username (the password is pulled from db_secret_arn at task start)."
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the DB credentials secret (JSON {username,password}); the task reads the password key."
  type        = string
}

variable "image_tag" {
  description = "Tag of the migration image in the migrate ECR repo the task runs."
  type        = string
  default     = "latest"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention (days). Bounded retention avoids indefinite log storage cost."
  type        = number
  default     = 14
}

variable "cpu" {
  description = "Fargate task CPU units (string, e.g. \"256\")."
  type        = string
  default     = "256"
}

variable "memory" {
  description = "Fargate task memory in MiB (string, e.g. \"512\")."
  type        = string
  default     = "512"
}
