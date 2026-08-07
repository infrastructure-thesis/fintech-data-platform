# AWS DEPLOYMENT Cost Analysis

## Monthly Cost Breakdown (Production)

### Compute
| Service | Type | Count | Size | Cost |
|---------|------|-------|------|------|
| MSK | Kafka Brokers | 3 | m5.large | $800 |
| RDS | Clickhouse Primary | 1 | r5.2xlarge | $400 |
| RDS | Clickhouse Replica | 1 | r5.2xlarge | $400 |
| ECS | Fargate Tasks | 3-10 | 2GB/1vCPU | $300-1000 |
| **Subtotal** | | | | **$1,900-2,600** |

### Storage
| Service | Type | Size | Cost |
|---------|-------|------|------|
| EBS | MSK Storage | 3TB | $300 |
| RDS | Snapshots | 500GB | $50 |
| S3 | Logs/Backups | 1TB | $23 |
| **Subtotal** | | | **$373** |

### Networking
| Service | Volume | Cost |
|---------|------|------|
| Data Transfer Out | 10TB/month | $900 |
| ALB | Standard | $20 |
| NAT Gateway | 3 gateways | $45 |
| **Subtotal** | | **$965** |

### Monitoring
| Service | Type | Cost |
|---------|------|------|
| CloudWatch | Logs | $50 |
| CloudWatch | Metrics | $10 |
| SNS | Notifications | $0.50 |
| **Subtotal** | | **$60** |

### **Total Monthly Cost: ~$3,360**

## Cost Optimization Opportunities

### Immediate Savings
- [ ] Use Reserved Instances (MSK): Save 30% ($240/month)
- [ ] Use Spot Instances for dev/staging: Save 70% on ECS
- [ ] Consolidate logs to S3 with Glacier archival: Save $40/month
- [ ] Optimize data transfer (Cloudwatch, VPC endpoints): Save $300+/month

### Architecture Changes
- [ ] - [ ] Single Clickhouse node (dev/staging): Save $400/month
- [ ] Reduce ECS task count from 3 to 2: Save $100/month
- [ ] Use MSK auto-scaling: Reduce peak costs 20%

## With Optimization
- **Reserved Instances:** -$240
- **Spot ECS:** -$500
- **Reduced data transfer:** -$300
- **Single Clickhouse (staging):** -$400

**Optimized Cost: ~$1,920/month (43% reduction)**

## Cost Projections
| Scale | TPS | Monthly | Annually |
|-------|-----|---------|----------|
| Startup | 100 | $2,000 | $24,000 |
| Growth | 1,000 | $3,360 | $40,320 |
| Scale | 10,000 | $8,500 | $ 102,000 |
| Enterprise | 100,000 | $45,000 | $ 540,000 |

## Budget Alerts
```bash
# Set up AWS Budget alert in Console
- Monthly limit: $5,000
- Alert at 50%, 75%, 100%
- SNS to ops-team@company.com
```

