"""
Content extraction from web pages.

Extracts and cleans text content from URLs.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ExtractedContent:
    """Extracted content from a web page."""
    url: str
    title: str
    content: str
    author: Optional[str] = None
    publication_date: Optional[str] = None
    word_count: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize computed fields."""
        if self.metadata is None:
            self.metadata = {}
        if self.word_count == 0:
            self.word_count = len(self.content.split())


class ContentExtractor:
    """
    Extracts content from web pages.

    This is a simplified version for development. In production, this would
    use libraries like BeautifulSoup, newspaper3k, or readability.
    """

    def __init__(self, min_content_length: int = 100):
        """
        Initialize content extractor.

        Args:
            min_content_length: Minimum content length in characters
        """
        self.min_content_length = min_content_length

    def extract(self, url: str, html_content: Optional[str] = None) -> ExtractedContent:
        """
        Extract content from URL.

        Args:
            url: URL to extract from
            html_content: Optional HTML content (for testing)

        Returns:
            Extracted content
        """
        # In a real implementation, this would fetch and parse the URL
        # For now, we'll create mock content
        if html_content:
            return self._parse_html(url, html_content)
        else:
            return self._create_mock_content(url)

    def _create_mock_content(self, url: str) -> ExtractedContent:
        """
        Create mock extracted content for development.

        Args:
            url: URL

        Returns:
            Mock extracted content
        """
        # Extract domain for title
        domain = self._extract_domain(url)

        title = f"Article from {domain}"
        content = f"This is mock content extracted from {url}. " \
                  f"In production, this would contain the actual text " \
                  f"extracted from the web page using proper HTML parsing " \
                  f"and content extraction techniques. The content would " \
                  f"be cleaned of navigation, ads, and other non-essential " \
                  f"elements to provide the main article text."

        return ExtractedContent(
            url=url,
            title=title,
            content=content,
            metadata={"mock": True, "domain": domain}
        )

    def _parse_html(self, url: str, html_content: str) -> ExtractedContent:
        """
        Parse HTML content.

        Args:
            url: URL
            html_content: HTML content

        Returns:
            Extracted content
        """
        # Simple HTML parsing (replace with BeautifulSoup in production)
        title = self._extract_title(html_content)
        content = self._extract_text(html_content)
        author = self._extract_author(html_content)

        return ExtractedContent(
            url=url,
            title=title or "Untitled",
            content=content,
            author=author
        )

    def _extract_title(self, html: str) -> Optional[str]:
        """Extract title from HTML."""
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if match:
            return self._clean_text(match.group(1))
        return None

    def _extract_text(self, html: str) -> str:
        """Extract text from HTML."""
        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Clean up whitespace
        text = self._clean_text(text)

        return text

    def _extract_author(self, html: str) -> Optional[str]:
        """Extract author from HTML."""
        # Simple pattern matching (improve in production)
        patterns = [
            r'<meta\s+name=["\']author["\']\s+content=["\'](.*?)["\']',
            r'by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        return "unknown"

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Decode HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()

        return text

    def summarize(self, content: str, max_sentences: int = 3) -> str:
        """
        Create simple summary of content.

        Args:
            content: Content to summarize
            max_sentences: Maximum sentences in summary

        Returns:
            Summary text
        """
        # Split into sentences (simple approach)
        sentences = re.split(r'[.!?]+\s+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Take first N sentences
        summary_sentences = sentences[:max_sentences]
        summary = '. '.join(summary_sentences)

        if not summary.endswith('.'):
            summary += '.'

        return summary

    def extract_keywords(self, content: str, top_n: int = 10) -> list[str]:
        """
        Extract keywords from content.

        Args:
            content: Content text
            top_n: Number of top keywords

        Returns:
            List of keywords
        """
        # Simple keyword extraction (improve with NLP in production)
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'it', 'its', 'they', 'their', 'them'
        }

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', content.lower())

        # Count word frequency
        word_freq: Dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top N
        return [word for word, _ in sorted_words[:top_n]]

    def validate_content(self, content: ExtractedContent) -> list[str]:
        """
        Validate extracted content.

        Args:
            content: Extracted content

        Returns:
            List of validation issues
        """
        issues = []

        if not content.title:
            issues.append("Missing title")

        if not content.content:
            issues.append("Missing content")
        elif len(content.content) < self.min_content_length:
            issues.append(f"Content too short ({len(content.content)} < {self.min_content_length})")

        if not content.url:
            issues.append("Missing URL")

        return issues

    def __repr__(self) -> str:
        """String representation."""
        return f"<ContentExtractor min_length={self.min_content_length}>"
