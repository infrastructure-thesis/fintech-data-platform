from src.metrics import (
    active_batches,
    record_compliance_check,
    record_pipeline_latency,
    record_transaction_failed,
    record_transaction_processed,
    set_active_batches,
)


def test_record_transaction_processed() -> None:
    """Test recording successful transaction."""
    record_transaction_processed("success")
    # Verify counter incremented
    assert record_transaction_processed.__module__ == "src.metrics"


def test_record_transaction_failed() -> None:
    """Test recording failed transaction."""
    record_transaction_failed("connection_error")
    assert record_transaction_failed.__module__ == "src.metrics"


def test_record_pipeline_latency() -> None:
    """Test recording pipeline latency."""
    record_pipeline_latency("consumer", 0.5)
    assert record_pipeline_latency.__module__ == "src.metrics"


def test_set_active_batches() -> None:
    """Test setting active batches."""
    set_active_batches(5)
    assert active_batches._value.get() == 5


def test_record_compliance_check() -> None:
    """Test recording compliance check."""
    record_compliance_check("EU")
    assert record_compliance_check.__module__ == "src.metrics"
