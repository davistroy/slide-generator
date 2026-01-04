"""
Outline generation skill.

Generates presentation outline from research and insights.
"""

from typing import Dict, Any, List
from ..base_skill import BaseSkill, SkillInput, SkillOutput


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
            presentations.append(self._generate_executive_summary(research, insights, objectives))
            presentations.append(self._generate_detailed_presentation(research, insights, objectives))
            presentations.append(self._generate_technical_presentation(research, insights, objectives))
        else:
            # Single presentation
            presentations.append(self._generate_single_presentation(
                research, insights, audience, duration, objectives
            ))

        return SkillOutput.success_result(
            data={
                "presentation_count": len(presentations),
                "presentations": presentations
            }
        )

    def _assess_topic_complexity(
        self,
        research: Dict[str, Any],
        insights: Dict[str, Any]
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
        self,
        research: Dict[str, Any],
        insights: Dict[str, Any],
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate executive summary presentation."""
        topic = research.get("search_query", "Research Topic")

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": f"{topic}: Executive Summary",
                "purpose": "Introduce the topic and set context",
                "key_points": ["High-level overview", "Key findings", "Recommendations"],
                "supporting_sources": []
            },
            {
                "slide_number": 2,
                "slide_type": "KEY INSIGHTS",
                "title": "Key Findings",
                "purpose": "Present top insights",
                "key_points": [i["statement"][:50] + "..." for i in insights.get("insights", [])[:3]],
                "supporting_sources": []
            },
            {
                "slide_number": 3,
                "slide_type": "RECOMMENDATIONS",
                "title": "Recommendations",
                "purpose": "Provide actionable next steps",
                "key_points": objectives or ["Review detailed presentation", "Consider implementation", "Further research"],
                "supporting_sources": []
            }
        ]

        return {
            "audience": "executive",
            "title": f"{topic}: Executive Summary",
            "subtitle": "High-level overview and key insights",
            "slides": slides,
            "estimated_duration": 10
        }

    def _generate_detailed_presentation(
        self,
        research: Dict[str, Any],
        insights: Dict[str, Any],
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate detailed presentation."""
        topic = research.get("search_query", "Research Topic")
        themes = research.get("key_themes", [])

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": topic,
                "purpose": "Introduce the comprehensive analysis",
                "key_points": [],
                "supporting_sources": []
            }
        ]

        # Add slides for each theme
        for i, theme in enumerate(themes[:5], start=2):
            slides.append({
                "slide_number": i,
                "slide_type": "CONTENT",
                "title": theme.title(),
                "purpose": f"Explore {theme} in detail",
                "key_points": [f"Point about {theme}", f"Evidence for {theme}", f"Implications of {theme}"],
                "supporting_sources": []
            })

        # Add conclusion
        slides.append({
            "slide_number": len(slides) + 1,
            "slide_type": "CONCLUSION",
            "title": "Summary and Next Steps",
            "purpose": "Wrap up and provide direction",
            "key_points": ["Key takeaways", "Recommendations", "Next steps"],
            "supporting_sources": []
        })

        return {
            "audience": "general",
            "title": topic,
            "subtitle": "Comprehensive Analysis",
            "slides": slides,
            "estimated_duration": 25
        }

    def _generate_technical_presentation(
        self,
        research: Dict[str, Any],
        insights: Dict[str, Any],
        objectives: List[str]
    ) -> Dict[str, Any]:
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
                "supporting_sources": []
            }
        ]

        # Add detailed analysis slides
        for i, source in enumerate(sources[:8], start=2):
            slides.append({
                "slide_number": i,
                "slide_type": "TECHNICAL_DETAIL",
                "title": source.get("title", "Technical Detail")[:50],
                "purpose": "Deep dive into specific aspect",
                "key_points": [
                    "Technical background",
                    "Implementation details",
                    "Data and evidence"
                ],
                "supporting_sources": [source.get("citation_id")]
            })

        return {
            "audience": "technical",
            "title": f"{topic}: Technical Analysis",
            "subtitle": "In-depth technical exploration",
            "slides": slides,
            "estimated_duration": 40
        }

    def _generate_single_presentation(
        self,
        research: Dict[str, Any],
        insights: Dict[str, Any],
        audience: str,
        duration: int,
        objectives: List[str]
    ) -> Dict[str, Any]:
        """Generate single presentation."""
        topic = research.get("search_query", "Research Topic")
        themes = research.get("key_themes", [])

        # Calculate slide count based on duration
        slides_count = max(5, min(int(duration / 2), 15))

        slides = [
            {
                "slide_number": 1,
                "slide_type": "TITLE SLIDE",
                "title": topic,
                "purpose": "Introduce the topic",
                "key_points": [],
                "supporting_sources": []
            }
        ]

        # Add content slides
        for i, theme in enumerate(themes[:slides_count - 2], start=2):
            slides.append({
                "slide_number": i,
                "slide_type": "CONTENT",
                "title": theme.title(),
                "purpose": f"Discuss {theme}",
                "key_points": [f"Point 1 about {theme}", f"Point 2 about {theme}", f"Point 3 about {theme}"],
                "supporting_sources": []
            })

        # Add conclusion
        slides.append({
            "slide_number": len(slides) + 1,
            "slide_type": "CONCLUSION",
            "title": "Conclusion",
            "purpose": "Summarize and provide next steps",
            "key_points": objectives or ["Summary", "Next steps"],
            "supporting_sources": []
        })

        return {
            "audience": audience,
            "title": topic,
            "subtitle": f"Presentation for {audience} audience",
            "slides": slides,
            "estimated_duration": duration
        }
