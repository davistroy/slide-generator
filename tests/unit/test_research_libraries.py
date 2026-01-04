"""
Unit tests for research libraries.

Tests CitationManager, WebSearch, and ContentExtractor.
"""

import pytest
from plugin.lib.citation_manager import CitationManager, Citation
from plugin.lib.web_search import WebSearch, MockSearchEngine, SearchResult
from plugin.lib.content_extractor import ContentExtractor, ExtractedContent


class TestCitation:
    """Tests for Citation dataclass."""

    def test_create_citation(self):
        """Test creating a citation."""
        citation = Citation(
            citation_id="cite-001",
            title="Test Article",
            url="https://example.com/article"
        )

        assert citation.citation_id == "cite-001"
        assert citation.title == "Test Article"
        assert citation.url == "https://example.com/article"
        assert citation.access_date is not None

    def test_citation_with_author(self):
        """Test citation with author."""
        citation = Citation(
            citation_id="cite-001",
            title="Test Article",
            url="https://example.com/article",
            author="John Doe"
        )

        assert citation.author == "John Doe"


class TestCitationManager:
    """Tests for CitationManager."""

    def test_create_citation_manager(self):
        """Test creating citation manager."""
        manager = CitationManager()

        assert manager.default_format == "APA"
        assert len(manager.citations) == 0

    def test_add_citation(self):
        """Test adding a citation."""
        manager = CitationManager()

        citation_id = manager.add_citation(
            title="Test Article",
            url="https://example.com/article",
            author="John Doe"
        )

        assert citation_id == "cite-001"
        assert citation_id in manager.citations

    def test_add_multiple_citations(self):
        """Test adding multiple citations."""
        manager = CitationManager()

        id1 = manager.add_citation("Article 1", "https://example.com/1")
        id2 = manager.add_citation("Article 2", "https://example.com/2")

        assert id1 == "cite-001"
        assert id2 == "cite-002"
        assert len(manager.citations) == 2

    def test_track_usage(self):
        """Test tracking citation usage."""
        manager = CitationManager()
        cid = manager.add_citation("Article", "https://example.com")

        manager.track_usage(cid, slide_number=1, context="Introduction")

        assert len(manager.usage) == 1
        assert manager.usage[0].citation_id == cid
        assert manager.usage[0].slide_number == 1

    def test_track_usage_invalid_citation(self):
        """Test tracking usage with invalid citation."""
        manager = CitationManager()

        with pytest.raises(ValueError, match="not found"):
            manager.track_usage("invalid-id", 1, "context")

    def test_format_citation_apa(self):
        """Test APA citation formatting."""
        manager = CitationManager(default_format="APA")
        cid = manager.add_citation(
            title="Test Article",
            url="https://example.com",
            author="Smith, J.",
            publication_date="2024"
        )

        formatted = manager.format_citation(cid)

        assert "Smith, J." in formatted
        assert "(2024)" in formatted
        assert "*Test Article*" in formatted
        assert "https://example.com" in formatted

    def test_format_citation_mla(self):
        """Test MLA citation formatting."""
        manager = CitationManager(default_format="MLA")
        cid = manager.add_citation(
            title="Test Article",
            url="https://example.com",
            author="Smith, John"
        )

        formatted = manager.format_citation(cid, style="MLA")

        assert "Smith, John" in formatted
        assert '"Test Article."' in formatted
        assert "https://example.com" in formatted

    def test_format_citation_chicago(self):
        """Test Chicago citation formatting."""
        manager = CitationManager()
        cid = manager.add_citation(
            title="Test Article",
            url="https://example.com",
            author="Smith"
        )

        formatted = manager.format_citation(cid, style="Chicago")

        assert "Smith" in formatted
        assert '"Test Article."' in formatted

    def test_format_citation_invalid_id(self):
        """Test formatting with invalid citation ID."""
        manager = CitationManager()

        with pytest.raises(ValueError, match="not found"):
            manager.format_citation("invalid-id")

    def test_format_citation_invalid_style(self):
        """Test formatting with invalid style."""
        manager = CitationManager()
        cid = manager.add_citation("Article", "https://example.com")

        with pytest.raises(ValueError, match="Unknown citation style"):
            manager.format_citation(cid, style="INVALID")

    def test_generate_bibliography(self):
        """Test generating bibliography."""
        manager = CitationManager()
        manager.add_citation("Article 1", "https://example.com/1")
        manager.add_citation("Article 2", "https://example.com/2")

        bibliography = manager.generate_bibliography()

        assert "## References" in bibliography
        assert "Article 1" in bibliography
        assert "Article 2" in bibliography

    def test_generate_bibliography_filtered(self):
        """Test generating filtered bibliography."""
        manager = CitationManager()
        cid1 = manager.add_citation("Article 1", "https://example.com/1")
        manager.add_citation("Article 2", "https://example.com/2")

        bibliography = manager.generate_bibliography([cid1])

        assert "Article 1" in bibliography
        assert "Article 2" not in bibliography

    def test_get_citation_usage(self):
        """Test getting citation usage."""
        manager = CitationManager()
        cid = manager.add_citation("Article", "https://example.com")
        manager.track_usage(cid, 1, "context1")
        manager.track_usage(cid, 2, "context2")

        usages = manager.get_citation_usage(cid)

        assert len(usages) == 2

    def test_get_slide_citations(self):
        """Test getting citations for a slide."""
        manager = CitationManager()
        cid1 = manager.add_citation("Article 1", "https://example.com/1")
        cid2 = manager.add_citation("Article 2", "https://example.com/2")
        manager.track_usage(cid1, 1, "context")
        manager.track_usage(cid2, 1, "context")
        manager.track_usage(cid1, 2, "context")

        slide1_citations = manager.get_slide_citations(1)

        assert len(slide1_citations) == 2
        assert cid1 in slide1_citations
        assert cid2 in slide1_citations

    def test_validate_citations(self):
        """Test citation validation."""
        manager = CitationManager()
        manager.add_citation("", "https://example.com")  # Missing title
        manager.add_citation("Article", "")  # Missing URL
        manager.add_citation("Article", "invalid-url")  # Invalid URL

        issues = manager.validate_citations()

        assert len(issues) >= 3

    def test_export_citations(self):
        """Test exporting citations."""
        manager = CitationManager()
        manager.add_citation("Article", "https://example.com")

        exported = manager.export_citations()

        assert len(exported) == 1
        assert exported[0]["title"] == "Article"

    def test_import_citations(self):
        """Test importing citations."""
        manager = CitationManager()
        citations_data = [
            {
                "id": "cite-001",
                "title": "Article",
                "url": "https://example.com"
            }
        ]

        manager.import_citations(citations_data)

        assert len(manager.citations) == 1
        assert "cite-001" in manager.citations


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            title="Test Result",
            url="https://example.com",
            snippet="Test snippet",
            source="TestEngine",
            relevance_score=0.95
        )

        assert result.title == "Test Result"
        assert result.relevance_score == 0.95
        assert result.metadata is not None


class TestMockSearchEngine:
    """Tests for MockSearchEngine."""

    def test_create_mock_engine(self):
        """Test creating mock search engine."""
        engine = MockSearchEngine(max_results=5)

        assert engine.max_results == 5
        assert len(engine.search_history) == 0

    def test_mock_search(self):
        """Test mock search execution."""
        engine = MockSearchEngine()

        results = engine.search("test query")

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_mock_search_history(self):
        """Test search history tracking."""
        engine = MockSearchEngine()

        engine.search("query 1")
        engine.search("query 2")

        assert len(engine.search_history) == 2
        assert "query 1" in engine.search_history


class TestWebSearch:
    """Tests for WebSearch."""

    def test_create_web_search(self):
        """Test creating web search."""
        search = WebSearch()

        assert search.search_engine is not None
        assert search.max_sources == 20

    def test_search(self):
        """Test executing search."""
        search = WebSearch()

        results = search.search("test query", max_results=5)

        assert len(results) == 5
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_caching(self):
        """Test search result caching."""
        search = WebSearch()

        # First search
        results1 = search.search("test query")

        # Second search (should use cache)
        results2 = search.search("test query", use_cache=True)

        assert results1 == results2

    def test_search_no_cache(self):
        """Test search without caching."""
        search = WebSearch()

        search.search("test query", use_cache=True)
        search.search("test query", use_cache=False)

        # Cache should still have results
        assert len(search.search_cache) > 0

    def test_search_multiple_queries(self):
        """Test searching multiple queries."""
        search = WebSearch()

        results = search.search_multiple_queries(["query1", "query2"], max_results_per_query=3)

        assert len(results) == 2
        assert "query1" in results
        assert "query2" in results
        assert len(results["query1"]) == 3

    def test_deduplicate_results(self):
        """Test result deduplication."""
        search = WebSearch()

        results = [
            SearchResult("Title", "https://example.com", "snippet1", "source"),
            SearchResult("Title", "https://example.com", "snippet2", "source"),  # Duplicate
            SearchResult("Title", "https://example.com/other", "snippet", "source")
        ]

        unique = search.deduplicate_results(results)

        assert len(unique) == 2

    def test_filter_by_relevance(self):
        """Test filtering by relevance score."""
        search = WebSearch()

        results = [
            SearchResult("A", "https://a.com", "snippet", "source", relevance_score=0.9),
            SearchResult("B", "https://b.com", "snippet", "source", relevance_score=0.4),
            SearchResult("C", "https://c.com", "snippet", "source", relevance_score=0.7)
        ]

        filtered = search.filter_by_relevance(results, min_score=0.5)

        assert len(filtered) == 2

    def test_sort_by_relevance(self):
        """Test sorting by relevance."""
        search = WebSearch()

        results = [
            SearchResult("A", "https://a.com", "snippet", "source", relevance_score=0.5),
            SearchResult("B", "https://b.com", "snippet", "source", relevance_score=0.9),
            SearchResult("C", "https://c.com", "snippet", "source", relevance_score=0.7)
        ]

        sorted_results = search.sort_by_relevance(results)

        assert sorted_results[0].relevance_score == 0.9
        assert sorted_results[2].relevance_score == 0.5

    def test_export_results(self):
        """Test exporting results."""
        search = WebSearch()

        results = [SearchResult("Title", "https://example.com", "snippet", "source")]
        exported = search.export_results(results)

        assert len(exported) == 1
        assert exported[0]["title"] == "Title"

    def test_clear_cache(self):
        """Test clearing cache."""
        search = WebSearch()

        search.search("query")
        assert len(search.search_cache) > 0

        search.clear_cache()
        assert len(search.search_cache) == 0

    def test_get_cache_stats(self):
        """Test getting cache statistics."""
        search = WebSearch()

        search.search("query1")
        search.search("query2")

        stats = search.get_cache_stats()

        assert stats["cached_queries"] == 2
        assert stats["total_cached_results"] > 0


class TestExtractedContent:
    """Tests for ExtractedContent dataclass."""

    def test_create_extracted_content(self):
        """Test creating extracted content."""
        content = ExtractedContent(
            url="https://example.com",
            title="Test Article",
            content="Test content"
        )

        assert content.url == "https://example.com"
        assert content.word_count > 0
        assert content.metadata is not None


class TestContentExtractor:
    """Tests for ContentExtractor."""

    def test_create_content_extractor(self):
        """Test creating content extractor."""
        extractor = ContentExtractor()

        assert extractor.min_content_length == 100

    def test_extract_mock_content(self):
        """Test extracting mock content."""
        extractor = ContentExtractor()

        content = extractor.extract("https://example.com/article")

        assert content.url == "https://example.com/article"
        assert content.title is not None
        assert content.content is not None
        assert content.metadata.get("mock") is True

    def test_extract_from_html(self):
        """Test extracting from HTML."""
        extractor = ContentExtractor()

        html = """
        <html>
            <head><title>Test Article</title></head>
            <body><p>This is the article content.</p></body>
        </html>
        """

        content = extractor.extract("https://example.com", html_content=html)

        assert content.title == "Test Article"
        assert "article content" in content.content

    def test_extract_with_author(self):
        """Test extracting content with author."""
        extractor = ContentExtractor()

        html = """
        <html>
            <head>
                <title>Test Article</title>
                <meta name="author" content="John Doe">
            </head>
            <body><p>Content</p></body>
        </html>
        """

        content = extractor.extract("https://example.com", html_content=html)

        assert content.author == "John Doe"

    def test_summarize(self):
        """Test content summarization."""
        extractor = ContentExtractor()

        content = "First sentence. Second sentence. Third sentence. Fourth sentence."
        summary = extractor.summarize(content, max_sentences=2)

        assert "First sentence" in summary
        assert "Second sentence" in summary
        assert "Fourth sentence" not in summary

    def test_extract_keywords(self):
        """Test keyword extraction."""
        extractor = ContentExtractor()

        content = "Python programming language is great. Python is popular. Programming is fun."
        keywords = extractor.extract_keywords(content, top_n=2)

        assert "python" in keywords or "programming" in keywords

    def test_validate_content(self):
        """Test content validation."""
        extractor = ContentExtractor()

        # Valid content (>100 chars)
        valid_content = ExtractedContent(
            url="https://example.com",
            title="Article",
            content="This is a long enough article content that meets the minimum requirements. "
                    "It has sufficient length to pass validation checks."
        )
        issues = extractor.validate_content(valid_content)
        assert len(issues) == 0

        # Invalid content (too short)
        invalid_content = ExtractedContent(
            url="https://example.com",
            title="Article",
            content="Short"
        )
        issues = extractor.validate_content(invalid_content)
        assert len(issues) > 0
