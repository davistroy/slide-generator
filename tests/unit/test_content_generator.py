"""
Unit tests for plugin/lib/content_generator.py

Tests the ContentGenerator class.
"""

import pytest
from unittest.mock import MagicMock, patch

from plugin.lib.content_generator import ContentGenerator, get_content_generator


class TestContentGeneratorInit:
    """Tests for ContentGenerator initialization."""

    def test_init_default_style_guide(self):
        """Test initialization with default style guide."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            generator = ContentGenerator()
            assert generator.style_guide is not None
            assert "tone" in generator.style_guide
            assert "audience" in generator.style_guide

    def test_init_custom_style_guide(self):
        """Test initialization with custom style guide."""
        custom_guide = {
            "tone": "casual",
            "audience": "students",
            "max_bullets_per_slide": 3,
        }
        with patch("plugin.lib.content_generator.get_claude_client"):
            generator = ContentGenerator(style_guide=custom_guide)
            assert generator.style_guide == custom_guide

    def test_default_style_guide_values(self):
        """Test default style guide has expected values."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            generator = ContentGenerator()
            guide = generator._default_style_guide()
            assert guide["tone"] == "professional"
            assert guide["audience"] == "general technical"
            assert guide["reading_level"] == "college"
            assert guide["max_bullets_per_slide"] == 5
            assert guide["max_words_per_bullet"] == 15
            assert guide["citation_style"] == "APA"


class TestGenerateTitleWithoutAPI:
    """Tests for generate_title that don't require API calls."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_generate_title_uses_existing_title(self):
        """Test generate_title uses existing good title from outline."""
        slide = {
            "title": "Rochester 2GC Carburetor Overview",
            "purpose": "Introduce carburetor",
            "key_points": ["history", "features"],
        }
        title = self.generator.generate_title(slide)
        assert title == "Rochester 2GC Carburetor Overview"

    def test_generate_title_uses_existing_title_with_whitespace(self):
        """Test generate_title handles whitespace in existing title."""
        slide = {
            "title": "  Good Title Here  ",
            "purpose": "Test purpose",
            "key_points": [],
        }
        title = self.generator.generate_title(slide)
        assert title == "Good Title Here"

    def test_generate_title_ignores_placeholder_point_about(self):
        """Test generate_title ignores 'point about' placeholder."""
        slide = {
            "title": "Point about carburetors",
            "purpose": "Explain carburetors",
            "key_points": ["overview"],
        }
        with patch.object(
            self.generator.client, "generate_text", return_value="Generated Title"
        ):
            title = self.generator.generate_title(slide)
            assert title == "Generated Title"

    def test_generate_title_ignores_placeholder_point_1(self):
        """Test generate_title ignores 'point 1' placeholder."""
        slide = {
            "title": "Point 1",
            "purpose": "First point",
            "key_points": [],
        }
        with patch.object(
            self.generator.client, "generate_text", return_value="Better Title"
        ):
            title = self.generator.generate_title(slide)
            assert title == "Better Title"

    def test_generate_title_ignores_short_title(self):
        """Test generate_title ignores very short titles."""
        slide = {
            "title": "Ok",  # Too short
            "purpose": "Test purpose",
            "key_points": [],
        }
        with patch.object(
            self.generator.client, "generate_text", return_value="Longer Title"
        ):
            title = self.generator.generate_title(slide)
            assert title == "Longer Title"

    def test_generate_title_ignores_extracted_placeholder(self):
        """Test generate_title ignores 'extracted' placeholder."""
        slide = {
            "title": "Extracted from research",
            "purpose": "Test",
            "key_points": [],
        }
        with patch.object(
            self.generator.client, "generate_text", return_value="New Title"
        ):
            title = self.generator.generate_title(slide)
            assert title == "New Title"


class TestFormatSlideMarkdown:
    """Tests for format_slide_markdown method."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_format_slide_markdown_basic(self):
        """Test basic markdown formatting."""
        result = self.generator.format_slide_markdown(
            slide_number=1,
            slide_type="CONTENT",
            title="Test Title",
            subtitle=None,
            bullets=["Point one", "Point two"],
            graphics_description="A visual description",
            speaker_notes="These are speaker notes.",
            citations=None,
        )

        assert "## SLIDE 1: CONTENT" in result
        assert "**Title:** Test Title" in result
        assert "- Point one" in result
        assert "- Point two" in result
        assert "**GRAPHICS:**" in result
        assert "A visual description" in result
        assert "**SPEAKER NOTES:**" in result
        assert "These are speaker notes." in result

    def test_format_slide_markdown_with_subtitle(self):
        """Test markdown formatting with subtitle."""
        result = self.generator.format_slide_markdown(
            slide_number=1,
            slide_type="TITLE SLIDE",
            title="Main Title",
            subtitle="A Subtitle Here",
            bullets=[],
            graphics_description="Title visual",
            speaker_notes="Opening remarks",
            citations=None,
        )

        assert "**Subtitle:** A Subtitle Here" in result

    def test_format_slide_markdown_without_subtitle(self):
        """Test markdown formatting without subtitle."""
        result = self.generator.format_slide_markdown(
            slide_number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle=None,
            bullets=["Bullet"],
            graphics_description="Visual",
            speaker_notes="Notes",
            citations=None,
        )

        assert "**Subtitle:**" not in result

    def test_format_slide_markdown_with_citations(self):
        """Test markdown formatting with citations."""
        result = self.generator.format_slide_markdown(
            slide_number=2,
            slide_type="CONTENT",
            title="Research Results",
            subtitle=None,
            bullets=["Finding one"],
            graphics_description="Chart",
            speaker_notes="Discussing findings",
            citations=["cite-001", "cite-002"],
        )

        assert "**BACKGROUND:**" in result
        assert "**Citations:**" in result
        assert "- cite-001" in result
        assert "- cite-002" in result

    def test_format_slide_markdown_empty_bullets(self):
        """Test markdown formatting with empty bullets list."""
        result = self.generator.format_slide_markdown(
            slide_number=1,
            slide_type="SECTION DIVIDER",
            title="New Section",
            subtitle=None,
            bullets=[],
            graphics_description="Section visual",
            speaker_notes="Transition notes",
            citations=None,
        )

        assert "**Content:**" in result
        # Should still have content section but no bullet points
        assert "- " not in result.split("**GRAPHICS:**")[0].split("**Content:**")[1]

    def test_format_slide_markdown_ends_with_separator(self):
        """Test markdown ends with slide separator."""
        result = self.generator.format_slide_markdown(
            slide_number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle=None,
            bullets=["Point"],
            graphics_description="Visual",
            speaker_notes="Notes",
            citations=None,
        )

        assert result.rstrip().endswith("---")


class TestGenerateBulletsMocked:
    """Tests for generate_bullets with mocked API."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_generate_bullets_parses_numbered_list(self):
        """Test generate_bullets parses numbered list response."""
        mock_response = """1. First bullet point here
2. Second bullet point here
3. Third bullet point here"""

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_response
        ):
            bullets = self.generator.generate_bullets(
                {"purpose": "test", "key_points": []}
            )
            assert len(bullets) == 3
            assert bullets[0] == "First bullet point here"
            assert bullets[1] == "Second bullet point here"
            assert bullets[2] == "Third bullet point here"

    def test_generate_bullets_parses_dashed_list(self):
        """Test generate_bullets parses dashed list response."""
        mock_response = """- First bullet
- Second bullet
- Third bullet"""

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_response
        ):
            bullets = self.generator.generate_bullets(
                {"purpose": "test", "key_points": []}
            )
            assert len(bullets) == 3
            assert bullets[0] == "First bullet"

    def test_generate_bullets_respects_max_limit(self):
        """Test generate_bullets limits to max_bullets_per_slide."""
        mock_response = """1. One
2. Two
3. Three
4. Four
5. Five
6. Six
7. Seven"""

        self.generator.style_guide["max_bullets_per_slide"] = 5

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_response
        ):
            bullets = self.generator.generate_bullets(
                {"purpose": "test", "key_points": []}
            )
            assert len(bullets) <= 5

    def test_generate_bullets_handles_empty_lines(self):
        """Test generate_bullets handles empty lines in response."""
        mock_response = """1. First bullet

2. Second bullet

3. Third bullet"""

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_response
        ):
            bullets = self.generator.generate_bullets(
                {"purpose": "test", "key_points": []}
            )
            assert len(bullets) == 3
            assert "" not in bullets


class TestGenerateSpeakerNotesMocked:
    """Tests for generate_speaker_notes with mocked API."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_generate_speaker_notes_returns_response(self):
        """Test generate_speaker_notes returns formatted response."""
        mock_notes = """[Pause and look at the audience]

Welcome everyone to this presentation. Today we'll be discussing some important topics.

[Gesture to slide] As you can see, we have several key points to cover.

[Transition] Let's move on to the first topic."""

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_notes
        ):
            notes = self.generator.generate_speaker_notes(
                slide={"purpose": "test", "slide_type": "CONTENT"},
                title="Test Title",
                bullets=["Point 1", "Point 2"],
            )
            assert "[Pause" in notes or "Pause" in notes
            assert len(notes) > 0


class TestGenerateGraphicsDescriptionMocked:
    """Tests for generate_graphics_description with mocked API."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_generate_graphics_description_returns_response(self):
        """Test generate_graphics_description returns description."""
        mock_description = "A clean technical diagram showing the main components."

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_description
        ):
            description = self.generator.generate_graphics_description(
                slide={"purpose": "test", "key_points": ["component"]},
                title="Component Overview",
                bullets=["First component"],
            )
            assert description == mock_description

    def test_generate_graphics_description_with_style_config(self):
        """Test generate_graphics_description uses style config."""
        mock_description = "Professional diagram with brand colors."

        style_config = {
            "brand_colors": ["#DD0033", "#004F71"],
            "style": "professional, clean",
        }

        with patch.object(
            self.generator.client, "generate_text", return_value=mock_description
        ) as mock_generate:
            self.generator.generate_graphics_description(
                slide={"purpose": "test", "key_points": []},
                title="Test",
                bullets=[],
                style_config=style_config,
            )
            # Verify the prompt includes brand colors
            call_args = mock_generate.call_args
            assert "#DD0033" in call_args.kwargs.get("prompt", call_args[1]["prompt"])


class TestGenerateSlideContentMocked:
    """Tests for generate_slide_content with mocked API."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            self.generator = ContentGenerator()

    def test_generate_slide_content_returns_dict(self):
        """Test generate_slide_content returns complete dict."""
        with patch.object(self.generator, "generate_title", return_value="Test Title"):
            with patch.object(
                self.generator, "generate_bullets", return_value=["Point 1", "Point 2"]
            ):
                with patch.object(
                    self.generator,
                    "generate_graphics_description",
                    return_value="Visual desc",
                ):
                    with patch.object(
                        self.generator,
                        "generate_speaker_notes",
                        return_value="Speaker notes",
                    ):
                        result = self.generator.generate_slide_content(
                            slide={
                                "purpose": "test",
                                "key_points": [],
                                "slide_type": "CONTENT",
                            },
                            slide_number=1,
                        )

                        assert "title" in result
                        assert "bullets" in result
                        assert "graphics_description" in result
                        assert "speaker_notes" in result
                        assert "markdown" in result
                        assert result["title"] == "Test Title"
                        assert result["bullets"] == ["Point 1", "Point 2"]

    def test_generate_slide_content_title_slide_no_bullets(self):
        """Test generate_slide_content skips bullets for title slides."""
        with patch.object(self.generator, "generate_title", return_value="Title"):
            with patch.object(
                self.generator, "generate_bullets", return_value=["Should not appear"]
            ) as mock_bullets:
                with patch.object(
                    self.generator, "generate_graphics_description", return_value="Desc"
                ):
                    with patch.object(
                        self.generator, "generate_speaker_notes", return_value="Notes"
                    ):
                        result = self.generator.generate_slide_content(
                            slide={
                                "purpose": "test",
                                "key_points": [],
                                "slide_type": "TITLE SLIDE",
                                "subtitle": "A Subtitle",
                            },
                            slide_number=1,
                        )

                        # generate_bullets should not be called for title slides
                        mock_bullets.assert_not_called()
                        assert result["bullets"] == []
                        assert result["subtitle"] == "A Subtitle"

    def test_generate_slide_content_section_divider_no_bullets(self):
        """Test generate_slide_content skips bullets for section dividers."""
        with patch.object(self.generator, "generate_title", return_value="Section"):
            with patch.object(
                self.generator, "generate_bullets"
            ) as mock_bullets:
                with patch.object(
                    self.generator, "generate_graphics_description", return_value="Desc"
                ):
                    with patch.object(
                        self.generator, "generate_speaker_notes", return_value="Notes"
                    ):
                        result = self.generator.generate_slide_content(
                            slide={
                                "purpose": "test",
                                "key_points": [],
                                "slide_type": "SECTION DIVIDER",
                            },
                            slide_number=1,
                        )

                        mock_bullets.assert_not_called()
                        assert result["bullets"] == []

    def test_generate_slide_content_includes_citations(self):
        """Test generate_slide_content includes citations from slide."""
        with patch.object(self.generator, "generate_title", return_value="Title"):
            with patch.object(self.generator, "generate_bullets", return_value=["Pt"]):
                with patch.object(
                    self.generator, "generate_graphics_description", return_value="Desc"
                ):
                    with patch.object(
                        self.generator, "generate_speaker_notes", return_value="Notes"
                    ):
                        result = self.generator.generate_slide_content(
                            slide={
                                "purpose": "test",
                                "key_points": [],
                                "slide_type": "CONTENT",
                                "supporting_sources": ["cite-001", "cite-002"],
                            },
                            slide_number=1,
                        )

                        assert result["citations"] == ["cite-001", "cite-002"]


class TestConvenienceFunction:
    """Tests for get_content_generator convenience function."""

    def test_get_content_generator_returns_instance(self):
        """Test get_content_generator returns ContentGenerator instance."""
        with patch("plugin.lib.content_generator.get_claude_client"):
            generator = get_content_generator()
            assert isinstance(generator, ContentGenerator)

    def test_get_content_generator_with_style_guide(self):
        """Test get_content_generator accepts style guide."""
        custom_guide = {"tone": "casual"}
        with patch("plugin.lib.content_generator.get_claude_client"):
            generator = get_content_generator(style_guide=custom_guide)
            assert generator.style_guide == custom_guide
