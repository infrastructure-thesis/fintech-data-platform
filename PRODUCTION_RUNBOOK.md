# Production Runbook: Settlement Data Pipeline

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (40/40)
- [ ] Coverage at 86%+
- [ ] All CI/CD checks green
- [ ] Security scan passed
- [ ] Load test results reviewed
- [ ] Terraform plan validated

### Deployment Steps

**1. Deploy Infrastructure (Terraform)**
```bash
cd terraform/
terraform init
terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

**2. Configure Kafka Topics**
```bash
# Create settlement-events topic
aws kafka create-topic \
  --cluster-arn <msk-cluster-arn> \
  --topic-name settlement-events \
  --partition-count 12 \
  --replication-factor 3
```

**3. Deploy Application**
```bash
# Via Docker (ECS/Fargate)
docker build -t fintech-data-platform:v1.0 .
docker push <ecr-registry>/fintech-data-platform:v1.0

# Or via Kubernetes (ArgoCD)
kubectl apply -f k8s/deployment.yaml
```

**4. Verify Services**
```bash
# Check Kafka connectivity
kafka-console-consumer --bootstrap-servers <brokers> \
  --topic settlement-events --max-messages 1

# Check Clickhouse
clickhouse-client -h <clickhouse-host> -q "SELECT 1"

# Check metrics endpoint
curl http://<app-host>:8000/metrics
```

## Monitoring & Alerting

### Key Metrics to Track

1. **Pipeline Latency**
   - Threshold: <500ms p95
   - Alert: >1000ms p95

2. **Transaction Success Rate**
   - Threshold: >99.9%
   - Alert: <99%

3. **Clickhouse Write Errors**
   - Threshold: 0
   - Alert: >10 errors/min

4. **Kafka Consumer Lag**
   - Threshold: <1000 messages
   - Alert: >10000 messages

### Alert Destinations
- PagerDuty: `settlement-alerts`
- Slack: `#fintech-incidents`
- Email: `ops-team@company.com`

## Troubleshooting

### Issue: High Pipeline Latency
1. Check Clickhouse connection pool
2. Review Kafka broker status
3. Monitor CPU/memory on worker nodes

### Issue: Transaction Processing Failures
1. Check Clickhouse connectivity
2. Review audit logs for validation errors
3. Verify compliance hash computation

### Issue: Consumer Lag Growing
1. Scale up consumer instances
2. Increase batch size (tuning needed)
3. Check for Kafka broker issues

## Rollback Procedure

**If critical issues detected:**
```bash
# Scale down new deployment
kubectl scale deployment settlement-pipeline --replicas=0

# Revert to previous version
kubectl set image deployment/settlement-pipeline \
  app=<ecr-registry>/fintech-data-platform:v0.9

# Monitor metrics return to baseline
watch kubectl get pods
```

## Performance Targets

| Metric | Target | P95 | P99 |
|--------|--------|-----|-----|
| End-to-end latency | <100ms | <300ms | <500ms |
| Throughput | >10k txn/sec | — | — |
| Success rate | >99.9% | — | — |
| Kafka lag | <1000 msgs | — | — |

## Escalation

**Level 1 (Warning):** Slack notification
**Level 2 (Critical):** PagerDuty alert + Slack
**Level 3 (Catastrophic):** Page on-call + Executive notification

---

**Last Updated:** Day 13
**Next Review:** After 1 week in production
