#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REPORT_FILE="db_profile_$(date +%Y%m%d_%H%M%S).txt"

{
  echo "Settlement Pipeline - Database Performance Profile"
  echo "=================================================="
  echo "Generated: $(date)"
  echo ""

  echo "1. TABLE SIZES & ROW COUNTS"
  echo "==========================="
  
  clickhouse-client --host localhost --port 9000 << 'SQL'
SELECT 
    table,
    formatReadableSize(total_bytes) as size,
    rows
FROM system.tables
WHERE database = 'settlement'
ORDER BY total_bytes DESC;
SQL

  echo ""
  echo "2. QUERY EXECUTION TIME (Last 10 Slow Queries)"
  echo "=============================================="
  
  clickhouse-client --host localhost --port 9000 << 'SQL'
SELECT 
    query_start_time,
    query_duration_ms,
    read_rows,
    query
FROM system.query_log
WHERE database = 'settlement'
AND type = 2  -- QueryFinish
ORDER BY query_duration_ms DESC
LIMIT 10;
SQL

  echo ""
  echo "3. INDEX USAGE & EFFECTIVENESS"
  echo "=============================="
  
  clickhouse-client --host localhost --port 9000 << 'SQL'
SELECT 
    table,
    name as index_name,
    type as index_type
FROM system.tables t
ARRAY JOIN indexes as indexes
WHERE database = 'settlement'
ORDER BY table, name;
SQL

  echo ""
  echo "4. PARTITION STATISTICS"
  echo "======================="
  
  clickhouse-client --host localhost --port 9000 << 'SQL'
SELECT 
    table,
    partition,
    formatReadableSize(bytes) as size,
    rows
FROM system.parts
WHERE database = 'settlement'
ORDER BY table, partition;
SQL

  echo ""
  echo "5. MEMORY USAGE"
  echo "==============="
  
  clickhouse-client --host localhost --port 9000 << 'SQL'
SELECT 
    formatReadableSize(memory_usage) as memory_used,
    count_queries,
    count_active
FROM system.metrics
WHERE metric LIKE 'ClickHousePeakMemory%'
   OR metric LIKE 'MemoryTracking';
SQL

} | tee "$REPORT_FILE"

echo ""
echo -e "${GREEN}Database profile saved to: $REPORT_FILE${NC}"
