"""
End-to-end production tests.
Run: docker-compose -f docker/compose.yml up -d &&
     pytest tests/test_production_e2e.py -v
"""
import json
import time
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.pipeline.orchestrator import PipelineOrchestrator


@pytest.mark.skip(reason="Requires docker-compose services running")
def test_full_production_pipeline():
    """Test complete production pipeline with live services."""
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
        batch_size=100,
    )

    # Generate 100 test transactions
    messages = []
    for i in range(100):
        message_data = {
            "id": f"tx_prod_{i:05d}",
            "tenant_id": f"tenant_{i % 10:02d}",
            "amount": f"{100 + i}.50",
            "region": ["EU", "US", "APAC"][i % 3],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        messages.append(json.dumps(message_data).encode("utf-8"))

    # Process batch
    start = time.time()
    processed, failed = orchestrator.process_batch(messages)
    elapsed = time.time() - start

    # Assertions
    assert processed + failed == 100
    assert elapsed < 5.0  # Should process 100 txns in <5s

    stats = orchestrator.get_stats()
    assert stats["total"] == 100
    assert stats["success_rate"] >= 90.0


@pytest.mark.skip(reason="Requires docker-compose services running")
def test_high_throughput_batch():
    """Test high-throughput batch processing."""
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
        batch_size=1000,
    )

    # Generate 1000 transactions
    messages = []
    for i in range(1000):
        message_data = {
            "id": f"tx_throughput_{i:06d}",
            "tenant_id": f"tenant_{i % 50:03d}",
            "amount": f"{Decimal(100 + (i % 10000)) / 100}",
            "region": ["EU", "US", "APAC", "APAC"][i % 4],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        messages.append(json.dumps(message_data).encode("utf-8"))

    start = time.time()
    processed, failed = orchestrator.process_batch(messages)
    elapsed = time.time() - start

    throughput = processed / elapsed if elapsed > 0 else 0
    assert throughput > 100  # >100 txn/sec


@pytest.mark.skip(reason="Requires docker-compose services running")
def test_compliance_audit_trail():
    """Test compliance audit trail generation."""
    from src.audit.encryption import ComplianceHasher
    from src.pipeline.consumer import SettlementConsumer
    from src.pipeline.transformer import SettlementTransformer

    consumer = SettlementConsumer("localhost:9092")

    message_data = {
        "id": "tx_compliance_001",
        "tenant_id": "tenant_audit",
        "amount": "5000.00",
        "region": "EU",
        "timestamp": "2026-08-13T12:00:00+00:00",
    }
    message = json.dumps(message_data).encode("utf-8")

    # Process through pipeline
    tx = consumer.consume_message(message)
    audit_entry = SettlementTransformer.transform(tx)

    # Verify compliance hash is deterministic
    tx_data = {
        "id": "tx.id",
        "tenant_id": "tx.tenant_id",
        "amount": str(tx.amount),
        "timestamp": tx.timestamp.isoformat(),
    }
    expected_hash = ComplianceHasher.compute_hash(tx_data)

    assert audit_entry.compliance_hash == expected_hash
    assert len(audit_entry.compliance_hash) == 64
