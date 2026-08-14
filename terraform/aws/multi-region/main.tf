# Multi-Region Settlement Pipeline
# Orchestrates deployments across 3 regions

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
        source  = "hashicorp/aws"
        version = "~> 5.0"
    }
  }
}

# Primary Region (us-east-1)
module "primary_region" {
  source = "../regions"

  aws_region         = "us-east-1"
  environment        = var.environment
  region_role        = "primary"
  ecs_desired_count  = 3
  enable_replication = true

  providers = {
    aws = aws.us-east-1
  }

  tags = {
    Region = "primary"
    Role   = "active"
  }
}

# Secondary Region (eu-west-1)
module "secondary_region" {
  source = "../regions"

  aws_region          = "eu-west-1"
  environment         = var.environment
  region_role         = "secondary"
  ecs_desired_count   = 3
  enable_replication  = true
  primary_db_endpoint = module.primary_region.db_endpoint

  providers = {
    aws = aws.eu-west-1
  }

  tags = {
    Region = "secondary"
    Role   = "standby"
  }

  depends_on = [module.primary_region]
}

# Tertiary Region (ap-southeast-1)
module "tertiary_region" {
  source = "../regions"

  aws_region          = "ap-southeast-1"
  environment         = var.environment
  region_role         = "tertiary"
  ecs_desired_count   = 2
  enable_replication  = true
  primary_db_endpoint = module.primary_region.db_endpoint

  providers = {
    aws = aws.ap-southeast-1
  }

  tags = {
    Region = "tertiary"
    Role   = "read-only"
  }

  depends_on = [module.primary_region]
}

# Route53 Global Health Checks
resource "aws_route53_health_check" "primary" {
  fqdn              = module.primary_region.alb_dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "settlement-primary-health"
  }
}

resource "aws_route53_health_check" "secondary" {
  fqdn              = module.secondary_region.alb_dns_name
  port              = 80
  type              = "HTTP"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30

  tags = {
    Name = "settlement-secondary-health"
  }
}

# Route53 Hosted Zone
resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Name = "settlement-zone"
  }
}

# Primary Region DNS Record
resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  alias {
    name                   = module.primary_region.alb_dns_name
    zone_id                = module.primary_region.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "Primary"
  failover_routing_policy {
    type = "PRIMARY"
  }
}

# Secondary Region DNS Record (Failover)
resource "aws_route53_record" "secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  alias {
    name                   = module.primary_region.alb_dns_name
    zone_id                = module.primary_region.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "Secondary"
  failover_routing_policy {
    type = "SECONDARY"
  }

  depends_on = [aws_route53_record.primary]
}

# Geolocation Routing (Optional: Route by geography)
resource "aws_route53_record" "us_traffic" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "us.${var.domain_name}"
  type    = "A"
  alias {
    name                   = module.primary_region.alb_dns_name
    zone_id                = module.primary_region.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "USA"
  geolocation_routing_policy {
    country = "US"
  }
}

resource "aws_route53_record" "eu_traffic" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "eu.${var.domain_name}"
  type    = "A"
  alias {
    name                   = module.primary_region.alb_dns_name
    zone_id                = module.primary_region.alb_zone_id
    evaluate_target_health = true
  }

  set_identifier = "Europe"
  geolocation_routing_policy {
    continent = "EU"
  }
}

# S3 Cross-Region Replication
resource "aws_s3_bucket" "primary_backups" {
  bucket = "settlement-backup-primary-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "settlement-primary-bachups"
  }
}

resource "aws_s3_bucket" "secondary_backups" {
  bucket = "settlement-backup-secondary-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "settlement-secondary-bachups"
  }
}

resource "aws_s3_bucket_replication_configuration" "primary" {
  depends_on = [aws_s3_bucket_versioning.primary]
  
  bucket = aws_s3_bucket.primary_backups.id

  role = aws_iam_role.s3_replication.arn

  rule {
    status = "Enabled"

    filter {
      prefix = "audit-logs/"
    }

    destination {
      bucket = aws_s3_bucket.secondary_backups.arn
      storage_class = "STANDARD_IA"
    }
  }
}

# Outputs
output "primary_endpoint" {
  value = module.primary_region.alb_dns_name
}

output "secondary_endpoint" {
  value = module.secondary_region.alb_dns_name
}

output "tertiary_endpoint" {
  value = module.tertiary_region.alb_dns_name
}

output "global_dns_name" {
  value = aws_route53_record.primary.fqdn
}

output "replication_status" {
  value = {
    primary_to_secondary = "Active"
    primary_to_tertiary = "Active"
  }
}
