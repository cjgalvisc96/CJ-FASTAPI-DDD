variable "repository_name" {
  description = "Name of the ECR repository for the app image."
  type        = string
}

variable "image_tag_mutability" {
  description = "Tag mutability. IMMUTABLE prevents overwriting a tag (safer, reproducible deploys)."
  type        = string
  default     = "IMMUTABLE"
}

variable "scan_on_push" {
  description = "Scan images for vulnerabilities on push."
  type        = bool
  default     = true
}

variable "max_image_count" {
  description = "Number of most-recent images to retain; older ones are expired to cap storage cost."
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags applied to every taggable resource. Align keys to the org tagging policy."
  type        = map(string)
  default     = {}
}
