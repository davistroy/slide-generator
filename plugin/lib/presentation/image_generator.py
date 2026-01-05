"""
Image generation module for presentation slides using Google Gemini API.

This module provides functions to generate slide images based on slide content,
graphics descriptions, and visual style configurations.
"""

import json
import os
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


try:
    from google import genai
    from google.genai import types

    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    GOOGLE_GENAI_AVAILABLE = False
    print(
        "Warning: google-genai package not installed. Image generation will not be available."
    )

# Try to import Slide from parser, but make it optional
try:
    from .parser import Slide

    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    # Define a simple Slide type hint for when parser is not available
    Slide = Any


# Constants
MODEL_ID = "gemini-3-pro-image-preview"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Default style configuration
DEFAULT_STYLE = {
    "style": "professional, modern, clean",
    "tone": "corporate",
    "visual_elements": "geometric shapes, minimal text, bold colors",
}


def load_style_config(style_path: str) -> dict:
    """
    Reads and parses a JSON style configuration file.

    Handles common JSON errors like trailing commas by using regex to clean
    the JSON before parsing.

    Args:
        style_path: Path to the JSON style configuration file

    Returns:
        Parsed style configuration as a dictionary

    Raises:
        FileNotFoundError: If the style file doesn't exist
        ValueError: If the JSON is invalid after cleaning
    """
    try:
        with open(style_path, encoding="utf-8") as f:
            text = f.read()
            # Remove trailing commas before closing braces/brackets
            # Matches a comma, optional whitespace, followed by } or ]
            text = re.sub(r",\s*([\]}])", r"\1", text)
            data = json.loads(text)
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Style configuration file not found: {style_path}")
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in style file: {e}\nTip: Remove comments if present."
        )
    except Exception as e:
        raise Exception(f"Error reading style file: {e}")


def _get_slide_field(slide: dict | Any, field: str, default: Any = None) -> Any:
    """
    Helper function to get a field from a slide object or dictionary.

    Args:
        slide: Slide object or dictionary
        field: Field name to retrieve
        default: Default value if field doesn't exist

    Returns:
        Field value or default
    """
    if isinstance(slide, dict):
        return slide.get(field, default)
    else:
        return getattr(slide, field, default)


def _format_style_config(style_config: dict) -> str:
    """
    Formats style configuration dictionary as readable text for prompts.

    Args:
        style_config: Style configuration dictionary

    Returns:
        Formatted style configuration as string
    """
    return json.dumps(style_config, indent=2)


def generate_slide_image(
    slide: dict | Slide,
    style_config: dict,
    output_dir: Path,
    fast_mode: bool = False,
    notext: bool = True,
    force: bool = False,
    api_key: str | None = None,
    prompt_override: str | None = None,
) -> Path | None:
    """
    Generate an image for a single slide using Google Gemini API.

    Args:
        slide: Slide object or dictionary with fields:
               - number: Slide number
               - title: Slide title (optional)
               - content: Slide content text (optional)
               - graphic: Visual description for image generation (required)
        style_config: Visual style configuration dictionary
        output_dir: Directory to save generated images
        fast_mode: If True, use standard resolution instead of 4K
        notext: If True, generate clean backgrounds without text/charts
        force: If True, overwrite existing images
        api_key: Google API key (if None, reads from GOOGLE_API_KEY env var)
        prompt_override: Optional refined prompt for regeneration (used by refinement engine)

    Returns:
        Path to generated image file, or None if generation failed or was skipped
    """
    # Check if google-genai is available
    if not GOOGLE_GENAI_AVAILABLE:
        print(
            "Error: google-genai package not installed. Run: pip install google-genai"
        )
        return None

    # Get API key
    if api_key is None:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("Warning: GOOGLE_API_KEY not found. Image generation skipped.")
        return None

    # Extract slide data
    slide_num = _get_slide_field(
        slide, "number", _get_slide_field(slide, "slide_number", "?")
    )
    slide_title = _get_slide_field(slide, "title", "")
    slide_content = _get_slide_field(slide, "content", "")

    # Use prompt_override if provided (for refinement), otherwise use slide's graphic field
    graphic_description = prompt_override or _get_slide_field(slide, "graphic", "")

    # If no graphic description, skip image generation
    if not graphic_description or not graphic_description.strip():
        return None

    # Determine output file path
    filename = f"slide-{slide_num}.jpg"
    output_file_path = Path(output_dir) / filename

    # Check if file exists
    if output_file_path.exists() and not force:
        print(
            f" > Skipping Slide {slide_num}: File exists (use force=True to overwrite)"
        )
        return output_file_path

    # Construct prompt
    text_instruction = ""
    if notext:
        text_instruction = (
            "\n\nIMPORTANT: Do not render any text, charts, or data labels inside the image. "
            "Create a clean, artistic background or illustration suitable for overlaying text in PowerPoint later."
        )

    # Build context from slide content
    context_parts = []
    if slide_title:
        context_parts.append(f"Title: {slide_title}")
    if slide_content:
        context_parts.append(f"Content:\n{slide_content}")

    context_text = (
        "\n\n".join(context_parts) if context_parts else "No additional context"
    )

    prompt = (
        f"You are an expert presentation designer.\n\n"
        f"--- VISUAL STYLE ---\n{_format_style_config(style_config)}\n\n"
        f"--- SLIDE CONTEXT ---\n{context_text}\n\n"
        f"--- VISUAL DESCRIPTION ---\n{graphic_description}\n\n"
        f"--- TASK ---\n"
        f"Generate a high-quality presentation slide image based on the visual description above. "
        f"The image must strictly adhere to the defined visual style.{text_instruction}"
    )

    # Configure image generation
    target_size = "4K" if not fast_mode else None

    config = types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size=target_size),
    )

    # Initialize Gemini client with 5-minute timeout for 4K generation
    client = genai.Client(
        api_key=api_key, http_options=types.HttpOptions(timeout=300000)
    )

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config=config,
            )

            # Check for image in response
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        # Create output directory if needed
                        output_file_path.parent.mkdir(parents=True, exist_ok=True)

                        # Save image
                        with open(output_file_path, "wb") as f:
                            f.write(part.inline_data.data)

                        print(f" > Success: Saved {filename}")
                        return output_file_path

            # No image returned
            print(f" > Attempt {attempt}: No image returned for Slide {slide_num}.")

            # Check for safety blocks
            if response.candidates:
                finish_reason = response.candidates[0].finish_reason
                if "SAFETY" in str(finish_reason):
                    print(
                        " > BLOCKED: Image blocked by safety filters. Check prompt or style content."
                    )
                    return None  # Don't retry safety blocks

        except Exception as e:
            print(f" > Attempt {attempt} failed for Slide {slide_num}: {e}")

        # Wait before retrying
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    print(f" > Failed to generate Slide {slide_num} after {MAX_RETRIES} attempts.")
    return None


def generate_all_images(
    slides: list[dict | Slide],
    style_config: dict,
    output_dir: Path,
    fast_mode: bool = False,
    notext: bool = True,
    force: bool = False,
    callback: Callable[[int, bool, Path | None], None] | None = None,
    api_key: str | None = None,
) -> dict[int, Path]:
    """
    Generate images for all slides in a presentation.

    Args:
        slides: List of slide objects or dictionaries
        style_config: Visual style configuration dictionary
        output_dir: Directory to save generated images
        fast_mode: If True, use standard resolution instead of 4K
        notext: If True, generate clean backgrounds without text/charts
        force: If True, overwrite existing images
        callback: Optional callback function called after each slide with:
                  callback(slide_number, success, image_path)
        api_key: Google API key (if None, reads from GOOGLE_API_KEY env var)

    Returns:
        Dictionary mapping slide numbers to generated image paths
    """
    results = {}
    total_slides = len(slides)

    print("--- Starting Batch Image Generation ---")
    print(f"Total Slides: {total_slides}")
    print(f"Model:        {MODEL_ID}")
    print(f"Resolution:   {'Standard (Fast)' if fast_mode else '4K (High Res)'}")
    print(f"Text Removal: {'Enabled' if notext else 'Disabled'}")
    print(f"Output Dir:   {Path(output_dir).absolute()}\n")

    for i, slide in enumerate(slides, 1):
        slide_num = _get_slide_field(
            slide, "number", _get_slide_field(slide, "slide_number", i)
        )

        print(f"Processing slide {i} of {total_slides} (Slide {slide_num})...")

        image_path = generate_slide_image(
            slide=slide,
            style_config=style_config,
            output_dir=output_dir,
            fast_mode=fast_mode,
            notext=notext,
            force=force,
            api_key=api_key,
        )

        success = image_path is not None

        if success:
            results[slide_num] = image_path

        # Call callback if provided
        if callback:
            callback(slide_num, success, image_path)

        print("-" * 40)

    print("\n--- Batch Generation Complete ---")
    print(f"Successfully generated: {len(results)}/{total_slides} images")

    return results


# Convenience function for backward compatibility with existing code
def get_style_instruction(style_path: str) -> str:
    """
    Reads style file and returns formatted JSON string.

    This function is for backward compatibility with existing code.
    Prefer using load_style_config() for new code.

    Args:
        style_path: Path to the JSON style configuration file

    Returns:
        Formatted JSON string
    """
    config = load_style_config(style_path)
    return _format_style_config(config)
