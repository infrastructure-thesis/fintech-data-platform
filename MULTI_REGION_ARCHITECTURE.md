# Multi-Region Deployment Architecture

## Overview
Settlement Pipeline deployed across 3 AWS regions for:
- High availability (99.99% uptime)
- Disaster recovery (<5 minute RTO)
- Geographic redundancy
- Compliance data residency

## Regional Topology
┌─────────────────────────────────────────────────────────┐
│ Global Architecture (Multi-Region) │
├─────────────────────────────────────────────────────────┤
│ │
│ ┌──────────────────┐ ┌──────────────────┐ │
│ │ Primary Region │ │ Secondary Region │ │
│ │ (us-east-1) │ │ (eu-west-1) │ │
│ │ ───────────── │ │ ────────────── │ │
│ │ • Active ECS │ │ • Hot Standby │ │
│ │ • Primary DB │ │ • Read Replica │ │
│ │ • Primary Kafka │ │ • Replica Kafka │ │
│ │ • 3 tasks (100%) │ │ • 3 tasks (100%) │ │
│ └──────────────────┘ └──────────────────┘ │
│ ↓ ↑ ↓ ↑ │
│ Replication Replication │
│ ↓ ↑ ↓ ↑ │
│ ┌──────────────────┐ │
│ │ Tertiary Region │ │
│ │ (ap-southeast-1) │ │
│ │ ──────────────── │ │
│ │ • Warm Standby │ │
│ │ • Read Replica │ │
│ │ • 2 tasks (50%) │ │
│ └──────────────────┘ │
│ │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Global Components │ │
│ │ ────────────────────────────────────────────────│ │
│ │ • Route53 (DNS + health checks) │ │
│ │ • CloudFront (API caching) │ │
│ │ • Global Load Balancer (active-active) │ │
│ │ • DynamoDB Global Tables (replication) │ │
│ │ • S3 Cross-Region Replication (backups) │ │
│ └──────────────────────────────────────────────────┘ │
│ │
└─────────────────────────────────────────────────────────┘

## Region Strategy

### Primary Region (us-east-1)
- **Role:** Active production traffic
- **Capacity:** 100% of normal load (3 ECS tasks)
- **Database:** Primary instance (read/write)
- **Kafka:** Primary cluster
- **RTO:** N/A (active)
- **Cost:** ~$2,870/month

### Secondary Region (eu-west-1)
- **Role:** Hot standby, active-passive
- **Capacity:** 100% of normal load (3 ECS tasks)
- **Database:** Continuous replication (read-only until failover)
- **Kafka:** Mirror cluster (continuous sync)
- **RTO:** <5 minutes
- **RPO:** <1 minute (near real-time)
- **Cost:** ~$2,870/month

### Tertiary Region (eu-west-1)
- **Role:** Warm standby, read-only replica
- **Capacity:** 50% load (2 ECS tasks)
- **Database:** Read replica (async replication)
- **Kafka:** Read-only replica
- **RTO:** 15-30 minutes (requires manual intervention)
- **RPO:** 5-15 minutes
- **Cost:** ~$1,400/month

## Data Replication Strategy

### Clickhouse Replication
Primary (us-east-1)
↓ (native replication)
Secondary (eu-west-1) → Read-Only
↓ (native replication)
Tertiary (ap-southeast-1) → Read-Only

Configuration:
```xml
<!-- Replication Queue -->
<replication>
  <max_replicated_mutations_in_queue>1000</max_replicated_mutations_in_queue>
  <max_parallel_fetches_for_table>4</max_parallel_fetches_for_table>
  <min_bytes_to_use_direct_io>0</min_bytes_to_use_direct_io>
  <use_compact_format_in_fully_asynchronous_read_from_disk>true</use_compact_format_in_fully_asynchronous_read_from_disk>
</replication>
```

### Kafka Replication
Primary (us-east-1)
↓ (MirrorMaker)
Secondary (eu-west-1)
↓ (MirrorMaker)
Tertiary (ap-southeast-1)

### S3 Cross-Region Replication
- Audit logs backed up to S3 (primary region)
- Auto-replicated to secondary region
- Lifecycle policy: Move to Glacier after 30 days

## Routing Strategy

### DNS (Route53)
settlement.company.com
├─ Health check: Primary region (us-east-1)
├─ Health check: Secondary region (eu-west-1)
├─ Routing policy: Geolocation + failover
│ ├─ US traffic → us-east-1 (primary)
│ ├─ EU traffic → eu-west-1 (primary)
│ ├─ APAC traffic → ap-southeast-1 (secondary)
│ └─ Failover: Automatic to secondary on health check failure
└─ TTL: 60 seconds (quick failover)

### CloudFront Distribution
- Origin: Primary ALB (us-east-1)
- Origin failover: Secondary ALB (eu-west-1)
- Edge locations worldwide
- Cache TTL: 300 seconds (health check interval)

## Failover Scenarios

### Scenario 1: Primary Region Complete Failure (RTO: <5 min)
**Trigger:** Route53 health check fails 3 times (180 seconds)

**Automatic Actions:**
1. Route53 routes new traffic to secondary region
2. Users reconnect to secondary ALB
3. Session state recovered from distributed cache
4. Database writes resume in secondary region

**Manual Verification:**
- Verify secondary region health
- Confirm no data loss
- Monitor error rates

### Scenario 2: Primary Database Failure (RTO: <1 min)
**Trigger:** Clickhouse primary becomes unavailable

**Automatic Actions:**
1. Application connection pool detects failure
2. Retry logic attempts reconnect (max 3 retries, 100ms backoff)
3. If failure persists, DNS failover to secondary database
4. Write operations redirect to secondary

**Recovery:**
1. Diagnose primary database issue
2. Restore from backup or promote replica
3. Resync data from secondary
4. Verify data consistency

### Scenario 3: Regional Network Partition (RTO: 30 sec)
**Trigger:** Latency spike or packet loss to primary region

**Behavior:**
1. Application detects high latency on connection pool
2. Requests timeout after 30 seconds
3. Automatic retry to secondary region
4. If successful, sticky connection to secondary

**Recovery:**
1. Restore network connectivity
2. Verify DNS resolves correctly
3. Monitor connection recovery

## Database Consistency

### Write Acknowledgment Guarantees
```python
# Synchronous write to primary
response = clickhouse.execute(
    "INSERT INTO settlement.audit_log",
    data,
    settings={'insert_quorum': 2}  # Wait for 2 replicas
)

# Async replication to tertiary region
# (eventual consistency within 60 seconds)
```

### Transaction Replay
If secondary becomes primary before all transactions replicated:
1. Audit log has all transactions (immutable)
2. Replay missing transactions from logs
3. Verify checksum matches before cutover
4. Zero data loss gurantee

## Cost Model

### Three-Region Deployment
| Service | Primary | Secondary | Tertiary | Total |
|---------|---------|-----------|----------|-------|
| ECS Fargate | $500 | $500 | $250 | $1,250 |
| RDS | $400 | $400 | $200 | $1,000 |
| MSK | $800 | $800 | $400 | $2,000 |
| RDS | $800 | $800 | $400 | $2,000 |
| Data Transfer | $300 | $300 | $150 | $750 |
| **Monthly** | **$2,000** | **$2,000** | **$1,000** | **$5,000** |

### Optimization
- Use Reserved Instances: Save 30% (~$1,500)
- Use Spot for tertiary: Save 50% (~$250)
- **Optimized cost:** ~$3,250/month (13+ vs single region)

## Operational Procedures

### Health Checks
Every 60 seconds:
- Primary region health check (ECS + ALB)
- Secondary region health check (ECS + ALB)
- Database replication lag check

### Failover Testing
Monthly:
1. Simulate primary region failure
2. Verify automatic failover to secondary
3. Confirm no data loss
4. Test failback procedures
5. Document lessons learned

### Disaster Recovery Drill
Quarterly:
1. Full multi-region failover test
2. Recovery from backup scenario
3. Data consistency verification
4. Incident response team training
