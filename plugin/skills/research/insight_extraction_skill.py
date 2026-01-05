"""
Insight extraction skill.

Extracts key insights, arguments, and concepts from research.
"""

from typing import Dict, Any, List
from plugin.base_skill import BaseSkill, SkillInput, SkillOutput
import re


class InsightExtractionSkill(BaseSkill):
    """
    Extracts key insights, arguments, and concepts from research.

    Analyzes research content to identify claims, evidence, and relationships.
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "extract-insights"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "Insight Extraction"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Extract key insights, arguments, and concepts from research"

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

        # Require research output
        if not input_data.get("research_output"):
            errors.append("Missing required field: research_output")

        return (len(errors) == 0, errors)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute insight extraction.

        Input:
        {
            "research_output": dict,  # Output from ResearchSkill
            "focus_areas": List[str] (optional)
        }

        Output:
        {
            "insights": [
                {
                    "statement": str,
                    "supporting_evidence": List[str],
                    "confidence": float,
                    "sources": List[str]
                }
            ],
            "arguments": [
                {
                    "claim": str,
                    "reasoning": str,
                    "evidence": List[str],
                    "counter_arguments": List[str]
                }
            ],
            "concept_map": {
                "concepts": List[str],
                "relationships": List[dict]
            }
        }

        Args:
            input_data: Skill input

        Returns:
            Skill output with extracted insights
        """
        research_output = input_data.get("research_output")
        focus_areas = input_data.get("focus_areas", [])

        sources = research_output.get("sources", [])

        # Extract insights
        insights = self._extract_insights(sources, focus_areas)

        # Extract arguments
        arguments = self._extract_arguments(sources)

        # Build concept map
        concept_map = self._build_concept_map(sources)

        return SkillOutput.success_result(
            data={
                "insights": insights,
                "arguments": arguments,
                "concept_map": concept_map,
                "insights_count": len(insights),
                "arguments_count": len(arguments)
            }
        )

    def _extract_insights(
        self,
        sources: List[Dict[str, Any]],
        focus_areas: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Extract key insights from sources.

        Args:
            sources: Research sources
            focus_areas: Optional focus areas

        Returns:
            List of insights
        """
        insights = []

        # Extract sentences from content
        for source in sources:
            content = source.get("content", "")
            sentences = re.split(r'[.!?]+\s+', content)

            # Find sentences with insight indicators
            insight_patterns = [
                r'\b(shows?|demonstrates?|proves?|indicates?|suggests?)\b',
                r'\b(importantly?|significantly?|notably?)\b',
                r'\b(research|study|analysis)\s+(shows?|finds?|reveals?)\b'
            ]

            for sentence in sentences:
                for pattern in insight_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        insights.append({
                            "statement": sentence.strip(),
                            "supporting_evidence": [source.get("snippet", "")],
                            "confidence": 0.75,
                            "sources": [source.get("citation_id")]
                        })
                        break

        # Deduplicate and limit
        return insights[:10]

    def _extract_arguments(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract arguments from sources.

        Args:
            sources: Research sources

        Returns:
            List of arguments
        """
        arguments = []

        # Find claim-evidence patterns
        claim_patterns = [
            r'(.*?)\s+because\s+(.*?)\.',
            r'(.*?)\s+therefore\s+(.*?)\.',
            r'(.*?)\s+thus\s+(.*?)\.'
        ]

        for source in sources:
            content = source.get("content", "")

            for pattern in claim_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    claim = match.group(1).strip()
                    reasoning = match.group(2).strip()

                    arguments.append({
                        "claim": claim,
                        "reasoning": reasoning,
                        "evidence": [source.get("snippet", "")],
                        "counter_arguments": []  # Would be populated by analysis
                    })

        # Limit results
        return arguments[:5]

    def _build_concept_map(
        self,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build concept map from sources.

        Args:
            sources: Research sources

        Returns:
            Concept map
        """
        # Extract key concepts from themes
        concepts = set()
        for source in sources:
            # Get keywords as concepts
            content = source.get("content", "")
            words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            concepts.update(words[:5])

        concept_list = list(concepts)[:15]

        # Create simple relationships
        relationships = []
        for i, concept in enumerate(concept_list):
            if i < len(concept_list) - 1:
                relationships.append({
                    "from": concept,
                    "to": concept_list[i + 1],
                    "type": "related_to"
                })

        return {
            "concepts": concept_list,
            "relationships": relationships
        }
