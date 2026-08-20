# Horizontal Scaling Strategy

## Settlement Pipeline - Growth Architecture

**Status:** Production-Ready for 10x Growth  
**Current Capacity:** 1,200 txn/sec  
**Target Capacity:** 12,000 txn/sec (10x)  
**Estimated Timeline:** Auto-scaling triggers within 2 minutes

---

## Current Baseline (Week 5)

| Metric | Value | Limit |
|--------|-------|-------|
| ECS Tasks | 3 | 100 (hard limit) |
| Throughput | 1,200 txn/sec | ~4,000 (current) |
| Latency (p95) | 180ms | <500ms |
| Memory/Task | 2GB | 4GB available |
| CPU/Task | 1024 units | 2048 available |

---

## Scaling Triggers

### CPU-Based Auto-Scaling
Target CPU Utilization: 70%

When CPU > 70% for 2 minutes:
├─ Scale up +2 tasks
├─ New tasks ready in 60 seconds
└─ Repeat until CPU < 60%

When CPU < 30% for 5 minutes:
├─ Scale down -1 task
├─ Preserve at least 2 tasks (redundancy)
└─ Repeat until CPU > 40%


### Memory-Based Auto-Scaling
Target Memory Utilization: 80%

When Memory > 80% for 3 minutes:
├─ Scale up +3 tasks (aggressive)
├─ Investigate memory leaks
└─ Consider connection pool tuning

When Memory < 20% for 10 minutes:
└─ Scale down -1 task


### Custom Metrics (Optional)
Queue Depth:

- If Kafka backlog > 100k messages
- Scale up +5 tasks immediately
- Catch up within 30 seconds

Response Time:

- If p95 latency > 500ms
- Scale up +2 tasks
- Target: p95 < 200ms


---

## Capacity Planning (10x Growth)

### Phase 1: Current (Week 5)
- 3 ECS tasks
- 1,200 txn/sec
- Single region (us-east-1)
- Cost: $2,870/month

### Phase 2: 3x Growth (Month 2-3)
- 9 ECS tasks
- 3,600 txn/sec
- Still single region
- Cost: $8,610/month
- Action: Enable secondary region read replicas

### Phase 3: 10x Growth (Month 4-6)
- 30 ECS tasks (3 regions × 10 tasks)
- 12,000 txn/sec (4,000/region)
- Multi-region active-active
- Cost: $28,700/month
- Action: Implement sharding, multi-tenant routing

### Phase 4: Beyond 10x (Month 6+)
- Distributed architecture required
- Database sharding by tenant_id
- Kafka partitioning strategy
- Global load balancing
- Cost: Custom (likely $50k+/month)

---

## Database Scaling

### Current Bottleneck: Clickhouse
Single instance can handle:

- 8 concurrent threads
- 50GB working set
- 100M rows/partition


### Solution: Read Replicas (Phase 2)
Primary (Write):
├─ us-east-1: Production writes
└─ Capacity: 5,000 txn/sec

Replicas (Read):
├─ eu-west-1: Analytics, backups
├─ ap-southeast-1: APAC queries
└─ Capacity: 10,000 txn/sec combined


### Solution: Sharding (Phase 3)
Shard by tenant_id:

Shard 1 (A-H):
├─ Tenants: tenant_001 - tenant_999
├─ Instance: clickhouse-shard-1
└─ Capacity: 4,000 txn/sec

Shard 2 (I-P):
├─ Tenants: tenant_1000 - tenant_1999
├─ Instance: clickhouse-shard-2
└─ Capacity: 4,000 txn/sec

Shard 3 (Q-Z):
├─ Tenants: tenant_2000 - tenant_2999
├─ Instance: clickhouse-shard-3
└─ Capacity: 4,000 txn/sec

Query Router:
├─ Incoming request
├─ Extract tenant_id
└─ Route to correct shard


---

## Kafka Scaling

### Current Setup
- 3 brokers
- 6 partitions (settlement.transactions)
- Replication factor: 3
- Throughput: 1,200 msg/sec

### Phase 2: Increase Partitions
6 partitions → 12 partitions
├─ Enables 2x consumer parallelism
├─ Spread across 3 brokers evenly
└─ Throughput: 2,400 msg/sec


### Phase 3: Add Brokers
3 brokers → 6 brokers
├─ 18 partitions
├─ Better fault tolerance
└─ Throughput: 4,800 msg/sec


---

## Load Balancer Strategy

### Current: Single ALB
ALB (us-east-1)
├─ 3 ECS tasks
├─ Health check: /health (10sec interval)
└─ Connection draining: 30sec


### Phase 2: Regional ALBs
ALB (us-east-1) ALB (eu-west-1)
├─ 9 tasks ├─ 9 tasks (read replicas)
└─ Primary traffic └─ Secondary traffic


### Phase 3: Global Load Balancer
Route53 (Global)
├─ Health check: all regions
├─ Routing: Geolocation + failover
└─ Clients connect to nearest region


---

## Network & Connection Limits

### Current Limits

| Resource | Current | Limit | Action at 70% |
|----------|---------|-------|---------------|
| ALB connections | 1,200 | 100,000 | None needed |
| ECS task connections | 400 | 65,535 | Monitor |
| RDS connections | 30 | 100 | Auto-scaling |
| Kafka brokers | 3 | 10 | None needed |

### Phase 3 Limits (10x)

| Resource | At 10x | Limit | Action |
|----------|--------|-------|--------|
| ALB connections | 12,000 | 100,000 | Still safe |
| ECS task connections | 4,000 | 65,535 | Monitor closely |
| RDS connections | 300 | 1,000 | Increase pool |
| Kafka brokers | 6 | 10 | Maintain headroom |

---

## Cost Optimization at Scale

### Reserved Instances (Save 30%)
Current: $2,870/month on-demand
Reserved: $2,010/month (3-year)
Savings: $860/month

At 10x scale:
Current: $28,700/month on-demand
Reserved: $20,090/month (3-year)
Savings: $8,610/month (30%)


### Spot Instances (Save 70%)
Use Spot for non-critical workloads:

- Read replicas: 70% spot
- Batch processing: 100% spot
- Dev/staging: 100% spot

Estimated savings at 10x: $15,000/month
Risk: Spot termination requires graceful shutdown


### Data Transfer Optimization
Current cross-region: $300/month

Optimization:

- Compress data before transfer (60% reduction)
- Cache frequently accessed data
- Use VPC endpoints (cheaper)
- Estimated savings: $180/month


---

## Monitoring at Scale

### Key Metrics to Track

**Application Metrics:**
- Throughput (txn/sec)
- Latency (p50, p95, p99)
- Error rate
- Queue depth

**Infrastructure Metrics:**
- CPU utilization (target: 60-70%)
- Memory utilization (target: 60-75%)
- Network throughput
- Disk I/O

**Business Metrics:**
- Revenue impact of latency
- Cost per transaction
- Customer satisfaction (NPS)

### Alerts at Scale
Critical (page on-call):
├─ Error rate > 1% (5 min)
├─ p95 latency > 1 second (10 min)
├─ Any availability zone down
└─ Database replication lag > 60 sec

Warning (Slack notification):
├─ CPU > 80% (5 min)
├─ Memory > 85% (5 min)
├─ Queue depth > 500k (10 min)
└─ Network errors > 0.1% (15 min)


---

## Testing at Scale

### Load Test Scenarios

**Scenario 1: Normal Growth**
Day 1: 1,200 txn/sec
Day 7: 2,400 txn/sec (2x)
Day 14: 3,600 txn/sec (3x)
Day 30: 6,000 txn/sec (5x)

Expected behavior:

- Auto-scaling triggers smoothly
- No error rate increase
- Latency stays <300ms (p95)


**Scenario 2: Traffic Spike**
Baseline: 1,200 txn/sec
Spike: +500% (6,000 txn/sec)
Duration: 5 minutes

Expected behavior:

- Auto-scaling triggers within 2 min
- Error rate < 0.1%
- Queue catches up within 10 min

Event: Primary database goes down
Failover target: Secondary region
Expected RTO: < 5 minutes
Expected RPO: < 1 minute

Test monthly.
