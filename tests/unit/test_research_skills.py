"""
Unit tests for research skills.

Tests ResearchSkill, InsightExtractionSkill, OutlineSkill, and ResearchAssistantSkill.
"""

import pytest
from plugin.skills.research_skill import ResearchSkill
from plugin.skills.insight_extraction_skill import InsightExtractionSkill
from plugin.skills.outline_skill import OutlineSkill
from plugin.skills.research_assistant_skill import ResearchAssistantSkill
from plugin.base_skill import SkillInput, SkillOutput


class TestResearchSkill:
    """Tests for ResearchSkill."""

    def test_skill_properties(self):
        """Test skill properties."""
        skill = ResearchSkill()

        assert skill.skill_id == "research"
        assert skill.display_name == "Web Research"
        assert len(skill.description) > 0

    def test_validate_input_valid(self):
        """Test input validation with valid data."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={"topic": "test topic"},
            context={},
            config={}
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_input_missing_topic(self):
        """Test validation with missing topic."""
        skill = ResearchSkill()

        input_data = SkillInput(data={}, context={}, config={})

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert any("topic" in error.lower() for error in errors)

    def test_validate_input_invalid_search_depth(self):
        """Test validation with invalid search depth."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={"topic": "test", "search_depth": "invalid"},
            context={},
            config={}
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False

    def test_execute_basic_research(self):
        """Test basic research execution."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={"topic": "artificial intelligence"},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert "sources" in output.data
        assert "summary" in output.data
        assert "key_themes" in output.data
        assert "citations" in output.data

    def test_execute_with_context(self):
        """Test research with additional context."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={
                "topic": "AI",
                "context": "focus on healthcare applications"
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert "search_query" in output.data

    def test_execute_with_max_sources(self):
        """Test research with max sources limit."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={
                "topic": "test",
                "max_sources": 5
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert len(output.data["sources"]) <= 5

    def test_execute_quick_search_depth(self):
        """Test quick search depth."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={
                "topic": "test",
                "search_depth": "quick"
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True

    def test_execute_comprehensive_search_depth(self):
        """Test comprehensive search depth."""
        skill = ResearchSkill()

        input_data = SkillInput(
            data={
                "topic": "test",
                "search_depth": "comprehensive"
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True

    def test_cleanup(self):
        """Test cleanup method."""
        skill = ResearchSkill()

        # Should not raise error
        skill.cleanup()


class TestInsightExtractionSkill:
    """Tests for InsightExtractionSkill."""

    def test_skill_properties(self):
        """Test skill properties."""
        skill = InsightExtractionSkill()

        assert skill.skill_id == "extract-insights"
        assert skill.display_name == "Insight Extraction"

    def test_validate_input_valid(self):
        """Test validation with valid input."""
        skill = InsightExtractionSkill()

        input_data = SkillInput(
            data={"research_output": {"sources": []}},
            context={},
            config={}
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True

    def test_validate_input_missing_research(self):
        """Test validation with missing research output."""
        skill = InsightExtractionSkill()

        input_data = SkillInput(data={}, context={}, config={})

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False

    def test_execute_extract_insights(self):
        """Test insight extraction."""
        skill = InsightExtractionSkill()

        research_output = {
            "sources": [
                {
                    "title": "Test Article",
                    "content": "Research shows that AI is important. The study finds that ML is useful.",
                    "snippet": "AI research",
                    "citation_id": "cite-001"
                }
            ]
        }

        input_data = SkillInput(
            data={"research_output": research_output},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert "insights" in output.data
        assert "arguments" in output.data
        assert "concept_map" in output.data

    def test_execute_with_focus_areas(self):
        """Test extraction with focus areas."""
        skill = InsightExtractionSkill()

        research_output = {
            "sources": [
                {"title": "Test", "content": "Content", "snippet": "snippet", "citation_id": "c1"}
            ]
        }

        input_data = SkillInput(
            data={
                "research_output": research_output,
                "focus_areas": ["technology", "healthcare"]
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True

    def test_concept_map_structure(self):
        """Test concept map structure."""
        skill = InsightExtractionSkill()

        research_output = {
            "sources": [
                {"title": "Test", "content": "Content about Machine Learning.", "snippet": "ML", "citation_id": "c1"}
            ]
        }

        input_data = SkillInput(
            data={"research_output": research_output},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        concept_map = output.data["concept_map"]
        assert "concepts" in concept_map
        assert "relationships" in concept_map


class TestOutlineSkill:
    """Tests for OutlineSkill."""

    def test_skill_properties(self):
        """Test skill properties."""
        skill = OutlineSkill()

        assert skill.skill_id == "outline"
        assert skill.display_name == "Outline Generation"

    def test_validate_input_valid(self):
        """Test validation with valid input."""
        skill = OutlineSkill()

        input_data = SkillInput(
            data={"research": {"sources": []}},
            context={},
            config={}
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True

    def test_validate_input_missing_research(self):
        """Test validation with missing research."""
        skill = OutlineSkill()

        input_data = SkillInput(data={}, context={}, config={})

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False

    def test_execute_single_presentation(self):
        """Test generating single presentation."""
        skill = OutlineSkill()

        research = {
            "search_query": "test topic",
            "sources": [
                {"title": "Source 1", "content": "content", "citation_id": "c1"}
            ],
            "key_themes": ["theme1", "theme2"]
        }

        input_data = SkillInput(
            data={"research": research},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["presentation_count"] == 1
        assert len(output.data["presentations"]) == 1

    def test_execute_multiple_presentations(self):
        """Test generating multiple presentations for complex topic."""
        skill = OutlineSkill()

        # Create complex research (many sources)
        sources = [
            {"title": f"Source {i}", "content": "content", "citation_id": f"c{i}"}
            for i in range(20)
        ]

        research = {
            "search_query": "complex topic",
            "sources": sources,
            "key_themes": ["t1", "t2", "t3", "t4", "t5"]
        }

        insights = {
            "insights_count": 10
        }

        input_data = SkillInput(
            data={
                "research": research,
                "insights": insights
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["presentation_count"] > 1

    def test_execute_with_audience(self):
        """Test outline with specific audience."""
        skill = OutlineSkill()

        research = {
            "search_query": "test",
            "sources": [],
            "key_themes": ["theme"]
        }

        input_data = SkillInput(
            data={
                "research": research,
                "audience": "technical"
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True

    def test_execute_with_duration(self):
        """Test outline with duration constraint."""
        skill = OutlineSkill()

        research = {
            "search_query": "test",
            "sources": [],
            "key_themes": ["t1", "t2", "t3"]
        }

        input_data = SkillInput(
            data={
                "research": research,
                "duration_minutes": 10
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        presentation = output.data["presentations"][0]
        assert presentation["estimated_duration"] >= 10

    def test_presentation_structure(self):
        """Test presentation structure."""
        skill = OutlineSkill()

        research = {
            "search_query": "test",
            "sources": [],
            "key_themes": ["theme1"]
        }

        input_data = SkillInput(
            data={"research": research},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        presentation = output.data["presentations"][0]
        assert "audience" in presentation
        assert "title" in presentation
        assert "slides" in presentation
        assert len(presentation["slides"]) > 0

        # Check slide structure
        slide = presentation["slides"][0]
        assert "slide_number" in slide
        assert "slide_type" in slide
        assert "title" in slide
        assert "purpose" in slide


class TestResearchAssistantSkill:
    """Tests for ResearchAssistantSkill."""

    def test_skill_properties(self):
        """Test skill properties."""
        skill = ResearchAssistantSkill()

        assert skill.skill_id == "research-assistant"
        assert skill.display_name == "Research Assistant"

    def test_validate_input_valid(self):
        """Test validation with valid input."""
        skill = ResearchAssistantSkill()

        input_data = SkillInput(
            data={"topic": "test topic"},
            context={},
            config={}
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True

    def test_validate_input_missing_topic(self):
        """Test validation with missing topic."""
        skill = ResearchAssistantSkill()

        input_data = SkillInput(data={}, context={}, config={})

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False

    def test_execute_generate_questions(self):
        """Test generating clarifying questions."""
        skill = ResearchAssistantSkill()

        input_data = SkillInput(
            data={"topic": "artificial intelligence"},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert "questions" in output.data
        assert len(output.data["questions"]) > 0
        assert output.data["ready_for_research"] is False

    def test_execute_with_responses(self):
        """Test with user responses."""
        skill = ResearchAssistantSkill()

        user_responses = {
            "audience": "Technical audience",
            "objective": "Inform and educate",
            "depth": "Standard coverage",
            "focus": "machine learning applications",
            "constraints": "No specific constraints"
        }

        input_data = SkillInput(
            data={
                "topic": "AI",
                "user_responses": user_responses
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["ready_for_research"] is True
        assert "refined_params" in output.data

    def test_refined_parameters(self):
        """Test refined parameters structure."""
        skill = ResearchAssistantSkill()

        user_responses = {
            "audience": "Executives",
            "depth": "Quick overview"
        }

        input_data = SkillInput(
            data={
                "topic": "test",
                "user_responses": user_responses
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        params = output.data["refined_params"]
        assert "topic" in params
        assert "audience" in params
        assert "depth" in params
        assert params["audience"] == "executive"
        assert params["depth"] == "quick"

    def test_question_structure(self):
        """Test question structure."""
        skill = ResearchAssistantSkill()

        input_data = SkillInput(
            data={"topic": "test"},
            context={},
            config={}
        )

        output = skill.execute(input_data)

        question = output.data["questions"][0]
        assert "id" in question
        assert "question" in question
        assert "options" in question

    def test_questions_answered_count(self):
        """Test questions answered count."""
        skill = ResearchAssistantSkill()

        user_responses = {
            "audience": "General",
            "objective": "Inform"
        }

        input_data = SkillInput(
            data={
                "topic": "test",
                "user_responses": user_responses
            },
            context={},
            config={}
        )

        output = skill.execute(input_data)

        assert "questions_answered" in output.data
        assert "total_questions" in output.data
        assert output.data["questions_answered"] <= output.data["total_questions"]
