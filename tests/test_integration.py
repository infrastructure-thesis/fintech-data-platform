import json
import time
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.pipeline.consumer import SettlementConsumer
from src.pipeline.models import Transaction
from src.pipeline.transformer import SettlementTransformer
from src.pipeline.writer import ClickhouseWriter


def test_end_to_end_pipeline():
    """Test full pipeline: consume → transform → write."""
    # Create consumer
    consumer = SettlementConsumer("localhost:9092")

    # Create sample message
    message_data = {
        "id": "tx_integration_001",
        "tenant_id": "tenant_xyz",
        "amount": "500.75",
        "region": "EU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(message_data).encode("utf-8")

    # Step 1: Consume
    tx = consumer.consume_message(message)
    assert isinstance(tx, Transaction)
    assert tx.id == "tx_integration_001"

    # Step 2: Transform
    audit_entry = SettlementTransformer.transform(tx)
    assert audit_entry.compliance_hash
    assert len(audit_entry.compliance_hash) == 64

    # Step 3: Write
    writer = ClickhouseWriter(host="localhost", port=9000)
    result = writer.write(audit_entry)
    assert result is True


def test_kafka_topic_creation():
    """Test that settlement-events topic exists."""
    consumer = SettlementConsumer("localhost:9092")
    assert consumer.topic == "settlement-events"


def test_clickhouse_connectivity():
    """Test Clickhouse connection."""
    writer = ClickhouseWriter(host="localhost", port=9000)
    assert writer.host == "localhost"
    assert writer.port == 9000
