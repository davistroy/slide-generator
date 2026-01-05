"""
Citation management for presentation generation.

Handles citation formatting, tracking, and bibliography generation.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Citation:
    """A single citation source."""

    citation_id: str
    title: str
    url: str
    author: str | None = None
    publication_date: str | None = None
    access_date: str = None
    publisher: str | None = None

    def __post_init__(self):
        """Set access date to current date if not provided."""
        if self.access_date is None:
            self.access_date = datetime.now().strftime("%Y-%m-%d")


@dataclass
class CitationUsage:
    """Tracks where a citation is used."""

    citation_id: str
    slide_number: int
    context: str  # The text that uses this citation


class CitationManager:
    """
    Manages citations and references throughout workflow.

    Supports APA, MLA, and Chicago citation formats.
    Tracks citation usage across slides.
    Generates formatted bibliographies.
    """

    def __init__(self, default_format: str = "APA"):
        """
        Initialize citation manager.

        Args:
            default_format: Default citation format (APA, MLA, Chicago)
        """
        self.default_format = default_format
        self.citations: dict[str, Citation] = {}
        self.usage: list[CitationUsage] = []
        self._id_counter = 0

    def add_citation(
        self,
        title: str,
        url: str,
        author: str | None = None,
        publication_date: str | None = None,
        publisher: str | None = None,
    ) -> str:
        """
        Add a citation source.

        Args:
            title: Source title
            url: Source URL
            author: Author name
            publication_date: Publication date
            publisher: Publisher name

        Returns:
            Citation ID
        """
        # Generate unique ID
        self._id_counter += 1
        citation_id = f"cite-{self._id_counter:03d}"

        citation = Citation(
            citation_id=citation_id,
            title=title,
            url=url,
            author=author,
            publication_date=publication_date,
            publisher=publisher,
        )

        self.citations[citation_id] = citation
        return citation_id

    def track_usage(self, citation_id: str, slide_number: int, context: str) -> None:
        """
        Track where a citation is used.

        Args:
            citation_id: Citation ID
            slide_number: Slide number where used
            context: Context text
        """
        if citation_id not in self.citations:
            raise ValueError(f"Citation {citation_id} not found")

        usage = CitationUsage(
            citation_id=citation_id, slide_number=slide_number, context=context
        )
        self.usage.append(usage)

    def format_citation(self, citation_id: str, style: str | None = None) -> str:
        """
        Format a citation.

        Args:
            citation_id: Citation ID
            style: Citation style (APA, MLA, Chicago), uses default if None

        Returns:
            Formatted citation string
        """
        if citation_id not in self.citations:
            raise ValueError(f"Citation {citation_id} not found")

        citation = self.citations[citation_id]
        style = style or self.default_format

        if style.upper() == "APA":
            return self._format_apa(citation)
        elif style.upper() == "MLA":
            return self._format_mla(citation)
        elif style.upper() == "CHICAGO":
            return self._format_chicago(citation)
        else:
            raise ValueError(f"Unknown citation style: {style}")

    def _format_apa(self, citation: Citation) -> str:
        """Format citation in APA style."""
        parts = []

        # Author (if available)
        if citation.author:
            parts.append(f"{citation.author}.")

        # Publication date
        if citation.publication_date:
            parts.append(f"({citation.publication_date}).")

        # Title (italicized in markdown)
        parts.append(f"*{citation.title}*.")

        # Publisher (if available)
        if citation.publisher:
            parts.append(f"{citation.publisher}.")

        # URL and access date
        parts.append(f"Retrieved {citation.access_date}, from {citation.url}")

        return " ".join(parts)

    def _format_mla(self, citation: Citation) -> str:
        """Format citation in MLA style."""
        parts = []

        # Author (Last, First)
        if citation.author:
            parts.append(f"{citation.author}.")

        # Title (in quotes)
        parts.append(f'"{citation.title}."')

        # Publisher and date
        if citation.publisher:
            parts.append(f"{citation.publisher},")
        if citation.publication_date:
            parts.append(f"{citation.publication_date}.")

        # URL
        parts.append(f"{citation.url}.")

        # Access date
        parts.append(f"Accessed {citation.access_date}.")

        return " ".join(parts)

    def _format_chicago(self, citation: Citation) -> str:
        """Format citation in Chicago style."""
        parts = []

        # Author
        if citation.author:
            parts.append(f"{citation.author}.")

        # Title (in quotes)
        parts.append(f'"{citation.title}."')

        # Publisher and date
        if citation.publisher and citation.publication_date:
            parts.append(f"{citation.publisher}, {citation.publication_date}.")
        elif citation.publisher:
            parts.append(f"{citation.publisher}.")
        elif citation.publication_date:
            parts.append(f"{citation.publication_date}.")

        # URL
        parts.append(f"{citation.url}.")

        return " ".join(parts)

    def generate_bibliography(
        self, citation_ids: list[str] | None = None, style: str | None = None
    ) -> str:
        """
        Generate formatted bibliography.

        Args:
            citation_ids: List of citation IDs to include (all if None)
            style: Citation style

        Returns:
            Formatted bibliography as string
        """
        if citation_ids is None:
            citation_ids = list(self.citations.keys())

        bibliography_lines = ["## References\n"]

        for cid in sorted(citation_ids):
            if cid in self.citations:
                formatted = self.format_citation(cid, style)
                bibliography_lines.append(f"- {formatted}")

        return "\n".join(bibliography_lines)

    def get_citation_usage(self, citation_id: str) -> list[CitationUsage]:
        """
        Get all usages of a citation.

        Args:
            citation_id: Citation ID

        Returns:
            List of citation usages
        """
        return [u for u in self.usage if u.citation_id == citation_id]

    def get_slide_citations(self, slide_number: int) -> list[str]:
        """
        Get all citations used in a slide.

        Args:
            slide_number: Slide number

        Returns:
            List of citation IDs
        """
        citation_ids = [
            u.citation_id for u in self.usage if u.slide_number == slide_number
        ]
        return list(set(citation_ids))  # Remove duplicates

    def validate_citations(self) -> list[str]:
        """
        Validate all citations for completeness.

        Returns:
            List of validation issues
        """
        issues = []

        for cid, citation in self.citations.items():
            # Check required fields
            if not citation.title:
                issues.append(f"{cid}: Missing title")
            if not citation.url:
                issues.append(f"{cid}: Missing URL")

            # Check URL format
            if citation.url and not re.match(r"https?://", citation.url):
                issues.append(f"{cid}: Invalid URL format")

        return issues

    def export_citations(self) -> list[dict[str, Any]]:
        """
        Export all citations as list of dictionaries.

        Returns:
            List of citation data
        """
        return [
            {
                "id": cid,
                "title": c.title,
                "url": c.url,
                "author": c.author,
                "publication_date": c.publication_date,
                "access_date": c.access_date,
                "publisher": c.publisher,
            }
            for cid, c in self.citations.items()
        ]

    def import_citations(self, citations_data: list[dict[str, Any]]) -> None:
        """
        Import citations from list of dictionaries.

        Args:
            citations_data: List of citation data
        """
        for data in citations_data:
            citation_id = data.get("id", f"cite-{self._id_counter + 1:03d}")
            self._id_counter = max(self._id_counter, int(citation_id.split("-")[1]))

            citation = Citation(
                citation_id=citation_id,
                title=data["title"],
                url=data["url"],
                author=data.get("author"),
                publication_date=data.get("publication_date"),
                access_date=data.get("access_date"),
                publisher=data.get("publisher"),
            )
            self.citations[citation_id] = citation

    def __repr__(self) -> str:
        """String representation."""
        return f"<CitationManager citations={len(self.citations)} usages={len(self.usage)}>"
