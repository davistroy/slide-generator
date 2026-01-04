"""
Claude Agent SDK integration for research and content generation.

Uses Claude Agent SDK for:
- Agentic research workflows with tool use
- Multi-turn research refinement conversations
- Planning and execution for complex tasks
- State management across research phases

Uses plain API for:
- Simple one-shot text generation
- Structured output parsing
"""

import os
from typing import Dict, Any, List, Optional, Callable
from anthropic import Anthropic
import json


class ResearchAgent:
    """
    Agent for conducting research with tool use.

    Capabilities:
    - Generate and execute search queries
    - Extract and analyze content from sources
    - Manage citations and references
    - Refine research based on feedback
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize research agent with Claude."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"
        self.conversation_history = []

    def _create_search_tool(self) -> Dict[str, Any]:
        """Define web search tool for the agent."""
        return {
            "name": "web_search",
            "description": "Search the web for information on a topic. Returns list of relevant sources with titles, URLs, and snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to execute"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }

    def _create_extract_content_tool(self) -> Dict[str, Any]:
        """Define content extraction tool."""
        return {
            "name": "extract_content",
            "description": "Extract and clean content from a web page URL. Returns full text content for analysis.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract content from"
                    }
                },
                "required": ["url"]
            }
        }

    def _create_citation_tool(self) -> Dict[str, Any]:
        """Define citation management tool."""
        return {
            "name": "add_citation",
            "description": "Add a source to the citation manager and get a citation ID for referencing.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the source"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL of the source"
                    },
                    "author": {
                        "type": "string",
                        "description": "Author name (if known)"
                    }
                },
                "required": ["title", "url"]
            }
        }

    def conduct_research(
        self,
        topic: str,
        search_depth: str = "comprehensive",
        max_sources: int = 20,
        search_function: Optional[Callable] = None,
        extract_function: Optional[Callable] = None,
        citation_function: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Conduct agentic research on a topic.

        The agent will:
        1. Generate effective search queries
        2. Execute searches using provided function
        3. Extract content from top sources
        4. Analyze and synthesize findings
        5. Manage citations

        Args:
            topic: Research topic
            search_depth: quick, standard, or comprehensive
            max_sources: Maximum sources to gather
            search_function: Function to execute web searches
            extract_function: Function to extract content from URLs
            citation_function: Function to add citations

        Returns:
            Research results with sources, themes, summary
        """
        # Define tools available to the agent
        tools = [
            self._create_search_tool(),
            self._create_extract_content_tool(),
            self._create_citation_tool()
        ]

        # System prompt for research agent
        system_prompt = f"""You are an expert research assistant conducting {search_depth} research.

Your task: Research the topic thoroughly and gather authoritative sources.

Process:
1. Generate 3-5 effective search queries covering different aspects
2. Use web_search tool to find sources for each query
3. Extract content from the most relevant sources (top {max_sources})
4. Add citations for all sources used
5. Analyze findings and identify key themes
6. Provide a comprehensive summary

Topic: {topic}

Be thorough and cite all sources properly."""

        # Initial user message
        user_message = f"""Research this topic comprehensively: {topic}

Find authoritative sources, extract key information, and provide a well-cited summary."""

        # Start conversation
        messages = [{"role": "user", "content": user_message}]

        # Agentic loop with tool use
        research_data = {
            "sources": [],
            "citations": [],
            "key_themes": [],
            "summary": ""
        }

        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

            # Add assistant response to conversation
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Check if agent wants to use tools
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            if not tool_uses:
                # No more tools to use - extract final response
                text_blocks = [block for block in response.content if hasattr(block, 'text')]
                if text_blocks:
                    final_text = text_blocks[0].text

                    # Try to parse structured output
                    try:
                        if "```json" in final_text:
                            json_str = final_text.split("```json")[1].split("```")[0].strip()
                        else:
                            json_str = final_text

                        parsed_data = json.loads(json_str)
                        research_data.update(parsed_data)
                    except json.JSONDecodeError:
                        research_data["summary"] = final_text

                break

            # Execute tool calls
            tool_results = []

            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input

                result = None

                if tool_name == "web_search" and search_function:
                    # Execute search
                    query = tool_input.get("query", "")
                    num_results = tool_input.get("num_results", 10)

                    search_results = search_function(query, num_results)
                    result = json.dumps(search_results)

                    # Track sources
                    for source in search_results[:5]:  # Top 5 per query
                        if source not in research_data["sources"]:
                            research_data["sources"].append(source)

                elif tool_name == "extract_content" and extract_function:
                    # Extract content
                    url = tool_input.get("url", "")
                    content = extract_function(url)
                    result = json.dumps(content)

                elif tool_name == "add_citation" and citation_function:
                    # Add citation
                    citation_id = citation_function(
                        title=tool_input.get("title", ""),
                        url=tool_input.get("url", ""),
                        author=tool_input.get("author")
                    )
                    result = json.dumps({"citation_id": citation_id})
                    research_data["citations"].append(citation_id)

                else:
                    result = json.dumps({"error": f"Tool {tool_name} not implemented"})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result
                })

            # Add tool results to conversation
            messages.append({
                "role": "user",
                "content": tool_results
            })

        # Ensure we have search query
        research_data["search_query"] = topic

        return research_data


class InsightAgent:
    """
    Agent for extracting insights from research.

    Analyzes sources to identify:
    - Key insights and claims
    - Supporting evidence
    - Arguments and reasoning
    - Concept relationships
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize insight extraction agent."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def extract_insights(
        self,
        sources: List[Dict[str, Any]],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract insights from research sources.

        Args:
            sources: List of research sources with content
            focus_areas: Specific areas to focus on

        Returns:
            Insights, arguments, and concept map
        """
        # Prepare source content
        source_text = "\n\n---\n\n".join([
            f"**Source {i+1}: {s.get('title', 'Untitled')}**\n{s.get('content', s.get('snippet', ''))}"
            for i, s in enumerate(sources[:15])  # Limit for context
        ])

        focus_context = ""
        if focus_areas:
            focus_context = f"\n\nFocus particularly on these areas:\n" + "\n".join(f"- {area}" for area in focus_areas)

        system_prompt = """You are an expert research analyst. Extract key insights, identify arguments, and map conceptual relationships from the provided sources.

Return your analysis as valid JSON with this exact structure:
{
  "insights": [
    {
      "statement": "clear insight statement",
      "supporting_evidence": ["evidence from sources"],
      "confidence": 0.9,
      "sources": ["source 1", "source 2"]
    }
  ],
  "arguments": [
    {
      "claim": "main claim",
      "reasoning": "logical reasoning",
      "evidence": ["supporting evidence"],
      "counter_arguments": ["potential objections"]
    }
  ],
  "concept_map": {
    "concepts": [
      {"name": "Concept Name", "description": "what it means"}
    ],
    "relationships": [
      {"from": "Concept A", "to": "Concept B", "type": "relationship type"}
    ]
  }
}"""

        user_prompt = f"""Analyze these research sources and extract insights:{focus_context}

{source_text}

Provide comprehensive analysis as JSON."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback structure
            return {
                "insights": [],
                "arguments": [],
                "concept_map": {"concepts": [], "relationships": []}
            }


class OutlineAgent:
    """
    Agent for generating presentation outlines.

    Creates structured outlines with:
    - Multi-presentation detection
    - Slide-by-slide structure
    - Learning objectives
    - Time estimates
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize outline generation agent."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-5-20250929"

    def generate_outline(
        self,
        research_data: Dict[str, Any],
        insights_data: Dict[str, Any],
        audience: str = "general",
        duration_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Generate presentation outline(s) from research.

        Args:
            research_data: Research results
            insights_data: Extracted insights
            audience: Target audience
            duration_minutes: Target duration

        Returns:
            Outline with presentations and slides
        """
        # Assess complexity for multi-presentation detection
        num_sources = len(research_data.get("sources", []))
        num_insights = len(insights_data.get("insights", []))
        num_themes = len(research_data.get("key_themes", []))

        complexity = "simple"
        if num_sources > 15 or num_insights > 8 or num_themes > 5:
            complexity = "complex"

        target_slides = max(5, min(40, duration_minutes // 2))

        system_prompt = """You are a presentation architect expert at structuring content into compelling narratives.

Create presentation outlines that:
- Tell a clear story with logical flow
- Match audience knowledge level
- Include specific slide types (TITLE SLIDE, CONTENT, IMAGE, etc.)
- Assign content appropriately to slides
- Estimate realistic timing

For complex topics, create multiple presentations for different audiences."""

        user_prompt = f"""Generate presentation outline(s) from this research.

**Research:**
- Topic: {research_data.get('search_query', 'Unknown')}
- Sources: {num_sources}
- Key Themes: {', '.join(research_data.get('key_themes', [])[:7])}

**Insights:** {num_insights} key insights identified

**Complexity:** {complexity}

**Parameters:**
- Audience: {audience}
- Duration: {duration_minutes} minutes
- Target slides: {target_slides}

**Multi-Presentation Strategy:**
If complex, create 2-3 presentations:
1. Executive overview (high-level, visual)
2. Detailed presentation (comprehensive)
3. Technical deep-dive (data/process heavy)

Return as JSON:
{{
  "presentation_count": 1,
  "presentations": [
    {{
      "title": "Presentation Title",
      "audience": "audience type",
      "subtitle": "engaging subtitle",
      "slides": [
        {{
          "slide_number": 1,
          "slide_type": "TITLE SLIDE",
          "title": "Slide Title",
          "purpose": "What this slide accomplishes",
          "key_points": ["point 1", "point 2"],
          "supporting_sources": ["cite-001"]
        }}
      ],
      "estimated_duration": {duration_minutes}
    }}
  ]
}}

Slide types: TITLE SLIDE, SECTION DIVIDER, CONTENT, IMAGE, PROBLEM STATEMENT,
INSIGHT, FRAMEWORK, COMPARISON, DEEP DIVE, ACTION, CONCLUSION"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=16384,
            temperature=0.8,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse response
        response_text = response.content[0].text

        try:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback
            return {
                "presentation_count": 1,
                "presentations": [{
                    "title": research_data.get("search_query", "Presentation"),
                    "audience": audience,
                    "slides": [],
                    "estimated_duration": duration_minutes
                }]
            }


# Convenience functions
def get_research_agent() -> ResearchAgent:
    """Get configured research agent."""
    return ResearchAgent()


def get_insight_agent() -> InsightAgent:
    """Get configured insight agent."""
    return InsightAgent()


def get_outline_agent() -> OutlineAgent:
    """Get configured outline agent."""
    return OutlineAgent()
