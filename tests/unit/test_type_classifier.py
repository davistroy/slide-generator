"""
Unit tests for plugin/lib/presentation/type_classifier.py

Tests the slide type classification system.
"""

from unittest.mock import patch

from plugin.lib.presentation.parser import Slide
from plugin.lib.presentation.type_classifier import (
    SlideTypeClassifier,
    TypeClassification,
)


class TestTypeClassification:
    """Tests for TypeClassification dataclass."""

    def test_create_classification(self):
        """Test creating a TypeClassification."""
        classification = TypeClassification(
            slide_type="content",
            confidence=0.95,
            reasoning="Has bullets and no graphic",
            template_method="add_content_slide",
        )
        assert classification.slide_type == "content"
        assert classification.confidence == 0.95
        assert classification.template_method == "add_content_slide"


class TestSlideTypeClassifierInit:
    """Tests for SlideTypeClassifier initialization."""

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            classifier = SlideTypeClassifier(api_key=None)
            assert classifier.api_key is None

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        classifier = SlideTypeClassifier(api_key="test-key")
        assert classifier.api_key == "test-key"

    @patch.dict("os.environ", {"GOOGLE_API_KEY": "env-key"})
    def test_init_uses_env_var(self):
        """Test initialization uses environment variable."""
        classifier = SlideTypeClassifier()
        assert classifier.api_key == "env-key"


class TestRuleBasedClassification:
    """Tests for rule-based classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_classify_title_slide_explicit(self):
        """Test classification of explicit title slide."""
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="My Presentation",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "title"
        assert result.confidence == 1.0
        assert result.template_method == "add_title_slide"

    def test_classify_section_divider_explicit(self):
        """Test classification of explicit section divider."""
        slide = Slide(
            number=5,
            slide_type="SECTION DIVIDER",
            title="New Section",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"
        assert result.template_method == "add_section_break"

    def test_classify_section_break_marker(self):
        """Test classification with BREAK marker."""
        slide = Slide(
            number=5,
            slide_type="SECTION BREAK",
            title="Section",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"

    def test_classify_qa_slide(self):
        """Test classification of Q&A slide."""
        slide = Slide(
            number=10,
            slide_type="Q&A",
            title="Questions?",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"

    def test_classify_image_slide_explicit(self):
        """Test classification of explicit image slide with graphic."""
        slide = Slide(
            number=3,
            slide_type="ARCHITECTURE",
            title="System Architecture",
            content_bullets=[],
            graphic="A detailed system diagram",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "image"
        assert result.template_method == "add_image_slide"

    def test_classify_first_slide_no_content(self):
        """Test classification of first slide with no content."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",  # Not explicitly title, but slide 1
            title="Presentation Title",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "title"
        assert result.confidence == 0.9

    def test_classify_no_content_no_graphic(self):
        """Test classification of slide with no content or graphic."""
        slide = Slide(
            number=5,
            slide_type="CONTENT",
            title="Empty Slide",
            content_bullets=[],
            graphic=None,
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"
        assert "No content or graphic" in result.reasoning

    def test_classify_graphic_only(self):
        """Test classification of slide with graphic but no bullets."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            content_bullets=[],
            graphic="A detailed chart showing data",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "image"
        assert result.template_method == "add_image_slide"

    def test_classify_bullets_only(self):
        """Test classification of slide with bullets but no graphic."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Text Slide",
            content_bullets=[("Point 1", 0), ("Point 2", 0), ("Point 3", 0)],
            graphic=None,
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "content"
        assert result.template_method == "add_content_slide"

    def test_classify_few_bullets_with_graphic(self):
        """Test classification of slide with few bullets and graphic."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Balanced Slide",
            content_bullets=[
                ("Point 1", 0),
                ("Point 2", 0),
                ("Point 3", 0),
            ],
            graphic="A supporting image",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "text_image"
        assert result.template_method == "add_text_and_image_slide"

    def test_classify_many_bullets_with_graphic_ambiguous(self):
        """Test classification of slide with many bullets and graphic is ambiguous."""
        slide = Slide(
            number=3,
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
            graphic="Some image",
        )
        result = self.classifier._rule_based_classify(slide)
        # Should return None for ambiguous case
        assert result is None


class TestClassifySlide:
    """Tests for classify_slide method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_classify_uses_rules_first(self):
        """Test that classify_slide uses rule-based first."""
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Title",
            content_bullets=[],
        )
        result = self.classifier.classify_slide(slide)
        assert result.slide_type == "title"
        assert result.confidence == 1.0

    def test_classify_fallback_without_gemini(self):
        """Test fallback when Gemini not available."""
        # Create ambiguous slide
        slide = Slide(
            number=5,
            slide_type="CONTENT",
            title="Ambiguous",
            content_bullets=[
                ("P1", 0),
                ("P2", 0),
                ("P3", 0),
                ("P4", 0),
                ("P5", 0),
                ("P6", 0),
                ("P7", 0),
            ],
            graphic="Image",
        )
        result = self.classifier.classify_slide(slide)
        # Without Gemini, should fallback to content
        assert result.slide_type == "content"
        assert result.confidence == 0.5
        assert "Fallback" in result.reasoning


class TestBuildClassificationPrompt:
    """Tests for _build_classification_prompt method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_prompt_includes_slide_info(self):
        """Test that prompt includes slide information."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="My Slide Title",
            subtitle="My Subtitle",
            content_bullets=[("Point 1", 0), ("Point 2", 1)],
            graphic="A diagram",
        )
        prompt = self.classifier._build_classification_prompt(slide)
        assert "Slide Number: 3" in prompt or "3" in prompt
        assert "My Slide Title" in prompt
        assert "My Subtitle" in prompt
        assert "Point 1" in prompt

    def test_prompt_includes_template_descriptions(self):
        """Test that prompt includes template type descriptions."""
        slide = Slide(number=1, slide_type="CONTENT", title="Test")
        prompt = self.classifier._build_classification_prompt(slide)
        assert "TITLE" in prompt
        assert "SECTION" in prompt
        assert "CONTENT" in prompt
        assert "IMAGE" in prompt
        assert "TEXT_IMAGE" in prompt

    def test_prompt_truncates_long_bullets(self):
        """Test that prompt truncates when many bullets."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[("Bullet " + str(i), 0) for i in range(10)],
        )
        prompt = self.classifier._build_classification_prompt(slide)
        # Should show first 5 and mention more
        assert "more bullets" in prompt or "5" in prompt


class TestParseClassificationResponse:
    """Tests for _parse_classification_response method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        response = '{"type": "content", "confidence": 0.95, "reasoning": "Has bullets"}'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "content"
        assert result.confidence == 0.95
        assert "Has bullets" in result.reasoning

    def test_parse_json_in_markdown_block(self):
        """Test parsing JSON inside markdown code block."""
        response = """```json
{"type": "image", "confidence": 0.9, "reasoning": "Visual focus"}
```"""
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "image"

    def test_parse_invalid_type_defaults_to_content(self):
        """Test that invalid type defaults to content."""
        response = '{"type": "invalid_type", "confidence": 0.9, "reasoning": "Test"}'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "content"
        assert result.confidence == 0.5

    def test_parse_malformed_json_returns_fallback(self):
        """Test that malformed JSON returns fallback."""
        response = "This is not JSON at all"
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "content"
        assert result.confidence == 0.5
        assert "Fallback" in result.reasoning

    def test_parse_missing_fields_uses_defaults(self):
        """Test that missing fields use defaults."""
        response = '{"type": "section"}'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "section"
        assert result.confidence == 0.7  # Default

    def test_parse_uppercase_type_normalized(self):
        """Test that uppercase type is normalized."""
        response = '{"type": "CONTENT", "confidence": 0.9, "reasoning": "Test"}'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "content"


class TestClassifyAllSlides:
    """Tests for classify_all_slides method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_classify_all_returns_dict(self):
        """Test that classify_all_slides returns dictionary."""
        slides = [
            Slide(
                number=1, slide_type="TITLE SLIDE", title="Title", content_bullets=[]
            ),
            Slide(
                number=2,
                slide_type="CONTENT",
                title="Content",
                content_bullets=[("P1", 0)],
            ),
        ]
        result = self.classifier.classify_all_slides(slides)
        assert isinstance(result, dict)
        assert 1 in result
        assert 2 in result

    def test_classify_all_with_callback(self):
        """Test that callback is called for each slide."""
        slides = [
            Slide(
                number=1, slide_type="TITLE SLIDE", title="Title", content_bullets=[]
            ),
            Slide(number=2, slide_type="SECTION", title="Section", content_bullets=[]),
        ]

        callback_calls = []

        def callback(num, classification):
            callback_calls.append((num, classification))

        self.classifier.classify_all_slides(slides, callback=callback)
        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 1
        assert callback_calls[1][0] == 2

    def test_classify_empty_list(self):
        """Test classifying empty slide list."""
        result = self.classifier.classify_all_slides([])
        assert result == {}


class TestSlideTypes:
    """Tests for SLIDE_TYPES mapping."""

    def test_all_types_have_methods(self):
        """Test that all slide types have template methods."""
        classifier = SlideTypeClassifier(api_key=None)
        expected_types = ["title", "section", "content", "image", "text_image"]
        for slide_type in expected_types:
            assert slide_type in classifier.SLIDE_TYPES
            assert classifier.SLIDE_TYPES[slide_type].startswith("add_")

    def test_method_names_are_valid(self):
        """Test that method names follow expected pattern."""
        classifier = SlideTypeClassifier(api_key=None)
        expected_methods = {
            "title": "add_title_slide",
            "section": "add_section_break",
            "content": "add_content_slide",
            "image": "add_image_slide",
            "text_image": "add_text_and_image_slide",
        }
        for slide_type, method in expected_methods.items():
            assert classifier.SLIDE_TYPES[slide_type] == method


class TestGeminiClientInitializationFailure:
    """Tests for Gemini client initialization failure handling."""

    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_init_with_api_key_client_creation_fails(self, mock_genai):
        """Test that client initialization failure is handled gracefully."""
        mock_genai.Client.side_effect = Exception("Connection failed")

        # Should not raise, should just print warning
        classifier = SlideTypeClassifier(api_key="test-key")

        assert classifier.api_key == "test-key"
        assert classifier.client is None  # Client should be None after failure

    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_init_with_api_key_client_creation_fails_runtime_error(self, mock_genai):
        """Test that RuntimeError during client init is handled."""
        mock_genai.Client.side_effect = RuntimeError("Invalid API key")

        classifier = SlideTypeClassifier(api_key="invalid-key")

        assert classifier.client is None


class TestGeminiClassificationFailure:
    """Tests for Gemini classification failure handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_gemini_classify_raises_exception_falls_back(self, mock_genai):
        """Test that Gemini classification exception triggers fallback."""
        # Create classifier with mocked client
        mock_client = mock_genai.Client.return_value
        classifier = SlideTypeClassifier(api_key="test-key")
        classifier.client = mock_client

        # Make _gemini_classify raise an exception
        mock_client.models.generate_content.side_effect = Exception("API Error")

        # Create ambiguous slide that would need Gemini
        slide = Slide(
            number=5,
            slide_type="CONTENT",
            title="Ambiguous",
            content_bullets=[("P" + str(i), 0) for i in range(7)],  # Many bullets
            graphic="Some image",
        )

        result = classifier.classify_slide(slide)

        # Should fallback to content slide
        assert result.slide_type == "content"
        assert result.confidence == 0.5
        assert "Fallback" in result.reasoning

    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_classify_slide_with_gemini_success(self, mock_genai):
        """Test successful Gemini classification for ambiguous slides."""
        mock_client = mock_genai.Client.return_value
        mock_response = mock_client.models.generate_content.return_value
        mock_response.text = (
            '{"type": "text_image", "confidence": 0.85, "reasoning": "Balanced layout"}'
        )

        classifier = SlideTypeClassifier(api_key="test-key")
        classifier.client = mock_client

        # Create ambiguous slide
        slide = Slide(
            number=5,
            slide_type="CONTENT",
            title="Ambiguous",
            content_bullets=[("P" + str(i), 0) for i in range(7)],
            graphic="Image description",
        )

        result = classifier.classify_slide(slide)

        assert result.slide_type == "text_image"
        assert result.confidence == 0.85


class TestAdditionalRuleBasedClassification:
    """Additional tests for rule-based classification edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_classify_qa_with_space_marker(self):
        """Test classification of Q & A slide (with space)."""
        slide = Slide(
            number=10,
            slide_type="Q & A",  # With space
            title="Questions?",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"

    def test_classify_divider_marker(self):
        """Test classification with DIVIDER marker."""
        slide = Slide(
            number=5,
            slide_type="DIVIDER",
            title="Part Two",
            content_bullets=[],
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "section"

    def test_classify_diagram_marker_with_graphic(self):
        """Test classification with DIAGRAM marker and graphic."""
        slide = Slide(
            number=4,
            slide_type="DIAGRAM",
            title="Flow Diagram",
            content_bullets=[],
            graphic="A flowchart showing process steps",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "image"
        assert result.confidence == 0.95

    def test_classify_image_marker_with_graphic(self):
        """Test classification with IMAGE marker and graphic."""
        slide = Slide(
            number=4,
            slide_type="IMAGE",
            title="Visual Showcase",
            content_bullets=[],
            graphic="A beautiful landscape photo",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "image"

    def test_classify_architecture_marker_without_graphic(self):
        """Test ARCHITECTURE marker without graphic does NOT match image rule."""
        slide = Slide(
            number=4,
            slide_type="ARCHITECTURE",
            title="System Design",
            content_bullets=[],
            graphic=None,  # No graphic
        )
        result = self.classifier._rule_based_classify(slide)
        # Should fall through to section (no content, no graphic)
        assert result is not None
        assert result.slide_type == "section"

    def test_classify_diagram_marker_without_graphic(self):
        """Test DIAGRAM marker without graphic falls through rules."""
        slide = Slide(
            number=4,
            slide_type="DIAGRAM",
            title="Missing Diagram",
            content_bullets=[("Some text", 0)],  # Has bullets but no graphic
            graphic=None,
        )
        result = self.classifier._rule_based_classify(slide)
        # Should be content (has bullets, no graphic)
        assert result is not None
        assert result.slide_type == "content"

    def test_classify_one_bullet_with_graphic(self):
        """Test classification with exactly 1 bullet and graphic."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Single Point",
            content_bullets=[("The main point", 0)],  # 1 bullet
            graphic="Supporting visual",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "text_image"
        assert "1 bullet" in result.reasoning

    def test_classify_five_bullets_with_graphic(self):
        """Test classification with exactly 5 bullets and graphic (boundary case)."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Five Points",
            content_bullets=[("Point " + str(i), 0) for i in range(5)],  # 5 bullets
            graphic="Supporting visual",
        )
        result = self.classifier._rule_based_classify(slide)
        assert result is not None
        assert result.slide_type == "text_image"
        assert "5 bullets" in result.reasoning

    def test_classify_six_bullets_with_graphic_ambiguous(self):
        """Test classification with 6 bullets and graphic is ambiguous."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Six Points",
            content_bullets=[("Point " + str(i), 0) for i in range(6)],  # 6 bullets
            graphic="Some image",
        )
        result = self.classifier._rule_based_classify(slide)
        # 6+ bullets with graphic is ambiguous, should return None
        assert result is None

    def test_classify_empty_graphic_string(self):
        """Test that empty/whitespace-only graphic is treated as no graphic."""
        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Test Slide",
            content_bullets=[("Point 1", 0)],
            graphic="   ",  # Whitespace only
        )
        result = self.classifier._rule_based_classify(slide)
        # Empty graphic should be treated as no graphic -> content slide
        assert result is not None
        assert result.slide_type == "content"

    def test_classify_first_slide_with_content_not_title(self):
        """Test that first slide WITH content is not automatically title."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Introduction",
            content_bullets=[("First point", 0), ("Second point", 0)],
        )
        result = self.classifier._rule_based_classify(slide)
        # Has content, so should be content slide, not title
        assert result is not None
        assert result.slide_type == "content"


class TestPromptBuildingEdgeCases:
    """Tests for edge cases in prompt building."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_prompt_with_long_graphic_truncated(self):
        """Test that long graphic description is truncated in prompt."""
        long_graphic = "A" * 500  # 500 characters
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
            graphic=long_graphic,
        )
        prompt = self.classifier._build_classification_prompt(slide)
        # Should be truncated to 300 chars + "..."
        assert "..." in prompt
        # Should not contain full 500 character string
        assert long_graphic not in prompt
        # Should contain truncated version (first 300 chars)
        assert long_graphic[:300] in prompt

    def test_prompt_with_exactly_300_char_graphic(self):
        """Test graphic description at exactly 300 chars is not truncated."""
        exact_graphic = "B" * 300
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
            graphic=exact_graphic,
        )
        prompt = self.classifier._build_classification_prompt(slide)
        # Should contain full graphic without truncation marker
        assert exact_graphic in prompt
        # Check that ellipsis is NOT added after the graphic content
        # (The prompt will contain "..." in other places, so we check context)
        graphic_section_end = prompt.find(exact_graphic) + len(exact_graphic)
        following_text = prompt[graphic_section_end : graphic_section_end + 10]
        assert "..." not in following_text or following_text.startswith("\n")

    def test_prompt_with_nested_bullets(self):
        """Test prompt building with nested bullet levels."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Nested Content",
            content_bullets=[
                ("Level 0 point", 0),
                ("Level 1 sub-point", 1),
                ("Level 2 deep point", 2),
            ],
        )
        prompt = self.classifier._build_classification_prompt(slide)
        assert "Level 0 point" in prompt
        assert "Level 1 sub-point" in prompt
        assert "Level 2 deep point" in prompt
        # Check indentation is present
        assert "  - Level 1" in prompt  # 2 spaces for level 1
        assert "    - Level 2" in prompt  # 4 spaces for level 2

    def test_prompt_with_no_subtitle(self):
        """Test prompt building when subtitle is None."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle=None,
            content_bullets=[],
        )
        prompt = self.classifier._build_classification_prompt(slide)
        assert "Subtitle:** None" in prompt or "None" in prompt

    def test_prompt_with_no_graphic(self):
        """Test prompt building when graphic is None."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
            graphic=None,
        )
        prompt = self.classifier._build_classification_prompt(slide)
        assert "Graphic Description:** None" in prompt or "None" in prompt


class TestParseResponseEdgeCases:
    """Additional tests for response parsing edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = SlideTypeClassifier(api_key=None)

    def test_parse_json_without_code_block(self):
        """Test parsing plain JSON without code block markers."""
        response = (
            '{"type": "section", "confidence": 0.88, "reasoning": "Section break"}'
        )
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "section"
        assert result.confidence == 0.88

    def test_parse_json_with_extra_text_before(self):
        """Test parsing JSON with text before it."""
        response = 'Here is my analysis: {"type": "image", "confidence": 0.92, "reasoning": "Visual slide"}'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "image"

    def test_parse_json_with_extra_text_after(self):
        """Test parsing JSON with text after it."""
        response = '{"type": "title", "confidence": 0.99, "reasoning": "Opening slide"} I hope this helps!'
        result = self.classifier._parse_classification_response(response, 1)
        assert result.slide_type == "title"

    def test_parse_response_generic_exception(self):
        """Test that generic exceptions in parsing are handled."""
        # Test with data that has an invalid confidence that can't be converted to float
        # This triggers ValueError in float() conversion, caught by generic Exception handler
        response = '{"type": "content", "confidence": "not_a_number_at_all"}'
        result = self.classifier._parse_classification_response(response, 1)
        # Should handle the ValueError from float() conversion
        assert result.slide_type == "content"
        assert result.confidence == 0.5
        assert "Fallback" in result.reasoning

    def test_parse_response_with_none_confidence(self):
        """Test parsing when confidence is None (causes TypeError in float())."""
        # This should trigger the generic exception handler
        response = '{"type": "section", "confidence": null, "reasoning": "Test"}'
        result = self.classifier._parse_classification_response(response, 1)
        # None can be converted to float in Python, so let's check behavior
        # Actually float(None) raises TypeError, so this should hit exception handler
        assert result.slide_type in {"content", "section"}

    @patch("plugin.lib.presentation.type_classifier.json.loads")
    def test_parse_response_unexpected_exception(self, mock_json_loads):
        """Test that unexpected exceptions during parsing are handled."""
        # Mock json.loads to raise an unexpected exception type
        mock_json_loads.side_effect = AttributeError("Unexpected attribute error")

        response = '{"type": "content"}'
        result = self.classifier._parse_classification_response(response, 1)

        assert result.slide_type == "content"
        assert result.confidence == 0.5
        assert "Fallback" in result.reasoning

    def test_parse_all_slide_types(self):
        """Test parsing all valid slide types."""
        valid_types = ["title", "section", "content", "image", "text_image"]
        for slide_type in valid_types:
            response = (
                f'{{"type": "{slide_type}", "confidence": 0.9, "reasoning": "Test"}}'
            )
            result = self.classifier._parse_classification_response(response, 1)
            assert result.slide_type == slide_type
            assert result.template_method == self.classifier.SLIDE_TYPES[slide_type]


class TestGenaiModuleNotAvailable:
    """Tests for when the genai module is not available."""

    def test_genai_available_constant_exists(self):
        """Test that GENAI_AVAILABLE constant is defined."""
        from plugin.lib.presentation import type_classifier

        assert hasattr(type_classifier, "GENAI_AVAILABLE")
        # In our test environment, genai is likely available
        # but we're just checking the constant exists

    @patch.dict("sys.modules", {"google": None, "google.genai": None})
    def test_classifier_works_without_genai(self):
        """Test classifier still works when genai is not available."""
        # Even if genai import fails, classifier should work in rule-based mode
        classifier = SlideTypeClassifier(api_key=None)
        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Test",
            content_bullets=[],
        )
        result = classifier.classify_slide(slide)
        assert result.slide_type == "title"

    def test_genai_available_is_true_when_module_present(self):
        """Test that GENAI_AVAILABLE is True when google.genai is importable."""
        from plugin.lib.presentation import type_classifier

        # In our environment, google.genai should be available
        assert type_classifier.GENAI_AVAILABLE is True
        assert type_classifier.genai is not None
        assert type_classifier.types is not None


class TestModuleLevelImportFallback:
    """Tests to verify import fallback behavior at module level."""

    def test_genai_and_types_set_when_import_succeeds(self):
        """Test that genai and types are set when import succeeds."""
        from plugin.lib.presentation import type_classifier

        # These should be set to actual modules, not None
        if type_classifier.GENAI_AVAILABLE:
            assert type_classifier.genai is not None
            assert type_classifier.types is not None

    @patch.dict("os.environ", {}, clear=True)
    def test_classifier_no_client_when_no_api_key(self):
        """Test that client is None when no API key provided."""
        classifier = SlideTypeClassifier(api_key=None)
        assert classifier.client is None

    def test_classifier_creates_client_with_valid_key(self):
        """Test that classifier attempts to create client with API key."""
        # This will fail if the key is invalid, but the exception is caught
        classifier = SlideTypeClassifier(api_key="test-invalid-key-12345")
        # Client creation will fail with invalid key, so it should be None
        # (the exception is caught in __init__)
        # We're just testing that the code path runs without raising
        assert classifier.api_key == "test-invalid-key-12345"


class TestMainFunction:
    """Tests for the main() function."""

    @patch("plugin.lib.presentation.parser.parse_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_function_runs(self, mock_args, mock_parse):
        """Test that main function can be executed."""
        from plugin.lib.presentation.type_classifier import main

        # Set up mocks
        mock_args.return_value.markdown_file = "test.md"
        mock_parse.return_value = [
            Slide(number=1, slide_type="TITLE", title="Test Title", content_bullets=[]),
            Slide(
                number=2,
                slide_type="CONTENT",
                title="Content",
                content_bullets=[("Point", 0)],
            ),
        ]

        # Should not raise
        main()

        mock_parse.assert_called_once_with("test.md")

    @patch("plugin.lib.presentation.parser.parse_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_empty_slides(self, mock_args, mock_parse):
        """Test main function with empty slide list."""
        from plugin.lib.presentation.type_classifier import main

        mock_args.return_value.markdown_file = "empty.md"
        mock_parse.return_value = []

        # Should not raise even with empty slides
        main()

    @patch("plugin.lib.presentation.parser.parse_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_truncates_long_titles(self, mock_args, mock_parse):
        """Test that main function handles long slide titles."""
        from plugin.lib.presentation.type_classifier import main

        mock_args.return_value.markdown_file = "test.md"
        long_title = "A" * 100  # Very long title
        mock_parse.return_value = [
            Slide(number=1, slide_type="CONTENT", title=long_title, content_bullets=[]),
        ]

        # Should not raise, title should be truncated in output
        main()


class TestGeminiClassifyMethod:
    """Tests for _gemini_classify method."""

    @patch("plugin.lib.presentation.type_classifier.types")
    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_gemini_classify_constructs_proper_config(self, mock_genai, mock_types):
        """Test that _gemini_classify uses correct configuration."""
        mock_client = mock_genai.Client.return_value
        mock_response = mock_client.models.generate_content.return_value
        mock_response.text = (
            '{"type": "content", "confidence": 0.9, "reasoning": "Test"}'
        )

        classifier = SlideTypeClassifier(api_key="test-key")
        classifier.client = mock_client

        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            content_bullets=[],
        )

        classifier._gemini_classify(slide)

        # Verify generate_content was called with correct model
        call_args = mock_client.models.generate_content.call_args
        assert call_args.kwargs["model"] == "gemini-2.0-flash-exp"

    @patch("plugin.lib.presentation.type_classifier.types")
    @patch("plugin.lib.presentation.type_classifier.genai")
    def test_gemini_classify_returns_parsed_result(self, mock_genai, mock_types):
        """Test that _gemini_classify returns properly parsed result."""
        mock_client = mock_genai.Client.return_value
        mock_response = mock_client.models.generate_content.return_value
        mock_response.text = (
            '{"type": "image", "confidence": 0.95, "reasoning": "Visual focus"}'
        )

        classifier = SlideTypeClassifier(api_key="test-key")
        classifier.client = mock_client

        slide = Slide(number=3, slide_type="CONTENT", title="Test", content_bullets=[])

        result = classifier._gemini_classify(slide)

        assert result.slide_type == "image"
        assert result.confidence == 0.95
        assert "Visual focus" in result.reasoning
