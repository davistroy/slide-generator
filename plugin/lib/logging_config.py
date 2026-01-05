"""
Structured logging configuration for the slide-generator plugin.

This module provides:
- Configurable logging setup with console and file handlers
- Color-coded console output for different log levels
- JSON formatted output option for production
- Human-readable format for development

Usage:
    from plugin.lib.logging_config import LogConfig, setup_logging, get_logger

    # Development setup
    config = LogConfig(level="INFO", json_output=False)
    setup_logging(config)

    # Get logger for module
    logger = get_logger(__name__)
    logger.info("Application started")
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ANSI color codes for console output
COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m",       # Reset
}


@dataclass
class LogConfig:
    """
    Configuration for logging setup.

    Attributes:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Custom log format string (optional)
        json_output: Whether to output logs in JSON format
        log_file: Path to log file (optional)
        include_timestamps: Whether to include timestamps in logs
        colored_output: Whether to use colored console output
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
    """

    level: str = "INFO"
    format: Optional[str] = None
    json_output: bool = False
    log_file: Optional[str] = None
    include_timestamps: bool = True
    colored_output: bool = True
    max_bytes: int = 10_485_760  # 10MB
    backup_count: int = 5


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter that adds color to console log output.

    Uses ANSI color codes to color-code different log levels:
    - DEBUG: Cyan
    - INFO: Green
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Magenta
    """

    def __init__(self, fmt: str, datefmt: Optional[str] = None) -> None:
        """
        Initialize the colored formatter.

        Args:
            fmt: Log format string
            datefmt: Date format string
        """
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with color codes.

        Args:
            record: Log record to format

        Returns:
            Formatted and colored log string
        """
        # Get the color for this log level
        color = COLORS.get(record.levelname, COLORS["RESET"])
        reset = COLORS["RESET"]

        # Add color to level name
        original_levelname = record.levelname
        record.levelname = f"{color}{record.levelname}{reset}"

        # Format the record
        result = super().format(record)

        # Restore original level name
        record.levelname = original_levelname

        return result


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs logs as JSON for structured logging.

    Each log entry is a JSON object with fields:
    - timestamp: ISO format timestamp
    - level: Log level name
    - logger: Logger name
    - message: Log message
    - module: Module name
    - function: Function name
    - line: Line number
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName", "relativeCreated",
                "thread", "threadName", "exc_info", "exc_text", "stack_info",
            }:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging(config: LogConfig) -> logging.Logger:
    """
    Setup logging with the specified configuration.

    Configures both console and optional file handlers with appropriate
    formatters. Supports both human-readable colored output for development
    and JSON structured output for production.

    Args:
        config: Logging configuration

    Returns:
        Configured root logger

    Example:
        >>> config = LogConfig(level="DEBUG", json_output=False)
        >>> logger = setup_logging(config)
        >>> logger.info("Application started")
    """
    # Get root logger
    root_logger = logging.getLogger()

    # Set level
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Determine format
    if config.format:
        log_format = config.format
    elif config.json_output:
        log_format = None  # JSON formatter doesn't use format string
    elif config.include_timestamps:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        log_format = "%(name)s - %(levelname)s - %(message)s"

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if config.json_output:
        console_formatter = JSONFormatter()
    elif config.colored_output and sys.stdout.isatty():
        # Only use colors if output is a terminal
        console_formatter = ColoredFormatter(log_format)
    else:
        console_formatter = logging.Formatter(log_format)

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Setup file handler if log file specified
    if config.log_file:
        from logging.handlers import RotatingFileHandler

        # Create log directory if it doesn't exist
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            config.log_file,
            maxBytes=config.max_bytes,
            backupCount=config.backup_count,
        )
        file_handler.setLevel(log_level)

        # Always use JSON format for file output in production
        if config.json_output:
            file_formatter = JSONFormatter()
        else:
            file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            file_formatter = logging.Formatter(file_format)

        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log initial configuration
    root_logger.debug(
        f"Logging configured: level={config.level}, "
        f"json_output={config.json_output}, "
        f"log_file={config.log_file}"
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified name.

    This is a convenience wrapper around logging.getLogger() that ensures
    consistent logger naming across the application.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    return logging.getLogger(name)


def configure_third_party_loggers(level: str = "WARNING") -> None:
    """
    Configure third-party library loggers to reduce noise.

    Sets log level for common third-party libraries to WARNING or higher
    to reduce verbose output during normal operation.

    Args:
        level: Log level to set for third-party loggers

    Example:
        >>> configure_third_party_loggers("WARNING")
    """
    third_party_loggers = [
        "urllib3",
        "httpx",
        "anthropic",
        "google.generativeai",
        "httpcore",
        "requests",
    ]

    log_level = getattr(logging, level.upper(), logging.WARNING)

    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(log_level)
