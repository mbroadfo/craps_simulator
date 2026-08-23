# Names match the TF_VAR_* GitHub variables set by scripts/bootstrap.ps1.
variable "APP_NAME" {
  description = "Resource name prefix, e.g. crapsim."
  type        = string
}

variable "ENVIRONMENT" {
  description = "Deployment environment; only prod is used today."
  type        = string
  default     = "prod"
}

variable "CUSTOM_DOMAIN" {
  description = "Hostname the app is served at."
  type        = string
}

variable "SSM_SECRET_PATH" {
  description = "SSM path prefix for this app's secrets."
  type        = string
}

variable "aws_region" {
  type    = string
  default = "us-west-2"
}

# Not committed: this repo is public, and while these are identifiers
# rather than credentials, there is no reason to publish them. Supplied
# via TF_VAR_cloudflare_* (GitHub variables in CI, exported locally).
variable "cloudflare_account_id" {
  type = string
}

variable "cloudflare_zone_id" {
  type = string
}

variable "access_emails" {
  description = <<-EOT
    Emails allowed through Cloudflare Access. This is the ONLY authentication
    in front of the app: the API itself has no auth, no rate limiting and no
    cap on who may create tables, so an empty or wrong list here means the
    endpoint is effectively open.
  EOT
  type        = list(string)

  validation {
    condition     = length(var.access_emails) > 0
    error_message = "At least one email must be allowed, or nobody can reach the app."
  }
}

variable "task_cpu" {
  description = "Fargate CPU units. 512 = 0.5 vCPU."
  type        = number
  default     = 512
}

variable "task_memory" {
  description = <<-EOT
    Fargate memory (MiB). 1024 rather than 512: the engine holds each table's
    event buffer in memory, and 512 leaves no headroom once a few sessions
    have run. The price difference is cents at ~30 hrs/month.
  EOT
  type        = number
  default     = 1024
}

variable "idle_shutdown_minutes" {
  description = "Minutes of no HTTP activity before the task scales itself to zero."
  type        = number
  default     = 20
}

variable "container_port" {
  type    = number
  default = 8000
}
