"""
Rate limiting for API calls using token bucket algorithm.

This module provides:
- Token bucket rate limiter implementation
- Multi-provider API rate limiter
- Thread-safe and async-compatible rate limiting
- Per-provider rate limit configuration

Features:
- Configurable requests per second/minute
- Thread-safe using locks
- Async support with async_acquire
- Multiple concurrent API providers
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """
    Configuration for rate limiting.

    Attributes:
        requests_per_minute: Maximum requests per minute
        requests_per_second: Maximum requests per second (takes precedence)
        burst_size: Maximum burst size (tokens in bucket)
    """

    requests_per_minute: int = 60
    requests_per_second: float | None = None
    burst_size: int | None = None

    def __post_init__(self):
        """Calculate derived values."""
        # If requests_per_second is specified, use it
        if self.requests_per_second is not None:
            self.rate = self.requests_per_second
        else:
            # Convert requests_per_minute to requests per second
            self.rate = self.requests_per_minute / 60.0

        # Default burst size is the rate (allows 1 second of burst)
        if self.burst_size is None:
            self.burst_size = max(1, int(self.rate))


class RateLimiter:
    """
    Token bucket rate limiter for controlling request rates.

    This implementation uses the token bucket algorithm:
    - Tokens are added to a bucket at a fixed rate
    - Each request consumes one token
    - If no tokens available, request must wait

    Thread-safe and async-compatible.
    """

    def __init__(
        self,
        rate: float,
        burst_size: int,
        name: str = "rate_limiter",
    ):
        """
        Initialize rate limiter.

        Args:
            rate: Rate of token generation (tokens per second)
            burst_size: Maximum number of tokens in bucket
            name: Name for logging purposes
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if burst_size <= 0:
            raise ValueError("Burst size must be positive")

        self.rate = rate
        self.burst_size = burst_size
        self.name = name

        # Token bucket state
        self.tokens = float(burst_size)  # Start with full bucket
        self.last_update = time.monotonic()

        # Thread safety
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time since last update."""
        now = time.monotonic()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst_size, self.tokens + new_tokens)
        self.last_update = now

    def _wait_time(self, tokens_needed: float = 1.0) -> float:
        """
        Calculate wait time for tokens.

        Args:
            tokens_needed: Number of tokens needed

        Returns:
            Time to wait in seconds (0 if tokens available)
        """
        self._add_tokens()

        if self.tokens >= tokens_needed:
            return 0.0

        # Calculate how long until we have enough tokens
        tokens_short = tokens_needed - self.tokens
        wait_time = tokens_short / self.rate
        return wait_time

    def acquire(self, tokens: float = 1.0, timeout: float | None = None) -> bool:
        """
        Acquire tokens (blocking, thread-safe).

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if tokens acquired, False if timeout exceeded

        Examples:
            >>> limiter = RateLimiter(rate=10.0, burst_size=10)
            >>> limiter.acquire()  # Blocks if no tokens available
            True
        """
        start_time = time.monotonic()

        with self._lock:
            while True:
                wait_time = self._wait_time(tokens)

                if wait_time <= 0:
                    # Tokens available - consume them
                    self.tokens -= tokens
                    logger.debug(
                        f"[{self.name}] Acquired {tokens} token(s), "
                        f"{self.tokens:.2f} remaining"
                    )
                    return True

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed + wait_time > timeout:
                        logger.warning(
                            f"[{self.name}] Timeout waiting for {tokens} token(s)"
                        )
                        return False

                # Wait for tokens (release lock during sleep)
                logger.debug(
                    f"[{self.name}] Waiting {wait_time:.2f}s for {tokens} token(s)"
                )
                self._lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._lock.acquire()

    async def async_acquire(
        self, tokens: float = 1.0, timeout: float | None = None
    ) -> bool:
        """
        Acquire tokens (async, non-blocking).

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds (None = wait forever)

        Returns:
            True if tokens acquired, False if timeout exceeded

        Examples:
            >>> limiter = RateLimiter(rate=10.0, burst_size=10)
            >>> await limiter.async_acquire()
            True
        """
        start_time = time.monotonic()

        async with self._async_lock:
            while True:
                # Use thread lock for token calculation
                with self._lock:
                    wait_time = self._wait_time(tokens)

                    if wait_time <= 0:
                        # Tokens available - consume them
                        self.tokens -= tokens
                        logger.debug(
                            f"[{self.name}] Acquired {tokens} token(s), "
                            f"{self.tokens:.2f} remaining"
                        )
                        return True

                # Check timeout
                if timeout is not None:
                    elapsed = time.monotonic() - start_time
                    if elapsed + wait_time > timeout:
                        logger.warning(
                            f"[{self.name}] Timeout waiting for {tokens} token(s)"
                        )
                        return False

                # Wait for tokens (async sleep)
                logger.debug(
                    f"[{self.name}] Waiting {wait_time:.2f}s for {tokens} token(s)"
                )
                await asyncio.sleep(wait_time)

    def get_available_tokens(self) -> float:
        """
        Get current number of available tokens.

        Returns:
            Number of tokens currently available
        """
        with self._lock:
            self._add_tokens()
            return self.tokens

    def reset(self) -> None:
        """Reset the rate limiter to full capacity."""
        with self._lock:
            self.tokens = float(self.burst_size)
            self.last_update = time.monotonic()
            logger.info(f"[{self.name}] Rate limiter reset")


class APIRateLimiter:
    """
    Rate limiter for multiple API providers.

    Manages separate rate limits for different API providers
    (Claude, Gemini, etc.) with provider-specific configurations.
    """

    # Default rate limits per provider (requests per minute)
    DEFAULT_LIMITS = {
        "claude": RateLimitConfig(requests_per_minute=50, burst_size=5),
        "anthropic": RateLimitConfig(requests_per_minute=50, burst_size=5),
        "gemini": RateLimitConfig(requests_per_minute=60, burst_size=10),
        "google": RateLimitConfig(requests_per_minute=60, burst_size=10),
        "default": RateLimitConfig(requests_per_minute=30, burst_size=5),
    }

    def __init__(
        self,
        custom_limits: dict[str, RateLimitConfig] | None = None,
    ):
        """
        Initialize API rate limiter.

        Args:
            custom_limits: Custom rate limit configurations per provider
        """
        self._limiters: dict[str, RateLimiter] = {}
        self._custom_limits = custom_limits or {}
        self._lock = threading.Lock()

    def _get_config(self, provider: str) -> RateLimitConfig:
        """
        Get rate limit configuration for provider.

        Args:
            provider: API provider name

        Returns:
            Rate limit configuration
        """
        provider_lower = provider.lower()

        # Check custom limits first
        if provider_lower in self._custom_limits:
            return self._custom_limits[provider_lower]

        # Check default limits
        if provider_lower in self.DEFAULT_LIMITS:
            return self.DEFAULT_LIMITS[provider_lower]

        # Use default config
        return self.DEFAULT_LIMITS["default"]

    def _get_limiter(self, provider: str) -> RateLimiter:
        """
        Get or create rate limiter for provider.

        Args:
            provider: API provider name

        Returns:
            RateLimiter instance for the provider
        """
        provider_lower = provider.lower()

        # Check if limiter exists
        if provider_lower not in self._limiters:
            with self._lock:
                # Double-check after acquiring lock
                if provider_lower not in self._limiters:
                    config = self._get_config(provider_lower)
                    self._limiters[provider_lower] = RateLimiter(
                        rate=config.rate,
                        burst_size=config.burst_size or 1,
                        name=f"{provider_lower}_api",
                    )
                    logger.info(
                        f"Created rate limiter for {provider_lower}: "
                        f"{config.rate:.2f} req/s, burst={config.burst_size}"
                    )

        return self._limiters[provider_lower]

    def acquire(
        self,
        provider: str,
        tokens: float = 1.0,
        timeout: float | None = None,
    ) -> bool:
        """
        Acquire rate limit token for API call (blocking).

        Args:
            provider: API provider name
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds

        Returns:
            True if token acquired, False if timeout

        Examples:
            >>> limiter = APIRateLimiter()
            >>> limiter.acquire("claude")  # Blocks if rate limit exceeded
            True
        """
        limiter = self._get_limiter(provider)
        return limiter.acquire(tokens=tokens, timeout=timeout)

    async def async_acquire(
        self,
        provider: str,
        tokens: float = 1.0,
        timeout: float | None = None,
    ) -> bool:
        """
        Acquire rate limit token for API call (async).

        Args:
            provider: API provider name
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds

        Returns:
            True if token acquired, False if timeout

        Examples:
            >>> limiter = APIRateLimiter()
            >>> await limiter.async_acquire("gemini")
            True
        """
        limiter = self._get_limiter(provider)
        return await limiter.async_acquire(tokens=tokens, timeout=timeout)

    def get_available_tokens(self, provider: str) -> float:
        """
        Get available tokens for provider.

        Args:
            provider: API provider name

        Returns:
            Number of available tokens
        """
        limiter = self._get_limiter(provider)
        return limiter.get_available_tokens()

    def reset(self, provider: str | None = None) -> None:
        """
        Reset rate limiter(s).

        Args:
            provider: Provider to reset (None = reset all)
        """
        if provider is None:
            # Reset all limiters
            with self._lock:
                for limiter in self._limiters.values():
                    limiter.reset()
                logger.info("Reset all API rate limiters")
        else:
            # Reset specific provider
            limiter = self._get_limiter(provider)
            limiter.reset()

    def set_limit(
        self,
        provider: str,
        config: RateLimitConfig,
    ) -> None:
        """
        Set or update rate limit for provider.

        Args:
            provider: API provider name
            config: New rate limit configuration
        """
        provider_lower = provider.lower()

        with self._lock:
            # Store custom limit
            self._custom_limits[provider_lower] = config

            # If limiter exists, recreate it with new config
            if provider_lower in self._limiters:
                del self._limiters[provider_lower]
                logger.info(f"Updated rate limit for {provider_lower}")


# Global API rate limiter instance
_global_limiter: APIRateLimiter | None = None


def get_global_rate_limiter() -> APIRateLimiter:
    """
    Get the global API rate limiter instance.

    Returns:
        Global APIRateLimiter instance
    """
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = APIRateLimiter()
    return _global_limiter
