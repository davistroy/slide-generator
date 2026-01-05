"""
Slide Refinement Engine

Interprets validation feedback and generates refined image generation parameters
to improve slide quality through iterative refinement.

Strategy:
- Pattern-based issue detection and remediation
- Progressive parameter escalation (prompt refinement -> 4K mode)
- Maximum 3 refinement attempts per slide
- Smart stopping when improvements are negligible

Refinement Approach:
- Attempt 1: Prompt enhancement only (fast mode OK)
- Attempt 2+: Force 4K generation + enhanced prompts (higher quality)
- Stop early if validation score improves < 5%
"""

import re
from dataclasses import dataclass

# Import from local modules
from .parser import Slide
from .visual_validator import ValidationResult


@dataclass
class RefinementStrategy:
    """
    Strategy for refining a slide based on validation feedback.

    Attributes:
        modified_prompt: Enhanced graphic description for image regeneration
        parameter_adjustments: Dict of generation parameters to change
        reasoning: Explanation of why this refinement strategy was chosen
        confidence: Confidence that this refinement will help (0.0 to 1.0)
    """

    modified_prompt: str
    parameter_adjustments: dict[str, any]
    reasoning: str
    confidence: float


class RefinementEngine:
    """
    Generates refinement strategies based on validation feedback.

    Uses pattern matching to detect common issues and applies targeted
    remediation strategies through prompt enhancement and parameter adjustment.

    Progressive Escalation:
    - Attempt 1: Prompt refinement (keep fast_mode if enabled)
    - Attempt 2+: Force 4K generation (fast_mode=False) + prompt refinement
    - Max attempts: 3 (hard cap)

    Early Stopping:
    - Stop if score improvement < 5% between attempts
    - Stop if score already >= 90% (diminishing returns)
    - Stop if max attempts reached
    """

    # Issue patterns and their remediation strategies
    # Pattern matches issue text -> prompt additions and parameter changes
    ISSUE_PATTERNS = {
        # Image sizing issues
        r"image.*(too small|tiny|barely visible)": {
            "prompt_addition": "IMPORTANT: Make the visual element LARGE and PROMINENT, filling most of the available image space. The graphic should be the dominant element.",
            "reasoning": "Image too small - emphasizing size in prompt",
        },
        r"image.*(too large|overwhelming|obscures)": {
            "prompt_addition": "IMPORTANT: Keep visual element BALANCED in size, leaving adequate whitespace. Do not let graphic dominate the entire composition.",
            "reasoning": "Image too large - requesting balanced sizing",
        },
        # Color issues
        r"color.*(mismatch|wrong|incorrect|off-brand)": {
            "prompt_addition": "CRITICAL: Use ONLY the exact brand colors specified in the style guide. Do not deviate from the approved color palette under any circumstances.",
            "reasoning": "Color mismatch - enforcing strict brand colors",
        },
        r"color.*(washed out|pale|faded)": {
            "prompt_addition": "Use vibrant, saturated brand colors. Colors should be bold and clear, not muted or desaturated.",
            "reasoning": "Colors too pale - requesting saturation",
        },
        # Text in images (common issue)
        r"text.*(in image|visible|overlaid|embedded)": {
            "prompt_addition": "ABSOLUTELY NO TEXT, NO LABELS, NO WORDS in the generated image. Pure visual graphic only. Text will be added separately in PowerPoint.",
            "param": {"notext": True},
            "reasoning": "Text found in image - emphasizing text-free generation",
        },
        r"(chart|diagram|graph).*(labels|text|numbers)": {
            "prompt_addition": "Generate diagram WITHOUT any text labels, numbers, or annotations. Show only the visual structure and relationships. All labeling will be done separately.",
            "param": {"notext": True},
            "reasoning": "Chart has text labels - requesting label-free diagrams",
        },
        # Visual clarity issues
        r"(blur|fuzzy|unclear|low quality)": {
            "param": {"fast_mode": False},
            "reasoning": "Image quality issues - forcing 4K generation",
        },
        r"(cluttered|busy|complex|overwhelming)": {
            "prompt_addition": "SIMPLIFY the visual design. Use clean, minimal composition with clear focal point. Remove unnecessary details.",
            "reasoning": "Visual clutter - requesting simplification",
        },
        # Layout and composition
        r"(spacing|layout|composition).*(awkward|poor|unbalanced)": {
            "prompt_addition": "Ensure clean, balanced composition with proper use of negative space. Follow rule of thirds for visual interest.",
            "reasoning": "Layout issues - emphasizing composition principles",
        },
        r"(crop|cut off|truncated)": {
            "prompt_addition": "Ensure all visual elements fit completely within the image bounds. Nothing should be cut off or cropped awkwardly.",
            "reasoning": "Cropping issues - requesting complete elements",
        },
        # Style and aesthetic
        r"(unprofessional|amateurish|poor quality)": {
            "prompt_addition": "Create polished, professional-grade graphic with high production value. This should look like it came from a professional design studio.",
            "param": {"fast_mode": False},
            "reasoning": "Professional quality needed - forcing 4K + quality prompt",
        },
        r"style.*(inconsistent|doesn\'t match)": {
            "prompt_addition": "Strictly follow the exact visual style specified in the style guide. Maintain perfect consistency with brand aesthetic.",
            "reasoning": "Style mismatch - emphasizing brand consistency",
        },
        # NEW PATTERNS (PRIORITY 4.2 Enhancement)
        # Aspect ratio issues
        r"aspect.*(ratio|stretched|squashed|distorted)": {
            "prompt_addition": "CRITICAL: Maintain correct aspect ratio for all visual elements. Nothing should appear stretched, squashed, or distorted. Use 16:9 widescreen format.",
            "reasoning": "Aspect ratio mismatch - requesting proper proportions",
        },
        r"(wide|narrow).*(stretched|compressed)": {
            "prompt_addition": "Preserve natural proportions of all objects. Ensure elements maintain their intended shape without horizontal or vertical distortion.",
            "reasoning": "Proportional distortion detected - enforcing natural dimensions",
        },
        # Brand color dominance
        r"(too much|excessive|overwhelming).*(brand color|red|blue)": {
            "prompt_addition": "Use brand colors SPARINGLY as accents, not as dominant fill. Balance brand colors with neutrals (white, gray) to avoid overwhelming the composition.",
            "reasoning": "Brand color overuse - requesting balanced palette",
        },
        r"(too little|not enough|barely visible).*(brand color|red|blue)": {
            "prompt_addition": "INCREASE presence of brand colors as key visual elements. Brand colors should be prominent and noticeable, but balanced.",
            "reasoning": "Insufficient brand color - requesting more prominent usage",
        },
        r"monotone|monochromatic|single color": {
            "prompt_addition": "Use FULL brand color palette strategically. Include primary and accent colors to create visual interest and depth.",
            "reasoning": "Limited color range - requesting varied palette",
        },
        # Visual complexity (too busy)
        r"too.*(busy|cluttered|chaotic|noisy)": {
            "prompt_addition": "DRASTICALLY SIMPLIFY the composition. Use minimal elements, clean lines, generous whitespace. One clear focal point only.",
            "reasoning": "Visual overload - requesting extreme simplification",
        },
        r"(hard to|difficult to|can\'t).*(understand|read|parse|see)": {
            "prompt_addition": "Create CRYSTAL CLEAR, instantly understandable visual. Reduce complexity, increase contrast, emphasize key elements.",
            "reasoning": "Comprehension difficulty - requesting clarity",
        },
        # Visual complexity (too simple)
        r"too.*(simple|plain|boring|empty)": {
            "prompt_addition": "ADD visual interest with subtle details, texture, depth, or layering. Make the graphic more engaging while keeping it professional.",
            "reasoning": "Insufficient visual interest - requesting enhanced details",
        },
        r"(sparse|bare|minimal|lacking).*(detail|interest|depth)": {
            "prompt_addition": "Enrich the visual with thoughtful details, dimension, and visual hierarchy. Add depth without creating clutter.",
            "reasoning": "Visual emptiness - requesting balanced enrichment",
        },
        # Image clarity (pixelated)
        r"pixelat|jaggy|aliased|low.?res": {
            "prompt_addition": "Generate ULTRA HIGH QUALITY image with smooth lines, anti-aliasing, and crisp details. No pixelation or jagged edges.",
            "param": {"fast_mode": False},
            "reasoning": "Pixelation detected - forcing 4K with quality emphasis",
        },
        r"(grainy|noisy|artifacts)": {
            "prompt_addition": "Produce clean, artifact-free image with smooth gradients and noise-free rendering. Professional print-quality output.",
            "param": {"fast_mode": False},
            "reasoning": "Image artifacts - forcing 4K generation",
        },
        # Composition balance
        r"(off.?center|unbalanced|lopsided|asymmetric)": {
            "prompt_addition": "Create WELL-BALANCED composition using rule of thirds or centered symmetry. Distribute visual weight evenly across the frame.",
            "reasoning": "Compositional imbalance - requesting balanced layout",
        },
        r"(awkward|uncomfortable|strange).*(placement|position|arrangement)": {
            "prompt_addition": "Position elements naturally with proper spacing and alignment. Follow compositional best practices for visual harmony.",
            "reasoning": "Awkward element placement - requesting natural arrangement",
        },
        r"empty.*(corner|space|area|region)": {
            "prompt_addition": "Utilize available space effectively. Extend visual elements or add subtle design accents to fill empty regions without cluttering.",
            "reasoning": "Inefficient space usage - requesting better utilization",
        },
        # Lighting and depth
        r"(flat|no depth|2d|lacks dimension)": {
            "prompt_addition": "Add subtle shadows, highlights, and gradients to create depth and dimension. Make the graphic feel three-dimensional and polished.",
            "reasoning": "Flat appearance - requesting depth cues",
        },
        r"(dark|muddy|hard to see)": {
            "prompt_addition": "BRIGHTEN the overall image with better lighting. Ensure all elements are clearly visible with good contrast and luminosity.",
            "reasoning": "Visibility issues - requesting brighter rendering",
        },
        r"(washed out|overexposed|too bright)": {
            "prompt_addition": "Reduce overall brightness and add richer, deeper colors. Ensure good tonal range with visible shadows and highlights.",
            "reasoning": "Overexposure - requesting balanced tones",
        },
    }

    # Minimum score improvement to continue refining (5%)
    MIN_IMPROVEMENT_THRESHOLD = 0.05

    # Score threshold where refinement has diminishing returns (90%)
    DIMINISHING_RETURNS_THRESHOLD = 0.90

    def __init__(self):
        """Initialize refinement engine."""
        pass

    def generate_refinement(
        self,
        slide: Slide,
        validation_result: ValidationResult,
        attempt_number: int,
        previous_score: float | None = None,
    ) -> RefinementStrategy:
        """
        Generate refinement strategy based on validation feedback.

        Args:
            slide: Original Slide object
            validation_result: ValidationResult with issues and suggestions
            attempt_number: Current attempt number (1, 2, 3...)
            previous_score: Score from previous attempt (for improvement tracking)

        Returns:
            RefinementStrategy with enhanced prompt and parameter adjustments
        """
        # Start with original graphic description
        base_prompt = slide.graphic or "Professional slide graphic"

        # Collect prompt additions from pattern matching
        prompt_additions = []
        param_adjustments = {}
        reasoning_parts = []

        # Analyze each issue and apply matching patterns
        for issue in validation_result.issues:
            for pattern, remedy in self.ISSUE_PATTERNS.items():
                if re.search(pattern, issue, re.IGNORECASE):
                    # Add prompt enhancement if specified
                    if "prompt_addition" in remedy:
                        prompt_additions.append(remedy["prompt_addition"])

                    # Add parameter adjustments if specified
                    if "param" in remedy:
                        param_adjustments.update(remedy["param"])

                    # Track reasoning
                    if "reasoning" in remedy:
                        reasoning_parts.append(remedy["reasoning"])

        # Incorporate suggestions from validation feedback
        for suggestion in validation_result.suggestions:
            # Extract actionable suggestions
            if "font" in suggestion.lower() or "size" in suggestion.lower():
                # Skip font/sizing suggestions (handled by PowerPoint layout, not image gen)
                continue

            # Add relevant suggestions to prompt
            prompt_additions.append(f"Suggestion: {suggestion}")
            reasoning_parts.append(f"Following validator suggestion: {suggestion[:50]}")

        # Progressive escalation: Force 4K on attempt 2+
        if attempt_number >= 2:
            param_adjustments["fast_mode"] = False
            reasoning_parts.append(
                f"Attempt {attempt_number}: forcing 4K generation for quality"
            )

        # Build refined prompt
        if prompt_additions:
            # Add enhancements to base prompt
            refined_prompt = f"{base_prompt}\n\nREFINEMENT REQUIREMENTS:\n"
            refined_prompt += "\n".join(
                f"- {addition}" for addition in prompt_additions[:5]
            )  # Limit to top 5
        else:
            # No specific patterns matched - general quality enhancement
            refined_prompt = f"{base_prompt}\n\nGeneral refinement: Improve visual quality, clarity, and brand alignment."
            reasoning_parts.append(
                "No specific issues matched - general quality improvement"
            )

        # Calculate confidence based on pattern matches and attempt number
        confidence = self._calculate_confidence(
            len(prompt_additions),
            attempt_number,
            validation_result.score,
            previous_score,
        )

        # Combine reasoning
        reasoning = (
            " | ".join(reasoning_parts)
            if reasoning_parts
            else "General refinement attempt"
        )

        return RefinementStrategy(
            modified_prompt=refined_prompt,
            parameter_adjustments=param_adjustments,
            reasoning=reasoning,
            confidence=confidence,
        )

    def should_retry(
        self,
        validation_result: ValidationResult,
        attempt_number: int,
        max_attempts: int = 3,
        previous_score: float | None = None,
    ) -> bool:
        """
        Determine if refinement should continue.

        Args:
            validation_result: Current validation result
            attempt_number: Current attempt number
            max_attempts: Maximum allowed attempts (default: 3)
            previous_score: Score from previous attempt (for improvement tracking)

        Returns:
            True if should retry, False if should accept current result
        """
        # Hard cap at max attempts
        if attempt_number >= max_attempts:
            return False

        # Already passed validation - accept it
        if validation_result.passed:
            # Check for diminishing returns (score already >= 90%)
            if validation_result.score >= self.DIMINISHING_RETURNS_THRESHOLD:
                return False  # Accept - further refinement has diminishing returns

            # If we have previous score, check improvement
            if previous_score is not None:
                improvement = validation_result.score - previous_score

                # If improvement is too small, stop refining
                if improvement < self.MIN_IMPROVEMENT_THRESHOLD:
                    return False  # Accept - minimal improvement

            # Passed but has room for improvement - continue if attempts remain
            return True

        # Failed validation - definitely retry if attempts remain
        return True

    def _calculate_confidence(
        self,
        pattern_matches: int,
        attempt_number: int,
        current_score: float,
        previous_score: float | None,
    ) -> float:
        """
        Calculate confidence that refinement will improve the slide.

        Args:
            pattern_matches: Number of issue patterns that matched
            attempt_number: Current attempt number
            current_score: Current validation score
            previous_score: Previous validation score (if available)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence starts at 0.5
        confidence = 0.5

        # More pattern matches = higher confidence we can fix it
        if pattern_matches > 0:
            confidence += min(0.3, pattern_matches * 0.1)

        # Lower confidence on later attempts (law of diminishing returns)
        confidence -= (attempt_number - 1) * 0.15

        # If previous score exists and showed improvement, boost confidence
        if previous_score is not None:
            improvement = current_score - previous_score
            if improvement > 0:
                confidence += 0.1  # Positive momentum

        # Clamp to 0.0 - 1.0
        return max(0.0, min(1.0, confidence))


# Test function for development
def main():
    """Test the refinement engine (for development)."""
    from plugin.lib.presentation.visual_validator import ValidationResult

    print("=" * 80)
    print("Refinement Engine Test")
    print("=" * 80)

    # Create test validation result
    test_result = ValidationResult(
        passed=False,
        score=0.65,
        issues=[
            "Image is too small and barely visible",
            "Text labels are visible in the diagram",
            "Colors don't match brand palette",
        ],
        suggestions=[
            "Increase image size to fill available space",
            "Remove all text from graphic",
            "Use brand colors from style guide",
        ],
        raw_feedback="Test feedback",
        rubric_scores={},
    )

    # Create test slide
    from plugin.lib.presentation.parser import Slide

    test_slide = Slide(
        number=5,
        slide_type="IMAGE",
        title="Test Slide",
        subtitle="",
        content_bullets=[],
        graphic="Professional architectural diagram showing system components and data flow",
        speaker_notes="",
        raw_content="",
    )

    # Initialize engine
    engine = RefinementEngine()

    # Generate refinement for attempt 1
    print("\n[ATTEMPT 1]")
    strategy1 = engine.generate_refinement(test_slide, test_result, attempt_number=1)

    print(f"Confidence: {strategy1.confidence:.2f}")
    print(f"Reasoning: {strategy1.reasoning}")
    print(f"Parameter Adjustments: {strategy1.parameter_adjustments}")
    print(f"Modified Prompt (first 200 chars):\n{strategy1.modified_prompt[:200]}...")

    # Simulate improvement for attempt 2
    test_result2 = ValidationResult(
        passed=False,
        score=0.70,  # Improved from 0.65
        issues=["Image still slightly small", "Color palette needs adjustment"],
        suggestions=["Increase image 20% more"],
        raw_feedback="Test feedback 2",
        rubric_scores={},
    )

    print("\n[ATTEMPT 2]")
    should_continue = engine.should_retry(
        test_result2, attempt_number=2, previous_score=0.65
    )
    print(f"Should retry: {should_continue}")

    if should_continue:
        strategy2 = engine.generate_refinement(
            test_slide, test_result2, attempt_number=2, previous_score=0.65
        )
        print(f"Confidence: {strategy2.confidence:.2f}")
        print(f"Reasoning: {strategy2.reasoning}")
        print(f"Parameter Adjustments: {strategy2.parameter_adjustments}")

    # Test passing result with high score
    print("\n[HIGH SCORE TEST]")
    high_score_result = ValidationResult(
        passed=True,
        score=0.92,
        issues=[],
        suggestions=[],
        raw_feedback="Excellent",
        rubric_scores={},
    )

    should_continue = engine.should_retry(high_score_result, attempt_number=2)
    print(f"Score: 0.92 (passed) - Should retry: {should_continue}")

    print("\n" + "=" * 80)
    print("Refinement engine test complete!")


if __name__ == "__main__":
    main()
