data "aws_region" "current" {}

locals {
  # Env vars wired from the other modules. The container reads these at cold start.
  # PORT/handler are provided so the same image runs under uvicorn locally and Mangum on Lambda.
  environment = merge({
    APP_PORT       = "8000"
    LAMBDA_HANDLER = var.lambda_handler
    DB_HOST        = var.db_host
    DB_PORT        = tostring(var.db_port)
    DB_NAME        = var.db_name
    DB_SECRET_ARN  = var.db_secret_arn
    REDIS_HOST     = var.redis_host
    REDIS_PORT     = tostring(var.redis_port)
    OIDC_ISSUER    = var.oidc_issuer
    OIDC_CLIENT_ID = var.oidc_client_id
    OIDC_JWKS_URL  = var.oidc_jwks_url
  }, var.extra_environment)
}

#############################
# IAM execution role (least-privilege)
#############################
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.name_prefix}-api-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-role"
  })
}

# VPC access (manage ENIs) — required for a VPC-attached Lambda.
resource "aws_iam_role_policy_attachment" "vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Secrets read scoped to the EXACT secret ARNs, never '*'.
data "aws_iam_policy_document" "secrets" {
  statement {
    sid       = "ReadAppSecrets"
    actions   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
    resources = var.secret_arns
  }
}

resource "aws_iam_role_policy" "secrets" {
  name   = "${var.name_prefix}-api-secrets"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.secrets.json
}

# CloudWatch Logs scoped to this function's log group.
data "aws_iam_policy_document" "logs" {
  statement {
    sid       = "WriteLogs"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.lambda.arn}:*"]
  }
}

resource "aws_iam_role_policy" "logs" {
  name   = "${var.name_prefix}-api-logs"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.logs.json
}

#############################
# CloudWatch log group (bounded retention)
#############################
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.name_prefix}-api"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-logs"
  })
}

#############################
# Lambda (container image, arm64/Graviton)
#############################
# arm64/Graviton — ~20% cheaper than x86 for the same performance on this workload.
resource "aws_lambda_function" "this" {
  function_name = "${var.name_prefix}-api"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = var.image_uri
  architectures = ["arm64"]

  memory_size                    = var.memory_size
  timeout                        = var.timeout
  reserved_concurrent_executions = var.reserved_concurrency

  dynamic "image_config" {
    for_each = var.image_command == null ? [] : [var.image_command]
    content {
      command = image_config.value
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.app_security_group_id]
  }

  environment {
    variables = local.environment
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api"
  })

  depends_on = [
    aws_iam_role_policy_attachment.vpc,
    aws_cloudwatch_log_group.lambda,
  ]
}

#############################
# HTTP API (cheaper than REST API) -> Lambda proxy
#############################
resource "aws_apigatewayv2_api" "this" {
  name          = "${var.name_prefix}-api"
  protocol_type = "HTTP"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api"
  })
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api-stage"
  })
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
