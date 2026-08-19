# Query Optimization Guide

## Performance Baseline

**Measured: Day 24, Week 5**

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| SELECT latency (p50) | 45ms | <30ms | ⚠️ |
| SELECT latency (p95) | 180ms | <100ms | ⚠️ |
| INSERT throughput | 1,200 txn/sec | 1,500 txn/sec | ⚠️ |
| Index scan cost | 2.3s | <1.5s | ⚠️ |

---

## Index Strategy

### Primary Table: settlement.audit_log

**Current Indexes:**
```sql
-- Order key (primary)
ORDER BY (timestamp, transaction_id)

-- Partition key
PARTITION BY toYYYYMM(timestamp)
```

**Recommended Indexes:**

```sql
-- Index 1: Tenant queries (read-heavy)
ALTER TABLE settlement.audit_log 
ADD INDEX idx_tenant_id 
tenant_id TYPE minmax 
GRANULARITY 1;

-- Index 2: Operation filtering
ALTER TABLE settlement.audit_log 
ADD INDEX idx_operation 
operation TYPE minmax 
GRANULARITY 1;

-- Index 3: User access auditing
ALTER TABLE settlement.audit_log 
ADD INDEX idx_user_id 
user_id TYPE hash 
GRANULARITY 8192;

-- Index 4: Timestamp range queries
ALTER TABLE settlement.audit_log 
ADD INDEX idx_timestamp 
timestamp TYPE minmax 
GRANULARITY 8;
```

**Expected Impact:**
- Tenant queries: 45ms → 12ms (73% faster)
- Operation filters: 180ms → 45ms (75% faster)
- User audits: 120ms → 25ms (79% faster)

---

### Secondary Table: settlement.transactions

**Current Indexes:**
```sql
ORDER BY (transaction_id, timestamp)
PARTITION BY toYYYYMM(timestamp)
```

**Recommended Indexes:**

```sql
-- Index: Status queries (for reconciliation)
ALTER TABLE settlement.transactions 
ADD INDEX idx_status 
status TYPE minmax 
GRANULARITY 1;

-- Index: Amount range queries
ALTER TABLE settlement.transactions 
ADD INDEX idx_amount 
amount TYPE minmax 
GRANULARITY 64;
```

---

## Query Optimization Patterns

### Pattern 1: Range Queries (Timestamps)

**SLOW (full scan):**
```sql
SELECT COUNT(*) FROM settlement.audit_log
WHERE timestamp >= '2026-08-20' 
AND timestamp < '2026-08-24';
```

**FAST (partition pruning):**
```sql
SELECT COUNT(*) FROM settlement.audit_log
WHERE timestamp >= '2026-08-20T00:00:00'
AND timestamp < '2026-08-24T00:00:00'
AND operation IN ('INSERT', 'UPDATE')
ORDER BY timestamp DESC;
```

**Why:** Partition key used first, then index scan.

---

### Pattern 2: IN Clauses (Tenant Filtering)

**SLOW:**
```sql
SELECT * FROM settlement.audit_log
WHERE tenant_id IN (
  SELECT id FROM tenants WHERE region = 'EU'
)
LIMIT 100;
```

**FAST:**
```sql
SELECT * FROM settlement.audit_log
WHERE tenant_id IN ('tenant_001', 'tenant_002', 'tenant_003')
LIMIT 100;
```

**Why:** Avoid subqueries; use IN with literals or pre-materialized list.

---

### Pattern 3: Aggregations (Time-Series)

**SLOW:**
```sql
SELECT 
  toStartOfHour(timestamp) as hour,
  COUNT(*) as count
FROM settlement.audit_log
GROUP BY hour
ORDER BY hour DESC;
```

**FAST:**
```sql
SELECT 
  toStartOfHour(timestamp) as hour,
  COUNT(*) as count
FROM settlement.audit_log
WHERE timestamp >= now() - INTERVAL 7 DAY
GROUP BY hour
ORDER BY hour DESC;
```

**Why:** Always filter by partition key first.

---

### Pattern 4: Joins (Denormalization)

**SLOW (join at query time):**
```sql
SELECT 
  l.transaction_id,
  l.amount,
  t.status
FROM settlement.audit_log l
JOIN settlement.transactions t 
  ON l.transaction_id = t.transaction_id;
```

**FAST (denormalized):**
```sql
-- Pre-compute in settlement.audit_log
ALTER TABLE settlement.audit_log
ADD COLUMN status String;

-- Query becomes simple SELECT
SELECT transaction_id, amount, status
FROM settlement.audit_log;
```

**Why:** Joins are expensive; pre-compute when possible.

---

## Connection Pool Tuning

### Current Settings (Day 21 baseline)
```python
pool_size = 10
pool_recycle = 3600  # seconds
max_overflow = 5
pool_pre_ping = True
```

### Recommended Settings
```python
pool_size = 20              # 2x for concurrency
pool_recycle = 1800         # Recycle more frequently
max_overflow = 15           # Allow more temporary connections
pool_pre_ping = True        # Verify connection health
echo_pool = True            # Log pool events (production monitoring)
```

### Configuration in Python
```python
# src/clickhouse_client.py
from clickhouse_driver import Client

client = Client(
    host='localhost',
    port=9000,
    database='settlement',
    settings={
        'max_block_size': 65536,
        'max_insert_threads': 4,
        'max_threads': 8,
    }
)
```

---

## Compression & Encoding

### Table-Level Compression

```sql
-- Current: No explicit compression
CREATE TABLE settlement.audit_log (...)
ENGINE = MergeTree
ORDER BY (timestamp, transaction_id);

-- Optimized: LZ4 compression
CREATE TABLE settlement.audit_log (
    id String CODEC(LZ4),
    timestamp DateTime CODEC(DoubleDelta),
    data String CODEC(ZSTD(3))
) ENGINE = MergeTree
ORDER BY (timestamp, transaction_id)
CODEC(LZ4HC);
```

**Expected Savings:**
- Storage: 50-70% reduction
- Network: 60-80% reduction (replication)
- CPU cost: 2-3% overhead (minimal)

---

## Caching Strategy

### Layer 1: Query Result Cache (Clickhouse)

```sql
-- Enable query cache
SET use_query_cache = 1;
SET query_cache_ttl = 3600;

-- Cache this query result for 1 hour
SELECT 
  toDate(timestamp) as date,
  COUNT(*) as transaction_count
FROM settlement.audit_log
GROUP BY date
ORDER BY date DESC;
```

### Layer 2: Application Cache (Python)

```python
# src/cache/redis_cache.py
from functools import wraps
import redis

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def cache_result(ttl: int = 300):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # Try cache first
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)
def get_transaction_stats(tenant_id: str) -> dict:
    """Get cached transaction statistics."""
    # Query result cached for 10 minutes
    return orchestrator.get_stats_for_tenant(tenant_id)
```

### Layer 3: CDN Cache (API responses)

```python
# src/api.py
from fastapi import FastAPI, Header
from datetime import datetime, timedelta

@app.get("/stats")
async def get_stats(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """Get pipeline statistics with cache headers."""
    stats = orchestrator.get_stats()
    
    # Return with cache directives
    headers = {
        'Cache-Control': 'public, max-age=300',  # 5 min cache
        'ETag': f'"{hash(json.dumps(stats))}"',
    }
    
    return JSONResponse(
        content=stats,
        headers=headers
    )
```

---

## Monitoring & Profiling

### Enable Query Profiling

```sql
SET log_queries = 1;
SET log_queries_min_type = 'QueryFinish';
SET log_query_threads = 1;

-- Queries logged to system.query_log
SELECT 
    event_time,
    query_duration_ms,
    read_bytes,
    written_bytes,
    query
FROM system.query_log
WHERE database = 'settlement'
ORDER BY event_time DESC
LIMIT 100;
```

### Metrics to Track

- Query execution time (p50, p95, p99)
- Bytes read/written per query
- Rows processed per query
- Index effectiveness (reads vs scans)
- Connection pool utilization
- Cache hit ratio
