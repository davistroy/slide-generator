"""
Unit tests for plugin/lib/graphics_validator.py

Tests the GraphicsValidator class and validation functions.
"""

from unittest.mock import patch

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
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is not None
        assert issue["type"] == "brand_alignment"
        assert penalty == 10.0

    def test_check_brand_alignment_hex_mentioned(self):
        """Test when hex color is mentioned."""
        description = "A diagram using #DD0033 for accents."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is None

    def test_check_brand_alignment_color_name_mentioned(self):
        """Test when color name (red/blue) is mentioned."""
        description = "A diagram with red highlights and blue backgrounds."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
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


class TestGraphicsValidatorGenerateImprovedDescription:
    """Tests for _generate_improved_description method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = patch(
            "plugin.lib.graphics_validator.get_claude_client"
        ).start()

    def teardown_method(self):
        """Tear down test fixtures."""
        patch.stopall()

    def test_generate_improved_description_success(self):
        """Test successful improved description generation."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = (
            "  A professional technical diagram showing a carburetor cross-section. "
            "The centered layout displays internal components with blue arrows "
            "indicating airflow. Red accents highlight fuel passages against "
            "a clean background with subtle depth and perspective.  "
        )

        validator = GraphicsValidator()
        description = "An image of a carburetor."
        issues = [
            {"type": "length", "message": "Too short"},
            {"type": "visual_elements", "message": "Missing visual elements"},
        ]
        slide_context = {
            "title": "How Carburetors Work",
            "bullets": ["Air intake", "Fuel mixture", "Venturi effect"],
        }
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}

        result = validator._generate_improved_description(
            description, issues, slide_context, style_config
        )

        assert result is not None
        assert "carburetor" in result.lower()
        assert result == result.strip()  # Should be stripped
        mock_client_instance.generate_text.assert_called_once()
        call_kwargs = mock_client_instance.generate_text.call_args[1]
        assert call_kwargs["temperature"] == 0.8
        assert call_kwargs["max_tokens"] == 500

    def test_generate_improved_description_api_exception(self):
        """Test improved description returns None on API exception."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.side_effect = Exception("API error")

        validator = GraphicsValidator()
        description = "A simple image."
        issues = [{"type": "length", "message": "Too short"}]
        slide_context = {"title": "Test Slide", "bullets": []}

        result = validator._generate_improved_description(
            description, issues, slide_context, None
        )

        assert result is None

    def test_generate_improved_description_without_style_config(self):
        """Test improved description without style config."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = "Improved description text."

        validator = GraphicsValidator()
        description = "A simple image."
        issues = [{"type": "length", "message": "Too short"}]
        slide_context = {"title": "Test Slide", "bullets": ["Point 1", "Point 2"]}

        result = validator._generate_improved_description(
            description, issues, slide_context, None
        )

        assert result is not None
        # Verify brand_context is empty when no style_config
        call_args = mock_client_instance.generate_text.call_args[1]
        assert "Brand colors:" not in call_args["prompt"]

    def test_generate_improved_description_with_empty_bullets(self):
        """Test improved description with empty bullets list."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = "Improved description."

        validator = GraphicsValidator()
        description = "A simple image."
        issues = [{"type": "length", "message": "Too short"}]
        slide_context = {"title": "Test Slide", "bullets": []}

        result = validator._generate_improved_description(
            description, issues, slide_context, None
        )

        assert result is not None
        call_args = mock_client_instance.generate_text.call_args[1]
        assert "N/A" in call_args["prompt"]

    def test_generate_improved_description_with_missing_title(self):
        """Test improved description with missing title in context."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = "Improved description."

        validator = GraphicsValidator()
        description = "A simple image."
        issues = [{"type": "length", "message": "Too short"}]
        slide_context = {"bullets": ["Point 1"]}

        result = validator._generate_improved_description(
            description, issues, slide_context, None
        )

        assert result is not None

    def test_generate_improved_description_with_brand_colors(self):
        """Test improved description includes brand colors in prompt."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = "Improved description."

        validator = GraphicsValidator()
        description = "A simple image."
        issues = [{"type": "length", "message": "Too short"}]
        slide_context = {"title": "Test", "bullets": []}
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}

        result = validator._generate_improved_description(
            description, issues, slide_context, style_config
        )

        assert result is not None
        call_args = mock_client_instance.generate_text.call_args[1]
        assert "Brand colors: #DD0033, #004F71" in call_args["prompt"]


class TestGraphicsValidatorValidateDescriptionEdgeCases:
    """Edge case tests for validate_description method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_patcher = patch(
            "plugin.lib.graphics_validator.get_claude_client"
        )
        self.mock_client = self.mock_client_patcher.start()

    def teardown_method(self):
        """Tear down test fixtures."""
        self.mock_client_patcher.stop()

    def test_validate_description_triggers_improvement_on_failure_with_context(self):
        """Test that failed validation with slide_context triggers improvement."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = (
            "A professional diagram with centered composition showing components."
        )

        validator = GraphicsValidator()
        description = "Simple visual."  # Will fail validation
        slide_context = {"title": "Test", "bullets": ["Point 1"]}

        result = validator.validate_description(
            description, slide_context=slide_context
        )

        assert result.passed is False
        assert result.description_improved is not None
        mock_client_instance.generate_text.assert_called_once()

    def test_validate_description_no_improvement_without_context(self):
        """Test that failed validation without context doesn't trigger improvement."""
        mock_client_instance = self.mock_client.return_value

        validator = GraphicsValidator()
        description = "Simple visual."  # Will fail validation

        result = validator.validate_description(description)

        assert result.passed is False
        assert result.description_improved is None
        mock_client_instance.generate_text.assert_not_called()

    def test_validate_description_score_capped_at_zero(self):
        """Test that score is capped at 0 when penalties exceed 100."""
        validator = GraphicsValidator()
        # This description should trigger multiple high-severity issues
        description = (
            "text."  # Too short, vague, no visual elements, no layout, has text
        )

        result = validator.validate_description(description)

        assert result.score >= 0
        assert result.passed is False

    def test_validate_description_improvement_failure_returns_none(self):
        """Test that improvement failure returns None in description_improved."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.side_effect = Exception("API failure")

        validator = GraphicsValidator()
        description = "Simple visual."
        slide_context = {"title": "Test", "bullets": []}

        result = validator.validate_description(
            description, slide_context=slide_context
        )

        assert result.passed is False
        assert result.description_improved is None


class TestGraphicsValidatorCheckBrandAlignmentEdgeCases:
    """Edge case tests for _check_brand_alignment method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_brand_alignment_empty_brand_colors_list(self):
        """Test with empty brand_colors list."""
        style_config = {"brand_colors": []}
        issue, penalty = self.validator._check_brand_alignment(
            "A diagram with blue elements.", style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_missing_brand_colors_key(self):
        """Test with missing brand_colors key in style_config."""
        style_config = {"other_setting": "value"}
        issue, penalty = self.validator._check_brand_alignment(
            "A diagram with blue elements.", style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_black_color_mentioned(self):
        """Test detection of black color name for #000000."""
        description = "A diagram with black outlines and clean design."
        style_config = {"brand_colors": ["#000000"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_white_color_mentioned(self):
        """Test detection of white color name for #FFFFFF."""
        description = "A clean diagram with white backgrounds."
        style_config = {"brand_colors": ["#FFFFFF"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_hex_without_hash(self):
        """Test hex color detection without hash prefix in description."""
        description = "A diagram using DD0033 as the primary accent color."
        style_config = {"brand_colors": ["#DD0033"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_case_insensitive(self):
        """Test brand alignment check is case insensitive."""
        description = "A diagram with RED highlights and BLUE backgrounds."
        style_config = {"brand_colors": ["#DD0033", "#004F71"]}
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is None
        assert penalty == 0

    def test_check_brand_alignment_unrecognized_hex_color(self):
        """Test brand alignment with unrecognized hex color (no color name mapping)."""
        description = "A green and yellow diagram."
        style_config = {"brand_colors": ["#123456"]}  # No color name mapping exists
        issue, penalty = self.validator._check_brand_alignment(
            description, style_config
        )
        assert issue is not None
        assert issue["type"] == "brand_alignment"
        assert penalty == 10.0


class TestGraphicsValidatorValidateAndImproveEdgeCases:
    """Edge case tests for validate_and_improve method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client_patcher = patch(
            "plugin.lib.graphics_validator.get_claude_client"
        )
        self.mock_client = self.mock_client_patcher.start()

    def teardown_method(self):
        """Tear down test fixtures."""
        self.mock_client_patcher.stop()

    def test_validate_and_improve_uses_improved_description_when_available(self):
        """Test that improved description is used as final when available."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = (
            "Much better improved description."
        )

        validator = GraphicsValidator()
        description = "Simple."
        slide_context = {"title": "Test", "bullets": []}

        result = validator.validate_and_improve(
            description, slide_context=slide_context
        )

        assert result["validation"].passed is False
        assert result["improved"] == "Much better improved description."
        assert result["final"] == "Much better improved description."
        assert result["original"] == description

    def test_validate_and_improve_falls_back_to_original_when_improvement_fails(self):
        """Test fallback to original when improvement generation fails."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.side_effect = Exception("API error")

        validator = GraphicsValidator()
        description = "Simple visual."
        slide_context = {"title": "Test", "bullets": []}

        result = validator.validate_and_improve(
            description, slide_context=slide_context
        )

        assert result["validation"].passed is False
        # When improvement fails, description_improved is None, so final should be original
        assert result["improved"] == description  # Falls back to original
        assert result["final"] == description

    def test_validate_and_improve_with_style_config(self):
        """Test validate_and_improve passes style_config correctly."""
        mock_client_instance = self.mock_client.return_value
        mock_client_instance.generate_text.return_value = "Improved with brand colors."

        validator = GraphicsValidator()
        description = "Simple."
        slide_context = {"title": "Test", "bullets": []}
        style_config = {"brand_colors": ["#DD0033"]}

        result = validator.validate_and_improve(
            description, slide_context=slide_context, style_config=style_config
        )

        # Should have brand alignment issue in validation
        assert result["validation"].passed is False
        brand_issues = [
            i for i in result["validation"].issues if i["type"] == "brand_alignment"
        ]
        assert len(brand_issues) > 0


class TestValidateGraphicsBatchEdgeCases:
    """Edge case tests for validate_graphics_batch function."""

    def test_validate_graphics_batch_empty_description_string(self):
        """Test batch validation skips slides with empty description strings."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {"title": "Slide 1", "graphics_description": ""},
                {
                    "title": "Slide 2",
                    "graphics_description": (
                        "A professional diagram with centered layout. "
                        "Arrows and shapes show flow with depth."
                    ),
                },
            ]
            result = validate_graphics_batch(slides)
            # Empty description should be skipped
            assert result["total_slides"] == 1

    def test_validate_graphics_batch_slide_context_passed_correctly(self):
        """Test that slide context is passed to validator for each slide."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "Test Title",
                    "bullets": ["Bullet 1", "Bullet 2"],
                    "graphics_description": (
                        "A professional diagram with centered layout and depth. "
                        "Arrows and shapes show flow direction clearly."
                    ),
                }
            ]
            result = validate_graphics_batch(slides)
            assert result["total_slides"] == 1
            # The validation result should be present
            assert "validation" in result["results"][0]

    def test_validate_graphics_batch_slide_numbering(self):
        """Test that slide numbers are correctly assigned (1-indexed)."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "First",
                    "graphics_description": (
                        "A diagram with centered layout and arrows. "
                        "Shapes show components with depth."
                    ),
                },
                {
                    "title": "Second",
                    "graphics_description": (
                        "A diagram with foreground elements. "
                        "Colors differentiate pathways with perspective."
                    ),
                },
            ]
            result = validate_graphics_batch(slides)
            assert result["results"][0]["slide_number"] == 1
            assert result["results"][1]["slide_number"] == 2

    def test_validate_graphics_batch_all_fail(self):
        """Test batch validation when all slides fail."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {"title": "Bad 1", "graphics_description": "Simple."},
                {"title": "Bad 2", "graphics_description": "Concept."},
            ]
            result = validate_graphics_batch(slides)
            assert result["passed"] == 0
            assert result["failed"] == 2
            assert result["pass_rate"] == 0.0

    def test_validate_graphics_batch_all_pass(self):
        """Test batch validation when all slides pass."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "Good 1",
                    "graphics_description": (
                        "A professional diagram with centered composition. "
                        "Blue arrows indicate flow direction clearly. "
                        "Red shapes highlight key components with depth."
                    ),
                },
                {
                    "title": "Good 2",
                    "graphics_description": (
                        "A technical illustration with foreground elements. "
                        "Gradient colors show transitions smoothly. "
                        "The balanced layout provides clear perspective."
                    ),
                },
            ]
            result = validate_graphics_batch(slides)
            assert result["passed"] == 2
            assert result["failed"] == 0
            assert result["pass_rate"] == 100.0

    def test_validate_graphics_batch_missing_bullets_key(self):
        """Test batch validation handles missing bullets key gracefully."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            slides = [
                {
                    "title": "No Bullets",
                    "graphics_description": (
                        "A diagram with centered layout and arrows. "
                        "Shapes indicate components with depth and perspective."
                    ),
                }
            ]
            result = validate_graphics_batch(slides)
            assert result["total_slides"] == 1


class TestGraphicsValidatorCheckLengthEdgeCases:
    """Edge case tests for _check_length method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_length_with_exclamation_marks(self):
        """Test sentence counting with exclamation marks."""
        description = "A bold diagram! It shows components! The layout is striking!"
        issue, penalty = self.validator._check_length(description)
        assert issue is None  # 3 sentences should pass
        assert penalty == 0

    def test_check_length_with_question_marks(self):
        """Test sentence counting with question marks."""
        description = "What does the diagram show? It reveals internal components. How is it arranged? Centrally."
        issue, penalty = self.validator._check_length(description)
        assert issue is None  # 4 sentences should pass
        assert penalty == 0

    def test_check_length_with_mixed_punctuation(self):
        """Test sentence counting with mixed punctuation."""
        description = "A diagram showing components. What else? It has arrows!"
        issue, penalty = self.validator._check_length(description)
        assert issue is None  # 3 sentences should pass
        assert penalty == 0

    def test_check_length_with_trailing_whitespace(self):
        """Test sentence counting handles trailing whitespace."""
        description = "A diagram.   "
        issue, penalty = self.validator._check_length(description)
        assert issue is not None
        assert issue["severity"] == "high"

    def test_check_length_with_multiple_periods(self):
        """Test sentence counting with ellipsis-like patterns."""
        description = "A diagram... showing components... in detail."
        issue, penalty = self.validator._check_length(description)
        # Should count as separate sentences based on period splitting
        assert issue is None or issue["severity"] == "low"


class TestGraphicsValidatorTextIndicators:
    """Tests for various text indicator keywords."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_check_text_avoidance_caption(self):
        """Test detection of caption keyword."""
        description = "A diagram with a caption underneath."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "caption" in issue["message"]

    def test_check_text_avoidance_heading(self):
        """Test detection of heading keyword."""
        description = "An image with a heading at the top."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "heading" in issue["message"]

    def test_check_text_avoidance_font(self):
        """Test detection of font keyword."""
        description = "A diagram using a sans-serif font for annotations."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "font" in issue["message"]

    def test_check_text_avoidance_typography(self):
        """Test detection of typography keyword."""
        description = "A visual with clean typography elements."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "typography" in issue["message"]

    def test_check_text_avoidance_written(self):
        """Test detection of written keyword."""
        description = "An image with written instructions visible."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "written" in issue["message"]

    def test_check_text_avoidance_words(self):
        """Test detection of words keyword."""
        description = "A diagram with words explaining the process."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "words" in issue["message"]

    def test_check_text_avoidance_letters(self):
        """Test detection of letters keyword."""
        description = "A visual with letters marking different parts."
        issue, penalty = self.validator._check_text_avoidance(description)
        assert issue is not None
        assert "letters" in issue["message"]


class TestGraphicsValidatorMultipleIssues:
    """Tests for handling multiple validation issues."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.graphics_validator.get_claude_client"):
            self.validator = GraphicsValidator()

    def test_multiple_issues_accumulate_penalties(self):
        """Test that multiple issues correctly accumulate penalties."""
        # Description that triggers multiple issues
        description = "concept."  # Short, vague, no visuals, no layout
        result = self.validator.validate_description(description)

        # Should have multiple issues
        assert len(result.issues) >= 3
        assert result.passed is False
        # Score should be significantly reduced
        assert result.score < 50

    def test_all_issue_types_detected(self):
        """Test that all issue types can be detected."""
        # Description triggering all possible issue types
        description = "abstract concept with labeled text."
        style_config = {"brand_colors": ["#DD0033"]}
        result = self.validator.validate_description(
            description, style_config=style_config
        )

        issue_types = {issue["type"] for issue in result.issues}
        expected_types = {
            "length",
            "specificity",
            "visual_elements",
            "layout",
            "text_in_image",
            "brand_alignment",
        }
        assert issue_types == expected_types

    def test_suggestions_cover_all_issue_types(self):
        """Test that suggestions are generated for all issue types."""
        description = "abstract concept with labeled text."
        style_config = {"brand_colors": ["#DD0033"]}
        result = self.validator.validate_description(
            description, style_config=style_config
        )

        # Should have a suggestion for each unique issue type
        issue_types = {issue["type"] for issue in result.issues}
        assert len(result.suggestions) == len(issue_types)
