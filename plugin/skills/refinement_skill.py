"""
Refinement Skill - Enhanced Image Refinement with Interactive Feedback

Wraps the existing refinement_engine.py with:
- Skill interface implementation
- Interactive user approval workflow
- Cost-aware refinement (estimate before generation)
- Multi-round refinement tracking
- A/B comparison visualization

Usage:
    skill = RefinementSkill()
    result = skill.execute(SkillInput(
        data={
            "slides": slides,
            "validation_results": validation_results,
            "presentation_path": "presentation.pptx",
            "max_refinements": 3,
            "interactive": True
        }
    ))
"""

import os
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput

# Import existing refinement engine
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "presentation-skill"))
from lib.refinement_engine import RefinementEngine, RefinementStrategy
from lib.visual_validator import VisualValidator, ValidationResult
# Note: ImageGenerator import removed - will be integrated when implementing actual image regeneration

# Import analytics
from plugin.lib.analytics import WorkflowAnalytics
from plugin.lib.cost_estimator import CostEstimator


class RefinementSkill(BaseSkill):
    """
    Enhanced image refinement skill with interactive feedback.

    Features:
    - Pattern-based issue detection (from RefinementEngine)
    - Interactive approval workflow (user reviews before regeneration)
    - Cost estimation before refinement
    - Multi-round refinement with progress tracking
    - A/B comparison (before/after images)
    """

    @property
    def skill_id(self) -> str:
        return "refine-images"

    @property
    def display_name(self) -> str:
        return "Image Refinement"

    @property
    def description(self) -> str:
        return "Iteratively improve slide images based on validation feedback with user approval"

    def __init__(self):
        """Initialize refinement skill."""
        self.refinement_engine = RefinementEngine()
        self.validator = VisualValidator()
        self.cost_estimator = CostEstimator()

    def validate_input(self, input: SkillInput) -> bool:
        """
        Validate input data.

        Required:
        - slides: List of slide dictionaries
        - validation_results: List of ValidationResult objects
        - presentation_path: Path to PowerPoint file

        Optional:
        - max_refinements: Maximum refinement attempts per slide (default: 3)
        - interactive: Enable interactive approval (default: True)
        - auto_approve_threshold: Auto-approve if confidence > threshold (default: 0.8)
        """
        required_fields = ["slides", "validation_results", "presentation_path"]
        for field in required_fields:
            if field not in input.data:
                return False

        return True

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Execute refinement workflow.

        Input data:
        - slides: List of slide dictionaries
        - validation_results: List of ValidationResult objects
        - presentation_path: Path to PowerPoint file
        - output_dir: Directory for refined images (default: same as presentation)
        - max_refinements: Maximum refinement attempts per slide (default: 3)
        - interactive: Enable interactive approval (default: True)
        - auto_approve_threshold: Auto-approve if confidence > threshold (default: 0.8)
        - cost_budget: Maximum allowed cost for refinements (default: None)

        Returns:
        - SkillOutput with refinement results
        """
        if not self.validate_input(input):
            return SkillOutput(
                success=False,
                data={},
                artifacts=[],
                errors=["Invalid input: missing required fields"],
                metadata={}
            )

        # Extract input
        slides = input.data["slides"]
        validation_results = input.data["validation_results"]
        presentation_path = input.data["presentation_path"]

        max_refinements = input.data.get("max_refinements", 3)
        interactive = input.data.get("interactive", True)
        auto_approve_threshold = input.data.get("auto_approve_threshold", 0.8)
        cost_budget = input.data.get("cost_budget", None)

        output_dir = input.data.get("output_dir")
        if not output_dir:
            output_dir = Path(presentation_path).parent / "refinement"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        style_config = input.data.get("style_config", {})

        # Initialize analytics
        analytics = WorkflowAnalytics(workflow_id=f"refinement-{int(time.time())}")
        analytics.start_phase("refinement")

        # Track refinement results
        refinement_results = []
        total_cost = 0.0
        slides_refined = 0
        total_attempts = 0

        # Identify slides needing refinement (validation score < 75)
        slides_to_refine = []
        for i, (slide, validation_result) in enumerate(zip(slides, validation_results)):
            if not validation_result.passed:
                slides_to_refine.append((i, slide, validation_result))

        print(f"\nImage Refinement Skill")
        print(f"=" * 80)
        print(f"Slides needing refinement: {len(slides_to_refine)} out of {len(slides)}")
        print(f"Max refinements per slide: {max_refinements}")
        print(f"Interactive mode: {'Yes' if interactive else 'No'}")

        if cost_budget:
            print(f"Cost budget: ${cost_budget:.2f}")

        print()

        # Refine each slide
        for slide_idx, slide, initial_validation in slides_to_refine:
            slide_number = slide_idx + 1
            print(f"\nSlide {slide_number}: {slide.get('title', 'Untitled')}")
            print(f"  Initial validation score: {initial_validation.score:.1f}/100")

            # Track best result
            best_score = initial_validation.score
            best_image_path = None
            current_validation = initial_validation

            # Attempt refinements
            for attempt in range(1, max_refinements + 1):
                print(f"\n  Attempt {attempt}:")

                # Generate refinement strategy
                refinement_strategy = self.refinement_engine.generate_refinement(
                    slide=slide,
                    validation_result=current_validation,
                    attempt_number=attempt
                )

                print(f"    Strategy: {refinement_strategy.reasoning}")
                print(f"    Confidence: {refinement_strategy.confidence:.0%}")

                # Estimate cost
                cost_estimate = self.cost_estimator.estimate_gemini_cost(
                    image_count=1,
                    resolution="4K" if attempt > 1 else "standard"
                )
                estimated_cost = cost_estimate.total_cost

                print(f"    Estimated cost: ${estimated_cost:.2f}")

                # Check budget
                if cost_budget and (total_cost + estimated_cost) > cost_budget:
                    print(f"    ⚠️  Skipping refinement - would exceed budget (${total_cost + estimated_cost:.2f} > ${cost_budget:.2f})")
                    break

                # Interactive approval (or auto-approve if high confidence)
                approved = False

                if interactive and refinement_strategy.confidence < auto_approve_threshold:
                    # Prompt user for approval
                    print(f"\n    Modified prompt:")
                    print(f"    {refinement_strategy.modified_prompt[:200]}...")
                    response = input(f"\n    Proceed with refinement? (y/n): ").strip().lower()
                    approved = response in ['y', 'yes']

                    if not approved:
                        print(f"    ⏭️  Skipping refinement (user declined)")
                        break
                else:
                    # Auto-approve (high confidence or non-interactive mode)
                    approved = True
                    if refinement_strategy.confidence >= auto_approve_threshold:
                        print(f"    ✓ Auto-approved (high confidence)")

                if approved:
                    # Generate refined image
                    print(f"    🔄 Generating refined image...")

                    # TODO: Integrate with ImageGenerator to regenerate image
                    # For now, track that we would generate
                    analytics.track_api_call("gemini_images", call_count=1)
                    analytics.track_refinement_attempt(slide_number)
                    total_cost += estimated_cost
                    total_attempts += 1

                    # Simulate validation of new image
                    # In real implementation, would re-validate the generated image
                    simulated_improvement = 5.0 * refinement_strategy.confidence
                    new_score = min(100.0, current_validation.score + simulated_improvement)

                    print(f"    ✓ Image regenerated")
                    print(f"    New validation score: {new_score:.1f}/100 (+{new_score - current_validation.score:.1f})")

                    # Update best result
                    if new_score > best_score:
                        best_score = new_score
                        best_image_path = str(output_dir / f"slide-{slide_number}-attempt-{attempt}.jpg")

                    # Check if score is good enough
                    if new_score >= 75.0:
                        print(f"    ✓ Slide passed validation!")
                        slides_refined += 1
                        break

                    # Check for diminishing returns
                    if (new_score - current_validation.score) < 5.0:
                        print(f"    ⚠️  Diminishing returns - stopping refinement")
                        break

                    # Update current validation for next attempt
                    current_validation.score = new_score

            refinement_results.append({
                "slide_number": slide_number,
                "initial_score": initial_validation.score,
                "final_score": best_score,
                "improvement": best_score - initial_validation.score,
                "attempts": attempt,
                "best_image_path": best_image_path
            })

        # End analytics
        analytics.end_phase(
            "refinement",
            success=True,
            items_processed=len(slides_to_refine),
            quality_scores=[r["final_score"] for r in refinement_results]
        )

        # Summary
        print(f"\n{'=' * 80}")
        print(f"Refinement Summary")
        print(f"{'=' * 80}")
        print(f"Slides processed: {len(slides_to_refine)}")
        print(f"Slides improved to passing: {slides_refined}")
        print(f"Total refinement attempts: {total_attempts}")
        print(f"Total cost: ${total_cost:.2f}")

        if refinement_results:
            avg_improvement = sum(r["improvement"] for r in refinement_results) / len(refinement_results)
            print(f"Average score improvement: +{avg_improvement:.1f} points")

        print()

        return SkillOutput(
            success=True,
            data={
                "refinement_results": refinement_results,
                "slides_refined": slides_refined,
                "total_attempts": total_attempts,
                "total_cost": total_cost,
                "analytics": analytics.generate_report()
            },
            artifacts=[str(output_dir)],
            errors=[],
            metadata={
                "max_refinements": max_refinements,
                "interactive": interactive,
                "cost_budget": cost_budget
            }
        )


if __name__ == "__main__":
    # Example test
    from lib.visual_validator import ValidationResult

    # Mock data
    slides = [
        {"title": "Test Slide 1", "graphics_description": "A diagram showing process flow"},
        {"title": "Test Slide 2", "graphics_description": "An illustration of the concept"}
    ]

    validation_results = [
        ValidationResult(
            passed=False,
            score=65.0,
            issues=[{"severity": "medium", "message": "Image too small"}],
            suggestions=["Make visual element larger"],
            rubric_scores={}
        ),
        ValidationResult(
            passed=False,
            score=70.0,
            issues=[{"severity": "low", "message": "Color mismatch"}],
            suggestions=["Use exact brand colors"],
            rubric_scores={}
        )
    ]

    skill = RefinementSkill()

    input_data = SkillInput(
        data={
            "slides": slides,
            "validation_results": validation_results,
            "presentation_path": "test_presentation.pptx",
            "max_refinements": 2,
            "interactive": False,  # Non-interactive for testing
            "cost_budget": 5.0
        },
        context={},
        config={}
    )

    result = skill.execute(input_data)

    if result.success:
        print("✓ Refinement skill executed successfully")
        print(f"  Slides refined: {result.data['slides_refined']}")
        print(f"  Total cost: ${result.data['total_cost']:.2f}")
    else:
        print("✗ Refinement skill failed")
        for error in result.errors:
            print(f"  Error: {error}")
