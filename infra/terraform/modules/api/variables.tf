variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "image_uri" {
  description = "Full ECR image URI (repository_url:tag) the Lambda runs."
  type        = string
}

variable "lambda_handler" {
  description = "Mangum handler exposed via env var; the container CMD is overridable to point at it."
  type        = string
  default     = "app.main.handler"
}

variable "image_command" {
  description = "Optional container image CMD override (e.g. the Mangum entrypoint). null keeps the image default."
  type        = list(string)
  default     = null
}

variable "memory_size" {
  description = "Lambda memory (MB); also scales CPU."
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Lambda timeout (seconds)."
  type        = number
  default     = 30
}

variable "reserved_concurrency" {
  description = "Reserved concurrent executions. null = unreserved (no extra cost floor)."
  type        = number
  default     = null
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention (days). Bounded retention avoids indefinite log storage cost."
  type        = number
  default     = 14
}

variable "vpc_id" {
  description = "VPC id for the Lambda ENIs."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids the Lambda runs in."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "Security group attached to the Lambda (data stores allow ingress from it)."
  type        = string
}

variable "secret_arns" {
  description = "Exact Secrets Manager ARNs the Lambda may read (scoped least-privilege, not '*')."
  type        = list(string)
}

variable "db_host" {
  description = "Aurora writer endpoint."
  type        = string
}

variable "db_port" {
  description = "Aurora port."
  type        = number
  default     = 5432
}

variable "db_name" {
  description = "Database name."
  type        = string
}

variable "db_secret_arn" {
  description = "ARN of the DB credentials secret (the app fetches user/password at runtime)."
  type        = string
}

variable "redis_host" {
  description = "ElastiCache Serverless endpoint address."
  type        = string
}

variable "redis_port" {
  description = "ElastiCache Serverless endpoint port."
  type        = number
  default     = 6379
}

variable "oidc_issuer" {
  description = "OIDC issuer URL (Cognito or Keycloak) used to verify JWTs."
  type        = string
}

variable "oidc_client_id" {
  description = "OIDC app client id (JWT audience)."
  type        = string
}

variable "oidc_jwks_url" {
  description = "JWKS URL for JWT signature verification."
  type        = string
}

variable "extra_environment" {
  description = "Additional environment variables to merge into the Lambda."
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
