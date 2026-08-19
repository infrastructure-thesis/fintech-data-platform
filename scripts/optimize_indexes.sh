#!/bin/bash
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Settlement Pipeline - Index Optimization${NC}"
echo "=========================================="

CLICKHOUSE_HOST=${CLICKHOUSE_HOST:-localhost}
CLICKHOUSE_PORT=${CLICKHOUSE_PORT:-9000}

echo -e "\n${BLUE}Creating recommended indexes...${NC}"

clickhouse-client \
  --host "$CLICKHOUSE_HOST" \
  --port "$CLICKHOUSE_PORT" << 'SQL'

-- Index 1: Tenant queries
ALTER TABLE settlement.audit_log 
ADD INDEX idx_tenant_id tenant_id TYPE minmax GRANULARITY 1;

-- Index 2: Operation filtering
ALTER TABLE settlement.audit_log 
ADD INDEX idx_operation operation TYPE minmax GRANULARITY 1;

-- Index 3: User access auditing
ALTER TABLE settlement.audit_log 
ADD INDEX idx_user_id user_id TYPE hash GRANULARITY 8192;

-- Index 4: Timestamp range queries
ALTER TABLE settlement.audit_log 
ADD INDEX idx_timestamp timestamp TYPE minmax GRANULARITY 8;

-- Index 5: Status queries
ALTER TABLE settlement.transactions 
ADD INDEX idx_status status TYPE minmax GRANULARITY 1;

-- Index 6: Amount range queries
ALTER TABLE settlement.transactions 
ADD INDEX idx_amount amount TYPE minmax GRANULARITY 64;

SQL

echo -e "${GREEN}✓ Indexes created successfully${NC}"

echo -e "\n${BLUE}Optimizing table settings...${NC}"

clickhouse-client \
  --host "$CLICKHOUSE_HOST" \
  --port "$CLICKHOUSE_PORT" << 'SQL'

-- Enable compression on audit_log
ALTER TABLE settlement.audit_log 
MODIFY SETTING compress_codec = 'LZ4HC';

-- Set read preference to replicas if available
ALTER TABLE settlement.audit_log 
MODIFY SETTING read_from_replica_replica_on_client_select = 1;

SQL

echo -e "${GREEN}✓ Table optimization complete${NC}"

echo -e "\n${BLUE}Current indexes:${NC}"

clickhouse-client \
  --host "$CLICKHOUSE_HOST" \
  --port "$CLICKHOUSE_PORT" << 'SQL'

SHOW INDEXES FROM settlement.audit_log;

SQL

echo -e "\n${GREEN}Optimization complete!${NC}"
