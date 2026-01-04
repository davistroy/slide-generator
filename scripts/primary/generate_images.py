#!/usr/bin/env python3
"""
Generate presentation images for any resolution using Gemini API.

Supports high/medium/small resolutions with config-driven generation parameters.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
import frontmatter
from google import genai
from google.genai import types

# Load environment variables from .env file
# Use override=True to ensure .env file takes precedence over shell environment
# This is important if there's an old/expired API key set in the shell session
load_dotenv(override=True)

# API Configuration - loaded from environment
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    print("[ERROR] GOOGLE_API_KEY not found in environment variables")
    print("[ERROR] Please create a .env file with your API key (see .env.example)")
    sys.exit(1)


def load_config(config_path: str = "prompt_config.md") -> dict:
    """Load unified configuration from YAML frontmatter."""
    if not os.path.exists(config_path):
        print(f"[WARNING] Config file not found: {config_path}")
        print(f"[WARNING] Using embedded defaults")
        return get_default_config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            return post.metadata
    except Exception as e:
        print(f"[WARNING] Failed to load config from {config_path}: {e}")
        print(f"[WARNING] Using embedded defaults")
        return get_default_config()


def get_default_config() -> dict:
    """Return embedded default configuration."""
    return {
        'image_generation': {
            'model': 'gemini-3-pro-image-preview',
            'generation_params': {
                'small': {'aspect_ratio': '5:4', 'image_size': 'STANDARD', 'delay_seconds': 4}
            },
            'prompt_parsing': {
                'text_prompt_header': '## Text Prompt (sent to Gemini)',
                'required_validation_text': 'DO NOT include ANY titles or slide numbers'
            },
            'file_patterns': {
                'prompt_file': 'prompt-{number:02d}.md',
                'output_file': 'slide-{number:02d}.jpg'
            },
            'console_output': {
                'success_message': 'Saved: {filename} ({size_mb:.2f} MB)',
                'skip_message': 'SKIPPED (already exists)',
                'generating_message': 'Generating image (no titles/numbers)...',
                'warning_validation': 'NO titles/slide numbers instruction not found in prompt!'
            }
        }
    }


def load_style_config(style_path: str) -> dict:
    """Load style configuration from JSON file."""
    with open(style_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_prompt_text(prompt_file_path: Path, config: dict) -> str:
    """Extract the text prompt section from a prompt file using config."""
    with open(prompt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get header from config
    header = config['image_generation']['prompt_parsing']['text_prompt_header']

    # Extract text prompt section
    if header in content:
        text_section = content.split(header)[1]
        # Remove markdown code fences
        text_section = text_section.strip().strip('```').strip()
        return text_section

    return ""


def generate_image(client, prompt: str, style_config: dict, config: dict, resolution: str = 'small') -> bytes:
    """Generate image using Gemini Pro with config-driven parameters."""

    # Get style details from config
    recipe = style_config.get('PromptRecipe', {})
    core_style = recipe.get('CoreStylePrompt', '')
    color_constraint = recipe.get('PaletteConstraintPrompt', '')
    text_enforcement = recipe.get('TextEnforcementPrompt', '')

    # Combine prompt with style configuration
    full_prompt = f"""{prompt}

STYLE DETAILS:
{core_style}

COLOR PALETTE:
{color_constraint}

TEXT RULES:
{text_enforcement}
"""

    # Get generation params from config
    gen_params = config['image_generation']['generation_params'][resolution]
    aspect_ratio = gen_params['aspect_ratio']
    image_size = gen_params['image_size']
    model = config['image_generation']['model']

    print(f"      Generating with aspect ratio: {aspect_ratio}, image size: {image_size}")

    # Generate image
    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size
                )
            )
        )

        # Extract image data
        if response.candidates and len(response.candidates) > 0:
            parts = response.candidates[0].content.parts
            for part in parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    return part.inline_data.data

        raise Exception("No image data in response")

    except Exception as e:
        print(f"      [ERROR] Generation failed: {str(e)}")
        raise


def save_image(image_data: bytes, output_path: Path):
    """Save image data to file."""
    with open(output_path, 'wb') as f:
        f.write(image_data)


def main():
    """Generate presentation images with configurable resolution and paths."""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Generate presentation images from prompts using Gemini API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate small resolution images (no titles)
  python scripts/primary/generate_images.py --resolution small

  # Generate high resolution 4K images (with titles)
  python scripts/primary/generate_images.py --resolution high --output ./images/high

  # Use custom config and style
  python scripts/primary/generate_images.py --config my_config.md --style my_style.json

Note:
  This script was previously named generate_small_images.py and has been
  reorganized into scripts/primary/. It now supports all resolutions.
        """
    )

    parser.add_argument(
        '--resolution', '-r',
        choices=['small', 'medium', 'high'],
        default='small',
        help='Output resolution (default: small). Determines aspect ratio and image size'
    )

    parser.add_argument(
        '--input', '-i',
        help='Input directory containing prompt files (default: tests/artifacts/images/stratfield/{resolution})'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output directory for images (default: same as input)'
    )

    parser.add_argument(
        '--style', '-s',
        default='templates/stratfield_style.json',
        help='Path to style configuration JSON (default: templates/stratfield_style.json)'
    )

    parser.add_argument(
        '--config', '-c',
        default='prompt_config.md',
        help='Path to unified config file (default: prompt_config.md)'
    )

    args = parser.parse_args()

    # Set paths from arguments
    resolution = args.resolution
    style_path = args.style
    config_path = args.config

    # Set input/output directories (default based on resolution)
    if args.input:
        input_dir = Path(args.input)
    else:
        input_dir = Path(f"tests/artifacts/images/stratfield/{resolution}")

    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = input_dir  # Same as input by default

    # Load configuration
    print("[*] Loading configuration...")
    config = load_config(config_path)
    config_exists = os.path.exists(config_path)
    print(f"    Config loaded from: {config_path if config_exists else 'embedded defaults'}")

    # Get config values
    gen_config = config['image_generation']
    model = gen_config['model']
    gen_params = gen_config['generation_params'][resolution]

    # Get resolution label if available
    res_label = resolution.upper()
    if config_exists:
        try:
            if 'resolutions' in config and resolution in config['resolutions']:
                res_label = config['resolutions'][resolution].get('label', res_label)
        except:
            pass

    # Verify paths
    if not os.path.exists(style_path):
        print(f"[ERROR] Style config not found: {style_path}")
        sys.exit(1)

    if not input_dir.exists():
        print(f"[ERROR] Input directory not found: {input_dir}/")
        sys.exit(1)

    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*70)
    print(f"  GEMINI IMAGE GENERATOR - {res_label}")
    print("="*70)
    print(f"\nModel: {model}")
    print(f"Resolution: {resolution}")
    print(f"Style: {style_path}")
    print(f"Config: {config_path if config_exists else '(embedded defaults)'}")
    print(f"Input: {input_dir}/")
    print(f"Output: {output_dir}/")
    print(f"Aspect Ratio: {gen_params['aspect_ratio']}")
    print(f"Image Size: {gen_params['image_size']}")
    print(f"Delay: {gen_params['delay_seconds']}s between requests")
    print()

    # Initialize Gemini client
    print("[*] Initializing Gemini client...")
    client = genai.Client(api_key=API_KEY)

    # Load style configuration
    print("[*] Loading Stratfield style configuration...")
    style_config = load_style_config(style_path)
    print(f"    Style: {style_config.get('StyleName', 'Unknown')}")
    print()

    # Find all prompt files
    prompt_files = sorted(input_dir.glob("prompt-*.md"))

    if not prompt_files:
        print(f"[ERROR] No prompt files found in {input_dir}/")
        sys.exit(1)

    print(f"Found {len(prompt_files)} prompt files")
    print()
    print("="*70)
    print("  GENERATING IMAGES")
    print("="*70)
    print()

    # Generate images
    total_generated = 0
    total_failed = 0

    # Get config values for messages and validation
    console_msgs = gen_config['console_output']
    parsing_config = gen_config['prompt_parsing']
    delay_seconds = gen_params['delay_seconds']

    for i, prompt_file in enumerate(prompt_files, 1):
        slide_num = int(prompt_file.stem.split('-')[1])
        output_pattern = gen_config['file_patterns']['output_file']
        output_image = output_dir / output_pattern.format(number=slide_num)

        # Skip if already exists
        if output_image.exists():
            print(f"[{i:2d}/{len(prompt_files)}] Slide {slide_num:2d}: {console_msgs['skip_message']}")
            total_generated += 1
            continue

        print(f"[{i:2d}/{len(prompt_files)}] Slide {slide_num:2d}: {console_msgs['generating_message']}")

        try:
            # Extract prompt text using config
            prompt_text = extract_prompt_text(prompt_file, config)

            if not prompt_text:
                print(f"      [ERROR] Could not extract prompt text")
                total_failed += 1
                continue

            # Verify required validation text is present (from config)
            validation_text = parsing_config['required_validation_text']
            if validation_text not in prompt_text:
                print(f"      [WARNING] {console_msgs['warning_validation']}")

            # Generate image using config
            image_data = generate_image(client, prompt_text, style_config, config, resolution)

            # Save image
            save_image(image_data, output_image)

            file_size = output_image.stat().st_size / (1024 * 1024)  # MB
            success_msg = console_msgs['success_message'].format(
                filename=output_image.name,
                size_mb=file_size
            )
            print(f"      [OK] {success_msg}")

            total_generated += 1

            # Delay between requests (from config)
            if i < len(prompt_files):
                print(f"      Waiting {delay_seconds}s before next request...")
                time.sleep(delay_seconds)

        except Exception as e:
            print(f"      [FAILED] {str(e)}")
            total_failed += 1
            time.sleep(delay_seconds)

    # Summary
    print()
    print("="*70)
    print("  GENERATION COMPLETE")
    print("="*70)
    print(f"\nTotal images generated: {total_generated}")
    print(f"Total failures: {total_failed}")
    print(f"Expected total: {len(prompt_files)} images")
    print()

    # Show directory contents
    images = list(output_dir.glob("slide-*.jpg"))
    print(f"{res_label}: {len(images)} images in {output_dir}/")
    print()

    if len(images) == len(prompt_files):
        print(f"[SUCCESS] All {len(prompt_files)} {resolution} images generated!")
    else:
        print(f"[WARNING] Expected {len(prompt_files)} images, found {len(images)}")

    print()


if __name__ == "__main__":
    main()
