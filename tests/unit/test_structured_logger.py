"""
Unit tests for structured_logger module.

Tests the StructuredLogger class with JSON-formatted logging,
context management, sensitive field masking, and correlation ID support.
"""

import logging
import re
import uuid
from datetime import datetime
from unittest.mock import patch

from plugin.lib.structured_logger import (
    LogContext,
    StructuredLogger,
    context_fields_var,
    correlation_id_var,
    get_structured_logger,
)


# ==============================================================================
# Test StructuredLogger Initialization
# ==============================================================================


class TestStructuredLoggerInit:
    """Tests for StructuredLogger initialization."""

    def test_init_with_name(self):
        """Test logger initialization with name."""
        logger = StructuredLogger("test.module")
        assert logger.name == "test.module"
        assert isinstance(logger.logger, logging.Logger)

    def test_init_with_default_mask_string(self):
        """Test logger uses default mask string."""
        logger = StructuredLogger("test")
        assert logger.mask_string == "***MASKED***"

    def test_init_with_custom_mask_string(self):
        """Test logger with custom mask string."""
        logger = StructuredLogger("test", mask_string="[REDACTED]")
        assert logger.mask_string == "[REDACTED]"

    def test_init_with_default_sensitive_patterns(self):
        """Test logger uses default sensitive patterns."""
        logger = StructuredLogger("test")
        assert len(logger.sensitive_patterns) > 0

        # Verify default patterns are compiled
        for pattern in logger.sensitive_patterns:
            assert isinstance(pattern, re.Pattern)

    def test_init_with_custom_sensitive_patterns(self):
        """Test logger with custom sensitive patterns."""
        custom_patterns = [r".*custom_field.*", r".*private.*"]
        logger = StructuredLogger("test", sensitive_patterns=custom_patterns)

        assert len(logger.sensitive_patterns) == 2

        # Verify custom patterns are compiled
        assert logger.sensitive_patterns[0].match("custom_field_name")
        assert logger.sensitive_patterns[1].match("private_data")

    def test_default_sensitive_patterns_coverage(self):
        """Test that default patterns cover common sensitive fields."""
        logger = StructuredLogger("test")

        sensitive_fields = [
            "api_key",
            "API_KEY",
            "apikey",
            "password",
            "PASSWORD",
            "user_password",
            "token",
            "access_token",
            "auth_token",
            "secret",
            "client_secret",
            "auth",
            "authorization",
            "credential",
            "credentials",
        ]

        for field in sensitive_fields:
            is_sensitive = any(
                pattern.match(field) for pattern in logger.sensitive_patterns
            )
            assert is_sensitive, f"Field '{field}' should be detected as sensitive"


# ==============================================================================
# Test Request ID Generation
# ==============================================================================


class TestRequestIdGeneration:
    """Tests for request ID generation."""

    def test_generate_request_id_returns_uuid(self):
        """Test request ID is a valid UUID."""
        logger = StructuredLogger("test")
        request_id = logger._generate_request_id()

        # Should be valid UUID format
        uuid_obj = uuid.UUID(request_id)
        assert str(uuid_obj) == request_id

    def test_generate_request_id_unique(self):
        """Test that generated request IDs are unique."""
        logger = StructuredLogger("test")

        ids = [logger._generate_request_id() for _ in range(100)]

        # All IDs should be unique
        assert len(set(ids)) == len(ids)


# ==============================================================================
# Test Sensitive Field Masking
# ==============================================================================


class TestSensitiveFieldMasking:
    """Tests for sensitive field masking."""

    def test_mask_simple_sensitive_field(self):
        """Test masking a simple sensitive field."""
        logger = StructuredLogger("test")
        data = {"user": "john", "password": "secret123"}

        masked = logger._mask_sensitive_fields(data)

        assert masked["user"] == "john"
        assert masked["password"] == "***MASKED***"

    def test_mask_multiple_sensitive_fields(self):
        """Test masking multiple sensitive fields."""
        logger = StructuredLogger("test")
        data = {
            "api_key": "key123",
            "token": "tok456",
            "secret": "sec789",
            "username": "john",
        }

        masked = logger._mask_sensitive_fields(data)

        assert masked["api_key"] == "***MASKED***"
        assert masked["token"] == "***MASKED***"
        assert masked["secret"] == "***MASKED***"
        assert masked["username"] == "john"

    def test_mask_nested_sensitive_fields(self):
        """Test masking sensitive fields in nested dictionaries."""
        logger = StructuredLogger("test")
        data = {
            "config": {"api_key": "key123", "timeout": 30},
            "user": "john",
        }

        masked = logger._mask_sensitive_fields(data)

        assert masked["config"]["api_key"] == "***MASKED***"
        assert masked["config"]["timeout"] == 30
        assert masked["user"] == "john"

    def test_mask_sensitive_fields_in_lists(self):
        """Test masking sensitive fields in lists of dictionaries."""
        logger = StructuredLogger("test")
        data = {
            "items": [
                {"name": "service1", "token": "tok1"},
                {"name": "service2", "token": "tok2"},
            ]
        }

        masked = logger._mask_sensitive_fields(data)

        assert masked["items"][0]["name"] == "service1"
        assert masked["items"][0]["token"] == "***MASKED***"
        assert masked["items"][1]["name"] == "service2"
        assert masked["items"][1]["token"] == "***MASKED***"

    def test_mask_preserves_non_dict_list_items(self):
        """Test that non-dict items in lists are preserved."""
        logger = StructuredLogger("test")
        data = {"values": [1, 2, 3, "string", None], "password": "secret"}

        masked = logger._mask_sensitive_fields(data)

        assert masked["values"] == [1, 2, 3, "string", None]
        assert masked["password"] == "***MASKED***"

    def test_mask_with_custom_mask_string(self):
        """Test masking with custom mask string."""
        logger = StructuredLogger("test", mask_string="[HIDDEN]")
        data = {"password": "secret123"}

        masked = logger._mask_sensitive_fields(data)

        assert masked["password"] == "[HIDDEN]"

    def test_mask_empty_dict(self):
        """Test masking empty dictionary."""
        logger = StructuredLogger("test")
        data = {}

        masked = logger._mask_sensitive_fields(data)

        assert masked == {}

    def test_mask_case_insensitive(self):
        """Test that pattern matching is case insensitive."""
        logger = StructuredLogger("test")
        data = {
            "PASSWORD": "secret1",
            "Password": "secret2",
            "password": "secret3",
            "API_KEY": "key1",
            "ApiKey": "key2",
        }

        masked = logger._mask_sensitive_fields(data)

        for key in data:
            assert masked[key] == "***MASKED***", f"Field '{key}' should be masked"

    def test_mask_deeply_nested_structures(self):
        """Test masking deeply nested structures."""
        logger = StructuredLogger("test")
        data = {
            "level1": {
                "level2": {"level3": {"api_key": "deep_secret", "public": "visible"}}
            }
        }

        masked = logger._mask_sensitive_fields(data)

        assert masked["level1"]["level2"]["level3"]["api_key"] == "***MASKED***"
        assert masked["level1"]["level2"]["level3"]["public"] == "visible"


# ==============================================================================
# Test Log Data Building
# ==============================================================================


class TestBuildLogData:
    """Tests for building structured log data."""

    def test_build_log_data_basic(self):
        """Test basic log data building."""
        logger = StructuredLogger("test.module")

        log_data = logger._build_log_data("Test message", "INFO")

        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.module"
        assert "timestamp" in log_data
        assert log_data["timestamp"].endswith("Z")

    def test_build_log_data_with_context(self):
        """Test log data building with context fields."""
        logger = StructuredLogger("test")

        log_data = logger._build_log_data(
            "User action", "INFO", user_id=123, action="login"
        )

        assert log_data["user_id"] == 123
        assert log_data["action"] == "login"

    def test_build_log_data_masks_sensitive_context(self):
        """Test that sensitive context fields are masked."""
        logger = StructuredLogger("test")

        log_data = logger._build_log_data(
            "API call", "INFO", api_key="secret123", endpoint="/users"
        )

        assert log_data["api_key"] == "***MASKED***"
        assert log_data["endpoint"] == "/users"

    def test_build_log_data_includes_caller_info(self):
        """Test that caller information is included."""
        logger = StructuredLogger("test")

        log_data = logger._build_log_data("Test message", "DEBUG")

        # Should have caller info from inspect
        assert "function" in log_data
        assert "line" in log_data
        assert "module" in log_data

    def test_build_log_data_timestamp_format(self):
        """Test timestamp is in ISO format with Z suffix."""
        logger = StructuredLogger("test")

        log_data = logger._build_log_data("Test", "INFO")

        timestamp = log_data["timestamp"]
        assert timestamp.endswith("Z")
        # Should be parseable as ISO format (without Z)
        datetime.fromisoformat(timestamp[:-1])


# ==============================================================================
# Test Correlation ID
# ==============================================================================


class TestCorrelationId:
    """Tests for correlation ID management."""

    def setup_method(self):
        """Clear correlation ID before each test."""
        correlation_id_var.set(None)

    def teardown_method(self):
        """Clear correlation ID after each test."""
        correlation_id_var.set(None)

    def test_set_correlation_id(self):
        """Test setting correlation ID."""
        logger = StructuredLogger("test")

        result = logger.set_correlation_id("test-correlation-123")

        assert result == "test-correlation-123"
        assert correlation_id_var.get() == "test-correlation-123"

    def test_set_correlation_id_generates_if_none(self):
        """Test that correlation ID is generated if None provided."""
        logger = StructuredLogger("test")

        result = logger.set_correlation_id()

        assert result is not None
        # Should be valid UUID
        uuid.UUID(result)
        assert correlation_id_var.get() == result

    def test_get_correlation_id(self):
        """Test getting correlation ID."""
        logger = StructuredLogger("test")
        correlation_id_var.set("existing-id")

        result = logger.get_correlation_id()

        assert result == "existing-id"

    def test_get_correlation_id_returns_none_when_not_set(self):
        """Test get_correlation_id returns None when not set."""
        logger = StructuredLogger("test")

        result = logger.get_correlation_id()

        assert result is None

    def test_clear_correlation_id(self):
        """Test clearing correlation ID."""
        logger = StructuredLogger("test")
        logger.set_correlation_id("to-be-cleared")

        logger.clear_correlation_id()

        assert correlation_id_var.get() is None

    def test_correlation_id_in_log_data(self):
        """Test that correlation ID is included in log data."""
        logger = StructuredLogger("test")
        logger.set_correlation_id("correlation-123")

        log_data = logger._build_log_data("Test", "INFO")

        assert log_data["correlation_id"] == "correlation-123"

    def test_no_correlation_id_in_log_data_when_not_set(self):
        """Test that correlation_id is not in log data when not set."""
        logger = StructuredLogger("test")

        log_data = logger._build_log_data("Test", "INFO")

        assert "correlation_id" not in log_data


# ==============================================================================
# Test Context Management
# ==============================================================================


class TestContextManagement:
    """Tests for context management."""

    def setup_method(self):
        """Reset context fields before each test."""
        context_fields_var.set({})

    def teardown_method(self):
        """Clear context fields after each test."""
        context_fields_var.set({})

    def test_context_manager_adds_fields(self):
        """Test that context manager adds fields."""
        logger = StructuredLogger("test")

        with logger.context(request_id="req-123", user_id=456):
            fields = context_fields_var.get()
            assert fields["request_id"] == "req-123"
            assert fields["user_id"] == 456

    def test_context_manager_restores_previous_context(self):
        """Test that context is restored after exiting context manager."""
        logger = StructuredLogger("test")
        context_fields_var.set({"original": "value"})

        with logger.context(new_field="new_value"):
            # Inside context
            assert context_fields_var.get()["new_field"] == "new_value"

        # After context - should be restored
        fields = context_fields_var.get()
        assert "new_field" not in fields
        assert fields["original"] == "value"

    def test_nested_context_managers(self):
        """Test nested context managers."""
        logger = StructuredLogger("test")

        with logger.context(outer="outer_value"):
            assert context_fields_var.get()["outer"] == "outer_value"

            with logger.context(inner="inner_value"):
                # Both should be available
                fields = context_fields_var.get()
                assert fields["outer"] == "outer_value"
                assert fields["inner"] == "inner_value"

            # Inner should be removed
            fields = context_fields_var.get()
            assert "inner" not in fields
            assert fields["outer"] == "outer_value"

    def test_context_fields_in_log_data(self):
        """Test that context fields are included in log data."""
        logger = StructuredLogger("test")

        with logger.context(request_id="req-123"):
            log_data = logger._build_log_data("Test", "INFO")
            assert log_data["request_id"] == "req-123"

    def test_context_restores_on_exception(self):
        """Test that context is restored even if exception occurs."""
        logger = StructuredLogger("test")
        context_fields_var.set({"original": "value"})

        try:
            with logger.context(new_field="new_value"):
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Context should be restored
        fields = context_fields_var.get()
        assert "new_field" not in fields
        assert fields["original"] == "value"


# ==============================================================================
# Test Logging Methods
# ==============================================================================


class TestLoggingMethods:
    """Tests for logging methods (debug, info, warning, error, critical)."""

    def test_debug_logs_at_debug_level(self, caplog):
        """Test debug() logs at DEBUG level."""
        logger = StructuredLogger("test.debug")
        logger.logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message", extra_field="value")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "DEBUG"
        assert caplog.records[0].message == "Debug message"

    def test_info_logs_at_info_level(self, caplog):
        """Test info() logs at INFO level."""
        logger = StructuredLogger("test.info")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Info message", user_id=123)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "INFO"
        assert caplog.records[0].message == "Info message"

    def test_warning_logs_at_warning_level(self, caplog):
        """Test warning() logs at WARNING level."""
        logger = StructuredLogger("test.warning")
        logger.logger.setLevel(logging.WARNING)

        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message", limit=100)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert caplog.records[0].message == "Warning message"

    def test_error_logs_at_error_level(self, caplog):
        """Test error() logs at ERROR level."""
        logger = StructuredLogger("test.error")
        logger.logger.setLevel(logging.ERROR)

        with caplog.at_level(logging.ERROR):
            logger.error("Error message", error_code=500)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert caplog.records[0].message == "Error message"

    def test_critical_logs_at_critical_level(self, caplog):
        """Test critical() logs at CRITICAL level."""
        logger = StructuredLogger("test.critical")
        logger.logger.setLevel(logging.CRITICAL)

        with caplog.at_level(logging.CRITICAL):
            logger.critical("Critical message")

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "CRITICAL"
        assert caplog.records[0].message == "Critical message"

    def test_exception_logs_with_traceback(self, caplog):
        """Test exception() logs with traceback."""
        logger = StructuredLogger("test.exception")
        logger.logger.setLevel(logging.ERROR)

        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except ValueError:
                logger.exception("Exception occurred", record_id=123)

        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert caplog.records[0].message == "Exception occurred"
        # Exception info should be attached
        assert caplog.records[0].exc_info is not None

    def test_debug_not_logged_when_level_too_high(self, caplog):
        """Test debug message not logged when level is higher."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")

        # Should not be logged
        debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
        assert len(debug_records) == 0

    def test_log_data_attached_to_record(self, caplog):
        """Test that log_data is attached to log record."""
        logger = StructuredLogger("test.logdata")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Test message", custom_field="custom_value")

        record = caplog.records[0]
        assert hasattr(record, "log_data")
        assert record.log_data["message"] == "Test message"
        assert record.log_data["custom_field"] == "custom_value"


# ==============================================================================
# Test LogContext Function
# ==============================================================================


class TestLogContextFunction:
    """Tests for the LogContext convenience function."""

    def setup_method(self):
        """Reset context fields before each test."""
        context_fields_var.set({})

    def teardown_method(self):
        """Clear context fields after each test."""
        context_fields_var.set({})

    def test_log_context_adds_fields(self):
        """Test LogContext adds fields."""
        logger = StructuredLogger("test")

        with LogContext(logger, request_id="req-123"):
            fields = context_fields_var.get()
            assert fields["request_id"] == "req-123"

    def test_log_context_restores_context(self):
        """Test LogContext restores context after exit."""
        logger = StructuredLogger("test")
        context_fields_var.set({"original": "value"})

        with LogContext(logger, new_field="new"):
            pass

        fields = context_fields_var.get()
        assert "new_field" not in fields
        assert fields["original"] == "value"

    def test_log_context_multiple_fields(self):
        """Test LogContext with multiple fields."""
        logger = StructuredLogger("test")

        with LogContext(logger, field1="val1", field2="val2", field3=123):
            fields = context_fields_var.get()
            assert fields["field1"] == "val1"
            assert fields["field2"] == "val2"
            assert fields["field3"] == 123


# ==============================================================================
# Test get_structured_logger Function
# ==============================================================================


class TestGetStructuredLogger:
    """Tests for get_structured_logger factory function."""

    def test_get_structured_logger_returns_logger(self):
        """Test that get_structured_logger returns a StructuredLogger."""
        logger = get_structured_logger("test.module")

        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test.module"

    def test_get_structured_logger_with_custom_patterns(self):
        """Test get_structured_logger with custom sensitive patterns."""
        custom_patterns = [r".*custom.*"]
        logger = get_structured_logger("test", sensitive_patterns=custom_patterns)

        assert len(logger.sensitive_patterns) == 1
        assert logger.sensitive_patterns[0].match("custom_field")

    def test_get_structured_logger_with_custom_mask(self):
        """Test get_structured_logger with custom mask string."""
        logger = get_structured_logger("test", mask_string="[REDACTED]")

        assert logger.mask_string == "[REDACTED]"

    def test_get_structured_logger_with_all_params(self):
        """Test get_structured_logger with all parameters."""
        logger = get_structured_logger(
            "test.full",
            sensitive_patterns=[r".*private.*"],
            mask_string="[HIDDEN]",
        )

        assert logger.name == "test.full"
        assert logger.mask_string == "[HIDDEN]"
        assert len(logger.sensitive_patterns) == 1


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_message(self, caplog):
        """Test logging empty message."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("")

        assert len(caplog.records) == 1
        assert caplog.records[0].message == ""

    def test_unicode_message(self, caplog):
        """Test logging unicode message."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Unicode message: hello")

        assert len(caplog.records) == 1

    def test_special_characters_in_context(self, caplog):
        """Test special characters in context fields."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Test", special="<>&\"'")

        assert len(caplog.records) == 1

    def test_none_value_in_context(self, caplog):
        """Test None value in context."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Test", nullable=None)

        assert len(caplog.records) == 1
        assert caplog.records[0].log_data["nullable"] is None

    def test_complex_objects_in_context(self, caplog):
        """Test complex objects in context."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        complex_data = {
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "number": 42.5,
        }

        with caplog.at_level(logging.INFO):
            logger.info("Test", data=complex_data)

        assert len(caplog.records) == 1

    def test_very_long_message(self, caplog):
        """Test very long message."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        long_message = "A" * 10000

        with caplog.at_level(logging.INFO):
            logger.info(long_message)

        assert len(caplog.records) == 1
        assert len(caplog.records[0].message) == 10000

    def test_mask_sensitive_field_with_none_value(self):
        """Test masking when sensitive field has None value."""
        logger = StructuredLogger("test")
        data = {"password": None, "user": "john"}

        masked = logger._mask_sensitive_fields(data)

        assert masked["password"] == "***MASKED***"
        assert masked["user"] == "john"

    def test_empty_list_in_mask(self):
        """Test masking data with empty list."""
        logger = StructuredLogger("test")
        data = {"items": [], "password": "secret"}

        masked = logger._mask_sensitive_fields(data)

        assert masked["items"] == []
        assert masked["password"] == "***MASKED***"

    def test_mixed_list_with_dicts_and_primitives(self):
        """Test masking list with mixed content."""
        logger = StructuredLogger("test")
        data = {
            "mixed": [
                {"token": "secret1"},
                "string",
                123,
                {"api_key": "secret2"},
                None,
            ]
        }

        masked = logger._mask_sensitive_fields(data)

        assert masked["mixed"][0]["token"] == "***MASKED***"
        assert masked["mixed"][1] == "string"
        assert masked["mixed"][2] == 123
        assert masked["mixed"][3]["api_key"] == "***MASKED***"
        assert masked["mixed"][4] is None


# ==============================================================================
# Test Log Level Filtering
# ==============================================================================


class TestLogLevelFiltering:
    """Tests for log level filtering behavior."""

    def test_isenabledfor_check(self):
        """Test that isEnabledFor is checked before building log data."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.WARNING)

        # Patch _build_log_data to track calls
        with patch.object(logger, "_build_log_data") as mock_build:
            logger.debug("Should not build")

        # Should not be called since DEBUG < WARNING
        mock_build.assert_not_called()

    def test_info_builds_when_enabled(self):
        """Test that log data is built when level is enabled."""
        logger = StructuredLogger("test")
        logger.logger.setLevel(logging.INFO)

        with patch.object(logger, "_build_log_data", return_value={}) as mock_build:
            with patch.object(logger.logger, "info"):
                logger.info("Should build")

        mock_build.assert_called_once()


# ==============================================================================
# Test Context Variable Isolation
# ==============================================================================


class TestContextVariableIsolation:
    """Tests for context variable isolation between loggers."""

    def setup_method(self):
        """Reset context variables before each test."""
        correlation_id_var.set(None)
        context_fields_var.set({})

    def teardown_method(self):
        """Clear context variables after each test."""
        correlation_id_var.set(None)
        context_fields_var.set({})

    def test_correlation_id_shared_across_loggers(self):
        """Test that correlation ID is shared across logger instances."""
        logger1 = StructuredLogger("test1")
        logger2 = StructuredLogger("test2")

        logger1.set_correlation_id("shared-id")

        assert logger2.get_correlation_id() == "shared-id"

    def test_context_fields_shared_across_loggers(self):
        """Test that context fields are shared across logger instances."""
        logger1 = StructuredLogger("test1")
        logger2 = StructuredLogger("test2")

        with logger1.context(shared_field="shared_value"):
            log_data = logger2._build_log_data("Test", "INFO")
            assert log_data["shared_field"] == "shared_value"

    def test_different_sensitive_patterns_per_logger(self):
        """Test that different loggers can have different sensitive patterns."""
        logger1 = StructuredLogger("test1", sensitive_patterns=[r".*custom1.*"])
        logger2 = StructuredLogger("test2", sensitive_patterns=[r".*custom2.*"])

        data1 = {"custom1_field": "secret", "custom2_field": "visible"}
        data2 = {"custom1_field": "visible", "custom2_field": "secret"}

        masked1 = logger1._mask_sensitive_fields(data1)
        masked2 = logger2._mask_sensitive_fields(data2)

        assert masked1["custom1_field"] == "***MASKED***"
        assert masked1["custom2_field"] == "visible"
        assert masked2["custom1_field"] == "visible"
        assert masked2["custom2_field"] == "***MASKED***"


# ==============================================================================
# Test Integration with Python Logging
# ==============================================================================


class TestPythonLoggingIntegration:
    """Tests for integration with Python's logging module."""

    def test_logger_uses_standard_logger(self):
        """Test that StructuredLogger wraps standard logging.Logger."""
        logger = StructuredLogger("test.integration")

        assert isinstance(logger.logger, logging.Logger)
        assert logger.logger.name == "test.integration"

    def test_logger_respects_handlers(self, tmp_path):
        """Test that StructuredLogger respects configured handlers."""
        log_file = tmp_path / "test.log"

        logger = StructuredLogger("test.handlers")
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.INFO)

        try:
            logger.info("Test file handler")

            # Read file and verify
            with open(log_file) as f:
                content = f.read()
            assert "Test file handler" in content
        finally:
            handler.close()
            logger.logger.removeHandler(handler)

    def test_logger_hierarchy(self):
        """Test that logger hierarchy is respected."""
        StructuredLogger("test")
        child_logger = StructuredLogger("test.child")

        # Child should be a child of parent in logging hierarchy
        assert child_logger.logger.parent.name == "test"
