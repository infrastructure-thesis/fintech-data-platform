from prometheus_client import Counter, Gauge, Histogram

# Transaction processing metrics
transactions_processed = Counter(
    "settlement_transactions_processed_total",
    "Total number of transactions processed",
    ["status"],
)

transactions_failed = Counter(
    "settlement_transactions_failed_total",
    "Total number of transactions failures",
    ["error_type"],
)

pipeline_latency = Histogram(
    "settlement_pipeline_latency_seconds",
    "Pipeline processing latency in seconds",
    ["stage"],
)

active_batches = Gauge(
    "settlement_active_batches",
    "Number of active batches being processed",
)

compliance_hash_checks = Counter(
    "settlement_compliance_hash_checks_total",
    "Total number of compliance hash checks",
    ["region"],
)

clickhouse_write_errors = Counter(
    "settlement_clickhouse_write_errors_total",
    "Total Clickhouse write errors",
    ["error_type"],
)

kafka_consumer_lag = Gauge(
    "settlement_kafka_consumer_lag",
    "Kafka consumer lag in messages",
    ["topic", "partition"],
)


def record_transaction_processed(status: str) -> None:
    """Record successful transaction processing."""
    transactions_processed.labels(status=status).inc()


def record_transaction_failed(error_type: str) -> None:
    """Record transaction failure."""
    transactions_failed.labels(error_type=error_type).inc()


def record_pipeline_latency(stage: str, latency: float) -> None:
    """Record pipeline stage latency."""
    pipeline_latency.labels(stage=stage).observe(latency)


def set_active_batches(count: int) -> None:
    """Set current active batch count."""
    active_batches.set(count)


def record_compliance_check(region: str) -> None:
    """Record compliance hash check."""
    compliance_hash_checks.labels(region=region).inc()


def record_clickhouse_error(error_type: str) -> None:
    """Record Clickhouse error."""
    clickhouse_write_errors.labels(error_type=error_type).inc()


def set_kafka_lag(topic: str, partition: int, lag: int) -> None:
    """Set Kafka consumer lag."""
    kafka_consumer_lag.labels(topic=topic, partition=str(partition)).set(lag)
