output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.app.name
}

output "ecs_service" {
  value = aws_ecs_service.app.name
}

output "app_url" {
  value = "https://${var.CUSTOM_DOMAIN}"
}

output "tunnel_id" {
  value = cloudflare_zero_trust_tunnel_cloudflared.app.id
}

output "log_group" {
  value = aws_cloudwatch_log_group.app.name
}

# Consumed once, when configuring the Cloudflare Worker's secrets.
output "waker_access_key_id" {
  value     = aws_iam_access_key.waker.id
  sensitive = true
}

output "waker_secret_access_key" {
  value     = aws_iam_access_key.waker.secret
  sensitive = true
}
