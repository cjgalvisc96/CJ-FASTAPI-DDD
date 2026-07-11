# Password is generated in-state and never hardcoded. Exclude characters that break DB/URI parsing.
resource "random_password" "db" {
  length           = var.password_length
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db" {
  name                    = "${var.name_prefix}/db-credentials"
  description             = "Database master credentials for ${var.name_prefix}."
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-db-credentials"
  })
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
  })
}

# App config secret — a place for OIDC client secrets, feature flags, etc. Present even when empty
# so the app has a single, stable config secret ARN to read.
resource "aws_secretsmanager_secret" "app_config" {
  name                    = "${var.name_prefix}/app-config"
  description             = "Application configuration for ${var.name_prefix}."
  recovery_window_in_days = var.recovery_window_in_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-app-config"
  })
}

resource "aws_secretsmanager_secret_version" "app_config" {
  secret_id     = aws_secretsmanager_secret.app_config.id
  secret_string = jsonencode(var.app_config)
}
