"""
Exponential backoff retry logic for API calls and network operations.

This module provides:
- RetryConfig dataclass for retry configuration
- Synchronous retry decorator with exponential backoff
- Async retry decorator with exponential backoff
- Intelligent handling of transient errors

Features:
- Configurable retry attempts and delays
- Exponential backoff with jitter to prevent thundering herd
- Specific exception type handling
- Comprehensive logging
"""

import asyncio
import logging
import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, TypeVar


# Type variables for generic decorators
F = TypeVar("F", bound=Callable[..., Any])
AsyncF = TypeVar("AsyncF", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior with exponential backoff.

    Attributes:
        max_attempts: Maximum number of retry attempts (including initial try)
        base_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to prevent thundering herd
        jitter_factor: Maximum jitter as fraction of delay (0.0-1.0)
        retryable_exceptions: Tuple of exception types that should trigger retry
        log_attempts: Whether to log retry attempts
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: tuple = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
            OSError,
        )
    )
    log_attempts: bool = True

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError("jitter_factor must be between 0 and 1")

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt.

        Args:
            attempt: The retry attempt number (0-based)

        Returns:
            Delay in seconds before next retry
        """
        # Exponential backoff: base_delay * (exponential_base ^ attempt)
        delay = self.base_delay * (self.exponential_base**attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter if enabled
        if self.jitter:
            jitter_amount = delay * self.jitter_factor
            delay += random.uniform(-jitter_amount, jitter_amount)
            # Ensure delay is still positive
            delay = max(0, delay)

        return delay


class RetryExhaustedError(Exception):
    """Raised when all retry attempts have been exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_exception: Exception | None = None,
    ):
        """
        Initialize retry exhausted error.

        Args:
            message: Error message
            attempts: Number of attempts made
            last_exception: The last exception that caused failure
        """
        super().__init__(message)
        self.attempts = attempts
        self.last_exception = last_exception


def retry_with_backoff(
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    retryable_exceptions: Sequence[type[Exception]] | None = None,
) -> Callable[[F], F]:
    """
    Decorator for synchronous functions to add retry logic with exponential backoff.

    Args:
        config: RetryConfig instance (overrides individual parameters)
        max_attempts: Maximum retry attempts (overrides config)
        base_delay: Initial delay in seconds (overrides config)
        retryable_exceptions: Exception types to retry on (overrides config)

    Returns:
        Decorated function with retry logic

    Examples:
        >>> @retry_with_backoff(max_attempts=3, base_delay=1.0)
        ... def fetch_data():
        ...     # Network call that might fail
        ...     return requests.get("https://api.example.com")

        >>> # With custom config
        >>> config = RetryConfig(max_attempts=5, base_delay=2.0)
        >>> @retry_with_backoff(config=config)
        ... def api_call():
        ...     return call_external_api()
    """
    # Create or update config
    if config is None:
        config = RetryConfig()
    else:
        # Create a copy to avoid modifying the original
        config = RetryConfig(
            max_attempts=config.max_attempts,
            base_delay=config.base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter,
            jitter_factor=config.jitter_factor,
            retryable_exceptions=config.retryable_exceptions,
            log_attempts=config.log_attempts,
        )

    # Override config with individual parameters
    if max_attempts is not None:
        config.max_attempts = max_attempts
    if base_delay is not None:
        config.base_delay = base_delay
    if retryable_exceptions is not None:
        config.retryable_exceptions = tuple(retryable_exceptions)

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    # Don't sleep after last attempt
                    if attempt == config.max_attempts - 1:
                        break

                    delay = config.calculate_delay(attempt)

                    if config.log_attempts:
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for "
                            f"{func.__name__}: {type(e).__name__}: {e!s}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                    time.sleep(delay)

            # All retries exhausted
            error_msg = f"Failed after {config.max_attempts} attempts: {func.__name__}"
            if config.log_attempts:
                logger.error(error_msg)

            raise RetryExhaustedError(
                error_msg,
                attempts=config.max_attempts,
                last_exception=last_exception,
            ) from last_exception

        return wrapper  # type: ignore

    return decorator


def async_retry_with_backoff(
    config: RetryConfig | None = None,
    max_attempts: int | None = None,
    base_delay: float | None = None,
    retryable_exceptions: Sequence[type[Exception]] | None = None,
) -> Callable[[AsyncF], AsyncF]:
    """
    Decorator for async functions to add retry logic with exponential backoff.

    Args:
        config: RetryConfig instance (overrides individual parameters)
        max_attempts: Maximum retry attempts (overrides config)
        base_delay: Initial delay in seconds (overrides config)
        retryable_exceptions: Exception types to retry on (overrides config)

    Returns:
        Decorated async function with retry logic

    Examples:
        >>> @async_retry_with_backoff(max_attempts=3)
        ... async def fetch_data():
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get("https://api.example.com") as resp:
        ...             return await resp.json()
    """
    # Create or update config
    if config is None:
        config = RetryConfig()
    else:
        # Create a copy to avoid modifying the original
        config = RetryConfig(
            max_attempts=config.max_attempts,
            base_delay=config.base_delay,
            max_delay=config.max_delay,
            exponential_base=config.exponential_base,
            jitter=config.jitter,
            jitter_factor=config.jitter_factor,
            retryable_exceptions=config.retryable_exceptions,
            log_attempts=config.log_attempts,
        )

    # Override config with individual parameters
    if max_attempts is not None:
        config.max_attempts = max_attempts
    if base_delay is not None:
        config.base_delay = base_delay
    if retryable_exceptions is not None:
        config.retryable_exceptions = tuple(retryable_exceptions)

    def decorator(func: AsyncF) -> AsyncF:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    # Don't sleep after last attempt
                    if attempt == config.max_attempts - 1:
                        break

                    delay = config.calculate_delay(attempt)

                    if config.log_attempts:
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed for "
                            f"{func.__name__}: {type(e).__name__}: {e!s}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                    await asyncio.sleep(delay)

            # All retries exhausted
            error_msg = f"Failed after {config.max_attempts} attempts: {func.__name__}"
            if config.log_attempts:
                logger.error(error_msg)

            raise RetryExhaustedError(
                error_msg,
                attempts=config.max_attempts,
                last_exception=last_exception,
            ) from last_exception

        return wrapper  # type: ignore

    return decorator


# Common retry configurations for different scenarios
class RetryPresets:
    """Preset retry configurations for common scenarios."""

    # Quick retries for fast operations
    QUICK = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
    )

    # Standard retries for normal API calls
    STANDARD = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
    )

    # Aggressive retries for critical operations
    AGGRESSIVE = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
    )

    # Conservative retries for rate-limited APIs
    CONSERVATIVE = RetryConfig(
        max_attempts=3,
        base_delay=5.0,
        max_delay=120.0,
        exponential_base=3.0,
    )


# Specific exception types for network and API errors
class NetworkException(Exception):
    """Base exception for network-related errors."""

    pass


class RateLimitException(NetworkException):
    """Exception raised when API rate limit is exceeded."""

    pass


class APITimeoutException(NetworkException):
    """Exception raised when API call times out."""

    pass


class APIServerException(NetworkException):
    """Exception raised for server-side API errors (5xx)."""

    pass


# Update default retryable exceptions to include our custom types
RetryConfig.__dataclass_fields__["retryable_exceptions"].default_factory = lambda: (
    ConnectionError,
    TimeoutError,
    OSError,
    NetworkException,
    RateLimitException,
    APITimeoutException,
    APIServerException,
)
