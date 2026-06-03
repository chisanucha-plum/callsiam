"""Core utilities for services: HTTP pooling, caching, etc."""

import hashlib
import logging
from functools import lru_cache
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HTTPConnectionPool:
    """Shared HTTP connection pool with keep-alive and retry logic."""

    def __init__(
        self,
        pool_connections: int = 10,
        pool_maxsize: int = 20,
        max_retries: int = 3,
        backoff_factor: float = 0.1,
    ) -> None:
        """Initialize HTTP connection pool.

        Args:
            pool_connections: Number of connection pools to cache.
            pool_maxsize: Maximum number of connections in the pool.
            max_retries: Maximum number of retry attempts.
            backoff_factor: Backoff factor for retries.
        """
        self._session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )

        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy,
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update({"Connection": "keep-alive"})

        logger.info("HTTP pool initialized")

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make a POST request using connection pool."""
        return self._session.post(url, **kwargs)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make a GET request using connection pool."""
        return self._session.get(url, **kwargs)

    def close(self) -> None:
        """Close all connections."""
        self._session.close()


@lru_cache(maxsize=1)
def get_http_pool() -> HTTPConnectionPool:
    """Get shared HTTP connection pool."""
    return HTTPConnectionPool()


class ResponseCache:
    """Generic response cache for TTS and other services."""

    def __init__(self, max_size: int = 100) -> None:
        """Initialize cache."""
        self._cache: Dict[str, bytes] = {}
        self._max_size = max_size
        self._hits = 0
        self._misses = 0
        logger.info("Cache initialized with max_size=%d", max_size)

    def get(self, key: str) -> Optional[bytes]:
        """Get cached value."""
        value = self._cache.get(key)
        if value:
            self._hits += 1
        else:
            self._misses += 1
        return value

    def put(self, key: str, value: bytes) -> None:
        """Store in cache."""
        if len(self._cache) >= self._max_size:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = value

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        total = self._hits + self._misses
        return (self._hits / total * 100) if total > 0 else 0

    def clear(self) -> None:
        """Clear cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


def make_cache_key(text: str) -> str:
    """Generate cache key from text."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()
