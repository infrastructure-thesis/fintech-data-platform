from src.utils.logging import configure_logging, get_logger


def test_configure_logging():
    """Test logging configuration."""
    configure_logging()  # Should not raise


def test_get_logger():
    """Test getting a logger."""
    logger = get_logger("test_module")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
