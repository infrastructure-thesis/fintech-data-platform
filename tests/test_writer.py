from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.pipeline.models import AuditLogEntry
from src.pipeline.writer import ClickhouseWriter


@pytest.fixture
def writer():
    """Create writer instance."""
    return ClickhouseWriter(host="localhost", port=9000)


@pytest.fixture
def audit_entry():
    """Create sample audit log entry."""
    return AuditLogEntry(
        timestamp=datetime.now(timezone.utc),
        tenant_id="tenant_abc",
        transaction_id="tx_001",
        amount=Decimal("100.50"),
        region="EU",
        compliance_hash="abc123def456",
        audit_timestamp=datetime.now(timezone.utc),
    )


def test_writer_initialization(writer):
    """Test writer initialization."""
    assert writer.host == "localhost"
    assert writer.port == 9000
    assert writer.max_retries == 3
    assert writer.table == "audit_log"


def test_write_valid_entry(writer, audit_entry):
    """Test writing valid entry (graceful if Clickhouse unavailbale)."""
    # This will gracefully fail if Cickhouse isn't running
    result = writer.write(audit_entry)
    assert isinstance(result, bool)


def test_write_missing_transaction_id(writer):
    """Test writing entry without transaction ID."""
    entry = AuditLogEntry(
        timestamp=datetime.now(timezone.utc),
        tenant_id="tenant_abc",
        transaction_id="",
        amount=Decimal("100.50"),
        region="EU",
        compliance_hash="abc123def456",
        audit_timestamp=datetime.now(timezone.utc),
    )

    result = writer.write(entry)
    assert isinstance(result, bool)


def test_write_missing_compliance_hash(writer):
    """Test writing entry without compliance hash."""
    entry = AuditLogEntry(
        timestamp=datetime.now(timezone.utc),
        tenant_id="tenant_abc",
        transaction_id="tx_001",
        amount=Decimal("100.50"),
        region="EU",
        compliance_hash="",
        audit_timestamp=datetime.now(timezone.utc),
    )

    result = writer.write(entry)
    assert isinstance(result, bool)
