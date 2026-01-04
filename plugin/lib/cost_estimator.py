"""
Cost Estimator for API Usage

Estimates costs for Claude and Gemini API calls based on current pricing.
Used for budget tracking and cost estimation before workflow execution.

Pricing (as of January 2026):
- Claude Sonnet 4.5: $3.00/MTok input, $15.00/MTok output
- Gemini Pro Vision: $0.075/image (standard), $0.30/image (4K)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


# API Pricing Constants (per million tokens or per image)
CLAUDE_PRICING = {
    "claude-sonnet-4-5": {
        "input": 3.00,   # $ per million tokens
        "output": 15.00  # $ per million tokens
    },
    "claude-opus-4": {
        "input": 15.00,
        "output": 75.00
    },
    "claude-haiku-3-5": {
        "input": 0.25,
        "output": 1.25
    }
}

GEMINI_PRICING = {
    "gemini-3-pro-image-preview": {
        "standard": 0.075,  # $ per image
        "4K": 0.30          # $ per high-res image
    }
}


@dataclass
class CostEstimate:
    """Estimated cost breakdown for API usage."""

    api_name: str
    operation: str
    estimated_calls: int
    unit_cost: float
    total_cost: float
    details: Dict[str, Any]


class CostEstimator:
    """
    Estimates costs for API usage across the presentation generation workflow.

    Usage:
        estimator = CostEstimator()

        # Estimate Claude API costs
        cost = estimator.estimate_claude_cost(
            input_tokens=5000,
            output_tokens=2000,
            model="claude-sonnet-4-5"
        )

        # Estimate Gemini image generation costs
        cost = estimator.estimate_gemini_cost(
            image_count=20,
            resolution="4K"
        )

        # Estimate full workflow
        workflow_cost = estimator.estimate_workflow_cost(
            num_slides=20,
            enable_validation=True,
            enable_refinement=True
        )
    """

    def __init__(self):
        """Initialize cost estimator with current pricing."""
        self.claude_pricing = CLAUDE_PRICING
        self.gemini_pricing = GEMINI_PRICING

    def estimate_claude_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-sonnet-4-5"
    ) -> CostEstimate:
        """
        Estimate cost for Claude API calls.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Claude model name

        Returns:
            CostEstimate with breakdown
        """
        if model not in self.claude_pricing:
            raise ValueError(f"Unknown Claude model: {model}")

        pricing = self.claude_pricing[model]

        # Convert tokens to millions
        input_millions = input_tokens / 1_000_000
        output_millions = output_tokens / 1_000_000

        # Calculate costs
        input_cost = input_millions * pricing["input"]
        output_cost = output_millions * pricing["output"]
        total_cost = input_cost + output_cost

        return CostEstimate(
            api_name="Claude",
            operation=model,
            estimated_calls=1,
            unit_cost=total_cost,
            total_cost=total_cost,
            details={
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4)
            }
        )

    def estimate_gemini_cost(
        self,
        image_count: int,
        resolution: str = "4K"
    ) -> CostEstimate:
        """
        Estimate cost for Gemini image generation.

        Args:
            image_count: Number of images to generate
            resolution: "standard" or "4K"

        Returns:
            CostEstimate with breakdown
        """
        pricing = self.gemini_pricing["gemini-3-pro-image-preview"]

        if resolution not in pricing:
            raise ValueError(f"Unknown resolution: {resolution}. Use 'standard' or '4K'")

        unit_cost = pricing[resolution]
        total_cost = image_count * unit_cost

        return CostEstimate(
            api_name="Gemini",
            operation="image_generation",
            estimated_calls=image_count,
            unit_cost=unit_cost,
            total_cost=total_cost,
            details={
                "resolution": resolution,
                "image_count": image_count,
                "unit_cost": unit_cost
            }
        )

    def estimate_workflow_cost(
        self,
        num_slides: int = 20,
        enable_research: bool = True,
        enable_optimization: bool = True,
        enable_validation: bool = False,
        enable_refinement: bool = False,
        max_refinements_per_slide: int = 3
    ) -> Dict[str, Any]:
        """
        Estimate total cost for complete workflow.

        Args:
            num_slides: Number of slides in presentation
            enable_research: Include research phase costs
            enable_optimization: Include optimization phase costs
            enable_validation: Include visual validation costs
            enable_refinement: Include refinement costs
            max_refinements_per_slide: Max refinement attempts per slide

        Returns:
            Cost breakdown by phase
        """
        estimates = []

        # Phase 1: Research (if enabled)
        if enable_research:
            # Estimate: ~10 sources, 5K input + 3K output per source = 80K tokens
            research_cost = self.estimate_claude_cost(
                input_tokens=50_000,
                output_tokens=30_000,
                model="claude-sonnet-4-5"
            )
            estimates.append(("Research", research_cost))

        # Phase 2: Insight Extraction (if research enabled)
        if enable_research:
            # Estimate: 20K input + 10K output
            insights_cost = self.estimate_claude_cost(
                input_tokens=20_000,
                output_tokens=10_000,
                model="claude-sonnet-4-5"
            )
            estimates.append(("Insight Extraction", insights_cost))

        # Phase 3: Outline Generation
        outline_cost = self.estimate_claude_cost(
            input_tokens=15_000,
            output_tokens=5_000,
            model="claude-sonnet-4-5"
        )
        estimates.append(("Outline Generation", outline_cost))

        # Phase 4: Content Drafting (per slide: 2K input + 1K output)
        drafting_cost = self.estimate_claude_cost(
            input_tokens=2_000 * num_slides,
            output_tokens=1_000 * num_slides,
            model="claude-sonnet-4-5"
        )
        estimates.append(("Content Drafting", drafting_cost))

        # Phase 5: Content Optimization (if enabled)
        if enable_optimization:
            # Estimate: 3K input + 1.5K output per slide
            optimization_cost = self.estimate_claude_cost(
                input_tokens=3_000 * num_slides,
                output_tokens=1_500 * num_slides,
                model="claude-sonnet-4-5"
            )
            estimates.append(("Content Optimization", optimization_cost))

        # Phase 6: Graphics Validation
        # Estimate: 1K input + 500 output per slide (for AI validation)
        graphics_validation_cost = self.estimate_claude_cost(
            input_tokens=1_000 * num_slides,
            output_tokens=500 * num_slides,
            model="claude-sonnet-4-5"
        )
        estimates.append(("Graphics Validation", graphics_validation_cost))

        # Phase 7: Image Generation (4K by default)
        image_cost = self.estimate_gemini_cost(
            image_count=num_slides,
            resolution="4K"
        )
        estimates.append(("Image Generation", image_cost))

        # Phase 8: Visual Validation (if enabled)
        if enable_validation:
            # Estimate: 2K input + 1K output per slide (Gemini vision analysis)
            # Using Claude pricing as proxy (Gemini vision costs TBD)
            validation_cost = self.estimate_claude_cost(
                input_tokens=2_000 * num_slides,
                output_tokens=1_000 * num_slides,
                model="claude-sonnet-4-5"
            )
            estimates.append(("Visual Validation", validation_cost))

        # Phase 9: Refinement (if enabled)
        if enable_refinement:
            # Estimate: 50% of slides need 1-2 refinements
            avg_refinements = num_slides * 0.5 * 1.5
            refinement_image_cost = self.estimate_gemini_cost(
                image_count=int(avg_refinements),
                resolution="4K"
            )
            estimates.append(("Image Refinement", refinement_image_cost))

        # Calculate totals
        total_cost = sum(est.total_cost for _, est in estimates)

        return {
            "total_cost": round(total_cost, 2),
            "breakdown": [
                {
                    "phase": phase,
                    "cost": round(est.total_cost, 2),
                    "details": est.details
                }
                for phase, est in estimates
            ],
            "configuration": {
                "num_slides": num_slides,
                "enable_research": enable_research,
                "enable_optimization": enable_optimization,
                "enable_validation": enable_validation,
                "enable_refinement": enable_refinement
            }
        }

    def format_cost_report(self, workflow_cost: Dict[str, Any]) -> str:
        """
        Format workflow cost estimate as human-readable report.

        Args:
            workflow_cost: Output from estimate_workflow_cost()

        Returns:
            Formatted cost report string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("WORKFLOW COST ESTIMATE")
        lines.append("=" * 70)
        lines.append("")

        # Configuration
        config = workflow_cost["configuration"]
        lines.append("Configuration:")
        lines.append(f"  Slides: {config['num_slides']}")
        lines.append(f"  Research: {'Yes' if config['enable_research'] else 'No'}")
        lines.append(f"  Optimization: {'Yes' if config['enable_optimization'] else 'No'}")
        lines.append(f"  Validation: {'Yes' if config['enable_validation'] else 'No'}")
        lines.append(f"  Refinement: {'Yes' if config['enable_refinement'] else 'No'}")
        lines.append("")

        # Breakdown
        lines.append("Cost Breakdown by Phase:")
        lines.append("-" * 70)

        for item in workflow_cost["breakdown"]:
            phase = item["phase"]
            cost = item["cost"]
            lines.append(f"  {phase:.<50} ${cost:>6.2f}")

        lines.append("-" * 70)
        lines.append(f"  {'TOTAL':.<50} ${workflow_cost['total_cost']:>6.2f}")
        lines.append("=" * 70)

        return "\n".join(lines)


def estimate_cost_for_presentation(
    num_slides: int,
    include_research: bool = True,
    include_optimization: bool = True
) -> float:
    """
    Quick cost estimate for a presentation.

    Args:
        num_slides: Number of slides
        include_research: Include research phase
        include_optimization: Include optimization phase

    Returns:
        Estimated total cost in dollars
    """
    estimator = CostEstimator()
    result = estimator.estimate_workflow_cost(
        num_slides=num_slides,
        enable_research=include_research,
        enable_optimization=include_optimization,
        enable_validation=False,
        enable_refinement=False
    )
    return result["total_cost"]


if __name__ == "__main__":
    # Example usage
    estimator = CostEstimator()

    print("Example 1: 20-slide presentation with full workflow")
    print("-" * 70)
    cost = estimator.estimate_workflow_cost(
        num_slides=20,
        enable_research=True,
        enable_optimization=True,
        enable_validation=True,
        enable_refinement=True
    )
    print(estimator.format_cost_report(cost))
    print()

    print("Example 2: 10-slide presentation (basic workflow)")
    print("-" * 70)
    cost = estimator.estimate_workflow_cost(
        num_slides=10,
        enable_research=False,
        enable_optimization=False,
        enable_validation=False,
        enable_refinement=False
    )
    print(estimator.format_cost_report(cost))
