# =============================================================================
# Serverless-native OIDC identity provider (AWS Cognito).
#
# NOTE FOR THE APP TEAM: the FastAPI service currently ships a Keycloak-specific
# token verifier that reads roles from `realm_access.roles`. Cognito issues roles
# via the `cognito:groups` claim instead. To use this pool, add a small claims
# adapter that maps `cognito:groups` -> the roles the app expects. This module is
# kept here to document the serverless-native auth option (no Keycloak servers to
# run); it does not change the app until that adapter lands.
#
# Issuer:  https://cognito-idp.<region>.amazonaws.com/<user_pool_id>
# JWKS:    <issuer>/.well-known/jwks.json
# =============================================================================

data "aws_region" "current" {}

resource "aws_cognito_user_pool" "this" {
  name = "${var.name_prefix}-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-pool"
  })
}

# Hosted-UI domain (Cognito-managed; serverless).
resource "aws_cognito_user_pool_domain" "this" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}

# App client. Auth code flow for interactive users; client_credentials for machine-to-machine.
# Token validity is bounded to limit blast radius of a leaked token.
resource "aws_cognito_user_pool_client" "this" {
  name         = "${var.name_prefix}-client"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = true

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code", "client_credentials"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]

  id_token_validity      = var.id_token_validity_minutes
  access_token_validity  = var.access_token_validity_minutes
  refresh_token_validity = var.refresh_token_validity_days

  token_validity_units {
    id_token      = "minutes"
    access_token  = "minutes"
    refresh_token = "days"
  }

  prevent_user_existence_errors = "ENABLED"
}

# Roles are expressed as groups; they surface in the `cognito:groups` JWT claim.
resource "aws_cognito_user_group" "admin" {
  name         = "admin"
  user_pool_id = aws_cognito_user_pool.this.id
  description  = "Administrators."
  precedence   = 1
}

resource "aws_cognito_user_group" "member" {
  name         = "member"
  user_pool_id = aws_cognito_user_pool.this.id
  description  = "Standard members."
  precedence   = 10
}
