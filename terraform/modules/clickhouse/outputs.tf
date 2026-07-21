output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.clickhouse.id
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.clickhouse.name
}
