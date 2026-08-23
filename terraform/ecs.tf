resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.APP_NAME}"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "app" {
  name = var.APP_NAME
}

# Two containers sharing one task. Under awsvpc they share a network
# namespace, so cloudflared reaches the app over localhost with no service
# discovery and no measurable latency.
resource "aws_ecs_task_definition" "app" {
  family                   = var.APP_NAME
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name = "app"
      # :latest on purpose. The service idles at desired_count 0, so there is
      # no running task to roll; whatever was last pushed is picked up on the
      # next wake. CI registers a new revision rather than forcing a
      # deployment.
      image     = "${aws_ecr_repository.app.repository_url}:latest"
      essential = true

      portMappings = [{
        containerPort = var.container_port
        protocol      = "tcp"
      }]

      environment = [
        { name = "PORT", value = tostring(var.container_port) },
        { name = "CRAPS_STATIC_DIR", value = "/app/static" },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "CRAPS_ECS_CLUSTER", value = var.APP_NAME },
        { name = "CRAPS_ECS_SERVICE", value = var.APP_NAME },
        { name = "CRAPS_IDLE_SHUTDOWN_MINUTES", value = tostring(var.idle_shutdown_minutes) },
      ]

      healthCheck = {
        command     = ["CMD-SHELL", "python -c \"import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'), timeout=2)\" || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 30
      }

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
    },
    {
      name      = "cloudflared"
      image     = "cloudflare/cloudflared:latest"
      essential = true
      command   = ["tunnel", "--no-autoupdate", "run"]

      # As a task secret, not an environment value: plain environment entries
      # are readable by anyone who can DescribeTaskDefinition.
      secrets = [
        { name = "TUNNEL_TOKEN", valueFrom = aws_ssm_parameter.tunnel_token.arn }
      ]

      # Without this the tunnel can come up before the app is listening and
      # serve 502s on the very first request after a wake.
      dependsOn = [{ containerName = "app", condition = "HEALTHY" }]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "cloudflared"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = var.APP_NAME
  cluster         = aws_ecs_cluster.app.id
  task_definition = aws_ecs_task_definition.app.arn
  launch_type     = "FARGATE"

  # Idles at zero. The Cloudflare Worker scales it to 1 on the first request,
  # and the app scales itself back to 0 after idle_shutdown_minutes. This is
  # the whole cost model: ~30 hrs/month instead of 730.
  desired_count = 0

  network_configuration {
    subnets = data.aws_subnets.default.ids
    # Public IP is for EGRESS only -- the security group has no ingress rules.
    # The alternative, a private subnet, needs a NAT gateway at ~$32/month.
    assign_public_ip = true
    security_groups  = [aws_security_group.task.id]
  }

  # Both are managed outside Terraform by design: desired_count is driven by
  # the waker and the app's own idle shutdown, and task_definition is bumped
  # by CI on each image push. Without these, every terraform apply would fight
  # them and reset the service.
  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }
}
