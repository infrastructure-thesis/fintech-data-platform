# Connection Pool Tuning Guide

## Current Configuration

### Clickhouse Connection Pool
```python
# src/clickhouse_client.py
POOL_SIZE = 10
POOL_RECYCLE = 3600  # 1 hour
MAX_OVERFLOW = 5
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 1.0
```

### Kafka Connection
```python
# src/pipeline/consumer.py
bootstrap_servers = ['kafka-broker-1:9092', ...]
connections_max_idle_ms = 540000  # 9 minutes
```

## Performance Tuning

### Monitor Current Usage

```bash
# Check Clickhouse connection count
clickhouse-client -q "SELECT count() FROM system.replicas"

# Monitor pool statistics
# Add to metrics.py:
@gauge_pool_size
def report_pool_size():
    return len(pool._queue)
```

### Optimization Parameters

| Parameter | Current | Recommended | Impact |
|-----------|---------|-------------|--------|
| pool_size | 10 | 20 | Better concurrent load handling |
| pool_recycle | 3600s | 1800s | Prevent stale connections |
| max_overflow | 5 | 10 | Handle traffic spikes |
| retry_attempts | 3 | 5 | Resilience to temporary failures |

### Batch Size Tuning

```python
# Test different batch sizes for throughput/latency tradeoff
batch_sizes = [50, 100, 200, 500]

for batch_size in batch_sizes:
    # Measure latency and throughput
    # Find optimal point where:
    # - Latency p95 < 300ms
    # - Throughput maximized
```

## Memory Impact

Current: ~200MB for pool + buffers
With optimization: ~300-350MB

## Testing Procedure

1. Baseline measurement (current config)
2. Adjust one parameter at a time
3. Load test for 10 minutes
4. Measure latency/throughput/memory
5. Compare to baseline
6. Deploy optimal configuration

## Expected Improvements

- Throughput: +15-25%
- Latency p95: -10-15%
- Connection failures: -50%
- Memory usage: +30-50MB
