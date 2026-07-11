output "db_secret_arn" {
  description = "ARN of the database credentials secret."
  value       = aws_secretsmanager_secret.db.arn
}

output "db_username" {
  description = "Database master username (non-sensitive; the password lives only in the secret)."
  value       = var.db_username
}

output "db_password" {
  description = "Generated database master password. Consumed by the aurora module; never log this."
  value       = random_password.db.result
  sensitive   = true
}

output "app_config_secret_arn" {
  description = "ARN of the application config secret."
  value       = aws_secretsmanager_secret.app_config.arn
}

output "secret_arns" {
  description = "All secret ARNs this app may read (used to scope the Lambda IAM policy)."
  value = [
    aws_secretsmanager_secret.db.arn,
    aws_secretsmanager_secret.app_config.arn,
  ]
}
