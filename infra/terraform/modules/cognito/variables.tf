variable "name_prefix" {
  description = "Prefix applied to resource names (e.g. cj-fastapi-ddd-dev)."
  type        = string
}

variable "domain_prefix" {
  description = "Globally-unique Cognito hosted-UI domain prefix. Must be unique across AWS."
  type        = string
}

variable "callback_urls" {
  description = "Allowed OAuth2 redirect URIs for the app client."
  type        = list(string)
  default     = ["http://localhost:8000/auth/callback"]
}

variable "logout_urls" {
  description = "Allowed sign-out redirect URIs for the app client."
  type        = list(string)
  default     = ["http://localhost:8000/"]
}

variable "id_token_validity_minutes" {
  description = "ID token validity (minutes)."
  type        = number
  default     = 60
}

variable "access_token_validity_minutes" {
  description = "Access token validity (minutes)."
  type        = number
  default     = 60
}

variable "refresh_token_validity_days" {
  description = "Refresh token validity (days)."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
