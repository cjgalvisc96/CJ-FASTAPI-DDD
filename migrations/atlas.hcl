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

# Used by the AWS Fargate migrate task — Atlas builds the URL from injected env vars (DB_PASSWORD comes
# from Secrets Manager). Requires a URL-safe password (see the secrets module). Run: `atlas migrate
# apply --env aws`.
env "aws" {
  url = "postgres://${getenv("DB_USER")}:${getenv("DB_PASSWORD")}@${getenv("DB_HOST")}:${getenv("DB_PORT")}/${getenv("DB_NAME")}?sslmode=require"
  migration {
    dir = "file://versions"
  }
}
