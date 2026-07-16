import json
from typing import Any, Dict

from src.pipeline.models import Transaction


class SettlementConsumer:
    """Kafka consumer for settlement events."""

    def __init__(self, bootstrap_servers: str):
        """Initialize consumer with Kafka bootstrap servers."""
        self.bootstrap_servers = bootstrap_servers
        self.topic = "settlement-events"

    def consume_message(self, message: bytes) -> Transaction:
        """Parse raw message into Transaction."""
        try:
            data = json.loads(message.decode("utf-8"))
            return self._parse_transaction(data)
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Failed to parse message: {e}")

    def _parse_transaction(self, data: Dict[str, Any]) -> Transaction:
        """Convert dict to Transaction object."""
        from datetime import datetime, timezone
        from decimal import Decimal

        return Transaction(
            id=str(data["id"]),
            tenant_id=str(data["tenant_id"]),
            amount=Decimal(str(data["amount"])),
            region=str(data["region"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )
