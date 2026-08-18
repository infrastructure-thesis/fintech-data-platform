"""FastAPI REST API with authentication."""
from typing import Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from src.auth import get_current_user, TokenPayload, jwt_auth
from src.auth import require_scope
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


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login token response."""

    access_token: str
    token_type: str
    expires_in: int


# Global orchestrator instance
orchestrator = PipelineOrchestrator(
    kafka_bootstrap_servers="localhost:9092",
    clickhouse_host="localhost",
)


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify username and password.

    PLACEHOLDER: Replace with actual database verification.
    """
    # In production, verify against database
    # For now, accept any credentials (development only)
    return bool(username and password)


@app.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest) -> LoginResponse:
    """Authenticate user and return JWT token."""
    if not verify_credentials(credentials.username, credentials.password):
        logger.warning(
            "login_failed",
            username=credentials.username,
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt_auth.create_token(
        user_id=credentials.username,
        tenant_id=credentials.username,
        scopes=["read", "write"],
    )

    logger.info(
        "login_success",
        user_id=credentials.username,
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=3600,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint (no auth required)."""
    return HealthResponse(
        status="healthy",
        service="settlement-pipeline",
    )


@app.get("/stats")
async def get_stats(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """Get pipeline statistics (requires authentication)."""
    logger.info("stats_requested", user_id=current_user.sub)
    return orchestrator.get_stats()


@app.post("/process", response_model=TransactionResponse)
async def process_transaction(
    request: TransactionRequest,
    current_user: TokenPayload = Depends(get_current_user),
) -> TransactionResponse:
    """Process a single transaction (requires write scope)."""
    # Verify tenant access
    if current_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Tenant mismatch",
        )

    # Verify write scope
    if "write" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Missing write scope",
        )

    try:
        import json

        message = json.dumps(request.model_dump()).encode("utf-8")
        processed, failed = orchestrator.process_batch([message])

        logger.info(
            "transaction_processed",
            user_id=current_user.sub,
            tenant_id=request.tenant_id,
        )

        return TransactionResponse(
            processed=processed,
            failed=failed,
            success_rate=100.0 if failed == 0 else 0.0,
        )
    except Exception as e:
        logger.error("process_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics() -> str:
    """Prometheus metrics endpoint (no auth required)."""
    from src.metrics_server import get_metrics

    return get_metrics().decode("utf-8")


@app.post("/process-admin")
async def process_transaction_admin(
    request: TransactionRequest,
    current_user: TokenPayload = Depends(require_scope("admin")),
) -> TransactionResponse:
    """Process transaction (requires admin scope)."""
    # Verify tenant access
    if current_user.tenant_id != request.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="Tenant mismatch",
        )

    # Verify write scope
    if "write" not in current_user.scopes:
        raise HTTPException(
            status_code=403,
            detail="Missing write scope",
        )

    try:
        import json

        message = json.dumps(request.model_dump()).encode("utf-8")
        processed, failed = orchestrator.process_batch([message])

        logger.info(
            "transaction_processed",
            user_id=current_user.sub,
            tenant_id=request.tenant_id,
        )

        return TransactionResponse(
            processed=processed,
            failed=failed,
            success_rate=100.0 if failed == 0 else 0.0,
        )
    except Exception as e:
        logger.error("process_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
