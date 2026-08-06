"""FastAPI REST API for settlement pipeline"""
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.pipeline.orchestrator import PipelineOrchestrator
from src.utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Settlement Data Pipeline API",
    description="Production-grade settlement transaction processing",
    version="1.0.0",
)


class TransactionRequest(BaseModel):
    """Transaction submission request."""

    id: str
    tenant_id: str
    amount: str
    region: str
    timestamp: str


class TransactionResponse(BaseModel):
    """Transaction processing response."""

    processed: int
    failed: int
    success_rate: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


# Global orchestrator instance
orchestrator = PipelineOrchestrator(
    kafka_bootstrap_servers="localhost:9092",
    clickhouse_host="localhost",
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="settlement-pipeline",
    )


@app.get("/stats")
def get_stats() -> dict[str, Any]:
    """Get pipeline statistics."""
    return orchestrator.get_stats()


@app.post("/process", response_model=TransactionResponse)
def process_transaction(
    request: TransactionRequest,
) -> TransactionResponse:
    """Process a single transaction."""
    try:
        import json

        message = json.dumps(request.model_dump()).encode("utf-8")
        processed, failed = orchestrator.process_batch([message])

        return TransactionResponse(
            processed=processed,
            failed=failed,
            success_rate=100.0 if failed == 0 else 0.0,
        )
    except Exception as e:
        logger.error("api_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def get_metrics() -> str:
    """Prometheus metrics endpoint."""
    from src.metrics_server import get_metrics

    return get_metrics().decode("utf-8")
