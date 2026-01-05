"""
Content Drafting Skill - AI-assisted presentation content generation.

Transforms presentation outlines into complete slide content with:
- Titles and subtitles
- Bullet points (properly structured)
- Detailed graphics descriptions
- Speaker notes with full narration
- Citations

Outputs markdown files following pres-template.md format.
"""

import os
from typing import Any

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput
from plugin.lib.content_generator import ContentGenerator


class ContentDraftingSkill(BaseSkill):
    """
    Generate complete slide content from presentation outlines.

    Uses AI-assisted content generation to create:
    - Engaging titles
    - Concise bullet points
    - Detailed graphics descriptions for image generation
    - Full speaker notes with narration and stage directions
    - Properly formatted citations

    Input: Outline from OutlineSkill + Research data
    Output: Complete presentation markdown file(s)
    """

    @property
    def skill_id(self) -> str:
        return "draft-content"

    @property
    def display_name(self) -> str:
        return "Content Drafting"

    @property
    def description(self) -> str:
        return "AI-assisted drafting of presentation slide content from outlines"

    def validate_input(self, input: SkillInput) -> bool:
        """
        Validate input has required data.

        Required:
        - outline: Output from OutlineSkill with presentations and slides
        """
        if "outline" not in input.data:
            return False

        outline = input.data["outline"]

        # Check outline structure
        if "presentations" not in outline:
            return False

        if not isinstance(outline["presentations"], list):
            return False

        if len(outline["presentations"]) == 0:
            return False

        # Check first presentation has slides
        first_pres = outline["presentations"][0]
        return "slides" in first_pres

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Execute content drafting for all presentations in outline.

        Args:
            input: SkillInput with:
                - outline: OutlineSkill output (required)
                - research: ResearchSkill output (optional, for context)
                - style_guide: Style parameters (optional)
                - style_config: Brand style config (optional, for graphics)
                - output_dir: Output directory (optional, default: ./output)

        Returns:
            SkillOutput with:
                - presentation_files: List of markdown file paths created
                - presentations: List of presentation data with generated content
                - slides_generated: Total number of slides
        """
        # Extract input data
        outline = input.data["outline"]
        research = input.data.get("research")
        style_guide = input.data.get("style_guide")
        style_config = input.data.get("style_config")
        output_dir = input.data.get("output_dir", "./output")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Initialize content generator
        generator = ContentGenerator(style_guide=style_guide)

        # Process each presentation
        presentation_files = []
        presentations_data = []
        total_slides = 0

        for pres_idx, presentation in enumerate(outline["presentations"]):
            # Generate content for this presentation
            result = self._generate_presentation_content(
                presentation=presentation,
                presentation_index=pres_idx,
                generator=generator,
                research_context=research,
                style_config=style_config,
                output_dir=output_dir,
            )

            presentation_files.append(result["file_path"])
            presentations_data.append(result["presentation_data"])
            total_slides += result["slides_count"]

        return SkillOutput(
            success=True,
            data={
                "presentation_files": presentation_files,
                "presentations": presentations_data,
                "slides_generated": total_slides,
            },
            artifacts=presentation_files,
            errors=[],
            metadata={
                "presentation_count": len(presentation_files),
                "total_slides": total_slides,
            },
        )

    def _generate_presentation_content(
        self,
        presentation: dict[str, Any],
        presentation_index: int,
        generator: ContentGenerator,
        research_context: dict[str, Any],
        style_config: dict[str, Any],
        output_dir: str,
    ) -> dict[str, Any]:
        """
        Generate content for a single presentation.

        Args:
            presentation: Presentation outline data
            presentation_index: Index of this presentation
            generator: ContentGenerator instance
            research_context: Research data for context
            style_config: Brand style configuration
            output_dir: Output directory

        Returns:
            Dictionary with file_path, presentation_data, slides_count
        """
        title = presentation.get("title", f"Presentation {presentation_index + 1}")
        audience = presentation.get("audience", "general")
        slides = presentation.get("slides", [])

        print(f"\nGenerating content for: {title}")
        print(f"Audience: {audience}")
        print(f"Slides: {len(slides)}")

        # Generate content for each slide
        generated_slides = []

        for slide_idx, slide in enumerate(slides, 1):
            print(
                f"  Generating slide {slide_idx}/{len(slides)}: {slide.get('title', 'Untitled')}..."
            )

            # Generate all content for this slide
            slide_content = generator.generate_slide_content(
                slide=slide,
                slide_number=slide_idx,
                research_context=research_context,
                style_config=style_config,
            )

            # Add slide outline data to content
            slide_content["outline"] = slide
            generated_slides.append(slide_content)

        # Create markdown file
        markdown_filename = self._sanitize_filename(title) + ".md"
        file_path = os.path.join(output_dir, markdown_filename)

        # Build complete markdown document
        markdown_content = self._build_markdown_document(
            title=title,
            audience=audience,
            slides=generated_slides,
            presentation=presentation,
        )

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"  Saved to: {file_path}")

        return {
            "file_path": file_path,
            "presentation_data": {
                "title": title,
                "audience": audience,
                "slides": generated_slides,
                "estimated_duration": presentation.get("estimated_duration"),
            },
            "slides_count": len(generated_slides),
        }

    def _build_markdown_document(
        self,
        title: str,
        audience: str,
        slides: list[dict[str, Any]],
        presentation: dict[str, Any],
    ) -> str:
        """
        Build complete markdown document from generated slides.

        Args:
            title: Presentation title
            audience: Target audience
            slides: List of generated slide content
            presentation: Original presentation outline

        Returns:
            Complete markdown document string
        """
        # Frontmatter
        markdown = "---\n"
        markdown += f"title: {title}\n"
        markdown += f"audience: {audience}\n"
        markdown += f"slides: {len(slides)}\n"
        estimated_duration = presentation.get("estimated_duration")
        if estimated_duration:
            markdown += f"duration: {estimated_duration} minutes\n"
        markdown += "---\n\n"

        # Presentation header
        markdown += f"# {title}\n\n"

        subtitle = presentation.get("subtitle")
        if subtitle:
            markdown += f"**{subtitle}**\n\n"

        markdown += f"**Target Audience:** {audience}\n\n"
        markdown += f"**Slides:** {len(slides)}\n\n"

        if estimated_duration:
            markdown += f"**Estimated Duration:** {estimated_duration} minutes\n\n"

        markdown += "---\n\n"

        # Add each slide
        for slide in slides:
            markdown += slide["markdown"]

        return markdown

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        # Replace spaces with underscores
        filename = filename.replace(" ", "_")

        # Limit length
        max_length = 100
        if len(filename) > max_length:
            filename = filename[:max_length]

        # Remove leading/trailing underscores
        filename = filename.strip("_")

        return filename.lower()


# Convenience function
def get_content_drafting_skill() -> ContentDraftingSkill:
    """Get configured content drafting skill instance."""
    return ContentDraftingSkill()
