"""
Unit tests for plugin/skills/content/content_drafting_skill.py

Tests the ContentDraftingSkill class for generating slide content from outlines.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from plugin.base_skill import SkillInput, SkillStatus
from plugin.skills.content.content_drafting_skill import (
    ContentDraftingSkill,
    get_content_drafting_skill,
)


# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def skill():
    """Create a ContentDraftingSkill instance."""
    return ContentDraftingSkill()


@pytest.fixture
def valid_outline():
    """Create a valid outline structure for testing."""
    return {
        "presentations": [
            {
                "title": "Test Presentation",
                "audience": "technical",
                "estimated_duration": 30,
                "subtitle": "A test subtitle",
                "slides": [
                    {
                        "slide_number": 1,
                        "slide_type": "TITLE SLIDE",
                        "title": "Introduction",
                        "purpose": "Introduce the topic",
                        "key_points": ["Welcome", "Overview"],
                        "supporting_sources": ["cite-001"],
                    },
                    {
                        "slide_number": 2,
                        "slide_type": "CONTENT",
                        "title": "Main Content",
                        "purpose": "Present main ideas",
                        "key_points": ["Point 1", "Point 2"],
                        "supporting_sources": ["cite-002"],
                    },
                ],
            }
        ]
    }


@pytest.fixture
def multi_presentation_outline():
    """Create an outline with multiple presentations."""
    return {
        "presentations": [
            {
                "title": "Technical Deep Dive",
                "audience": "engineers",
                "estimated_duration": 45,
                "slides": [
                    {
                        "slide_number": 1,
                        "slide_type": "CONTENT",
                        "title": "Technical Overview",
                        "purpose": "Technical details",
                        "key_points": ["Architecture"],
                    }
                ],
            },
            {
                "title": "Executive Summary",
                "audience": "executives",
                "estimated_duration": 15,
                "slides": [
                    {
                        "slide_number": 1,
                        "slide_type": "CONTENT",
                        "title": "Business Impact",
                        "purpose": "Show business value",
                        "key_points": ["ROI", "Benefits"],
                    }
                ],
            },
        ]
    }


@pytest.fixture
def mock_content_generator():
    """Create a mock ContentGenerator."""
    mock_gen = MagicMock()
    mock_gen.generate_slide_content.return_value = {
        "title": "Generated Title",
        "subtitle": None,
        "bullets": ["Bullet 1", "Bullet 2"],
        "graphics_description": "A visual description",
        "speaker_notes": "Speaker notes here",
        "markdown": "## SLIDE 1: CONTENT\n\n**Title:** Generated Title\n\n---\n\n",
        "citations": ["cite-001"],
    }
    return mock_gen


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ==============================================================================
# Test Skill Properties
# ==============================================================================


class TestContentDraftingSkillProperties:
    """Tests for ContentDraftingSkill properties."""

    def test_skill_id(self, skill):
        """Test skill_id property returns correct value."""
        assert skill.skill_id == "draft-content"

    def test_display_name(self, skill):
        """Test display_name property returns correct value."""
        assert skill.display_name == "Content Drafting"

    def test_description(self, skill):
        """Test description property returns non-empty string."""
        assert len(skill.description) > 0
        assert "drafting" in skill.description.lower() or "content" in skill.description.lower()

    def test_version_default(self, skill):
        """Test skill inherits default version."""
        assert skill.version == "1.0.0"

    def test_dependencies_default(self, skill):
        """Test skill has no dependencies by default."""
        assert skill.dependencies == []


# ==============================================================================
# Test Input Validation
# ==============================================================================


class TestValidateInput:
    """Tests for validate_input method."""

    def test_validate_input_valid(self, skill, valid_outline):
        """Test validation with valid outline input."""
        input_data = SkillInput(data={"outline": valid_outline})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_missing_outline(self, skill):
        """Test validation fails when outline is missing."""
        input_data = SkillInput(data={})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_missing_presentations(self, skill):
        """Test validation fails when presentations key is missing."""
        input_data = SkillInput(data={"outline": {}})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_presentations_not_list(self, skill):
        """Test validation fails when presentations is not a list."""
        input_data = SkillInput(data={"outline": {"presentations": "not a list"}})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_empty_presentations(self, skill):
        """Test validation fails when presentations list is empty."""
        input_data = SkillInput(data={"outline": {"presentations": []}})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_presentation_missing_slides(self, skill):
        """Test validation fails when first presentation has no slides key."""
        input_data = SkillInput(
            data={
                "outline": {
                    "presentations": [
                        {"title": "Test", "audience": "general"}
                        # Missing "slides" key
                    ]
                }
            }
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_with_empty_slides_list(self, skill):
        """Test validation passes with empty slides list (slides key exists)."""
        input_data = SkillInput(
            data={
                "outline": {
                    "presentations": [
                        {"title": "Test", "audience": "general", "slides": []}
                    ]
                }
            }
        )
        # The validation only checks if "slides" key exists, not if it's non-empty
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_none_outline(self, skill):
        """Test validation fails when outline is None."""
        input_data = SkillInput(data={"outline": None})
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_with_research(self, skill, valid_outline):
        """Test validation passes with additional research data."""
        input_data = SkillInput(
            data={
                "outline": valid_outline,
                "research": {"sources": [], "key_themes": ["theme1"]},
            }
        )
        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []


# ==============================================================================
# Test Execute Method
# ==============================================================================


class TestExecute:
    """Tests for execute method."""

    def test_execute_creates_output_directory(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute creates output directory if it doesn't exist."""
        new_output_dir = os.path.join(temp_output_dir, "new_subdir")

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": new_output_dir}
            )
            skill.execute(input_data)

        assert os.path.exists(new_output_dir)

    def test_execute_returns_success_output(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute returns successful SkillOutput."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.success is True
        assert output.status == SkillStatus.SUCCESS
        assert "presentation_files" in output.data
        assert "presentations" in output.data
        assert "slides_generated" in output.data

    def test_execute_creates_presentation_file(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute creates markdown file for presentation."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        # Check file was created
        assert len(output.data["presentation_files"]) == 1
        file_path = output.data["presentation_files"][0]
        assert os.path.exists(file_path)

    def test_execute_multiple_presentations(
        self, skill, multi_presentation_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute handles multiple presentations."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={
                    "outline": multi_presentation_outline,
                    "output_dir": temp_output_dir,
                }
            )
            output = skill.execute(input_data)

        assert len(output.data["presentation_files"]) == 2
        assert output.metadata["presentation_count"] == 2

    def test_execute_counts_slides_correctly(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute counts total slides correctly."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        # valid_outline has 2 slides
        assert output.data["slides_generated"] == 2
        assert output.metadata["total_slides"] == 2

    def test_execute_uses_default_output_dir(
        self, skill, valid_outline, mock_content_generator
    ):
        """Test execute uses default output directory when not specified."""
        default_dir = "./output"

        with (
            patch(
                "plugin.skills.content.content_drafting_skill.ContentGenerator",
                return_value=mock_content_generator,
            ),
            patch("os.makedirs") as mock_makedirs,
            patch("builtins.open", MagicMock()),
        ):
            input_data = SkillInput(data={"outline": valid_outline})
            skill.execute(input_data)

            # Check that makedirs was called with the default output dir
            mock_makedirs.assert_called_once_with(default_dir, exist_ok=True)

    def test_execute_passes_style_guide_to_generator(
        self, skill, valid_outline, temp_output_dir
    ):
        """Test execute passes style_guide to ContentGenerator."""
        style_guide = {"tone": "casual", "max_bullets_per_slide": 3}

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator"
        ) as MockGenerator:
            mock_gen = MagicMock()
            mock_gen.generate_slide_content.return_value = {
                "title": "Title",
                "subtitle": None,
                "bullets": [],
                "graphics_description": "Desc",
                "speaker_notes": "Notes",
                "markdown": "## SLIDE\n---\n",
                "citations": [],
            }
            MockGenerator.return_value = mock_gen

            input_data = SkillInput(
                data={
                    "outline": valid_outline,
                    "style_guide": style_guide,
                    "output_dir": temp_output_dir,
                }
            )
            skill.execute(input_data)

            MockGenerator.assert_called_once_with(style_guide=style_guide)

    def test_execute_passes_research_context(
        self, skill, valid_outline, temp_output_dir
    ):
        """Test execute passes research context to content generator."""
        research = {"sources": [{"title": "Source 1"}], "key_themes": ["theme1"]}

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator"
        ) as MockGenerator:
            mock_gen = MagicMock()
            mock_gen.generate_slide_content.return_value = {
                "title": "Title",
                "subtitle": None,
                "bullets": [],
                "graphics_description": "Desc",
                "speaker_notes": "Notes",
                "markdown": "## SLIDE\n---\n",
                "citations": [],
            }
            MockGenerator.return_value = mock_gen

            input_data = SkillInput(
                data={
                    "outline": valid_outline,
                    "research": research,
                    "output_dir": temp_output_dir,
                }
            )
            skill.execute(input_data)

            # Verify generate_slide_content was called with research_context
            call_args = mock_gen.generate_slide_content.call_args_list[0]
            assert call_args.kwargs.get("research_context") == research

    def test_execute_passes_style_config(self, skill, valid_outline, temp_output_dir):
        """Test execute passes style_config to content generator."""
        style_config = {"brand_colors": ["#DD0033"], "style": "corporate"}

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator"
        ) as MockGenerator:
            mock_gen = MagicMock()
            mock_gen.generate_slide_content.return_value = {
                "title": "Title",
                "subtitle": None,
                "bullets": [],
                "graphics_description": "Desc",
                "speaker_notes": "Notes",
                "markdown": "## SLIDE\n---\n",
                "citations": [],
            }
            MockGenerator.return_value = mock_gen

            input_data = SkillInput(
                data={
                    "outline": valid_outline,
                    "style_config": style_config,
                    "output_dir": temp_output_dir,
                }
            )
            skill.execute(input_data)

            # Verify generate_slide_content was called with style_config
            call_args = mock_gen.generate_slide_content.call_args_list[0]
            assert call_args.kwargs.get("style_config") == style_config

    def test_execute_returns_artifacts(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute returns file paths as artifacts."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert len(output.artifacts) == 1
        assert output.artifacts[0] == output.data["presentation_files"][0]

    def test_execute_returns_empty_errors(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute returns empty errors list on success."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.errors == []


# ==============================================================================
# Test _generate_presentation_content Method
# ==============================================================================


class TestGeneratePresentationContent:
    """Tests for _generate_presentation_content method."""

    def test_generate_presentation_content_basic(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content returns expected structure."""
        presentation = valid_outline["presentations"][0]

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert "file_path" in result
        assert "presentation_data" in result
        assert "slides_count" in result
        assert result["slides_count"] == 2

    def test_generate_presentation_content_creates_file(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content creates markdown file."""
        presentation = valid_outline["presentations"][0]

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert os.path.exists(result["file_path"])
        assert result["file_path"].endswith(".md")

    def test_generate_presentation_content_uses_title(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content uses presentation title."""
        presentation = valid_outline["presentations"][0]

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert result["presentation_data"]["title"] == "Test Presentation"

    def test_generate_presentation_content_default_title(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content uses default title when missing."""
        presentation = {
            "audience": "general",
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "CONTENT",
                    "title": "Slide",
                    "purpose": "Test",
                    "key_points": [],
                }
            ],
        }

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=2,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert result["presentation_data"]["title"] == "Presentation 3"

    def test_generate_presentation_content_default_audience(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content uses default audience when missing."""
        presentation = {
            "title": "Test",
            "slides": [
                {
                    "slide_number": 1,
                    "slide_type": "CONTENT",
                    "title": "Slide",
                    "purpose": "Test",
                    "key_points": [],
                }
            ],
        }

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert result["presentation_data"]["audience"] == "general"

    def test_generate_presentation_content_includes_estimated_duration(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content includes estimated duration."""
        presentation = valid_outline["presentations"][0]

        result = skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        assert result["presentation_data"]["estimated_duration"] == 30

    def test_generate_presentation_content_calls_generator_for_each_slide(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content calls generator for each slide."""
        presentation = valid_outline["presentations"][0]

        skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        # Should be called once per slide (2 slides in valid_outline)
        assert mock_content_generator.generate_slide_content.call_count == 2

    def test_generate_presentation_content_passes_slide_number(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test _generate_presentation_content passes correct slide numbers."""
        presentation = valid_outline["presentations"][0]

        skill._generate_presentation_content(
            presentation=presentation,
            presentation_index=0,
            generator=mock_content_generator,
            research_context=None,
            style_config=None,
            output_dir=temp_output_dir,
        )

        # Check slide_number was passed correctly (1-indexed)
        calls = mock_content_generator.generate_slide_content.call_args_list
        assert calls[0].kwargs.get("slide_number") == 1
        assert calls[1].kwargs.get("slide_number") == 2


# ==============================================================================
# Test _build_markdown_document Method
# ==============================================================================


class TestBuildMarkdownDocument:
    """Tests for _build_markdown_document method."""

    def test_build_markdown_document_basic(self, skill):
        """Test _build_markdown_document creates basic structure."""
        slides = [
            {"markdown": "## SLIDE 1: CONTENT\n\n---\n\n"},
            {"markdown": "## SLIDE 2: CONTENT\n\n---\n\n"},
        ]
        presentation = {"title": "Test", "estimated_duration": 30}

        result = skill._build_markdown_document(
            title="Test Presentation",
            audience="technical",
            slides=slides,
            presentation=presentation,
        )

        # Check frontmatter
        assert result.startswith("---\n")
        assert "title: Test Presentation" in result
        assert "audience: technical" in result
        assert "slides: 2" in result
        assert "duration: 30 minutes" in result

    def test_build_markdown_document_includes_header(self, skill):
        """Test _build_markdown_document includes presentation header."""
        slides = [{"markdown": "## SLIDE\n---\n"}]
        presentation = {"title": "Test"}

        result = skill._build_markdown_document(
            title="My Presentation",
            audience="executives",
            slides=slides,
            presentation=presentation,
        )

        assert "# My Presentation" in result
        assert "**Target Audience:** executives" in result
        assert "**Slides:** 1" in result

    def test_build_markdown_document_includes_subtitle(self, skill):
        """Test _build_markdown_document includes subtitle when present."""
        slides = [{"markdown": "## SLIDE\n---\n"}]
        presentation = {"subtitle": "A Deeper Look"}

        result = skill._build_markdown_document(
            title="Main Title",
            audience="general",
            slides=slides,
            presentation=presentation,
        )

        assert "**A Deeper Look**" in result

    def test_build_markdown_document_no_subtitle(self, skill):
        """Test _build_markdown_document handles missing subtitle."""
        slides = [{"markdown": "## SLIDE\n---\n"}]
        presentation = {}

        result = skill._build_markdown_document(
            title="Title",
            audience="general",
            slides=slides,
            presentation=presentation,
        )

        # Should not have subtitle line (just title section)
        lines = result.split("\n")
        title_line_found = False
        next_line_is_subtitle = False
        for i, line in enumerate(lines):
            if line.startswith("# Title"):
                title_line_found = True
                # Next non-empty line should not be a bold subtitle
                for next_line in lines[i + 1 :]:
                    if next_line.strip():
                        next_line_is_subtitle = (
                            next_line.startswith("**")
                            and next_line.endswith("**")
                            and "Target Audience" not in next_line
                        )
                        break
                break

        assert title_line_found
        assert not next_line_is_subtitle

    def test_build_markdown_document_includes_duration(self, skill):
        """Test _build_markdown_document includes duration when present."""
        slides = [{"markdown": "## SLIDE\n---\n"}]
        presentation = {"estimated_duration": 45}

        result = skill._build_markdown_document(
            title="Title",
            audience="general",
            slides=slides,
            presentation=presentation,
        )

        assert "**Estimated Duration:** 45 minutes" in result

    def test_build_markdown_document_no_duration(self, skill):
        """Test _build_markdown_document handles missing duration."""
        slides = [{"markdown": "## SLIDE\n---\n"}]
        presentation = {}

        result = skill._build_markdown_document(
            title="Title",
            audience="general",
            slides=slides,
            presentation=presentation,
        )

        assert "duration:" not in result.lower()

    def test_build_markdown_document_includes_all_slides(self, skill):
        """Test _build_markdown_document includes all slide markdown."""
        slides = [
            {"markdown": "## SLIDE 1: CONTENT\n\nContent 1\n\n---\n\n"},
            {"markdown": "## SLIDE 2: CONTENT\n\nContent 2\n\n---\n\n"},
            {"markdown": "## SLIDE 3: CONTENT\n\nContent 3\n\n---\n\n"},
        ]
        presentation = {}

        result = skill._build_markdown_document(
            title="Title",
            audience="general",
            slides=slides,
            presentation=presentation,
        )

        assert "## SLIDE 1: CONTENT" in result
        assert "## SLIDE 2: CONTENT" in result
        assert "## SLIDE 3: CONTENT" in result
        assert "Content 1" in result
        assert "Content 2" in result
        assert "Content 3" in result


# ==============================================================================
# Test _sanitize_filename Method
# ==============================================================================


class TestSanitizeFilename:
    """Tests for _sanitize_filename method."""

    def test_sanitize_filename_basic(self, skill):
        """Test _sanitize_filename with basic text."""
        result = skill._sanitize_filename("Simple Title")
        assert result == "simple_title"

    def test_sanitize_filename_removes_invalid_chars(self, skill):
        """Test _sanitize_filename removes invalid characters."""
        result = skill._sanitize_filename('Test<>:"/\\|?*Title')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_filename_replaces_spaces(self, skill):
        """Test _sanitize_filename replaces spaces with underscores."""
        result = skill._sanitize_filename("Title With Spaces")
        assert " " not in result
        assert "_" in result

    def test_sanitize_filename_truncates_long_names(self, skill):
        """Test _sanitize_filename truncates very long filenames."""
        long_title = "A" * 150
        result = skill._sanitize_filename(long_title)
        assert len(result) <= 100

    def test_sanitize_filename_removes_leading_trailing_underscores(self, skill):
        """Test _sanitize_filename removes leading/trailing underscores."""
        result = skill._sanitize_filename("  Title  ")
        assert not result.startswith("_")
        assert not result.endswith("_")

    def test_sanitize_filename_converts_to_lowercase(self, skill):
        """Test _sanitize_filename converts to lowercase."""
        result = skill._sanitize_filename("UPPERCASE TITLE")
        assert result == "uppercase_title"

    def test_sanitize_filename_handles_special_cases(self, skill):
        """Test _sanitize_filename handles edge cases."""
        # Multiple consecutive spaces/invalid chars
        result = skill._sanitize_filename("Title   with   many   spaces")
        assert "___" in result  # Multiple underscores from spaces

        # Only invalid characters
        result = skill._sanitize_filename("<>:*?")
        # Should result in underscores that get stripped
        assert result == ""

    def test_sanitize_filename_preserves_valid_chars(self, skill):
        """Test _sanitize_filename preserves valid characters."""
        result = skill._sanitize_filename("Title-with_valid123chars")
        assert "title-with_valid123chars" == result


# ==============================================================================
# Test Convenience Function
# ==============================================================================


class TestConvenienceFunction:
    """Tests for get_content_drafting_skill convenience function."""

    def test_get_content_drafting_skill_returns_instance(self):
        """Test get_content_drafting_skill returns ContentDraftingSkill instance."""
        skill = get_content_drafting_skill()
        assert isinstance(skill, ContentDraftingSkill)

    def test_get_content_drafting_skill_returns_new_instance(self):
        """Test get_content_drafting_skill returns new instance each call."""
        skill1 = get_content_drafting_skill()
        skill2 = get_content_drafting_skill()
        assert skill1 is not skill2


# ==============================================================================
# Test Integration with run() Method
# ==============================================================================


class TestRunIntegration:
    """Tests for integration with BaseSkill.run() method."""

    def test_run_with_valid_input(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test run() with valid input succeeds."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.run(input_data)

        assert output.success is True
        assert "skill_id" in output.metadata
        assert output.metadata["skill_id"] == "draft-content"

    def test_run_with_invalid_input_fails(self, skill):
        """Test run() with invalid input returns failure."""
        input_data = SkillInput(data={})  # Missing outline
        output = skill.run(input_data)

        assert output.success is False
        assert output.status == SkillStatus.FAILURE

    def test_run_handles_generator_exception(self, skill, valid_outline, temp_output_dir):
        """Test run() handles exceptions from ContentGenerator."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator"
        ) as MockGenerator:
            mock_gen = MagicMock()
            mock_gen.generate_slide_content.side_effect = Exception("API Error")
            MockGenerator.return_value = mock_gen

            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.run(input_data)

        assert output.success is False
        assert output.status == SkillStatus.FAILURE
        assert len(output.errors) > 0


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_execute_with_empty_slides(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test execute handles presentation with empty slides list."""
        outline = {
            "presentations": [
                {"title": "Empty Presentation", "audience": "general", "slides": []}
            ]
        }

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.success is True
        assert output.data["slides_generated"] == 0

    def test_execute_with_missing_slide_fields(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test execute handles slides with missing optional fields."""
        outline = {
            "presentations": [
                {
                    "title": "Test",
                    "slides": [
                        {
                            # Minimal slide with only required fields
                            "slide_number": 1,
                            "slide_type": "CONTENT",
                        }
                    ],
                }
            ]
        }

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.success is True

    def test_execute_special_characters_in_title(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test execute handles special characters in presentation title."""
        outline = {
            "presentations": [
                {
                    "title": "Test: A <Special> Title?",
                    "audience": "general",
                    "slides": [
                        {
                            "slide_number": 1,
                            "slide_type": "CONTENT",
                            "title": "Slide",
                            "purpose": "Test",
                            "key_points": [],
                        }
                    ],
                }
            ]
        }

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.success is True
        # Filename should be sanitized
        file_path = output.data["presentation_files"][0]
        filename = os.path.basename(file_path)
        assert "<" not in filename
        assert ">" not in filename
        assert ":" not in filename
        assert "?" not in filename

    def test_execute_preserves_slide_outline_data(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test execute preserves original slide outline in generated content."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        # Check that outline data is preserved in presentation data
        slides = output.data["presentations"][0]["slides"]
        for slide in slides:
            assert "outline" in slide

    def test_execute_with_unicode_title(
        self, skill, mock_content_generator, temp_output_dir
    ):
        """Test execute handles unicode characters in title."""
        outline = {
            "presentations": [
                {
                    "title": "Test Title",
                    "audience": "general",
                    "slides": [
                        {
                            "slide_number": 1,
                            "slide_type": "CONTENT",
                            "title": "Slide",
                            "purpose": "Test",
                            "key_points": [],
                        }
                    ],
                }
            ]
        }

        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert output.success is True


# ==============================================================================
# Test Output Structure
# ==============================================================================


class TestOutputStructure:
    """Tests for SkillOutput structure."""

    def test_output_has_correct_data_keys(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test output data contains expected keys."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        required_keys = ["presentation_files", "presentations", "slides_generated"]
        for key in required_keys:
            assert key in output.data

    def test_output_has_correct_metadata_keys(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test output metadata contains expected keys."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        assert "presentation_count" in output.metadata
        assert "total_slides" in output.metadata

    def test_presentation_data_structure(
        self, skill, valid_outline, mock_content_generator, temp_output_dir
    ):
        """Test presentation data has correct structure."""
        with patch(
            "plugin.skills.content.content_drafting_skill.ContentGenerator",
            return_value=mock_content_generator,
        ):
            input_data = SkillInput(
                data={"outline": valid_outline, "output_dir": temp_output_dir}
            )
            output = skill.execute(input_data)

        presentation = output.data["presentations"][0]
        assert "title" in presentation
        assert "audience" in presentation
        assert "slides" in presentation
        assert "estimated_duration" in presentation
