CREATE DATABASE IF NOT EXISTS settlement;

USE settlement;

CREATE TABLE IF NOT EXISTS audit_log (
    timestamp DateTime,
    tenant_id String,
    transaction_id String,
    amount Decimal(18,2),
    region String,
    compliance_hash String,
    audit_timestamp DateTime
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp)
PARTITION BY toYYYYMM(timestamp);
