"""
JSON structured logging with context management and sensitive field masking.

This module provides:
- StructuredLogger class for JSON-formatted logging
- Automatic request_id, timestamp, module, and function tracking
- Sensitive field masking for security
- LogContext context manager for temporary context fields
- Correlation ID support for tracking requests across components

Usage:
    from plugin.lib.structured_logger import StructuredLogger, LogContext

    logger = StructuredLogger(__name__)
    logger.info("User logged in", user_id=123, action="login")

    # Add temporary context
    with LogContext(logger, request_id="abc-123"):
        logger.info("Processing request")
"""

from __future__ import annotations

import contextvars
import logging
import re
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional, Set

# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)

# Context variable for additional context fields
context_fields_var: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "context_fields", default={}
)


class StructuredLogger:
    """
    Logger that outputs structured JSON logs with context and field masking.

    Wraps the standard logging module to provide:
    - Automatic addition of request_id, timestamp, module, function
    - Sensitive field masking (api_key, password, token patterns)
    - Context management for temporary fields
    - Correlation ID support

    Attributes:
        name: Logger name
        logger: Underlying Python logger
        sensitive_patterns: Regex patterns for sensitive field names
        mask_string: String to use for masked values
    """

    # Default sensitive field patterns
    DEFAULT_SENSITIVE_PATTERNS = [
        r".*api[_-]?key.*",
        r".*password.*",
        r".*token.*",
        r".*secret.*",
        r".*auth.*",
        r".*credential.*",
    ]

    def __init__(
        self,
        name: str,
        sensitive_patterns: Optional[List[str]] = None,
        mask_string: str = "***MASKED***",
    ) -> None:
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__)
            sensitive_patterns: List of regex patterns for sensitive field names
            mask_string: String to use for masked values
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.mask_string = mask_string

        # Compile sensitive patterns
        patterns = sensitive_patterns or self.DEFAULT_SENSITIVE_PATTERNS
        self.sensitive_patterns: List[re.Pattern] = [
            re.compile(pattern, re.IGNORECASE) for pattern in patterns
        ]

    def _generate_request_id(self) -> str:
        """
        Generate a unique request ID.

        Returns:
            UUID-based request ID
        """
        return str(uuid.uuid4())

    def _mask_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask sensitive fields in the data dictionary.

        Recursively processes dictionaries and lists to mask any fields
        matching sensitive patterns.

        Args:
            data: Dictionary to mask

        Returns:
            Dictionary with sensitive fields masked
        """
        masked_data = {}

        for key, value in data.items():
            # Check if key matches any sensitive pattern
            is_sensitive = any(
                pattern.match(key) for pattern in self.sensitive_patterns
            )

            if is_sensitive:
                masked_data[key] = self.mask_string
            elif isinstance(value, dict):
                masked_data[key] = self._mask_sensitive_fields(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self._mask_sensitive_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked_data[key] = value

        return masked_data

    def _build_log_data(
        self, message: str, level: str, **context: Any
    ) -> Dict[str, Any]:
        """
        Build structured log data with automatic fields.

        Args:
            message: Log message
            level: Log level
            **context: Additional context fields

        Returns:
            Dictionary with complete log data
        """
        import inspect

        # Get caller information
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame and frame.f_back else None

        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
        }

        # Add caller information if available
        if caller_frame:
            log_data.update({
                "module": caller_frame.f_globals.get("__name__", "unknown"),
                "function": caller_frame.f_code.co_name,
                "line": caller_frame.f_lineno,
            })

        # Add correlation ID if set
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add context fields from context var
        context_fields = context_fields_var.get()
        if context_fields:
            log_data.update(context_fields)

        # Add additional context from call
        if context:
            # Mask sensitive fields
            masked_context = self._mask_sensitive_fields(context)
            log_data.update(masked_context)

        return log_data

    def debug(self, message: str, **context: Any) -> None:
        """
        Log a debug message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        if self.logger.isEnabledFor(logging.DEBUG):
            log_data = self._build_log_data(message, "DEBUG", **context)
            self.logger.debug(message, extra={"log_data": log_data})

    def info(self, message: str, **context: Any) -> None:
        """
        Log an info message with context.

        Args:
            message: Log message
            **context: Additional context fields

        Example:
            >>> logger.info("User logged in", user_id=123, action="login")
        """
        if self.logger.isEnabledFor(logging.INFO):
            log_data = self._build_log_data(message, "INFO", **context)
            self.logger.info(message, extra={"log_data": log_data})

    def warning(self, message: str, **context: Any) -> None:
        """
        Log a warning message with context.

        Args:
            message: Log message
            **context: Additional context fields

        Example:
            >>> logger.warning("Rate limit approaching", remaining=10, limit=100)
        """
        if self.logger.isEnabledFor(logging.WARNING):
            log_data = self._build_log_data(message, "WARNING", **context)
            self.logger.warning(message, extra={"log_data": log_data})

    def error(self, message: str, **context: Any) -> None:
        """
        Log an error message with context.

        Args:
            message: Log message
            **context: Additional context fields

        Example:
            >>> logger.error("API call failed", error=str(e), retry_count=3)
        """
        if self.logger.isEnabledFor(logging.ERROR):
            log_data = self._build_log_data(message, "ERROR", **context)
            self.logger.error(message, extra={"log_data": log_data})

    def critical(self, message: str, **context: Any) -> None:
        """
        Log a critical message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        if self.logger.isEnabledFor(logging.CRITICAL):
            log_data = self._build_log_data(message, "CRITICAL", **context)
            self.logger.critical(message, extra={"log_data": log_data})

    def exception(self, message: str, **context: Any) -> None:
        """
        Log an exception with traceback.

        Should be called from an exception handler.

        Args:
            message: Log message
            **context: Additional context fields

        Example:
            >>> try:
            ...     raise ValueError("Bad value")
            ... except Exception:
            ...     logger.exception("Error processing data", record_id=123)
        """
        if self.logger.isEnabledFor(logging.ERROR):
            log_data = self._build_log_data(message, "ERROR", **context)
            self.logger.exception(message, extra={"log_data": log_data})

    @contextmanager
    def context(self, **fields: Any) -> Generator[None, None, None]:
        """
        Context manager for adding temporary context fields.

        All log calls within this context will include the specified fields.

        Args:
            **fields: Context fields to add

        Yields:
            None

        Example:
            >>> with logger.context(request_id="abc-123", user_id=456):
            ...     logger.info("Processing request")
            ...     logger.info("Request complete")
        """
        # Get current context fields
        current_fields = context_fields_var.get().copy()

        # Add new fields
        new_fields = current_fields.copy()
        new_fields.update(fields)

        # Set context
        token = context_fields_var.set(new_fields)

        try:
            yield
        finally:
            # Restore previous context
            context_fields_var.reset(token)

    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """
        Set correlation ID for tracking requests.

        Args:
            correlation_id: Correlation ID to set (generates if None)

        Returns:
            The correlation ID that was set

        Example:
            >>> correlation_id = logger.set_correlation_id()
            >>> logger.info("Starting workflow")
        """
        if correlation_id is None:
            correlation_id = self._generate_request_id()

        correlation_id_var.set(correlation_id)
        return correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """
        Get current correlation ID.

        Returns:
            Current correlation ID or None
        """
        return correlation_id_var.get()

    def clear_correlation_id(self) -> None:
        """
        Clear the current correlation ID.
        """
        correlation_id_var.set(None)


@contextmanager
def LogContext(
    logger: StructuredLogger, **fields: Any
) -> Generator[None, None, None]:
    """
    Context manager for adding temporary context fields to a logger.

    This is a convenience wrapper around logger.context().

    Args:
        logger: StructuredLogger instance
        **fields: Context fields to add

    Yields:
        None

    Example:
        >>> logger = StructuredLogger(__name__)
        >>> with LogContext(logger, request_id="abc-123"):
        ...     logger.info("Processing request")
    """
    with logger.context(**fields):
        yield


def get_structured_logger(
    name: str,
    sensitive_patterns: Optional[List[str]] = None,
    mask_string: str = "***MASKED***",
) -> StructuredLogger:
    """
    Get or create a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        sensitive_patterns: List of regex patterns for sensitive field names
        mask_string: String to use for masked values

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_structured_logger(__name__)
        >>> logger.info("Application started")
    """
    return StructuredLogger(
        name=name,
        sensitive_patterns=sensitive_patterns,
        mask_string=mask_string,
    )
