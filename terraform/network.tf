# The account's default VPC, rather than a purpose-built one. The task needs
# a public subnet ONLY for egress -- pulling its image from ECR and dialling
# out to Cloudflare -- and accepts no inbound traffic at all. Building a VPC
# would mean an internet gateway, route tables and more IAM surface for no
# benefit; a private subnet would mean a NAT gateway at ~$32/month, which is
# 30x the entire rest of this deployment.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

# No ingress rules whatsoever. Nothing reaches this task from the internet:
# cloudflared establishes an OUTBOUND tunnel to Cloudflare, and traffic
# arrives back down that connection. This is what removes the need for a load
# balancer (~$16/month, more than everything else combined) and means there
# is no public listener to attack.
resource "aws_security_group" "task" {
  name        = "${var.APP_NAME}-task"
  description = "Egress-only; inbound arrives via the Cloudflare tunnel"
  vpc_id      = data.aws_vpc.default.id

  egress {
    description = "All outbound (ECR pull, CloudWatch logs, Cloudflare tunnel)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.APP_NAME}-task" }
}
