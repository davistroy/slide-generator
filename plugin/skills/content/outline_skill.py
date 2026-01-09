"""
Outline generation skill.

Generates presentation outline from research and insights.
"""

from typing import Any

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput
from plugin.lib.json_utils import extract_json_from_response


class OutlineSkill(BaseSkill):
    """
    Generates presentation outline from research and insights.

    Creates structured presentation outline with slides, titles, and content.
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "outline"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "Outline Generation"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Generate presentation outline from research and insights"

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    def validate_input(self, input_data: SkillInput) -> tuple[bool, list[str]]:
        """
        Validate input before execution.

        Args:
            input_data: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Require research output
        if not input_data.get("research"):
            errors.append("Missing required field: research")

        return (len(errors) == 0, errors)

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute outline generation.

        Input:
        {
            "research": dict,  # ResearchSkill output
            "insights": dict (optional),  # InsightExtractionSkill output
            "audience": str (default: "general"),
            "duration_minutes": int (default: 20),
            "objectives": List[str] (optional)
        }

        Output:
        {
            "presentation_count": int,
            "presentations": [
                {
                    "audience": str,
                    "title": str,
                    "subtitle": str,
                    "slides": [
                        {
                            "slide_number": int,
                            "slide_type": str,
                            "title": str,
                            "purpose": str,
                            "key_points": List[str],
                            "supporting_sources": List[str]
                        }
                    ],
                    "estimated_duration": int
                }
            ]
        }

        Args:
            input_data: Skill input

        Returns:
            Skill output with presentation outline(s)
        """
        research = input_data.get("research")
        insights = input_data.get("insights", {})
        audience = input_data.get("audience", "general")
        duration = input_data.get("duration_minutes", 20)
        objectives = input_data.get("objectives", [])

        # Determine if multi-presentation is needed
        topic_complexity = self._assess_topic_complexity(research, insights)
        presentations = []

        if topic_complexity == "complex":
            # Generate multiple presentations for different audiences
            presentations.append(
                self._generate_executive_summary(research, insights, objectives)
            )
            presentations.append(
                self._generate_detailed_presentation(research, insights, objectives)
            )
            presentations.append(
                self._generate_technical_presentation(research, insights, objectives)
            )
        else:
            # Single presentation
            presentations.append(
                self._generate_single_presentation(
                    research, insights, audience, duration, objectives
                )
            )

        return SkillOutput.success_result(
            data={
                "presentation_count": len(presentations),
                "presentations": presentations,
            }
        )

    def _assess_topic_complexity(
        self, research: dict[str, Any], insights: dict[str, Any]
    ) -> str:
        """
        Assess topic complexity to determine presentation strategy.

        Args:
            research: Research output
            insights: Insights output

        Returns:
            Complexity level: "simple", "moderate", "complex"
        """
        sources_count = len(research.get("sources", []))
        insights_count = insights.get("insights_count", 0)

        if sources_count > 15 or insights_count > 8:
            return "complex"
        elif sources_count > 8 or insights_count > 4:
            return "moderate"
        else:
            return "simple"

    def _generate_executive_summary(
        self, research: dict[str, Any], insights: dict[str, Any], objectives: list[str]
    ) -> dict[str, Any]:
        """Generate executive summary presentation."""
        topic = research.get("search_query", "Research Topic")

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": f"{topic}: Executive Summary",
                "purpose": "Introduce the topic and set context",
                "key_points": [
                    "High-level overview",
                    "Key findings",
                    "Recommendations",
                ],
                "supporting_sources": [],
            },
            {
                "slide_number": 2,
                "slide_type": "KEY INSIGHTS",
                "title": "Key Findings",
                "purpose": "Present top insights",
                "key_points": [
                    i["statement"][:50] + "..."
                    for i in insights.get("insights", [])[:3]
                ],
                "supporting_sources": [],
            },
            {
                "slide_number": 3,
                "slide_type": "RECOMMENDATIONS",
                "title": "Recommendations",
                "purpose": "Provide actionable next steps",
                "key_points": objectives
                or [
                    "Review detailed presentation",
                    "Consider implementation",
                    "Further research",
                ],
                "supporting_sources": [],
            },
        ]

        return {
            "audience": "executive",
            "title": f"{topic}: Executive Summary",
            "subtitle": "High-level overview and key insights",
            "slides": slides,
            "estimated_duration": 10,
        }

    def _generate_detailed_presentation(
        self, research: dict[str, Any], insights: dict[str, Any], objectives: list[str]
    ) -> dict[str, Any]:
        """Generate detailed presentation using Claude API with actual research content."""
        from plugin.lib.claude_client import get_claude_client

        topic = research.get("search_query", "Research Topic")
        sources = research.get("sources", [])

        # Build research summary for Claude
        research_summary = f"Topic: {topic}\n\n"
        research_summary += f"Number of sources: {len(sources)}\n\n"
        research_summary += "Key source content:\n"

        for i, source in enumerate(sources[:10], 1):
            research_summary += f"\n{i}. {source.get('title', 'Untitled')}\n"
            research_summary += f"   Citation: {source.get('citation_id', 'N/A')}\n"
            research_summary += f"   Content: {source.get('content', '')[:400]}...\n"

        # Use Claude to generate intelligent outline
        client = get_claude_client()

        prompt = f"""Based on this research, create a detailed presentation outline.

{research_summary}

Generate a comprehensive presentation outline with 8-12 slides. For each slide, provide:
- slide_type: Choose from TITLE SLIDE, SECTION DIVIDER, CONTENT, IMAGE, TEXT+IMAGE, PROBLEM STATEMENT, INSIGHT, FRAMEWORK, COMPARISON, CASE STUDY, ACTION, CONCLUSION
- title: Clear, specific slide title (not generic)
- purpose: What this slide accomplishes
- key_points: 3-5 specific, research-based points (NOT generic placeholders)
- supporting_sources: Citation IDs from research

Return as JSON with this structure:
{{
  "title": "presentation title",
  "subtitle": "subtitle",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "TITLE SLIDE",
      "title": "specific title from research",
      "purpose": "specific purpose",
      "key_points": ["specific point 1", "specific point 2", "specific point 3"],
      "supporting_sources": ["cite-001", "cite-002"]
    }}
  ]
}}

Focus on creating a logical flow that teaches the topic comprehensively."""

        system_prompt = """You are a presentation architect creating detailed, research-based outlines.
Use specific information from the research sources, not generic placeholders.
Create a compelling narrative arc that educates the audience."""

        response = client.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7, max_tokens=4096
        )

        # Parse JSON response
        outline_data = extract_json_from_response(response, fallback=None)

        if outline_data is None:
            print("[WARN] Failed to parse outline JSON")
            return self._generate_simple_fallback_outline(research, insights)

        return {
            "audience": "general",
            "title": outline_data.get("title", topic),
            "subtitle": outline_data.get("subtitle", "Comprehensive Analysis"),
            "slides": outline_data.get("slides", []),
            "estimated_duration": len(outline_data.get("slides", [])) * 2,
        }

    def _generate_technical_presentation(
        self, research: dict[str, Any], insights: dict[str, Any], objectives: list[str]
    ) -> dict[str, Any]:
        """Generate technical deep-dive presentation."""
        topic = research.get("search_query", "Research Topic")
        sources = research.get("sources", [])

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": f"{topic}: Technical Deep Dive",
                "purpose": "Introduce detailed technical analysis",
                "key_points": [],
                "supporting_sources": [],
            }
        ]

        # Add detailed analysis slides
        for i, source in enumerate(sources[:8], start=2):
            slides.append(
                {
                    "slide_number": i,
                    "slide_type": "TECHNICAL_DETAIL",
                    "title": source.get("title", "Technical Detail")[:50],
                    "purpose": "Deep dive into specific aspect",
                    "key_points": [
                        "Technical background",
                        "Implementation details",
                        "Data and evidence",
                    ],
                    "supporting_sources": [source.get("citation_id")],
                }
            )

        return {
            "audience": "technical",
            "title": f"{topic}: Technical Analysis",
            "subtitle": "In-depth technical exploration",
            "slides": slides,
            "estimated_duration": 40,
        }

    def _generate_simple_fallback_outline(
        self, research: dict[str, Any], insights: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate simple fallback outline when API fails."""
        topic = research.get("search_query", "Research Topic")
        sources = research.get("sources", [])

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": topic,
                "purpose": "Introduce the topic",
                "key_points": [],
                "supporting_sources": [],
            }
        ]

        # Add slides for top sources
        for i, source in enumerate(sources[:8], start=2):
            slides.append(
                {
                    "slide_number": i,
                    "slide_type": "CONTENT",
                    "title": source.get("title", "")[:60],
                    "purpose": f"Present information from {source.get('title', 'source')[:30]}",
                    "key_points": [
                        source.get("content", "")[:100],
                        source.get("snippet", "")[:100],
                    ],
                    "supporting_sources": [source.get("citation_id", "")],
                }
            )

        slides.append(
            {
                "slide_number": len(slides) + 1,
                "slide_type": "CONCLUSION",
                "title": "Summary",
                "purpose": "Wrap up",
                "key_points": ["Key takeaways"],
                "supporting_sources": [],
            }
        )

        return {
            "audience": "general",
            "title": topic,
            "subtitle": "",
            "slides": slides,
            "estimated_duration": len(slides) * 2,
        }

    def _generate_single_presentation(
        self,
        research: dict[str, Any],
        insights: dict[str, Any],
        audience: str,
        duration: int,
        objectives: list[str],
    ) -> dict[str, Any]:
        """Generate single presentation using Claude API with research content."""
        # Use the improved detailed presentation generator
        return self._generate_detailed_presentation(research, insights, objectives)
