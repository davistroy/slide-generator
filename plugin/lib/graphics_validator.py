"""
Graphics Description Validator - Ensure quality before image generation.

Validates graphics descriptions for:
- Specificity (concrete vs vague)
- Visual elements (what to actually draw)
- Brand alignment (mentions brand colors/style)
- Layout hints (composition, framing)
- Text avoidance (no text in images)
- Adequate length (2-4 sentences minimum)

Uses hybrid approach: rule-based validation + Claude API for improvements.
"""

import re
from dataclasses import dataclass
from typing import Any

from plugin.lib.claude_client import get_claude_client


@dataclass
class ValidationResult:
    """Result of graphics description validation."""

    passed: bool
    score: float  # 0-100
    issues: list[dict[str, Any]]
    suggestions: list[str]
    description_improved: str | None = None


class GraphicsValidator:
    """
    Validate and improve graphics descriptions.

    Ensures graphics descriptions are specific enough for quality image generation.
    """

    # Vague words that indicate lack of specificity
    VAGUE_WORDS = {
        "representing",
        "showing",
        "depicting",
        "illustrating",
        "concept",
        "idea",
        "notion",
        "theme",
        "abstract",
        "various",
        "some",
        "several",
        "many",
        "general",
    }

    # Visual element keywords (positive indicators)
    VISUAL_KEYWORDS = {
        "diagram",
        "illustration",
        "chart",
        "graph",
        "photo",
        "image",
        "cross-section",
        "cutaway",
        "close-up",
        "wide-angle",
        "arrows",
        "lines",
        "shapes",
        "colors",
        "gradient",
        "centered",
        "split-screen",
        "foreground",
        "background",
        "lighting",
        "shadow",
        "depth",
        "perspective",
        "angle",
    }

    # Layout/composition keywords
    LAYOUT_KEYWORDS = {
        "centered",
        "split-screen",
        "left-aligned",
        "right-aligned",
        "top-down",
        "side-view",
        "front-facing",
        "angled",
        "foreground",
        "background",
        "layered",
        "stacked",
        "horizontal",
        "vertical",
        "diagonal",
        "balanced",
    }

    # Text-indicating words (should trigger warnings)
    TEXT_INDICATORS = {
        "label",
        "labeled",
        "text",
        "caption",
        "title",
        "heading",
        "words",
        "letters",
        "font",
        "typography",
        "written",
    }

    def __init__(self):
        """Initialize graphics validator."""
        self.client = get_claude_client()

    def validate_description(
        self,
        description: str,
        slide_context: dict[str, Any] | None = None,
        style_config: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate a graphics description.

        Args:
            description: Graphics description to validate
            slide_context: Optional slide context (title, bullets)
            style_config: Optional brand style configuration

        Returns:
            ValidationResult with pass/fail, score, issues, and suggestions
        """
        issues = []
        score = 100.0

        # Rule 1: Length check (2-4 sentences minimum)
        length_issue, length_penalty = self._check_length(description)
        if length_issue:
            issues.append(length_issue)
            score -= length_penalty

        # Rule 2: Specificity check (avoid vague words)
        specificity_issue, specificity_penalty = self._check_specificity(description)
        if specificity_issue:
            issues.append(specificity_issue)
            score -= specificity_penalty

        # Rule 3: Visual elements check
        visual_issue, visual_penalty = self._check_visual_elements(description)
        if visual_issue:
            issues.append(visual_issue)
            score -= visual_penalty

        # Rule 4: Layout hints check
        layout_issue, layout_penalty = self._check_layout_hints(description)
        if layout_issue:
            issues.append(layout_issue)
            score -= layout_penalty

        # Rule 5: Text avoidance check
        text_issue, text_penalty = self._check_text_avoidance(description)
        if text_issue:
            issues.append(text_issue)
            score -= text_penalty

        # Rule 6: Brand alignment check (if style config provided)
        if style_config:
            brand_issue, brand_penalty = self._check_brand_alignment(
                description, style_config
            )
            if brand_issue:
                issues.append(brand_issue)
                score -= brand_penalty

        # Determine pass/fail (threshold: 75)
        passed = score >= 75

        # Generate suggestions
        suggestions = self._generate_suggestions(issues)

        # If failed, offer AI improvement
        improved_description = None
        if not passed and slide_context:
            improved_description = self._generate_improved_description(
                description, issues, slide_context, style_config
            )

        return ValidationResult(
            passed=passed,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
            description_improved=improved_description,
        )

    def _check_length(self, description: str) -> tuple[dict | None, float]:
        """
        Check description length (minimum 2-4 sentences).

        Returns:
            (issue_dict or None, penalty_score)
        """
        # Count sentences (approximate)
        sentences = [s.strip() for s in re.split(r"[.!?]+", description) if s.strip()]
        sentence_count = len(sentences)

        if sentence_count < 2:
            return {
                "type": "length",
                "severity": "high",
                "message": f"Description too short ({sentence_count} sentence). Minimum 2-4 sentences recommended.",
                "suggestion": "Add more specific visual details about composition, colors, and elements.",
            }, 30.0
        elif sentence_count == 2:
            return {
                "type": "length",
                "severity": "low",
                "message": "Description could be more detailed (2 sentences). 3-4 sentences ideal.",
                "suggestion": "Consider adding composition or color details.",
            }, 10.0

        return None, 0

    def _check_specificity(self, description: str) -> tuple[dict | None, float]:
        """
        Check for vague/abstract language.

        Returns:
            (issue_dict or None, penalty_score)
        """
        description_lower = description.lower()
        vague_found = [word for word in self.VAGUE_WORDS if word in description_lower]

        if len(vague_found) >= 3:
            return {
                "type": "specificity",
                "severity": "high",
                "message": f"Too many vague words: {', '.join(vague_found[:3])}",
                "suggestion": "Replace abstract concepts with concrete visual elements.",
            }, 25.0
        elif len(vague_found) >= 1:
            return {
                "type": "specificity",
                "severity": "medium",
                "message": f"Contains vague language: {', '.join(vague_found)}",
                "suggestion": "Be more specific about what to actually draw.",
            }, 15.0

        return None, 0

    def _check_visual_elements(self, description: str) -> tuple[dict | None, float]:
        """
        Check for concrete visual elements.

        Returns:
            (issue_dict or None, penalty_score)
        """
        description_lower = description.lower()
        visual_found = [
            word for word in self.VISUAL_KEYWORDS if word in description_lower
        ]

        if len(visual_found) == 0:
            return {
                "type": "visual_elements",
                "severity": "high",
                "message": "Missing specific visual element descriptions",
                "suggestion": "Describe what type of visual (diagram, illustration, etc.) and specific elements (shapes, arrows, etc.).",
            }, 30.0
        elif len(visual_found) == 1:
            return {
                "type": "visual_elements",
                "severity": "low",
                "message": "Limited visual element detail",
                "suggestion": "Add more visual element descriptions (colors, shapes, depth, etc.).",
            }, 10.0

        return None, 0

    def _check_layout_hints(self, description: str) -> tuple[dict | None, float]:
        """
        Check for composition/layout guidance.

        Returns:
            (issue_dict or None, penalty_score)
        """
        description_lower = description.lower()
        layout_found = [
            word for word in self.LAYOUT_KEYWORDS if word in description_lower
        ]

        if len(layout_found) == 0:
            return {
                "type": "layout",
                "severity": "medium",
                "message": "Missing layout/composition hints",
                "suggestion": "Specify composition (centered, split-screen, etc.) and perspective (top-down, angled, etc.).",
            }, 20.0

        return None, 0

    def _check_text_avoidance(self, description: str) -> tuple[dict | None, float]:
        """
        Check that description doesn't request text in image.

        Returns:
            (issue_dict or None, penalty_score)
        """
        description_lower = description.lower()
        text_found = [
            word for word in self.TEXT_INDICATORS if word in description_lower
        ]

        if len(text_found) > 0:
            return {
                "type": "text_in_image",
                "severity": "high",
                "message": f"May request text in image: {', '.join(text_found)}",
                "suggestion": "Remove text/labels from description. Text will be added in PowerPoint.",
            }, 25.0

        return None, 0

    def _check_brand_alignment(
        self, description: str, style_config: dict[str, Any]
    ) -> tuple[dict | None, float]:
        """
        Check for brand color/style mentions.

        Returns:
            (issue_dict or None, penalty_score)
        """
        brand_colors = style_config.get("brand_colors", [])

        if not brand_colors:
            return None, 0  # Can't check without brand colors

        description_lower = description.lower()

        # Check if any brand colors are mentioned
        colors_mentioned = any(
            color.lower().replace("#", "") in description_lower
            for color in brand_colors
        )

        # Also check for color names (red, blue, etc.)
        color_names = {
            "#DD0033": "red",
            "#004F71": "blue",
            "#000000": "black",
            "#FFFFFF": "white",
        }

        for hex_color, color_name in color_names.items():
            if hex_color in brand_colors and color_name in description_lower:
                colors_mentioned = True
                break

        if not colors_mentioned:
            return {
                "type": "brand_alignment",
                "severity": "low",
                "message": "No brand colors mentioned in description",
                "suggestion": f"Consider referencing brand colors: {', '.join(brand_colors[:2])}",
            }, 10.0

        return None, 0

    def _generate_suggestions(self, issues: list[dict[str, Any]]) -> list[str]:
        """Generate actionable suggestions from issues."""
        suggestions = []

        # Group by type
        issue_types = {issue["type"] for issue in issues}

        for issue_type in issue_types:
            relevant_issues = [i for i in issues if i["type"] == issue_type]
            if relevant_issues:
                suggestions.append(relevant_issues[0]["suggestion"])

        return suggestions

    def _generate_improved_description(
        self,
        description: str,
        issues: list[dict[str, Any]],
        slide_context: dict[str, Any],
        style_config: dict[str, Any] | None,
    ) -> str | None:
        """
        Generate improved description using Claude API.

        Args:
            description: Original description
            issues: Validation issues found
            slide_context: Slide title, bullets for context
            style_config: Brand style config

        Returns:
            Improved description or None if generation fails
        """
        title = slide_context.get("title", "")
        bullets = slide_context.get("bullets", [])

        # Build issue summary
        issue_summary = "\n".join([f"- {i['message']}" for i in issues])

        # Build brand context
        brand_context = ""
        if style_config:
            brand_colors = style_config.get("brand_colors", [])
            if brand_colors:
                brand_context = f"\nBrand colors: {', '.join(brand_colors)}"

        prompt = f"""Improve this graphics description for a presentation slide.

Slide Title: {title}
Key Points: {", ".join(bullets[:3]) if bullets else "N/A"}

Current Description:
{description}

Issues Found:
{issue_summary}
{brand_context}

Requirements:
- SPECIFIC visual elements (not vague concepts)
- 3-4 sentences with concrete details
- Mention composition/layout (centered, split-screen, etc.)
- Reference brand colors if applicable
- NO TEXT in the image (text added in PowerPoint)
- Describe what to actually draw/show
- Include visual style details (professional, clean, etc.)

Return ONLY the improved description, nothing else."""

        system_prompt = """You are an expert at creating detailed visual descriptions for AI image generation.
Focus on concrete, specific elements that can be drawn."""

        try:
            improved = self.client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=500,
            )

            return improved.strip()

        except Exception:
            return None

    def validate_and_improve(
        self,
        description: str,
        slide_context: dict[str, Any] | None = None,
        style_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate and automatically improve if needed.

        Convenience method that validates and returns improved version if validation fails.

        Args:
            description: Graphics description
            slide_context: Slide context
            style_config: Brand style config

        Returns:
            Dictionary with:
            - original: original description
            - validation: ValidationResult
            - improved: improved description (if validation failed)
            - final: final description to use (original if passed, improved if failed)
        """
        validation = self.validate_description(description, slide_context, style_config)

        if validation.passed:
            return {
                "original": description,
                "validation": validation,
                "improved": None,
                "final": description,
            }
        else:
            improved = validation.description_improved or description
            return {
                "original": description,
                "validation": validation,
                "improved": improved,
                "final": improved,
            }


# Convenience function
def get_graphics_validator() -> GraphicsValidator:
    """Get configured graphics validator instance."""
    return GraphicsValidator()


# Validation helper function
def validate_graphics_batch(
    slides: list[dict[str, Any]], style_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Validate graphics descriptions for multiple slides.

    Args:
        slides: List of slides with graphics_description
        style_config: Brand style config

    Returns:
        Batch validation results with pass rate and issues
    """
    validator = GraphicsValidator()

    results = []
    total_passed = 0

    for slide_idx, slide in enumerate(slides, 1):
        description = slide.get("graphics_description", "")

        if not description:
            continue

        slide_context = {
            "title": slide.get("title", ""),
            "bullets": slide.get("bullets", []),
        }

        validation = validator.validate_description(
            description, slide_context, style_config
        )

        if validation.passed:
            total_passed += 1

        results.append({"slide_number": slide_idx, "validation": validation})

    pass_rate = (total_passed / len(results) * 100) if results else 100

    return {
        "total_slides": len(results),
        "passed": total_passed,
        "failed": len(results) - total_passed,
        "pass_rate": round(pass_rate, 1),
        "results": results,
    }
