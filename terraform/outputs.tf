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

output "clickhouse_endpoint" {
  description = "Clickhouse cluster endpoint"
  value       = "To be added in Week 3"
}

output "prometheus_url" {
  description = "Prometheus monitoring endpoint"
  value       = "To be added in Week 7"
}