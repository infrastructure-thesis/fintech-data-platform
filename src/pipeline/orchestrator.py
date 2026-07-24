import logging
from typing import Any, List

from src.pipeline.consumer import SettlementConsumer
from src.pipeline.models import AuditLogEntry
from src.pipeline.transformer import SettlementTransformer
from src.pipeline.writer import ClickhouseWriter
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates settlement pipeline: consume → transform → write."""

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        clickhouse_host: str,
        clickhouse_port: int = 9000,
        batch_size: int = 100,
    ):
        """Initialize orchestrator with service endpoints."""
        self.consumer = SettlementConsumer(kafka_bootstrap_servers)
        self.writer = ClickhouseWriter(clickhouse_host, clickhouse_port)
        self.batch_size = batch_size
        self.processed_count = 0
        self.failed_count = 0

    def process_batch(self, messages: List[bytes]) -> tuple[int, int]:
        """Process a batch of messages through full pipeline."""
        processed = 0
        failed = 0

        for message in messages:
            try:
                # Step 1: Consume
                transaction = self.consumer.consume_message(message)

                # Step 2: Transform
                audit_entry = SettlementTransformer.transform(transaction)

                # Step 3: Write
                success = self.writer.write(audit_entry)

                if success:
                    processed += 1
                    logger.info(
                        "pipeline_success",
                        transaction_id=transaction.id,
                        tenant_id=transaction.tenant_id,
                    )
                else:
                    failed += 1
                    logger.warning(
                        "pipeline_write_failed",
                        transaction_id=transaction.id,
                    )
            except Exception as e:
                failed += 1
                logger.error("pipeline_error", error=str(e))

        self.processed_count += processed
        self.failed_count += failed

        return processed, failed

    def get_stats(self) -> dict[str, Any]:
        """Return pipeline statistics."""
        total = self.processed_count + self.failed_count
        success_rate = (self.processed_count / total * 100) if total > 0 else 0

        return {
            "processed": self.processed_count,
            "failed": self.failed_count,
            "total": total,
            "success_rate": success_rate,
        }
