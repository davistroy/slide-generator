"""
Unit tests for plugin/skills/content/content_optimization_skill.py

Tests the ContentOptimizationSkill class and its methods.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from plugin.base_skill import SkillInput, SkillStatus
from plugin.skills.content.content_optimization_skill import (
    ContentOptimizationSkill,
    get_content_optimization_skill,
)


class TestContentOptimizationSkillProperties:
    """Tests for ContentOptimizationSkill properties."""

    def test_skill_id(self):
        """Test skill_id property returns correct value."""
        skill = ContentOptimizationSkill()
        assert skill.skill_id == "optimize-content"

    def test_display_name(self):
        """Test display_name property returns correct value."""
        skill = ContentOptimizationSkill()
        assert skill.display_name == "Content Optimization"

    def test_description(self):
        """Test description property returns non-empty string."""
        skill = ContentOptimizationSkill()
        assert len(skill.description) > 0
        assert "optimization" in skill.description.lower() or "quality" in skill.description.lower()

    def test_skill_inherits_from_base_skill(self):
        """Test skill inherits from BaseSkill."""
        from plugin.base_skill import BaseSkill
        skill = ContentOptimizationSkill()
        assert isinstance(skill, BaseSkill)


class TestContentOptimizationSkillValidation:
    """Tests for input validation."""

    def test_validate_input_with_slides(self):
        """Test validation passes with slides in input."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={"slides": [{"title": "Test Slide", "bullets": ["Point 1"]}]},
            context={},
            config={},
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_with_presentation_file(self):
        """Test validation passes with presentation_file in input."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={"presentation_file": "presentation.md"},
            context={},
            config={},
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_with_both_slides_and_file(self):
        """Test validation passes when both slides and file are present."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={
                "slides": [{"title": "Test"}],
                "presentation_file": "presentation.md"
            },
            context={},
            config={},
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_missing_required_data(self):
        """Test validation fails when neither slides nor file is provided."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={},
            context={},
            config={},
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_with_only_style_guide(self):
        """Test validation fails with only style_guide (no slides or file)."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={"style_guide": {"tone": "professional"}},
            context={},
            config={},
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_empty_slides_list(self):
        """Test validation passes even with empty slides list."""
        skill = ContentOptimizationSkill()
        input_data = SkillInput(
            data={"slides": []},
            context={},
            config={},
        )
        # Empty list still has 'slides' key
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []


class TestContentOptimizationSkillExecute:
    """Tests for the execute method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_with_slides_success(self, mock_analyzer_class, mock_get_client):
        """Test successful execution with slides input."""
        # Set up mocks
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.return_value = {
            "overall_score": 75.0,
            "issues": [],
            "recommendations": [],
        }
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slides = [
            {"title": "Test Slide", "bullets": ["Point 1", "Point 2"], "markdown": "## Test\n\n- Point 1\n"}
        ]
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": slides,
                "output_file": output_file,
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.status == SkillStatus.SUCCESS
        assert "optimized_file" in output.data
        assert "quality_score_before" in output.data
        assert "quality_score_after" in output.data
        assert output_file in output.artifacts

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_generates_default_output_filename(self, mock_analyzer_class, mock_get_client):
        """Test execute generates default output filename when not provided."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.return_value = {
            "overall_score": 80.0,
            "issues": [],
            "recommendations": [],
        }
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test"}],
                "presentation_file": "my_presentation.md",
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["optimized_file"] == "my_presentation_optimized.md"

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_includes_quality_improvement(self, mock_analyzer_class, mock_get_client):
        """Test execute calculates quality improvement."""
        mock_analyzer = MagicMock()
        # First call (initial) returns 60, second call (final) returns 85
        mock_analyzer.analyze_presentation.side_effect = [
            {"overall_score": 60.0, "issues": []},
            {"overall_score": 85.0, "issues": []},
        ]
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test"}],
                "output_file": output_file,
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["quality_score_before"] == 60.0
        assert output.data["quality_score_after"] == 85.0
        assert output.data["quality_improvement"] == 25.0

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_with_style_guide(self, mock_analyzer_class, mock_get_client):
        """Test execute passes style_guide to analyzer."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.return_value = {
            "overall_score": 75.0,
            "issues": [],
        }
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        style_guide = {"tone": "professional", "max_words_per_bullet": 12}

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test"}],
                "output_file": output_file,
                "style_guide": style_guide,
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        # Verify analyzer was called with style_guide
        mock_analyzer.analyze_presentation.assert_called()
        call_args = mock_analyzer.analyze_presentation.call_args
        assert call_args[0][1] == style_guide or call_args[1].get("style_guide") == style_guide

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_with_custom_optimization_goals(self, mock_analyzer_class, mock_get_client):
        """Test execute uses custom optimization_goals when provided."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.return_value = {
            "overall_score": 75.0,
            "issues": [
                {"slide_number": 1, "type": "readability", "message": "Complex text"}
            ],
        }
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test", "bullets": ["Point"]}],
                "output_file": output_file,
                "optimization_goals": ["readability", "parallelism"],
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_execute_metadata_contains_counts(self, mock_analyzer_class, mock_get_client):
        """Test execute includes metadata with slide and improvement counts."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.return_value = {
            "overall_score": 80.0,
            "issues": [],
        }
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": [
                    {"title": "Slide 1"},
                    {"title": "Slide 2"},
                ],
                "output_file": output_file,
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert "slides_optimized" in output.metadata
        assert output.metadata["slides_optimized"] == 2
        assert "improvements_count" in output.metadata


class TestLoadSlidesFromFile:
    """Tests for _load_slides_from_file method."""

    def test_load_slides_from_file_returns_empty_list(self):
        """Test _load_slides_from_file returns empty list (stub implementation)."""
        skill = ContentOptimizationSkill()
        result = skill._load_slides_from_file("nonexistent.md")
        assert result == []


class TestOptimizeSlides:
    """Tests for _optimize_slides method."""

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slides_no_issues(self, mock_get_client):
        """Test _optimize_slides keeps slides as-is when no issues."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slides = [
            {"title": "Slide 1", "bullets": ["Point 1"]},
            {"title": "Slide 2", "bullets": ["Point 2"]},
        ]
        analysis = {"issues": []}  # No issues

        optimized, improvements = skill._optimize_slides(
            slides=slides,
            analysis=analysis,
            optimization_goals=["readability"],
            style_guide={},
            client=mock_client,
        )

        assert len(optimized) == 2
        assert len(improvements) == 0
        # Slides should be unchanged
        assert optimized[0] == slides[0]
        assert optimized[1] == slides[1]

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slides_with_issues(self, mock_get_client):
        """Test _optimize_slides processes slides with issues."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. Improved point one\n2. Improved point two"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slides = [
            {"title": "Slide 1", "bullets": ["Point one", "Point two"]},
        ]
        analysis = {
            "issues": [
                {"slide_number": 1, "type": "structure", "message": "Not parallel"}
            ]
        }

        optimized, improvements = skill._optimize_slides(
            slides=slides,
            analysis=analysis,
            optimization_goals=["readability"],
            style_guide={},
            client=mock_client,
        )

        assert len(optimized) == 1
        # Should have attempted optimization via Claude client
        assert mock_client.generate_text.called

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slides_filters_issues_by_slide_number(self, mock_get_client):
        """Test _optimize_slides correctly filters issues per slide."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slides = [
            {"title": "Slide 1", "bullets": ["Point 1"]},
            {"title": "Slide 2", "bullets": ["Point 2"]},
            {"title": "Slide 3", "bullets": ["Point 3"]},
        ]
        # Only slide 2 has issues
        analysis = {
            "issues": [
                {"slide_number": 2, "type": "structure", "message": "Issue on slide 2"}
            ]
        }

        optimized, improvements = skill._optimize_slides(
            slides=slides,
            analysis=analysis,
            optimization_goals=["readability"],
            style_guide={},
            client=mock_client,
        )

        assert len(optimized) == 3
        # Slide 1 and 3 should be unchanged
        assert optimized[0] == slides[0]
        assert optimized[2] == slides[2]


class TestOptimizeSlide:
    """Tests for _optimize_slide method."""

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slide_with_bullets_and_structure_issues(self, mock_get_client):
        """Test _optimize_slide handles bullet optimization for structure issues."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. First improved bullet\n2. Second improved bullet"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slide = {
            "title": "Test Slide",
            "bullets": ["First bullet", "Second bullet"],
        }
        issues = [
            {"type": "structure", "message": "Bullets not parallel"}
        ]

        optimized, improvements = skill._optimize_slide(
            slide=slide,
            slide_number=1,
            issues=issues,
            optimization_goals=["parallelism"],
            style_guide={"max_words_per_bullet": 15},
            client=mock_client,
        )

        assert "bullets" in optimized
        # Client should have been called to optimize bullets
        assert mock_client.generate_text.called

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slide_with_readability_issues(self, mock_get_client):
        """Test _optimize_slide handles readability issues."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. Simple point\n2. Clear message"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slide = {
            "title": "Test Slide",
            "bullets": ["Complex convoluted point", "Another difficult text"],
        }
        issues = [
            {"type": "readability", "message": "Text too complex"}
        ]

        optimized, improvements = skill._optimize_slide(
            slide=slide,
            slide_number=1,
            issues=issues,
            optimization_goals=["readability"],
            style_guide={},
            client=mock_client,
        )

        assert mock_client.generate_text.called

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slide_with_graphics_description(self, mock_get_client):
        """Test _optimize_slide handles graphics description optimization."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "A detailed visualization showing data trends with blue bars and clear labels."
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slide = {
            "title": "Data Overview",
            "graphics_description": "Some vague picture of data.",
        }
        issues = [
            {"message": "Graphics description too vague"}
        ]

        optimized, improvements = skill._optimize_slide(
            slide=slide,
            slide_number=1,
            issues=issues,
            optimization_goals=["graphics"],
            style_guide={},
            client=mock_client,
        )

        assert "graphics_description" in optimized
        # Graphics should have been updated
        assert mock_client.generate_text.called

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slide_no_bullets(self, mock_get_client):
        """Test _optimize_slide handles slide without bullets."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slide = {
            "title": "Title Slide",
            # No bullets
        }
        issues = [
            {"type": "structure", "message": "Some issue"}
        ]

        optimized, improvements = skill._optimize_slide(
            slide=slide,
            slide_number=1,
            issues=issues,
            optimization_goals=["parallelism"],
            style_guide={},
            client=mock_client,
        )

        # Should not crash, should return slide as-is for bullets
        assert optimized["title"] == "Title Slide"

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_slide_empty_bullets(self, mock_get_client):
        """Test _optimize_slide handles slide with empty bullets list."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        slide = {
            "title": "Empty Slide",
            "bullets": [],
        }
        issues = [
            {"type": "structure", "message": "No content"}
        ]

        optimized, improvements = skill._optimize_slide(
            slide=slide,
            slide_number=1,
            issues=issues,
            optimization_goals=["parallelism"],
            style_guide={},
            client=mock_client,
        )

        assert optimized["bullets"] == []


class TestOptimizeBullets:
    """Tests for _optimize_bullets method."""

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_success(self, mock_get_client):
        """Test _optimize_bullets successfully improves bullets."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. Improved first bullet\n2. Improved second bullet"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["Original first bullet", "Original second bullet"]
        issues = [{"type": "structure", "message": "Not parallel"}]

        improved, improvements = skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide={"max_words_per_bullet": 15, "tone": "professional"},
            client=mock_client,
        )

        assert len(improved) == 2
        assert improved[0] == "Improved first bullet"
        assert improved[1] == "Improved second bullet"

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_logs_improvements(self, mock_get_client):
        """Test _optimize_bullets logs improvements when bullets change."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. New first\n2. New second"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["Old first", "Old second"]
        issues = [{"type": "structure", "message": "Issue"}]

        improved, improvements = skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide={},
            client=mock_client,
        )

        # Should have logged improvements
        assert len(improvements) == 2
        assert all(imp["issue_type"] == "bullet_improvement" for imp in improvements)
        assert all("original" in imp for imp in improvements)
        assert all("improved" in imp for imp in improvements)

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_returns_originals_on_parsing_failure(self, mock_get_client):
        """Test _optimize_bullets returns originals when response parsing fails."""
        mock_client = MagicMock()
        # Response that doesn't match expected format
        mock_client.generate_text.return_value = "Some unparseable response"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["Original one", "Original two"]
        issues = [{"type": "structure", "message": "Issue"}]

        improved, improvements = skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide={},
            client=mock_client,
        )

        # Should return originals since parsing failed (count mismatch)
        assert improved == bullets
        assert improvements == []

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_returns_originals_on_count_mismatch(self, mock_get_client):
        """Test _optimize_bullets returns originals when bullet count doesn't match."""
        mock_client = MagicMock()
        # Returns only 2 bullets when 3 were expected
        mock_client.generate_text.return_value = "1. First\n2. Second"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["One", "Two", "Three"]
        issues = [{"type": "structure", "message": "Issue"}]

        improved, improvements = skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide={},
            client=mock_client,
        )

        # Should return originals since count doesn't match
        assert improved == bullets
        assert improvements == []

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_returns_originals_on_exception(self, mock_get_client):
        """Test _optimize_bullets returns originals when API call fails."""
        mock_client = MagicMock()
        mock_client.generate_text.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["Original one", "Original two"]
        issues = [{"type": "structure", "message": "Issue"}]

        improved, improvements = skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide={},
            client=mock_client,
        )

        # Should return originals on exception
        assert improved == bullets
        assert improvements == []

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_bullets_uses_style_guide(self, mock_get_client):
        """Test _optimize_bullets incorporates style_guide in prompt."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. Bullet one\n2. Bullet two"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        bullets = ["Test one", "Test two"]
        issues = [{"type": "structure", "message": "Issue"}]
        style_guide = {"max_words_per_bullet": 10, "tone": "conversational"}

        skill._optimize_bullets(
            bullets=bullets,
            issues=issues,
            style_guide=style_guide,
            client=mock_client,
        )

        # Verify the prompt includes style guide values
        call_args = mock_client.generate_text.call_args
        prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert "10" in prompt  # max_words_per_bullet
        assert "Conversational" in prompt  # tone (capitalized)


class TestOptimizeGraphicsDescription:
    """Tests for _optimize_graphics_description method."""

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_graphics_description_success(self, mock_get_client):
        """Test _optimize_graphics_description successfully improves description."""
        mock_client = MagicMock()
        improved_desc = "A detailed bar chart with blue bars showing quarterly sales growth. The y-axis displays revenue in millions, x-axis shows Q1 through Q4."
        mock_client.generate_text.return_value = improved_desc
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        description = "Chart showing sales."
        title = "Quarterly Sales"
        issues = []

        improved, improvement = skill._optimize_graphics_description(
            description=description,
            title=title,
            issues=issues,
            client=mock_client,
        )

        assert improved == improved_desc
        assert improvement["issue_type"] == "graphics_clarity"
        assert "Enhanced" in improvement["reasoning"]

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_graphics_description_logs_improvement(self, mock_get_client):
        """Test _optimize_graphics_description creates improvement log."""
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "Improved description with details."
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        description = "Vague description"
        title = "Test Slide"
        issues = []

        improved, improvement = skill._optimize_graphics_description(
            description=description,
            title=title,
            issues=issues,
            client=mock_client,
        )

        assert "original" in improvement
        assert "improved" in improvement
        assert "reasoning" in improvement

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_graphics_description_truncates_long_descriptions(self, mock_get_client):
        """Test _optimize_graphics_description truncates long descriptions in log."""
        mock_client = MagicMock()
        long_improved = "A" * 200
        mock_client.generate_text.return_value = long_improved
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        description = "B" * 200
        title = "Test"
        issues = []

        improved, improvement = skill._optimize_graphics_description(
            description=description,
            title=title,
            issues=issues,
            client=mock_client,
        )

        # Original and improved in log should be truncated to 100 chars + "..."
        assert len(improvement["original"]) <= 103  # 100 + "..."
        assert len(improvement["improved"]) <= 103

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    def test_optimize_graphics_description_returns_original_on_exception(self, mock_get_client):
        """Test _optimize_graphics_description returns original on API error."""
        mock_client = MagicMock()
        mock_client.generate_text.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()

        description = "Original description"
        title = "Test"
        issues = []

        improved, improvement = skill._optimize_graphics_description(
            description=description,
            title=title,
            issues=issues,
            client=mock_client,
        )

        assert improved == description
        assert improvement == {}


class TestSaveOptimizedPresentation:
    """Tests for _save_optimized_presentation method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_save_optimized_presentation_creates_file(self):
        """Test _save_optimized_presentation creates output file."""
        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "output.md")

        slides = [{"title": "Test", "markdown": "## Test\n\n- Point\n\n---\n\n"}]
        improvements = []

        skill._save_optimized_presentation(
            slides=slides,
            output_file=output_file,
            improvements=improvements,
            initial_score=60.0,
            final_score=80.0,
        )

        assert os.path.exists(output_file)

    def test_save_optimized_presentation_includes_metadata(self):
        """Test _save_optimized_presentation includes quality metadata in file."""
        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "output.md")

        slides = [{"title": "Test", "markdown": "## Test\n\n---\n\n"}]
        improvements = [{"type": "improvement"}]

        skill._save_optimized_presentation(
            slides=slides,
            output_file=output_file,
            improvements=improvements,
            initial_score=50.0,
            final_score=90.0,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "optimized: true" in content
        assert "quality_score_before: 50.0" in content
        assert "quality_score_after: 90.0" in content
        assert "improvements: 1" in content
        assert "+40.0 points" in content

    def test_save_optimized_presentation_includes_slide_markdown(self):
        """Test _save_optimized_presentation includes slide markdown."""
        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "output.md")

        slides = [
            {"title": "Slide One", "markdown": "## Slide One\n\n- Point A\n\n---\n\n"},
            {"title": "Slide Two", "markdown": "## Slide Two\n\n- Point B\n\n---\n\n"},
        ]
        improvements = []

        skill._save_optimized_presentation(
            slides=slides,
            output_file=output_file,
            improvements=improvements,
            initial_score=70.0,
            final_score=80.0,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "## Slide One" in content
        assert "## Slide Two" in content
        assert "- Point A" in content
        assert "- Point B" in content

    def test_save_optimized_presentation_creates_directory(self):
        """Test _save_optimized_presentation creates parent directory if needed."""
        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "subdir", "nested", "output.md")

        slides = [{"title": "Test", "markdown": "## Test\n\n---\n\n"}]

        skill._save_optimized_presentation(
            slides=slides,
            output_file=output_file,
            improvements=[],
            initial_score=70.0,
            final_score=80.0,
        )

        assert os.path.exists(output_file)

    def test_save_optimized_presentation_rebuilds_missing_markdown(self):
        """Test _save_optimized_presentation rebuilds markdown when not present."""
        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "output.md")

        slides = [
            {"title": "Rebuilt Slide", "bullets": ["Bullet A", "Bullet B"]},
        ]

        skill._save_optimized_presentation(
            slides=slides,
            output_file=output_file,
            improvements=[],
            initial_score=70.0,
            final_score=80.0,
        )

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert "## Slide: Rebuilt Slide" in content
        assert "- Bullet A" in content
        assert "- Bullet B" in content


class TestRebuildSlideMarkdown:
    """Tests for _rebuild_slide_markdown method."""

    def test_rebuild_slide_markdown_with_title_and_bullets(self):
        """Test _rebuild_slide_markdown generates correct format."""
        skill = ContentOptimizationSkill()

        slide = {
            "title": "My Slide Title",
            "bullets": ["First point", "Second point", "Third point"],
        }

        markdown = skill._rebuild_slide_markdown(slide)

        assert "## Slide: My Slide Title" in markdown
        assert "**Content:**" in markdown
        assert "- First point" in markdown
        assert "- Second point" in markdown
        assert "- Third point" in markdown
        assert "---" in markdown

    def test_rebuild_slide_markdown_no_title(self):
        """Test _rebuild_slide_markdown handles missing title."""
        skill = ContentOptimizationSkill()

        slide = {"bullets": ["Point"]}

        markdown = skill._rebuild_slide_markdown(slide)

        assert "## Slide: Untitled" in markdown

    def test_rebuild_slide_markdown_no_bullets(self):
        """Test _rebuild_slide_markdown handles no bullets."""
        skill = ContentOptimizationSkill()

        slide = {"title": "Title Only"}

        markdown = skill._rebuild_slide_markdown(slide)

        assert "## Slide: Title Only" in markdown
        assert "**Content:**" not in markdown  # No content section when no bullets

    def test_rebuild_slide_markdown_empty_bullets(self):
        """Test _rebuild_slide_markdown handles empty bullets list."""
        skill = ContentOptimizationSkill()

        slide = {"title": "Empty", "bullets": []}

        markdown = skill._rebuild_slide_markdown(slide)

        assert "## Slide: Empty" in markdown
        assert "**Content:**" not in markdown


class TestGetContentOptimizationSkill:
    """Tests for get_content_optimization_skill convenience function."""

    def test_get_content_optimization_skill_returns_instance(self):
        """Test get_content_optimization_skill returns correct type."""
        skill = get_content_optimization_skill()
        assert isinstance(skill, ContentOptimizationSkill)

    def test_get_content_optimization_skill_returns_new_instance(self):
        """Test get_content_optimization_skill returns new instance each call."""
        skill1 = get_content_optimization_skill()
        skill2 = get_content_optimization_skill()
        assert skill1 is not skill2


class TestContentOptimizationSkillIntegration:
    """Integration tests for ContentOptimizationSkill with mocked dependencies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_full_optimization_flow_with_issues(self, mock_analyzer_class, mock_get_client):
        """Test complete optimization flow when slides have issues."""
        # Set up analyzer mock
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.side_effect = [
            {
                "overall_score": 60.0,
                "issues": [
                    {"slide_number": 1, "type": "structure", "message": "Bullets not parallel"},
                    {"slide_number": 2, "type": "readability", "message": "Text too complex"},
                ],
            },
            {
                "overall_score": 85.0,
                "issues": [],
            },
        ]
        mock_analyzer_class.return_value = mock_analyzer

        # Set up client mock
        mock_client = MagicMock()
        mock_client.generate_text.return_value = "1. Improved first\n2. Improved second"
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": [
                    {"title": "Slide 1", "bullets": ["Point A", "Point B"]},
                    {"title": "Slide 2", "bullets": ["Complex point", "Another point"]},
                ],
                "output_file": output_file,
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True
        assert output.data["quality_score_before"] == 60.0
        assert output.data["quality_score_after"] == 85.0
        assert output.data["quality_improvement"] == 25.0
        assert os.path.exists(output_file)

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_optimization_with_graphics_issues(self, mock_analyzer_class, mock_get_client):
        """Test optimization handles graphics description issues."""
        mock_analyzer = MagicMock()
        mock_analyzer.analyze_presentation.side_effect = [
            {
                "overall_score": 65.0,
                "issues": [
                    {"slide_number": 1, "message": "Graphics description vague"}
                ],
            },
            {
                "overall_score": 80.0,
                "issues": [],
            },
        ]
        mock_analyzer_class.return_value = mock_analyzer

        mock_client = MagicMock()
        mock_client.generate_text.return_value = "A detailed visualization with blue charts and clear data labels."
        mock_get_client.return_value = mock_client

        skill = ContentOptimizationSkill()
        output_file = os.path.join(self.temp_dir, "optimized.md")

        input_data = SkillInput(
            data={
                "slides": [
                    {
                        "title": "Data Slide",
                        "graphics_description": "Some chart.",
                        "markdown": "## Data\n\n---\n\n",
                    },
                ],
                "output_file": output_file,
                "optimization_goals": ["graphics"],
            },
            context={},
            config={},
        )

        output = skill.execute(input_data)

        assert output.success is True
        # Client should have been called to improve graphics
        assert mock_client.generate_text.called

    @patch("plugin.skills.content.content_optimization_skill.get_claude_client")
    @patch("plugin.skills.content.content_optimization_skill.QualityAnalyzer")
    def test_run_method_handles_validation_failure(self, mock_analyzer_class, mock_get_client):
        """Test run method handles validation failure gracefully."""
        skill = ContentOptimizationSkill()

        # Invalid input (missing required data)
        input_data = SkillInput(
            data={},  # No slides or presentation_file
            context={},
            config={},
        )

        # run() method should catch validation failure
        # validate_input returns (bool, list[str])
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0
