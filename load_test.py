#!/usr/bin/env python3
"""
Load testing script for settlement pipeline.
Run: python load_test.py --duration 60 --throughput 1000
"""
import argparse
import json
import time
from datetime import datetime, timezone

from src.pipeline.orchestrator import PipelineOrchestrator


def generate_transaction(tx_id: int) -> bytes:
    """Generate a test transaction."""
    message_data = {
        "id": f"tx_load_{tx_id:08d}",
        "tenant_id": f"tenant_{tx_id % 100:03d}",
        "amount": f"{100 + (tx_id % 10000)}.50",
        "region": ["EU", "US", "APAC"][tx_id % 3],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(message_data).encode("utf-8")


def run_load_test(
    duration: int = 60, throughput: int = 1000
) -> None:
    """Run load test against pipeline."""
    orchestrator = PipelineOrchestrator(
        kafka_bootstrap_servers="localhost:9092",
        clickhouse_host="localhost",
        batch_size=100,
    )

    msg = f"Starting load test: {duration}s, {throughput} txn/sec"
    print(msg)
    start_time = time.time()
    total_processed = 0
    total_failed = 0
    batch_count = 0

    while time.time() - start_time < duration:
        # Generate batch
        messages = [
            generate_transaction(total_processed + i)
            for i in range(throughput // 10)
        ]

        # Process
        processed, failed = orchestrator.process_batch(messages)
        total_processed += processed
        total_failed += failed
        batch_count += 1

        # Sleep to maintain throughput
        elapsed_in_sec = time.time() - start_time
        expected_processed = int(elapsed_in_sec * throughput)
        if total_processed < expected_processed:
            time.sleep(0.1)

    elapsed = time.time() - start_time
    actual_throughput = (
        total_processed / elapsed if elapsed > 0 else 0
    )

    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Duration: {elapsed:.1f}s")
    print(f"Total Processed: {total_processed}")
    print(f"Total Failed: {total_failed}")
    success_pct = (
        total_processed / (total_processed + total_failed) * 100
    )
    print(f"Success Rate: {success_pct:.2f}%")
    print(f"Actual Throughput: {actual_throughput:.0f} txn/sec")
    print(f"Batches: {batch_count}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds",
    )
    parser.add_argument(
        "--throughput",
        type=int,
        default=1000,
        help="Target throughput in txn/sec",
    )
    args = parser.parse_args()

    run_load_test(duration=args.duration, throughput=args.throughput)
