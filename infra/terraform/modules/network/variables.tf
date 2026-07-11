variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of Availability Zones to span (public + private subnet per AZ)."
  type        = number
  default     = 2
}

variable "single_nat_gateway" {
  description = "Use a single shared NAT gateway instead of one-per-AZ. One NAT is much cheaper; keep true in dev."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
