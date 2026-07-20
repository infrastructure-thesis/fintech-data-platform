# Kafka cluster for settlement pipeline

resource "aws_msk_cluster" "settlement_pipeline" {
  cluster_name           = "${var.environment}-settlement-kafka"
  kafka_version          = "3.6"
  number_of_broker_nodes = var.brokers

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    security_groups = [aws_security_group.kafka.id]
    client_subnets  = var.subnet_ids

    storage_info {
      ebs_storage_info {
        volume_size = 1000
      }
    }
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.kafka_logs.name
      }
    }
  }

  tags = {
    Name        = "${var.environment}-settlement-kafka"
    Environment = var.environment
  }
}

resource "aws_security_group" "kafka" {
  name        = "${var.environment}-kafka-sg"
  description = "Security group for Kafka cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-kafka-sg"
  }
}

resource "aws_cloudwatch_log_group" "kafka_logs" {
  name              = "/aws/msk/${var.environment}-settlement-kafka"
  retention_in_days = 7

  tags = {
    Name = "${var.environment}-kafka-logs"
  }
}
