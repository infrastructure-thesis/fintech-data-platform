#!/bin/bash
set -e

# Update System
sudo yum update -y

# Install Clickhouse
sudo yum install -y clickhouse-server clickhouse-client

# Create data directory
sudo mkdir -p /var/lib/clickhouse
sudo chown clickhouse:clickhouse /var/lib/clickhouse

# Start service
sudo systemctl start clickhouse-server
sudo systemctl enable clickhouse-server

# Create audit log table
clickhouse-client --query "
CREATE TABLE IF NOT EXISTS default.audit_log (
  timetable DateTime,
  tenant_id String,
  transaction_id String,
  amount Decimal(18,2),
  region String,
  compliance_hash String,
  audit_timestamp DateTime
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{cluster}/${cluster_name}/audit_log', '${node_index}')
PARTITION BY toYYYYMM(timestamp)
ORDER BY (tenant_id, timestamp)
"

chmod +x terraform/modules/clickhouse/clickhouse_init.sh