"""
Library modules for the presentation generation plugin.

This package contains core libraries for:
- API clients (Claude, Gemini)
- Async API clients (AsyncClaudeClient, AsyncGeminiClient)
- Connection pooling for async HTTP
- Async workflow execution utilities
- Web search and content extraction
- Citation management
- Content generation and quality analysis
- Graphics validation
- Logging and metrics collection
- Progress reporting
- Security (validation, rate limiting, retry logic)

Type Support:
    This package is PEP 561 compliant with type annotations.
"""

from .citation_manager import Citation, CitationManager
from .claude_client import ClaudeClient, get_claude_client
from .content_extractor import ContentExtractor, ExtractedContent
from .logging_config import LogConfig, get_logger, setup_logging
from .metrics import (
    Counter,
    Gauge,
    Histogram,
    MetricsCollector,
    get_metrics_collector,
)
from .progress import (
    ProgressReporter,
    SilentProgressReporter,
    Task,
    create_progress_reporter,
)
from .rate_limiter import (
    APIRateLimiter,
    RateLimitConfig,
    RateLimiter,
    get_global_rate_limiter,
)
from .retry import (
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
from .secure_config import (
    EnvironmentConfig,
    SecureConfigLoader,
    get_global_config_loader,
    load_api_key,
    load_skill_config,
)
from .structured_logger import (
    LogContext,
    StructuredLogger,
    get_structured_logger,
)
from .validators import Validators
from .web_search import MockSearchEngine, SearchResult, WebSearch, WebSearchEngine

# Async modules
from .async_claude_client import AsyncClaudeClient, get_async_claude_client
from .async_gemini_client import AsyncGeminiClient, get_async_gemini_client
from .connection_pool import ConnectionPool, ConnectionPoolStats, create_connection_pool
from .async_workflow import (
    AsyncWorkflowExecutor,
    TaskResult,
    WorkflowResult,
    run_parallel,
    run_sequential,
    run_batched,
)

__all__ = [
    # Sync API Clients
    "ClaudeClient",
    "get_claude_client",
    # Async API Clients
    "AsyncClaudeClient",
    "get_async_claude_client",
    "AsyncGeminiClient",
    "get_async_gemini_client",
    # Connection Pooling
    "ConnectionPool",
    "ConnectionPoolStats",
    "create_connection_pool",
    # Async Workflow
    "AsyncWorkflowExecutor",
    "TaskResult",
    "WorkflowResult",
    "run_parallel",
    "run_sequential",
    "run_batched",
    # Citation Management
    "CitationManager",
    "Citation",
    # Web Search
    "WebSearch",
    "WebSearchEngine",
    "MockSearchEngine",
    "SearchResult",
    # Content Extraction
    "ContentExtractor",
    "ExtractedContent",
    # Logging
    "LogConfig",
    "setup_logging",
    "get_logger",
    "StructuredLogger",
    "LogContext",
    "get_structured_logger",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    "Counter",
    "Gauge",
    "Histogram",
    # Progress
    "ProgressReporter",
    "SilentProgressReporter",
    "Task",
    "create_progress_reporter",
    # Validation
    "Validators",
    # Retry Logic
    "RetryConfig",
    "RetryPresets",
    "RetryExhaustedError",
    "retry_with_backoff",
    "async_retry_with_backoff",
    "NetworkException",
    "RateLimitException",
    "APITimeoutException",
    "APIServerException",
    # Rate Limiting
    "RateLimiter",
    "RateLimitConfig",
    "APIRateLimiter",
    "get_global_rate_limiter",
    # Secure Configuration
    "SecureConfigLoader",
    "EnvironmentConfig",
    "get_global_config_loader",
    "load_api_key",
    "load_skill_config",
]
