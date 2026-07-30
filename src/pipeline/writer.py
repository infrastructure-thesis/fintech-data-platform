import time
from typing import Optional

from src.pipeline.models import AuditLogEntry
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClickhouseWriter:
    """Write audit log entries to Clickhouse with retry logic."""

    def __init__(
        self,
        host: str,
        port: int = 9000,
        max_retries: int = 3,
    ):
        """Initialize writer with Clickhouse connection details."""
        self.host = host
        self.port = port
        self.max_retries = max_retries
        self.table = "audit_log"
        self.client: Optional[object] = None

    def _get_client(self) -> object:
        """Get or create Clickhouse client."""
        if self.client is None:
            from src.clickhouse_client import ClickhouseClient

            new_client = ClickhouseClient(host=self.host, port=self.port)
            new_client.connect()
            new_client.create_table_if_not_exists()
            self.client = new_client
        return self.client

    def write(self, entry: AuditLogEntry) -> bool:
        """Write audit entry with retry logic."""
        for attempt in range(self.max_retries):
            try:
                client = self._get_client()
                if client.insert_audit_entry(entry):  # type: ignore[attr-defined]
                    return True
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        "audit_write_failed",
                        transaction_id=entry.transaction_id,
                        error=str(e),
                        attempts=self.max_retries,
                    )
                    return False
                wait_time = 2 ** attempt
                logger.warning(
                    "audit_write_retry",
                    transaction_id=entry.transaction_id,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                )
                time.sleep(wait_time)
        return False
