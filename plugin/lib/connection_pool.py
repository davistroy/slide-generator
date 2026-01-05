"""
HTTP Connection Pool for Async API Clients

Provides configurable connection pooling for httpx-based async HTTP clients.
Includes health checking, automatic reconnection, and usage statistics.

Usage:
    pool = ConnectionPool(
        pool_size=10,
        timeout=30.0,
        keepalive=60.0
    )

    async with pool:
        response = await pool.client.get(url)

    # Check pool stats
    stats = pool.get_stats()
"""

import asyncio
import time
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ConnectionPoolStats:
    """Statistics for connection pool usage."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    active_connections: int = 0
    reconnections: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    average_response_time: float = 0.0
    last_health_check: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "active_connections": self.active_connections,
            "reconnections": self.reconnections,
            "total_bytes_sent": self.total_bytes_sent,
            "total_bytes_received": self.total_bytes_received,
            "average_response_time": self.average_response_time,
            "last_health_check": self.last_health_check,
        }


class ConnectionPool:
    """
    HTTP connection pool with health checking and automatic reconnection.

    Features:
    - Configurable pool size and timeouts
    - Connection keepalive
    - Health checking
    - Automatic reconnection on failures
    - Request/response statistics
    - Async context manager support

    Args:
        pool_size: Maximum number of connections in pool (default: 10)
        timeout: Request timeout in seconds (default: 30.0)
        keepalive: Connection keepalive in seconds (default: 60.0)
        max_keepalive_connections: Maximum keepalive connections (default: pool_size)
        max_connections: Maximum total connections (default: pool_size * 2)
        enable_http2: Enable HTTP/2 support (default: True)
        verify_ssl: Verify SSL certificates (default: True)

    Example:
        >>> async with ConnectionPool(pool_size=5) as pool:
        ...     response = await pool.client.get("https://api.example.com")
        ...     stats = pool.get_stats()
    """

    def __init__(
        self,
        pool_size: int = 10,
        timeout: float = 30.0,
        keepalive: float = 60.0,
        max_keepalive_connections: int | None = None,
        max_connections: int | None = None,
        enable_http2: bool = True,
        verify_ssl: bool = True,
        headers: dict[str, str] | None = None,
    ):
        """Initialize connection pool."""
        self.pool_size = pool_size
        self.timeout = timeout
        self.keepalive = keepalive
        self.max_keepalive_connections = max_keepalive_connections or pool_size
        self.max_connections = max_connections or (pool_size * 2)
        self.enable_http2 = enable_http2
        self.verify_ssl = verify_ssl
        self.default_headers = headers or {}

        self._client: httpx.AsyncClient | None = None
        self._stats = ConnectionPoolStats()
        self._lock = asyncio.Lock()
        self._response_times: list[float] = []
        self._health_check_task: asyncio.Task | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the underlying httpx client."""
        if self._client is None:
            raise RuntimeError(
                "Connection pool not initialized. Use 'async with' context manager."
            )
        return self._client

    async def __aenter__(self) -> "ConnectionPool":
        """Enter async context manager - initialize connection pool."""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager - close connection pool."""
        await self._cleanup()

    async def _initialize(self) -> None:
        """Initialize the HTTP client with connection pool settings."""
        limits = httpx.Limits(
            max_keepalive_connections=self.max_keepalive_connections,
            max_connections=self.max_connections,
            keepalive_expiry=self.keepalive,
        )

        timeout = httpx.Timeout(self.timeout)

        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=self.enable_http2,
            verify=self.verify_ssl,
            headers=self.default_headers,
        )

        # Start health check task
        self._health_check_task = asyncio.create_task(self._periodic_health_check())

    async def _cleanup(self) -> None:
        """Clean up resources."""
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._health_check_task

        # Close client
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _periodic_health_check(self) -> None:
        """Periodically check connection health."""
        while True:
            try:
                await asyncio.sleep(30.0)  # Check every 30 seconds
                await self._health_check()
            except asyncio.CancelledError:
                break
            except Exception:
                # Silently continue on health check errors
                pass

    async def _health_check(self) -> bool:
        """
        Perform health check on connection pool.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Simple check - ensure client is still operational
            if self._client is None or self._client.is_closed:
                return False

            async with self._lock:
                self._stats.last_health_check = time.time()

            return True
        except Exception:
            return False

    async def reconnect(self) -> None:
        """Reconnect the client (close and reinitialize)."""
        async with self._lock:
            # Close existing client
            if self._client:
                await self._client.aclose()

            # Reinitialize
            await self._initialize()

            self._stats.reconnections += 1

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """
        Make an HTTP request with automatic retry on connection failure.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional arguments passed to httpx.request()

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On request failure after retry
        """
        start_time = time.time()

        try:
            async with self._lock:
                self._stats.total_requests += 1
                self._stats.active_connections += 1

            response = await self.client.request(method, url, **kwargs)

            # Track success
            async with self._lock:
                self._stats.successful_requests += 1
                response_time = time.time() - start_time
                self._response_times.append(response_time)

                # Keep only last 100 response times
                if len(self._response_times) > 100:
                    self._response_times.pop(0)

                # Update average
                if self._response_times:
                    self._stats.average_response_time = sum(self._response_times) / len(
                        self._response_times
                    )

                # Track bytes (if available)
                if hasattr(response, "num_bytes_downloaded"):
                    self._stats.total_bytes_received += response.num_bytes_downloaded

            return response

        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            # Connection error - try to reconnect once
            async with self._lock:
                self._stats.failed_requests += 1

            # Attempt reconnection
            await self.reconnect()

            # Retry request once
            try:
                response = await self.client.request(method, url, **kwargs)

                async with self._lock:
                    self._stats.successful_requests += 1

                return response
            except Exception:
                raise e

        except Exception:
            async with self._lock:
                self._stats.failed_requests += 1
            raise

        finally:
            async with self._lock:
                self._stats.active_connections -= 1

    def get_stats(self) -> ConnectionPoolStats:
        """
        Get current connection pool statistics.

        Returns:
            ConnectionPoolStats object with current stats
        """
        return self._stats

    def reset_stats(self) -> None:
        """Reset all statistics to zero."""
        self._stats = ConnectionPoolStats()
        self._response_times.clear()

    @asynccontextmanager
    async def stream(self, method: str, url: str, **kwargs):
        """
        Context manager for streaming requests.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx.stream()

        Yields:
            httpx.Response object for streaming

        Example:
            >>> async with pool.stream("GET", url) as response:
            ...     async for chunk in response.aiter_bytes():
            ...         process(chunk)
        """
        async with self._lock:
            self._stats.total_requests += 1
            self._stats.active_connections += 1

        try:
            async with self.client.stream(method, url, **kwargs) as response:
                yield response

                async with self._lock:
                    self._stats.successful_requests += 1

        except Exception:
            async with self._lock:
                self._stats.failed_requests += 1
            raise

        finally:
            async with self._lock:
                self._stats.active_connections -= 1


# Convenience function for creating a connection pool
def create_connection_pool(
    pool_size: int = 10, timeout: float = 30.0, **kwargs
) -> ConnectionPool:
    """
    Create a connection pool with default settings.

    Args:
        pool_size: Maximum number of connections
        timeout: Request timeout in seconds
        **kwargs: Additional arguments for ConnectionPool

    Returns:
        ConnectionPool instance
    """
    return ConnectionPool(pool_size=pool_size, timeout=timeout, **kwargs)
