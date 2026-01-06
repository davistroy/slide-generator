"""
Unit tests for ValidationSkill.

Tests the visual validation skill that wraps the VisualValidator
with skill interface, platform detection, and error handling.
"""

import platform
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from plugin.base_skill import SkillInput, SkillOutput
from plugin.skills.images.validation_skill import ValidationSkill, ValidationSummary


# ==============================================================================
# Test ValidationSummary Dataclass
# ==============================================================================


class TestValidationSummary:
    """Tests for ValidationSummary dataclass."""

    def test_create_validation_summary(self):
        """Test creating ValidationSummary with all fields."""
        summary = ValidationSummary(
            total_slides=10,
            passed=8,
            failed=2,
            pass_rate=80.0,
            average_score=85.5,
            validation_time=30.5,
            platform="Windows",
            export_available=True,
        )

        assert summary.total_slides == 10
        assert summary.passed == 8
        assert summary.failed == 2
        assert summary.pass_rate == 80.0
        assert summary.average_score == 85.5
        assert summary.validation_time == 30.5
        assert summary.platform == "Windows"
        assert summary.export_available is True

    def test_validation_summary_to_dict(self):
        """Test ValidationSummary can be converted to dict."""
        summary = ValidationSummary(
            total_slides=5,
            passed=4,
            failed=1,
            pass_rate=80.0,
            average_score=82.0,
            validation_time=15.0,
            platform="Linux",
            export_available=False,
        )

        summary_dict = summary.__dict__
        assert isinstance(summary_dict, dict)
        assert summary_dict["total_slides"] == 5
        assert summary_dict["platform"] == "Linux"


# ==============================================================================
# Test ValidationSkill Properties
# ==============================================================================


class TestValidationSkillProperties:
    """Tests for ValidationSkill properties (skill_id, display_name, description)."""

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.SlideExporter")
    def test_skill_id(self, mock_exporter, mock_validator):
        """Test skill_id property returns correct value."""
        skill = ValidationSkill()
        assert skill.skill_id == "validate-slides"

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.SlideExporter")
    def test_display_name(self, mock_exporter, mock_validator):
        """Test display_name property returns correct value."""
        skill = ValidationSkill()
        assert skill.display_name == "Visual Validation"

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.SlideExporter")
    def test_description(self, mock_exporter, mock_validator):
        """Test description property returns correct value."""
        skill = ValidationSkill()
        assert "Validate slide quality" in skill.description
        assert "Gemini vision" in skill.description
        assert "Windows" in skill.description


# ==============================================================================
# Test Platform Detection
# ==============================================================================


class TestPlatformDetection:
    """Tests for platform detection in ValidationSkill."""

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_detect_platform_windows_with_powerpoint(
        self, mock_system, mock_exporter, mock_validator
    ):
        """Test platform detection on Windows with PowerPoint available."""
        mock_system.return_value = "Windows"
        # SlideExporter doesn't raise, so PowerPoint is available
        mock_exporter.return_value = MagicMock()

        skill = ValidationSkill()
        platform_info = skill.platform_info

        assert platform_info["os"] == "Windows"
        assert platform_info["is_windows"] is True
        assert platform_info["powerpoint_available"] is True
        assert platform_info["export_method"] == "PowerShell COM"

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_detect_platform_windows_without_powerpoint(
        self, mock_system, mock_exporter, mock_validator
    ):
        """Test platform detection on Windows without PowerPoint."""
        mock_system.return_value = "Windows"
        # SlideExporter raises, so PowerPoint is not available
        mock_exporter.side_effect = OSError("PowerPoint not found")

        skill = ValidationSkill()
        platform_info = skill.platform_info

        assert platform_info["os"] == "Windows"
        assert platform_info["is_windows"] is True
        assert platform_info["powerpoint_available"] is False
        assert platform_info["export_method"] == "cloud_fallback"

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_detect_platform_linux(self, mock_system, mock_validator):
        """Test platform detection on Linux."""
        mock_system.return_value = "Linux"

        skill = ValidationSkill()
        platform_info = skill.platform_info

        assert platform_info["os"] == "Linux"
        assert platform_info["is_windows"] is False
        assert platform_info["powerpoint_available"] is False
        assert platform_info["export_method"] == "cloud_fallback"

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_detect_platform_macos(self, mock_system, mock_validator):
        """Test platform detection on macOS."""
        mock_system.return_value = "Darwin"

        skill = ValidationSkill()
        platform_info = skill.platform_info

        assert platform_info["os"] == "Darwin"
        assert platform_info["is_windows"] is False
        assert platform_info["powerpoint_available"] is False
        assert platform_info["export_method"] == "cloud_fallback"


# ==============================================================================
# Test validate_input
# ==============================================================================


class TestValidateInput:
    """Tests for validate_input method."""

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_validate_input_with_required_fields(self, mock_system, mock_validator):
        """Test validate_input returns True when required fields present."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide"}],
                "presentation_path": "/path/to/presentation.pptx",
            }
        )

        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_validate_input_missing_slides(self, mock_system, mock_validator):
        """Test validate_input returns False when slides missing."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(
            data={"presentation_path": "/path/to/presentation.pptx"}
        )

        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_validate_input_missing_presentation_path(
        self, mock_system, mock_validator
    ):
        """Test validate_input returns False when presentation_path missing."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(data={"slides": [{"title": "Test Slide"}]})

        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_validate_input_empty_data(self, mock_system, mock_validator):
        """Test validate_input returns False when data is empty."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(data={})

        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_validate_input_with_optional_fields(self, mock_system, mock_validator):
        """Test validate_input accepts optional fields."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": "/path/to/presentation.pptx",
                "style_config": {"brand_colors": ["#FF0000"]},
                "enable_caching": True,
                "parallel": False,
                "dpi": 300,
            }
        )

        is_valid, errors = skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []


# ==============================================================================
# Test execute Method
# ==============================================================================


class TestExecute:
    """Tests for execute method."""

    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_invalid_input_returns_failure(self, mock_system, mock_validator):
        """Test execute returns failure SkillOutput for invalid input."""
        mock_system.return_value = "Linux"
        skill = ValidationSkill()

        input_data = SkillInput(data={})  # Missing required fields

        result = skill.execute(input_data)

        assert result.success is False
        assert len(result.errors) > 0
        # Error message contains specific missing field or generic "Invalid input"
        assert "missing" in result.errors[0].lower() or "required" in result.errors[0].lower() or "Invalid input" in result.errors[0]

    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_no_powerpoint_skip_export_errors(
        self, mock_system, mock_validator, mock_analytics, tmp_path
    ):
        """Test execute continues when PowerPoint not available and skip_export_errors=True."""
        mock_system.return_value = "Linux"
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        skill = ValidationSkill()

        # Create temp presentation path
        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        # Should succeed (graceful degradation)
        assert result.success is True

    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_no_powerpoint_fail_on_export_errors(
        self, mock_system, mock_validator, mock_analytics, tmp_path
    ):
        """Test execute fails when PowerPoint not available and skip_export_errors=False."""
        mock_system.return_value = "Linux"
        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        skill = ValidationSkill()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": False,
            }
        )

        result = skill.execute(input_data)

        assert result.success is False
        assert "PowerPoint not available" in str(result.errors) or len(result.errors) > 0

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_with_cached_images(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute uses cached exported images if they exist."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        # Mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 85.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        # Create temp files
        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        # Create cached slide image
        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        cached_image = validation_dir / "slide-1.jpg"
        cached_image.write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
                "enable_caching": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Validator should be called since image exists
        mock_validator_instance.validate_slide.assert_called_once()

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_exports_slides_when_not_cached(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute exports slides when not cached."""
        mock_system.return_value = "Windows"

        # Mock exporter
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export_slide.return_value = True
        mock_exporter_class.return_value = mock_exporter_instance

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        # Mock validation result
        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        # Create temp presentation
        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "dpi": 150,
            }
        )

        # Note: The slide won't actually be exported since it's a mock,
        # so validation won't happen either since the image file won't exist
        result = skill.execute(input_data)

        assert result.success is True
        # Exporter should be called
        mock_exporter_instance.export_slide.assert_called_once()

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_handles_validation_error(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute handles validation errors gracefully."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        # Mock validator to raise exception
        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.side_effect = Exception("API error")
        mock_validator_class.return_value = mock_validator_instance

        # Create temp files
        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        slide_image = validation_dir / "slide-1.jpg"
        slide_image.write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        # Should still succeed (graceful degradation)
        assert result.success is True
        # Validation results should contain error
        assert len(result.data["validation_results"]) == 1
        assert "error" in result.data["validation_results"][0]

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_calculates_pass_rate(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute calculates pass rate correctly."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        # Create validation results - 2 pass, 1 fail
        def create_validation_result(slide_num):
            result = MagicMock()
            result.passed = slide_num != 2  # Slide 2 fails
            result.score = 80.0 if slide_num != 2 else 60.0
            result.issues = [] if slide_num != 2 else [{"message": "Low score"}]
            return result

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.side_effect = [
            create_validation_result(1),
            create_validation_result(2),
            create_validation_result(3),
        ]
        mock_validator_class.return_value = mock_validator_instance

        # Create temp files
        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        for i in range(1, 4):
            (validation_dir / f"slide-{i}.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [
                    {"title": f"Slide {i}", "type": "content"} for i in range(1, 4)
                ],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # 2 passed, 1 failed = 66.67% pass rate
        assert result.data["summary"]["passed"] == 2
        assert result.data["summary"]["failed"] == 1
        assert abs(result.data["pass_rate"] - 66.67) < 1.0

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_handles_export_failure(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute handles slide export failure."""
        mock_system.return_value = "Windows"

        # Mock exporter to fail
        mock_exporter_instance = MagicMock()
        mock_exporter_instance.export_slide.return_value = False
        mock_exporter_class.return_value = mock_exporter_instance

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert len(result.data["export_errors"]) > 0

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_skips_validation_without_image(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute skips validation when no exported image available."""
        mock_system.return_value = "Linux"  # No export available

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Validation should be skipped
        assert len(result.data["validation_results"]) == 1
        assert result.data["validation_results"][0].get("skipped") is True

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_creates_output_directory(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute creates output directory if it doesn't exist."""
        mock_system.return_value = "Linux"

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        output_dir = tmp_path / "new_output_dir"

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(output_dir),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert output_dir.exists()

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_uses_default_output_dir(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute uses default output directory when not specified."""
        mock_system.return_value = "Linux"

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Default output dir should be validation/ in same directory as presentation
        expected_output_dir = pres_path.parent / "validation"
        assert expected_output_dir.exists()
        assert str(expected_output_dir) in result.artifacts

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_includes_platform_metadata(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute includes platform info in metadata."""
        mock_system.return_value = "Linux"

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert "platform" in result.metadata
        assert result.metadata["platform"]["os"] == "Linux"

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_tracks_analytics(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute tracks analytics correctly."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 85.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        (validation_dir / "slide-1.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Analytics should be called
        mock_analytics_instance.start_phase.assert_called_once_with("validation")
        mock_analytics_instance.end_phase.assert_called_once()
        mock_analytics_instance.track_api_call.assert_called_once_with(
            "gemini_vision", call_count=1
        )


# ==============================================================================
# Test Multiple Slides
# ==============================================================================


class TestMultipleSlides:
    """Tests for processing multiple slides."""

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_multiple_slides_all_pass(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute with multiple slides all passing."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        for i in range(1, 6):
            (validation_dir / f"slide-{i}.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        slides = [{"title": f"Slide {i}", "type": "content"} for i in range(1, 6)]

        input_data = SkillInput(
            data={
                "slides": slides,
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["summary"]["total_slides"] == 5
        assert result.data["summary"]["passed"] == 5
        assert result.data["summary"]["failed"] == 0
        assert result.data["pass_rate"] == 100.0

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_multiple_slides_mixed_results(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute with multiple slides having mixed results."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        # Create alternating pass/fail results
        call_count = [0]

        def create_result(*args, **kwargs):
            call_count[0] += 1
            result = MagicMock()
            result.passed = call_count[0] % 2 == 1  # Odd slides pass
            result.score = 85.0 if result.passed else 65.0
            result.issues = [] if result.passed else [{"message": "Issues found"}]
            return result

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.side_effect = create_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        for i in range(1, 5):
            (validation_dir / f"slide-{i}.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        slides = [{"title": f"Slide {i}", "type": "content"} for i in range(1, 5)]

        input_data = SkillInput(
            data={
                "slides": slides,
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["summary"]["total_slides"] == 4
        assert result.data["summary"]["passed"] == 2
        assert result.data["summary"]["failed"] == 2
        assert result.data["pass_rate"] == 50.0


# ==============================================================================
# Test Slide Type Handling
# ==============================================================================


class TestSlideTypeHandling:
    """Tests for slide type handling."""

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_passes_slide_type_to_validator(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute passes slide type to validator."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        (validation_dir / "slide-1.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Title Slide", "type": "title"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        # Verify slide_type was passed to validator
        call_args = mock_validator_instance.validate_slide.call_args
        assert call_args.kwargs["slide_type"] == "title"

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_defaults_to_content_type(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute defaults to 'content' type when not specified."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        (validation_dir / "slide-1.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide"}],  # No type specified
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        call_args = mock_validator_instance.validate_slide.call_args
        assert call_args.kwargs["slide_type"] == "content"


# ==============================================================================
# Test Style Config Handling
# ==============================================================================


class TestStyleConfigHandling:
    """Tests for style config handling."""

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_passes_style_config_to_validator(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute passes style config to validator."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        (validation_dir / "slide-1.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        style_config = {
            "brand_colors": ["#DD0033", "#004F71"],
            "style": "professional",
        }

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
                "style_config": style_config,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        call_args = mock_validator_instance.validate_slide.call_args
        assert call_args.kwargs["style_config"] == style_config

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_uses_empty_style_config_when_not_provided(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter, tmp_path
    ):
        """Test execute uses empty dict when style_config not provided."""
        mock_system.return_value = "Windows"
        mock_exporter.return_value = MagicMock()

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 90.0
        mock_validation_result.issues = []

        mock_validator_instance = MagicMock()
        mock_validator_instance.validate_slide.return_value = mock_validation_result
        mock_validator_class.return_value = mock_validator_instance

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        validation_dir = tmp_path / "validation"
        validation_dir.mkdir()
        (validation_dir / "slide-1.jpg").write_bytes(b"fake image data")

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "output_dir": str(validation_dir),
                # No style_config provided
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        call_args = mock_validator_instance.validate_slide.call_args
        assert call_args.kwargs["style_config"] == {}


# ==============================================================================
# Test SlideExporter Initialization Failure
# ==============================================================================


class TestSlideExporterInitialization:
    """Tests for SlideExporter initialization handling."""

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_handles_exporter_init_failure_skip_errors(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute handles SlideExporter initialization failure when skip_export_errors=True."""
        mock_system.return_value = "Windows"

        # Platform detection passes but execute-time initialization fails
        mock_exporter_class.side_effect = [MagicMock(), Exception("COM error")]

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        # Should succeed (graceful degradation)
        assert result.success is True

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_handles_exporter_init_failure_no_skip(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute handles SlideExporter initialization failure when skip_export_errors=False."""
        mock_system.return_value = "Windows"

        # Platform detection passes but execute-time initialization fails
        mock_exporter_class.side_effect = [MagicMock(), Exception("COM error")]

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "skip_export_errors": False,
            }
        )

        result = skill.execute(input_data)

        # Should fail
        assert result.success is False
        assert len(result.errors) > 0


# ==============================================================================
# Test Empty Slides List
# ==============================================================================


class TestEmptySlidesList:
    """Tests for empty slides list handling."""

    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_empty_slides_list(
        self, mock_system, mock_validator, mock_analytics, tmp_path
    ):
        """Test execute with empty slides list."""
        mock_system.return_value = "Linux"

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [],
                "presentation_path": str(pres_path),
                "skip_export_errors": True,
            }
        )

        result = skill.execute(input_data)

        assert result.success is True
        assert result.data["summary"]["total_slides"] == 0
        assert result.data["pass_rate"] == 0.0


# ==============================================================================
# Test DPI Configuration
# ==============================================================================


class TestDPIConfiguration:
    """Tests for DPI configuration."""

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_uses_custom_dpi(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute uses custom DPI value."""
        mock_system.return_value = "Windows"

        mock_exporter_instance = MagicMock()
        mock_exporter_class.return_value = mock_exporter_instance

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                "dpi": 300,
            }
        )

        skill.execute(input_data)

        # Second call to SlideExporter (first is platform detection)
        # Check that it was called with resolution=300
        calls = mock_exporter_class.call_args_list
        # The second call should have resolution=300
        assert any(call.kwargs.get("resolution") == 300 for call in calls if call.kwargs)

    @patch("plugin.skills.images.validation_skill.SlideExporter")
    @patch("plugin.skills.images.validation_skill.WorkflowAnalytics")
    @patch("plugin.skills.images.validation_skill.VisualValidator")
    @patch("plugin.skills.images.validation_skill.platform.system")
    def test_execute_uses_default_dpi(
        self, mock_system, mock_validator_class, mock_analytics, mock_exporter_class, tmp_path
    ):
        """Test execute uses default DPI (150) when not specified."""
        mock_system.return_value = "Windows"

        mock_exporter_instance = MagicMock()
        mock_exporter_class.return_value = mock_exporter_instance

        mock_analytics_instance = MagicMock()
        mock_analytics.return_value = mock_analytics_instance
        mock_analytics_instance.generate_report.return_value = {"workflow_id": "test"}

        mock_validator_class.return_value = MagicMock()

        pres_path = tmp_path / "presentation.pptx"
        pres_path.touch()

        skill = ValidationSkill()

        input_data = SkillInput(
            data={
                "slides": [{"title": "Test Slide", "type": "content"}],
                "presentation_path": str(pres_path),
                # No dpi specified
            }
        )

        skill.execute(input_data)

        # Check that SlideExporter was called with default resolution=150
        calls = mock_exporter_class.call_args_list
        assert any(call.kwargs.get("resolution") == 150 for call in calls if call.kwargs)
