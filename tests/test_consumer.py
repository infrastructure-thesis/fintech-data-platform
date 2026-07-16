import json
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.pipeline.consumer import SettlementConsumer
from src.pipeline.models import Transaction


@pytest.fixture
def consumer():
    """Create consumer instance."""
    return SettlementConsumer("localhost:9092")


def test_consumer_initialization(consumer):
    """Test consumer initialization."""
    assert consumer.bootstrap_servers == "localhost:9092"
    assert consumer.topic == "settlement-events"


def test_consume_message_valid(consumer):
    """Test consuming valid message."""
    message_data = {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        "amount": "100.50",
        "region": "EU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(message_data).encode("utf-8")

    tx = consumer.consume_message(message)

    assert isinstance(tx, Transaction)
    assert tx.id == "tx_001"
    assert tx.tenant_id == "tenant_abc"
    assert tx.amount == Decimal("100.50")
    assert tx.region == "EU"


def test_consume_message_invalid_json(consumer):
    """Test consuming invalid JSON."""
    message = b"not valid json"

    with pytest.raises(ValueError, match="Failed to parse message"):
        consumer.consume_message(message)


def test_consume_message_missing_field(consumer):
    """Test consuming message with missing field."""
    message_data = {
        "id": "tx_001",
        "tenant_id": "tenant_abc",
        # Missing 'amount'
        "region": "EU",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = json.dumps(message_data).encode("utf-8")

    with pytest.raises(ValueError, match="Failed to parse message"):
        consumer.consume_message(message)
