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

module "kafka_cluster" {
  source = "./modules/kafka"

  environment         = var.environment
  brokers             = var.kafka_brokers
  vpc_id              = var.vpc_id
  subnet_ids          = var.subnet_ids
  allowed_cidr_blocks = var.kafka_allowed_cidr_blocks
}

module "clickhouse_cluster" {
  source = "./modules/clickhouse"

  cluster_name        = "${var.environment}-settlement-clickhouse"
  environment         = var.environment
  cluster_size        = var.clickhouse_nodes
  instance_type       = var.clickhouse_instance_type
  vpc_id              = var.vpc_id
  subnet_ids          = var.subnet_ids
  allowed_cidr_blocks = var.clickhouse_allowed_cidr_blocks
}
