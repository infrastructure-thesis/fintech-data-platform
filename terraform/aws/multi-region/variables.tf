variable "environment" {
  type        = string
  description = "Environment (dev, staging, prod)"
  default     = "prod"
}

variable "domain_name" {
  type        = string
  description = "Domain name for settlement pipeline"
}

variable "primary_region" {
  type    = string
  default = "us-east-1"
}

variable "secondary_region" {
  type    = string
  default = "eu-west-1"
}

variable "tertiary_region" {
  type    = string
  default = "ap-southeast-1"
}

variable "enable_tertiary" {
  type        = bool
  description = "Enable tertiary region deployment"
  default     = true
}

variable "replication_mode" {
  type        = string
  description = "active-active or active-passive"
  default     = "active-passive"

  validation {
    condition = can(regex("^(active-active|active-passive)$", var.replication_mode))
    error_message = "Must be active-active or active-passive"
  }
}

data "aws_caller_identity" "current" {}
