import time

from src.pipeline.models import AuditLogEntry
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ClickhouseWriter:
    """Write audit log entries to Clickhouse."""

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

    def write(self, entry: AuditLogEntry) -> bool:
        """Write audit entry with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self._insert(entry)
                logger.info(
                    "audit_write_success",
                    transaction_id=entry.transaction_id,
                    attempt=attempt + 1,
                )
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
                wait_time = 2**attempt
                logger.warning(
                    "audit_write_retry",
                    transaction_id=entry.transaction_id,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                )
                time.sleep(wait_time)
        return False

    def _insert(self, entry: AuditLogEntry) -> None:
        """Insert entry into Clickhouse (stub for now)."""
        if not entry.transaction_id or not entry.compliance_hash:
            raise ValueError("Missing required fields for audit entry")
