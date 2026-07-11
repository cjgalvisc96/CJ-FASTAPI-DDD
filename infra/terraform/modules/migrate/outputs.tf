output "repository_url" {
  description = "ECR repository URL for the migration image (push migrate:<tag> here)."
  value       = aws_ecr_repository.migrate.repository_url
}

output "cluster_arn" {
  description = "ECS cluster ARN the migration task runs on."
  value       = aws_ecs_cluster.this.arn
}

output "cluster_name" {
  description = "ECS cluster name the migration task runs on."
  value       = aws_ecs_cluster.this.name
}

output "task_definition_arn" {
  description = "Migration task definition ARN (revision-pinned)."
  value       = aws_ecs_task_definition.this.arn
}

output "task_definition_family" {
  description = "Migration task definition family (use to run the latest revision)."
  value       = aws_ecs_task_definition.this.family
}

output "log_group_name" {
  description = "CloudWatch log group for the migration task."
  value       = aws_cloudwatch_log_group.this.name
}

output "subnet_ids" {
  description = "Private subnet ids for the run-task network configuration."
  value       = var.private_subnet_ids
}

output "security_group_id" {
  description = "Security group id for the run-task network configuration (reused app SG)."
  value       = var.app_security_group_id
}
