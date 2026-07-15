# Architecture

## System Overview
Settlement pipeline: Kafka → Python → Clickhouse

## Components
- **Kafka**: Durable event queue, 3 brokers, multi-region replication
- **Python**: Consumer → Transformer → Writer (all type-safe, tested)
- **ClickHouse**: Time-series audit log, 7-year retention
- **Prometheus/Grafana**: Monitoring + alerting

## Data Flow
1. Settlement events arrive via Kafka
2. Python consumer parses + validates
3. Transformer computes SHA256 hash (audit proof)
4. Writer appends to Clickhouse
5. Metrics exported to Prometheus

## Multi-Region
- Kafka replicates across regions (eventual consistency)
- Clickhouse shards by tenant_id
- Each region has independent monitoring