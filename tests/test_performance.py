"""Performance benchmarking tests."""
import time
import concurrent.futures
from typing import Generator

import pytest

from src.cache.redis_cache import RedisCache, cache_result


@pytest.fixture
def redis_cache() -> Generator[RedisCache, None, None]:
    """Create Redis cache instance."""
    cache_inst = RedisCache(host="localhost", port=6379, db=0)
    # Flush before test
    cache_inst.flush()
    yield cache_inst
    # Flush after test
    cache_inst.flush()


@pytest.fixture(autouse=True)
def flush_cache() -> Generator[None, None, None]:
    """Auto-flush cache before each test."""
    cache = RedisCache(host="localhost", port=6379, db=0)
    cache.flush()
    yield
    cache.flush()


def test_cache_set_get_performance(redis_cache: RedisCache) -> None:
    """Test cache set/get performance."""
    test_data = {
        "transactions": [{"id": f"tx_{i}", "amount": 100.50} for i in range(1000)]
    }

    # Measure set time
    start = time.time()
    redis_cache.set("perf_test", test_data, ttl=60)
    set_time = time.time() - start

    # Measure get time
    start = time.time()
    result = redis_cache.get("perf_test")
    get_time = time.time() - start

    assert result == test_data
    assert set_time < 0.05  # < 50ms
    assert get_time < 0.01  # < 10ms


def test_cache_decorator_caching() -> None:
    """Test cache decorator effectiveness."""
    call_count = 0

    @cache_result(ttl=60)
    def expensive_function(param: str) -> dict:
        nonlocal call_count
        call_count += 1
        return {"param": param, "result": "expensive"}

    # First call - executes function
    result1 = expensive_function("test")
    assert call_count == 1

    # Second call - cached
    result2 = expensive_function("test")
    assert call_count == 1  # Not incremented
    assert result1 == result2


def test_cache_miss_performance(redis_cache: RedisCache) -> None:
    """Test cache miss doesn't block execution."""
    # Delete key to ensure miss
    redis_cache.delete("nonexistent_key")

    start = time.time()
    result = redis_cache.get("nonexistent_key")
    elapsed = time.time() - start

    assert result is None
    assert elapsed < 0.01  # < 10ms


def test_cache_ttl_expiry(redis_cache: RedisCache) -> None:
    """Test cache TTL functionality."""
    redis_cache.set("expiry_test", {"data": "value"}, ttl=1)

    # Immediately available
    assert redis_cache.get("expiry_test") is not None

    # Wait for expiry
    time.sleep(1.5)
    assert redis_cache.get("expiry_test") is None


def test_cache_stats(redis_cache: RedisCache) -> None:
    """Test cache statistics retrieval."""
    redis_cache.set("stat_test", {"data": "value"}, ttl=60)

    stats = redis_cache.get_stats()

    assert "used_memory" in stats
    assert "keyspace" in stats
    assert stats["keyspace"] >= 1


def test_concurrent_cache_access(redis_cache: RedisCache) -> None:
    """Test concurrent cache access."""

    def cache_operation(i: int) -> bool:
        key = f"concurrent_{i}"
        redis_cache.set(key, {"index": i}, ttl=60)
        result = redis_cache.get(key)
        return result is not None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(cache_operation, range(100)))

    assert all(results)
    assert len([r for r in results if r]) == 100
