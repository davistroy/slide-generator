"""
Unit tests for logging configuration module.

Tests the structured logging setup including formatters, handlers,
and configuration options.
"""

import json
import logging
import sys
from unittest.mock import patch

from plugin.lib.logging_config import (
    COLORS,
    ColoredFormatter,
    JSONFormatter,
    LogConfig,
    configure_third_party_loggers,
    get_logger,
    setup_logging,
)


class TestColors:
    """Tests for COLORS constant."""

    def test_all_log_levels_have_colors(self):
        """Test that all standard log levels have color codes."""
        assert "DEBUG" in COLORS
        assert "INFO" in COLORS
        assert "WARNING" in COLORS
        assert "ERROR" in COLORS
        assert "CRITICAL" in COLORS
        assert "RESET" in COLORS

    def test_colors_are_ansi_codes(self):
        """Test that colors are valid ANSI escape codes."""
        for level, color in COLORS.items():
            assert color.startswith("\033["), f"{level} color should be ANSI code"
            assert color.endswith("m"), f"{level} color should end with 'm'"

    def test_reset_color(self):
        """Test reset color is the standard ANSI reset."""
        assert COLORS["RESET"] == "\033[0m"


class TestLogConfig:
    """Tests for LogConfig dataclass."""

    def test_default_values(self):
        """Test LogConfig has correct default values."""
        config = LogConfig()

        assert config.level == "INFO"
        assert config.format is None
        assert config.json_output is False
        assert config.log_file is None
        assert config.include_timestamps is True
        assert config.colored_output is True
        assert config.max_bytes == 10_485_760  # 10MB
        assert config.backup_count == 5

    def test_custom_values(self):
        """Test LogConfig accepts custom values."""
        config = LogConfig(
            level="DEBUG",
            format="%(message)s",
            json_output=True,
            log_file="/var/log/app.log",
            include_timestamps=False,
            colored_output=False,
            max_bytes=5_000_000,
            backup_count=3,
        )

        assert config.level == "DEBUG"
        assert config.format == "%(message)s"
        assert config.json_output is True
        assert config.log_file == "/var/log/app.log"
        assert config.include_timestamps is False
        assert config.colored_output is False
        assert config.max_bytes == 5_000_000
        assert config.backup_count == 3

    def test_partial_custom_values(self):
        """Test LogConfig with partial custom values uses defaults for rest."""
        config = LogConfig(level="WARNING", json_output=True)

        assert config.level == "WARNING"
        assert config.json_output is True
        # Defaults for others
        assert config.format is None
        assert config.log_file is None
        assert config.include_timestamps is True


class TestColoredFormatter:
    """Tests for ColoredFormatter class."""

    def test_initialization(self):
        """Test ColoredFormatter initializes correctly."""
        fmt = "%(levelname)s - %(message)s"
        formatter = ColoredFormatter(fmt)

        assert formatter._fmt == fmt

    def test_initialization_with_datefmt(self):
        """Test ColoredFormatter with custom date format."""
        fmt = "%(asctime)s - %(message)s"
        datefmt = "%Y-%m-%d"
        formatter = ColoredFormatter(fmt, datefmt)

        assert formatter.datefmt == datefmt

    def test_format_debug_level(self):
        """Test DEBUG level is colored cyan."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert COLORS["DEBUG"] in result
        assert COLORS["RESET"] in result
        assert "Test message" in result

    def test_format_info_level(self):
        """Test INFO level is colored green."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Info message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert COLORS["INFO"] in result
        assert COLORS["RESET"] in result

    def test_format_warning_level(self):
        """Test WARNING level is colored yellow."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="Warning message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert COLORS["WARNING"] in result

    def test_format_error_level(self):
        """Test ERROR level is colored red."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert COLORS["ERROR"] in result

    def test_format_critical_level(self):
        """Test CRITICAL level is colored magenta."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.CRITICAL,
            pathname="test.py",
            lineno=1,
            msg="Critical message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert COLORS["CRITICAL"] in result

    def test_format_restores_original_levelname(self):
        """Test that original levelname is restored after formatting."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        original_levelname = record.levelname
        formatter.format(record)

        # Levelname should be restored
        assert record.levelname == original_levelname
        assert COLORS["INFO"] not in record.levelname

    def test_format_unknown_level_uses_reset(self):
        """Test that unknown log level uses RESET color."""
        formatter = ColoredFormatter("%(levelname)s - %(message)s")
        record = logging.LogRecord(
            name="test",
            level=25,  # Custom level between INFO and WARNING
            pathname="test.py",
            lineno=1,
            msg="Custom level message",
            args=(),
            exc_info=None,
        )
        record.levelname = "CUSTOM"

        result = formatter.format(record)

        # Should use RESET color for unknown level
        assert COLORS["RESET"] in result


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_format_basic_record(self):
        """Test formatting a basic log record as JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test_module.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.funcName = "test_function"
        record.module = "test_module"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.module"
        assert data["message"] == "Test message"
        assert data["module"] == "test_module"
        assert data["function"] == "test_function"
        assert data["line"] == 42
        assert "timestamp" in data

    def test_format_with_message_args(self):
        """Test formatting a log record with message arguments."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Hello %s",
            args=("World",),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert data["message"] == "Hello World"

    def test_format_with_exception(self):
        """Test formatting a log record with exception info."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="An error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "Test error" in data["exception"]

    def test_format_with_extra_fields(self):
        """Test formatting includes extra fields from record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )
        # Add custom extra field
        record.request_id = "abc-123"
        record.user_id = 42

        result = formatter.format(record)
        data = json.loads(result)

        assert data["request_id"] == "abc-123"
        assert data["user_id"] == 42

    def test_format_excludes_standard_fields(self):
        """Test that standard LogRecord fields are not duplicated in extras."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        # These should not appear as extra fields
        assert "msg" not in data
        assert "args" not in data
        assert "levelno" not in data
        assert "pathname" not in data
        assert "process" not in data
        assert "thread" not in data

    def test_format_timestamp_is_iso_format(self):
        """Test that timestamp is in ISO format."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        data = json.loads(result)

        # ISO format has 'T' separator between date and time
        assert "T" in data["timestamp"]
        # Should have date portion
        assert "-" in data["timestamp"].split("T")[0]


class TestSetupLogging:
    """Tests for setup_logging function."""

    def teardown_method(self):
        """Clean up loggers after each test."""
        # Reset root logger
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_basic_setup(self):
        """Test basic logging setup."""
        config = LogConfig(level="INFO")
        logger = setup_logging(config)

        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

    def test_setup_with_debug_level(self):
        """Test setup with DEBUG level."""
        config = LogConfig(level="DEBUG")
        logger = setup_logging(config)

        assert logger.level == logging.DEBUG

    def test_setup_with_warning_level(self):
        """Test setup with WARNING level."""
        config = LogConfig(level="WARNING")
        logger = setup_logging(config)

        assert logger.level == logging.WARNING

    def test_setup_with_error_level(self):
        """Test setup with ERROR level."""
        config = LogConfig(level="ERROR")
        logger = setup_logging(config)

        assert logger.level == logging.ERROR

    def test_setup_with_critical_level(self):
        """Test setup with CRITICAL level."""
        config = LogConfig(level="CRITICAL")
        logger = setup_logging(config)

        assert logger.level == logging.CRITICAL

    def test_setup_with_invalid_level_defaults_to_info(self):
        """Test setup with invalid level defaults to INFO."""
        config = LogConfig(level="INVALID")
        logger = setup_logging(config)

        assert logger.level == logging.INFO

    def test_setup_with_lowercase_level(self):
        """Test setup accepts lowercase level names."""
        config = LogConfig(level="debug")
        logger = setup_logging(config)

        assert logger.level == logging.DEBUG

    def test_setup_clears_existing_handlers(self):
        """Test that setup clears existing handlers we add."""
        root = logging.getLogger()
        # Track initial handler count (pytest may add its own handlers)
        initial_count = len(root.handlers)

        # Add custom handlers
        custom1 = logging.StreamHandler()
        custom1.set_name("test_custom_1")
        custom2 = logging.StreamHandler()
        custom2.set_name("test_custom_2")
        root.addHandler(custom1)
        root.addHandler(custom2)

        assert len(root.handlers) == initial_count + 2

        config = LogConfig(level="INFO")
        logger = setup_logging(config)

        # After setup, our custom handlers should be removed
        custom_handlers = [
            h
            for h in logger.handlers
            if (getattr(h, "name", None) or "").startswith("test_custom_")
        ]
        assert len(custom_handlers) == 0

    def test_setup_with_custom_format(self):
        """Test setup with custom format string."""
        custom_format = "%(message)s only"
        config = LogConfig(level="INFO", format=custom_format)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert handler.formatter._fmt == custom_format

    def test_setup_with_json_output(self):
        """Test setup with JSON output format."""
        config = LogConfig(level="INFO", json_output=True)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_with_timestamps(self):
        """Test setup includes timestamps by default."""
        config = LogConfig(level="INFO", include_timestamps=True)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert "%(asctime)s" in handler.formatter._fmt

    def test_setup_without_timestamps(self):
        """Test setup can exclude timestamps."""
        config = LogConfig(level="INFO", include_timestamps=False)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert "%(asctime)s" not in handler.formatter._fmt

    @patch("sys.stdout.isatty", return_value=True)
    def test_setup_with_colored_output_in_tty(self, mock_isatty):
        """Test colored output is used when in TTY."""
        config = LogConfig(level="INFO", colored_output=True)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert isinstance(handler.formatter, ColoredFormatter)

    @patch("sys.stdout.isatty", return_value=False)
    def test_setup_without_tty_uses_plain_formatter(self, mock_isatty):
        """Test plain formatter is used when not in TTY."""
        config = LogConfig(level="INFO", colored_output=True)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        # Should not be ColoredFormatter when not in TTY
        assert not isinstance(handler.formatter, ColoredFormatter)
        assert isinstance(handler.formatter, logging.Formatter)

    def test_setup_with_colored_output_disabled(self):
        """Test colored output can be disabled."""
        config = LogConfig(level="INFO", colored_output=False)
        logger = setup_logging(config)

        handler = logger.handlers[0]
        assert not isinstance(handler.formatter, ColoredFormatter)

    def test_setup_with_log_file(self, tmp_path):
        """Test setup with file logging."""
        log_file = tmp_path / "test.log"
        config = LogConfig(level="INFO", log_file=str(log_file))
        logger = setup_logging(config)

        # Should have 2 handlers (console + file)
        assert len(logger.handlers) == 2

        # Write a log message
        logger.info("Test file logging")

        # Flush handlers
        for handler in logger.handlers:
            handler.flush()

        # Check file was created
        assert log_file.exists()

    def test_setup_creates_log_directory(self, tmp_path):
        """Test setup creates log directory if it doesn't exist."""
        log_dir = tmp_path / "logs" / "subdir"
        log_file = log_dir / "app.log"

        config = LogConfig(level="INFO", log_file=str(log_file))
        setup_logging(config)

        assert log_dir.exists()

    def test_setup_file_handler_with_rotation(self, tmp_path):
        """Test file handler uses rotation settings."""
        log_file = tmp_path / "test.log"
        config = LogConfig(
            level="INFO",
            log_file=str(log_file),
            max_bytes=1024,
            backup_count=3,
        )
        logger = setup_logging(config)

        # Find file handler
        from logging.handlers import RotatingFileHandler

        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                file_handler = handler
                break

        assert file_handler is not None
        assert file_handler.maxBytes == 1024
        assert file_handler.backupCount == 3

    def test_setup_file_handler_with_json(self, tmp_path):
        """Test file handler uses JSON format when enabled."""
        log_file = tmp_path / "test.log"
        config = LogConfig(level="INFO", log_file=str(log_file), json_output=True)
        logger = setup_logging(config)

        # Find file handler
        from logging.handlers import RotatingFileHandler

        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                file_handler = handler
                break

        assert isinstance(file_handler.formatter, JSONFormatter)

    def test_setup_file_handler_with_plain_format(self, tmp_path):
        """Test file handler uses plain format when JSON disabled."""
        log_file = tmp_path / "test.log"
        config = LogConfig(level="INFO", log_file=str(log_file), json_output=False)
        logger = setup_logging(config)

        # Find file handler
        from logging.handlers import RotatingFileHandler

        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                file_handler = handler
                break

        assert not isinstance(file_handler.formatter, JSONFormatter)

    def test_setup_logs_initial_configuration(self, tmp_path, capsys):
        """Test that setup logs initial configuration at DEBUG level."""
        config = LogConfig(level="DEBUG")

        setup_logging(config)

        # The debug message about configuration should be logged to stdout
        captured = capsys.readouterr()
        assert "Logging configured" in captured.out


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test get_logger returns a Logger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"

    def test_get_logger_same_name_returns_same_instance(self):
        """Test same name returns same logger instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")

        assert logger1 is logger2

    def test_get_logger_different_names_return_different_instances(self):
        """Test different names return different logger instances."""
        logger1 = get_logger("test.one")
        logger2 = get_logger("test.two")

        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_get_logger_with_dunder_name(self):
        """Test get_logger with __name__ style input."""
        logger = get_logger(__name__)

        assert logger.name == __name__

    def test_get_logger_hierarchical_names(self):
        """Test loggers with hierarchical names."""
        parent = get_logger("app")
        child = get_logger("app.module")
        grandchild = get_logger("app.module.submodule")

        assert parent.name == "app"
        assert child.name == "app.module"
        assert grandchild.name == "app.module.submodule"


class TestConfigureThirdPartyLoggers:
    """Tests for configure_third_party_loggers function."""

    def teardown_method(self):
        """Reset third-party loggers after each test."""
        for name in [
            "urllib3",
            "httpx",
            "anthropic",
            "google.generativeai",
            "httpcore",
            "requests",
        ]:
            logger = logging.getLogger(name)
            logger.setLevel(logging.NOTSET)

    def test_sets_default_warning_level(self):
        """Test default level is WARNING."""
        configure_third_party_loggers()

        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("anthropic").level == logging.WARNING

    def test_sets_custom_level(self):
        """Test custom level can be set."""
        configure_third_party_loggers("ERROR")

        assert logging.getLogger("urllib3").level == logging.ERROR
        assert logging.getLogger("httpx").level == logging.ERROR

    def test_accepts_lowercase_level(self):
        """Test accepts lowercase level names."""
        configure_third_party_loggers("error")

        assert logging.getLogger("urllib3").level == logging.ERROR

    def test_configures_all_third_party_loggers(self):
        """Test all expected third-party loggers are configured."""
        configure_third_party_loggers("INFO")

        expected_loggers = [
            "urllib3",
            "httpx",
            "anthropic",
            "google.generativeai",
            "httpcore",
            "requests",
        ]

        for name in expected_loggers:
            assert logging.getLogger(name).level == logging.INFO

    def test_invalid_level_defaults_to_warning(self):
        """Test invalid level defaults to WARNING."""
        configure_third_party_loggers("INVALID")

        assert logging.getLogger("urllib3").level == logging.WARNING


class TestIntegration:
    """Integration tests for logging configuration."""

    def teardown_method(self):
        """Clean up loggers after each test."""
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    def test_full_logging_workflow(self, tmp_path):
        """Test complete logging workflow."""
        log_file = tmp_path / "app.log"

        # Setup logging
        config = LogConfig(
            level="DEBUG",
            log_file=str(log_file),
            json_output=False,
            include_timestamps=True,
        )
        root_logger = setup_logging(config)

        # Get module logger
        logger = get_logger("test.integration")

        # Configure third-party loggers
        configure_third_party_loggers("WARNING")

        # Log some messages
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Flush handlers
        for handler in root_logger.handlers:
            handler.flush()

        # Check file content
        content = log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content

    def test_json_logging_workflow(self, tmp_path):
        """Test JSON logging produces valid JSON."""
        log_file = tmp_path / "app.log"

        config = LogConfig(
            level="INFO",
            log_file=str(log_file),
            json_output=True,
        )
        root_logger = setup_logging(config)

        logger = get_logger("test.json")
        logger.info("Test JSON message")

        # Flush handlers
        for handler in root_logger.handlers:
            handler.flush()

        # Each line should be valid JSON
        for line in log_file.read_text().strip().split("\n"):
            if line:
                data = json.loads(line)
                assert "timestamp" in data
                assert "level" in data
                assert "message" in data

    def test_exception_logging(self, tmp_path):
        """Test exception info is captured in logs."""
        log_file = tmp_path / "app.log"

        config = LogConfig(
            level="ERROR",
            log_file=str(log_file),
            json_output=True,
        )
        root_logger = setup_logging(config)

        logger = get_logger("test.exception")

        try:
            raise RuntimeError("Test exception")
        except RuntimeError:
            logger.exception("An error occurred")

        # Flush handlers
        for handler in root_logger.handlers:
            handler.flush()

        content = log_file.read_text()
        data = json.loads(content.strip())

        assert "exception" in data
        assert "RuntimeError" in data["exception"]
        assert "Test exception" in data["exception"]

    def test_multiple_setup_calls_work_correctly(self):
        """Test that calling setup multiple times works correctly."""
        # First setup with DEBUG
        config1 = LogConfig(level="DEBUG")
        logger1 = setup_logging(config1)
        assert logger1.level == logging.DEBUG

        # Second setup with WARNING
        config2 = LogConfig(level="WARNING")
        logger2 = setup_logging(config2)
        assert logger2.level == logging.WARNING

        # Should only have one handler
        assert len(logger2.handlers) == 1

    def test_log_record_with_args(self, capsys):
        """Test log messages with format arguments work correctly."""
        config = LogConfig(level="INFO", json_output=True, colored_output=False)
        setup_logging(config)

        logger = get_logger("test.args")
        logger.info("User %s logged in from %s", "john", "192.168.1.1")

        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())

        assert data["message"] == "User john logged in from 192.168.1.1"
