# Incident Response Playbook

## Severity Levels

**P1 (Critical):** Service unavailable, error rate > 5%, customer transactions failing
**P2 (Major):** Degraded performance, error rate 1-5%, some users affected
**P3 (Minor):** Non-critical issues, error rate < 1%, workaround available

---

## P1: Service Down (Error Rate > 5%)

**Trigger:** PagerDuty alert OR manual observation

**Immediate Actions (0-5 min):**
1. Declare incident in #settlement-incidents Slack
2. Initiate conference bridge: [bridge link]
3. Check service status
```bash
   aws ecs describe-services --cluster settlement-ecs-cluster
   aws ecs describe-tasks --cluster settlement-ecs-cluster
```
4. Check recent errors
```bash
   aws logs tail /ecs/settlement-service --follow
```

**Diagnosis (5-10 min):**
- [ ] Check ECS task health
- [ ] Check database connectivity
- [ ] Check Kafka availability
- [ ] Review recent deployments
- [ ] Check CloudWatch alarms

**Resolution:**
```bash
# Option 1: Restart failed tasks
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service --force-new-deployment

# Option 2: Rollback to previous version
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service \
  --task-definition settlement-task:$(($CURRENT - 1))

# Option 3: Scale down and up
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service --desired-count 0
sleep 30
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service --desired-count 3
```

**Verification (Post-Resolution):**
- [ ] Error rate < 1%
- [ ] All health checks passing
- [ ] Transactions flowing normally
- [ ] Secondary region healthy

**Post-Incident:**
- [ ] Document timeline
- [ ] Schedule retrospective (24 hours)
- [ ] Update runbooks
- [ ] Notify customers

---

## P2: Degraded Performance (1-5% Error Rate)

**Trigger:** Latency spike OR moderate error rate

**Immediate Actions:**
1. Post to #settlement-alerts Slack
2. Gather data points
```bash
   # CPU/Memory
   aws cloudwatch get-metric-statistics --metric-name CPUUtilization
   
   # Error rate
   aws logs filter-log-events --log-group-name /ecs/settlement-service
   
   # Latency
   aws cloudwatch get-metric-statistics --metric-name TargetResponseTime
```
3. Check auto-scaling
```bash
   aws autoscaling describe-auto-scaling-activities
```

**Resolution:**
- Scale up if CPU > 75%
- Restart tasks if memory high
- Check database connections

---

## P3: Minor Issues (< 1% Error Rate)

**Trigger:** Isolated errors OR slow response times

**Action:** Monitor and log
- Note in #settlement-alerts
- Track in incident tracker
- Batch for next review cycle
