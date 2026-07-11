resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-aurora"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-aurora-subnet-group"
  })
}

# DB SG: ingress 5432 only from the app/Lambda SG — the database is never exposed publicly.
resource "aws_security_group" "db" {
  name_prefix = "${var.name_prefix}-aurora-"
  description = "Aurora PostgreSQL security group."
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from app/Lambda SG"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-aurora-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Aurora Serverless v2: engine_mode "provisioned" + serverlessv2_scaling_configuration.
# Scales down to min_capacity ACUs when idle, so dev spend tracks usage rather than a fixed instance.
resource "aws_rds_cluster" "this" {
  cluster_identifier = "${var.name_prefix}-aurora"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = var.engine_version

  database_name   = var.database_name
  master_username = var.master_username
  master_password = var.master_password

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]

  storage_encrypted         = true
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name_prefix}-aurora-final"
  backup_retention_period   = var.backup_retention_period

  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-aurora"
  })
}

# Single writer instance on the db.serverless class (one instance keeps dev cost down; add
# reader instances in prod for HA/read scaling).
resource "aws_rds_cluster_instance" "writer" {
  identifier         = "${var.name_prefix}-aurora-writer"
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.this.engine
  engine_version     = aws_rds_cluster.this.engine_version

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-aurora-writer"
  })
}
