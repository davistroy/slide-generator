"""
Unit tests for MarkdownParsingSkill.

Tests the markdown parsing skill that transforms markdown presentation files
into structured slide data.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from plugin.base_skill import SkillInput, SkillOutput, SkillStatus
from plugin.skills.assembly.markdown_parsing_skill import MarkdownParsingSkill
from plugin.lib.presentation.parser import (
    BulletItem,
    CodeBlockItem,
    Slide,
    TableItem,
    TextItem,
)


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def skill():
    """Create a fresh MarkdownParsingSkill instance."""
    return MarkdownParsingSkill()


@pytest.fixture
def sample_slide():
    """Create a sample Slide object for testing."""
    return Slide(
        number=1,
        slide_type="CONTENT",
        title="Test Slide",
        subtitle="Test Subtitle",
        content=[
            BulletItem(text="First bullet", level=0),
            BulletItem(text="Second bullet", level=1),
        ],
        content_bullets=[("First bullet", 0), ("Second bullet", 1)],
        graphic="A test graphic description",
        speaker_notes="Test speaker notes",
        raw_content="Raw markdown content",
    )


@pytest.fixture
def sample_slide_with_table():
    """Create a sample Slide with table content."""
    return Slide(
        number=2,
        slide_type="CONTENT",
        title="Table Slide",
        content=[
            TableItem(
                headers=["Column 1", "Column 2"],
                rows=[["Cell 1", "Cell 2"], ["Cell 3", "Cell 4"]],
            )
        ],
        content_bullets=[("Column 1, Column 2", 0), ("Cell 1, Cell 2", 1)],
    )


@pytest.fixture
def sample_slide_with_code():
    """Create a sample Slide with code block content."""
    return Slide(
        number=3,
        slide_type="CONTENT",
        title="Code Slide",
        content=[
            CodeBlockItem(code="print('hello')", language="python"),
        ],
        content_bullets=[("[Code: python]", 0)],
    )


@pytest.fixture
def sample_slide_with_text():
    """Create a sample Slide with plain text content."""
    return Slide(
        number=4,
        slide_type="CONTENT",
        title="Text Slide",
        content=[
            TextItem(text="This is plain text paragraph."),
        ],
        content_bullets=[("This is plain text paragraph.", 0)],
    )


@pytest.fixture
def sample_markdown_content():
    """Sample markdown content for testing."""
    return """# Test Presentation

## **SLIDE 1: TITLE SLIDE**

**Title:** Welcome to the Test
**Subtitle:** A Test Presentation

**SPEAKER NOTES:**
This is the opening slide.

---

## **SLIDE 2: CONTENT**

**Title:** Main Content

**Content:**
- First bullet point
- Second bullet point
  - Sub-bullet

**Graphic:** A visualization showing the main concepts.

**SPEAKER NOTES:**
Discuss the main content here.
"""


@pytest.fixture
def temp_markdown_file(tmp_path, sample_markdown_content):
    """Create a temporary markdown file for testing."""
    file_path = tmp_path / "test_presentation.md"
    file_path.write_text(sample_markdown_content, encoding="utf-8")
    return file_path


# ==============================================================================
# Test Skill Properties
# ==============================================================================


class TestMarkdownParsingSkillProperties:
    """Tests for skill properties."""

    def test_skill_id(self, skill):
        """Test that skill_id returns correct value."""
        assert skill.skill_id == "parse-markdown"

    def test_display_name(self, skill):
        """Test that display_name returns correct value."""
        assert skill.display_name == "Markdown Parsing"

    def test_description(self, skill):
        """Test that description returns correct value."""
        assert skill.description == "Parse presentation markdown files into structured slide data"

    def test_version(self, skill):
        """Test that version returns correct value."""
        assert skill.version == "1.0.0"

    def test_dependencies(self, skill):
        """Test that dependencies returns empty list."""
        assert skill.dependencies == []

    def test_repr(self, skill):
        """Test string representation of skill."""
        repr_str = repr(skill)
        assert "MarkdownParsingSkill" in repr_str
        assert "parse-markdown" in repr_str
        assert "1.0.0" in repr_str


# ==============================================================================
# Test Input Validation
# ==============================================================================


class TestValidateInput:
    """Tests for validate_input method."""

    def test_validate_input_missing_markdown_path(self, skill):
        """Test validation fails when markdown_path is missing."""
        input_data = SkillInput(data={})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert len(errors) == 1
        assert "markdown_path is required" in errors[0]

    def test_validate_input_empty_markdown_path(self, skill):
        """Test validation fails when markdown_path is empty string."""
        input_data = SkillInput(data={"markdown_path": ""})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert "markdown_path is required" in errors[0]

    def test_validate_input_none_markdown_path(self, skill):
        """Test validation fails when markdown_path is None."""
        input_data = SkillInput(data={"markdown_path": None})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert "markdown_path is required" in errors[0]

    def test_validate_input_file_not_found(self, skill, tmp_path):
        """Test validation fails when file does not exist."""
        non_existent_path = tmp_path / "non_existent.md"
        input_data = SkillInput(data={"markdown_path": str(non_existent_path)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert len(errors) == 1
        assert "File not found" in errors[0]

    def test_validate_input_wrong_extension_txt(self, skill, tmp_path):
        """Test validation fails for .txt file."""
        wrong_ext_file = tmp_path / "test.txt"
        wrong_ext_file.write_text("content", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(wrong_ext_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert "File must be markdown (.md)" in errors[0]

    def test_validate_input_wrong_extension_json(self, skill, tmp_path):
        """Test validation fails for .json file."""
        wrong_ext_file = tmp_path / "test.json"
        wrong_ext_file.write_text("{}", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(wrong_ext_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert "File must be markdown (.md)" in errors[0]

    def test_validate_input_valid_md_extension(self, skill, temp_markdown_file):
        """Test validation passes for .md file."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert errors == []

    def test_validate_input_valid_markdown_extension(self, skill, tmp_path):
        """Test validation passes for .markdown file."""
        markdown_file = tmp_path / "test.markdown"
        markdown_file.write_text("# Test", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(markdown_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert errors == []

    def test_validate_input_uppercase_md_extension(self, skill, tmp_path):
        """Test validation passes for .MD file (case insensitive)."""
        markdown_file = tmp_path / "test.MD"
        markdown_file.write_text("# Test", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(markdown_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert errors == []


# ==============================================================================
# Test Execute Method
# ==============================================================================


class TestExecute:
    """Tests for execute method."""

    def test_execute_success_with_slides(self, skill, temp_markdown_file):
        """Test successful execution with valid markdown file."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        assert result.success is True
        assert result.status == SkillStatus.SUCCESS
        assert "slides" in result.data
        assert "slide_count" in result.data
        assert "has_graphics" in result.data
        assert "graphics_count" in result.data
        assert result.data["slide_count"] > 0
        assert str(temp_markdown_file) in result.artifacts
        assert result.metadata["markdown_path"] == str(temp_markdown_file)

    def test_execute_returns_correct_slide_count(self, skill, temp_markdown_file):
        """Test that execute returns correct slide count."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        # Sample markdown has 2 slides
        assert result.data["slide_count"] == 2
        assert len(result.data["slides"]) == 2

    def test_execute_detects_graphics(self, skill, temp_markdown_file):
        """Test that execute correctly detects slides with graphics."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        # Sample markdown has 1 slide with graphic (slide 2)
        assert result.data["has_graphics"] is True
        assert result.data["graphics_count"] == 1

    def test_execute_no_slides_found(self, skill, tmp_path):
        """Test failure when no slides found in markdown."""
        empty_markdown = tmp_path / "empty.md"
        empty_markdown.write_text("# Just a header\n\nNo slides here.", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(empty_markdown)})
        result = skill.execute(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert "No slides found in markdown file" in result.errors[0]
        assert result.metadata["markdown_path"] == str(empty_markdown)

    def test_execute_file_not_found_error(self, skill, tmp_path):
        """Test handling of FileNotFoundError during execution."""
        # The file existed during validation but was deleted before execution
        with patch("plugin.skills.assembly.markdown_parsing_skill.parse_presentation") as mock_parse:
            mock_parse.side_effect = FileNotFoundError("File was deleted")
            input_data = SkillInput(data={"markdown_path": "/some/path.md"})
            result = skill.execute(input_data)

            assert result.success is False
            assert "File not found" in result.errors[0]

    def test_execute_generic_exception(self, skill, tmp_path):
        """Test handling of generic exceptions during execution."""
        with patch("plugin.skills.assembly.markdown_parsing_skill.parse_presentation") as mock_parse:
            mock_parse.side_effect = ValueError("Parsing error")
            input_data = SkillInput(data={"markdown_path": "/some/path.md"})
            result = skill.execute(input_data)

            assert result.success is False
            assert "Failed to parse markdown" in result.errors[0]
            assert result.metadata["exception_type"] == "ValueError"

    def test_execute_slide_data_structure(self, skill, temp_markdown_file):
        """Test that slide data has correct structure."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        slides = result.data["slides"]
        assert len(slides) > 0

        first_slide = slides[0]
        expected_keys = ["number", "slide_type", "title", "subtitle", "content",
                         "content_bullets", "graphic", "speaker_notes", "raw_content"]
        for key in expected_keys:
            assert key in first_slide

    def test_execute_no_graphics_file(self, skill, tmp_path):
        """Test execution with markdown that has no graphics."""
        no_graphics_md = tmp_path / "no_graphics.md"
        no_graphics_md.write_text("""## **SLIDE 1: CONTENT**

**Title:** No Graphics Slide

**Content:**
- Just bullet points

**SPEAKER NOTES:**
Speaker notes here.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(no_graphics_md)})
        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["has_graphics"] is False
        assert result.data["graphics_count"] == 0


# ==============================================================================
# Test Run Method (Integration with BaseSkill)
# ==============================================================================


class TestRun:
    """Tests for run method (inherited from BaseSkill)."""

    def test_run_validates_and_executes(self, skill, temp_markdown_file):
        """Test that run() validates input and executes skill."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.run(input_data)

        assert result.success is True
        assert "skill_id" in result.metadata
        assert result.metadata["skill_id"] == "parse-markdown"
        assert "skill_version" in result.metadata

    def test_run_fails_on_invalid_input(self, skill):
        """Test that run() fails when input is invalid."""
        input_data = SkillInput(data={})
        result = skill.run(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert "markdown_path is required" in result.errors[0]

    def test_run_initializes_skill(self, skill, temp_markdown_file, mocker):
        """Test that run() initializes skill if not initialized."""
        spy = mocker.spy(skill, "initialize")
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        skill.run(input_data)

        spy.assert_called_once()

    def test_run_calls_cleanup(self, skill, temp_markdown_file, mocker):
        """Test that run() calls cleanup after execution."""
        spy = mocker.spy(skill, "cleanup")
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        skill.run(input_data)

        spy.assert_called_once()


# ==============================================================================
# Test Private Methods
# ==============================================================================


class TestSlideToDict:
    """Tests for _slide_to_dict private method."""

    def test_slide_to_dict_basic(self, skill, sample_slide):
        """Test basic slide to dict conversion."""
        result = skill._slide_to_dict(sample_slide)

        assert result["number"] == 1
        assert result["slide_type"] == "CONTENT"
        assert result["title"] == "Test Slide"
        assert result["subtitle"] == "Test Subtitle"
        assert result["graphic"] == "A test graphic description"
        assert result["speaker_notes"] == "Test speaker notes"
        assert result["raw_content"] == "Raw markdown content"

    def test_slide_to_dict_content_items(self, skill, sample_slide):
        """Test that content items are properly converted."""
        result = skill._slide_to_dict(sample_slide)

        assert len(result["content"]) == 2
        assert result["content"][0]["type"] == "bullet"
        assert result["content"][0]["text"] == "First bullet"
        assert result["content"][0]["level"] == 0

    def test_slide_to_dict_content_bullets(self, skill, sample_slide):
        """Test that content_bullets are preserved."""
        result = skill._slide_to_dict(sample_slide)

        assert result["content_bullets"] == [("First bullet", 0), ("Second bullet", 1)]

    def test_slide_to_dict_with_none_values(self, skill):
        """Test slide to dict with None values."""
        minimal_slide = Slide(
            number=1,
            slide_type="TITLE",
            title="Title Only",
        )
        result = skill._slide_to_dict(minimal_slide)

        assert result["number"] == 1
        assert result["title"] == "Title Only"
        assert result["subtitle"] is None
        assert result["graphic"] is None
        assert result["speaker_notes"] is None
        assert result["content"] == []
        assert result["content_bullets"] == []


class TestContentItemToDict:
    """Tests for _content_item_to_dict private method."""

    def test_bullet_item_to_dict(self, skill):
        """Test BulletItem conversion."""
        item = BulletItem(text="Test bullet", level=1)
        result = skill._content_item_to_dict(item)

        assert result["type"] == "bullet"
        assert result["text"] == "Test bullet"
        assert result["level"] == 1

    def test_table_item_to_dict(self, skill):
        """Test TableItem conversion."""
        item = TableItem(
            headers=["Header 1", "Header 2"],
            rows=[["Row 1 Col 1", "Row 1 Col 2"]]
        )
        result = skill._content_item_to_dict(item)

        assert result["type"] == "table"
        assert result["headers"] == ["Header 1", "Header 2"]
        assert result["rows"] == [["Row 1 Col 1", "Row 1 Col 2"]]

    def test_code_block_item_to_dict(self, skill):
        """Test CodeBlockItem conversion."""
        item = CodeBlockItem(code="print('hello')", language="python")
        result = skill._content_item_to_dict(item)

        assert result["type"] == "code"
        assert result["code"] == "print('hello')"
        assert result["language"] == "python"

    def test_code_block_item_no_language(self, skill):
        """Test CodeBlockItem without language."""
        item = CodeBlockItem(code="some code", language=None)
        result = skill._content_item_to_dict(item)

        assert result["type"] == "code"
        assert result["code"] == "some code"
        assert result["language"] is None

    def test_text_item_to_dict(self, skill):
        """Test TextItem conversion."""
        item = TextItem(text="Plain text content")
        result = skill._content_item_to_dict(item)

        assert result["type"] == "text"
        assert result["text"] == "Plain text content"

    def test_unknown_item_type(self, skill):
        """Test handling of unknown item types."""
        # Create a custom object that doesn't match known types
        class UnknownItem:
            def __str__(self):
                return "unknown item"

        item = UnknownItem()
        result = skill._content_item_to_dict(item)

        assert result["type"] == "unknown"
        assert result["raw"] == "unknown item"


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_execute_with_path_object(self, skill, temp_markdown_file):
        """Test execution with Path object instead of string."""
        # The skill should handle both str and Path
        input_data = SkillInput(data={"markdown_path": temp_markdown_file})
        result = skill.execute(input_data)

        # Path object should work with str() conversion in the skill
        assert result.success is True

    def test_execute_with_unicode_content(self, skill, tmp_path):
        """Test execution with unicode characters in markdown."""
        unicode_md = tmp_path / "unicode.md"
        unicode_md.write_text("""## **SLIDE 1: CONTENT**

**Title:** Unicode Test

**Content:**
- First bullet point with emoji and unicode characters

**SPEAKER NOTES:**
Notes with unicode.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(unicode_md)})
        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["slide_count"] == 1

    def test_execute_with_long_content(self, skill, tmp_path):
        """Test execution with many slides."""
        many_slides_md = tmp_path / "many_slides.md"
        slides_content = ""
        for i in range(1, 51):  # 50 slides
            slides_content += f"""## **SLIDE {i}: CONTENT**

**Title:** Slide {i} Title

**Content:**
- Bullet for slide {i}

---

"""
        many_slides_md.write_text(slides_content, encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(many_slides_md)})
        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["slide_count"] == 50
        assert len(result.data["slides"]) == 50

    def test_execute_metadata_contains_expected_fields(self, skill, temp_markdown_file):
        """Test that metadata contains all expected fields."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        assert "markdown_path" in result.metadata
        assert "slide_count" in result.metadata
        assert "graphics_count" in result.metadata

    def test_slide_to_dict_with_all_content_types(self, skill):
        """Test slide conversion with mixed content types."""
        mixed_slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Mixed Content",
            content=[
                BulletItem(text="Bullet 1", level=0),
                TableItem(headers=["A", "B"], rows=[["1", "2"]]),
                CodeBlockItem(code="x = 1", language="python"),
                TextItem(text="Plain text"),
            ],
            content_bullets=[],
        )
        result = skill._slide_to_dict(mixed_slide)

        assert len(result["content"]) == 4
        assert result["content"][0]["type"] == "bullet"
        assert result["content"][1]["type"] == "table"
        assert result["content"][2]["type"] == "code"
        assert result["content"][3]["type"] == "text"

    def test_validate_input_path_with_spaces(self, skill, tmp_path):
        """Test validation with path containing spaces."""
        dir_with_spaces = tmp_path / "path with spaces"
        dir_with_spaces.mkdir()
        md_file = dir_with_spaces / "test file.md"
        md_file.write_text("## **SLIDE 1: CONTENT**\n**Title:** Test", encoding="utf-8")

        input_data = SkillInput(data={"markdown_path": str(md_file)})
        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert errors == []

    def test_execute_with_empty_slides_list(self, skill, tmp_path, mocker):
        """Test execution when parser returns empty list."""
        # Mock the parser to return empty list
        with patch("plugin.skills.assembly.markdown_parsing_skill.parse_presentation") as mock_parse:
            mock_parse.return_value = []

            md_file = tmp_path / "empty.md"
            md_file.write_text("# Empty", encoding="utf-8")
            input_data = SkillInput(data={"markdown_path": str(md_file)})
            result = skill.execute(input_data)

            assert result.success is False
            assert "No slides found" in result.errors[0]


# ==============================================================================
# Test Different Slide Types
# ==============================================================================


class TestSlideTypes:
    """Tests for different slide type conversions."""

    def test_title_slide_conversion(self, skill, tmp_path):
        """Test title slide parsing and conversion."""
        title_slide_md = tmp_path / "title.md"
        title_slide_md.write_text("""## **SLIDE 1: TITLE SLIDE**

**Title:** Main Presentation Title
**Subtitle:** Presented by Author Name

**SPEAKER NOTES:**
Welcome everyone to this presentation.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(title_slide_md)})
        result = skill.execute(input_data)

        assert result.success is True
        slide = result.data["slides"][0]
        assert slide["slide_type"] == "TITLE SLIDE"
        assert slide["title"] == "Main Presentation Title"
        assert slide["subtitle"] is not None

    def test_section_divider_conversion(self, skill, tmp_path):
        """Test section divider slide parsing."""
        section_md = tmp_path / "section.md"
        section_md.write_text("""## **SLIDE 1: SECTION DIVIDER**

**Title:** Part Two

**SPEAKER NOTES:**
Now we move to part two.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(section_md)})
        result = skill.execute(input_data)

        assert result.success is True
        slide = result.data["slides"][0]
        assert slide["slide_type"] == "SECTION DIVIDER"

    def test_content_slide_with_graphic(self, skill, tmp_path):
        """Test content slide with graphic description."""
        graphic_md = tmp_path / "graphic.md"
        graphic_md.write_text("""## **SLIDE 1: CONTENT**

**Title:** Visual Slide

**Content:**
- Key point one
- Key point two

**Graphic:** A detailed infographic showing the process flow from start to finish with arrows and icons.

**SPEAKER NOTES:**
Let's look at this visual representation.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(graphic_md)})
        result = skill.execute(input_data)

        assert result.success is True
        slide = result.data["slides"][0]
        assert slide["graphic"] is not None
        assert "infographic" in slide["graphic"].lower()


# ==============================================================================
# Test Configuration and Initialization
# ==============================================================================


class TestConfiguration:
    """Tests for skill configuration and initialization."""

    def test_skill_with_config(self):
        """Test creating skill with custom configuration."""
        config = {"custom_setting": "value"}
        skill = MarkdownParsingSkill(config=config)

        assert skill.config == config

    def test_skill_with_empty_config(self):
        """Test creating skill with empty configuration."""
        skill = MarkdownParsingSkill(config={})

        assert skill.config == {}

    def test_skill_with_none_config(self):
        """Test creating skill with None configuration."""
        skill = MarkdownParsingSkill(config=None)

        assert skill.config == {}

    def test_skill_initialization(self, skill):
        """Test skill initialization state."""
        assert skill._is_initialized is False

        skill.initialize()

        assert skill._is_initialized is True

    def test_skill_only_initializes_once(self, skill, temp_markdown_file):
        """Test that skill only initializes once across multiple runs."""
        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})

        # First run
        skill.run(input_data)
        assert skill._is_initialized is True

        # Second run - should not re-initialize
        skill.run(input_data)
        assert skill._is_initialized is True


# ==============================================================================
# Test Output Serialization
# ==============================================================================


class TestOutputSerialization:
    """Tests for output data serialization."""

    def test_slides_are_json_serializable(self, skill, temp_markdown_file):
        """Test that slide data can be serialized to JSON."""
        import json

        input_data = SkillInput(data={"markdown_path": str(temp_markdown_file)})
        result = skill.execute(input_data)

        # This should not raise an exception
        json_str = json.dumps(result.data)
        assert json_str is not None

        # Parse it back
        parsed = json.loads(json_str)
        assert parsed["slide_count"] == result.data["slide_count"]

    def test_nested_content_structures(self, skill, tmp_path):
        """Test that nested content structures are properly serialized."""
        import json

        complex_md = tmp_path / "complex.md"
        complex_md.write_text("""## **SLIDE 1: CONTENT**

**Title:** Complex Content

**Content:**
- Level 0 bullet
  - Level 1 bullet
    - Level 2 bullet
- Another level 0

**SPEAKER NOTES:**
Notes here.
""", encoding="utf-8")
        input_data = SkillInput(data={"markdown_path": str(complex_md)})
        result = skill.execute(input_data)

        # Should be JSON serializable
        json_str = json.dumps(result.data)
        parsed = json.loads(json_str)
        assert "slides" in parsed
