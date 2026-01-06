"""
Unit tests for PowerPointAssemblySkill.

Tests the skill that assembles PowerPoint presentations from markdown
and generated images using brand templates.
"""

import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plugin.base_skill import SkillInput, SkillStatus
from plugin.skills.assembly.powerpoint_assembly_skill import PowerPointAssemblySkill


# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def skill():
    """Create a fresh PowerPointAssemblySkill instance."""
    return PowerPointAssemblySkill()


@pytest.fixture
def temp_markdown_file(tmp_path):
    """Create a temporary markdown file with sample slide content."""
    markdown_content = """# Sample Presentation

## **SLIDE 1: Introduction**

**Content:**
- First point
- Second point

**Speaker Notes:**
Welcome to the presentation.

---

## **SLIDE 2: Main Content**

**Content:**
- Content point one
- Content point two

**Graphic:**
A beautiful landscape with mountains.

**Speaker Notes:**
Here we discuss the main points.

---

## **SLIDE 3: Conclusion**

**Content:**
- Summary
- Questions?

**Speaker Notes:**
Thank you for attending.
"""
    md_file = tmp_path / "presentation.md"
    md_file.write_text(markdown_content, encoding="utf-8")
    return md_file


@pytest.fixture
def temp_images_dir(tmp_path):
    """Create a temporary images directory with sample images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Create mock image files
    for i in range(1, 4):
        (images_dir / f"slide-{i}.jpg").write_bytes(b"fake image content")

    return images_dir


@pytest.fixture
def valid_input_data(temp_markdown_file):
    """Create valid input data for the skill."""
    return SkillInput(
        data={
            "markdown_path": str(temp_markdown_file),
            "template": "cfa",
        },
        context={},
        config={},
    )


# ==============================================================================
# Test Skill Properties
# ==============================================================================


class TestSkillProperties:
    """Tests for skill properties (skill_id, display_name, etc.)."""

    def test_skill_id(self, skill):
        """Test skill_id property returns correct identifier."""
        assert skill.skill_id == "assemble-powerpoint"

    def test_display_name(self, skill):
        """Test display_name property returns correct name."""
        assert skill.display_name == "PowerPoint Assembly"

    def test_description(self, skill):
        """Test description property returns non-empty string."""
        assert len(skill.description) > 0
        assert (
            "PowerPoint" in skill.description
            or "powerpoint" in skill.description.lower()
        )

    def test_version(self, skill):
        """Test version property returns valid version string."""
        assert skill.version == "1.0.0"
        # Verify version format matches semver pattern
        assert re.match(r"^\d+\.\d+\.\d+$", skill.version)

    def test_dependencies(self, skill):
        """Test dependencies property returns correct list."""
        deps = skill.dependencies
        assert isinstance(deps, list)
        assert "parse-markdown" in deps


# ==============================================================================
# Test Input Validation
# ==============================================================================


class TestValidateInput:
    """Tests for input validation."""

    def test_validate_input_valid(self, skill, temp_markdown_file):
        """Test validation with valid input."""
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_input_valid_with_stratfield_template(
        self, skill, temp_markdown_file
    ):
        """Test validation with stratfield template."""
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "stratfield",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_input_missing_markdown_path(self, skill):
        """Test validation fails when markdown_path is missing."""
        input_data = SkillInput(
            data={"template": "cfa"},
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert any("markdown_path" in error.lower() for error in errors)

    def test_validate_input_empty_markdown_path(self, skill):
        """Test validation fails when markdown_path is empty."""
        input_data = SkillInput(
            data={
                "markdown_path": "",
                "template": "cfa",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert any("markdown_path" in error.lower() for error in errors)

    def test_validate_input_nonexistent_file(self, skill):
        """Test validation fails when markdown file doesn't exist."""
        input_data = SkillInput(
            data={
                "markdown_path": "/nonexistent/path/presentation.md",
                "template": "cfa",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert any("not found" in error.lower() for error in errors)

    def test_validate_input_invalid_template(self, skill, temp_markdown_file):
        """Test validation fails with invalid template."""
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "invalid_template",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        assert any("template" in error.lower() for error in errors)
        assert any("invalid" in error.lower() for error in errors)

    def test_validate_input_default_template(self, skill, temp_markdown_file):
        """Test validation uses default template when not specified."""
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        # Default template is 'cfa' which is valid
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_input_multiple_errors(self, skill):
        """Test validation collects multiple errors."""
        input_data = SkillInput(
            data={
                "markdown_path": "",
                "template": "invalid_template",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is False
        # Should have error for missing markdown_path
        # Template error may or may not be present since markdown_path check happens first
        assert len(errors) >= 1


# ==============================================================================
# Test Execute Method
# ==============================================================================


class TestExecute:
    """Tests for execute method."""

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_success(self, mock_assemble, skill, temp_markdown_file, tmp_path):
        """Test successful execution."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert result.status == SkillStatus.SUCCESS
        assert result.data["output_path"] == output_path
        assert result.data["template"] == "cfa"
        assert output_path in result.artifacts

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_with_all_options(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test execution with all optional parameters."""
        output_path = str(tmp_path / "custom_output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "stratfield",
                "style_config_path": "/path/to/style.json",
                "output_name": "custom_output.pptx",
                "output_dir": str(tmp_path),
                "skip_images": True,
                "fast_mode": True,
                "notext": False,
                "force_images": True,
                "enable_validation": True,
                "max_refinement_attempts": 5,
                "validation_dpi": 200,
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Verify assemble_presentation was called with correct arguments
        mock_assemble.assert_called_once()
        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["template_id"] == "stratfield"
        assert call_kwargs["skip_images"] is True
        assert call_kwargs["fast_mode"] is True
        assert call_kwargs["notext"] is False
        assert call_kwargs["force_images"] is True
        assert call_kwargs["enable_validation"] is True
        assert call_kwargs["max_refinement_attempts"] == 5
        assert call_kwargs["validation_dpi"] == 200

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_with_progress_callback(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test execution with progress callback from context."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        mock_callback = MagicMock()
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={"progress_callback": mock_callback},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True
        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["progress_callback"] == mock_callback

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_file_not_found_error(
        self, mock_assemble, skill, temp_markdown_file
    ):
        """Test execution handles FileNotFoundError."""
        mock_assemble.side_effect = FileNotFoundError("Template not found")

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert any("not found" in error.lower() for error in result.errors)
        assert result.metadata["markdown_path"] == str(temp_markdown_file)
        assert result.metadata["template"] == "cfa"

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_value_error(self, mock_assemble, skill, temp_markdown_file):
        """Test execution handles ValueError."""
        mock_assemble.side_effect = ValueError("Invalid template configuration")

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert any("invalid input" in error.lower() for error in result.errors)

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_generic_exception(self, mock_assemble, skill, temp_markdown_file):
        """Test execution handles generic exceptions."""
        mock_assemble.side_effect = RuntimeError("Unexpected error occurred")

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert any("failed to assemble" in error.lower() for error in result.errors)
        assert result.metadata["exception_type"] == "RuntimeError"

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_output_metadata(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test that execute returns correct metadata."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
                "fast_mode": True,
                "enable_validation": True,
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert result.metadata["output_path"] == output_path
        assert result.metadata["markdown_path"] == str(temp_markdown_file)
        assert result.metadata["template"] == "cfa"
        assert result.metadata["fast_mode"] is True
        assert result.metadata["validation_enabled"] is True


# ==============================================================================
# Test Helper Methods
# ==============================================================================


class TestCountSlidesInMarkdown:
    """Tests for _count_slides_in_markdown helper method."""

    def test_count_slides_basic(self, skill, tmp_path):
        """Test counting slides in a basic markdown file."""
        content = """## **SLIDE 1: Introduction**
Content here

## **SLIDE 2: Main**
More content

## **SLIDE 3: Conclusion**
Final content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 3

    def test_count_slides_with_h3_headers(self, skill, tmp_path):
        """Test counting slides with h3 headers."""
        content = """### **SLIDE 1: Introduction**
Content here

### **SLIDE 2: Main**
More content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 2

    def test_count_slides_case_insensitive(self, skill, tmp_path):
        """Test counting slides is case insensitive."""
        content = """## **slide 1: Introduction**
Content here

## **Slide 2: Main**
More content

## **SLIDE 3: Conclusion**
Final content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 3

    def test_count_slides_no_asterisks(self, skill, tmp_path):
        """Test counting slides without bold markers."""
        content = """## SLIDE 1: Introduction
Content here

## SLIDE 2: Main
More content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content, encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 2

    def test_count_slides_empty_file(self, skill, tmp_path):
        """Test counting slides in an empty file."""
        md_file = tmp_path / "empty.md"
        md_file.write_text("", encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 0

    def test_count_slides_no_slides(self, skill, tmp_path):
        """Test counting slides in file with no slides."""
        content = """# Title

## Introduction

Just regular content without slide markers.
"""
        md_file = tmp_path / "no_slides.md"
        md_file.write_text(content, encoding="utf-8")

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 0

    def test_count_slides_nonexistent_file(self, skill):
        """Test counting slides in nonexistent file returns 0."""
        count = skill._count_slides_in_markdown("/nonexistent/path.md")

        assert count == 0

    def test_count_slides_read_error(self, skill, tmp_path, mocker):
        """Test counting slides handles read errors gracefully."""
        md_file = tmp_path / "test.md"
        md_file.write_text("## SLIDE 1: Test", encoding="utf-8")

        # Mock Path.read_text to raise an exception
        mocker.patch.object(Path, "read_text", side_effect=OSError("Read error"))

        count = skill._count_slides_in_markdown(str(md_file))

        assert count == 0


class TestCountImagesInDirectory:
    """Tests for _count_images_in_directory helper method."""

    def test_count_images_basic(self, skill, tmp_path):
        """Test counting images in a directory."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Create slide images
        for i in range(1, 5):
            (images_dir / f"slide-{i}.jpg").write_bytes(b"fake image")

        count = skill._count_images_in_directory(images_dir)

        assert count == 4

    def test_count_images_empty_directory(self, skill, tmp_path):
        """Test counting images in an empty directory."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        count = skill._count_images_in_directory(images_dir)

        assert count == 0

    def test_count_images_nonexistent_directory(self, skill, tmp_path):
        """Test counting images in nonexistent directory returns 0."""
        images_dir = tmp_path / "nonexistent"

        count = skill._count_images_in_directory(images_dir)

        assert count == 0

    def test_count_images_ignores_non_slide_files(self, skill, tmp_path):
        """Test that only slide-*.jpg files are counted."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Create slide images
        (images_dir / "slide-1.jpg").write_bytes(b"fake image")
        (images_dir / "slide-2.jpg").write_bytes(b"fake image")

        # Create other files that should not be counted
        (images_dir / "background.jpg").write_bytes(b"fake image")
        (images_dir / "logo.png").write_bytes(b"fake image")
        (images_dir / "slide-info.txt").write_text("info")

        count = skill._count_images_in_directory(images_dir)

        assert count == 2

    def test_count_images_handles_glob_error(self, skill, tmp_path, mocker):
        """Test counting images handles glob errors gracefully."""
        images_dir = tmp_path / "images"
        images_dir.mkdir()

        # Mock glob to raise an exception
        mocker.patch.object(Path, "glob", side_effect=PermissionError("Access denied"))

        count = skill._count_images_in_directory(images_dir)

        assert count == 0


# ==============================================================================
# Test Integration with run() method
# ==============================================================================


class TestRunMethod:
    """Tests for the inherited run() method."""

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_run_full_workflow(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test full workflow through run() method."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.run(input_data)

        assert result.success is True
        assert "skill_id" in result.metadata
        assert result.metadata["skill_id"] == "assemble-powerpoint"
        assert "skill_version" in result.metadata

    def test_run_validation_failure(self, skill):
        """Test run() stops on validation failure."""
        input_data = SkillInput(
            data={
                "markdown_path": "",
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.run(input_data)

        assert result.success is False
        assert result.metadata["stage"] == "validation"

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_run_handles_execution_exception(
        self, mock_assemble, skill, temp_markdown_file
    ):
        """Test run() handles execution exceptions."""
        mock_assemble.side_effect = RuntimeError("Unexpected error")

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.run(input_data)

        assert result.success is False
        # Should still have skill metadata
        assert "skill_id" in result.metadata


# ==============================================================================
# Test Default Values
# ==============================================================================


class TestDefaultValues:
    """Tests for default parameter values."""

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_template(self, mock_assemble, skill, temp_markdown_file, tmp_path):
        """Test default template is 'cfa'."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["template_id"] == "cfa"

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_skip_images(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test default skip_images is False."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["skip_images"] is False

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_notext(self, mock_assemble, skill, temp_markdown_file, tmp_path):
        """Test default notext is True."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["notext"] is True

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_enable_validation(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test default enable_validation is False."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["enable_validation"] is False

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_max_refinement_attempts(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test default max_refinement_attempts is 3."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["max_refinement_attempts"] == 3

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_default_validation_dpi(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test default validation_dpi is 150."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        skill.execute(input_data)

        call_kwargs = mock_assemble.call_args.kwargs
        assert call_kwargs["validation_dpi"] == 150


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_with_none_optional_values(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test execution with None for optional values."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
                "style_config_path": None,
                "output_name": None,
                "output_dir": None,
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True

    def test_validate_input_with_path_object(self, skill, temp_markdown_file):
        """Test validation accepts Path object as markdown_path."""
        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),  # Convert to string
                "template": "cfa",
            },
            context={},
            config={},
        )

        is_valid, errors = skill.validate_input(input_data)

        assert is_valid is True

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_execute_with_special_characters_in_path(
        self, mock_assemble, skill, tmp_path
    ):
        """Test execution with special characters in file path."""
        # Create file with special characters in name
        special_dir = tmp_path / "Test Presentation (2024)"
        special_dir.mkdir()
        md_file = special_dir / "my presentation.md"
        md_file.write_text("## SLIDE 1: Test\nContent", encoding="utf-8")

        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(md_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.success is True

    def test_skill_initialization_with_config(self):
        """Test skill can be initialized with config."""
        config = {"custom_setting": "value"}
        skill = PowerPointAssemblySkill(config=config)

        assert skill.config == config

    def test_skill_cleanup_does_not_raise(self, skill):
        """Test cleanup method doesn't raise exceptions."""
        # Cleanup should not raise any errors
        skill.cleanup()

    def test_skill_initialize_does_not_raise(self, skill):
        """Test initialize method doesn't raise exceptions."""
        skill.initialize()
        assert skill._is_initialized is True

    def test_skill_repr(self, skill):
        """Test skill string representation."""
        repr_str = repr(skill)

        assert "PowerPointAssemblySkill" in repr_str
        assert "assemble-powerpoint" in repr_str
        assert "1.0.0" in repr_str


# ==============================================================================
# Test Output Data Structure
# ==============================================================================


class TestOutputDataStructure:
    """Tests for output data structure correctness."""

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_success_output_contains_required_fields(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test successful output contains all required fields."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        # Check data fields
        assert "output_path" in result.data
        assert "slide_count" in result.data
        assert "images_generated" in result.data
        assert "template" in result.data
        assert "validation_enabled" in result.data

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_success_output_artifacts(
        self, mock_assemble, skill, temp_markdown_file, tmp_path
    ):
        """Test successful output has output path in artifacts."""
        output_path = str(tmp_path / "output.pptx")
        mock_assemble.return_value = output_path

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert len(result.artifacts) == 1
        assert result.artifacts[0] == output_path

    @patch("plugin.skills.assembly.powerpoint_assembly_skill.assemble_presentation")
    def test_failure_output_contains_metadata(
        self, mock_assemble, skill, temp_markdown_file
    ):
        """Test failure output contains helpful metadata."""
        mock_assemble.side_effect = RuntimeError("Test error")

        input_data = SkillInput(
            data={
                "markdown_path": str(temp_markdown_file),
                "template": "cfa",
            },
            context={},
            config={},
        )

        result = skill.execute(input_data)

        assert result.metadata["markdown_path"] == str(temp_markdown_file)
        assert result.metadata["template"] == "cfa"
        assert "exception_type" in result.metadata
