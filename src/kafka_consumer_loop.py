from typing import List, Optional

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from src.pipeline.orchestrator import PipelineOrchestrator
from src.utils.logging import get_logger

logger = get_logger(__name__)


class KafkaConsumerLoop:
    """Continuous Kafka consumer that processes settlement messages."""

    def __init__(
        self,
        kafka_bootstrap_servers: str,
        clickhouse_host: str,
        topic: str = "settlement-events",
        batch_size: int = 100,
        group_id: str = "settlement-pipeline",
    ):
        """Initialize Kafka consumer loop."""
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.clickhouse_host = clickhouse_host
        self.topic = topic
        self.batch_size = batch_size
        self.group_id = group_id
        self.orchestrator = PipelineOrchestrator(
            kafka_bootstrap_servers=kafka_bootstrap_servers,
            clickhouse_host=clickhouse_host,
            batch_size=batch_size,
        )
        self.consumer: Optional[KafkaConsumer] = None
        self.running = False

    def start(self) -> bool:
        """Start Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.kafka_bootstrap_servers,
                group_id=self.group_id,
                auto_offset_reset="earliest",
                value_deserializer=lambda m: m.decode("utf-8"),
            )
            self.running = True
            logger.info(
                "kafka_consumer_started",
                topic=self.topic,
                group_id=self.group_id,
            )
            return True
        except KafkaError as e:
            logger.error("kafka_consumer_start_failed", error=str(e))
            return False

    def run(self) -> None:
        """Run continuous consumer loop (processes until stopped)."""
        if not self.start():
            return

        if self.consumer is None:
            return

        batch: List[bytes] = []

        try:
            for message in self.consumer:
                batch.append(message.value.encode("utf-8"))

                if len(batch) >= self.batch_size:
                    self._process_batch(batch)
                    batch = []

            if batch:
                self._process_batch(batch)
        except KeyboardInterrupt:
            logger.info("kafka_consumer_interrupted")
        finally:
            self.stop()

    def _process_batch(self, batch: List[bytes]) -> None:
        """Process a batch of messages."""
        processed, failed = self.orchestrator.process_batch(batch)
        stats = self.orchestrator.get_stats()

        logger.info(
            "batch_processed",
            batch_size=len(batch),
            processed=processed,
            failed=failed,
            total_processed=stats["processed"],
            success_rate=stats["success_rate"],
        )

    def stop(self) -> None:
        """Stop Kafka consumer."""
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("kafka_consumer_stopped")


def main(
    kafka_bootstrap_servers: str = "localhost:9092",
    clickhouse_host: str = "localhost",
) -> None:
    """Run settlement pipeline consumer."""
    consumer_loop = KafkaConsumerLoop(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        clickhouse_host=clickhouse_host,
    )
    consumer_loop.run()


if __name__ == "__main__":
    main()
