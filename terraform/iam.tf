data "aws_caller_identity" "current" {}

# ---------------------------------------------------------------- execution
# Used by the ECS agent (not the app): pulls the image, writes log streams,
# and reads the tunnel token out of SSM to inject as a secret.
resource "aws_iam_role" "execution" {
  name = "${var.APP_NAME}-task-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_managed" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "read-tunnel-token"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ssm:GetParameters"]
      Resource = aws_ssm_parameter.tunnel_token.arn
    }]
  })
}

# --------------------------------------------------------------------- task
# Used by the application itself. Its only privilege is scaling its OWN
# service to zero, which is how the container shuts itself down after an idle
# period instead of running (and billing) around the clock.
resource "aws_iam_role" "task" {
  name = "${var.APP_NAME}-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "task_self_scale" {
  name = "scale-self-to-zero"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
      Resource = "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/${var.APP_NAME}/${var.APP_NAME}"
    }]
  })
}

# -------------------------------------------------------------------- waker
# Credentials for the Cloudflare Worker that wakes the service on the first
# request of the day. Deliberately a user rather than a role: a Worker cannot
# assume an AWS role, so it needs a long-lived key -- scoped here to starting
# and inspecting exactly one service, and nothing else.
resource "aws_iam_user" "waker" {
  name = "${var.APP_NAME}-waker"
}

resource "aws_iam_user_policy" "waker" {
  name = "wake-service"
  user = aws_iam_user.waker.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ecs:UpdateService", "ecs:DescribeServices"]
      Resource = "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:service/${var.APP_NAME}/${var.APP_NAME}"
    }]
  })
}

resource "aws_iam_access_key" "waker" {
  user = aws_iam_user.waker.name
}
