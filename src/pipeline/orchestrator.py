import time
from typing import Any, List

from src.metrics import (
    record_compliance_check,
    record_pipeline_latency,
    record_transaction_failed,
    record_transaction_processed,
    set_active_batches,
)
from src.pipeline.consumer import SettlementConsumer
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
        set_active_batches(len(messages))

        for message in messages:
            start_time = time.time()
            try:
                # Step 1: Consume
                transaction = self.consumer.consume_message(message)
                consumer_latency = time.time() - start_time
                record_pipeline_latency("consumer", consumer_latency)

                # Step 2: Transform
                transform_start = time.time()
                audit_entry = SettlementTransformer.transform(transaction)
                transformer_latency = time.time() - transform_start
                record_pipeline_latency("transformer", transformer_latency)
                record_compliance_check(transaction.region)

                # Step 3: Write
                write_start = time.time()
                success = self.writer.write(audit_entry)
                writer_latency = time.time() - write_start
                record_pipeline_latency("writer", writer_latency)

                if success:
                    processed += 1
                    record_transaction_processed("success")
                    logger.info(
                        "pipeline_success",
                        transaction_id=transaction.id,
                        tenant_id=transaction.tenant_id,
                    )
                else:
                    failed += 1
                    record_transaction_failed("write_error")
                    logger.warning(
                        "pipeline_write_failed",
                        transaction_id=transaction.id,
                    )
            except Exception as e:
                failed += 1
                record_transaction_failed("processing_error")
                logger.error("pipeline_error", error=str(e))

        self.processed_count += processed
        self.failed_count += failed
        set_active_batches(0)

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
