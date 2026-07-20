variable "environment" {
  type        = string
  description = "Environment name (dev, prod)"
}

variable "brokers" {
  type        = number
  description = "Number of Kafka brokers"
  default     = 3
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for Kafka cluster"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for Kafka brokers"
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "CIDR blocks allowed to access Kafka"
  default     = ["10.0.0.0/8"]
}
