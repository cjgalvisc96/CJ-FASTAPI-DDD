variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "vpc_id" {
  description = "VPC id the cache lives in."
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet ids for the serverless cache."
  type        = list(string)
}

variable "app_security_group_id" {
  description = "App/Lambda security group allowed to reach the cache on 6379."
  type        = string
}

variable "engine" {
  description = "Serverless cache engine. valkey is Redis-compatible and lower cost than redis."
  type        = string
  default     = "valkey"
}

variable "major_engine_version" {
  description = "Major engine version for the serverless cache."
  type        = string
  default     = "8"
}

variable "max_data_storage_gb" {
  description = "Max stored data in GB — caps ElastiCache Serverless storage spend."
  type        = number
  default     = 1
}

variable "max_ecpu_per_second" {
  description = "Max ElastiCache Processing Units/sec — caps compute spend."
  type        = number
  default     = 5000
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
