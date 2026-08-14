# Disaster Recovery Plan: Settlement Data Pipeline

## RTO/RPO Targets

| Scenario | RTO | RPO | Priority |
|----------|-----|-----|----------|
| Single service instance failure | 5 min | 0 min | P2 |
| Regional outage (primary) | <5 min | <1 min | P1 |
| Database corruption | <30 min | <5 min | P1 |
| Data center fire/flood | 1 hour | 30 min | P0 |
| Widespread AWS outage | 4 hours | 1 hour | P0 |

## Recovery Procedures

### Scenario 1: ECS Task Failure (RTO: 5 min)

**Detection:** CloudWatch alarm triggers on unhealthy targets

**Automatic Recovery:**
1. ECS marks task as failed
2. New task launched automatically (auto-scaling)
3. ALB removes failed task from pool
4. New task joins target group after health check passes (60 sec)

**Manual Verification:**
- Check CloudWatch metrics for error spike
- Verify task logs for error cause
- Confirm replacement task is healthy

**Rollback:** None needed (automatic recovery)

### Scenario 2: Primary Region Outage (RTO: <5 min)

**Detection:**
- Route53 health check fails 3x (180 sec)
- CloudWatch alarm for region-wide issues
- Manual report from customers

**Automatic Failover:**
1. Route53 detects primary region unhealthy
2. DNS updates to point to secondary region
3. Client connections redirect to secondary ALB
4. Application reads from secondary database replica

**Verification Steps:**
```bash
# 1. Verify DNS failover
dig +short settlement.company.com

# 2. Check secondary region health
aws ecs describe-services --cluster settlement-ecs-cluster \
  --services settlement-service --region eu-west-1

# 3. Verify database replication status
aws rds describe-db-clusters --region eu-west-1

# 4. Test API endpoints
curl http://secondary.settlement.company.com/health
```

**Failback Process (After Primary Recovery):**
1. Restore primary region services
2. Verify health checks passing
3. Monitor for 10 minutes
4. DNS automatically fails back when primary healthy
5. Resync any transactions from secondary

### Scenario 3: Database Corruption (RTO: 30 min)

**Detection:**
- Automated checksums fail
- Data validation errors spike
- Manual audit discovery

**Recovery Options:**

**Option A: Restore from Secondary (Best)**
```bash
# Promote secondary to primary
aws rds promote-read-replica \
  --db-instance-identifier settlement-db-secondary \
  --region eu-west-1 --backup-retention-period 7

# Verify data integrity
aws rds describe-db-instances --region eu-west-1
```

**Option B: Restore from Backup**
```bash
# List available backups
aws rds describe-db-snapshots \
  --db-instance-identifier settlement-db \
  --region us-east-1

# Create new database from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier settlement-db-recovered \
  --db-snapshot-identifier settlement-db-2026-08-22-03-00

# Restore audit logs from S3
aws s3 sync s3://settlement-backups/audit-logs/ ./recovery/
```

**Verification:**
```bash
# Verify restored data
SELECT COUNT(*) FROM audit_log;
SELECT MAX(timestamp) FROM audit_log;

# Compare with secondary
// Run equivalent query on secondary
// Verify counts match
```

### Scenario 4: Data Center Failure (RTO: 1 hour)

**Scope:** Entire AWS region becomes unavailable

**Automatic Actions:**
1. Route53 failover to secondary region (5 min)
2. Secondary region becomes primary for all traffic
3. Tertiary region can be promoted if secondary fails

**Manual Actions:**

**Step 1: Assess Damage**
```bash
# Check all regions status
for region in us-east-1 eu-west-1 ap-southeast-1; do
  echo "Region: $region"
  aws ec2 describe-instances --region $region \
    --filters "Name=tag:Environment,Values=prod" \
    --query 'Reservations[].Instances[].[InstanceId,State.Name]'
done
```

**Step 2: Promote Secondary to Primary**
```bash
# Create RDS instance from secondary read replica
aws rds promote-read-replica \
  --db-instance-identifier settlement-db-secondary \
  --region eu-west-1 --backup-retention-period 7

# Confirm Kafka mirror is now primary
# Update configuration to accept writes
```

**Step 3: Redeploy Primary Region**
```bash
# Scale down failed region
aws ecs update-service --cluster settlement-ecs-cluster \
  --service settlement-service --desired-count 0 \
  --region us-east-1

# Wait for AWS to restore services (manual/AWS dependent)
# Then redeploy with Terraform
cd terraform/aws/multi-region
terraform apply -target=module.primary_region
```

**Step 4: Restore Replication**
```bash
# Once primary is healthy, resync from secondary
# Setup replication from secondary (now acting as primary)
# Monitor replication lag until caught up
```

### Scenario 5: Widespread AWS Outage (RTO: 4 hours)

**Scope:** Multiple AWS regions affected

**Immediate Actions:**
1. Activate disaster recovery command center
2. Page L3+ on-call (all hands)
3. Open incident in PagerDuty
4. Create executive bridge

**Recovery (Assuming at least one region available):**

**If Primary + Secondary Down, Tertiary Available:**
1. Promote tertiary region to primary
2. Accept 5-15 minutes of data loss (async replication gap)
3. Redirect all traffic to tertiary region
4. Restore at least one other region for redundancy
5. Resume normal operations once restored

**If All Regions Down:**
1. Wait for AWS recovery
2. Deploy to first available region
3. Restore from S3 backup (audit logs only)
4. Accept data loss up to last S3 backup
5. Issue customer notification

**Recovery Steps:**
```bash
# Assume tertiary region is still available
# 1. List available EBS snapshots (cross-region)
aws ec2 describe-snapshots --region ap-southeast-1 \
  --filters "Name=tag:BackupType,Values=daily"

# 2. Create volume from latest snapshot
aws ec2 create-volume --availability-zone ap-southeast-1a \
  --snapshot-id snap-xxxxx

# 3. Restore audit logs from S3 Glacier
aws s3 sync s3://settlement-backups/archive/ ./recovery/ \
  --storage-class GLACIER
```

## Testing Schedule

### Monthly Failover Test
- Simulate primary region failure
- Verify automatic failover to secondary
- Confirm DNS updates correctly
- Test failback procedures
- Document time to recover
- **Success Criteria:** RTO < 5 min, zero data loss

### Quarterly Disaster Recovery Drill
- Full multi-region recovery test
- Database restore from backup
- Data consistency verification
- Team communication drill
- Post-incident review
- **Success Criteria:** RTO < 1 hour, RPO < 30 min

### Annual Full Disaster Test
- Simulate regional failure + backup corruption
- Test recovery procedures from scratch
- Verify disaster recovery runbook accuracy
- Team training on rarely-used procedures
- **Success Criteria:** All procedures documented and tested

## Communication Plan

**Immediate (0-5 min):**
- Page on-call engineer in primary region
- Create incident in PagerDuty
- Post to #settlement-incidents Slack

**Escalation (5-15 min):**
- Page L2+ if P1 incident not resolving
- Notify platform team lead
- Prepare customer communication

**Customer Communication (15+ min):**
- Post to status page
- Email affected customers
- Prepare incident report

**Post-Incident (2-24 hours):**
- Schedule post-incident review
- Update runbooks based on findings
- Notify customers of resolution
- Share findings with team

## Runbook Maintenance

Update procedures:
- After each incident
- After each disaster recovery drill
- After AWS service changes
- Quarterly review for accuracy

**Runbook version:** 1.0
**Last updated:** Day 22, Week 5
**Next review:** Day 22, Week 6
