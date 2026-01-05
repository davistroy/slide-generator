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
