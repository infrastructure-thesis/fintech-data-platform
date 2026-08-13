# Production Validation Checklist

## Pre-Go-Live Validation (48 hours before)

### Infrastructure Verification
- [ ] AWS account configured correctly
- [ ] VPC, subnets, security groups in place
- [ ] MSK cluster operational and healthy
- [ ] Clickhouse database operational and healthy
- [ ] RDS backups configured and tested
- [ ] ECS cluster created with capacity providers
- [ ] ALB deployed and routing traffic
- [ ] Auto-scaling policies attached
- [ ] IAM roles and policies correct

### Application Validation
- [ ] Docker image built and scanned
- [ ] Image pushed to ECR with version tag
- [ ] ECS task definition created
- [ ] ECS service running with 3+ tasks
- [ ] All tasks healthy (ALB target health green)
- [ ] API endpoints responding correctly
- [ ] Health check endpoint: /health ✓
- [ ] Metrics endpoint: /metrics ✓
- [ ] Process endpoint: /process ✓

### Monitoring & Alerting
- [ ] CloudWatch dashboard created
- [ ] 6 alarms configured and tested
- [ ] SNS topic created and subscriptions active
- [ ] PagerDuty integration working
- [ ] Slack integration configured
- [ ] Log group created with retention policy
- [ ] CloudWatch Insights queries saved

### Security Validation
- [ ] All secrets in Secrets Manager (not env vars)
- [ ] Database encrypted at rest
- [ ] Network traffic encrypted in transit
- [ ] Security groups follow least privilege
- [ ] CloudTrail enabled for audit logs
- [ ] No hardcoded secrets in code/images
- [ ] Docker image security scan passed
- [ ] IAM permissions scoped correctly

### Load Testing
- [ ] Baseline load test passed (1000 txn/sec)
- [ ] High load test passed (5000 txn/sec)
- [ ] Response time under 300ms p95
- [ ] Error rate < 0.1%
- [ ] Auto-scaling triggered correctly
- [ ] No connection pool exhaustion
- [ ] Memory usage stable (no leaks)

### Failover Testing
- [ ] Single task failure - service recovered ✓
- [ ] Multi-task failure - service recovered ✓
- [ ] Availability zone failure - service recovered ✓
- [ ] Database connection failure - logged gracefully ✓
- [ ] Network partition - service responded correctly ✓

### Documentation Complete
- [ ] Runbook reviewed and tested
- [ ] Monitoring guide finalized
- [ ] Escalation procedures documented
- [ ] Deployment procedures documented
- [ ] Rollback procedures tested
- [ ] Team trained on procedures

---

## Day-of Go-Live Checklist

### 1-2 Hours Before Launch
- [ ] All team members ready and on-call
- [ ] Incident response channel open (#settlement-incidents)
- [ ] PagerDuty on-call rotation active
- [ ] Monitoring dashboard live and watched
- [ ] Database backups completed
- [ ] Final health checks passed
- [ ] Deployment approval obtained

### Launch Window (Gradual Rollout)
- [ ] Phase 1: Route 5% of traffic
  - [ ] Monitor for 15 minutes
  - [ ] Error rate < 0.1%
  - [ ] Latency normal
  - [ ] No alarms triggered
  
- [ ] Phase 2: Route 25% of traffic
  - [ ] Monitor for 15 minutes
  - [ ] Auto-scaling responds normally
  - [ ] No connectivity issues
  
- [ ] Phase 3: Route 100% of traffic
  - [ ] Full traffic migration
  - [ ] Monitor continuously
  - [ ] Be ready to rollback

### Immediate Post-Launch (First Hour)
- [ ] Monitor all metrics closely
- [ ] Check error logs regularly
- [ ] Verify auto-scaling behavior
- [ ] Confirm database connectivity
- [ ] Test key API endpoints manually
- [ ] Verify Prometheus metrics endpoint

### First 24 Hours
- [ ] Run additional load tests
- [ ] Monitor cost (unexpected spikes?)
- [ ] Check for memory leaks
- [ ] Verify backup retention
- [ ] Confirm alert routing works
- [ ] Test incident response procedures

### First Week
- [ ] Monitor performance baselines
- [ ] Analyze error patterns
- [ ] Review CloudWatch Insights logs
- [ ] Capacity planning for next month
- [ ] Performance optimization review
- [ ] Team retrospective

---

## Rollback Procedures

### If Critical Issues Detected

**Issue: Service not responding**
```bash
# 1. Check ECS service
aws ecs describe-services --cluster settlement-ecs-cluster --services settlement-service

# 2. Check ALB target health
aws elbv2 describe-target-health --target-group-arn arn:aws:...

# 3. View recent logs
aws logs tail /ecs/settlement-pipeline --since 10m

# 4. If unresolvable, roll back:
# Scale down new deployment
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service --desired-count 0

# 5. Update task definition to previous version
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service \
  --task-definition settlement-pipeline:PREVIOUS_VERSION \
  --desired-count 3
```

**Issue: Database connectivity**
```bash
# Check Clickhouse status
telnet clickhouse-host 9000

# Verify security group allows access
aws ec2 describe-security-groups --group-ids sg-xxxxx

# Check database logs
aws rds describe-db-instances --db-instance-identifier settlement-clickhouse
```

**Issue: High error rate**
```bash
# 1. Check recent logs for ERROR patterns
aws logs filter-log-events --log-group-name /ecs/settlement-pipeline \
  --filter-pattern "ERROR" --since 30m

# 2. Check if specific endpoint is failing
# (health, process, metrics)

# 3. If critical: redirect traffic to previous version
# Update ALB listener to point to old target group
```

---

## Success Criteria

### All Must-Have Conditions
- ✅ Zero data loss
- ✅ Error rate < 0.5% for first 24h
- ✅ Latency p95 < 300ms
- ✅ All alarms configured and alerting
- ✅ Team responded to test alerts
- ✅ No security vulnerabilities
- ✅ Database backups created

### Go/No-Go Decision
**GO if:** All conditions met + no critical issues + team confident
**NO-GO if:** Any critical issue + uncertain team + failed validation

---

## Post-Go-Live Monitoring

### Critical Metrics (Check every 5 minutes for first hour)
✓ Running task count: 3+
✓ Healthy target count: 2+
✓ Error rate: < 0.1%
✓ CPU utilization: < 70%
✓ Memory utilization: < 80%
✓ Response time p95: < 300ms
✓ No CRITICAL alarms

### Handoff to Operations
After first stable 4 hours:
- [ ] Provide Ops with monitoring dashboard
- [ ] Review escalation procedures
- [ ] Confirm on-call rotation
- [ ] Enable daily status reports
- [ ] Schedule weekly optimization reviews
