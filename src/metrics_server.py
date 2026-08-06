from prometheus_client import generate_latest, REGISTRY

from src.utils.logging import get_logger

logger = get_logger(__name__)


def get_metrics() -> bytes:
    """Generate Prometheus metrics endpoint."""
    return generate_latest(REGISTRY)


def metrics_handler() -> bytes:
    """Handle metrics requests."""
    return get_metrics()


def start_metrics_server(port: int = 8000) -> None:
    """Start HTTP server for metrics (requires FastAPI/Uvicorn)."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import Response
        import uvicorn

        app = FastAPI()

        @app.get("/metrics")
        def metrics() -> Response:
            """Prometheus metrics endpoint."""
            return Response(metrics_handler(), media_type="text/plain")

        logger.info(
            "metrics_server_started",
            port=port,
        )
        uvicorn.run(app, host="0.0.0.0", port=port)  # nosec
    except ImportError:
        logger.error("fastapi_not_installed")
