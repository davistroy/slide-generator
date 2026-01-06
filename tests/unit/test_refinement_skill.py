"""
Unit tests for RefinementSkill.

Tests the image refinement skill that iteratively improves slide images
based on validation feedback with interactive user approval.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plugin.base_skill import SkillInput
from plugin.lib.presentation.refinement_engine import RefinementStrategy
from plugin.lib.presentation.visual_validator import ValidationResult
from plugin.skills.assembly.refinement_skill import RefinementSkill


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def refinement_skill():
    """Create a RefinementSkill instance with mocked dependencies."""
    with (
        patch(
            "plugin.skills.assembly.refinement_skill.RefinementEngine"
        ) as mock_engine,
        patch(
            "plugin.skills.assembly.refinement_skill.VisualValidator"
        ) as mock_validator,
        patch(
            "plugin.skills.assembly.refinement_skill.CostEstimator"
        ) as mock_estimator,
    ):
        skill = RefinementSkill()
        skill.refinement_engine = mock_engine.return_value
        skill.validator = mock_validator.return_value
        skill.cost_estimator = mock_estimator.return_value

        # Default cost estimate
        mock_cost = MagicMock()
        mock_cost.total_cost = 0.30
        skill.cost_estimator.estimate_gemini_cost.return_value = mock_cost

        yield skill


@pytest.fixture
def sample_slides():
    """Sample slide data for testing."""
    return [
        {
            "title": "Introduction",
            "graphics_description": "A diagram showing the overview",
        },
        {
            "title": "Main Content",
            "graphics_description": "An illustration of key concepts",
        },
        {
            "title": "Conclusion",
            "graphics_description": "A summary visualization",
        },
    ]


@pytest.fixture
def passing_validation_results():
    """Validation results where all slides pass."""
    return [
        ValidationResult(
            passed=True,
            score=85.0,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        ),
        ValidationResult(
            passed=True,
            score=90.0,
            issues=[],
            suggestions=[],
            raw_feedback="Excellent",
            rubric_scores={},
        ),
        ValidationResult(
            passed=True,
            score=80.0,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        ),
    ]


@pytest.fixture
def failing_validation_results():
    """Validation results where some slides fail."""
    return [
        ValidationResult(
            passed=False,
            score=65.0,
            issues=["Image too small", "Colors mismatch brand"],
            suggestions=["Increase image size", "Use brand colors"],
            raw_feedback="Needs improvement",
            rubric_scores={},
        ),
        ValidationResult(
            passed=True,
            score=80.0,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        ),
        ValidationResult(
            passed=False,
            score=70.0,
            issues=["Text visible in image"],
            suggestions=["Remove all text from graphic"],
            raw_feedback="Minor issues",
            rubric_scores={},
        ),
    ]


@pytest.fixture
def mock_refinement_strategy():
    """Sample refinement strategy."""
    return RefinementStrategy(
        modified_prompt="Enhanced graphic with larger visual elements and brand colors",
        parameter_adjustments={"fast_mode": False},
        reasoning="Image too small - emphasizing size in prompt",
        confidence=0.75,
    )


@pytest.fixture
def valid_input(sample_slides, failing_validation_results, tmp_path):
    """Valid input for refinement skill."""
    # Create output directory
    output_dir = tmp_path / "refinement"
    output_dir.mkdir()

    return SkillInput(
        data={
            "slides": sample_slides,
            "validation_results": failing_validation_results,
            "presentation_path": str(tmp_path / "presentation.pptx"),
            "output_dir": str(output_dir),
            "max_refinements": 3,
            "interactive": False,  # Non-interactive for testing
            "auto_approve_threshold": 0.8,
        },
        context={},
        config={},
    )


# ==============================================================================
# Test Skill Properties
# ==============================================================================


class TestRefinementSkillProperties:
    """Tests for RefinementSkill properties."""

    def test_skill_id(self, refinement_skill):
        """Test skill_id property returns correct value."""
        assert refinement_skill.skill_id == "refine-images"

    def test_display_name(self, refinement_skill):
        """Test display_name property returns correct value."""
        assert refinement_skill.display_name == "Image Refinement"

    def test_description(self, refinement_skill):
        """Test description property returns correct value."""
        assert "improve slide images" in refinement_skill.description.lower()
        assert "validation feedback" in refinement_skill.description.lower()


# ==============================================================================
# Test Input Validation
# ==============================================================================


class TestRefinementSkillValidation:
    """Tests for RefinementSkill input validation."""

    def test_validate_input_with_required_fields(
        self, refinement_skill, sample_slides, failing_validation_results
    ):
        """Test validation passes with all required fields."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": "test.pptx",
            }
        )
        is_valid, errors = refinement_skill.validate_input(input_data)
        assert is_valid is True
        assert errors == []

    def test_validate_input_missing_slides(
        self, refinement_skill, failing_validation_results
    ):
        """Test validation fails when slides are missing."""
        input_data = SkillInput(
            data={
                "validation_results": failing_validation_results,
                "presentation_path": "test.pptx",
            }
        )
        is_valid, errors = refinement_skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_missing_validation_results(
        self, refinement_skill, sample_slides
    ):
        """Test validation fails when validation_results are missing."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "presentation_path": "test.pptx",
            }
        )
        is_valid, errors = refinement_skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_missing_presentation_path(
        self, refinement_skill, sample_slides, failing_validation_results
    ):
        """Test validation fails when presentation_path is missing."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
            }
        )
        is_valid, errors = refinement_skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_input_empty_data(self, refinement_skill):
        """Test validation fails with empty data."""
        input_data = SkillInput(data={})
        is_valid, errors = refinement_skill.validate_input(input_data)
        assert is_valid is False
        assert len(errors) > 0


# ==============================================================================
# Test Execute - Invalid Input
# ==============================================================================


class TestRefinementSkillExecuteInvalidInput:
    """Tests for RefinementSkill execute with invalid input."""

    def test_execute_with_invalid_input_returns_failure(self, refinement_skill):
        """Test execute returns failure when input is invalid."""
        input_data = SkillInput(data={})  # Missing required fields
        result = refinement_skill.execute(input_data)

        assert result.success is False
        assert len(result.errors) > 0
        # Check for missing field error message
        assert (
            "missing" in result.errors[0].lower()
            or "required" in result.errors[0].lower()
        )

    def test_execute_with_missing_slides_returns_failure(
        self, refinement_skill, failing_validation_results
    ):
        """Test execute returns failure when slides are missing."""
        input_data = SkillInput(
            data={
                "validation_results": failing_validation_results,
                "presentation_path": "test.pptx",
            }
        )
        result = refinement_skill.execute(input_data)

        assert result.success is False
        # Check for slides missing error
        assert "slides" in result.errors[0].lower()


# ==============================================================================
# Test Execute - All Slides Pass Validation
# ==============================================================================


class TestRefinementSkillExecuteAllPass:
    """Tests for RefinementSkill execute when all slides pass validation."""

    def test_execute_no_refinements_needed(
        self, refinement_skill, sample_slides, passing_validation_results, tmp_path
    ):
        """Test execute when no slides need refinement."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": passing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "interactive": False,
            }
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        assert result.data["slides_refined"] == 0
        assert result.data["total_attempts"] == 0
        assert len(result.data["refinement_results"]) == 0

    def test_execute_with_all_passing_returns_zero_cost(
        self, refinement_skill, sample_slides, passing_validation_results, tmp_path
    ):
        """Test execute returns zero cost when no refinements needed."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": passing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "interactive": False,
            }
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.data["total_cost"] == 0.0


# ==============================================================================
# Test Execute - Slides Need Refinement
# ==============================================================================


class TestRefinementSkillExecuteWithRefinements:
    """Tests for RefinementSkill execute when slides need refinement."""

    def test_execute_identifies_slides_needing_refinement(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute correctly identifies slides that need refinement."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        assert result.success is True
        # 2 slides failed validation (slides 1 and 3)
        assert len(result.data["refinement_results"]) == 2

    def test_execute_calls_refinement_engine(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute calls refinement engine for each failing slide."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        # Should be called for each failing slide (2 slides)
        assert refinement_skill.refinement_engine.generate_refinement.call_count >= 2

    def test_execute_tracks_api_calls(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute tracks API calls in analytics."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        # Verify analytics API tracking was called
        mock_analytics_instance.track_api_call.assert_called()

    def test_execute_returns_refinement_results_with_improvement(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute returns results showing score improvement."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        # Check refinement results contain improvement data
        for refinement_result in result.data["refinement_results"]:
            assert "initial_score" in refinement_result
            assert "final_score" in refinement_result
            assert "improvement" in refinement_result
            assert refinement_result["improvement"] >= 0


# ==============================================================================
# Test Execute - Budget Constraints
# ==============================================================================


class TestRefinementSkillBudgetConstraints:
    """Tests for RefinementSkill budget handling."""

    def test_execute_respects_cost_budget(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute stops refinement when budget is exceeded."""
        # Set a very low budget
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 3,
                "interactive": False,
                "cost_budget": 0.01,  # Very low budget
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        # Set cost higher than budget
        mock_cost = MagicMock()
        mock_cost.total_cost = 0.30
        refinement_skill.cost_estimator.estimate_gemini_cost.return_value = mock_cost

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        # Should still succeed but with limited refinements
        assert result.success is True
        # Cost should be within or near budget (first attempt allowed)
        assert result.data["total_cost"] <= mock_cost.total_cost + 0.01

    def test_execute_no_budget_no_limit(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute continues refinement when no budget is set."""
        # Remove budget constraint
        valid_input.data["cost_budget"] = None

        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        assert result.success is True
        # Should have attempted refinements
        assert result.data["total_attempts"] > 0


# ==============================================================================
# Test Execute - Interactive Mode
# ==============================================================================


class TestRefinementSkillInteractiveMode:
    """Tests for RefinementSkill interactive mode."""

    def test_execute_prompts_user_in_interactive_mode(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute prompts user when in interactive mode with low confidence."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 1,
                "interactive": True,
                "auto_approve_threshold": 0.9,  # High threshold
            }
        )

        # Low confidence strategy triggers user prompt
        low_confidence_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.5,  # Below threshold
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            low_confidence_strategy
        )

        with (
            patch(
                "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
            ) as mock_analytics,
            patch("builtins.input", return_value="y") as mock_input,
        ):
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        # Should have called input for user approval
        mock_input.assert_called()
        assert result.success is True

    def test_execute_user_declines_refinement(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute skips refinement when user declines."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 1,
                "interactive": True,
                "auto_approve_threshold": 0.9,
            }
        )

        low_confidence_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.5,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            low_confidence_strategy
        )

        with (
            patch(
                "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
            ) as mock_analytics,
            patch("builtins.input", return_value="n"),
        ):
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        # No cost incurred when user declines
        assert result.data["total_cost"] == 0.0

    def test_execute_auto_approves_high_confidence(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute auto-approves when confidence is above threshold."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 1,
                "interactive": True,
                "auto_approve_threshold": 0.7,  # Lower threshold
            }
        )

        high_confidence_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.85,  # Above threshold
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            high_confidence_strategy
        )

        with (
            patch(
                "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
            ) as mock_analytics,
            patch("builtins.input") as mock_input,
        ):
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        # Should NOT have called input (auto-approved)
        mock_input.assert_not_called()
        assert result.success is True


# ==============================================================================
# Test Execute - Max Refinements
# ==============================================================================


class TestRefinementSkillMaxRefinements:
    """Tests for RefinementSkill max refinements limit."""

    def test_execute_respects_max_refinements(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute stops after max refinements reached."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 2,  # Limit to 2 attempts
                "interactive": False,
            }
        )

        # Strategy that never passes (low simulated improvement)
        low_improvement_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.3,  # Low confidence = low improvement
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            low_improvement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        # Check that attempts don't exceed max per slide
        for refinement_result in result.data["refinement_results"]:
            assert refinement_result["attempts"] <= 2

    def test_execute_metadata_contains_max_refinements(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute includes max_refinements in metadata."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        assert "max_refinements" in result.metadata
        assert result.metadata["max_refinements"] == 3


# ==============================================================================
# Test Execute - Output Directory
# ==============================================================================


class TestRefinementSkillOutputDirectory:
    """Tests for RefinementSkill output directory handling."""

    def test_execute_creates_output_directory_if_not_exists(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute creates output directory if it doesn't exist."""
        output_dir = tmp_path / "new_refinement_dir"
        assert not output_dir.exists()

        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "output_dir": str(output_dir),
                "interactive": False,
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        assert output_dir.exists()

    def test_execute_uses_default_output_dir_when_not_specified(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses default output directory when not specified."""
        pres_path = tmp_path / "presentation.pptx"

        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(pres_path),
                # No output_dir specified
                "interactive": False,
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        # Default directory should be created
        default_dir = tmp_path / "refinement"
        assert default_dir.exists()

    def test_execute_artifacts_contain_output_dir(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute includes output directory in artifacts."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        assert len(result.artifacts) > 0
        assert valid_input.data["output_dir"] in result.artifacts


# ==============================================================================
# Test Execute - Analytics and Reporting
# ==============================================================================


class TestRefinementSkillAnalytics:
    """Tests for RefinementSkill analytics tracking."""

    def test_execute_starts_analytics_phase(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute starts analytics refinement phase."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        mock_analytics_instance.start_phase.assert_called_with("refinement")

    def test_execute_ends_analytics_phase(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute ends analytics refinement phase."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        mock_analytics_instance.end_phase.assert_called()

    def test_execute_tracks_refinement_attempts(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute tracks refinement attempts in analytics."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        # Should track refinement attempts
        mock_analytics_instance.track_refinement_attempt.assert_called()

    def test_execute_returns_analytics_in_data(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute includes analytics report in output data."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        expected_report = {"test": "report"}

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = expected_report

            result = refinement_skill.execute(valid_input)

        assert "analytics" in result.data
        assert result.data["analytics"] == expected_report


# ==============================================================================
# Test Execute - Diminishing Returns
# ==============================================================================


class TestRefinementSkillDiminishingReturns:
    """Tests for RefinementSkill diminishing returns handling."""

    def test_execute_stops_on_diminishing_returns(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute stops refinement when improvement is negligible."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 5,  # High limit
                "interactive": False,
            }
        )

        # Very low confidence = negligible improvement
        low_improvement_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.1,  # Very low = < 5% improvement
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            low_improvement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        # Should stop early due to diminishing returns (improvement < 5)
        for refinement_result in result.data["refinement_results"]:
            # With confidence 0.1, improvement = 5.0 * 0.1 = 0.5 < 5.0
            # So it should stop after first attempt
            assert refinement_result["attempts"] <= 2


# ==============================================================================
# Test Execute - Slide Passes During Refinement
# ==============================================================================


class TestRefinementSkillSlidePassesDuringRefinement:
    """Tests for RefinementSkill when slides pass during refinement."""

    def test_execute_stops_when_slide_passes(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute stops refinement when slide reaches passing score."""
        # Start with a score of 70, need to reach 75 to pass
        failing_validation_results[0] = ValidationResult(
            passed=False,
            score=70.0,
            issues=["Minor issue"],
            suggestions=["Minor fix"],
            raw_feedback="Almost there",
            rubric_scores={},
        )

        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "max_refinements": 5,
                "interactive": False,
                "presentation_path": str(tmp_path / "presentation.pptx"),
            }
        )

        # High confidence = good improvement (5.0 * 0.9 = 4.5)
        # 70 + 4.5 = 74.5, still not passing
        # But with confidence 1.0: 5.0 * 1.0 = 5.0, 70 + 5 = 75, passes!
        high_improvement_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=1.0,  # Maximum confidence
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            high_improvement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.success is True
        # First slide should pass after refinement
        first_slide_result = result.data["refinement_results"][0]
        assert first_slide_result["final_score"] >= 75.0


# ==============================================================================
# Test Execute - Slide Numbers and Ordering
# ==============================================================================


class TestRefinementSkillSlideNumbering:
    """Tests for RefinementSkill slide numbering."""

    def test_execute_uses_correct_slide_numbers(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses 1-based slide numbers."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "interactive": False,
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        # Slide numbers should be 1-based
        for refinement_result in result.data["refinement_results"]:
            assert refinement_result["slide_number"] >= 1
            assert refinement_result["slide_number"] <= len(sample_slides)


# ==============================================================================
# Test Default Parameters
# ==============================================================================


class TestRefinementSkillDefaultParameters:
    """Tests for RefinementSkill default parameter handling."""

    def test_execute_uses_default_max_refinements(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses default max_refinements of 3."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                # No max_refinements specified
                "interactive": False,
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.metadata["max_refinements"] == 3

    def test_execute_uses_default_interactive_true(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses default interactive mode of True."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                # No interactive specified - defaults to True
            }
        )

        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.9,  # Above default threshold
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        assert result.metadata["interactive"] is True

    def test_execute_uses_default_auto_approve_threshold(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses default auto_approve_threshold of 0.8."""
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "interactive": True,
                # No auto_approve_threshold specified - defaults to 0.8
            }
        )

        # Confidence exactly at 0.8 should auto-approve
        mock_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=0.8,  # At default threshold
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_strategy
        )

        with (
            patch(
                "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
            ) as mock_analytics,
            patch("builtins.input") as mock_input,
        ):
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(input_data)

        # Should NOT prompt user (auto-approved at threshold)
        mock_input.assert_not_called()
        assert result.success is True


# ==============================================================================
# Test Image Path Generation
# ==============================================================================


class TestRefinementSkillImagePaths:
    """Tests for RefinementSkill image path generation."""

    def test_execute_generates_correct_image_paths(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute generates correct image paths for refined images."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            result = refinement_skill.execute(valid_input)

        # Check image paths follow expected pattern
        for refinement_result in result.data["refinement_results"]:
            if refinement_result["best_image_path"]:
                path = Path(refinement_result["best_image_path"])
                assert "slide-" in path.name
                assert "-attempt-" in path.name
                assert path.suffix == ".jpg"


# ==============================================================================
# Test Error Handling
# ==============================================================================


class TestRefinementSkillErrorHandling:
    """Tests for RefinementSkill error handling."""

    def test_execute_handles_refinement_engine_error(
        self, refinement_skill, valid_input
    ):
        """Test execute handles errors from refinement engine gracefully."""
        refinement_skill.refinement_engine.generate_refinement.side_effect = Exception(
            "Engine error"
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            # Should raise exception (not caught in execute)
            with pytest.raises(Exception, match="Engine error"):
                refinement_skill.execute(valid_input)

    def test_execute_handles_cost_estimator_error(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute handles errors from cost estimator."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )
        refinement_skill.cost_estimator.estimate_gemini_cost.side_effect = Exception(
            "Cost estimation error"
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            # Should raise exception
            with pytest.raises(Exception, match="Cost estimation error"):
                refinement_skill.execute(valid_input)


# ==============================================================================
# Test Resolution Parameter
# ==============================================================================


class TestRefinementSkillResolution:
    """Tests for RefinementSkill resolution handling."""

    def test_execute_uses_standard_resolution_first_attempt(
        self, refinement_skill, valid_input, mock_refinement_strategy
    ):
        """Test execute uses standard resolution on first attempt."""
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            mock_refinement_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(valid_input)

        # Check first call used "standard" resolution
        calls = refinement_skill.cost_estimator.estimate_gemini_cost.call_args_list
        if calls:
            first_call = calls[0]
            assert (
                first_call.kwargs.get(
                    "resolution",
                    first_call.args[1] if len(first_call.args) > 1 else "standard",
                )
                == "standard"
            )

    def test_execute_uses_4k_resolution_subsequent_attempts(
        self, refinement_skill, sample_slides, failing_validation_results, tmp_path
    ):
        """Test execute uses 4K resolution on subsequent attempts."""
        # Set up for multiple attempts
        input_data = SkillInput(
            data={
                "slides": sample_slides,
                "validation_results": failing_validation_results,
                "presentation_path": str(tmp_path / "presentation.pptx"),
                "max_refinements": 3,
                "interactive": False,
            }
        )

        # Higher confidence to get improvements > 5 points (avoids diminishing returns stop)
        # Simulated improvement = 5.0 * confidence, so need confidence > 1.0 for > 5 point gain
        higher_confidence_strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt",
            parameter_adjustments={},
            reasoning="Test reasoning",
            confidence=1.5,  # High confidence = 7.5 point improvement per attempt
        )
        refinement_skill.refinement_engine.generate_refinement.return_value = (
            higher_confidence_strategy
        )

        with patch(
            "plugin.skills.assembly.refinement_skill.WorkflowAnalytics"
        ) as mock_analytics:
            mock_analytics_instance = MagicMock()
            mock_analytics.return_value = mock_analytics_instance
            mock_analytics_instance.generate_report.return_value = {}

            refinement_skill.execute(input_data)

        # Check that 4K was used for later attempts
        calls = refinement_skill.cost_estimator.estimate_gemini_cost.call_args_list
        if len(calls) > 1:
            # Second call should use 4K
            second_call = calls[1]
            resolution_arg = second_call.kwargs.get("resolution")
            if resolution_arg is None and len(second_call.args) > 1:
                resolution_arg = second_call.args[1]
            assert resolution_arg == "4K"
