import json
from datetime import datetime, timezone


from src.pipeline.consumer import SettlementConsumer
from src.pipeline.orchestrator import PipelineOrchestrator
from src.pipeline.transformer import SettlementTransformer


def test_full_pipeline_e2e():
    """Test complete pipeline: message → consumer → transformer →
    orchestrator"""
    # Create orchestrator
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
    )

    # Create test message
    message_data = {
        "id": "tx_e2e_001",
        "tenant_id": "tenant_prod",
        "amount": "1250.99",
        "region": "EU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(message_data).encode("utf-8")

    # Process through orchestrator
    processed, failed = orchestrator.process_batch([message])

    assert processed == 1
    assert failed == 0

    # Verify stats
    stats = orchestrator.get_stats()
    assert stats["success_rate"] == 100.0


def test_multiple_regions_e2e():
    """Test pipeline with messages from multiple regions."""
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
    )

    regions = ["EU", "US", "APAC"]
    messages = []

    for i, region in enumerate(regions):
        message_data = {
            "id": f"tx_region_{i}",
            "tenant_id": "tenant_multi",
            "amount": "500.00",
            "region": region,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        messages.append(json.dumps(message_data).encode("utf-8"))

    processed, failed = orchestrator.process_batch(messages)

    assert processed == 3
    assert failed == 0


def test_compliance_hash_consistency_e2e():
    """Test that compliance hashing is deterministic across pipeline."""
    consumer = SettlementConsumer("localhost:9092")

    message_data = {
        "id": "tx_hash_001",
        "tenant_id": "tenant_hash",
        "amount": "999.99",
        "region": "EU",
        "timestamp": "2026-07-24T12:00:00+00:00",
    }
    message = json.dumps(message_data).encode("utf-8")

    # Parse message
    tx = consumer.consume_message(message)

    # Transform twice
    audit_entry_1 = SettlementTransformer.transform(tx)
    audit_entry_2 = SettlementTransformer.transform(tx)

    # Hashes should match
    assert audit_entry_1.compliance_hash == audit_entry_2.compliance_hash
