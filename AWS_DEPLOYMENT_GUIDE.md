# AWS Deployment Guide: Settlement Data Pipeline

## Pre-Deployment Checklist

### AWS Account Setup
- [ ] AWS account created
- [ ] IAM user with programmatic access (not root)
- [ ] AWS CLI installed and configured
- [ ] VPC created (or use default)
- [ ] Security groups planned

### Required Permissions (IAM Policy)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "msk:*",
        "ec2:*",
        "ecr:*",
        "ecs:*",
        "eks:*",
        "rds:*",
        "cloudwatch:*",
        "logs:*",
        "s3:*",
      ],
      "Resources": "*"
    }
  ]
}
```

## Architecture on AWS
┌─────────────────────────────────────────────────────┐
│ AWS Account (fintech-settlement) │
├─────────────────────────────────────────────────────┤
│ │
│ VPC (10.0.0.0/16) │
│ ├─ Public Subnets (3): 10.0.1.0/24, 10.0.2.0/24 │
│ └─ Private Subnets (3): 10.0.11.0/24, 10.0.12.0 │
│ │
│ ┌─────────────────────────────────────────────┐ │
│ │ MSK Cluster (Kafka) │ │
│ │ • 3 broker nodes (kafka.m5.large) │ │
│ │ • 3 AZs for HA │ │
│ │ • EBS storage: 1TB per broker │ │
│ │ • Security group: port 9092, 9094 │ │
│ └─────────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────────┐ │
│ │ RDS for Clickhouse (or EC2 cluster) │ │
│ │ • Multi-AZ deployment │ │
│ │ • Automated backups │ │
│ │ • Security group: port 9000, 8123 │ │
│ └─────────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────────┐ │
│ │ ECS Fargate (Settlement Pipeline) │ │
│ │ • 3 tasks in private subnets │ │
│ │ • Auto-scaling (2-10 tasks) │ │
│ │ • CloudWatch logs │ │
│ │ • Container port: 8000 (FastAPI) │ │
│ └─────────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────────┐ │
│ │ ALB (Application Load Balancer) │ │
│ │ • Health check: /health │ │
│ │ • Target group: ECS tasks │ │
│ │ • SSL/TLS termination │ │
│ └─────────────────────────────────────────────┘ │
│ │
│ ┌─────────────────────────────────────────────┐ │
│ │ CloudWatch Monitoring │ │
│ │ • Prometheus metrics scraping │ │
│ │ • Custom dashboards │ │
│ │ • Log aggregation │ │
│ └─────────────────────────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────┘

## Deployment Phases

### Phase 1: Infrastructure (Day 16)
- MSK cluster creation
- RDS instance setup
- VPC & security groups
- IAM roles

### Phase 2: Container Registry (Day 17)
- ECR repository
- Docker image build
- Push to ECR

### Phase 3: Compute (Day 18)
- ECS cluster
- Task definition
- Fargate service
- ALB setup

### Phase 4: Monitoring (Day 19)
- Cloudwatch dashboards
- SNS topics for alerts
- PagerDuty integration
- Log aggregation

### Phase 5: Production Validation (Day 20)
- Load testing
- Failover testing
- Performance tuning
- Go-live checklist

## Estimated Costs (Monthly)
| Service | Instance | Count | Cost |
|---------|----------|-------|------|
| MSK | kafka.m5.large | 3 | ~$800 |
| Clickhouse | r5.2xlarge | 2 | ~$600 |
| ECS Fargate | 2GB/1vCPU | 3 | ~$300 |
| ALB | Standard | 1 | ~$20 |
| Data Transfer | Out (TB) | 10 | ~$900 |
| **Total** | | | **~$2,620** |

## AWS CLI Commands (Preview)
```bash
# Create MSK cluster
aws kafka create-cluster --cluster-name settlement-msk \
  --broker-node-group-info file://broker-config.json

# Create RDS Clickhouse instance
aws rds create-db-instance --db-instance-identifier settlement-clickhouse \
  --engine clickhouse

# Create ECR repository
aws ecr create-repository --repository-name fintech-data-platform

# Create ECS cluster
aws ecs create-cluster --cluster-name settlement-ecs
```

---

## Environment Variables (EC2/ECS)
```bash
KAFKA_BOOTSTRAP_SERVERS="msk-broker-1:9092,msk-broker-2:9092,msk-broker-3:9092"
CLICKHOUSE_HOST="clickhouse-primary.c123abc.us-east-1.rds.amazonaws.com"
CLICKHOUSE_PORT="9000"
AWS_REGION="us-east-1"
LOG_LEVEL="INFO"
METRICS_PORT="8000"
```

---

## Security Checklist
- [ ] VPC restricted to private subnets (no public access)
- [ ] Security groups follow principle of least privilege
- [ ] IAM roles scoped to minimum permissions
- [ ] Secrets stored in AWS Secrets Manager (no env vars)
- [ ] CloudTrail enabled for audit logging
- [ ] VPC Flow Logs enabled
- [ ] ALB with SSL/TLS certificate
- [ ] RDS encryption at rest enabled
- [ ] MSK encryption in transit enabled
