output "bootstrap_servers" {
  description = "Kafka bootstrap server endpoints"
  value       = aws_msk_cluster.settlement_pipeline.bootstrap_brokers
}

output "bootstrap_servers_tls" {
  description = "Kafka bootstrap server TLS endpoints"
  value       = aws_msk_cluster.settlement_pipeline.bootstrap_brokers_tls
}

output "cluster_arn" {
  description = "ARN of Kafka cluster"
  value       = aws_msk_cluster.settlement_pipeline.arn
}

output "security_group_id" {
  description = "Security group ID for Kafka"
  value       = aws_security_group.kafka.id
}

output "kafka_version" {
  description = "Kafka version"
  value = aws_msk_cluster.settlement_pipeline.kafka_version
}
