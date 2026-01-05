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

# Async modules
from .async_claude_client import AsyncClaudeClient, get_async_claude_client
from .async_gemini_client import AsyncGeminiClient, get_async_gemini_client
from .async_workflow import (
    AsyncWorkflowExecutor,
    TaskResult,
    WorkflowResult,
    run_batched,
    run_parallel,
    run_sequential,
)
from .citation_manager import Citation, CitationManager
from .claude_client import ClaudeClient, get_claude_client
from .connection_pool import ConnectionPool, ConnectionPoolStats, create_connection_pool
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


__all__ = [
    "APIRateLimiter",
    "APIServerException",
    "APITimeoutException",
    # Async API Clients
    "AsyncClaudeClient",
    "AsyncGeminiClient",
    # Async Workflow
    "AsyncWorkflowExecutor",
    "Citation",
    # Citation Management
    "CitationManager",
    # Sync API Clients
    "ClaudeClient",
    # Connection Pooling
    "ConnectionPool",
    "ConnectionPoolStats",
    # Content Extraction
    "ContentExtractor",
    "Counter",
    "EnvironmentConfig",
    "ExtractedContent",
    "Gauge",
    "Histogram",
    # Logging
    "LogConfig",
    "LogContext",
    # Metrics
    "MetricsCollector",
    "MockSearchEngine",
    "NetworkException",
    # Progress
    "ProgressReporter",
    "RateLimitConfig",
    "RateLimitException",
    # Rate Limiting
    "RateLimiter",
    # Retry Logic
    "RetryConfig",
    "RetryExhaustedError",
    "RetryPresets",
    "SearchResult",
    # Secure Configuration
    "SecureConfigLoader",
    "SilentProgressReporter",
    "StructuredLogger",
    "Task",
    "TaskResult",
    # Validation
    "Validators",
    # Web Search
    "WebSearch",
    "WebSearchEngine",
    "WorkflowResult",
    "async_retry_with_backoff",
    "create_connection_pool",
    "create_progress_reporter",
    "get_async_claude_client",
    "get_async_gemini_client",
    "get_claude_client",
    "get_global_config_loader",
    "get_global_rate_limiter",
    "get_logger",
    "get_metrics_collector",
    "get_structured_logger",
    "load_api_key",
    "load_skill_config",
    "retry_with_backoff",
    "run_batched",
    "run_parallel",
    "run_sequential",
    "setup_logging",
]
