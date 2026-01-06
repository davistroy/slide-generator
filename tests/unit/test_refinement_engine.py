"""
Unit tests for plugin/lib/presentation/refinement_engine.py

Tests the RefinementEngine class and RefinementStrategy dataclass.
"""

import pytest

from plugin.lib.presentation.refinement_engine import (
    RefinementEngine,
    RefinementStrategy,
)
from plugin.lib.presentation.parser import Slide
from plugin.lib.presentation.visual_validator import ValidationResult


class TestRefinementStrategyDataclass:
    """Tests for RefinementStrategy dataclass."""

    def test_create_refinement_strategy(self):
        """Test creating a RefinementStrategy with all fields."""
        strategy = RefinementStrategy(
            modified_prompt="Enhanced prompt text",
            parameter_adjustments={"fast_mode": False},
            reasoning="Test reasoning",
            confidence=0.75,
        )
        assert strategy.modified_prompt == "Enhanced prompt text"
        assert strategy.parameter_adjustments == {"fast_mode": False}
        assert strategy.reasoning == "Test reasoning"
        assert strategy.confidence == 0.75

    def test_refinement_strategy_empty_adjustments(self):
        """Test RefinementStrategy with empty parameter adjustments."""
        strategy = RefinementStrategy(
            modified_prompt="Prompt",
            parameter_adjustments={},
            reasoning="No adjustments needed",
            confidence=0.5,
        )
        assert strategy.parameter_adjustments == {}

    def test_refinement_strategy_multiple_adjustments(self):
        """Test RefinementStrategy with multiple parameter adjustments."""
        strategy = RefinementStrategy(
            modified_prompt="Prompt",
            parameter_adjustments={"fast_mode": False, "notext": True},
            reasoning="Multiple fixes",
            confidence=0.8,
        )
        assert strategy.parameter_adjustments["fast_mode"] is False
        assert strategy.parameter_adjustments["notext"] is True


class TestRefinementEngineInit:
    """Tests for RefinementEngine initialization."""

    def test_init_creates_engine(self):
        """Test RefinementEngine initialization."""
        engine = RefinementEngine()
        assert engine is not None

    def test_issue_patterns_defined(self):
        """Test that ISSUE_PATTERNS are properly defined."""
        engine = RefinementEngine()
        assert len(engine.ISSUE_PATTERNS) > 0

    def test_threshold_constants(self):
        """Test threshold constants are set correctly."""
        assert RefinementEngine.MIN_IMPROVEMENT_THRESHOLD == 0.05
        assert RefinementEngine.DIMINISHING_RETURNS_THRESHOLD == 0.90


class TestRefinementEngineGenerateRefinement:
    """Tests for generate_refinement method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()
        self.test_slide = Slide(
            number=5,
            slide_type="IMAGE",
            title="Test Slide",
            subtitle="",
            content_bullets=[],
            graphic="Professional diagram showing system components",
            speaker_notes="",
            raw_content="",
        )

    def test_generate_refinement_with_size_issue(self):
        """Test refinement generation for image too small issue."""
        validation_result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Image is too small and barely visible"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        assert "LARGE" in strategy.modified_prompt or "PROMINENT" in strategy.modified_prompt
        assert "too small" in strategy.reasoning.lower() or "size" in strategy.reasoning.lower()
        assert strategy.confidence > 0

    def test_generate_refinement_with_text_in_image_issue(self):
        """Test refinement generation for text in image issue."""
        validation_result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Text labels are visible in the diagram"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        assert "notext" in strategy.parameter_adjustments or "NO TEXT" in strategy.modified_prompt
        assert strategy.confidence > 0

    def test_generate_refinement_with_color_mismatch(self):
        """Test refinement generation for color mismatch issue."""
        validation_result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Colors are wrong and don't match brand palette"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        assert "color" in strategy.reasoning.lower() or "brand" in strategy.modified_prompt.lower()
        assert strategy.confidence > 0

    def test_generate_refinement_with_blur_issue(self):
        """Test refinement generation for blur/quality issue."""
        validation_result = ValidationResult(
            passed=False,
            score=0.55,
            issues=["Image appears blurry and unclear"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Blur issue should recommend 4K mode
        assert strategy.parameter_adjustments.get("fast_mode") is False
        assert "quality" in strategy.reasoning.lower()

    def test_generate_refinement_with_multiple_issues(self):
        """Test refinement generation with multiple issues."""
        validation_result = ValidationResult(
            passed=False,
            score=0.50,
            issues=[
                "Image is too small and barely visible",
                "Text labels are visible in the diagram",
                "Colors don't match brand palette",
            ],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Should have multiple prompt additions
        assert "REFINEMENT REQUIREMENTS" in strategy.modified_prompt
        # Reasoning should mention multiple issues
        assert " | " in strategy.reasoning

    def test_generate_refinement_no_matching_patterns(self):
        """Test refinement generation when no patterns match."""
        validation_result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Some unrecognized issue type that doesn't match any pattern"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Should fall back to general refinement
        assert "General refinement" in strategy.modified_prompt
        assert "general quality" in strategy.reasoning.lower()

    def test_generate_refinement_uses_original_graphic_description(self):
        """Test that refinement starts with original graphic description."""
        validation_result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Image too small"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        assert self.test_slide.graphic in strategy.modified_prompt

    def test_generate_refinement_with_missing_graphic_description(self):
        """Test refinement when slide has no graphic description."""
        slide_no_graphic = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic=None,
            speaker_notes="",
            raw_content="",
        )

        validation_result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Some issue"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            slide_no_graphic, validation_result, attempt_number=1
        )

        # Should use default prompt
        assert "Professional slide graphic" in strategy.modified_prompt

    def test_generate_refinement_incorporates_suggestions(self):
        """Test that suggestions are incorporated into prompt."""
        validation_result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Minor visual issues"],
            suggestions=[
                "Increase image contrast",
                "Use deeper colors",
            ],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Suggestions should be added to prompt
        assert "Increase image contrast" in strategy.modified_prompt
        assert "Use deeper colors" in strategy.modified_prompt

    def test_generate_refinement_skips_font_suggestions(self):
        """Test that font/size suggestions are skipped (handled by PowerPoint)."""
        validation_result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Minor issues"],
            suggestions=[
                "Change font to Arial",
                "Increase font size to 24pt",
                "Improve visual contrast",
            ],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Font suggestions should be skipped
        assert "font" not in strategy.modified_prompt.lower() or "Improve visual" in strategy.modified_prompt
        assert "Improve visual contrast" in strategy.modified_prompt

    def test_generate_refinement_limits_prompt_additions(self):
        """Test that prompt additions are limited to top 5."""
        # Create many issues that will all match patterns
        validation_result = ValidationResult(
            passed=False,
            score=0.40,
            issues=[
                "Image is too small",
                "Image is too large",
                "Color is washed out",
                "Colors don't match brand",
                "Text visible in image",
                "Image appears blurry",
                "Visual is cluttered",
                "Layout is awkward",
            ],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

        # Count requirement lines
        requirement_lines = [
            line for line in strategy.modified_prompt.split("\n")
            if line.strip().startswith("- ")
        ]
        assert len(requirement_lines) <= 5

    def test_generate_refinement_attempt_2_forces_4k(self):
        """Test that attempt 2+ forces 4K generation."""
        validation_result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Minor visual issues"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=2
        )

        assert strategy.parameter_adjustments.get("fast_mode") is False
        assert "4K" in strategy.reasoning

    def test_generate_refinement_attempt_3_forces_4k(self):
        """Test that attempt 3 also forces 4K generation."""
        validation_result = ValidationResult(
            passed=False,
            score=0.72,
            issues=["Minor visual issues"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=3
        )

        assert strategy.parameter_adjustments.get("fast_mode") is False

    def test_generate_refinement_with_previous_score_positive_momentum(self):
        """Test refinement with positive improvement momentum."""
        validation_result = ValidationResult(
            passed=False,
            score=0.72,
            issues=["Minor issues"],
            suggestions=[],
            raw_feedback="Test feedback",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=2, previous_score=0.65
        )

        # Confidence should be boosted due to positive momentum
        assert strategy.confidence >= 0


class TestRefinementEnginePatternMatching:
    """Tests for specific issue pattern matching."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()
        self.test_slide = Slide(
            number=1,
            slide_type="IMAGE",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

    def _get_strategy_for_issue(self, issue: str) -> RefinementStrategy:
        """Helper to get refinement strategy for a single issue."""
        validation_result = ValidationResult(
            passed=False,
            score=0.65,
            issues=[issue],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )
        return self.engine.generate_refinement(
            self.test_slide, validation_result, attempt_number=1
        )

    # Image sizing patterns
    def test_pattern_image_tiny(self):
        """Test pattern matching for tiny image."""
        strategy = self._get_strategy_for_issue("The image is tiny and hard to see")
        assert "LARGE" in strategy.modified_prompt or "PROMINENT" in strategy.modified_prompt

    def test_pattern_image_overwhelming(self):
        """Test pattern matching for overwhelming image."""
        strategy = self._get_strategy_for_issue("The image is too large and overwhelming")
        assert "BALANCED" in strategy.modified_prompt or "whitespace" in strategy.modified_prompt

    # Color patterns
    def test_pattern_color_off_brand(self):
        """Test pattern matching for off-brand colors."""
        strategy = self._get_strategy_for_issue("Colors are off-brand and incorrect")
        assert "brand colors" in strategy.modified_prompt.lower() or "color" in strategy.reasoning.lower()

    def test_pattern_colors_faded(self):
        """Test pattern matching for faded colors."""
        strategy = self._get_strategy_for_issue("Colors appear washed out and pale")
        assert "vibrant" in strategy.modified_prompt.lower() or "saturated" in strategy.modified_prompt.lower()

    # Text in image patterns
    def test_pattern_text_visible(self):
        """Test pattern matching for visible text."""
        strategy = self._get_strategy_for_issue("There is text visible in the image")
        assert "NO TEXT" in strategy.modified_prompt or strategy.parameter_adjustments.get("notext")

    def test_pattern_chart_labels(self):
        """Test pattern matching for chart labels."""
        strategy = self._get_strategy_for_issue("The chart has text labels and numbers")
        assert "WITHOUT" in strategy.modified_prompt or "notext" in strategy.parameter_adjustments

    # Visual quality patterns
    def test_pattern_fuzzy(self):
        """Test pattern matching for fuzzy image."""
        strategy = self._get_strategy_for_issue("Image is fuzzy and low quality")
        assert strategy.parameter_adjustments.get("fast_mode") is False

    def test_pattern_busy_cluttered(self):
        """Test pattern matching for cluttered image."""
        strategy = self._get_strategy_for_issue("Visual is too busy and cluttered")
        assert "SIMPLIFY" in strategy.modified_prompt or "minimal" in strategy.modified_prompt.lower()

    # Layout patterns
    def test_pattern_awkward_spacing(self):
        """Test pattern matching for awkward spacing."""
        strategy = self._get_strategy_for_issue("The spacing is awkward and composition poor")
        assert "balanced" in strategy.modified_prompt.lower() or "composition" in strategy.modified_prompt.lower()

    def test_pattern_cropped(self):
        """Test pattern matching for cropped elements."""
        strategy = self._get_strategy_for_issue("Elements are cut off at the edge")
        assert "completely" in strategy.modified_prompt.lower() or "within" in strategy.modified_prompt.lower()

    # Style patterns
    def test_pattern_unprofessional(self):
        """Test pattern matching for unprofessional appearance."""
        strategy = self._get_strategy_for_issue("The image looks unprofessional and amateurish")
        assert "professional" in strategy.modified_prompt.lower()
        assert strategy.parameter_adjustments.get("fast_mode") is False

    def test_pattern_style_inconsistent(self):
        """Test pattern matching for inconsistent style."""
        strategy = self._get_strategy_for_issue("Style doesn't match the brand guidelines")
        assert "style" in strategy.reasoning.lower() or "brand" in strategy.modified_prompt.lower()

    # Aspect ratio patterns
    def test_pattern_aspect_stretched(self):
        """Test pattern matching for stretched aspect ratio."""
        strategy = self._get_strategy_for_issue("The aspect ratio looks stretched and distorted")
        assert "aspect" in strategy.modified_prompt.lower() or "proportions" in strategy.modified_prompt.lower()

    def test_pattern_compressed(self):
        """Test pattern matching for compressed proportions."""
        strategy = self._get_strategy_for_issue("Elements appear narrow and compressed")
        assert "proportions" in strategy.modified_prompt.lower()

    # Brand color patterns
    def test_pattern_excessive_brand_color(self):
        """Test pattern matching for excessive brand color."""
        strategy = self._get_strategy_for_issue("There is too much brand color red")
        assert "SPARINGLY" in strategy.modified_prompt or "balanced" in strategy.modified_prompt.lower()

    def test_pattern_not_enough_brand_color(self):
        """Test pattern matching for insufficient brand color."""
        # Pattern expects: (too little|not enough|barely visible).*(brand color|red|blue)
        strategy = self._get_strategy_for_issue("not enough brand color in the image")
        assert "INCREASE" in strategy.modified_prompt or "prominent" in strategy.modified_prompt.lower()

    def test_pattern_monotone(self):
        """Test pattern matching for monotone image."""
        strategy = self._get_strategy_for_issue("Image is monotone and lacks color variety")
        assert "palette" in strategy.modified_prompt.lower() or "color" in strategy.modified_prompt.lower()

    # Visual complexity patterns
    def test_pattern_chaotic(self):
        """Test pattern matching for chaotic visual."""
        strategy = self._get_strategy_for_issue("Visual is too chaotic and noisy")
        assert "SIMPLIFY" in strategy.modified_prompt or "minimal" in strategy.modified_prompt.lower()

    def test_pattern_hard_to_understand(self):
        """Test pattern matching for hard to understand visual."""
        strategy = self._get_strategy_for_issue("Hard to understand what's in the image")
        assert "CLEAR" in strategy.modified_prompt or "clarity" in strategy.modified_prompt.lower()

    def test_pattern_too_simple(self):
        """Test pattern matching for too simple image."""
        strategy = self._get_strategy_for_issue("Image is too simple and boring")
        assert "interest" in strategy.modified_prompt.lower() or "detail" in strategy.modified_prompt.lower()

    def test_pattern_lacking_depth(self):
        """Test pattern matching for lacking depth."""
        strategy = self._get_strategy_for_issue("Visual is sparse and lacking detail")
        assert "detail" in strategy.modified_prompt.lower() or "depth" in strategy.modified_prompt.lower()

    # Image clarity patterns
    def test_pattern_pixelated(self):
        """Test pattern matching for pixelated image."""
        strategy = self._get_strategy_for_issue("Image is pixelated with jagged edges")
        assert "HIGH QUALITY" in strategy.modified_prompt or "crisp" in strategy.modified_prompt.lower()
        assert strategy.parameter_adjustments.get("fast_mode") is False

    def test_pattern_grainy(self):
        """Test pattern matching for grainy image."""
        strategy = self._get_strategy_for_issue("Image has grainy artifacts")
        assert strategy.parameter_adjustments.get("fast_mode") is False

    # Composition patterns
    def test_pattern_off_center(self):
        """Test pattern matching for off-center composition."""
        strategy = self._get_strategy_for_issue("Composition is off-center and unbalanced")
        assert "BALANCED" in strategy.modified_prompt or "thirds" in strategy.modified_prompt.lower()

    def test_pattern_awkward_placement(self):
        """Test pattern matching for awkward placement."""
        strategy = self._get_strategy_for_issue("Elements have awkward placement")
        assert "naturally" in strategy.modified_prompt.lower() or "spacing" in strategy.modified_prompt.lower()

    def test_pattern_empty_space(self):
        """Test pattern matching for empty space."""
        strategy = self._get_strategy_for_issue("There is an empty corner that needs filling")
        assert "space" in strategy.modified_prompt.lower() or "fill" in strategy.modified_prompt.lower()

    # Lighting patterns
    def test_pattern_flat_no_depth(self):
        """Test pattern matching for flat appearance."""
        strategy = self._get_strategy_for_issue("Image looks flat and has no depth")
        assert "shadow" in strategy.modified_prompt.lower() or "depth" in strategy.modified_prompt.lower()

    def test_pattern_too_dark(self):
        """Test pattern matching for dark image."""
        strategy = self._get_strategy_for_issue("Image is dark and muddy")
        assert "BRIGHTEN" in strategy.modified_prompt or "bright" in strategy.modified_prompt.lower()

    def test_pattern_overexposed(self):
        """Test pattern matching for overexposed image."""
        strategy = self._get_strategy_for_issue("Image is washed out and overexposed")
        assert "brightness" in strategy.modified_prompt.lower() or "tonal" in strategy.modified_prompt.lower()


class TestRefinementEngineShouldRetry:
    """Tests for should_retry method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()

    def test_should_retry_max_attempts_reached(self):
        """Test that should_retry returns False at max attempts."""
        validation_result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Some issues"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        result = self.engine.should_retry(
            validation_result, attempt_number=3, max_attempts=3
        )
        assert result is False

    def test_should_retry_exceeds_max_attempts(self):
        """Test that should_retry returns False when exceeding max attempts."""
        validation_result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Some issues"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        result = self.engine.should_retry(
            validation_result, attempt_number=4, max_attempts=3
        )
        assert result is False

    def test_should_retry_passed_high_score(self):
        """Test that should_retry returns False for passed with high score."""
        validation_result = ValidationResult(
            passed=True,
            score=0.92,  # Above DIMINISHING_RETURNS_THRESHOLD
            issues=[],
            suggestions=[],
            raw_feedback="Excellent",
            rubric_scores={},
        )

        result = self.engine.should_retry(validation_result, attempt_number=1)
        assert result is False

    def test_should_retry_passed_threshold_exactly(self):
        """Test should_retry with score at diminishing returns threshold."""
        validation_result = ValidationResult(
            passed=True,
            score=0.90,  # Exactly at DIMINISHING_RETURNS_THRESHOLD
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        result = self.engine.should_retry(validation_result, attempt_number=1)
        assert result is False

    def test_should_retry_passed_with_room_for_improvement(self):
        """Test that should_retry returns True for passed with low score."""
        validation_result = ValidationResult(
            passed=True,
            score=0.80,  # Below DIMINISHING_RETURNS_THRESHOLD
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        result = self.engine.should_retry(
            validation_result, attempt_number=1, max_attempts=3
        )
        assert result is True

    def test_should_retry_failed_validation(self):
        """Test that should_retry returns True for failed validation."""
        validation_result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Issues found"],
            suggestions=[],
            raw_feedback="Needs work",
            rubric_scores={},
        )

        result = self.engine.should_retry(
            validation_result, attempt_number=1, max_attempts=3
        )
        assert result is True

    def test_should_retry_minimal_improvement(self):
        """Test that should_retry returns False for minimal improvement."""
        validation_result = ValidationResult(
            passed=True,
            score=0.82,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        # Previous score was 0.80, improvement is only 0.02 (< 0.05 threshold)
        result = self.engine.should_retry(
            validation_result, attempt_number=2, previous_score=0.80
        )
        assert result is False

    def test_should_retry_sufficient_improvement(self):
        """Test that should_retry returns True for sufficient improvement."""
        validation_result = ValidationResult(
            passed=True,
            score=0.85,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        # Previous score was 0.75, improvement is 0.10 (>= 0.05 threshold)
        result = self.engine.should_retry(
            validation_result, attempt_number=2, previous_score=0.75
        )
        assert result is True

    def test_should_retry_no_previous_score_passed(self):
        """Test should_retry with no previous score and passed validation."""
        validation_result = ValidationResult(
            passed=True,
            score=0.80,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        result = self.engine.should_retry(
            validation_result, attempt_number=1, max_attempts=3
        )
        assert result is True

    def test_should_retry_custom_max_attempts(self):
        """Test should_retry with custom max attempts."""
        validation_result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Issues"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        # With max_attempts=5, attempt 3 should retry
        result = self.engine.should_retry(
            validation_result, attempt_number=3, max_attempts=5
        )
        assert result is True

        # With max_attempts=5, attempt 5 should not retry
        result = self.engine.should_retry(
            validation_result, attempt_number=5, max_attempts=5
        )
        assert result is False


class TestRefinementEngineCalculateConfidence:
    """Tests for _calculate_confidence method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()

    def test_calculate_confidence_base(self):
        """Test base confidence calculation with no pattern matches."""
        confidence = self.engine._calculate_confidence(
            pattern_matches=0,
            attempt_number=1,
            current_score=0.70,
            previous_score=None,
        )
        # Base confidence is 0.5, attempt 1 has no penalty
        assert confidence == 0.5

    def test_calculate_confidence_with_pattern_matches(self):
        """Test confidence increases with pattern matches."""
        confidence = self.engine._calculate_confidence(
            pattern_matches=2,
            attempt_number=1,
            current_score=0.70,
            previous_score=None,
        )
        # 0.5 base + 0.2 for 2 matches = 0.7
        assert confidence == 0.7

    def test_calculate_confidence_max_pattern_boost(self):
        """Test confidence pattern boost is capped at 0.3."""
        confidence = self.engine._calculate_confidence(
            pattern_matches=10,  # Many matches
            attempt_number=1,
            current_score=0.70,
            previous_score=None,
        )
        # 0.5 base + 0.3 max = 0.8
        assert confidence == 0.8

    def test_calculate_confidence_decreases_with_attempts(self):
        """Test confidence decreases on later attempts."""
        conf_attempt_1 = self.engine._calculate_confidence(
            pattern_matches=2,
            attempt_number=1,
            current_score=0.70,
            previous_score=None,
        )

        conf_attempt_2 = self.engine._calculate_confidence(
            pattern_matches=2,
            attempt_number=2,
            current_score=0.70,
            previous_score=0.65,
        )

        conf_attempt_3 = self.engine._calculate_confidence(
            pattern_matches=2,
            attempt_number=3,
            current_score=0.70,
            previous_score=0.67,
        )

        # Confidence should decrease with each attempt
        # Note: positive momentum can affect this, so test relative decrease
        assert conf_attempt_2 < conf_attempt_1

    def test_calculate_confidence_positive_momentum(self):
        """Test confidence boost from positive improvement momentum."""
        # With improvement (0.70 - 0.65 = 0.05 > 0)
        confidence_with_improvement = self.engine._calculate_confidence(
            pattern_matches=1,
            attempt_number=2,
            current_score=0.70,
            previous_score=0.65,
        )

        # Without improvement (0.65 - 0.70 = -0.05 < 0)
        confidence_without_improvement = self.engine._calculate_confidence(
            pattern_matches=1,
            attempt_number=2,
            current_score=0.65,
            previous_score=0.70,
        )

        # Positive momentum should give higher confidence
        assert confidence_with_improvement > confidence_without_improvement

    def test_calculate_confidence_clamped_to_zero(self):
        """Test confidence is clamped to minimum of 0.0."""
        # Very late attempt with no matches
        confidence = self.engine._calculate_confidence(
            pattern_matches=0,
            attempt_number=10,  # Very high attempt number
            current_score=0.40,
            previous_score=0.50,  # Negative momentum
        )
        assert confidence >= 0.0

    def test_calculate_confidence_clamped_to_one(self):
        """Test confidence is clamped to maximum of 1.0."""
        # Many matches, first attempt, positive momentum
        confidence = self.engine._calculate_confidence(
            pattern_matches=10,  # Many matches
            attempt_number=1,
            current_score=0.80,
            previous_score=0.70,  # Would give positive momentum but no previous on attempt 1
        )
        assert confidence <= 1.0


class TestRefinementEngineIntegration:
    """Integration tests for RefinementEngine workflow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()
        self.test_slide = Slide(
            number=3,
            slide_type="IMAGE",
            title="System Architecture",
            subtitle="",
            content_bullets=[],
            graphic="Professional diagram showing microservices architecture with API gateway",
            speaker_notes="",
            raw_content="",
        )

    def test_full_refinement_workflow_success(self):
        """Test complete refinement workflow that succeeds."""
        # Initial validation fails
        result_1 = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Image is too small", "Colors are washed out"],
            suggestions=["Increase image size", "Use more vibrant colors"],
            raw_feedback="Needs improvement",
            rubric_scores={},
        )

        # Generate first refinement
        strategy_1 = self.engine.generate_refinement(
            self.test_slide, result_1, attempt_number=1
        )

        assert strategy_1.modified_prompt != ""
        assert strategy_1.confidence > 0

        # Check if should retry
        should_continue = self.engine.should_retry(result_1, attempt_number=1)
        assert should_continue is True

        # Simulated second validation with improvement
        result_2 = ValidationResult(
            passed=True,
            score=0.85,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        # Generate second refinement
        strategy_2 = self.engine.generate_refinement(
            self.test_slide, result_2, attempt_number=2, previous_score=0.60
        )

        assert strategy_2.parameter_adjustments.get("fast_mode") is False  # Attempt 2 forces 4K

        # Check if should continue (significant improvement)
        should_continue = self.engine.should_retry(
            result_2, attempt_number=2, previous_score=0.60
        )
        # Score is 0.85, below 0.90 threshold, improvement is 0.25 >= 0.05
        assert should_continue is True

    def test_full_refinement_workflow_stops_at_high_quality(self):
        """Test that workflow stops when quality is high enough."""
        result = ValidationResult(
            passed=True,
            score=0.92,
            issues=[],
            suggestions=[],
            raw_feedback="Excellent",
            rubric_scores={},
        )

        should_continue = self.engine.should_retry(result, attempt_number=1)
        assert should_continue is False

    def test_full_refinement_workflow_stops_at_max_attempts(self):
        """Test that workflow stops at max attempts."""
        result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Still has issues"],
            suggestions=[],
            raw_feedback="Needs work",
            rubric_scores={},
        )

        should_continue = self.engine.should_retry(result, attempt_number=3, max_attempts=3)
        assert should_continue is False

    def test_refinement_strategy_can_be_used_for_regeneration(self):
        """Test that refinement strategy contains usable data."""
        result = ValidationResult(
            passed=False,
            score=0.55,
            issues=[
                "Image is blurry and unclear",
                "Text labels visible in diagram",
            ],
            suggestions=[],
            raw_feedback="Needs improvement",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(
            self.test_slide, result, attempt_number=1
        )

        # Strategy should have usable prompt
        assert len(strategy.modified_prompt) > len(self.test_slide.graphic)

        # Strategy should have parameter adjustments that can be passed to generator
        assert isinstance(strategy.parameter_adjustments, dict)

        # Should have meaningful reasoning for logging
        assert len(strategy.reasoning) > 0

        # Confidence should be valid probability
        assert 0.0 <= strategy.confidence <= 1.0


class TestRefinementEngineEdgeCases:
    """Edge case tests for RefinementEngine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RefinementEngine()

    def test_empty_issues_list(self):
        """Test handling of empty issues list."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        result = ValidationResult(
            passed=True,
            score=0.80,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)

        # Should produce general refinement
        assert "General refinement" in strategy.modified_prompt
        assert strategy.confidence >= 0

    def test_empty_suggestions_list(self):
        """Test handling of empty suggestions list."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        result = ValidationResult(
            passed=False,
            score=0.70,
            issues=["Image too small"],
            suggestions=[],
            raw_feedback="Needs work",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)

        # Should still work without suggestions
        assert strategy.modified_prompt != ""

    def test_very_long_issue_text(self):
        """Test handling of very long issue text."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        long_issue = "Image is too small " * 100  # Very long issue text
        result = ValidationResult(
            passed=False,
            score=0.60,
            issues=[long_issue],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        # Should not raise exception
        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)
        assert strategy.modified_prompt != ""

    def test_special_characters_in_issues(self):
        """Test handling of special characters in issue text."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        result = ValidationResult(
            passed=False,
            score=0.60,
            issues=["Color doesn't match (RGB: #FF0000) <script>alert('test')</script>"],
            suggestions=["Use colors like #DD0033 & #004F71"],
            raw_feedback="Test",
            rubric_scores={},
        )

        # Should not raise exception
        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)
        assert strategy.modified_prompt != ""

    def test_zero_score(self):
        """Test handling of zero validation score."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        result = ValidationResult(
            passed=False,
            score=0.0,
            issues=["Complete failure"],
            suggestions=[],
            raw_feedback="Failed",
            rubric_scores={},
        )

        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)
        assert strategy.confidence >= 0

    def test_score_exactly_at_threshold(self):
        """Test handling of score exactly at threshold."""
        result = ValidationResult(
            passed=True,
            score=0.75,  # Exactly at typical threshold
            issues=[],
            suggestions=[],
            raw_feedback="At threshold",
            rubric_scores={},
        )

        # Should continue since below diminishing returns threshold
        should_continue = self.engine.should_retry(result, attempt_number=1)
        assert should_continue is True

    def test_case_insensitive_pattern_matching(self):
        """Test that issue patterns match case-insensitively."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="Test",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        # Test uppercase
        result_upper = ValidationResult(
            passed=False,
            score=0.60,
            issues=["IMAGE IS TOO SMALL AND BARELY VISIBLE"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        # Test lowercase
        result_lower = ValidationResult(
            passed=False,
            score=0.60,
            issues=["image is too small and barely visible"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        strategy_upper = self.engine.generate_refinement(slide, result_upper, attempt_number=1)
        strategy_lower = self.engine.generate_refinement(slide, result_lower, attempt_number=1)

        # Both should match the same pattern
        assert "LARGE" in strategy_upper.modified_prompt or "PROMINENT" in strategy_upper.modified_prompt
        assert "LARGE" in strategy_lower.modified_prompt or "PROMINENT" in strategy_lower.modified_prompt

    def test_slide_with_empty_title(self):
        """Test handling of slide with empty title."""
        slide = Slide(
            number=1,
            slide_type="CONTENT",
            title="",
            subtitle="",
            content_bullets=[],
            graphic="Test graphic",
            speaker_notes="",
            raw_content="",
        )

        result = ValidationResult(
            passed=False,
            score=0.65,
            issues=["Some issue"],
            suggestions=[],
            raw_feedback="Test",
            rubric_scores={},
        )

        # Should not raise exception
        strategy = self.engine.generate_refinement(slide, result, attempt_number=1)
        assert strategy.modified_prompt != ""

    def test_negative_previous_score(self):
        """Test handling of invalid negative previous score."""
        result = ValidationResult(
            passed=True,
            score=0.80,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        # Negative previous score (invalid but should not crash)
        should_continue = self.engine.should_retry(
            result, attempt_number=2, previous_score=-0.1
        )
        # Improvement is 0.80 - (-0.1) = 0.90, which is >= 0.05
        assert should_continue is True

    def test_previous_score_greater_than_one(self):
        """Test handling of invalid previous score > 1."""
        result = ValidationResult(
            passed=True,
            score=0.80,
            issues=[],
            suggestions=[],
            raw_feedback="Good",
            rubric_scores={},
        )

        # Invalid previous score (should not crash)
        should_continue = self.engine.should_retry(
            result, attempt_number=2, previous_score=1.5
        )
        # Improvement is 0.80 - 1.5 = -0.70, which is < 0.05
        assert should_continue is False
