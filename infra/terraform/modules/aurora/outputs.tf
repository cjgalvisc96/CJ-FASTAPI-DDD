output "cluster_endpoint" {
  description = "Writer (primary) endpoint."
  value       = aws_rds_cluster.this.endpoint
}

output "reader_endpoint" {
  description = "Reader endpoint (load-balances across readers; equals writer when only one instance)."
  value       = aws_rds_cluster.this.reader_endpoint
}

output "port" {
  description = "Database port."
  value       = aws_rds_cluster.this.port
}

output "database_name" {
  description = "Initial database name."
  value       = aws_rds_cluster.this.database_name
}

output "security_group_id" {
  description = "Aurora security group id."
  value       = aws_security_group.db.id
}
