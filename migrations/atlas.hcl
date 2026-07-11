variable "url" {
  type    = string
  default = getenv("ATLAS_DB_URL")
}

env "local" {
  url = var.url != "" ? var.url : "postgres://ddd:ddd@localhost:5432/ddd?sslmode=disable"
  dev = "docker://postgres/16/dev"
  migration {
    dir = "file://versions"
  }
}
