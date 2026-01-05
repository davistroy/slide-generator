"""
Resilient API client wrappers with circuit breakers and retry logic.
"""

import logging
from functools import wraps
from typing import Callable, TypeVar, Any

from circuitbreaker import circuit, CircuitBreakerError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


# Circuit breaker configuration
CIRCUIT_FAILURE_THRESHOLD = 5
CIRCUIT_RECOVERY_TIMEOUT = 60
CIRCUIT_EXPECTED_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    Exception  # Catch API errors
)

# Retry configuration
RETRY_MAX_ATTEMPTS = 3
RETRY_MIN_WAIT = 4
RETRY_MAX_WAIT = 60
RETRY_MULTIPLIER = 2


class APICircuitOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


def resilient_api_call(
    failure_threshold: int = CIRCUIT_FAILURE_THRESHOLD,
    recovery_timeout: int = CIRCUIT_RECOVERY_TIMEOUT,
    max_retries: int = RETRY_MAX_ATTEMPTS
) -> Callable:
    """
    Decorator combining circuit breaker and retry logic.

    Usage:
        @resilient_api_call()
        def call_claude_api(prompt):
            return client.messages.create(...)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Apply circuit breaker
        @circuit(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=CIRCUIT_EXPECTED_EXCEPTIONS
        )
        # Apply retry logic
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(
                multiplier=RETRY_MULTIPLIER,
                min=RETRY_MIN_WAIT,
                max=RETRY_MAX_WAIT
            ),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            before_sleep=before_sleep_log(logger, logging.WARNING)
        )
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open for {func.__name__}: {e}")
                raise APICircuitOpen(
                    f"Service temporarily unavailable. "
                    f"Circuit breaker will reset in {recovery_timeout}s"
                ) from e

        return wrapper
    return decorator


class ResilientClaudeClient:
    """Claude API client with circuit breaker and retry logic."""

    def __init__(self, client):
        self.client = client

    @resilient_api_call(failure_threshold=5, recovery_timeout=60)
    def create_message(self, **kwargs) -> Any:
        """Create a message with resilience."""
        return self.client.messages.create(**kwargs)

    @resilient_api_call(failure_threshold=3, recovery_timeout=30)
    def create_completion(self, **kwargs) -> Any:
        """Create a completion with resilience."""
        return self.client.completions.create(**kwargs)


class ResilientGeminiClient:
    """Gemini API client with circuit breaker and retry logic."""

    def __init__(self, client):
        self.client = client

    @resilient_api_call(failure_threshold=3, recovery_timeout=60)
    def generate_image(self, prompt: str, **kwargs) -> Any:
        """Generate image with resilience."""
        return self.client.generate(prompt, **kwargs)


def call_with_resilience(func: Callable, *args, **kwargs) -> Any:
    """Call any function with resilience wrapper."""
    @resilient_api_call()
    def wrapped():
        return func(*args, **kwargs)
    return wrapped()
