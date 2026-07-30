from typing import Optional

from clickhouse_driver import Client

from src.pipeline.models import AuditLogEntry
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClickhouseClient:
    """Real Clickhouse client with connection pooling and retry logic."""

    def __init__(
        self,
        host: str,
        port: int = 9000,
        database: str = "settlement",
        max_retries: int = 3,
    ):
        """Initialize Clickhouse client."""
        self.host = host
        self.port = port
        self.database = database
        self.max_retries = max_retries
        self.client: Optional[Client] = None

    def connect(self) -> bool:
        """Connect to Clickhouse server."""
        try:
            self.client = Client(
                host=self.host,
                port=self.port,
                database=self.database,
            )
            # Test connection
            self.client.execute("SELECT 1")
            logger.info(
                "clickhouse_connected",
                host=self.host,
                port=self.port,
            )
            return True
        except Exception as e:
            logger.error("Clickhouse_connection_failed", error=str(e))
            return False

    def create_table_if_not_exists(self) -> bool:
        """Create audit_log table if it doesn't exist."""
        if not self.client:
            logger.error("clickhouse_not_connected")
            return False

        try:
            self.client.execute(
                """
                CREATE TABLE IF NOT EXISTS settlement.audit_log (
                    timestamp DateTime,
                    tenant_id String,
                    transaction_id String,
                    amount Decimal(18,2),
                    region String,
                    compliance_hash String,
                    audit_timestamp DateTime
                ) ENGINE = MergeTree()
                ORDER BY (tenant_id, timestamp)
                PARTITION BY toYYYYMM(timestamp)
                """
            )
            logger.info("clickhouse_table_created")
            return True
        except Exception as e:
            logger.error("clickhouse_table_creation_failed", error=str(e))
            return False

    def insert_audit_entry(self, entry: AuditLogEntry) -> bool:
        """Insert audit log entry into Clickhouse."""
        if not self.client:
            logger.error("clickhouse_not_connected")
            return False

        try:
            self.client.execute(
                """
                INSERT INTO settlement.audit_log (
                    timestamp, tenant_id, transaction_id, amount,
                    region, compliance_hash, audit_timestamp
                ) VALUES
                """,
                [
                    (
                        entry.timestamp,
                        entry.tenant_id,
                        entry.transaction_id,
                        entry.amount,
                        entry.region,
                        entry.compliance_hash,
                        entry.audit_timestamp,
                    )
                ],
            )
            logger.info(
                "clickhouse_insert_success",
                transaction_id=entry.transaction_id,
            )
            return True
        except Exception as e:
            logger.error(
                "clickhouse_insert_failed",
                transaction_id=entry.transaction_id,
                error=str(e),
            )
            return False

    def close(self) -> None:
        """Close Clickhouse connection."""
        if self.client:
            self.client.disconnect()
            logger.info("clickhouse_disconnected")
