# The missing "HTTP request arrives -> start the task" primitive. AWS has no
# such thing for ECS, so this Worker sits on the hostname's route, notices the
# origin is down, asks ECS for one task, and holds the visitor on a
# self-refreshing page until the container answers.
resource "cloudflare_workers_script" "waker" {
  account_id  = var.cloudflare_account_id
  script_name = "${var.APP_NAME}-waker"
  content     = file("${path.module}/../worker/waker.js")
  main_module = "waker.js"

  # Pinned rather than floating: AbortSignal.timeout and the module-worker
  # format both depend on runtime behaviour, and a silently shifting runtime
  # under an unattended waker is not worth the freshness.
  compatibility_date = "2026-08-01"

  # Persist console output. Debugging this Worker from request analytics
  # alone was guesswork: analytics said "ran, no errors" while the wake
  # silently never fired, with no way to see which branch it took.
  observability = {
    enabled            = true
    head_sampling_rate = 1
  }

  bindings = [
    { name = "AWS_REGION", type = "plain_text", text = var.aws_region },
    { name = "ECS_CLUSTER", type = "plain_text", text = aws_ecs_cluster.app.name },
    { name = "ECS_SERVICE", type = "plain_text", text = aws_ecs_service.app.name },
    # A Worker cannot assume an AWS role, so this is a long-lived key -- scoped
    # by terraform/iam.tf to UpdateService/DescribeServices on this one service
    # ARN and nothing else.
    { name = "AWS_ACCESS_KEY_ID", type = "secret_text", text = aws_iam_access_key.waker.id },
    { name = "AWS_SECRET_ACCESS_KEY", type = "secret_text", text = aws_iam_access_key.waker.secret },
  ]
}

# Covers the whole hostname: any path can be the one that wakes it, since the
# visitor may deep-link rather than hit "/".
resource "cloudflare_workers_route" "waker" {
  zone_id = var.cloudflare_zone_id
  pattern = "${var.CUSTOM_DOMAIN}/*"
  script  = cloudflare_workers_script.waker.script_name
}
