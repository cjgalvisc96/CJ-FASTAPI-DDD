output "user_pool_id" {
  description = "Cognito user pool id."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "Cognito user pool ARN."
  value       = aws_cognito_user_pool.this.arn
}

output "app_client_id" {
  description = "App client id."
  value       = aws_cognito_user_pool_client.this.id
}

output "app_client_secret" {
  description = "App client secret."
  value       = aws_cognito_user_pool_client.this.client_secret
  sensitive   = true
}

output "issuer_url" {
  description = "OIDC issuer URL for token verification."
  value       = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${aws_cognito_user_pool.this.id}"
}

output "jwks_url" {
  description = "JWKS URL for verifying JWT signatures."
  value       = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${aws_cognito_user_pool.this.id}/.well-known/jwks.json"
}

output "hosted_ui_domain" {
  description = "Cognito hosted-UI domain."
  value       = "https://${aws_cognito_user_pool_domain.this.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}
