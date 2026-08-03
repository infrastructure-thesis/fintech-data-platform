# fintech-data-platform

Production-grade settlement data pipeline for elite fintech roles (Stripe, Wise, Revolut, Toss).

## Overview

Real-time settlement transaction processing with compliance hashing, batch orchestration, and comprehensive monitoring.

**Stack:** Kafka + Clickhouse + Python + Terraform + ArgoCD + Prometheus

## Architecture

Kafka Consumer → Transaction Parser → Compliance Hashing → Clickhouse Writer
↓
Prometheus Metrics

## Week-by-Week Progress

### Week 1: Foundation ✅
- Core Python models (Transaction, AuditLogEntry)
- Kafka consumer skeleton
- Clickhouse writer stub
- 24 tests, 99% coverage

### Week 2: Infrastructure ✅
- Terraform Kafka module (MSK cluster)
- Terraform Clickhouse module (security groups, logging)
- Docker Compose (local dev environment)
- Integration tests (docker-compose orchestration)
- Pipeline orchestrator (batch processing)
- 35 tests, 97.79% coverage

### Week 3: Integration & Monitoring ✅
- Real Clickhouse client (connection pooling, retry logic)
- Kafka consumer loop (continuous processing)
- Prometheus metrics (latency, throughput, errors)
- Metrics HTTP endpoint (FastAPI)
- 40 tests, 86% coverage

## Quick Start

### Local Development
```bash
docker-compose -f docker/compose.yml up -d
pytest tests/ --cov=src
black src/ tests/
flake8 src/ tests/
mypy src/ --strict
```

### Infrastructure
```bash
cd terraform/
terraform init
terraform plan -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

## Features

✅ **Compliance Ready**
- SHA-256 transaction hashing (FCA/SOX)
- Audit log tracking
- Regional compliance checks

✅ **High Performance**
- Batch processing (configurable size)
- Connection pooling (Clickhouse)
- Pipeline latency metrics

✅ **Observable**
- Prometheus metrics endpoint
- Transaction success/failure tracking
- Pipeline stage latency
- Consumer lag monitoring

✅ **Resilient**
- Retry logic with exponential backoff
- Comprehensive error handling
- Graceful degradation

## Testing

- **39 unit tests** (core logic, mocked integrations)
- **8 integration tests** (skipped without live services)
- **86% code coverage**
- **CI/CD:** GitHub Actions (all checks automated)

## Deployment

**Week 4 focus:**
- AWS/GCP deployment
- Production alerting (PagerDuty/Slack)
- Load testing & optimization
- API documentation (OpenAPI)
- Monitoring dashboard (Grafana)

## Repository Structure

fintech-data-platform/
├── src/
│ ├── pipeline/ # Core processing (consumer, transformer, writer)
│ ├── audit/ # Compliance hashing
│ ├── clickhouse_client.py
│ ├── kafka_consumer_loop.py
│ ├── metrics.py # Prometheus metrics
│ └── metrics_server.py # HTTP endpoint
├── terraform/ # Infrastructure as Code
│ ├── modules/
│ │ ├── kafka/ # MSK cluster
│ │ └── clickhouse/ # Database
│ └── environments/ # dev.tfvars, prod.tfvars
├── docker/ # Docker Compose
├── tests/ # Comprehensive test suite
└── README.md

## Contact & Status

**Elite Fintech Positioning:** Stripe, Wise, Revolut, Toss

**PE Portfolio Track:** HG Capital (Value Creation Analyst)

**Portfolio Status:** Production-ready, Week 4 deployment phase
