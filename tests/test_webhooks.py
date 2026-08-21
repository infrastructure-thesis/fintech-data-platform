"""Webhook event system tests."""
import pytest

from src.webhooks.events import (
    EventType,
    WebhookEvent,
    WebhookRegistry,
)


@pytest.fixture
def webhook_event() -> WebhookEvent:
    """Create test webhook event."""
    return WebhookEvent(
        event_type=EventType.TRANSACTION_PROCESSED,
        tenant_id="test-tenant",
        data={"transaction_id": "txn_001", "status": "success"},
    )


def test_webhook_event_creation(webhook_event: WebhookEvent) -> None:
    """Test webhook event creation."""
    assert webhook_event.event_type == EventType.TRANSACTION_PROCESSED
    assert webhook_event.tenant_id == "test-tenant"
    assert webhook_event.data["transaction_id"] == "txn_001"


def test_webhook_event_to_dict(webhook_event: WebhookEvent) -> None:
    """Test webhook event to_dict conversion."""
    event_dict = webhook_event.to_dict()

    assert event_dict["type"] == "transaction.processed"
    assert event_dict["tenant_id"] == "test-tenant"
    assert "id" in event_dict
    assert "timestamp" in event_dict


def test_webhook_event_to_json(webhook_event: WebhookEvent) -> None:
    """Test webhook event to_json conversion."""
    event_json = webhook_event.to_json()

    assert isinstance(event_json, str)
    assert "transaction.processed" in event_json
    assert "test-tenant" in event_json


def test_webhook_event_signing(webhook_event: WebhookEvent) -> None:
    """Test webhook event HMAC signing."""
    secret = "test-secret-key"
    signature = webhook_event.sign(secret)

    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA256 hex digest


def test_webhook_event_signature_verification(
    webhook_event: WebhookEvent,
) -> None:
    """Test webhook signature verification."""
    secret = "test-secret-key"
    signature = webhook_event.sign(secret)

    # Verify signature is consistent
    signature2 = webhook_event.sign(secret)
    assert signature == signature2

    # Different secret should produce different signature
    signature3 = webhook_event.sign("different-secret")
    assert signature != signature3


def test_webhook_registry_register() -> None:
    """Test webhook registry handler registration."""
    registry = WebhookRegistry()
    handler_called = False

    def test_handler(event: WebhookEvent) -> None:
        nonlocal handler_called
        handler_called = True

    registry.register(EventType.TRANSACTION_PROCESSED, test_handler)

    assert EventType.TRANSACTION_PROCESSED in registry.handlers
    assert len(registry.handlers[EventType.TRANSACTION_PROCESSED]) == 1


def test_webhook_registry_multiple_handlers() -> None:
    """Test webhook registry with multiple handlers."""
    registry = WebhookRegistry()
    handler1_called = False
    handler2_called = False

    def handler1(event: WebhookEvent) -> None:
        nonlocal handler1_called
        handler1_called = True

    def handler2(event: WebhookEvent) -> None:
        nonlocal handler2_called
        handler2_called = True

    registry.register(EventType.TRANSACTION_PROCESSED, handler1)
    registry.register(EventType.TRANSACTION_PROCESSED, handler2)

    assert len(registry.handlers[EventType.TRANSACTION_PROCESSED]) == 2


def test_event_type_values() -> None:
    """Test event type enum values."""
    assert EventType.TRANSACTION_PROCESSED.value == "transaction.processed"
    assert EventType.TRANSACTION_FAILED.value == "transaction.failed"
    assert EventType.BATCH_COMPLETED.value == "batch.completed"
    assert EventType.ERROR_THRESHOLD_EXCEEDED.value == ("error.threshold_exceeded")
    assert EventType.SYSTEM_HEALTHY.value == "system.healthy"
    assert EventType.SYSTEM_DEGRADED.value == "system.degraded"
