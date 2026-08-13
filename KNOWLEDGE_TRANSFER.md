# Knowledge Transfer: Settlement Data Pipeline Operations

## Operations Team Onboarding

### Day 1: Architecture Overview (1 hour)
- [ ] Watch 10-minute architecture video
- [ ] Review high-level diagram
- [ ] Understand data flow (Kafka → Transformer → Clickhouse)
- [ ] Know key AWS services (ECS, ALB, RDS, MSK)

### Day 2: Monitoring & Alerting (2 hours)
- [ ] Access CloudWatch dashboard
- [ ] Understand metric meanings (CPU, latency, errors)
- [ ] Test alert routing (email, Slack, PagerDuty)
- [ ] Practice acknowledging incidents

### Day 3: Common Troubleshooting (2 hours)
- [ ] Query logs in CloudWatch Insights
- [ ] Identify and resolve common errors
- [ ] Practice scaling tasks manually
- [ ] Review runbook for task failure

### Day 4: Incident Response (2 hours)
- [ ] Walk through incident response procedure
- [ ] Practice communication with team
- [ ] Understand escalation path
- [ ] Review post-incident review process

### Day 5: Hands-On Validation (3 hours)
- [ ] Deploy hotfix to staging
- [ ] Monitor deployment through all stages
- [ ] Handle simulated incident
- [ ] Complete post-incident checklist

---

## Quick Reference

### Access Points
- **Dashboard:** https://console.aws.amazon.com/cloudwatch/#dashboards:name=settlement-pipeline
- **Logs:** https://console.aws.amazon.com/cloudwatch/home#logsV2:logs-insights
- **ECS:** https://console.aws.amazon.com/ecs/v2/clusters/settlement-ecs-cluster
- **PagerDuty:** https://pagerduty.com/incidents

### Common Commands
```bash
# View service status
aws ecs describe-services --cluster settlement-ecs-cluster --services settlement-service

# View task logs (last 100 lines)
aws logs tail /ecs/settlement-pipeline --max-items 100 --follow

# Scale tasks manually
aws ecs update-service --cluster settlement-ecs-cluster --service settlement-service --desired-count 5

# Check ALB health
aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:...
```

### SLA Targets
| Metric | SLA |
|--------|-----|
| Availability | 99.9% (8.7 hours/month) |
| Incident Response | <5 min for P1, <30 min for P2 |
| Recovery Time | <10 minutes |
| Error Rate | <0.5% |

---

## Decision Tree for Troubleshooting
Issue: API not responding

├─ Check service health
│ ├─ Running count: 0?
│ │ └─ Restart service: aws ecs update-service ... --desired-count 3
│ └─ Running count: >0?
│ └─ Check logs for errors
│
├─ Check database connectivity
│ ├─ Can connect to Clickhouse?
│ │ ├─ No → Check security groups, RDS status
│ │ └─ Yes → Database issue not root cause
│
├─ Check Kafka connectivity
│ ├─ Consumer lag high?
│ │ ├─ Yes → Scale up tasks or optimize batch size
│ │ └─ No → Issue elsewhere
│
└─ Escalate to platform team if unresolved

---

## On-Call Runbook

### Alert: High CPU (>80%)
1. Check current CPU in dashboard
2. If >85%, scale up: `aws ecs update-service ... --desired-count 10`
3. Monitor for 5 minutes
4. If still high, check logs for inefficient code
5. If code issue, trigger hotfix deployment

### Alert: Task Unhealthy
1. Check task logs: `aws logs tail /ecs/settlement-pipeline`
2. Common causes:
   - Database unavailable → Check RDS status
   - Out of memory → Scale up task memory or count
   - Code crash → Check recent deployments
3. If critical, drain traffic and restart: `aws ecs update-service ... --desired-count 0 && sleep 30 && aws ecs update-service ... --desired-count 3`

### Alert: High Error Rate (>1%)
1. Query recent errors: `aws logs filter-log-events ... --filter-pattern ERROR`
2. Identify error pattern (database, Kafka, validation?)
3. If data validation error → Check input format
4. If database error → Check connection pool, Clickhouse status
5. If critical → Rollback to previous version

### During Incident
1. Create incident in PagerDuty
2. Notify #settlement-incidents Slack channel
3. Follow runbook procedures
4. Document steps taken
5. Post all-clear when recovered
6. Schedule post-incident review within 24 hours

---

## Monthly Tasks

- [ ] Review CloudWatch logs for errors and trends
- [ ] Analyze cost breakdown and optimization opportunities
- [ ] Check for security updates (base image, dependencies)
- [ ] Capacity planning for next month
- [ ] Team knowledge sharing session
- [ ] Runbook accuracy review

---

## Escalation Contact

| Level | Contact | Response Time |
|-------|---------|----------------|
| L1 | On-call engineer | 5 minutes |
| L2 | Team lead | 15 minutes |
| L3 | Platform manager | 30 minutes |

PagerDuty: settlement-alerts (automatic)
Slack: @settlement-oncall (mention in #settlement-incidents)
