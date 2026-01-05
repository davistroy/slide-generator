"""
Build presentation command implementation.

Builds PowerPoint presentation from markdown and images.
"""

from typing import Dict, Any
from pathlib import Path

from plugin.skills import PowerPointAssemblySkill
from plugin.base_skill import SkillInput


def execute(args) -> Dict[str, Any]:
    """
    Execute build-presentation command.

    Args:
        args: Command-line arguments containing:
            - markdown_file: Path to markdown presentation
            - template: Template ID (cfa, stratfield)
            - output: Output filename (optional)
            - output_dir: Output directory (optional)
            - skip_images: Skip image generation flag
            - fast: Use standard resolution flag
            - enable_validation: Enable visual validation flag

    Returns:
        Build results with output_path and metadata
    """
    skill = PowerPointAssemblySkill()

    # Build input data
    input_data = {
        "markdown_path": args.markdown_file,
        "template": getattr(args, "template", "cfa"),
        "skip_images": getattr(args, "skip_images", False),
        "fast_mode": getattr(args, "fast", False),
        "enable_validation": getattr(args, "enable_validation", False),
    }

    # Optional parameters
    if hasattr(args, "output") and args.output:
        input_data["output_name"] = args.output
    if hasattr(args, "output_dir") and args.output_dir:
        input_data["output_dir"] = args.output_dir

    # Execute skill
    result = skill.execute(SkillInput(data=input_data))

    if result.success:
        return {
            "success": True,
            "output_path": result.artifacts[0] if result.artifacts else None,
            "slide_count": result.data.get("slide_count"),
            "images_generated": result.data.get("images_generated"),
            "template": result.data.get("template"),
        }
    else:
        return {
            "success": False,
            "errors": result.errors,
        }
