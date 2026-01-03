"""
Markdown parser for presentation slide definitions.

Parses markdown files following the pres-template.md format to extract
structured slide data including titles, content, graphics, and speaker notes.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class Slide:
    """
    Represents a single presentation slide with all its components.

    Attributes:
        number: Slide number in the presentation sequence
        slide_type: Classification of slide type (e.g., "TITLE SLIDE", "CONTENT", "SECTION DIVIDER")
        title: Main title displayed on slide
        subtitle: Optional secondary title (used primarily on title slides)
        content: List of (text, indent_level) tuples representing bullet points
        graphic: Description of visual element for AI image generation (if present)
        speaker_notes: Full narration with stage directions
        raw_content: Complete markdown text for this slide
    """
    number: int
    slide_type: str
    title: str
    subtitle: Optional[str] = None
    content: List[Tuple[str, int]] = field(default_factory=list)
    graphic: Optional[str] = None
    speaker_notes: Optional[str] = None
    raw_content: str = ""

    def __repr__(self) -> str:
        return f"Slide({self.number}, type='{self.slide_type}', title='{self.title}')"


def parse_presentation(file_path: str) -> List[Slide]:
    """
    Parse a markdown presentation file and extract all slide data.

    Args:
        file_path: Path to the markdown file following pres-template.md format

    Returns:
        List of Slide objects in presentation order

    Raises:
        FileNotFoundError: If the specified file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Presentation file not found: {file_path}")

    content = path.read_text(encoding='utf-8')
    slides = []

    # Split content into individual slides
    # Match slide headers: ## **SLIDE N: TYPE**, ## Slide N, ## **Slide N: TYPE**
    slide_pattern = re.compile(
        r'^##\s+\*{0,2}SLIDE\s+(\d+)(?::\s*([^*\n]+?))?\*{0,2}\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(slide_pattern.finditer(content))

    for i, match in enumerate(matches):
        slide_number = int(match.group(1))
        slide_type = match.group(2).strip() if match.group(2) else "CONTENT"

        # Extract the full slide content (from this header to the next slide header or end)
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        slide_content = content[start_pos:end_pos].strip()

        # Parse the slide fields
        slide = _parse_slide_content(slide_number, slide_type, slide_content)
        slides.append(slide)

    return slides


def _parse_slide_content(number: int, slide_type: str, content: str) -> Slide:
    """
    Parse the content of a single slide to extract all fields.

    Args:
        number: Slide number
        slide_type: Type of slide
        content: Markdown content for this slide

    Returns:
        Parsed Slide object
    """
    slide = Slide(number=number, slide_type=slide_type, title="", raw_content=content)

    # Extract title
    title_match = re.search(r'^\*{0,2}Title\*{0,2}:\s*(.+?)$', content, re.MULTILINE | re.IGNORECASE)
    if title_match:
        slide.title = title_match.group(1).strip()

    # Extract subtitle
    subtitle_match = re.search(r'^\*{0,2}Subtitle\*{0,2}:\s*(.+?)$', content, re.MULTILINE | re.IGNORECASE)
    if subtitle_match:
        slide.subtitle = subtitle_match.group(1).strip()

    # Extract content section (bullet points)
    slide.content = _extract_content_bullets(content)

    # Extract graphic description
    graphic_match = re.search(
        r'^\*{0,2}Graphic\*{0,2}:\s*(.+?)(?=^\*{0,2}[A-Z\s]+\*{0,2}:|$)',
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL
    )
    if graphic_match:
        graphic_text = graphic_match.group(1).strip()
        # Clean up the graphic text (remove extra whitespace, newlines)
        graphic_text = re.sub(r'\s+', ' ', graphic_text)
        if graphic_text and graphic_text != "None" and graphic_text != "[None]":
            slide.graphic = graphic_text

    # Extract speaker notes
    notes_match = re.search(
        r'^\*{0,2}SPEAKER NOTES\*{0,2}:\s*(.+?)(?=^\*{0,2}BACKGROUND\*{0,2}:|^\*{0,2}Sources\*{0,2}:|^---\s*$|$)',
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL
    )
    if notes_match:
        notes_text = notes_match.group(1).strip()
        if notes_text:
            slide.speaker_notes = notes_text

    return slide


def _extract_content_bullets(content: str) -> List[Tuple[str, int]]:
    """
    Extract bullet points from the Content section with indentation levels.

    Indentation levels:
        - Lines starting with `- ` are level 0
        - Lines starting with `  - ` (2 spaces) are level 1
        - Lines starting with `    - ` (4+ spaces) are level 2

    Args:
        content: Full slide markdown content

    Returns:
        List of (text, indent_level) tuples
    """
    bullets = []

    # Find the Content section - it ends at known major section headers
    # Major sections: Graphic, SPEAKER NOTES, BACKGROUND, Sources, IMPLEMENTATION GUIDANCE, or ---
    # Note: Use \n instead of ^ in lookahead to avoid matching start of every line in MULTILINE mode
    # Note: Use \Z instead of $ to match only end of string, not end of line
    content_match = re.search(
        r'^\*{0,2}Content\*{0,2}:\s*\n(.+?)(?=\n\*{0,2}(?:Graphic|SPEAKER NOTES|BACKGROUND|Sources|IMPLEMENTATION GUIDANCE)\*{0,2}:|\n---\s*$|\Z)',
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL
    )

    if not content_match:
        return bullets

    content_section = content_match.group(1)

    # Parse bullet points with indentation
    for line in content_section.split('\n'):
        # Skip empty lines
        if not line.strip():
            continue

        # Match bullet points: count leading spaces, then -, *, or number
        # Allow up to 10 spaces for indentation
        bullet_match = re.match(r'^( *)[-*]\s+(.+)$', line)
        if bullet_match:
            indent_spaces = len(bullet_match.group(1))
            bullet_text = bullet_match.group(2).strip()

            # Determine indentation level based on spaces
            # 0-1 spaces = level 0
            # 2-3 spaces = level 1
            # 4+ spaces = level 2
            if indent_spaces < 2:
                indent_level = 0
            elif indent_spaces < 4:
                indent_level = 1
            else:
                indent_level = 2

            bullets.append((bullet_text, indent_level))
            continue

        # Match numbered lists
        numbered_match = re.match(r'^( *)(\d+)\.\s+(.+)$', line)
        if numbered_match:
            indent_spaces = len(numbered_match.group(1))
            bullet_text = numbered_match.group(3).strip()

            if indent_spaces < 2:
                indent_level = 0
            elif indent_spaces < 4:
                indent_level = 1
            else:
                indent_level = 2

            bullets.append((bullet_text, indent_level))
            continue

        # If line starts with bold text (subsection label like **Key Principle:**), include it
        # But skip if it's a known section header (Graphic, SPEAKER NOTES, etc.)
        if line.strip().startswith('**') and ':' in line:
            # Check if it's a major section header that we should skip
            header_match = re.match(r'^\*{0,2}(Graphic|SPEAKER NOTES|BACKGROUND|Sources|IMPLEMENTATION GUIDANCE)\*{0,2}:',
                                   line.strip(), re.IGNORECASE)
            if not header_match:
                # It's a subsection label within Content, include it
                bullets.append((line.strip(), 0))
            continue

        # Also capture non-bullet lines that are part of content (like quotes)
        # Only if they start with special characters
        if line.strip().startswith('>') or line.strip().startswith('```'):
            bullets.append((line.strip(), 0))

    return bullets


def get_slides_needing_images(slides: List[Slide]) -> List[Slide]:
    """
    Filter slides that have graphic descriptions and need images generated.

    Args:
        slides: List of all slides in the presentation

    Returns:
        List of slides that have non-empty graphic fields
    """
    return [slide for slide in slides if slide.graphic]


def map_slide_type_to_method(slide_type: str) -> str:
    """
    Map slide type classification to template method name.

    Args:
        slide_type: Slide type from markdown (e.g., "TITLE SLIDE", "CONTENT")

    Returns:
        Method name to call on template class (e.g., "add_title_slide")
    """
    # Normalize the slide type (uppercase, strip whitespace)
    normalized_type = slide_type.upper().strip()

    # Title slides
    if normalized_type in ["TITLE SLIDE", "TITLE"]:
        return "add_title_slide"

    # Section dividers
    if normalized_type in ["SECTION DIVIDER", "SECTION BREAK", "SECTION"]:
        return "add_section_break"

    # Image-focused slides (architecture diagrams, etc.)
    if normalized_type in ["ARCHITECTURE", "DIAGRAM", "IMAGE"]:
        return "add_image_slide"

    # Q&A slides (often formatted as section breaks)
    if normalized_type in ["Q&A", "Q&A / CONTACT", "CONTACT"]:
        return "add_section_break"

    # All other content slides (most common)
    # This includes: CONTENT, PROBLEM STATEMENT, INSIGHT, CONCEPT INTRODUCTION,
    # FRAMEWORK, COMPARISON, DEEP DIVE, CASE STUDY, PATTERN, METRICS, ACTION,
    # SUMMARY, CLOSING, APPENDIX, etc.
    return "add_content_slide"


def get_slide_summary(slides: List[Slide]) -> str:
    """
    Generate a summary of the parsed presentation.

    Args:
        slides: List of parsed slides

    Returns:
        Human-readable summary string
    """
    if not slides:
        return "No slides found in presentation."

    summary_lines = [
        f"Parsed {len(slides)} slides:",
        ""
    ]

    slides_with_graphics = get_slides_needing_images(slides)

    for slide in slides:
        has_graphic = slide in slides_with_graphics
        graphic_marker = " [HAS GRAPHIC]" if has_graphic else ""
        summary_lines.append(
            f"  Slide {slide.number}: {slide.slide_type} - \"{slide.title}\"{graphic_marker}"
        )

    summary_lines.extend([
        "",
        f"Slides with graphics: {len(slides_with_graphics)}/{len(slides)}"
    ])

    return "\n".join(summary_lines)


if __name__ == "__main__":
    # Example usage for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <presentation.md>")
        sys.exit(1)

    presentation_file = sys.argv[1]

    try:
        slides = parse_presentation(presentation_file)
        print(get_slide_summary(slides))

        # Show details for first slide
        if slides:
            print("\n--- First Slide Details ---")
            first_slide = slides[0]
            print(f"Number: {first_slide.number}")
            print(f"Type: {first_slide.slide_type}")
            print(f"Title: {first_slide.title}")
            print(f"Subtitle: {first_slide.subtitle}")
            print(f"Content bullets: {len(first_slide.content)}")
            if first_slide.content:
                print("First 3 bullets:")
                for text, level in first_slide.content[:3]:
                    indent = "  " * level
                    print(f"  {indent}- {text}")
            print(f"Has graphic: {'Yes' if first_slide.graphic else 'No'}")
            if first_slide.graphic:
                print(f"Graphic description: {first_slide.graphic[:100]}...")
            print(f"Has speaker notes: {'Yes' if first_slide.speaker_notes else 'No'}")
            print(f"Method to use: {map_slide_type_to_method(first_slide.slide_type)}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
