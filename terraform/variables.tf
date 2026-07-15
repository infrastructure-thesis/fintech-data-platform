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

variable "kafka_brokers" {
  type    = number
  default = 3
}

variable "kafka_auto_scaling" {
  type    = bool
  default = true
}

variable "clickhouse_shards" {
  type    = number
  default = 2
}
