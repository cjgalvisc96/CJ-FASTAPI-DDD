output "vpc_id" {
  description = "VPC id."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = aws_vpc.this.cidr_block
}

output "private_subnet_ids" {
  description = "Private subnet ids (for Lambda, Aurora, ElastiCache)."
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet ids (for NAT / load balancers)."
  value       = aws_subnet.public[*].id
}

output "app_security_group_id" {
  description = "Security group attached to the app/Lambda ENIs; data stores allow ingress from this SG."
  value       = aws_security_group.app.id
}
