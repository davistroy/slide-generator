"""
Content Optimization Skill - AI-assisted content quality improvement.

Analyzes and optimizes presentation content for:
- Readability (Flesch-Kincaid analysis)
- Tone consistency
- Bullet point parallelism
- Redundancy removal
- Citation completeness
- Graphics description clarity

Outputs improved presentation with detailed improvement log.
"""

import os
from typing import Any

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput, SkillStatus
from plugin.lib.claude_client import get_claude_client
from plugin.lib.quality_analyzer import QualityAnalyzer


class ContentOptimizationSkill(BaseSkill):
    """
    Optimize presentation content through AI analysis and improvement.

    Uses quality metrics and Claude API to:
    - Identify quality issues
    - Generate improved content
    - Track improvements made
    - Provide quality scores before/after
    """

    @property
    def skill_id(self) -> str:
        return "optimize-content"

    @property
    def display_name(self) -> str:
        return "Content Optimization"

    @property
    def description(self) -> str:
        return (
            "AI-assisted optimization of presentation content for quality and clarity"
        )

    def validate_input(self, input: SkillInput) -> bool:
        """
        Validate input has required data.

        Required:
        - Either 'slides' (list of slide data) or 'presentation_file' (path to markdown)
        """
        has_slides = "slides" in input.data
        has_file = "presentation_file" in input.data

        return has_slides or has_file

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Execute content optimization.

        Args:
            input: SkillInput with:
                - slides: List of slide content (OR)
                - presentation_file: Path to markdown file
                - style_guide: Style parameters (optional)
                - optimization_goals: List of focus areas (optional)
                - output_file: Output path (optional)

        Returns:
            SkillOutput with:
                - optimized_file: Path to optimized presentation
                - improvements: List of improvements made
                - quality_score_before: Score before optimization
                - quality_score_after: Score after optimization
        """
        # Load slides
        if "slides" in input.data:
            slides = input.data["slides"]
            input_file = input.data.get("presentation_file", "presentation.md")
        else:
            input_file = input.data["presentation_file"]
            slides = self._load_slides_from_file(input_file)

        style_guide = input.data.get("style_guide", {})
        optimization_goals = input.data.get(
            "optimization_goals",
            ["readability", "tone", "parallelism", "redundancy", "citations"],
        )
        output_file = input.data.get("output_file")

        if not output_file:
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"{base_name}_optimized.md"

        print(f"\nOptimizing presentation: {input_file}")
        print(f"Slides to optimize: {len(slides)}")
        print(f"Focus areas: {', '.join(optimization_goals)}")

        # Initialize analyzer and client
        analyzer = QualityAnalyzer()
        client = get_claude_client()

        # Analyze current quality
        print("\nAnalyzing current quality...")
        initial_analysis = analyzer.analyze_presentation(slides, style_guide)

        print(f"  Initial quality score: {initial_analysis['overall_score']:.1f}/100")
        print(f"  Issues found: {len(initial_analysis['issues'])}")

        # Optimize slides
        print("\nOptimizing slides...")
        optimized_slides, improvements = self._optimize_slides(
            slides=slides,
            analysis=initial_analysis,
            optimization_goals=optimization_goals,
            style_guide=style_guide,
            client=client,
        )

        print(f"  Improvements made: {len(improvements)}")

        # Analyze optimized quality
        print("\nAnalyzing optimized quality...")
        final_analysis = analyzer.analyze_presentation(optimized_slides, style_guide)

        print(f"  Final quality score: {final_analysis['overall_score']:.1f}/100")
        print(
            f"  Improvement: +{final_analysis['overall_score'] - initial_analysis['overall_score']:.1f} points"
        )

        # Save optimized presentation
        self._save_optimized_presentation(
            slides=optimized_slides,
            output_file=output_file,
            improvements=improvements,
            initial_score=initial_analysis["overall_score"],
            final_score=final_analysis["overall_score"],
        )

        print(f"\nSaved optimized presentation: {output_file}")

        return SkillOutput(
            success=True,
            status=SkillStatus.SUCCESS,
            data={
                "optimized_file": output_file,
                "improvements": improvements,
                "quality_score_before": initial_analysis["overall_score"],
                "quality_score_after": final_analysis["overall_score"],
                "quality_improvement": final_analysis["overall_score"]
                - initial_analysis["overall_score"],
                "initial_analysis": initial_analysis,
                "final_analysis": final_analysis,
            },
            artifacts=[output_file],
            errors=[],
            metadata={
                "slides_optimized": len(optimized_slides),
                "improvements_count": len(improvements),
            },
        )

    def _load_slides_from_file(self, file_path: str) -> list[dict[str, Any]]:
        """
        Load slides from markdown file.

        This is a simplified parser - in production, use proper markdown parser.
        """
        # For now, return empty list - full implementation would parse markdown
        # In real usage, slides would be passed from ContentDraftingSkill
        return []

    def _optimize_slides(
        self,
        slides: list[dict[str, Any]],
        analysis: dict[str, Any],
        optimization_goals: list[str],
        style_guide: dict[str, Any],
        client: Any,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Optimize slides based on quality analysis.

        Args:
            slides: Original slides
            analysis: Quality analysis results
            optimization_goals: Focus areas
            style_guide: Style parameters
            client: Claude client

        Returns:
            (optimized_slides, improvements_log)
        """
        optimized_slides = []
        improvements = []

        for slide_idx, slide in enumerate(slides):
            # Find issues for this slide
            slide_issues = [
                issue
                for issue in analysis["issues"]
                if issue.get("slide_number") == slide_idx + 1
            ]

            if not slide_issues:
                # No issues - keep slide as is
                optimized_slides.append(slide)
                continue

            # Optimize slide
            optimized_slide, slide_improvements = self._optimize_slide(
                slide=slide,
                slide_number=slide_idx + 1,
                issues=slide_issues,
                optimization_goals=optimization_goals,
                style_guide=style_guide,
                client=client,
            )

            optimized_slides.append(optimized_slide)
            improvements.extend(slide_improvements)

        return optimized_slides, improvements

    def _optimize_slide(
        self,
        slide: dict[str, Any],
        slide_number: int,
        issues: list[dict[str, Any]],
        optimization_goals: list[str],
        style_guide: dict[str, Any],
        client: Any,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """
        Optimize a single slide.

        Args:
            slide: Slide content
            slide_number: Slide number
            issues: Issues found for this slide
            optimization_goals: Focus areas
            style_guide: Style parameters
            client: Claude client

        Returns:
            (optimized_slide, improvements_made)
        """
        improvements = []
        optimized_slide = slide.copy()

        # Optimize bullets
        if "bullets" in slide and len(slide["bullets"]) > 0:
            bullet_issues = [
                i for i in issues if i["type"] in ["structure", "readability"]
            ]

            if bullet_issues:
                improved_bullets, bullet_improvements = self._optimize_bullets(
                    bullets=slide["bullets"],
                    issues=bullet_issues,
                    style_guide=style_guide,
                    client=client,
                )

                if improved_bullets:
                    optimized_slide["bullets"] = improved_bullets
                    for imp in bullet_improvements:
                        imp["slide_number"] = slide_number
                        improvements.append(imp)

        # Optimize graphics description if clarity issues
        if "graphics_description" in slide:
            graphics_issues = [
                i for i in issues if "graphics" in i.get("message", "").lower()
            ]

            if graphics_issues or "graphics" in optimization_goals:
                improved_graphics, graphics_improvement = (
                    self._optimize_graphics_description(
                        description=slide["graphics_description"],
                        title=slide.get("title", ""),
                        issues=graphics_issues,
                        client=client,
                    )
                )

                if (
                    improved_graphics
                    and improved_graphics != slide["graphics_description"]
                ):
                    optimized_slide["graphics_description"] = improved_graphics
                    graphics_improvement["slide_number"] = slide_number
                    improvements.append(graphics_improvement)

        return optimized_slide, improvements

    def _optimize_bullets(
        self,
        bullets: list[str],
        issues: list[dict[str, Any]],
        style_guide: dict[str, Any],
        client: Any,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """
        Optimize bullet points.

        Args:
            bullets: Original bullets
            issues: Issues found
            style_guide: Style parameters
            client: Claude client

        Returns:
            (improved_bullets, improvements_log)
        """
        # Build optimization prompt
        issue_descriptions = "\n".join([f"- {i['message']}" for i in issues])

        max_words = style_guide.get("max_words_per_bullet", 15)
        tone = style_guide.get("tone", "professional")

        prompt = f"""Improve these bullet points:

Original bullets:
{chr(10).join(f"{i + 1}. {b}" for i, b in enumerate(bullets))}

Issues to fix:
{issue_descriptions}

Requirements:
- Maintain parallel grammatical structure
- Maximum {max_words} words per bullet
- {tone.capitalize()} tone
- Clear and specific (not vague)
- Active voice preferred

Return ONLY the improved bullets as a numbered list."""

        system_prompt = """You are an expert presentation writer improving bullet points.
Return only the improved bullets, numbered 1-N."""

        try:
            response = client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=500,
            )

            # Parse improved bullets
            improved_bullets = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    # Remove numbering
                    bullet_text = line.split(".", 1)[1].strip() if "." in line else line
                    improved_bullets.append(bullet_text)

            if len(improved_bullets) != len(bullets):
                # Parsing failed - return originals
                return bullets, []

            # Log improvements
            improvements = []
            for _i, (original, improved) in enumerate(
                zip(bullets, improved_bullets, strict=False)
            ):
                if original != improved:
                    improvements.append(
                        {
                            "issue_type": "bullet_improvement",
                            "original": original,
                            "improved": improved,
                            "reasoning": f"Fixed: {issues[0]['type'] if issues else 'quality'}",
                        }
                    )

            return improved_bullets, improvements

        except Exception:
            # If optimization fails, return originals
            return bullets, []

    def _optimize_graphics_description(
        self, description: str, title: str, issues: list[dict[str, Any]], client: Any
    ) -> tuple[str, dict[str, Any]]:
        """
        Optimize graphics description.

        Args:
            description: Original description
            title: Slide title for context
            issues: Issues found
            client: Claude client

        Returns:
            (improved_description, improvement_log)
        """
        prompt = f"""Improve this graphics description for a presentation slide.

Slide title: {title}

Current description:
{description}

Requirements:
- SPECIFIC visual elements (not vague concepts)
- 3-5 sentences with concrete details
- Mention composition/layout
- NO TEXT in the image
- Describe what to actually draw/show

Return ONLY the improved description."""

        system_prompt = """You are an expert at creating detailed visual descriptions for AI image generation."""

        try:
            improved = client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=500,
            )

            improvement = {
                "issue_type": "graphics_clarity",
                "original": description[:100] + "..."
                if len(description) > 100
                else description,
                "improved": improved[:100] + "..." if len(improved) > 100 else improved,
                "reasoning": "Enhanced specificity and visual detail",
            }

            return improved.strip(), improvement

        except Exception:
            return description, {}

    def _save_optimized_presentation(
        self,
        slides: list[dict[str, Any]],
        output_file: str,
        improvements: list[dict[str, Any]],
        initial_score: float,
        final_score: float,
    ) -> None:
        """
        Save optimized presentation to markdown file.

        Args:
            slides: Optimized slides
            output_file: Output file path
            improvements: List of improvements made
            initial_score: Quality score before optimization
            final_score: Quality score after optimization
        """
        markdown = f"""---
optimized: true
quality_score_before: {initial_score:.1f}
quality_score_after: {final_score:.1f}
improvements: {len(improvements)}
---

# Optimized Presentation

**Quality Improvement:** {final_score - initial_score:+.1f} points ({initial_score:.1f} → {final_score:.1f})

**Improvements Made:** {len(improvements)}

---

"""

        # Add each slide's markdown
        for slide in slides:
            if "markdown" in slide:
                markdown += slide["markdown"]
            else:
                # Rebuild markdown if not present
                markdown += self._rebuild_slide_markdown(slide)

        # Write file
        os.makedirs(
            os.path.dirname(output_file) if os.path.dirname(output_file) else ".",
            exist_ok=True,
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown)

    def _rebuild_slide_markdown(self, slide: dict[str, Any]) -> str:
        """Rebuild markdown for a slide (simplified)."""
        markdown = f"## Slide: {slide.get('title', 'Untitled')}\n\n"

        bullets = slide.get("bullets", [])
        if bullets:
            markdown += "**Content:**\n\n"
            for bullet in bullets:
                markdown += f"- {bullet}\n"
            markdown += "\n"

        markdown += "---\n\n"
        return markdown


# Convenience function
def get_content_optimization_skill() -> ContentOptimizationSkill:
    """Get configured content optimization skill instance."""
    return ContentOptimizationSkill()
