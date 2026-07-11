data "aws_region" "current" {}

#############################
# ECR repository for the migration image
#############################
# MUTABLE: the migration image is re-tagged per release (e.g. reusing "latest").
resource "aws_ecr_repository" "migrate" {
  name                 = "${var.name_prefix}-migrate"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate"
  })
}

# Keep only the last 10 images; expiring old images caps ECR storage cost.
resource "aws_ecr_lifecycle_policy" "migrate" {
  repository = aws_ecr_repository.migrate.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

#############################
# ECS cluster (Fargate)
#############################
resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-migrate"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate"
  })
}

resource "aws_ecs_cluster_capacity_providers" "this" {
  cluster_name       = aws_ecs_cluster.this.name
  capacity_providers = ["FARGATE"]
}

#############################
# CloudWatch log group (bounded retention)
#############################
resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.name_prefix}-migrate"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate-logs"
  })
}

#############################
# IAM: task execution role (pull image, write logs, read the DB secret)
#############################
data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "exec" {
  name               = "${var.name_prefix}-migrate-exec"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate-exec"
  })
}

# Standard ECS execution perms: ECR pull + CloudWatch Logs.
resource "aws_iam_role_policy_attachment" "exec_managed" {
  role       = aws_iam_role.exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Secrets read scoped to the EXACT db secret ARN, never '*'.
# The secret is KMS-encrypted with the default AWS-managed key, so the managed
# execution policy + this GetSecretValue perm suffice (no extra KMS perms needed).
data "aws_iam_policy_document" "secrets" {
  statement {
    sid       = "ReadDbSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "exec_secrets" {
  name   = "${var.name_prefix}-migrate-secrets"
  role   = aws_iam_role.exec.id
  policy = data.aws_iam_policy_document.secrets.json
}

#############################
# IAM: task role (no AWS API calls — Atlas only reaches the DB over the network)
#############################
resource "aws_iam_role" "task" {
  name               = "${var.name_prefix}-migrate-task"
  assume_role_policy = data.aws_iam_policy_document.assume.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate-task"
  })
}

#############################
# ECS task definition (one-off Atlas migration, Fargate, arm64)
#############################
# arm64/Graviton Fargate — ~20% cheaper than x86; the arigaio/atlas base is multi-arch.
resource "aws_ecs_task_definition" "this" {
  family                   = "${var.name_prefix}-migrate"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.cpu
  memory                   = var.memory

  execution_role_arn = aws_iam_role.exec.arn
  task_role_arn      = aws_iam_role.task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "ARM64"
  }

  container_definitions = jsonencode([
    {
      name      = "migrate"
      image     = "${aws_ecr_repository.migrate.repository_url}:${var.image_tag}"
      essential = true
      # Image entrypoint is `atlas`; `--env aws` is defined in migrations/atlas.hcl baked into the image.
      command = ["migrate", "apply", "--env", "aws"]

      environment = [
        { name = "DB_HOST", value = var.aurora_endpoint },
        { name = "DB_PORT", value = tostring(var.aurora_port) },
        { name = "DB_NAME", value = var.database_name },
        { name = "DB_USER", value = var.db_username },
      ]

      # Pull the `password` key out of the JSON {username,password} secret.
      secrets = [
        { name = "DB_PASSWORD", valueFrom = "${var.db_secret_arn}:password::" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.this.name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "migrate"
        }
      }
    }
  ])

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-migrate"
  })
}
