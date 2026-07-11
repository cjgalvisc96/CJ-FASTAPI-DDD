output "endpoint_address" {
  description = "Cache primary endpoint address."
  value       = one(aws_elasticache_serverless_cache.this.endpoint[*].address)
}

output "endpoint_port" {
  description = "Cache endpoint port."
  value       = one(aws_elasticache_serverless_cache.this.endpoint[*].port)
}

output "reader_endpoint_address" {
  description = "Cache reader endpoint address."
  value       = one(aws_elasticache_serverless_cache.this.reader_endpoint[*].address)
}

output "security_group_id" {
  description = "Cache security group id."
  value       = aws_security_group.cache.id
}
