from unittest.mock import MagicMock, patch

from src.clickhouse_client import ClickhouseClient


def test_clickhouse_client_initialization():
    """Test Clickhouse client initialization."""
    client = ClickhouseClient(
        host="localhost",
        port=9000,
        database="settlement",
    )

    assert client.host == "localhost"
    assert client.port == 9000
    assert client.database == "settlement"
    assert client.max_retries == 3


@patch("src.clickhouse_client.Client")
def test_clickhouse_client_connect_success(mock_client_class):
    """Test successful connection."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance

    client = ClickhouseClient(host="localhost")
    result = client.connect()

    assert result is True
    mock_instance.execute.assert_called_once_with("SELECT 1")


@patch("src.clickhouse_client.Client")
def test_clickhouse_client_connect_failure(mock_client_class):
    """Test connection failure."""
    mock_client_class.side_effect = Exception("Connection refused")

    client = ClickhouseClient(host="localhost")
    result = client.connect()

    assert result is False


@patch("src.clickhouse_client.Client")
def test_create_table_success(mock_client_class):
    """Test table creation success."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance

    client = ClickhouseClient(host="localhost")
    client.connect()
    result = client.create_table_if_not_exists()

    assert result is True


def test_create_table_not_connected():
    """Test table creation without connection."""
    client = ClickhouseClient(host="localhost")
    result = client.create_table_if_not_exists()

    assert result is False


def test_insert_not_connected():
    """Test insert without connection."""
    from datetime import datetime, timezone
    from decimal import Decimal

    from src.pipeline.models import AuditLogEntry

    entry = AuditLogEntry(
        timestamp=datetime.now(timezone.utc),
        tenant_id="tenant_abc",
        transaction_id="tx_001",
        amount=Decimal("100.50"),
        region="EU",
        compliance_hash="abc123",
        audit_timestamp=datetime.now(timezone.utc),
    )

    client = ClickhouseClient(host="localhost")
    result = client.insert_audit_entry(entry)

    assert result is False


@patch("src.clickhouse_client.Client")
def test_close_connection(mock_client_class):
    """Test closing connection."""
    mock_instance = MagicMock()
    mock_client_class.return_value = mock_instance

    client = ClickhouseClient(host="localhost")
    client.connect()
    client.close()

    mock_instance.disconnect.assert_called_once()
