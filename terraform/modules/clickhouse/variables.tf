variable "cluster_name" {
  type        = string
  description = "Clickhouse cluster name"
}

variable "environment" {
  type        = string
  description = "Environment (dev, prod)"
}

variable "cluster_size" {
  type        = number
  description = "Number of Clickhouse nodes"
  default     = 3
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type"
  default     = "r5.2xlarge"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet IDs for nodes"
}

variable "allowed_cidr_blocks" {
  type        = list(string)
  description = "CIDR blocks allowed to access Clickhouse"
  default     = ["10.0.0.0/8"]
}
