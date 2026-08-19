"""Redis-based caching for query results."""
import json
import redis
from functools import wraps
from typing import Any, Callable, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Redis client configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


class RedisCache:
    """Redis caching client."""

    def __init__(
        self,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        db: int = REDIS_DB,
    ) -> None:
        self.client = redis.Redis(  # type: ignore[var-annotated]
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.client.get(key)  # type: ignore[union-attr]
            if value:
                logger.debug("cache_hit", key=key)
                return json.loads(value)  # type: ignore[arg-type]
            logger.debug("cache_miss", key=key)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL."""
        try:
            self.client.setex(key, ttl, json.dumps(value))
            logger.debug("cache_set", key=key, ttl=ttl)
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.client.delete(key)
            logger.debug("cache_delete", key=key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    def flush(self) -> bool:
        """Flush entire cache."""
        try:
            self.client.flushdb()
            logger.info("cache_flush")
            return True
        except Exception as e:
            logger.error("cache_flush_error", error=str(e))
            return False

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.client.info()  # type: ignore[union-attr]
            return {
                "used_memory": (
                    info.get("used_memory_human")  # type: ignore[union-attr]
                ),
                "connected_clients": (
                    info.get("connected_clients")  # type: ignore[union-attr]
                ),
                "total_commands": (
                    info.get("total_commands_processed")  # type: ignore[union-attr]
                ),
                "keyspace": self.client.dbsize(),
            }
        except Exception as e:
            logger.error("cache_stats_error", error=str(e))
            return {}


# Global cache instance
cache = RedisCache()


def cache_result(
    ttl: int = 300,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to cache function results in Redis."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__module__}:{func.__name__}:" f"{args}:{kwargs}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator
