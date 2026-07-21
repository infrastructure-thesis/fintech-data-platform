output "kafka_bootstrap_servers" {
  description = "Kafka bootstrap servers"
  value       = module.kafka_cluster.bootstrap_servers
}

output "kafka_bootstrap_servers_tls" {
  description = "Kafka bootstrap servers (TLS)"
  value       = module.kafka_cluster.bootstrap_servers_tls
}

output "kafka_security_group_id" {
  description = "Kafka security group ID"
  value       = module.kafka_cluster.security_group_id
}

output "clickhouse_security_group_id" {
  description = "Clickhouse security group ID"
  value       = module.clickhouse_cluster.security_group_id
}

output "clickhouse_log_group" {
  description = "Clickhouse CloudWatch log group"
  value       = module.clickhouse_cluster.log_group_name
}
