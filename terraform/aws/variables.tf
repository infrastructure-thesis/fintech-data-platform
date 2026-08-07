variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment (dev, staging, prod)"
  default     = "dev"

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.enviroment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "msk_broker_count" {
  type        = number
  description = "Number of MSK brokers"
  default     = 3
}

variable "msk_instance_type" {
  type        = string
  description = "MSK broker instance type"
  default     = "kafka.m5.large"
}

variable "clickhouse_instance_type" {
  type        = string
  description = "Clickhouse instance type (RDS or EC2)"
  default     = "r5.2xlarge"
}

variable "ecs_task_count" {
  type        = number
  description = "Number of ECS tasks"
  default     = 3
}
