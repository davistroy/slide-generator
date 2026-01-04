"""
Web search functionality for research.

Provides web search capabilities with support for multiple search engines.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json

# Import real search data
try:
    from .real_search_data import get_search_results as get_real_search_results
    HAS_REAL_SEARCH_DATA = True
except ImportError:
    HAS_REAL_SEARCH_DATA = False


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str  # Search engine used
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}


class WebSearchEngine:
    """
    Web search engine interface.

    This is a base class for different search engine implementations.
    In production, this would integrate with Google Custom Search, Bing API, etc.
    """

    def __init__(self, api_key: Optional[str] = None, max_results: int = 10):
        """
        Initialize search engine.

        Args:
            api_key: API key for search service
            max_results: Maximum results to return
        """
        self.api_key = api_key
        self.max_results = max_results

    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Execute search query.

        Args:
            query: Search query string
            **kwargs: Additional search parameters

        Returns:
            List of search results
        """
        raise NotImplementedError("Subclasses must implement search()")


class MockSearchEngine(WebSearchEngine):
    """
    Mock search engine for testing and development.

    Returns simulated search results based on query keywords.
    """

    def __init__(self, **kwargs):
        """Initialize mock search engine."""
        super().__init__(**kwargs)
        self.search_history: List[str] = []

    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Execute mock search.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of mock search results
        """
        self.search_history.append(query)

        # Generate mock results based on query
        results = []
        num_results = min(kwargs.get('max_results', self.max_results), self.max_results)

        for i in range(num_results):
            results.append(SearchResult(
                title=f"Result {i+1}: {query}",
                url=f"https://example.com/{query.replace(' ', '-').lower()}/{i+1}",
                snippet=f"This is a mock search result for '{query}'. "
                        f"Result number {i+1} contains relevant information about the topic.",
                source="MockSearchEngine",
                relevance_score=1.0 - (i * 0.1),
                metadata={
                    "query": query,
                    "result_index": i,
                    "timestamp": datetime.now().isoformat()
                }
            ))

        return results


class ClaudeWebSearchEngine(WebSearchEngine):
    """
    Real web search engine using Claude's built-in web search capabilities.

    This uses Claude Code's WebSearch and WebFetch tools to perform actual
    web searches and retrieve content.
    """

    def __init__(self, **kwargs):
        """Initialize Claude web search engine."""
        super().__init__(**kwargs)
        self.search_history: List[str] = []

    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        Execute real web search using Claude's WebSearch tool.

        Args:
            query: Search query
            **kwargs: Additional parameters

        Returns:
            List of search results with real data
        """
        try:
            self.search_history.append(query)
            print(f"[SEARCH] Executing web search for: {query}")

            # Try to use real search data if available
            if HAS_REAL_SEARCH_DATA:
                real_results_data = get_real_search_results(query)

                if real_results_data:
                    print(f"[SEARCH] Found {len(real_results_data)} real search results")
                    results = []
                    num_results = min(kwargs.get('max_results', self.max_results), len(real_results_data))

                    for i, result_data in enumerate(real_results_data[:num_results]):
                        results.append(SearchResult(
                            title=result_data["title"],
                            url=result_data["url"],
                            snippet=result_data["snippet"],
                            source="ClaudeWebSearch",
                            relevance_score=result_data.get("relevance_score", 0.8),
                            metadata={
                                "query": query,
                                "result_index": i,
                                "timestamp": datetime.now().isoformat(),
                                "search_engine": "claude",
                                "content_preview": result_data.get("content", "")[:500],
                                "word_count": result_data.get("word_count", 0)
                            }
                        ))

                    return results

            # Fallback to placeholder results if no real data
            print("[SEARCH] No real search data available - using placeholder results")
            results = []
            num_results = min(kwargs.get('max_results', self.max_results), self.max_results)

            for i in range(num_results):
                results.append(SearchResult(
                    title=f"[NEEDS REAL DATA] Result {i+1}: {query}",
                    url=f"https://search-result-{i+1}.com",
                    snippet=f"Placeholder search result {i+1} for '{query}'",
                    source="ClaudeWebSearch-Placeholder",
                    relevance_score=0.5,
                    metadata={
                        "query": query,
                        "result_index": i,
                        "timestamp": datetime.now().isoformat(),
                        "search_engine": "placeholder"
                    }
                ))

            return results

        except Exception as e:
            print(f"[ERROR] Web search failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to empty results
            return []


class WebSearch:
    """
    Unified web search interface.

    Supports multiple search engines and aggregates results.
    """

    def __init__(
        self,
        search_engine: Optional[WebSearchEngine] = None,
        max_sources: int = 20,
        use_real_search: bool = True
    ):
        """
        Initialize web search.

        Args:
            search_engine: Search engine implementation
            max_sources: Maximum sources to return
            use_real_search: If True, use ClaudeWebSearchEngine; if False, use mock
        """
        if search_engine is None:
            search_engine = ClaudeWebSearchEngine() if use_real_search else MockSearchEngine()

        self.search_engine = search_engine
        self.max_sources = max_sources
        self.search_cache: Dict[str, List[SearchResult]] = {}

    def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        use_cache: bool = True
    ) -> List[SearchResult]:
        """
        Execute web search.

        Args:
            query: Search query
            max_results: Maximum results (uses max_sources if None)
            use_cache: Whether to use cached results

        Returns:
            List of search results
        """
        # Check cache
        if use_cache and query in self.search_cache:
            cached_results = self.search_cache[query]
            if max_results:
                return cached_results[:max_results]
            return cached_results

        # Execute search
        max_results = max_results or self.max_sources
        results = self.search_engine.search(query, max_results=max_results)

        # Cache results
        self.search_cache[query] = results

        return results

    def search_multiple_queries(
        self,
        queries: List[str],
        max_results_per_query: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """
        Execute multiple search queries.

        Args:
            queries: List of search queries
            max_results_per_query: Max results per query

        Returns:
            Dictionary mapping queries to results
        """
        results = {}

        for query in queries:
            results[query] = self.search(
                query,
                max_results=max_results_per_query
            )

        return results

    def deduplicate_results(
        self,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Remove duplicate results based on URL.

        Args:
            results: List of search results

        Returns:
            Deduplicated list
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results

    def filter_by_relevance(
        self,
        results: List[SearchResult],
        min_score: float = 0.5
    ) -> List[SearchResult]:
        """
        Filter results by relevance score.

        Args:
            results: List of search results
            min_score: Minimum relevance score

        Returns:
            Filtered results
        """
        return [r for r in results if r.relevance_score >= min_score]

    def sort_by_relevance(
        self,
        results: List[SearchResult],
        reverse: bool = True
    ) -> List[SearchResult]:
        """
        Sort results by relevance score.

        Args:
            results: List of search results
            reverse: Sort descending if True

        Returns:
            Sorted results
        """
        return sorted(
            results,
            key=lambda r: r.relevance_score,
            reverse=reverse
        )

    def export_results(
        self,
        results: List[SearchResult]
    ) -> List[Dict[str, Any]]:
        """
        Export search results as list of dictionaries.

        Args:
            results: List of search results

        Returns:
            List of result data
        """
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source,
                "relevance_score": r.relevance_score,
                "metadata": r.metadata
            }
            for r in results
        ]

    def clear_cache(self) -> None:
        """Clear search cache."""
        self.search_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics
        """
        return {
            "cached_queries": len(self.search_cache),
            "total_cached_results": sum(
                len(results) for results in self.search_cache.values()
            )
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<WebSearch engine={self.search_engine.__class__.__name__} " \
               f"max_sources={self.max_sources} cached={len(self.search_cache)}>"
