# Monitoring & Observability Guide

## Dashboard Access

### CloudWatch Dashboard
https://console.aws.amazon.com/cloudwatch/home#dashboards:name=settlement-pipeline

Displays:
- ECS CPU/Memory utilization
- ALB response times & request counts
- Pipeline metrics (transactions, latency)
- Error rates (4xx, 5xx)
- Recent error logs

### Metrics to Watch
| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU % | > 70% | > 85% | Scale up |
| Memory % | > 75% | > 90% | Scale up |
| Response Time | > 300ms | > 500ms | Debug latency |
| Error Rate | > 1% | > 5% | Check logs |
| Task Count | < 2 | 0 | Auto-scale triggered |

## Log Analysis

### Query Recent Errors
```bash
aws logs tail /ecs/settlement-pipeline --since 1h --follow
```

### Filter by Level
```bash
aws logs filter-log-events \
  --log-group-name /ecs/settlement-pipeline \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s%000)))
```

### CloudWatch Insights Query
fields @timestamp, @message, @logStream
| filter @message like /ERROR/
| stats count() by #logStream

## Alerts & Notification

### Alert Channels
- **Email:** ops-team@company.com
- **Slack:** #settlement-incidents
- **PagerDuty:** Critical incidents only

### Alert Response Time
- Warning: 15 minutes
- Critical: 5 minutes (paged on-call)

## Performance Baselines

### Normal Operation
Latency p50: 50ms
Latency p95: 200ms
Latency p99: 300ms
Throughput: 1000+ txn/sec
Success Rate: >99.9%
CPU: 30-40%
Memory: 50-60%

### Under Load
Latency p50: 80ms
Latency p95: 300ms
Latency p99: 500ms
Throughput: 5000+ txn/sec
Success Rate: >99.9%
CPU: 70-80%
Memory: 75-85%

## Incident Response

### When alert fires:
1. Check dashboard for metric context
2. Review logs for error patterns
3. Check service health (ECS tasks, ALB targets)
4. If needed, trigger manual scaling
5. Communicate status to team

### Escalation:
- L1 (Engineer): 30 minutes
- L2 (Lead): 30 minutes
- L3 (Manager): 30 minutes

## Monthly Review
Every month:
- [ ] Review alert accuracy (false positives?)
- [ ] Update baselines based on growth
- [ ] Analyze error trends
- [ ] Capacity planning for next month
- [ ] Cost optimization review

## Custom Metrics
Add pipeline metrics to CloudWatch:

```python
from src.metrics import *
import boto3

cloudwatch = boto3.client('cloudwatch')

# Publish custom metric
cloudwatch.put_metric_data(
    Namespace='settlement-pipeline',
    MetricData=[
        {
            'MetricName': 'batch_processing_time',
            'Value': elapsed_ms,
            'Unit': 'Milliseconds'
        }
    ]
)
```

## Cost Optimization

### Monitor CloudWatch Costs
```bash
# Get CloudWatch bill estimate
aws ce get-cost-and-usage \
  --time-period Start=2026-08-01,End=2026-08-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

### Reduce Costs
- Adjust log retention (30 days is current)
- Use log sampling for high-volume services
- Archive old logs to S3 with Glacier
