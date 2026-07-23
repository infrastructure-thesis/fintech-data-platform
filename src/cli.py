import json
import sys
from typing import Optional

from src.pipeline.orchestrator import PipelineOrchestrator


def main(
    kafka_bootstrap_servers: str = "localhost:9092",
    clickhouse_host: str = "localhost",
    clickhouse_port: int = 9000,
    batch_size: int = 100,
):
    """Run settlement pipeline orchestrator."""
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers=kafka_bootstrap_servers,
        clickhouse_host=clickhouse_host,
        clickhouse_port=clickhouse_port,
        batch_size=batch_size,
    )
    
    print("Settlement Pipeline Orchestration Started")
    print(f"Kafka: {kafka_bootstrap_servers}")
    print(f"Clickhouse: {clickhouse_host}:{clickhouse_port}")
    print(f"Batch size: {batch_size}")
    print("-" * 60)
    
    # Placeholder for Kafka consumer loop
    # In production, this would raed from Kafka continuously
    print("Waiting for messages from Kafka...")
    print("(Press Ctrl+C to stop)")
    
    try:
        # Example: process empty batch to show stats
        orchestrator.process_batch([])
        stats = orchestrator.get_stats()
        print("\nPipeline Statistics:")
        print(json.dumps(stats, indent=2))
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        stats = orchestrator.get_stats()
        print("Final Statistics:")
        print(json.dumps(stats, indent=2))
        sys.exit(0)
        
        
if __name__ == "__main__":
    main()
