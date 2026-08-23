terraform {
  required_version = ">= 1.10"

  # Native S3 state locking (use_lockfile) instead of a DynamoDB table -
  # requires Terraform >= 1.10, and saves running a table for one lock.
  backend "s3" {
    bucket       = "crapsim-tf-state"
    key          = "prod/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      app        = var.APP_NAME
      env        = var.ENVIRONMENT
      managed_by = "terraform"
    }
  }
}

provider "cloudflare" {
  # CLOUDFLARE_API_TOKEN from the environment.
}
