# Cache SG: ingress 6379 only from the app/Lambda SG — the cache stays private.
resource "aws_security_group" "cache" {
  name_prefix = "${var.name_prefix}-cache-"
  description = "ElastiCache Serverless (Valkey) security group."
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis/Valkey from app/Lambda SG"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  # No egress rules: security groups are stateful, so replies to inbound connections are allowed.
  # The cache never initiates outbound traffic, so it needs no egress allowance.

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# ElastiCache Serverless for Valkey — no node sizing to manage; usage_limits cap spend so an
# idle/dev cache costs little. Valkey is Redis-wire-compatible and cheaper than the redis engine.
resource "aws_elasticache_serverless_cache" "this" {
  engine     = var.engine
  name       = "${var.name_prefix}-cache"
  subnet_ids = var.private_subnet_ids

  security_group_ids   = [aws_security_group.cache.id]
  major_engine_version = var.major_engine_version

  cache_usage_limits {
    data_storage {
      maximum = var.max_data_storage_gb
      unit    = "GB"
    }
    ecpu_per_second {
      maximum = var.max_ecpu_per_second
    }
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache"
  })
}
