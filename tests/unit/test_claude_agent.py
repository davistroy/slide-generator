"""
Unit tests for plugin/lib/claude_agent.py

Tests the Claude Agent SDK integration for research, insight extraction,
and outline generation.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from plugin.lib.claude_agent import (
    InsightAgent,
    OutlineAgent,
    ResearchAgent,
    get_insight_agent,
    get_outline_agent,
    get_research_agent,
)


# ==============================================================================
# Test ResearchAgent
# ==============================================================================


class TestResearchAgentInit:
    """Tests for ResearchAgent initialization."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_api_key(self, mock_anthropic):
        """Test initialization with explicit API key."""
        agent = ResearchAgent(api_key="test-api-key")
        assert agent.api_key == "test-api-key"
        mock_anthropic.assert_called_once_with(api_key="test-api-key")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-api-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_env_var(self, mock_anthropic):
        """Test initialization with environment variable."""
        agent = ResearchAgent()
        assert agent.api_key == "env-api-key"
        mock_anthropic.assert_called_once_with(api_key="env-api-key")

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key_raises(self):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            ResearchAgent()

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_sets_model(self, mock_anthropic):
        """Test initialization sets correct model."""
        agent = ResearchAgent(api_key="test-key")
        assert agent.model == "claude-sonnet-4-5-20250929"
        assert agent.conversation_history == []


class TestResearchAgentTools:
    """Tests for ResearchAgent tool creation."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_create_search_tool(self, mock_anthropic):
        """Test search tool definition."""
        agent = ResearchAgent(api_key="test-key")
        tool = agent._create_search_tool()

        assert tool["name"] == "web_search"
        assert "query" in tool["input_schema"]["properties"]
        assert "num_results" in tool["input_schema"]["properties"]
        assert tool["input_schema"]["required"] == ["query"]

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_create_extract_content_tool(self, mock_anthropic):
        """Test content extraction tool definition."""
        agent = ResearchAgent(api_key="test-key")
        tool = agent._create_extract_content_tool()

        assert tool["name"] == "extract_content"
        assert "url" in tool["input_schema"]["properties"]
        assert tool["input_schema"]["required"] == ["url"]

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_create_citation_tool(self, mock_anthropic):
        """Test citation tool definition."""
        agent = ResearchAgent(api_key="test-key")
        tool = agent._create_citation_tool()

        assert tool["name"] == "add_citation"
        assert "title" in tool["input_schema"]["properties"]
        assert "url" in tool["input_schema"]["properties"]
        assert tool["input_schema"]["required"] == ["title", "url"]


class TestResearchAgentConductResearch:
    """Tests for ResearchAgent.conduct_research method."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_no_tool_use(self, mock_anthropic):
        """Test research when agent doesn't use tools."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Create a mock response with no tool use
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = '{"key_themes": ["theme1"], "summary": "Test summary"}'

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]

        mock_client.messages.create.return_value = mock_response

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic")

        assert result["search_query"] == "test topic"
        assert "summary" in result

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_with_search_tool(self, mock_anthropic):
        """Test research with search tool use."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # First response with tool use
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "web_search"
        mock_tool_use.id = "tool-123"
        mock_tool_use.input = {"query": "test query", "num_results": 5}

        mock_response1 = MagicMock()
        mock_response1.content = [mock_tool_use]

        # Second response with final text
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = '{"summary": "Research complete"}'

        mock_response2 = MagicMock()
        mock_response2.content = [mock_text_block]

        mock_client.messages.create.side_effect = [mock_response1, mock_response2]

        # Mock search function
        def mock_search(query, num_results):
            return [{"title": "Result 1", "url": "http://example.com"}]

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic", search_function=mock_search)

        assert len(result["sources"]) > 0
        assert result["search_query"] == "test topic"

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_with_extract_tool(self, mock_anthropic):
        """Test research with content extraction tool use."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Tool use response
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "extract_content"
        mock_tool_use.id = "tool-456"
        mock_tool_use.input = {"url": "http://example.com/page"}

        mock_response1 = MagicMock()
        mock_response1.content = [mock_tool_use]

        # Final response
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = '{"summary": "Extracted content"}'

        mock_response2 = MagicMock()
        mock_response2.content = [mock_text_block]

        mock_client.messages.create.side_effect = [mock_response1, mock_response2]

        def mock_extract(url):
            return {"text": "Page content", "url": url}

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic", extract_function=mock_extract)

        assert result["search_query"] == "test topic"

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_with_citation_tool(self, mock_anthropic):
        """Test research with citation tool use."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Tool use response
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "add_citation"
        mock_tool_use.id = "tool-789"
        mock_tool_use.input = {"title": "Source Title", "url": "http://example.com"}

        mock_response1 = MagicMock()
        mock_response1.content = [mock_tool_use]

        # Final response
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = '{"summary": "Citation added"}'

        mock_response2 = MagicMock()
        mock_response2.content = [mock_text_block]

        mock_client.messages.create.side_effect = [mock_response1, mock_response2]

        def mock_citation(title, url, author=None):
            return "cite-001"

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic", citation_function=mock_citation)

        assert "cite-001" in result["citations"]

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_unimplemented_tool(self, mock_anthropic):
        """Test research with unimplemented tool (no function provided)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Tool use response for search without search_function
        mock_tool_use = MagicMock()
        mock_tool_use.type = "tool_use"
        mock_tool_use.name = "web_search"
        mock_tool_use.id = "tool-101"
        mock_tool_use.input = {"query": "test"}

        mock_response1 = MagicMock()
        mock_response1.content = [mock_tool_use]

        # Final response
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = '{"summary": "Done"}'

        mock_response2 = MagicMock()
        mock_response2.content = [mock_text_block]

        mock_client.messages.create.side_effect = [mock_response1, mock_response2]

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic")  # No functions provided

        assert result["search_query"] == "test topic"

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_json_in_markdown(self, mock_anthropic):
        """Test parsing JSON wrapped in markdown code block."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = """```json
{"key_themes": ["theme1", "theme2"], "summary": "Markdown wrapped JSON"}
```"""

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic")

        assert "theme1" in result["key_themes"]
        assert result["summary"] == "Markdown wrapped JSON"

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_conduct_research_invalid_json_fallback(self, mock_anthropic):
        """Test fallback when response is not valid JSON."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "This is just plain text, not JSON"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = ResearchAgent(api_key="test-key")
        result = agent.conduct_research("test topic")

        assert result["summary"] == "This is just plain text, not JSON"


# ==============================================================================
# Test InsightAgent
# ==============================================================================


class TestInsightAgentInit:
    """Tests for InsightAgent initialization."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_api_key(self, mock_anthropic):
        """Test initialization with explicit API key."""
        agent = InsightAgent(api_key="test-api-key")
        assert agent.api_key == "test-api-key"
        mock_anthropic.assert_called_once_with(api_key="test-api-key")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_env_var(self, mock_anthropic):
        """Test initialization with environment variable."""
        agent = InsightAgent()
        assert agent.api_key == "env-key"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key_raises(self):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            InsightAgent()


class TestInsightAgentExtractInsights:
    """Tests for InsightAgent.extract_insights method."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_extract_insights_basic(self, mock_anthropic):
        """Test basic insight extraction."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps(
            {
                "insights": [{"statement": "Key insight", "confidence": 0.9}],
                "arguments": [],
                "concept_map": {"concepts": [], "relationships": []},
            }
        )

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = InsightAgent(api_key="test-key")
        sources = [{"title": "Source 1", "content": "Some content"}]
        result = agent.extract_insights(sources)

        assert len(result["insights"]) > 0
        assert result["insights"][0]["statement"] == "Key insight"

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_extract_insights_with_focus_areas(self, mock_anthropic):
        """Test insight extraction with focus areas."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps(
            {
                "insights": [{"statement": "Focused insight", "confidence": 0.85}],
                "arguments": [],
                "concept_map": {"concepts": [], "relationships": []},
            }
        )

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = InsightAgent(api_key="test-key")
        sources = [{"title": "Source 1", "snippet": "Some snippet"}]
        result = agent.extract_insights(sources, focus_areas=["technology", "trends"])

        assert "insights" in result

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_extract_insights_json_in_markdown(self, mock_anthropic):
        """Test parsing JSON in markdown code block."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = """```json
{"insights": [], "arguments": [], "concept_map": {"concepts": [], "relationships": []}}
```"""

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = InsightAgent(api_key="test-key")
        result = agent.extract_insights([])

        assert "insights" in result

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_extract_insights_plain_code_block(self, mock_anthropic):
        """Test parsing JSON in plain code block (no json marker)."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = """```
{"insights": [{"statement": "Test"}], "arguments": [], "concept_map": {"concepts": [], "relationships": []}}
```"""

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = InsightAgent(api_key="test-key")
        result = agent.extract_insights([])

        assert "insights" in result

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_extract_insights_invalid_json_fallback(self, mock_anthropic):
        """Test fallback when response is not valid JSON."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = "Not valid JSON at all"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = InsightAgent(api_key="test-key")
        result = agent.extract_insights([])

        # Should return fallback structure
        assert result["insights"] == []
        assert result["arguments"] == []
        assert result["concept_map"]["concepts"] == []


# ==============================================================================
# Test OutlineAgent
# ==============================================================================


class TestOutlineAgentInit:
    """Tests for OutlineAgent initialization."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_api_key(self, mock_anthropic):
        """Test initialization with explicit API key."""
        agent = OutlineAgent(api_key="test-api-key")
        assert agent.api_key == "test-api-key"
        mock_anthropic.assert_called_once_with(api_key="test-api-key")

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "env-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_init_with_env_var(self, mock_anthropic):
        """Test initialization with environment variable."""
        agent = OutlineAgent()
        assert agent.api_key == "env-key"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key_raises(self):
        """Test initialization without API key raises ValueError."""
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            OutlineAgent()


class TestOutlineAgentGenerateOutline:
    """Tests for OutlineAgent.generate_outline method."""

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_generate_outline_simple_topic(self, mock_anthropic):
        """Test outline generation for simple topic."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps(
            {
                "presentation_count": 1,
                "presentations": [
                    {
                        "title": "Test Presentation",
                        "audience": "general",
                        "slides": [{"slide_number": 1, "title": "Title Slide"}],
                        "estimated_duration": 30,
                    }
                ],
            }
        )

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = OutlineAgent(api_key="test-key")
        research_data = {"search_query": "Test Topic", "sources": [], "key_themes": []}
        insights_data = {"insights": []}

        result = agent.generate_outline(research_data, insights_data)

        assert result["presentation_count"] == 1
        assert len(result["presentations"]) == 1

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_generate_outline_complex_topic(self, mock_anthropic):
        """Test outline generation for complex topic with multiple presentations."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = json.dumps(
            {
                "presentation_count": 2,
                "presentations": [
                    {
                        "title": "Executive Overview",
                        "audience": "executives",
                        "slides": [],
                        "estimated_duration": 15,
                    },
                    {
                        "title": "Detailed Analysis",
                        "audience": "technical",
                        "slides": [],
                        "estimated_duration": 45,
                    },
                ],
            }
        )

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = OutlineAgent(api_key="test-key")
        research_data = {
            "search_query": "Complex Topic",
            "sources": [{"title": f"Source {i}"} for i in range(20)],  # Many sources
            "key_themes": [
                "Theme 1",
                "Theme 2",
                "Theme 3",
                "Theme 4",
                "Theme 5",
                "Theme 6",
            ],
        }
        insights_data = {"insights": [{"statement": f"Insight {i}"} for i in range(10)]}

        result = agent.generate_outline(
            research_data, insights_data, audience="executives", duration_minutes=60
        )

        assert result["presentation_count"] == 2

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_generate_outline_json_in_markdown(self, mock_anthropic):
        """Test parsing JSON in markdown code block."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = """```json
{"presentation_count": 1, "presentations": [{"title": "Test", "audience": "general", "slides": [], "estimated_duration": 30}]}
```"""

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = OutlineAgent(api_key="test-key")
        result = agent.generate_outline({"search_query": "Test"}, {"insights": []})

        assert result["presentation_count"] == 1

    @patch("plugin.lib.claude_agent.Anthropic")
    def test_generate_outline_invalid_json_fallback(self, mock_anthropic):
        """Test fallback when response is not valid JSON."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_text_block = MagicMock()
        mock_text_block.text = "Not valid JSON"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_client.messages.create.return_value = mock_response

        agent = OutlineAgent(api_key="test-key")
        result = agent.generate_outline(
            {"search_query": "Test Topic"},
            {"insights": []},
            audience="developers",
            duration_minutes=45,
        )

        # Should return fallback structure
        assert result["presentation_count"] == 1
        assert result["presentations"][0]["title"] == "Test Topic"
        assert result["presentations"][0]["audience"] == "developers"


# ==============================================================================
# Test Convenience Functions
# ==============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_get_research_agent(self, mock_anthropic):
        """Test get_research_agent factory function."""
        agent = get_research_agent()
        assert isinstance(agent, ResearchAgent)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_get_insight_agent(self, mock_anthropic):
        """Test get_insight_agent factory function."""
        agent = get_insight_agent()
        assert isinstance(agent, InsightAgent)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("plugin.lib.claude_agent.Anthropic")
    def test_get_outline_agent(self, mock_anthropic):
        """Test get_outline_agent factory function."""
        agent = get_outline_agent()
        assert isinstance(agent, OutlineAgent)
