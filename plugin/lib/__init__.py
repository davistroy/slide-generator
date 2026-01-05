"""
Library modules for the presentation generation plugin.

This package contains core libraries for:
- API clients (Claude, Gemini)
- Web search and content extraction
- Citation management
- Content generation and quality analysis
- Graphics validation

Type Support:
    This package is PEP 561 compliant with type annotations.
"""

from .citation_manager import Citation, CitationManager
from .claude_client import ClaudeClient, get_claude_client
from .content_extractor import ContentExtractor, ExtractedContent
from .web_search import MockSearchEngine, SearchResult, WebSearch, WebSearchEngine

__all__ = [
    # API Clients
    "ClaudeClient",
    "get_claude_client",
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
]
