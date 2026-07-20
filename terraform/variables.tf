variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "transaction_volume_daily" {
  type        = number
  default     = 2100000
  description = "Expected daily transactions"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for infrastructure"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for resources"
}

variable "kafka_brokers" {
  type        = number
  default     = 3
  description = "Number of Kafka brokers"
}

variable "kafka_allowed_cidr_blocks" {
  type        = list(string)
  default     = ["10.0.0.0/8"]
  description = "CIDR blocks allowed to access Kafka"
}
