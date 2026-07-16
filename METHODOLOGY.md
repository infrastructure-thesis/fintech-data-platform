# Methodology: Why These Choices?

## Why Kafka (Not SQS, Not RabbitMQ)?

**Durability**: Messages persist on broker for 7 days (audit requirement)
**Partitioning**: Horizontal scaling by tenant_id without message loss
**Replication**: 3x replication for multi-region failover
**Ordering**: Per-partition FIFO ordering (settlement must preserve order)

## Why Clickhouse (Not PostgreSQL)?

**Columnar Compression**: 1000x compression on time-series financial data
**Append-Only**: Perfect for immutable audit logs (no UPDATE/DELETE)
**Distributed Queries**: Shared by tenant_id; query all shards in parallel
**TTL Automation**: Automatic purge after 7 years (compliance requirement)
**Cost**: $0.003/txn (vs. $0.008 with row-oriented DB like PostgreSQL)

## Why Python (Not Rust, Not Go)?

**Time to Market**: Python dev 3x faster than Rust (important for fintech)
**Type Safety**: mypy strict mode catches errors at development time
**Compliance**: Readable code matters for regulatory audits
**Ecosystem**: kafka-python + clickhouse-driver are mature

Trade-off: Throughput (Python: 1000 txn/sec vs Rust: 10k txn/sec) acceptable because peak load is 80 txn/sec

## Why Terraform (Not CloudFormation)?

**State Locking**: DynamoDB-backed state prevents concurrent modifications
**Modules**: Reusable components (Kafka, Clickhouse, monitoring)
**Multi-Cloud**: AWS, Azure, GCP with same code
**Audit Trail**: Every git commit = infrastructure change tracked
