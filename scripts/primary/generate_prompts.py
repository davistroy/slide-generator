#!/usr/bin/env python3
"""
Generate image prompts for any resolution using config-driven templates.

Supports high/medium/small resolutions with customizable composition rules.

This script uses the official lib.parser module to parse presentations,
eliminating the need for duplicate parsing code.
"""

import argparse
import os
import sys
from pathlib import Path


# Add paths for imports
# __file__ = scripts/primary/generate_prompts.py
# .parent.parent.parent goes up to the project root directory
project_root = Path(__file__).parent.parent.parent

# Add specific lib directories to avoid import conflicts
# There are two lib/ directories: one in root, one in presentation-skill/
# We need both, but they can conflict, so we add the specific directories
sys.path.insert(0, str(project_root / "presentation-skill" / "lib"))
sys.path.insert(0, str(project_root / "lib"))

# Import the official parser module from presentation-skill/lib/
# This ensures consistency and reduces maintenance burden
# Import image prompt builder from root lib/ directory
from image_prompt_builder import ImagePromptBuilder
from parser import parse_presentation as official_parse_presentation


def parse_presentation(md_path: str):
    """
    Parse presentation markdown using the official parser.

    This is a wrapper function that adapts the official parser's output
    format to match what this script expects. It exists for backward
    compatibility and will be fully integrated in a future version.

    Args:
        md_path: Path to presentation markdown file

    Returns:
        Tuple of (slides_list, presentation_title) where:
            - slides_list: List of dicts with 'number', 'title', 'content', 'graphics'
            - presentation_title: Title of the presentation (from slide 1)

    Note for Junior Developers:
        Instead of copying the parsing code, we call the official parser
        and convert its output format. This way if the parser improves,
        this script automatically benefits from those improvements.
    """
    # Use the official parser to get Slide objects
    # This returns a list of Slide dataclass instances
    parsed_slides = official_parse_presentation(md_path)

    # Convert Slide objects to dictionaries for compatibility
    # Later we can update this script to work directly with Slide objects
    slides = []
    presentation_title = None

    for slide in parsed_slides:
        # Extract presentation title from first slide if available
        # The title field in slide 1 often contains the presentation name
        if slide.number == 1 and not presentation_title:
            # Try to extract just the core title without prefix
            title = slide.title
            if ":" in title and "Block" in title:
                # Remove "Block N Week N:" prefix if present
                presentation_title = title.split(":", 1)[1].strip()
            else:
                presentation_title = title

        # Convert Slide object to dictionary format
        # This maintains backward compatibility with existing code
        #
        # Note for Junior Developers:
        #   slide.content is a list of ContentItem objects (BulletItem, TableItem, etc)
        #   not strings. We need to extract the text from each one.
        content_lines = []
        if slide.content:
            for item in slide.content:
                # Check what type of content item this is and extract text accordingly
                if hasattr(item, "text"):
                    # BulletItem or TextItem - has a .text attribute
                    # Add indentation for bullets based on level
                    if hasattr(item, "level"):
                        indent = "  " * item.level  # 2 spaces per level
                        content_lines.append(f"{indent}- {item.text}")
                    else:
                        content_lines.append(item.text)
                elif hasattr(item, "code"):
                    # CodeBlockItem - has .code and .language
                    content_lines.append(f"```{item.language or ''}\n{item.code}\n```")
                elif hasattr(item, "headers"):
                    # TableItem - has .headers and .rows
                    # Convert table to simple text representation
                    content_lines.append(" | ".join(item.headers))
                    for row in item.rows:
                        content_lines.append(" | ".join(row))

        content_text = "\n".join(content_lines)

        slides.append(
            {
                "number": slide.number,
                "title": slide.title,
                "content": content_text,
                "graphics": slide.graphic if slide.graphic else "",
            }
        )

    return slides, presentation_title


def main():
    """Generate image prompts with configurable resolution and paths."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate AI image prompts from presentation markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate small resolution prompts (no titles)
  python scripts/primary/generate_prompts.py --resolution small

  # Generate high resolution prompts (with titles)
  python scripts/primary/generate_prompts.py --resolution high --output ./prompts/high

  # Use custom config and style
  python scripts/primary/generate_prompts.py --config my_config.md --style my_style.json

Note:
  This script was previously named generate_small_prompts.py and has been
  reorganized into scripts/primary/. It now supports all resolutions.
        """,
    )

    parser.add_argument(
        "--resolution",
        "-r",
        choices=["small", "medium", "high"],
        default="small",
        help="Output resolution (default: small). Small = no titles, High/Medium = with titles",
    )

    parser.add_argument(
        "--presentation",
        "-p",
        default="tests/testfiles/presentation.md",
        help="Path to presentation markdown file (default: tests/testfiles/presentation.md)",
    )

    parser.add_argument(
        "--style",
        "-s",
        default="templates/stratfield_style.json",
        help="Path to style configuration JSON (default: templates/stratfield_style.json)",
    )

    parser.add_argument(
        "--config",
        "-c",
        default="prompt_config.md",
        help="Path to prompt config file (default: prompt_config.md)",
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for prompts (default: tests/artifacts/images/stratfield/{resolution})",
    )

    args = parser.parse_args()

    # Set paths from arguments
    md_path = args.presentation
    style_path = args.style
    config_path = args.config
    resolution = args.resolution

    # Set output directory (default based on resolution)
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(f"tests/artifacts/images/stratfield/{resolution}")

    # Verify required paths
    if not os.path.exists(md_path):
        print(f"[ERROR] Markdown file not found: {md_path}")
        sys.exit(1)

    if not os.path.exists(style_path):
        print(f"[ERROR] Style config not found: {style_path}")
        sys.exit(1)

    # Config file is optional - will use defaults if not found
    config_exists = os.path.exists(config_path)
    if not config_exists:
        print(f"[WARNING] Config file not found: {config_path}")
        print("[WARNING] Using embedded default configuration")
        config_path = None

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get resolution info from config if available
    res_label = resolution.upper()
    res_info = "Custom resolution"
    if config_exists:
        try:
            import frontmatter

            with open(config_path, encoding="utf-8") as f:
                cfg = frontmatter.load(f).metadata
                if "resolutions" in cfg and resolution in cfg["resolutions"]:
                    res_cfg = cfg["resolutions"][resolution]
                    res_info = f"{res_cfg['width']}x{res_cfg['height']} ({res_cfg['aspect_ratio']})"
                    res_label = res_cfg.get("label", res_label)
        except:
            pass

    print("=" * 70)
    print(f"  IMAGE PROMPT GENERATOR - {res_label}")
    print("=" * 70)
    print(f"\nResolution: {resolution} ({res_info})")
    print(f"Source: {md_path}")
    print(f"Style: {style_path}")
    print(f"Config: {config_path if config_exists else '(embedded defaults)'}")
    print(f"Output: {output_dir}/")
    print()

    # Parse presentation
    print("[*] Parsing presentation...")
    slides, presentation_title = parse_presentation(md_path)
    print(f"    Found {len(slides)} slides")
    print(f"    Presentation: {presentation_title}")
    print()

    # Initialize builder with specified resolution and config
    print(f"[*] Initializing builder for {resolution} resolution...")
    builder = ImagePromptBuilder(
        style_path,
        resolution=resolution,
        presentation_title=presentation_title,
        config_path=config_path,
    )
    print(f"    Style: {builder.style_name}")
    print(f"    Resolution: {resolution}")
    print(f"    Config loaded: {'Yes' if config_exists else 'No (using defaults)'}")
    print()

    # Generate prompts
    print(f"[*] Generating {len(slides)} prompts for {resolution} resolution...")
    print("=" * 70)

    success_count = 0
    for slide in slides:
        print(f"\nSlide {slide['number']:2d}: {slide['title'][:50]}...")

        # Build prompt using new builder
        prompt_data = builder.build_prompt(slide)

        # Save prompt
        prompt_path = output_dir / f"prompt-{slide['number']:02d}.md"
        builder.save_prompt(prompt_data, prompt_path)

        # Show stats
        text_len = len(prompt_data["text"])
        elements = len(prompt_data["structured"]["key_elements"])
        layout = prompt_data["structured"]["composition"]["layout"]

        print(
            f"   [OK] {prompt_path.name} - {layout}, {elements} elements, {text_len} chars"
        )

        success_count += 1

    # Summary
    print("\n" + "=" * 70)
    print("  GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nSuccess: {success_count}/{len(slides)} prompts")
    print(f"Output directory: {output_dir}/")
    print(f"Files: prompt-01.md through prompt-{len(slides):02d}.md")
    print(f"\nAll prompts generated using '{builder.resolution}' resolution config")
    print("Config-driven composition rules and format instructions applied")
    print()


if __name__ == "__main__":
    main()
