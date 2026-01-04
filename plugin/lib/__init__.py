"""
Library modules for the presentation generation plugin.
"""

from .citation_manager import CitationManager, Citation
from .web_search import WebSearch, WebSearchEngine, MockSearchEngine, SearchResult
from .content_extractor import ContentExtractor, ExtractedContent

__all__ = [
    "CitationManager",
    "Citation",
    "WebSearch",
    "WebSearchEngine",
    "MockSearchEngine",
    "SearchResult",
    "ContentExtractor",
    "ExtractedContent"
]
