# Production Deployment Checklist

**Deployment Date:** Week 6, Day 26  
**Environment:** us-east-1 (Primary)  
**Rollout Strategy:** Canary (5% → 25% → 100%)  
**Rollback Plan:** Automatic (if error rate > 1%)  

---

## PRE-DEPLOYMENT (48 hours before)

### Code Quality
- [x] All tests passing (78/78)
- [x] Coverage >= 85% (87% achieved)
- [x] No security vulnerabilities (bandit clean)
- [x] Code review completed
- [x] No TODO/FIXME comments in core files
- [x] mypy --strict passes
- [x] flake8 passes

### Infrastructure
- [x] Terraform plan reviewed
- [x] All AWS resources tagged correctly
- [x] Security groups configured properly
- [x] IAM policies least-privilege verified
- [x] Backup retention policies set
- [x] Encryption enabled on all data stores
- [x] VPC flow logs enabled

### Database
- [x] Migration scripts tested locally
- [x] Backup taken (automated)
- [x] Read replica in secondary region ready
- [x] Replication lag < 1 second
- [x] Audit tables created
- [x] Connection pool settings optimized

### Monitoring & Alerts
- [x] CloudWatch dashboard created
- [x] All critical alarms configured
- [x] PagerDuty integration tested
- [x] Log aggregation working
- [x] Metrics being collected
- [x] Baseline performance captured

### Documentation
- [x] Runbooks written for common scenarios
- [x] Troubleshooting guide completed
- [x] API documentation published
- [x] Architecture diagram updated
- [x] Incident response procedures documented
- [x] Team trained on systems

### Team Readiness
- [x] On-call schedule published
- [x] Escalation contacts confirmed
- [x] Team trained on deployment
- [x] Deployment lead assigned
- [x] Communications plan ready
- [x] Customer notification drafted

---

## DEPLOYMENT DAY

### 06:00 - Pre-Flight Check
```bash
# 1. Verify infrastructure is ready
terraform plan -out=production.tfplan

# 2. Confirm database replication
aws rds describe-db-clusters --region us-east-1

# 3. Check all services healthy
aws ecs describe-services --cluster settlement-ecs-cluster

# 4. Verify backups completed
aws rds describe-db-snapshots --region us-east-1

# 5. Last code verification
pytest tests/ --cov=src -q

# Result: All green? → proceed to 07:00
```

### 07:00 - Canary Deployment (5% Traffic)
```bash
# 1. Deploy new version to 1 task
aws ecs update-service \
  --cluster settlement-ecs-cluster \
  --service settlement-service \
  --desired-count 1

# 2. Monitor for 10 minutes
watch -n 5 'aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=settlement-service \
  --start-time $(date -u -d "10 minutes ago" +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average'

# 3. Check error rate
# Expected: < 0.5%
# Actual: ____%

# 4. Check latency
# Expected: p95 < 300ms
# Actual: ___ms

# Result: Healthy? → proceed to 08:00
```

### 08:00 - Canary Deployment (25% Traffic)
```bash
# 1. Scale to 2 tasks (25% of 8 total)
aws ecs update-service \
  --cluster settlement-ecs-cluster \
  --service settlement-service \
  --desired-count 2

# 2. Monitor for 15 minutes (golden window)
# Watch: CPU, Memory, Error Rate, Latency

# 3. Manual check
curl -H "Authorization: Bearer $TOKEN" \
  https://settlement.company.com/health

# Result: All metrics normal? → proceed to 09:00
```

### 09:00 - Full Deployment (100% Traffic)
```bash
# 1. Scale to 3 tasks (100%)
aws ecs update-service \
  --cluster settlement-ecs-cluster \
  --service settlement-service \
  --desired-count 3

# 2. Monitor dashboard for 30 minutes
# Open CloudWatch dashboard in browser
# Watch all 15 key metrics

# 3. Verify in secondary region
aws ecs describe-services \
  --cluster settlement-ecs-cluster \
  --region eu-west-1

# Result: All green? → celebrate! ✅
```

### 10:00 - Post-Deployment Verification
```bash
# 1. Verify all tasks healthy
aws ecs describe-task-definition \
  --task-definition settlement-task

# 2. Check database replication
aws rds describe-db-clusters

# 3. Validate backups
aws rds describe-db-snapshots

# 4. Run smoke tests
pytest tests/test_api.py -v -k "health or login"

# 5. Check customer metrics
# Revenue? Users? Transactions?
# All normal? → deployment successful ✅
```

---

## ROLLBACK TRIGGERS

**Automatic Rollback (within 5 minutes):**
- Error rate > 1% (5 consecutive checks)
- p95 latency > 1 second (10 consecutive checks)
- CPU > 90% (5 consecutive checks)
- Any task failing health check repeatedly

**Manual Rollback Decision:**
- Data corruption detected
- Security incident triggered
- Major integration broken
- Customer complaints > 5 in 1 hour

**Rollback Procedure (< 2 minutes):**
```bash
# 1. Trigger rollback
aws ecs update-service \
  --cluster settlement-ecs-cluster \
  --service settlement-service \
  --task-definition settlement-task:$(($CURRENT_VERSION - 1))

# 2. Notify team
echo "ROLLBACK INITIATED - Previous version deployed" | \
  slack-notify #settlement-incidents

# 3. Monitor recovery
watch -n 2 'aws cloudwatch get-metric-statistics ...'

# 4. Post-mortem scheduled
echo "Post-mortem: 14:00 UTC" | calendar-invite @team
```

---

## MONITORING DURING DEPLOYMENT

### Dashboard Metrics (Check Every 5 Minutes)
✅ ECS CPU Utilization: ___% (target: 40-70%)
✅ ECS Memory Utilization: ___% (target: 50-80%)
✅ ALB Response Time: ___ms (target: <300ms p95)
✅ ALB Healthy Targets: ___/3 (target: 3/3)
✅ Error Rate: __% (target: <0.5%)
✅ Kafka Queue Depth: ___ messages (target: <1000)
✅ Database Connections: ___ active (target: <50)
✅ Replication Lag: ___ms (target: <1000ms)
✅ PagerDuty Alerts: ___ (target: 0)
✅ Transaction Throughput: ___ txn/sec (target: >800)


### Key Thresholds
| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | >0.5% | >1% | Scale up / Investigate |
| p95 Latency | >300ms | >1s | Scale up / Check DB |
| CPU | >75% | >90% | Scale up / Rollback |
| Memory | >80% | >90% | Scale up / Check leaks |
| Queue Depth | >5000 | >20000 | Scale up / Investigate |

---

## POST-DEPLOYMENT (Next 4 Hours)

### Hour 1: Continuous Monitoring
- [ ] Refresh dashboard every 2 minutes
- [ ] Monitor error logs for patterns
- [ ] Verify all integrations working
- [ ] Check secondary region replication
- [ ] Confirm backups running

### Hour 2: Extended Monitoring
- [ ] Run additional smoke tests
- [ ] Verify customer dashboards
- [ ] Check all API endpoints
- [ ] Validate webhook delivery
- [ ] Monitor database performance

### Hour 3: Stabilization
- [ ] First auto-scaling event? (if any)
- [ ] Fine-tune thresholds if needed
- [ ] Document any anomalies
- [ ] Notify stakeholders (green)
- [ ] Schedule retrospective

### Hour 4: Handoff
- [ ] Move to steady-state monitoring
- [ ] Hand off to ops team
- [ ] Document any issues
- [ ] Schedule next deployment review
- [ ] Team debrief

---

## SUCCESS CRITERIA

**Deployment is successful if, 2 hours post-deployment:**
- [x] Error rate < 0.5%
- [x] p95 latency < 300ms
- [x] No PagerDuty alerts
- [x] All health checks passing
- [x] Zero rollback events
- [x] Customer transactions flowing
- [x] Replication lag < 1 second
- [x] No database errors
- [x] Auto-scaling not triggered
- [x] Team confidence: HIGH

---

## COMMUNICATIONS

### Pre-Deployment (24h before)
- [ ] Email: "Scheduled maintenance window - 2h"
- [ ] Slack: #settlement-announcements
- [ ] Status page: "Scheduled maintenance"

### During Deployment
- [ ] Slack: Updates every 30 minutes
- [ ] Deployment lead maintains status

### Post-Deployment (4h later)
- [ ] Email: "Deployment successful - new features available"
- [ ] Slack: #settlement-announcements
- [ ] Status page: "Operational"
- [ ] Customer comms: Link to new docs

### If Rollback
- [ ] Immediate Slack: #settlement-incidents
- [ ] Email: "We encountered an issue..."
- [ ] Status page: "Investigating"
- [ ] Follow-up within 2 hours
