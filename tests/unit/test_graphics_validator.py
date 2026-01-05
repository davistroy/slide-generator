"""
Unit tests for plugin/lib/graphics_validator.py

Tests the GraphicsValidator class and validation functions.
"""

import pytest
from unittest.mock import MagicMock, patch

from plugin.lib.graphics_validator import (
    GraphicsValidator,
    ValidationResult,
    get_graphics_validator,
    validate_graphics_batch,
)


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_validation_result(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            passed=True,
            score=95.0,
            issues=[],
            suggestions=[],
        )
        assert result.passed is True
        assert result.score == 95.0
        assert result.issues == []
        assert result.description_improved is None

    def test_validation_result_with_improved_description(self):
        """Test ValidationResult with improved description."""
        result = ValidationResult(
            passed=False,
            score=60.0,
            issues=[{"type": "length", "message": "Too short"}],
            suggestions=["Add more detail"],
            description_improved="Improved description here",
        )
        assert result.passed is False
        assert result.description_improved == "Improved description here"


class TestGraphicsValidatorCheckLength:
    """Tests for _check_length method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_length_too_short_one_sentence(self):
        """Test detection of too short description (1 sentence)."""
        description = "A simple image."
        issue, penalty = self.validator._check_length(description)
        assert issue is not None
        assert issue["type"] == "length"
        assert issue["severity"] == "high"
        assert penalty == 30.0

    def test_check_length_two_sentences(self):
        """Test detection of borderline length (2 sentences)."""
        description = "A clean diagram showing components. The layout is centered."
        issue, penalty = self.validator._check_length(description)
        assert issue is not None
        assert issue["severity"] == "low"
        assert penalty == 10.0

    def test_check_length_adequate(self):
        """Test adequate length (3+ sentences)."""
        description = (
            "A detailed diagram showing the carburetor components. "
            "The layout is centered with clear labels. "
            "Colors include blue for air flow and red for fuel."
        )
        issue, penalty = self.validator._check_length(description)
        assert issue is None
        assert penalty == 0

    def test_check_length_empty(self):
        """Test empty description."""
        issue, penalty = self.validator._check_length("")
        assert issue is not None
        assert penalty == 30.0


class TestGraphicsValidatorCheckSpecificity:
    """Tests for _check_specificity method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_specificity_many_vague_words(self):
        """Test detection of many vague words."""
        description = (
            "An abstract concept representing the general idea "
            "of various themes showing the notion."
        )
        issue, penalty = self.validator._check_specificity(description)
        assert issue is not None
        assert issue["severity"] == "high"
        assert penalty == 25.0

    def test_check_specificity_few_vague_words(self):
        """Test detection of few vague words."""
        description = "A diagram showing the components of the system."
        issue, penalty = self.validator._check_specificity(description)
        assert issue is not None
        assert issue["severity"] == "medium"
        assert penalty == 15.0

    def test_check_specificity_concrete(self):
        """Test concrete description without vague words."""
        description = (
            "A blue and red cross-section diagram of a carburetor. "
            "The venturi passage is highlighted in the center."
        )
        issue, penalty = self.validator._check_specificity(description)
        assert issue is None
        assert penalty == 0


class TestGraphicsValidatorCheckVisualElements:
    """Tests for _check_visual_elements method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_visual_elements_none(self):
        """Test detection of missing visual elements."""
        description = "Something about carburetors and how they work."
        issue, penalty = self.validator._check_visual_elements(description)
        assert issue is not None
        assert issue["severity"] == "high"
        assert penalty == 30.0

    def test_check_visual_elements_one(self):
        """Test detection of limited visual elements."""
        description = "A diagram of the system."
        issue, penalty = self.validator._check_visual_elements(description)
        assert issue is not None
        assert issue["severity"] == "low"
        assert penalty == 10.0

    def test_check_visual_elements_multiple(self):
        """Test adequate visual elements."""
        description = (
            "A detailed diagram with arrows showing airflow. "
            "The cross-section reveals internal shapes and colors."
        )
        issue, penalty = self.validator._check_visual_elements(description)
        assert issue is None
        assert penalty == 0


class TestGraphicsValidatorCheckLayoutHints:
    """Tests for _check_layout_hints method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_layout_hints_missing(self):
        """Test detection of missing layout hints."""
        description = "A diagram of the carburetor with internal components visible."
        issue, penalty = self.validator._check_layout_hints(description)
        assert issue is not None
        assert issue["type"] == "layout"
        assert penalty == 20.0

    def test_check_layout_hints_present(self):
        """Test layout hints present."""
        description = (
            "A centered diagram with the component in the foreground. "
            "The background shows supporting elements."
        )
        issue, penalty = self.validator._check_layout_hints(description)
        assert issue is None
        assert penalty == 0

    def test_check_layout_hints_various_keywords(self):
        """Test various layout keywords are detected."""
        descriptions = [
            "A split-screen view showing before and after.",
            "The component is positioned top-down.",
            "A side-view of the mechanism.",
            "Horizontal arrangement of parts.",
        ]
        for desc in descriptions:
            issue, penalty = self.validator._check_layout_hints(desc)
            assert issue is None, f"Failed for: {desc}"


class TestGraphicsValidatorCheckTextAvoidance:
    """Tests for _check_text_avoidance method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_text_avoidance_contains_label(self):
        """Test detection of label keyword."""
        description = "A diagram with labeled components."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert issue["type"] == "text_in_image"
        assert penalty == 25.0

    def test_check_text_avoidance_contains_text(self):
        """Test detection of text keyword."""
        description = "An image with text explaining the process."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert penalty == 25.0

    def test_check_text_avoidance_contains_title(self):
        """Test detection of title keyword."""
        description = "A visual with the title displayed at the top."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None

    def test_check_text_avoidance_no_text_references(self):
        """Test description without text references."""
        description = (
            "A clean diagram showing components with arrows indicating flow. "
            "Colors differentiate the pathways."
        )
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is None
        assert penalty == 0


class TestGraphicsValidatorCheckBrandAlignment:
    """Tests for _check_brand_alignment method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_brand_alignment_no_config(self):
        """Test with no style config."""
        issue, penalty = self.validator._check_brand_alignment(
            "A diagram.", {"brand_colors": []}
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_missing_colors(self):
        """Test when brand colors not mentioned."""
        description = "A green and yellow diagram."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(description, style_config)
        assert issue is not None
        assert issue["type"] == "brand_alignment"
        assert penalty == 10.0

    def test_check_brand_alignment_hex_mentioned(self):
        """Test when hex color is mentioned."""
        description = "A diagram using #DD0033 for accents."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(description, style_config)
        assert issue is None

    def test_check_brand_alignment_color_name_mentioned(self):
        """Test when color name (red/blue) is mentioned."""
        description = "A diagram with red highlights and blue backgrounds."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(description, style_config)
        assert issue is None


class TestGraphicsValidatorValidateDescription:
    """Tests for validate_description method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_validate_description_good(self):
        """Test validation of good description."""
        description = (
            "A professional technical diagram showing a cross-section of a carburetor. "
            "The venturi is centered with arrows indicating airflow in blue. "
            "Fuel passages are shown in red tones against a gray background. "
            "The composition is balanced with depth and perspective."
        )
        result = self.validator.validate_description(description)
        assert result.passed is True
        assert result.score >= 75

    def test_validate_description_poor(self):
        """Test validation of poor description."""
        description = "An image representing the concept."
        result = self.validator.validate_description(description)
        assert result.passed is False
        assert result.score < 75
        assert len(result.issues) > 0

    def test_validate_description_with_suggestions(self):
        """Test validation generates suggestions."""
        description = "A simple visual."
        result = self.validator.validate_description(description)
        assert len(result.suggestions) > 0

    def test_validate_description_with_style_config(self):
        """Test validation with style config."""
        description = "A professional diagram with clean lines and depth."
        style_config = {"brand_colors": ["#DD0033"]}
        result = self.validator.validate_description(
            description, style_config=style_config
        )
        # Should have brand alignment issue
        brand_issues = [i for i in result.issues if i["type"] == "brand_alignment"]
        assert len(brand_issues) > 0


class TestGraphicsValidatorGenerateSuggestions:
    """Tests for _generate_suggestions method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_generate_suggestions_empty(self):
        """Test suggestions for empty issues."""
        suggestions = self.validator._generate_suggestions([])
        assert suggestions == []

    def test_generate_suggestions_groups_by_type(self):
        """Test suggestions are grouped by issue type."""
        issues = [
            {"type": "length", "suggestion": "Add more detail"},
            {"type": "length", "suggestion": "Expand description"},
            {"type": "specificity", "suggestion": "Be more specific"},
        ]
        suggestions = self.validator._generate_suggestions(issues)
        # Should have one suggestion per type
        assert len(suggestions) == 2


class TestGraphicsValidatorValidateAndImprove:
    """Tests for validate_and_improve method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_validate_and_improve_passes(self):
        """Test validate_and_improve when validation passes."""
        description = (
            "A professional diagram showing components in the foreground. "
            "The centered layout includes arrows and shapes. "
            "Blue and red colors indicate different pathways with depth."
        )
        result = self.validator.validate_and_improve(description)
        assert result["validation"].passed is True
        assert result["improved"] is None
        assert result["final"] == description

    def test_validate_and_improve_fails_returns_original_without_context(self):
        """Test validate_and_improve when fails without context."""
        description = "A simple visual."
        result = self.validator.validate_and_improve(description)
        assert result["validation"].passed is False
        # Without slide_context, improved will be None
        assert result["original"] == description


class TestValidateGraphicsBatch:
    """Tests for validate_graphics_batch function."""

    def test_validate_graphics_batch_empty(self):
        """Test batch validation with empty slides."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            result = validate_graphics_batch([])
            assert result["total_slides"] == 0
            assert result["pass_rate"] == 100

    def test_validate_graphics_batch_no_descriptions(self):
        """Test batch validation with slides without descriptions."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {"title": "Slide 1", "bullets": []},
                {"title": "Slide 2", "bullets": []},
            ]
            result = validate_graphics_batch(slides)
            assert result["total_slides"] == 0

    def test_validate_graphics_batch_mixed(self):
        """Test batch validation with mixed quality descriptions."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "Good Slide",
                    "bullets": ["Point 1"],
                    "graphics_description": (
                        "A professional diagram with centered layout. "
                        "Arrows and shapes show the flow. "
                        "Blue and red colors with depth."
                    ),
                },
                {
                    "title": "Bad Slide",
                    "bullets": ["Point 2"],
                    "graphics_description": "A simple image.",
                },
            ]
            result = validate_graphics_batch(slides)
            assert result["total_slides"] == 2
            assert result["passed"] >= 1  # At least the good one passes
            assert result["failed"] >= 0

    def test_validate_graphics_batch_with_style_config(self):
        """Test batch validation with style config."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "Test",
                    "graphics_description": "A diagram with shapes and arrows centered.",
                }
            ]
            style_config = {"brand_colors": ["#DD0033"]}
            result = validate_graphics_batch(slides, style_config)
            assert result["total_slides"] == 1


class TestGetGraphicsValidator:
    """Tests for get_graphics_validator convenience function."""

    def test_get_graphics_validator_returns_instance(self):
        """Test get_graphics_validator returns GraphicsValidator instance."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            validator = get_graphics_validator()
            assert isinstance(validator, GraphicsValidator)
