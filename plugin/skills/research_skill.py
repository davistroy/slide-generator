"""
Research skill for web research and source gathering.

Conducts web research and gathers authoritative sources on a topic.
"""

from typing import Dict, Any, List
from ..base_skill import BaseSkill, SkillInput, SkillOutput
from ..lib.web_search import WebSearch, SearchResult
from ..lib.content_extractor import ContentExtractor, ExtractedContent
from ..lib.citation_manager import CitationManager
import json


class ResearchSkill(BaseSkill):
    """
    Conducts web research and gathers sources on a topic.

    Uses web search to find relevant sources, extracts content,
    and manages citations.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize research skill.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.web_search = WebSearch()
        self.content_extractor = ContentExtractor()
        self.citation_manager = CitationManager()

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "research"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "Web Research"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Search the web and gather authoritative sources on a topic"

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    def validate_input(self, input_data: SkillInput) -> tuple[bool, List[str]]:
        """
        Validate input before execution.

        Args:
            input_data: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Require topic
        if not input_data.get("topic"):
            errors.append("Missing required field: topic")

        # Validate search depth
        search_depth = input_data.get("search_depth", "standard")
        if search_depth not in ["quick", "standard", "comprehensive"]:
            errors.append(f"Invalid search_depth: {search_depth}")

        # Validate max_sources
        max_sources = input_data.get("max_sources", 20)
        if not isinstance(max_sources, int) or max_sources < 1 or max_sources > 100:
            errors.append("max_sources must be between 1 and 100")

        return (len(errors) == 0, errors)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute the research skill.

        Input:
        {
            "topic": str,
            "context": str (optional),
            "max_sources": int (default: 20),
            "search_depth": "quick" | "standard" | "comprehensive"
        }

        Output:
        {
            "sources": [
                {
                    "citation_id": str,
                    "url": str,
                    "title": str,
                    "content": str,
                    "relevance_score": float,
                    "word_count": int
                }
            ],
            "summary": str,
            "key_themes": List[str],
            "citations": List[dict]
        }

        Args:
            input_data: Skill input

        Returns:
            Skill output with research results
        """
        topic = input_data.get("topic")
        context = input_data.get("context", "")
        max_sources = input_data.get("max_sources", 20)
        search_depth = input_data.get("search_depth", "standard")

        # Determine number of results based on search depth
        depth_multipliers = {
            "quick": 0.5,
            "standard": 1.0,
            "comprehensive": 1.5
        }
        search_count = int(max_sources * depth_multipliers[search_depth])

        # Execute search
        query = self._build_search_query(topic, context)
        search_results = self.web_search.search(query, max_results=search_count)

        # Extract content from top results
        sources = []
        for result in search_results[:max_sources]:
            extracted = self.content_extractor.extract(result.url)

            # Add citation
            citation_id = self.citation_manager.add_citation(
                title=extracted.title,
                url=extracted.url,
                author=extracted.author,
                publication_date=extracted.publication_date
            )

            sources.append({
                "citation_id": citation_id,
                "url": extracted.url,
                "title": extracted.title,
                "content": extracted.content,
                "relevance_score": result.relevance_score,
                "word_count": extracted.word_count,
                "snippet": result.snippet
            })

        # Generate summary
        summary = self._generate_summary(sources)

        # Extract key themes
        key_themes = self._extract_themes(sources)

        # Export citations
        citations = self.citation_manager.export_citations()

        return SkillOutput.success_result(
            data={
                "sources": sources,
                "summary": summary,
                "key_themes": key_themes,
                "citations": citations,
                "search_query": query,
                "sources_count": len(sources)
            }
        )

    def _build_search_query(self, topic: str, context: str = "") -> str:
        """
        Build optimized search query.

        Args:
            topic: Research topic
            context: Additional context

        Returns:
            Search query string
        """
        if context:
            return f"{topic} {context}"
        return topic

    def _generate_summary(self, sources: List[Dict[str, Any]]) -> str:
        """
        Generate research summary from sources.

        Args:
            sources: List of source data

        Returns:
            Summary text
        """
        if not sources:
            return "No sources found."

        summary_parts = [
            f"Researched topic with {len(sources)} sources.",
            f"Total content: {sum(s['word_count'] for s in sources):,} words."
        ]

        # Add top sources
        top_sources = sorted(sources, key=lambda s: s['relevance_score'], reverse=True)[:3]
        summary_parts.append("\nTop sources:")
        for i, source in enumerate(top_sources, 1):
            summary_parts.append(f"{i}. {source['title']} ({source['url']})")

        return "\n".join(summary_parts)

    def _extract_themes(self, sources: List[Dict[str, Any]]) -> List[str]:
        """
        Extract key themes from research sources.

        Args:
            sources: List of source data

        Returns:
            List of key themes
        """
        # Simple theme extraction based on keywords
        all_keywords = []
        for source in sources:
            keywords = self.content_extractor.extract_keywords(source['content'], top_n=5)
            all_keywords.extend(keywords)

        # Count keyword frequency
        keyword_freq: Dict[str, int] = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

        # Get top themes
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        themes = [keyword for keyword, _ in sorted_keywords[:10]]

        return themes

    def cleanup(self) -> None:
        """Optional cleanup after execution."""
        self.web_search.clear_cache()
