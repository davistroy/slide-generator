"""
PowerPoint Assembly Skill - Build PowerPoint presentations.

Assembles parsed slide data and generated images into a final
PowerPoint presentation using brand templates.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput, SkillStatus
from plugin.lib.presentation.assembler import assemble_presentation


class PowerPointAssemblySkill(BaseSkill):
    """
    Assemble PowerPoint presentations from markdown and images.

    Uses plugin.lib.presentation.assembler for PowerPoint generation.
    Supports multiple brand templates (cfa, stratfield).

    Input:
        - markdown_path: Path to the presentation markdown file
        - template: Template ID (e.g., 'cfa', 'stratfield')
        - output_name: Output filename (optional)
        - output_dir: Output directory (optional)
        - skip_images: Skip image generation (optional)
        - fast_mode: Use standard resolution (optional)
        - notext: Generate clean backgrounds without text (optional, default: True)
        - force_images: Regenerate existing images (optional)
        - enable_validation: Enable visual validation (optional, experimental)
        - max_refinement_attempts: Max refinement attempts (optional, default: 3)
        - validation_dpi: DPI for validation export (optional, default: 150)

    Output:
        - output_path: Path to generated .pptx file
        - slide_count: Number of slides generated
        - images_generated: Number of images generated
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "assemble-powerpoint"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "PowerPoint Assembly"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Assemble PowerPoint presentations from markdown with brand templates"

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """List of skill IDs this skill depends on."""
        return ["parse-markdown"]  # Depends on parsing skill

    def validate_input(self, input_data: SkillInput) -> Tuple[bool, List[str]]:
        """
        Validate required inputs.

        Args:
            input_data: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check markdown path
        markdown_path = input_data.get("markdown_path")
        if not markdown_path:
            errors.append("markdown_path is required")
        elif not Path(markdown_path).exists():
            errors.append(f"Markdown file not found: {markdown_path}")

        # Check template
        template = input_data.get("template", "cfa")
        valid_templates = ["cfa", "stratfield"]
        if template not in valid_templates:
            errors.append(f"Invalid template: {template}. Valid: {valid_templates}")

        return len(errors) == 0, errors

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute PowerPoint assembly.

        Args:
            input_data: Skill input with markdown path and options

        Returns:
            SkillOutput with path to generated presentation
        """
        # Extract all options from input
        markdown_path = input_data.get("markdown_path")
        template = input_data.get("template", "cfa")
        style_config_path = input_data.get("style_config_path")
        output_name = input_data.get("output_name")
        output_dir = input_data.get("output_dir")
        skip_images = input_data.get("skip_images", False)
        fast_mode = input_data.get("fast_mode", False)
        notext = input_data.get("notext", True)
        force_images = input_data.get("force_images", False)
        enable_validation = input_data.get("enable_validation", False)
        max_refinement_attempts = input_data.get("max_refinement_attempts", 3)
        validation_dpi = input_data.get("validation_dpi", 150)

        # Setup progress callback if provided in context
        progress_callback = input_data.get_context("progress_callback")

        try:
            print(f"\n[*] Assembling PowerPoint presentation...")
            print(f"   Template: {template}")
            print(f"   Markdown: {markdown_path}")

            # Call the assembler
            output_path = assemble_presentation(
                markdown_path=markdown_path,
                template_id=template,
                style_config_path=style_config_path,
                output_name=output_name,
                output_dir=output_dir,
                skip_images=skip_images,
                fast_mode=fast_mode,
                notext=notext,
                force_images=force_images,
                enable_validation=enable_validation,
                max_refinement_attempts=max_refinement_attempts,
                validation_dpi=validation_dpi,
                progress_callback=progress_callback
            )

            # Get metadata about the presentation
            output_path_obj = Path(output_path)

            # Count slides and images if possible
            slide_count = self._count_slides_in_markdown(markdown_path)
            images_count = self._count_images_in_directory(output_path_obj.parent / "images")

            print(f"\n[SUCCESS] PowerPoint generated: {output_path}")

            return SkillOutput.success_result(
                data={
                    "output_path": str(output_path),
                    "slide_count": slide_count,
                    "images_generated": images_count,
                    "template": template,
                    "validation_enabled": enable_validation
                },
                artifacts=[str(output_path)],
                metadata={
                    "output_path": str(output_path),
                    "markdown_path": markdown_path,
                    "template": template,
                    "slide_count": slide_count,
                    "images_generated": images_count,
                    "fast_mode": fast_mode,
                    "validation_enabled": enable_validation
                }
            )

        except FileNotFoundError as e:
            return SkillOutput.failure_result(
                errors=[f"File not found: {str(e)}"],
                metadata={
                    "markdown_path": markdown_path,
                    "template": template
                }
            )
        except ValueError as e:
            return SkillOutput.failure_result(
                errors=[f"Invalid input: {str(e)}"],
                metadata={
                    "markdown_path": markdown_path,
                    "template": template
                }
            )
        except Exception as e:
            return SkillOutput.failure_result(
                errors=[f"Failed to assemble presentation: {str(e)}"],
                metadata={
                    "markdown_path": markdown_path,
                    "template": template,
                    "exception_type": type(e).__name__
                }
            )

    def _count_slides_in_markdown(self, markdown_path: str) -> int:
        """
        Count number of slides in markdown file.

        Args:
            markdown_path: Path to markdown file

        Returns:
            Number of slides found
        """
        try:
            import re
            content = Path(markdown_path).read_text(encoding='utf-8')
            # Count slide headers: ## **SLIDE N:
            slide_pattern = re.compile(
                r'^#{2,3}\s+\*{0,2}SLIDE\s+(\d+)',
                re.MULTILINE | re.IGNORECASE
            )
            matches = slide_pattern.findall(content)
            return len(matches)
        except Exception:
            return 0

    def _count_images_in_directory(self, images_dir: Path) -> int:
        """
        Count number of images in the images directory.

        Args:
            images_dir: Path to images directory

        Returns:
            Number of image files found
        """
        if not images_dir.exists():
            return 0

        try:
            # Count .jpg files matching slide-*.jpg pattern
            image_files = list(images_dir.glob("slide-*.jpg"))
            return len(image_files)
        except Exception:
            return 0
