# The tunnel token lives in SSM so it reaches the container as a task secret
# rather than a plaintext env var in the task definition (which is visible to
# anyone who can DescribeTaskDefinition).
#
# It does transit Terraform state. That is acceptable here because the state
# bucket is private, versioned and AES256-encrypted, and the alternative --
# creating the tunnel by hand and pasting the token in -- trades an
# encrypted-at-rest secret for a manual step that is easy to get wrong.
resource "aws_ssm_parameter" "tunnel_token" {
  name        = "${var.SSM_SECRET_PATH}/tunnel_token"
  description = "Cloudflare tunnel token for ${var.APP_NAME}"
  type        = "SecureString"
  value       = local.tunnel_token
}
