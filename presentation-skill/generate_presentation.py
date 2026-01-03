#!/usr/bin/env python3
"""
Interactive Presentation Generator CLI

Main entry point for generating PowerPoint presentations from markdown.
Supports both interactive mode and command-line arguments.

Usage:
    # Interactive mode
    python generate_presentation.py

    # Command-line mode
    python generate_presentation.py presentation.md --template cfa --output output.pptx
"""

import sys
import os
from pathlib import Path
import argparse
from typing import Optional, List, Tuple

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent))

from lib.assembler import assemble_presentation, preview_presentation, get_available_templates
from lib.parser import parse_presentation, get_slides_needing_images


class InteractiveCLI:
    """Interactive command-line interface for presentation generation."""

    def __init__(self):
        self.markdown_path: Optional[str] = None
        self.template_id: Optional[str] = None
        self.style_config: Optional[str] = None
        self.output_name: Optional[str] = None
        self.templates: List[Tuple[str, str, str]] = []

    def run(self) -> None:
        """Run the interactive workflow."""
        print("\n" + "="*60)
        print("  📊 PowerPoint Presentation Generator")
        print("="*60 + "\n")

        # Step 1: Get markdown file
        self.markdown_path = self._get_markdown_file()

        # Step 2: Preview presentation
        self._preview_presentation()

        # Step 3: Select template
        self.template_id = self._select_template()

        # Step 4: Get style config (optional)
        self.style_config = self._get_style_config()

        # Step 5: Get output filename
        self.output_name = self._get_output_filename()

        # Step 6: Confirm
        if not self._confirm_generation():
            print("\n[ERROR] Cancelled by user")
            return

        # Step 7: Execute
        self._execute_generation()

    def _get_markdown_file(self) -> str:
        """Step 1: Get and validate markdown file path."""
        while True:
            print("📄 Enter path to presentation markdown file:")
            file_path = input("   > ").strip()

            if not file_path:
                print("   [WARN]  File path cannot be empty. Please try again.\n")
                continue

            # Expand user home directory if needed
            file_path = os.path.expanduser(file_path)

            # Try to resolve relative paths
            path = Path(file_path)
            if not path.is_absolute():
                path = Path.cwd() / path

            if not path.exists():
                print(f"   [ERROR] File not found: {path}")
                print("   Please check the path and try again.\n")
                continue

            if not path.is_file():
                print(f"   [ERROR] Path is not a file: {path}\n")
                continue

            return str(path)

    def _preview_presentation(self) -> None:
        """Step 2: Parse and preview the presentation."""
        print(f"\n🔍 Analyzing presentation...")

        try:
            slides = parse_presentation(self.markdown_path)
            slides_with_graphics = get_slides_needing_images(slides)

            print(f"   [OK] Found {len(slides)} slides")
            print(f"   🎨 {len(slides_with_graphics)} slides have graphics requiring image generation")

            if slides_with_graphics:
                print("\n   Slides with graphics:")
                for slide in slides_with_graphics[:5]:  # Show first 5
                    print(f"      • Slide {slide.number}: {slide.title[:50]}")
                if len(slides_with_graphics) > 5:
                    print(f"      ... and {len(slides_with_graphics) - 5} more")

        except Exception as e:
            print(f"   [ERROR] Error parsing presentation: {e}")
            sys.exit(1)

    def _select_template(self) -> str:
        """Step 3: Select brand template."""
        print("\n🎨 Select brand template:")

        self.templates = get_available_templates()

        if not self.templates:
            print("   [ERROR] No templates available!")
            sys.exit(1)

        for i, (template_id, name, desc) in enumerate(self.templates, 1):
            desc_str = f" - {desc}" if desc else ""
            print(f"   {i}. {name}{desc_str}")

        default_choice = 1
        while True:
            prompt = f"\nEnter number [1]: "
            choice = input(prompt).strip()

            # Default to 1
            if not choice:
                choice = str(default_choice)

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.templates):
                    selected = self.templates[choice_num - 1]
                    print(f"   [OK] Selected: {selected[1]}")
                    return selected[0]  # Return template ID
                else:
                    print(f"   [WARN]  Please enter a number between 1 and {len(self.templates)}")
            except ValueError:
                print(f"   [WARN]  Invalid input. Please enter a number.")

    def _get_style_config(self) -> Optional[str]:
        """Step 4: Get style config file (optional)."""
        print("\n📝 Path to style.json (or press Enter for default):")
        style_path = input("   > ").strip()

        if not style_path:
            print("   ℹ️  Using default style configuration")
            return None

        # Expand and resolve path
        style_path = os.path.expanduser(style_path)
        path = Path(style_path)
        if not path.is_absolute():
            path = Path.cwd() / path

        if not path.exists():
            print(f"   [WARN]  File not found: {path}")
            print("   Using default style configuration")
            return None

        print(f"   [OK] Using custom style: {path.name}")
        return str(path)

    def _get_output_filename(self) -> str:
        """Step 5: Get output filename."""
        default_name = "presentation.pptx"
        print(f"\n💾 Output filename [{default_name}]:")
        output = input("   > ").strip()

        if not output:
            output = default_name

        # Ensure .pptx extension
        if not output.endswith('.pptx'):
            output += '.pptx'

        print(f"   [OK] Output will be saved as: {output}")
        return output

    def _confirm_generation(self) -> bool:
        """Step 6: Show summary and confirm."""
        print("\n" + "="*60)
        print("  Ready to generate presentation")
        print("="*60)

        # Get slide counts
        slides = parse_presentation(self.markdown_path)
        slides_with_graphics = get_slides_needing_images(slides)

        template_name = next(name for tid, name, _ in self.templates if tid == self.template_id)

        print(f"\n  📄 Input:    {Path(self.markdown_path).name} ({len(slides)} slides)")
        print(f"  🎨 Template: {template_name}")
        print(f"  🖼️  Images:   {len(slides_with_graphics)} slides will be generated")
        if self.style_config:
            print(f"  📝 Style:    {Path(self.style_config).name}")
        print(f"  💾 Output:   {self.output_name}")

        # Check for API key if images need to be generated
        if slides_with_graphics and not os.getenv('GOOGLE_API_KEY'):
            print("\n  [WARN]  Warning: GOOGLE_API_KEY not set - image generation will be skipped")

        print()
        confirm = input("Continue? [Y/n]: ").strip().lower()

        return confirm in ['', 'y', 'yes']

    def _execute_generation(self) -> None:
        """Step 7: Execute the presentation generation."""
        print("\n" + "="*60)
        print("  🚀 Generating presentation...")
        print("="*60)

        try:
            output_path = assemble_presentation(
                markdown_path=self.markdown_path,
                template_id=self.template_id,
                style_config_path=self.style_config,
                output_name=self.output_name
            )

            print("\n" + "="*60)
            print("  [OK] Generation complete!")
            print("="*60)
            print(f"\n  📦 Output: {output_path}\n")

        except KeyboardInterrupt:
            print("\n\n[ERROR] Cancelled by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n\n[ERROR] Error during generation: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def non_interactive_mode(args: argparse.Namespace) -> None:
    """Run in non-interactive mode using command-line arguments."""

    # Preview mode
    if args.preview:
        try:
            preview_presentation(args.markdown)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Validate markdown file
    if not args.markdown:
        print("Error: Markdown file is required in non-interactive mode", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        sys.exit(1)

    markdown_path = Path(args.markdown)
    if not markdown_path.exists():
        print(f"Error: File not found: {markdown_path}", file=sys.stderr)
        sys.exit(1)

    # Validate template
    template_id = args.template
    available_templates = get_available_templates()
    available_ids = [tid for tid, _, _ in available_templates]

    if template_id not in available_ids:
        print(f"Error: Unknown template '{template_id}'", file=sys.stderr)
        print(f"Available templates:", file=sys.stderr)
        for tid, name, desc in available_templates:
            desc_str = f" - {desc}" if desc else ""
            print(f"  • {tid}: {name}{desc_str}", file=sys.stderr)
        sys.exit(1)

    # Validate style config if provided
    style_config = args.style
    if style_config:
        style_path = Path(style_config)
        if not style_path.exists():
            print(f"Warning: Style config not found: {style_path}", file=sys.stderr)
            print("Using default style configuration", file=sys.stderr)
            style_config = None

    # Execute generation
    try:
        output_path = assemble_presentation(
            markdown_path=str(markdown_path),
            template_id=template_id,
            style_config_path=style_config,
            output_name=args.output,
            skip_images=args.skip_images,
            fast_mode=args.fast,
            force_images=args.force
        )

        print(f"\n[OK] Success! Generated: {output_path}")

    except KeyboardInterrupt:
        print("\n[ERROR] Cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate PowerPoint presentations from markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python generate_presentation.py

  # Non-interactive mode
  python generate_presentation.py presentation.md --template cfa --output demo.pptx

  # Preview only
  python generate_presentation.py presentation.md --preview

  # Skip image generation
  python generate_presentation.py presentation.md --template cfa --skip-images

  # Fast/low-res images for testing
  python generate_presentation.py presentation.md --template cfa --fast
        """
    )

    parser.add_argument(
        'markdown',
        nargs='?',
        help='Path to markdown presentation file'
    )
    parser.add_argument(
        '--template', '-t',
        default='cfa',
        help='Template ID (default: cfa)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output filename (default: presentation.pptx)'
    )
    parser.add_argument(
        '--style', '-s',
        help='Path to style.json for image generation'
    )
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help='Skip image generation entirely'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Use fast/low-resolution image generation'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate existing images'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Preview presentation without generating'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Disable interactive prompts (requires markdown argument)'
    )

    args = parser.parse_args()

    # Determine mode
    if args.markdown or args.non_interactive or args.preview:
        # Non-interactive mode
        non_interactive_mode(args)
    else:
        # Interactive mode
        try:
            cli = InteractiveCLI()
            cli.run()
        except KeyboardInterrupt:
            print("\n\n[ERROR] Cancelled by user")
            sys.exit(130)
        except Exception as e:
            print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
