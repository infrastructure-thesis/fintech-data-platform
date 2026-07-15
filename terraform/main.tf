terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = "fintech-data-platform"
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

# Modules called here (added Week 2)
