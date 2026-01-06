"""
Unit tests for plugin/lib/presentation/visual_validator.py

Tests the VisualValidator class that validates PowerPoint slides using Gemini Vision API.
"""

import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from plugin.lib.presentation.parser import Slide


class TestValidationResultDataclass:
    """Tests for ValidationResult dataclass."""

    def test_create_validation_result_passed(self):
        """Test creating a passed ValidationResult."""
        from plugin.lib.presentation.visual_validator import ValidationResult

        result = ValidationResult(
            passed=True,
            score=0.85,
            issues=[],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={"content_accuracy": 0.9, "visual_hierarchy": 0.8},
        )
        assert result.passed is True
        assert result.score == 0.85
        assert result.issues == []
        assert result.suggestions == []
        assert result.raw_feedback == "Test feedback"
        assert result.rubric_scores["content_accuracy"] == 0.9

    def test_create_validation_result_failed(self):
        """Test creating a failed ValidationResult with issues."""
        from plugin.lib.presentation.visual_validator import ValidationResult

        result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Title too small", "Missing bullet"],
            suggestions=["Increase font size", "Add missing content"],
            raw_feedback='{"total_score": 60}',
            rubric_scores={
                "content_accuracy": 0.5,
                "visual_hierarchy": 0.6,
                "brand_alignment": 0.7,
                "image_quality": 0.8,
                "layout_effectiveness": 0.6,
            },
        )
        assert result.passed is False
        assert result.score == 0.60
        assert len(result.issues) == 2
        assert "Title too small" in result.issues
        assert len(result.suggestions) == 2

    def test_validation_result_empty_rubric(self):
        """Test ValidationResult with empty rubric scores (error case)."""
        from plugin.lib.presentation.visual_validator import ValidationResult

        result = ValidationResult(
            passed=True,
            score=0.75,
            issues=["Validation error"],
            suggestions=[],
            raw_feedback="Error occurred",
            rubric_scores={},
        )
        assert result.rubric_scores == {}


class TestVisualValidatorInit:
    """Tests for VisualValidator initialization."""

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises OSError."""
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
        ):
            with pytest.raises(OSError) as exc_info:
                from plugin.lib.presentation.visual_validator import (
                    VisualValidator,
                )

                VisualValidator(api_key=None)
            assert "Google API key required" in str(exc_info.value)

    def test_init_with_explicit_api_key(self):
        """Test initialization with explicit API key."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            validator = VisualValidator(api_key="test-api-key")
            assert validator.api_key == "test-api-key"
            mock_genai.Client.assert_called_once_with(api_key="test-api-key")

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "env-api-key"})
    def test_init_uses_environment_variable(self):
        """Test initialization uses GOOGLE_API_KEY environment variable."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            validator = VisualValidator()
            assert validator.api_key == "env-api-key"

    def test_init_client_failure_raises_error(self):
        """Test initialization when Gemini client fails."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_genai.Client.side_effect = Exception("Connection failed")

            with pytest.raises(OSError) as exc_info:
                from plugin.lib.presentation.visual_validator import (
                    VisualValidator,
                )

                VisualValidator(api_key="test-key")
            assert "Failed to initialize Gemini client" in str(exc_info.value)


class TestVisualValidatorConstants:
    """Tests for VisualValidator class constants."""

    def test_validation_threshold(self):
        """Test validation threshold is 0.75."""
        from plugin.lib.presentation.visual_validator import VisualValidator

        assert VisualValidator.VALIDATION_THRESHOLD == 0.75

    def test_rubric_weights_sum_to_one(self):
        """Test rubric weights sum to 1.0."""
        from plugin.lib.presentation.visual_validator import VisualValidator

        total_weight = sum(VisualValidator.RUBRIC_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_rubric_weights_contain_all_categories(self):
        """Test rubric weights contain all expected categories."""
        from plugin.lib.presentation.visual_validator import VisualValidator

        expected_categories = [
            "content_accuracy",
            "visual_hierarchy",
            "brand_alignment",
            "image_quality",
            "layout_effectiveness",
        ]
        for category in expected_categories:
            assert category in VisualValidator.RUBRIC_WEIGHTS

    def test_rubric_weights_values(self):
        """Test specific rubric weight values."""
        from plugin.lib.presentation.visual_validator import VisualValidator

        assert VisualValidator.RUBRIC_WEIGHTS["content_accuracy"] == 0.30
        assert VisualValidator.RUBRIC_WEIGHTS["visual_hierarchy"] == 0.20
        assert VisualValidator.RUBRIC_WEIGHTS["brand_alignment"] == 0.20
        assert VisualValidator.RUBRIC_WEIGHTS["image_quality"] == 0.15
        assert VisualValidator.RUBRIC_WEIGHTS["layout_effectiveness"] == 0.15


class TestBuildValidationPrompt:
    """Tests for _build_validation_prompt method."""

    def setup_method(self):
        """Set up test fixtures with mocked Gemini client."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_prompt_includes_slide_number(self):
        """Test prompt includes slide number."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Test Slide",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Slide Number:** 3" in prompt

    def test_prompt_includes_slide_type(self):
        """Test prompt includes slide type."""
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Presentation Title",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "title")
        assert "**Type:** title" in prompt

    def test_prompt_includes_title(self):
        """Test prompt includes slide title."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="My Important Title",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Title:** My Important Title" in prompt

    def test_prompt_includes_subtitle(self):
        """Test prompt includes subtitle when present."""
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Main Title",
            subtitle="Subtitle Here",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "title")
        assert "**Subtitle:** Subtitle Here" in prompt

    def test_prompt_shows_none_for_missing_subtitle(self):
        """Test prompt shows 'None' for missing subtitle."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Title",
            subtitle=None,
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Subtitle:** None" in prompt

    def test_prompt_includes_bullet_points(self):
        """Test prompt includes bullet points."""
        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Content Slide",
            content_bullets=[
                ("First point", 0),
                ("Second point", 0),
                ("Sub-point", 1),
            ],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Bullet Points:** 3 total" in prompt
        assert "- First point" in prompt
        assert "- Second point" in prompt
        assert "  - Sub-point" in prompt

    def test_prompt_truncates_many_bullets(self):
        """Test prompt truncates when more than 5 bullets."""
        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Dense Slide",
            content_bullets=[
                ("Point 1", 0),
                ("Point 2", 0),
                ("Point 3", 0),
                ("Point 4", 0),
                ("Point 5", 0),
                ("Point 6", 0),
                ("Point 7", 0),
            ],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "2 more" in prompt
        assert "Point 5" in prompt
        assert "Point 6" not in prompt

    def test_prompt_includes_graphic_description(self):
        """Test prompt includes graphic description."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            content_bullets=[],
            graphic="A detailed diagram showing system architecture",
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "image")
        assert "**Graphic Intent:** A detailed diagram" in prompt

    def test_prompt_truncates_long_graphic(self):
        """Test prompt truncates graphic description over 200 chars."""
        long_graphic = "A" * 250
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
            graphic=long_graphic,
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "image")
        assert "..." in prompt
        # Should have 200 chars + "..."
        graphic_section = prompt.split("**Graphic Intent:** ")[1].split("\n")[0]
        assert len(graphic_section) <= 203  # 200 chars + "..."

    def test_prompt_shows_none_for_no_graphic(self):
        """Test prompt shows 'None' when no graphic."""
        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Text Slide",
            content_bullets=[("Point", 0)],
            graphic=None,
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Graphic Intent:** None" in prompt

    def test_prompt_includes_brand_colors(self):
        """Test prompt includes brand colors from style config."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        style_config = {"brand_colors": ["#DD0033", "#004F71", "#FFFFFF"]}
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        assert "#DD0033" in prompt
        assert "#004F71" in prompt
        assert "#FFFFFF" in prompt

    def test_prompt_handles_empty_brand_colors(self):
        """Test prompt handles empty brand colors list."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        style_config = {"brand_colors": []}
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        assert "**Brand Colors:** Not specified" in prompt

    def test_prompt_includes_style(self):
        """Test prompt includes style description."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        style_config = {"style": "modern minimalist"}
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        assert "**Style:** modern minimalist" in prompt

    def test_prompt_uses_default_style(self):
        """Test prompt uses 'professional' as default style."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Style:** professional" in prompt

    def test_prompt_includes_validation_rubric(self):
        """Test prompt includes all rubric categories."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "CONTENT ACCURACY" in prompt
        assert "30 points" in prompt
        assert "VISUAL HIERARCHY" in prompt
        assert "20 points" in prompt
        assert "BRAND ALIGNMENT" in prompt
        assert "IMAGE QUALITY" in prompt
        assert "15 points" in prompt
        assert "LAYOUT EFFECTIVENESS" in prompt

    def test_prompt_requests_json_format(self):
        """Test prompt requests JSON format response."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Slide",
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "JSON object" in prompt
        assert '"total_score"' in prompt
        assert '"issues"' in prompt
        assert '"suggestions"' in prompt


class TestParseValidationResponse:
    """Tests for _parse_validation_response method."""

    def setup_method(self):
        """Set up test fixtures with mocked Gemini client."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = json.dumps(
            {
                "content_accuracy": 28,
                "visual_hierarchy": 18,
                "brand_alignment": 19,
                "image_quality": 14,
                "layout_effectiveness": 13,
                "total_score": 92,
                "issues": ["Minor font issue"],
                "suggestions": ["Use larger title"],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is True
        assert result.score > 0.9
        assert len(result.issues) == 1
        assert "Minor font issue" in result.issues
        assert len(result.suggestions) == 1

    def test_parse_json_in_markdown_code_block(self):
        """Test parsing JSON inside markdown code block."""
        response = """```json
{
    "content_accuracy": 25,
    "visual_hierarchy": 16,
    "brand_alignment": 15,
    "image_quality": 12,
    "layout_effectiveness": 10,
    "total_score": 78,
    "issues": [],
    "suggestions": []
}
```"""
        result = self.validator._parse_validation_response(response, 2)
        assert result.passed is True
        assert result.score >= 0.75

    def test_parse_json_without_markdown(self):
        """Test parsing JSON without markdown wrapping."""
        response = """Some text before
{
    "content_accuracy": 20,
    "visual_hierarchy": 15,
    "brand_alignment": 14,
    "image_quality": 10,
    "layout_effectiveness": 11,
    "total_score": 70,
    "issues": ["Title missing"],
    "suggestions": ["Add title"]
}
Some text after"""
        result = self.validator._parse_validation_response(response, 3)
        # Should extract and parse the JSON portion
        assert isinstance(result.score, float)

    def test_parse_passing_score(self):
        """Test parsing result that passes threshold."""
        response = json.dumps(
            {
                "content_accuracy": 24,
                "visual_hierarchy": 16,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is True
        assert result.score >= 0.75

    def test_parse_failing_score(self):
        """Test parsing result that fails threshold."""
        response = json.dumps(
            {
                "content_accuracy": 15,
                "visual_hierarchy": 10,
                "brand_alignment": 10,
                "image_quality": 8,
                "layout_effectiveness": 7,
                "total_score": 50,
                "issues": ["Many issues"],
                "suggestions": ["Major improvements needed"],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is False
        assert result.score < 0.75

    def test_parse_calculates_weighted_score(self):
        """Test that weighted score is calculated correctly."""
        # All categories at 50%
        response = json.dumps(
            {
                "content_accuracy": 15,  # 50% of 30
                "visual_hierarchy": 10,  # 50% of 20
                "brand_alignment": 10,  # 50% of 20
                "image_quality": 7.5,  # 50% of 15
                "layout_effectiveness": 7.5,  # 50% of 15
                "total_score": 50,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        # Expected: 0.5 * 0.30 + 0.5 * 0.20 + 0.5 * 0.20 + 0.5 * 0.15 + 0.5 * 0.15 = 0.5
        assert abs(result.score - 0.5) < 0.01

    def test_parse_rubric_scores_normalized(self):
        """Test rubric scores are normalized to 0-1 range."""
        response = json.dumps(
            {
                "content_accuracy": 30,  # Max
                "visual_hierarchy": 20,  # Max
                "brand_alignment": 20,  # Max
                "image_quality": 15,  # Max
                "layout_effectiveness": 15,  # Max
                "total_score": 100,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.rubric_scores["content_accuracy"] == 1.0
        assert result.rubric_scores["visual_hierarchy"] == 1.0
        assert result.rubric_scores["brand_alignment"] == 1.0
        assert result.rubric_scores["image_quality"] == 1.0
        assert result.rubric_scores["layout_effectiveness"] == 1.0
        assert abs(result.score - 1.0) < 0.01

    def test_parse_extracts_issues(self):
        """Test extraction of issues list."""
        response = json.dumps(
            {
                "content_accuracy": 20,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 10,
                "layout_effectiveness": 10,
                "total_score": 70,
                "issues": [
                    "Title font too small",
                    "Missing bullet point",
                    "Image blurry",
                ],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert len(result.issues) == 3
        assert "Title font too small" in result.issues
        assert "Missing bullet point" in result.issues
        assert "Image blurry" in result.issues

    def test_parse_extracts_suggestions(self):
        """Test extraction of suggestions list."""
        response = json.dumps(
            {
                "content_accuracy": 20,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 10,
                "layout_effectiveness": 10,
                "total_score": 70,
                "issues": [],
                "suggestions": ["Use 44pt for title", "Add more whitespace"],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert len(result.suggestions) == 2
        assert "Use 44pt for title" in result.suggestions

    def test_parse_invalid_json_returns_fallback(self):
        """Test invalid JSON returns fallback result."""
        response = "This is not valid JSON at all"
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is True
        assert result.score == self.validator.VALIDATION_THRESHOLD
        assert "Validation parse error" in result.issues
        assert result.rubric_scores == {}

    def test_parse_malformed_json_returns_fallback(self):
        """Test malformed JSON returns fallback result."""
        response = '{"content_accuracy": 20, "visual_hierarchy":}'  # Invalid JSON
        result = self.validator._parse_validation_response(response, 2)
        assert result.passed is True
        assert result.score == 0.75

    def test_parse_missing_fields_uses_defaults(self):
        """Test missing fields use default values of 0."""
        response = json.dumps(
            {
                "content_accuracy": 20,
                "total_score": 20,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        # Missing fields default to 0
        assert result.rubric_scores["visual_hierarchy"] == 0.0
        assert result.rubric_scores["brand_alignment"] == 0.0

    def test_parse_stores_raw_feedback(self):
        """Test raw feedback is stored in result."""
        response = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 18,
                "brand_alignment": 17,
                "image_quality": 13,
                "layout_effectiveness": 12,
                "total_score": 85,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.raw_feedback is not None
        assert "content_accuracy" in result.raw_feedback

    def test_parse_handles_exception_gracefully(self):
        """Test unexpected exceptions are handled gracefully."""
        # Create response that will cause issues during processing
        response = json.dumps(
            {
                "content_accuracy": "not_a_number",  # Will fail float conversion
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 10,
                "layout_effectiveness": 10,
                "total_score": 60,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        # Should return fallback on error
        assert result.passed is True
        assert "Validation error" in result.issues


class TestValidateSlide:
    """Tests for validate_slide method."""

    def setup_method(self):
        """Set up test fixtures with mocked Gemini client."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            self.mock_genai = mock_genai
            self.mock_client = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_validate_slide_image_not_found_raises_error(self):
        """Test validate_slide raises error when image not found."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )
        with pytest.raises(FileNotFoundError) as exc_info:
            self.validator.validate_slide(
                slide_image_path="nonexistent.jpg",
                original_slide=slide,
                style_config={},
                slide_type="content",
            )
        assert "Slide image not found" in str(exc_info.value)

    def test_validate_slide_successful(self):
        """Test successful slide validation."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test Slide",
            content_bullets=[("Point 1", 0)],
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 28,
                "visual_hierarchy": 18,
                "brand_alignment": 18,
                "image_quality": 14,
                "layout_effectiveness": 14,
                "total_score": 92,
                "issues": [],
                "suggestions": [],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"fake image bytes")):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.validator.validate_slide(
                    slide_image_path="test_slide.jpg",
                    original_slide=slide,
                    style_config={"brand_colors": ["#DD0033"]},
                    slide_type="content",
                )

        assert result.passed is True
        assert result.score > 0.9

    def test_validate_slide_with_large_image_warning(self, capsys):
        """Test validation prints warning for large images."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        # Mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": [],
                "suggestions": [],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        # Create large image data (>10MB)
        large_image_data = b"x" * (11 * 1024 * 1024)

        with patch("builtins.open", mock_open(read_data=large_image_data)):
            with patch("pathlib.Path.exists", return_value=True):
                self.validator.validate_slide(
                    slide_image_path="large_slide.jpg",
                    original_slide=slide,
                    style_config={},
                    slide_type="content",
                )

        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "Large image size" in captured.out

    def test_validate_slide_api_error_retries(self, capsys):
        """Test validation retries on API errors."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        # Fail twice, succeed on third try
        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": [],
                "suggestions": [],
            }
        )
        self.mock_client.models.generate_content.side_effect = [
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_response,
        ]

        with patch("builtins.open", mock_open(read_data=b"fake image")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("time.sleep"):  # Speed up test
                    result = self.validator.validate_slide(
                        slide_image_path="test.jpg",
                        original_slide=slide,
                        style_config={},
                        slide_type="content",
                    )

        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "Retrying" in captured.out
        assert result.passed is True

    def test_validate_slide_max_retries_exceeded(self, capsys):
        """Test validation returns fallback after max retries."""
        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        # Fail all 3 attempts
        self.mock_client.models.generate_content.side_effect = Exception(
            "Persistent API Error"
        )

        with patch("builtins.open", mock_open(read_data=b"fake image")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("time.sleep"):  # Speed up test
                    result = self.validator.validate_slide(
                        slide_image_path="test.jpg",
                        original_slide=slide,
                        style_config={},
                        slide_type="content",
                    )

        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "after 3 attempts" in captured.out
        # Should return fallback (pass with threshold)
        assert result.passed is True
        assert result.score == self.validator.VALIDATION_THRESHOLD
        assert "Validation unavailable" in result.raw_feedback

    def test_validate_slide_value_error_no_retry(self, capsys):
        """Test validation does not retry on ValueError."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        # Raise ValueError (non-retryable)
        self.mock_client.models.generate_content.side_effect = ValueError(
            "Invalid response format"
        )

        with patch("builtins.open", mock_open(read_data=b"fake image")):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.validator.validate_slide(
                    slide_image_path="test.jpg",
                    original_slide=slide,
                    style_config={},
                    slide_type="content",
                )

        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert "Invalid validation response" in captured.out
        # Should not mention "Retrying"
        assert "Retrying" not in captured.out
        # Returns fallback
        assert result.passed is True

    def test_validate_slide_file_not_found_no_retry(self):
        """Test validation does not retry on FileNotFoundError."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        with pytest.raises(FileNotFoundError):
            self.validator.validate_slide(
                slide_image_path="missing.jpg",
                original_slide=slide,
                style_config={},
                slide_type="content",
            )

    def test_validate_slide_calls_gemini_correctly(self):
        """Test validate_slide calls Gemini API with correct parameters."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": [],
                "suggestions": [],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"test image data")):
            with patch("pathlib.Path.exists", return_value=True):
                self.validator.validate_slide(
                    slide_image_path="test.jpg",
                    original_slide=slide,
                    style_config={},
                    slide_type="content",
                )

        # Verify API call
        self.mock_client.models.generate_content.assert_called_once()
        call_kwargs = self.mock_client.models.generate_content.call_args
        assert call_kwargs.kwargs["model"] == "gemini-2.0-flash-exp"


class TestValidateSlideIntegration:
    """Integration-style tests for validate_slide with various scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            self.mock_client = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_validate_title_slide(self):
        """Test validation of title slide."""
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Presentation Title",
            subtitle="Presented by Author",
            content_bullets=[],
        )

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 30,
                "visual_hierarchy": 20,
                "brand_alignment": 18,
                "image_quality": 15,
                "layout_effectiveness": 14,
                "total_score": 97,
                "issues": [],
                "suggestions": [],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image")):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.validator.validate_slide(
                    slide_image_path="slide1.jpg",
                    original_slide=slide,
                    style_config={"brand_colors": ["#DD0033"], "style": "corporate"},
                    slide_type="title",
                )

        assert result.passed is True
        assert result.score > 0.95

    def test_validate_content_slide_with_issues(self):
        """Test validation of content slide with issues detected."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Key Points",
            content_bullets=[
                ("First important point", 0),
                ("Second important point", 0),
                ("Sub-point detail", 1),
            ],
            graphic="A supporting diagram",
        )

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 20,
                "visual_hierarchy": 14,
                "brand_alignment": 12,
                "image_quality": 8,
                "layout_effectiveness": 10,
                "total_score": 64,
                "issues": [
                    "Third bullet point is cut off",
                    "Image overlaps text area",
                    "Brand colors not consistent",
                ],
                "suggestions": [
                    "Reduce text or use smaller font",
                    "Reposition image to right side",
                    "Use #DD0033 for highlights",
                ],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image")):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.validator.validate_slide(
                    slide_image_path="slide3.jpg",
                    original_slide=slide,
                    style_config={"brand_colors": ["#DD0033"]},
                    slide_type="text_image",
                )

        assert result.passed is False
        assert result.score < 0.75
        assert len(result.issues) == 3
        assert len(result.suggestions) == 3

    def test_validate_image_only_slide(self):
        """Test validation of image-only slide."""
        slide = Slide(
            number=5,
            slide_type="CONTENT",
            title="System Architecture",
            content_bullets=[],
            graphic="A detailed system architecture diagram showing microservices",
        )

        mock_response = MagicMock()
        mock_response.text = json.dumps(
            {
                "content_accuracy": 27,
                "visual_hierarchy": 18,
                "brand_alignment": 17,
                "image_quality": 14,
                "layout_effectiveness": 13,
                "total_score": 89,
                "issues": ["Image could be higher resolution"],
                "suggestions": ["Use SVG format for diagrams"],
            }
        )
        self.mock_client.models.generate_content.return_value = mock_response

        with patch("builtins.open", mock_open(read_data=b"image")):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.validator.validate_slide(
                    slide_image_path="slide5.jpg",
                    original_slide=slide,
                    style_config={},
                    slide_type="image",
                )

        assert result.passed is True
        assert len(result.issues) == 1


class TestGenaiNotAvailable:
    """Tests for when google-genai package is not available."""

    def test_genai_import_error_handled(self):
        """Test that import error for genai is handled gracefully."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", False),
            patch("plugin.lib.presentation.visual_validator.genai", None),
        ):
            # Should be able to import module without error
            from plugin.lib.presentation.visual_validator import (
                GENAI_AVAILABLE,
            )

            assert GENAI_AVAILABLE is False


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            self.mock_client = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_slide_with_empty_title(self):
        """Test handling slide with empty title."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="",
            content_bullets=[("Point", 0)],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Title:** " in prompt

    def test_slide_with_special_characters_in_title(self):
        """Test handling slide with special characters."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title='Title with "quotes" and {braces}',
            content_bullets=[],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert '"quotes"' in prompt
        assert "{braces}" in prompt

    def test_slide_with_unicode_content(self):
        """Test handling slide with unicode characters."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Title with emoji and unicode",
            content_bullets=[("Point with special chars", 0)],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "emoji" in prompt.lower() or "unicode" in prompt.lower()

    def test_parse_response_with_extra_fields(self):
        """Test parsing response with extra unexpected fields."""
        response = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": [],
                "suggestions": [],
                "extra_field": "should be ignored",
                "another_extra": 123,
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is True

    def test_parse_response_with_empty_arrays(self):
        """Test parsing response with empty issues and suggestions."""
        response = json.dumps(
            {
                "content_accuracy": 30,
                "visual_hierarchy": 20,
                "brand_alignment": 20,
                "image_quality": 15,
                "layout_effectiveness": 15,
                "total_score": 100,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.issues == []
        assert result.suggestions == []

    def test_parse_response_with_null_values(self):
        """Test parsing response with null values."""
        response = json.dumps(
            {
                "content_accuracy": 25,
                "visual_hierarchy": 15,
                "brand_alignment": 15,
                "image_quality": 12,
                "layout_effectiveness": 12,
                "total_score": 79,
                "issues": None,
                "suggestions": None,
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        # Should handle None gracefully
        assert result is not None

    def test_boundary_threshold_score(self):
        """Test score exactly at threshold boundary."""
        response = json.dumps(
            {
                "content_accuracy": 22.5,  # 0.75 * 30
                "visual_hierarchy": 15,  # 0.75 * 20
                "brand_alignment": 15,  # 0.75 * 20
                "image_quality": 11.25,  # 0.75 * 15
                "layout_effectiveness": 11.25,  # 0.75 * 15
                "total_score": 75,
                "issues": [],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is True  # >= 0.75 should pass
        assert abs(result.score - 0.75) < 0.01

    def test_just_below_threshold_score(self):
        """Test score just below threshold."""
        response = json.dumps(
            {
                "content_accuracy": 22,  # slightly below 0.75 * 30
                "visual_hierarchy": 14,  # slightly below 0.75 * 20
                "brand_alignment": 14,  # slightly below 0.75 * 20
                "image_quality": 11,  # slightly below 0.75 * 15
                "layout_effectiveness": 11,  # slightly below 0.75 * 15
                "total_score": 72,
                "issues": ["Minor issues"],
                "suggestions": [],
            }
        )
        result = self.validator._parse_validation_response(response, 1)
        assert result.passed is False  # < 0.75 should fail

    def test_deeply_nested_bullet_points(self):
        """Test slide with deeply nested bullet points."""
        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Nested Content",
            content_bullets=[
                ("Top level", 0),
                ("First indent", 1),
                ("Second indent", 2),
            ],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "- Top level" in prompt
        assert "  - First indent" in prompt
        assert "    - Second indent" in prompt


class TestStyleConfigVariations:
    """Tests for various style configuration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_style_config_with_multiple_brand_colors(self):
        """Test style config with multiple brand colors."""
        slide = Slide(number=1, slide_type="CONTENT", title="Test")
        style_config = {
            "brand_colors": ["#DD0033", "#004F71", "#FFFFFF", "#333333", "#F5F5F5"]
        }
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        assert "#DD0033" in prompt
        assert "#004F71" in prompt
        assert "#FFFFFF" in prompt

    def test_style_config_empty(self):
        """Test empty style config."""
        slide = Slide(number=1, slide_type="CONTENT", title="Test")
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Brand Colors:** Not specified" in prompt
        assert "**Style:** professional" in prompt  # Default

    def test_style_config_with_custom_style(self):
        """Test style config with custom style description."""
        slide = Slide(number=1, slide_type="CONTENT", title="Test")
        style_config = {"style": "modern minimalist with bold accents"}
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        assert "modern minimalist with bold accents" in prompt

    def test_style_config_missing_keys(self):
        """Test style config with some missing keys."""
        slide = Slide(number=1, slide_type="CONTENT", title="Test")
        style_config = {"some_other_key": "value"}
        prompt = self.validator._build_validation_prompt(slide, style_config, "content")
        # Should use defaults for missing keys
        assert "**Brand Colors:** Not specified" in prompt
        assert "**Style:** professional" in prompt


class TestSlideTypeVariations:
    """Tests for different slide type classifications."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("plugin.lib.presentation.visual_validator.GENAI_AVAILABLE", True),
            patch("plugin.lib.presentation.visual_validator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.visual_validator import (
                VisualValidator,
            )

            self.validator = VisualValidator(api_key="test-key")

    def test_prompt_with_title_type(self):
        """Test prompt generation for title slide type."""
        slide = Slide(number=1, slide_type="TITLE SLIDE", title="Main Title")
        prompt = self.validator._build_validation_prompt(slide, {}, "title")
        assert "**Type:** title" in prompt

    def test_prompt_with_section_type(self):
        """Test prompt generation for section slide type."""
        slide = Slide(number=5, slide_type="SECTION DIVIDER", title="New Section")
        prompt = self.validator._build_validation_prompt(slide, {}, "section")
        assert "**Type:** section" in prompt

    def test_prompt_with_content_type(self):
        """Test prompt generation for content slide type."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Content",
            content_bullets=[("Point", 0)],
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "content")
        assert "**Type:** content" in prompt

    def test_prompt_with_image_type(self):
        """Test prompt generation for image slide type."""
        slide = Slide(
            number=4,
            slide_type="CONTENT",
            title="Visual",
            graphic="A diagram",
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "image")
        assert "**Type:** image" in prompt

    def test_prompt_with_text_image_type(self):
        """Test prompt generation for text_image slide type."""
        slide = Slide(
            number=6,
            slide_type="CONTENT",
            title="Mixed",
            content_bullets=[("Point", 0)],
            graphic="Supporting image",
        )
        prompt = self.validator._build_validation_prompt(slide, {}, "text_image")
        assert "**Type:** text_image" in prompt
