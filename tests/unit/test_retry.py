"""
Unit tests for retry module.

Tests exponential backoff retry logic, decorators, and retry configurations.
"""

import time
from unittest.mock import AsyncMock, patch

import pytest

from plugin.lib.retry import (
    APIServerException,
    APITimeoutException,
    NetworkException,
    RateLimitException,
    RetryConfig,
    RetryExhaustedError,
    RetryPresets,
    async_retry_with_backoff,
    retry_with_backoff,
)


# ==============================================================================
# Test RetryConfig Dataclass
# ==============================================================================


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """Test RetryConfig has sensible defaults."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.jitter_factor == 0.1
        assert config.log_attempts is True

    def test_custom_values(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
            jitter_factor=0.2,
            log_attempts=False,
        )

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.jitter_factor == 0.2
        assert config.log_attempts is False

    def test_custom_retryable_exceptions(self):
        """Test RetryConfig with custom exception types."""
        config = RetryConfig(retryable_exceptions=(ValueError, KeyError))

        assert ValueError in config.retryable_exceptions
        assert KeyError in config.retryable_exceptions
        assert ConnectionError not in config.retryable_exceptions

    def test_default_retryable_exceptions_include_network_errors(self):
        """Test default exceptions include network-related errors."""
        config = RetryConfig()

        # Default includes basic Python network exceptions
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
        assert OSError in config.retryable_exceptions

        # Custom exceptions need to be explicitly added
        config_with_custom = RetryConfig(
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                OSError,
                NetworkException,
                RateLimitException,
                APITimeoutException,
                APIServerException,
            )
        )
        assert NetworkException in config_with_custom.retryable_exceptions
        assert RateLimitException in config_with_custom.retryable_exceptions
        assert APITimeoutException in config_with_custom.retryable_exceptions
        assert APIServerException in config_with_custom.retryable_exceptions


class TestRetryConfigValidation:
    """Tests for RetryConfig validation in __post_init__."""

    def test_max_attempts_must_be_positive(self):
        """Test max_attempts validation."""
        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            RetryConfig(max_attempts=0)

        with pytest.raises(ValueError, match="max_attempts must be at least 1"):
            RetryConfig(max_attempts=-1)

    def test_max_attempts_of_one_is_valid(self):
        """Test max_attempts of 1 is allowed (no retries, just one try)."""
        config = RetryConfig(max_attempts=1)
        assert config.max_attempts == 1

    def test_base_delay_must_be_non_negative(self):
        """Test base_delay validation."""
        with pytest.raises(ValueError, match="base_delay must be non-negative"):
            RetryConfig(base_delay=-1.0)

    def test_base_delay_of_zero_is_valid(self):
        """Test base_delay of 0 is allowed."""
        config = RetryConfig(base_delay=0.0)
        assert config.base_delay == 0.0

    def test_max_delay_must_be_gte_base_delay(self):
        """Test max_delay must be >= base_delay."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_max_delay_equal_to_base_delay_is_valid(self):
        """Test max_delay equal to base_delay is allowed."""
        config = RetryConfig(base_delay=5.0, max_delay=5.0)
        assert config.max_delay == 5.0

    def test_exponential_base_must_be_gte_one(self):
        """Test exponential_base validation."""
        with pytest.raises(ValueError, match="exponential_base must be >= 1"):
            RetryConfig(exponential_base=0.5)

    def test_exponential_base_of_one_is_valid(self):
        """Test exponential_base of 1 is allowed (linear backoff)."""
        config = RetryConfig(exponential_base=1.0)
        assert config.exponential_base == 1.0

    def test_jitter_factor_must_be_between_zero_and_one(self):
        """Test jitter_factor validation."""
        with pytest.raises(ValueError, match="jitter_factor must be between 0 and 1"):
            RetryConfig(jitter_factor=-0.1)

        with pytest.raises(ValueError, match="jitter_factor must be between 0 and 1"):
            RetryConfig(jitter_factor=1.1)

    def test_jitter_factor_boundary_values(self):
        """Test jitter_factor boundary values 0 and 1 are valid."""
        config_zero = RetryConfig(jitter_factor=0.0)
        assert config_zero.jitter_factor == 0.0

        config_one = RetryConfig(jitter_factor=1.0)
        assert config_one.jitter_factor == 1.0


class TestRetryConfigCalculateDelay:
    """Tests for RetryConfig.calculate_delay method."""

    def test_exponential_backoff_calculation(self):
        """Test exponential backoff formula."""
        config = RetryConfig(
            base_delay=1.0, exponential_base=2.0, max_delay=100.0, jitter=False
        )

        # attempt 0: 1.0 * 2^0 = 1.0
        assert config.calculate_delay(0) == 1.0

        # attempt 1: 1.0 * 2^1 = 2.0
        assert config.calculate_delay(1) == 2.0

        # attempt 2: 1.0 * 2^2 = 4.0
        assert config.calculate_delay(2) == 4.0

        # attempt 3: 1.0 * 2^3 = 8.0
        assert config.calculate_delay(3) == 8.0

    def test_max_delay_cap(self):
        """Test delay is capped at max_delay."""
        config = RetryConfig(
            base_delay=10.0, exponential_base=2.0, max_delay=30.0, jitter=False
        )

        # attempt 0: 10.0 * 2^0 = 10.0 (within cap)
        assert config.calculate_delay(0) == 10.0

        # attempt 1: 10.0 * 2^1 = 20.0 (within cap)
        assert config.calculate_delay(1) == 20.0

        # attempt 2: 10.0 * 2^2 = 40.0 (exceeds cap, should be 30.0)
        assert config.calculate_delay(2) == 30.0

        # attempt 10: would be huge, but capped at 30.0
        assert config.calculate_delay(10) == 30.0

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        config = RetryConfig(
            base_delay=10.0,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=True,
            jitter_factor=0.1,
        )

        # With jitter, delay should vary within +-10% of base
        # For attempt 0, base is 10.0, so range is 9.0-11.0
        delays = [config.calculate_delay(0) for _ in range(100)]

        # Check that there's variation
        assert len(set(delays)) > 1, "Jitter should produce varying delays"

        # Check that all delays are within expected range
        for delay in delays:
            assert 9.0 <= delay <= 11.0, f"Delay {delay} outside expected range"

    def test_jitter_disabled(self):
        """Test delay is consistent when jitter is disabled."""
        config = RetryConfig(
            base_delay=10.0, exponential_base=2.0, max_delay=100.0, jitter=False
        )

        delays = [config.calculate_delay(0) for _ in range(10)]

        # All delays should be identical
        assert len(set(delays)) == 1, "Without jitter, delays should be consistent"
        assert all(d == 10.0 for d in delays)

    def test_delay_never_negative_with_jitter(self):
        """Test delay never goes negative even with large jitter."""
        config = RetryConfig(
            base_delay=0.1,
            exponential_base=2.0,
            max_delay=100.0,
            jitter=True,
            jitter_factor=1.0,
        )

        # With jitter_factor=1.0, jitter could theoretically subtract 100%
        # but delay should always be >= 0
        delays = [config.calculate_delay(0) for _ in range(100)]

        for delay in delays:
            assert delay >= 0, f"Delay should never be negative, got {delay}"

    def test_linear_backoff_with_base_one(self):
        """Test linear backoff when exponential_base is 1."""
        config = RetryConfig(
            base_delay=5.0, exponential_base=1.0, max_delay=100.0, jitter=False
        )

        # With exponential_base=1, delay should always be base_delay
        assert config.calculate_delay(0) == 5.0
        assert config.calculate_delay(1) == 5.0
        assert config.calculate_delay(5) == 5.0


# ==============================================================================
# Test RetryExhaustedError Exception
# ==============================================================================


class TestRetryExhaustedError:
    """Tests for RetryExhaustedError exception."""

    def test_basic_creation(self):
        """Test creating RetryExhaustedError."""
        error = RetryExhaustedError("Failed after 3 attempts", attempts=3)

        assert str(error) == "Failed after 3 attempts"
        assert error.attempts == 3
        assert error.last_exception is None

    def test_with_last_exception(self):
        """Test RetryExhaustedError with last_exception."""
        original_error = ConnectionError("Network down")
        error = RetryExhaustedError(
            "Failed after 3 attempts", attempts=3, last_exception=original_error
        )

        assert error.attempts == 3
        assert error.last_exception is original_error
        assert isinstance(error.last_exception, ConnectionError)

    def test_inherits_from_exception(self):
        """Test RetryExhaustedError inherits from Exception."""
        error = RetryExhaustedError("Test", attempts=1)
        assert isinstance(error, Exception)


# ==============================================================================
# Test Synchronous Retry Decorator
# ==============================================================================


class TestRetryWithBackoffDecorator:
    """Tests for retry_with_backoff decorator."""

    def test_successful_call_no_retry(self):
        """Test successful call doesn't retry."""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()

        assert result == "success"
        assert call_count == 1

    def test_retry_on_retryable_exception(self):
        """Test retry on retryable exception."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,  # Very short delay for testing
            retryable_exceptions=[ValueError],
        )
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = failing_then_success()

        assert result == "success"
        assert call_count == 3

    def test_raises_retry_exhausted_on_persistent_failure(self):
        """Test RetryExhaustedError when all retries fail."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            retryable_exceptions=[ValueError],
        )
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_fails()

        assert call_count == 3
        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_non_retryable_exception_not_retried(self):
        """Test non-retryable exception raises immediately."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        def raises_key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError("Not retryable")

        with pytest.raises(KeyError):
            raises_key_error()

        # Should only be called once - no retries for non-retryable exceptions
        assert call_count == 1

    def test_decorator_with_config_object(self):
        """Test decorator with RetryConfig object."""
        call_count = 0
        config = RetryConfig(
            max_attempts=2, base_delay=0.01, retryable_exceptions=(ValueError,)
        )

        @retry_with_backoff(config=config)
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            failing_func()

        assert call_count == 2
        assert exc_info.value.attempts == 2

    def test_config_override_with_individual_params(self):
        """Test individual params override config."""
        call_count = 0
        config = RetryConfig(max_attempts=5, base_delay=0.01)

        # max_attempts=2 should override config's max_attempts=5
        @retry_with_backoff(
            config=config, max_attempts=2, retryable_exceptions=[ValueError]
        )
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        assert call_count == 2  # Uses overridden value, not config's 5

    def test_preserves_function_metadata(self):
        """Test decorator preserves function name and docstring."""

        @retry_with_backoff()
        def my_function():
            """My docstring."""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_passes_args_and_kwargs(self):
        """Test decorator passes arguments correctly."""

        @retry_with_backoff()
        def add(a, b, multiplier=1):
            return (a + b) * multiplier

        assert add(2, 3) == 5
        assert add(2, 3, multiplier=2) == 10

    def test_single_attempt_max(self):
        """Test with max_attempts=1 (no retries)."""
        call_count = 0

        @retry_with_backoff(max_attempts=1, retryable_exceptions=[ValueError])
        def single_try():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            single_try()

        assert call_count == 1

    @patch("plugin.lib.retry.time.sleep")
    def test_delay_is_applied_between_retries(self, mock_sleep):
        """Test delay is applied between retry attempts."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=1.0,
            retryable_exceptions=[ValueError],
        )
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        # Sleep should be called between attempts (2 times for 3 attempts)
        # Note: last attempt doesn't sleep after failure
        assert mock_sleep.call_count == 2

    @patch("plugin.lib.retry.time.sleep")
    def test_no_delay_after_final_attempt(self, mock_sleep):
        """Test no delay after final attempt fails."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=2,
            base_delay=1.0,
            retryable_exceptions=[ValueError],
        )
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        # Only 1 sleep (after first attempt, before second)
        assert mock_sleep.call_count == 1

    @patch("plugin.lib.retry.logger")
    def test_logging_on_retry(self, mock_logger):
        """Test warning is logged on retry."""

        @retry_with_backoff(
            max_attempts=2, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        def failing_func():
            raise ValueError("Test failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        # Check warning was logged
        assert mock_logger.warning.called
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Attempt 1/2" in warning_call
        assert "failing_func" in warning_call
        assert "ValueError" in warning_call

    @patch("plugin.lib.retry.logger")
    def test_logging_on_exhaustion(self, mock_logger):
        """Test error is logged when retries exhausted."""

        @retry_with_backoff(
            max_attempts=2, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        def failing_func():
            raise ValueError("Test failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        # Check error was logged
        assert mock_logger.error.called
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed after 2 attempts" in error_call
        assert "failing_func" in error_call

    @patch("plugin.lib.retry.logger")
    def test_logging_disabled(self, mock_logger):
        """Test logging can be disabled."""
        config = RetryConfig(
            max_attempts=2,
            base_delay=0.01,
            log_attempts=False,
            retryable_exceptions=(ValueError,),
        )

        @retry_with_backoff(config=config)
        def failing_func():
            raise ValueError("Test failure")

        with pytest.raises(RetryExhaustedError):
            failing_func()

        # No logging should occur
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()

    def test_does_not_modify_original_config(self):
        """Test decorator doesn't modify the original config object."""
        config = RetryConfig(max_attempts=3, base_delay=1.0)

        @retry_with_backoff(config=config, max_attempts=5)
        def some_func():
            pass

        # Original config should be unchanged
        assert config.max_attempts == 3


# ==============================================================================
# Test Async Retry Decorator
# ==============================================================================


class TestAsyncRetryWithBackoffDecorator:
    """Tests for async_retry_with_backoff decorator."""

    @pytest.mark.asyncio
    async def test_successful_async_call_no_retry(self):
        """Test successful async call doesn't retry."""
        call_count = 0

        @async_retry_with_backoff(max_attempts=3)
        async def successful_async():
            nonlocal call_count
            call_count += 1
            return "async success"

        result = await successful_async()

        assert result == "async success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_on_retryable_exception(self):
        """Test async retry on retryable exception."""
        call_count = 0

        @async_retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await failing_then_success()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_raises_retry_exhausted(self):
        """Test async raises RetryExhaustedError when all retries fail."""
        call_count = 0

        @async_retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await always_fails()

        assert call_count == 3
        assert exc_info.value.attempts == 3

    @pytest.mark.asyncio
    async def test_async_non_retryable_exception_not_retried(self):
        """Test async non-retryable exception raises immediately."""
        call_count = 0

        @async_retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        async def raises_key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError("Not retryable")

        with pytest.raises(KeyError):
            await raises_key_error()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_decorator_with_config(self):
        """Test async decorator with RetryConfig object."""
        call_count = 0
        config = RetryConfig(
            max_attempts=2, base_delay=0.01, retryable_exceptions=(ValueError,)
        )

        @async_retry_with_backoff(config=config)
        async def failing_async():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            await failing_async()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_preserves_function_metadata(self):
        """Test async decorator preserves function metadata."""

        @async_retry_with_backoff()
        async def my_async_function():
            """My async docstring."""
            pass

        assert my_async_function.__name__ == "my_async_function"
        assert my_async_function.__doc__ == "My async docstring."

    @pytest.mark.asyncio
    async def test_async_passes_args_and_kwargs(self):
        """Test async decorator passes arguments correctly."""

        @async_retry_with_backoff()
        async def async_add(a, b, multiplier=1):
            return (a + b) * multiplier

        result = await async_add(2, 3, multiplier=2)
        assert result == 10

    @pytest.mark.asyncio
    @patch("plugin.lib.retry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_delay_between_retries(self, mock_sleep):
        """Test async delay is applied between retries."""
        call_count = 0

        @async_retry_with_backoff(
            max_attempts=3, base_delay=1.0, retryable_exceptions=[ValueError]
        )
        async def failing_async():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            await failing_async()

        # 2 sleeps for 3 attempts (no sleep after final attempt)
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("plugin.lib.retry.logger")
    async def test_async_logging_on_retry(self, mock_logger):
        """Test async logging on retry."""

        @async_retry_with_backoff(
            max_attempts=2, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        async def failing_async():
            raise ValueError("Test failure")

        with pytest.raises(RetryExhaustedError):
            await failing_async()

        assert mock_logger.warning.called
        assert mock_logger.error.called

    @pytest.mark.asyncio
    async def test_async_config_override(self):
        """Test async config override with individual params."""
        call_count = 0
        config = RetryConfig(max_attempts=5, base_delay=0.01)

        @async_retry_with_backoff(
            config=config, max_attempts=2, retryable_exceptions=[ValueError]
        )
        async def failing_async():
            nonlocal call_count
            call_count += 1
            raise ValueError("Failure")

        with pytest.raises(RetryExhaustedError):
            await failing_async()

        assert call_count == 2


# ==============================================================================
# Test RetryPresets
# ==============================================================================


class TestRetryPresets:
    """Tests for RetryPresets configurations."""

    def test_quick_preset(self):
        """Test QUICK preset configuration."""
        config = RetryPresets.QUICK

        assert config.max_attempts == 3
        assert config.base_delay == 0.5
        assert config.max_delay == 5.0
        assert config.exponential_base == 2.0

    def test_standard_preset(self):
        """Test STANDARD preset configuration."""
        config = RetryPresets.STANDARD

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.exponential_base == 2.0

    def test_aggressive_preset(self):
        """Test AGGRESSIVE preset configuration."""
        config = RetryPresets.AGGRESSIVE

        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0

    def test_conservative_preset(self):
        """Test CONSERVATIVE preset configuration."""
        config = RetryPresets.CONSERVATIVE

        assert config.max_attempts == 3
        assert config.base_delay == 5.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0

    def test_presets_are_valid_configs(self):
        """Test all presets are valid RetryConfig instances."""
        presets = [
            RetryPresets.QUICK,
            RetryPresets.STANDARD,
            RetryPresets.AGGRESSIVE,
            RetryPresets.CONSERVATIVE,
        ]

        for preset in presets:
            assert isinstance(preset, RetryConfig)
            # Validation should have passed during creation
            assert preset.max_attempts >= 1
            assert preset.base_delay >= 0
            assert preset.max_delay >= preset.base_delay

    def test_presets_can_be_used_with_decorator(self):
        """Test presets work with retry decorator."""
        call_count = 0

        @retry_with_backoff(
            config=RetryPresets.QUICK, retryable_exceptions=[ValueError]
        )
        def some_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temp failure")
            return "success"

        result = some_func()
        assert result == "success"
        assert call_count == 2


# ==============================================================================
# Test Custom Exception Types
# ==============================================================================


class TestCustomExceptions:
    """Tests for custom exception types."""

    def test_network_exception(self):
        """Test NetworkException is base exception."""
        error = NetworkException("Network error")
        assert isinstance(error, Exception)
        assert str(error) == "Network error"

    def test_rate_limit_exception_inherits_from_network(self):
        """Test RateLimitException inherits from NetworkException."""
        error = RateLimitException("Rate limited")
        assert isinstance(error, NetworkException)
        assert isinstance(error, Exception)

    def test_api_timeout_exception_inherits_from_network(self):
        """Test APITimeoutException inherits from NetworkException."""
        error = APITimeoutException("Timeout")
        assert isinstance(error, NetworkException)
        assert isinstance(error, Exception)

    def test_api_server_exception_inherits_from_network(self):
        """Test APIServerException inherits from NetworkException."""
        error = APIServerException("Server error")
        assert isinstance(error, NetworkException)
        assert isinstance(error, Exception)

    def test_custom_exceptions_can_be_added_to_retryable(self):
        """Test custom exceptions can be added to retryable exceptions."""
        config = RetryConfig(
            retryable_exceptions=(
                NetworkException,
                RateLimitException,
                APITimeoutException,
                APIServerException,
            )
        )

        assert NetworkException in config.retryable_exceptions
        assert RateLimitException in config.retryable_exceptions
        assert APITimeoutException in config.retryable_exceptions
        assert APIServerException in config.retryable_exceptions

    def test_retry_on_custom_exceptions(self):
        """Test retry decorator works with custom exceptions."""
        call_count = 0

        # Explicitly add RateLimitException to retryable exceptions
        @retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[RateLimitException]
        )
        def raises_rate_limit():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitException("Rate limited")
            return "success"

        result = raises_rate_limit()
        assert result == "success"
        assert call_count == 3


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_first_call_succeeds(self):
        """Test first call success doesn't waste retries."""
        call_count = 0

        @retry_with_backoff(max_attempts=5, base_delay=0.01)
        def immediate_success():
            nonlocal call_count
            call_count += 1
            return "immediate"

        result = immediate_success()
        assert result == "immediate"
        assert call_count == 1

    def test_last_retry_succeeds(self):
        """Test success on last retry attempt."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        def last_chance_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "finally!"

        result = last_chance_success()
        assert result == "finally!"
        assert call_count == 3

    def test_empty_retryable_exceptions_tuple(self):
        """Test with empty retryable_exceptions (nothing is retryable)."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01, retryable_exceptions=[])
        def raises_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Error")

        with pytest.raises(ValueError):
            raises_error()

        # Should only be called once since nothing is retryable
        assert call_count == 1

    def test_very_high_max_attempts(self):
        """Test with high max_attempts count."""
        call_count = 0
        target = 10

        @retry_with_backoff(
            max_attempts=100, base_delay=0.001, retryable_exceptions=[ValueError]
        )
        def succeeds_on_attempt_10():
            nonlocal call_count
            call_count += 1
            if call_count < target:
                raise ValueError("Keep trying")
            return "success"

        result = succeeds_on_attempt_10()
        assert result == "success"
        assert call_count == target

    def test_exception_chaining(self):
        """Test RetryExhaustedError chains from last exception."""

        @retry_with_backoff(
            max_attempts=2, base_delay=0.01, retryable_exceptions=[ConnectionError]
        )
        def always_fails():
            raise ConnectionError("Network down")

        with pytest.raises(RetryExhaustedError) as exc_info:
            always_fails()

        # Check exception chaining
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ConnectionError)

    def test_function_returning_none(self):
        """Test function returning None works correctly."""

        @retry_with_backoff()
        def returns_none():
            return None

        result = returns_none()
        assert result is None

    def test_function_returning_falsy_values(self):
        """Test function returning falsy values works correctly."""

        @retry_with_backoff()
        def returns_zero():
            return 0

        @retry_with_backoff()
        def returns_empty_string():
            return ""

        @retry_with_backoff()
        def returns_empty_list():
            return []

        assert returns_zero() == 0
        assert returns_empty_string() == ""
        assert returns_empty_list() == []

    def test_multiple_exception_types(self):
        """Test retry on multiple exception types."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=5,
            base_delay=0.01,
            retryable_exceptions=[ValueError, KeyError, ConnectionError],
        )
        def raises_different_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First")
            elif call_count == 2:
                raise KeyError("Second")
            elif call_count == 3:
                raise ConnectionError("Third")
            return "success"

        result = raises_different_exceptions()
        assert result == "success"
        assert call_count == 4

    def test_decorator_stacking(self):
        """Test retry decorator can be stacked with other decorators."""

        def logging_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            wrapper.__name__ = func.__name__
            return wrapper

        call_count = 0

        @logging_decorator
        @retry_with_backoff(
            max_attempts=2, base_delay=0.01, retryable_exceptions=[ValueError]
        )
        def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retry me")
            return "success"

        result = decorated_func()
        assert result == "success"
        assert call_count == 2

    def test_instance_method_decoration(self):
        """Test decorator works with instance methods."""

        class MyClass:
            def __init__(self):
                self.call_count = 0

            @retry_with_backoff(
                max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
            )
            def failing_method(self):
                self.call_count += 1
                if self.call_count < 2:
                    raise ValueError("Retry")
                return f"success: {self.call_count}"

        obj = MyClass()
        result = obj.failing_method()
        assert result == "success: 2"
        assert obj.call_count == 2

    def test_class_method_decoration(self):
        """Test decorator works with class methods."""

        class MyClass:
            call_count = 0

            @classmethod
            @retry_with_backoff(
                max_attempts=3, base_delay=0.01, retryable_exceptions=[ValueError]
            )
            def failing_classmethod(cls):
                cls.call_count += 1
                if cls.call_count < 2:
                    raise ValueError("Retry")
                return "class method success"

        result = MyClass.failing_classmethod()
        assert result == "class method success"
        assert MyClass.call_count == 2

    def test_generator_function_not_supported(self):
        """Test that retry decorator with generators returns generator."""
        # Note: generators with retry decorator will behave unexpectedly
        # This test documents current behavior

        @retry_with_backoff()
        def generator_func():
            yield 1
            yield 2
            yield 3

        result = generator_func()
        # The wrapper returns the generator object without issues
        # but retries won't work as expected for iteration failures
        assert hasattr(result, "__iter__")


# ==============================================================================
# Test Real Timing (Integration-style tests)
# ==============================================================================


class TestRealTiming:
    """Tests that verify actual timing behavior (kept short)."""

    def test_actual_delay_applied(self):
        """Test that actual delay is applied between retries."""
        call_count = 0
        call_times = []

        # Use config object to specify jitter=False
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.05,  # 50ms base delay
            jitter=False,
            retryable_exceptions=(ValueError,),
        )

        @retry_with_backoff(config=config)
        def timed_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 3:
                raise ValueError("Retry")
            return "done"

        result = timed_func()

        assert result == "done"
        assert len(call_times) == 3

        # Check delays between calls
        # First retry: ~50ms (0.05s * 2^0)
        delay1 = call_times[1] - call_times[0]
        assert 0.04 <= delay1 <= 0.1, f"First delay {delay1} not in expected range"

        # Second retry: ~100ms (0.05s * 2^1)
        delay2 = call_times[2] - call_times[1]
        assert 0.08 <= delay2 <= 0.2, f"Second delay {delay2} not in expected range"

    @pytest.mark.asyncio
    async def test_async_actual_delay_applied(self):
        """Test that actual async delay is applied between retries."""
        call_count = 0
        call_times = []

        # Use config object to specify jitter=False
        config = RetryConfig(
            max_attempts=2,
            base_delay=0.05,
            jitter=False,
            retryable_exceptions=(ValueError,),
        )

        @async_retry_with_backoff(config=config)
        async def timed_async_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            if call_count < 2:
                raise ValueError("Retry")
            return "done"

        result = await timed_async_func()

        assert result == "done"
        assert len(call_times) == 2

        # Check delay between calls
        delay = call_times[1] - call_times[0]
        assert 0.04 <= delay <= 0.1, f"Delay {delay} not in expected range"


# ==============================================================================
# Test Default Config Changes (at module level)
# ==============================================================================


class TestDefaultConfigChanges:
    """Tests for the default_factory at module level."""

    def test_new_retry_config_has_default_exceptions(self):
        """Test that new RetryConfig instances have default Python exceptions."""
        config = RetryConfig()

        # Default includes basic Python network exceptions
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
        assert OSError in config.retryable_exceptions

        # Custom exceptions are not included by default (must be explicitly added)
        assert NetworkException not in config.retryable_exceptions
        assert RateLimitException not in config.retryable_exceptions

    def test_retry_config_can_extend_defaults(self):
        """Test that custom exceptions can be added alongside defaults."""
        config = RetryConfig(
            retryable_exceptions=(
                # Default types
                ConnectionError,
                TimeoutError,
                OSError,
                # Custom types
                NetworkException,
                RateLimitException,
                APITimeoutException,
                APIServerException,
            )
        )

        # All types should be included
        assert ConnectionError in config.retryable_exceptions
        assert TimeoutError in config.retryable_exceptions
        assert OSError in config.retryable_exceptions
        assert NetworkException in config.retryable_exceptions
        assert RateLimitException in config.retryable_exceptions
        assert APITimeoutException in config.retryable_exceptions
        assert APIServerException in config.retryable_exceptions
