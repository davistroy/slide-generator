"""
Claude API client for research and content generation.

Uses Anthropic's Claude API for:
- Web research assistance
- Content analysis and insights
- Outline generation
- Content drafting

Gemini is used separately ONLY for image generation.
"""

import os
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


class ClaudeClient:
    """
    Client for Claude API operations.

    Uses Claude for all text-based AI operations:
    - Research queries and analysis
    - Insight extraction
    - Outline generation
    - Content drafting

    NOT used for image generation (Gemini handles that).
    """

    def __init__(
        self, api_key: str | None = None, model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: Claude Sonnet 4.5)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in .env file or pass as parameter."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs,
    ) -> str:
        """
        Generate text using Claude.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional parameters for the API

        Returns:
            Generated text response
        """
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "",
            messages=messages,
            **kwargs,
        )

        return response.content[0].text

    def analyze_content(
        self, content: str, analysis_type: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Analyze content using Claude.

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (insights, themes, summary, etc.)
            context: Additional context for analysis

        Returns:
            Analysis results as dictionary
        """
        context_str = ""
        if context:
            context_str = "\n\nContext:\n" + "\n".join(
                f"- {k}: {v}" for k, v in context.items()
            )

        prompt = f"""Analyze the following content and extract {analysis_type}.

Content:
{content}
{context_str}

Provide your analysis as a JSON object."""

        system_prompt = f"""You are an expert content analyst. Extract {analysis_type}
from the provided content and return results as valid JSON."""

        response = self.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7
        )

        # Parse JSON response
        import json

        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            # If parsing fails, return raw text
            return {"analysis": response}

    def generate_search_queries(
        self, topic: str, num_queries: int = 5, depth: str = "standard"
    ) -> list[str]:
        """
        Generate optimized search queries for a topic.

        Args:
            topic: Research topic
            num_queries: Number of queries to generate
            depth: Search depth (quick, standard, comprehensive)

        Returns:
            List of search query strings
        """
        depth_instructions = {
            "quick": "Generate broad, general queries",
            "standard": "Generate balanced queries covering main aspects",
            "comprehensive": "Generate detailed queries covering all aspects and subtopics",
        }

        prompt = f"""Generate {num_queries} optimized web search queries for researching this topic:

Topic: {topic}

Instructions: {depth_instructions.get(depth, depth_instructions["standard"])}

Return a JSON array of query strings."""

        system_prompt = """You are a research librarian expert at formulating effective
search queries. Generate queries that will find authoritative, comprehensive sources."""

        response = self.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.8
        )

        # Parse JSON response
        import json

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            queries = json.loads(json_str)
            return queries if isinstance(queries, list) else [topic]
        except json.JSONDecodeError:
            # Fallback to simple query
            return [topic]

    def extract_insights(
        self, sources: list[dict[str, Any]], focus_areas: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Extract insights from research sources.

        Args:
            sources: List of source documents
            focus_areas: Optional specific areas to focus on

        Returns:
            Dictionary with insights, arguments, and concept map
        """
        # Prepare source content
        source_text = "\n\n".join(
            [
                f"Source {i + 1}: {s.get('title', 'Untitled')}\n{s.get('content', s.get('snippet', ''))}"
                for i, s in enumerate(sources[:20])  # Limit to 20 sources
            ]
        )

        focus_str = ""
        if focus_areas:
            focus_str = f"\n\nFocus particularly on: {', '.join(focus_areas)}"

        prompt = f"""Analyze these research sources and extract key insights.

{source_text}
{focus_str}

Extract:
1. Key insights (claims supported by evidence)
2. Main arguments (with reasoning and evidence)
3. Core concepts and their relationships

Return as JSON with this structure:
{{
  "insights": [
    {{
      "statement": "insight statement",
      "supporting_evidence": ["evidence1", "evidence2"],
      "confidence": 0.9,
      "sources": ["source1", "source2"]
    }}
  ],
  "arguments": [
    {{
      "claim": "main claim",
      "reasoning": "explanation",
      "evidence": ["evidence"],
      "counter_arguments": ["potential objections"]
    }}
  ],
  "concept_map": {{
    "concepts": [
      {{"name": "concept", "description": "what it is"}}
    ],
    "relationships": [
      {{"from": "concept1", "to": "concept2", "type": "relationship"}}
    ]
  }}
}}"""

        system_prompt = """You are a research analyst expert at extracting insights from
multiple sources. Identify patterns, synthesize information, and map conceptual relationships."""

        return self.analyze_content(
            source_text,
            "insights and arguments",
            {"prompt": prompt, "system": system_prompt},
        )

    def generate_outline(
        self,
        research_data: dict[str, Any],
        insights_data: dict[str, Any],
        audience: str = "general",
        duration_minutes: int = 30,
    ) -> dict[str, Any]:
        """
        Generate presentation outline from research.

        Args:
            research_data: Research output with sources and themes
            insights_data: Insights extraction output
            audience: Target audience
            duration_minutes: Presentation duration

        Returns:
            Outline with slides and structure
        """
        # Estimate slides based on duration (roughly 2-3 min per slide)
        target_slides = max(5, min(40, duration_minutes // 2))

        prompt = f"""Generate a presentation outline from this research.

Research Summary:
- Topic: {research_data.get("search_query", "Unknown")}
- Sources: {len(research_data.get("sources", []))}
- Key Themes: {", ".join(research_data.get("key_themes", [])[:5])}

Key Insights: {len(insights_data.get("insights", []))}

Presentation Parameters:
- Audience: {audience}
- Duration: {duration_minutes} minutes
- Target slides: {target_slides}

Generate outline as JSON:
{{
  "presentations": [
    {{
      "title": "presentation title",
      "audience": "audience type",
      "slides": [
        {{
          "slide_number": 1,
          "slide_type": "TITLE SLIDE",
          "title": "slide title",
          "purpose": "what this slide accomplishes",
          "key_points": ["point1", "point2"],
          "supporting_sources": ["cite-001"]
        }}
      ],
      "estimated_duration": {duration_minutes}
    }}
  ],
  "presentation_count": 1
}}

Slide types: TITLE SLIDE, SECTION DIVIDER, CONTENT, IMAGE, PROBLEM STATEMENT,
INSIGHT, FRAMEWORK, COMPARISON, CASE STUDY, ACTION, CONCLUSION"""

        system_prompt = """You are a presentation architect. Create clear, logical
outlines that tell compelling stories and achieve learning objectives."""

        response = self.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.7, max_tokens=8192
        )

        # Parse JSON response
        import json

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback outline
            return {
                "presentations": [
                    {
                        "title": research_data.get("search_query", "Presentation"),
                        "audience": audience,
                        "slides": [],
                        "estimated_duration": duration_minutes,
                    }
                ],
                "presentation_count": 1,
            }

    def generate_clarifying_questions(
        self, topic: str, num_questions: int = 5
    ) -> list[dict[str, Any]]:
        """
        Generate clarifying questions for research refinement.

        Args:
            topic: Research topic
            num_questions: Number of questions to generate

        Returns:
            List of questions with options
        """
        prompt = f"""For this research topic, generate {num_questions} clarifying questions
to better understand the user's needs:

Topic: {topic}

Generate questions about:
- Target audience
- Presentation objectives
- Level of detail needed
- Specific focus areas
- Constraints or requirements

Return as JSON array:
[
  {{
    "id": "audience",
    "question": "Who is the primary audience?",
    "options": ["Executives", "Technical", "General", "Mixed"]
  }}
]"""

        system_prompt = """You are a research consultant helping to refine research
scope. Ask insightful questions that clarify requirements."""

        response = self.generate_text(
            prompt=prompt, system_prompt=system_prompt, temperature=0.8
        )

        # Parse JSON response
        import json

        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            questions = json.loads(json_str)
            return questions if isinstance(questions, list) else []
        except json.JSONDecodeError:
            # Fallback questions
            return [
                {
                    "id": "audience",
                    "question": "Who is the primary audience?",
                    "options": ["Technical", "General", "Executive", "Mixed"],
                }
            ]


# Convenience function for getting a client instance
def get_claude_client(model: str = "claude-sonnet-4-5-20250929") -> ClaudeClient:
    """
    Get a configured Claude client instance.

    Args:
        model: Claude model to use

    Returns:
        ClaudeClient instance
    """
    return ClaudeClient(model=model)
