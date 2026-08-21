"""Webhook event types and handlers."""
import json
import hmac
import hashlib
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone
from enum import Enum

from src.utils.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    """Webhook event types."""

    TRANSACTION_PROCESSED = "transaction.processed"
    TRANSACTION_FAILED = "transaction.failed"
    BATCH_COMPLETED = "batch.completed"
    ERROR_THRESHOLD_EXCEEDED = "error.threshold_exceeded"
    SYSTEM_HEALTHY = "system.healthy"
    SYSTEM_DEGRADED = "system.degraded"


class WebhookEvent:
    """Webhook event payload."""

    def __init__(
        self,
        event_type: EventType,
        tenant_id: str,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.event_type = event_type
        self.tenant_id = tenant_id
        self.data = data
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.event_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique event ID."""
        content = f"{self.tenant_id}{self.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.event_id,
            "type": self.event_type.value,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    def sign(self, secret: str) -> str:
        """Create HMAC-SHA256 signature for webhook."""
        payload = self.to_json()
        signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return signature


class WebhookRegistry:
    """Registry for webhook handlers."""

    def __init__(self) -> None:
        self.handlers: Dict[EventType, List[Callable[[WebhookEvent], None]]] = {}

    def register(
        self,
        event_type: EventType,
        handler: Callable[[WebhookEvent], None],
    ) -> None:
        """Register a handler for an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(
            "webhook_handler_registered",
            event_type=event_type.value,
        )

    async def emit(self, event: WebhookEvent) -> None:
        """Emit an event to all registered handlers."""
        handlers = self.handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                handler(event)  # Remove await - handlers are sync
            except Exception as e:
                logger.error(
                    "webhook_handler_error",
                    event_type=event.event_type.value,
                    error=str(e),
                )


# Global registry
webhook_registry = WebhookRegistry()
