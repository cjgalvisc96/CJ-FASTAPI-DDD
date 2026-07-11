variable "name_prefix" {
  description = "Prefix applied to secret names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "db_username" {
  description = "Master username stored in the database credentials secret."
  type        = string
  default     = "app_admin"
}

variable "password_length" {
  description = "Length of the generated database password."
  type        = number
  default     = 32
}

variable "recovery_window_in_days" {
  description = "Days before a deleted secret is permanently removed. 0 = immediate delete (handy in dev)."
  type        = number
  default     = 7
}

variable "app_config" {
  description = "Optional non-sensitive-per-se app config key/values stored in the app config secret."
  type        = map(string)
  default     = {}
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
