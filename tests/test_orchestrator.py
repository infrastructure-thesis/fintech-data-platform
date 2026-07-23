import json
from datetime import datetime, timezone


import pytest

from src.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def orchestrator():
    """Create orchestrator instance."""
    return PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
        batch_size=100,
    )


@pytest.fixture
def sample_messages():
    """Create sample Kafka messages."""
    messages = []
    for i in range(3):
        message_data = {
            "id": f"tx_orch_{i:03d}",
            "tenant_id": "tenant_abc",
            "amount": "100.50",
            "region": "EU",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        messages.append(json.dumps(message_data).encode("utf-8"))
    return messages


def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initialization."""
    assert orchestrator.batch_size == 100
    assert orchestrator.processed_count == 0
    assert orchestrator.failed_count == 0


def test_process_batch_success(orchestrator, sample_messages):
    """Test processing batch of messages."""
    processed, failed = orchestrator.process_batch(sample_messages)

    assert processed == 3
    assert failed == 0


def test_pipeline_stats(orchestrator, sample_messages):
    """Test pipeline statistics."""
    orchestrator.process_batch(sample_messages)
    stats = orchestrator.get_stats()

    assert stats["processed"] == 3
    assert stats["failed"] == 0
    assert stats["total"] == 3
    assert stats["success_rate"] == 100.0


def test_pipeline_error_handling(orchestrator):
    """Test handling of invalid messages."""
    invalid_messages = [b"not valid json"]

    processed, failed = orchestrator.process_batch(invalid_messages)

    assert processed == 0
    assert failed == 1
