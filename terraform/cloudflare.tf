# A locally-generated secret is what makes the tunnel token reconstructible.
# The v5 provider exposes no `token` attribute on the tunnel resource, so the
# token cloudflared needs is assembled below from the account tag, tunnel id
# and this secret -- that is the documented token format.
resource "random_password" "tunnel_secret" {
  length  = 48
  special = false
}

resource "cloudflare_zero_trust_tunnel_cloudflared" "app" {
  account_id    = var.cloudflare_account_id
  name          = "${var.APP_NAME}-${var.ENVIRONMENT}"
  tunnel_secret = base64encode(random_password.tunnel_secret.result)
}

locals {
  # cloudflared expects base64(JSON) with these exact single-letter keys.
  tunnel_token = base64encode(jsonencode({
    a = var.cloudflare_account_id
    t = cloudflare_zero_trust_tunnel_cloudflared.app.id
    s = base64encode(random_password.tunnel_secret.result)
  }))
}

# Routes everything arriving for the hostname to the app container. Both
# containers share a network namespace under awsvpc, so localhost is the app.
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "app" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.app.id

  config = {
    ingress = [
      {
        hostname = var.CUSTOM_DOMAIN
        service  = "http://localhost:${var.container_port}"
      },
      # cloudflared requires a catch-all rule as the final entry.
      {
        service = "http_status:404"
      }
    ]
  }
}

# Proxied on purpose: the CNAME points at the tunnel's internal endpoint,
# which only resolves through Cloudflare's edge. This is also what puts
# Access in the request path.
resource "cloudflare_dns_record" "app" {
  zone_id = var.cloudflare_zone_id
  name    = var.CUSTOM_DOMAIN
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.app.id}.cfargotunnel.com"
  proxied = true
  ttl     = 1 # must be 1 ("automatic") when proxied
}

# The only authentication in the entire system. The API behind it has no auth,
# no rate limiting and no cap on table creation, so this is load-bearing.
# Uses the built-in one-time-PIN identity provider: Access emails a code, so
# there is no IdP to configure and no password anywhere.
# NOTE: a service token would let the authenticated path be smoke-tested
# without a human and an email client -- which is how the waker's auth check
# shipped broken. Blocked for now: the Cloudflare API token lacks
# "Access: Service Tokens -> Edit" (403 on POST /access/service_tokens).
# Add that permission to the token to enable it.

resource "cloudflare_zero_trust_access_policy" "allowed_emails" {
  account_id = var.cloudflare_account_id
  name       = "${var.APP_NAME}-allowed-emails"
  decision   = "allow"

  include = [
    for email in var.access_emails : { email = { email = email } }
  ]
}

resource "cloudflare_zero_trust_access_application" "app" {
  account_id       = var.cloudflare_account_id
  name             = "${var.APP_NAME} (${var.ENVIRONMENT})"
  domain           = var.CUSTOM_DOMAIN
  type             = "self_hosted"
  session_duration = "24h"

  policies = [
    { id = cloudflare_zero_trust_access_policy.allowed_emails.id }
  ]
}
