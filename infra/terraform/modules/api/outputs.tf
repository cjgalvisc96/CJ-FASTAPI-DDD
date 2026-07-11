output "api_endpoint" {
  description = "HTTP API invoke URL (base). Health check: <endpoint>/health"
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_id" {
  description = "HTTP API id."
  value       = aws_apigatewayv2_api.this.id
}

output "lambda_function_name" {
  description = "Lambda function name."
  value       = aws_lambda_function.this.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN."
  value       = aws_lambda_function.this.arn
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN."
  value       = aws_iam_role.lambda.arn
}

output "log_group_name" {
  description = "CloudWatch log group for the Lambda."
  value       = aws_cloudwatch_log_group.lambda.name
}
