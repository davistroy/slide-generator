"""
Markdown parser for presentation slide definitions.

Parses markdown files following the pres-template.md format to extract
structured slide data including titles, content, graphics, and speaker notes.

ENHANCED VERSION: Supports tables, numbered lists, code blocks, and mixed content.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union


# Content item types
@dataclass
class BulletItem:
    """A bullet point with text and indentation level."""

    text: str
    level: int  # 0, 1, or 2


@dataclass
class TableItem:
    """A markdown table."""

    headers: list[str]
    rows: list[list[str]]


@dataclass
class CodeBlockItem:
    """A code block."""

    code: str
    language: str | None = None


@dataclass
class TextItem:
    """Plain text paragraph."""

    text: str


# Union type for all content items
ContentItem = Union[BulletItem, TableItem, CodeBlockItem, TextItem]


@dataclass
class Slide:
    """
    Represents a single presentation slide with all its components.

    Attributes:
        number: Slide number in the presentation sequence
        slide_type: Classification of slide type (e.g., "TITLE SLIDE", "CONTENT", "SECTION DIVIDER")
        title: Main title displayed on slide
        subtitle: Optional secondary title (used primarily on title slides)
        content: List of content items (bullets, tables, code blocks, text)
        content_bullets: Legacy format - list of (text, indent_level) tuples for backward compatibility
        graphic: Description of visual element for AI image generation (if present)
        speaker_notes: Full narration with stage directions
        raw_content: Complete markdown text for this slide
    """

    number: int
    slide_type: str
    title: str
    subtitle: str | None = None
    content: list[ContentItem] = field(default_factory=list)
    content_bullets: list[tuple[str, int]] = field(
        default_factory=list
    )  # Backward compatibility
    graphic: str | None = None
    speaker_notes: str | None = None
    raw_content: str = ""

    def __repr__(self) -> str:
        return f"Slide({self.number}, type='{self.slide_type}', title='{self.title}')"


def parse_presentation(file_path: str) -> list[Slide]:
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

    content = path.read_text(encoding="utf-8")
    slides = []

    # Split content into individual slides
    # Match slide headers: ## **SLIDE N: TYPE**, ### SLIDE N: TYPE, ## Slide N, ## **Slide N: TYPE**
    slide_pattern = re.compile(
        r"^#{2,3}\s+\*{0,2}SLIDE\s+(\d+)(?::\s*([^*\n]+?))?\*{0,2}\s*$",
        re.MULTILINE | re.IGNORECASE,
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


def _clean_markdown_formatting(text: str) -> str:
    """
    Remove markdown formatting from text.

    Strips:
    - Bold markers (**text** -> text)
    - Italic markers (*text* -> text)
    - Inline code markers (`text` -> text)
    - Leading/trailing markers (** text -> text)

    Args:
        text: Text with potential markdown formatting

    Returns:
        Clean text without formatting markers
    """
    # Remove bold (**text**)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    # Remove italic (*text*)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    # Remove inline code (`text`)
    text = re.sub(r"`(.+?)`", r"\1", text)
    # Remove leading/trailing ** or *
    text = text.strip("*").strip()
    # Remove any remaining standalone asterisks at word boundaries
    text = re.sub(r"^\*+\s*", "", text)
    text = re.sub(r"\s*\*+$", "", text)
    return text.strip()


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

    # Extract title (and clean markdown formatting)
    title_match = re.search(
        r"^\*{0,2}Title\*{0,2}:\s*(.+?)$", content, re.MULTILINE | re.IGNORECASE
    )
    if title_match:
        raw_title = title_match.group(1).strip()
        slide.title = _clean_markdown_formatting(raw_title)

    # Extract subtitle (and clean markdown formatting)
    subtitle_match = re.search(
        r"^\*{0,2}Subtitle\*{0,2}:\s*(.+?)$", content, re.MULTILINE | re.IGNORECASE
    )
    if subtitle_match:
        raw_subtitle = subtitle_match.group(1).strip()
        slide.subtitle = _clean_markdown_formatting(raw_subtitle)

    # Extract content section (bullets, tables, code blocks, text)
    slide.content, slide.content_bullets = _extract_content_section(content)

    # Extract graphic description
    graphic_match = re.search(
        r"^\*{0,2}Graphic\*{0,2}:\s*(.+?)(?=^\*{0,2}[A-Z\s]+\*{0,2}:|$)",
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if graphic_match:
        graphic_text = graphic_match.group(1).strip()
        # Clean up the graphic text (remove extra whitespace, newlines, and markdown formatting)
        graphic_text = re.sub(r"\s+", " ", graphic_text)
        graphic_text = _clean_markdown_formatting(graphic_text)
        if graphic_text and graphic_text not in {"None", "[None]"}:
            slide.graphic = graphic_text

    # Extract speaker notes
    notes_match = re.search(
        r"^\*{0,2}SPEAKER NOTES\*{0,2}:\s*(.+?)(?=^\*{0,2}BACKGROUND\*{0,2}:|^\*{0,2}Sources\*{0,2}:|^---\s*$|$)",
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )
    if notes_match:
        notes_text = notes_match.group(1).strip()
        if notes_text:
            slide.speaker_notes = notes_text

    return slide


def _extract_content_section(
    content: str,
) -> tuple[list[ContentItem], list[tuple[str, int]]]:
    """
    Extract all content from the Content section.

    Supports:
    - Bullet points (-, *)
    - Numbered lists (1., 2., 3.)
    - Markdown tables
    - Code blocks (```...```)
    - Plain text paragraphs

    Returns:
        Tuple of (content_items, legacy_bullets) for backward compatibility
    """
    content_items = []
    legacy_bullets = []

    # Find the Content section - more flexible regex
    # Allow optional whitespace and newlines after "Content:"
    content_match = re.search(
        r"^\*{0,2}Content\*{0,2}:\s*(.+?)(?=^\*{0,2}(?:Graphic|SPEAKER NOTES|BACKGROUND|Sources|IMPLEMENTATION GUIDANCE|GRAPHICS)\*{0,2}:|^---\s*$|\Z)",
        content,
        re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )

    if not content_match:
        return content_items, legacy_bullets

    content_text = content_match.group(1).strip()

    # Parse tables first (they have a distinct structure)
    tables = _extract_tables(content_text)
    if tables:
        for table in tables:
            content_items.append(table)
            # Add table rows as legacy bullets for templates that don't support tables yet
            if table.headers:
                legacy_bullets.append((", ".join(table.headers), 0))
            for row in table.rows:
                legacy_bullets.append((", ".join(row), 1))
        # If content is primarily a table, we're done
        if len(tables) > 0 and len(content_text.split("\n")) < 50:
            return content_items, legacy_bullets

    # Parse code blocks
    code_blocks = _extract_code_blocks(content_text)
    for code_block in code_blocks:
        content_items.append(code_block)
        # Add code as legacy bullet
        legacy_bullets.append((f"[Code: {code_block.language or 'text'}]", 0))

    # Parse bullets and numbered lists
    bullets = _extract_bullets_and_numbers(content_text)
    content_items.extend(bullets)
    legacy_bullets.extend([(item.text, item.level) for item in bullets])

    # If no structured content found, treat as plain text
    if not content_items:
        paragraphs = _extract_plain_text(content_text)
        content_items.extend(paragraphs)
        for para in paragraphs:
            legacy_bullets.append((para.text, 0))

    return content_items, legacy_bullets


def _extract_tables(content: str) -> list[TableItem]:
    """
    Extract markdown tables from content.

    Markdown table format:
    | Header 1 | Header 2 |
    |----------|----------|
    | Cell 1   | Cell 2   |
    """
    tables = []

    # Find tables by looking for lines with pipes
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this line looks like a table header
        if "|" in line and i + 1 < len(lines) and "|" in lines[i + 1]:
            # Potential table found
            separator_line = lines[i + 1].strip()
            # Check if next line is a separator (contains dashes)
            if "-" in separator_line:
                # Extract headers (and clean markdown formatting)
                headers = [
                    _clean_markdown_formatting(cell.strip())
                    for cell in line.split("|")
                    if cell.strip()
                ]

                # Extract rows (and clean markdown formatting from cells)
                rows = []
                j = i + 2
                while j < len(lines) and "|" in lines[j]:
                    row_cells = [
                        _clean_markdown_formatting(cell.strip())
                        for cell in lines[j].split("|")
                        if cell.strip()
                    ]
                    if row_cells:
                        rows.append(row_cells)
                    j += 1

                # Create table item
                if headers and rows:
                    tables.append(TableItem(headers=headers, rows=rows))

                # Skip past this table
                i = j
                continue

        i += 1

    return tables


def _extract_code_blocks(content: str) -> list[CodeBlockItem]:
    """
    Extract code blocks from content.

    Format: ```language\ncode\n```
    """
    code_blocks = []

    # Find code blocks
    pattern = r"```(\w+)?\n(.+?)```"
    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        language = match.group(1)
        code = match.group(2).strip()
        code_blocks.append(CodeBlockItem(code=code, language=language))

    return code_blocks


def _extract_bullets_and_numbers(content: str) -> list[BulletItem]:
    """
    Extract bullet points and numbered lists from content.

    Supports:
    - Bullet points: -, *
    - Numbered lists: 1., 2., 3.
    - Indentation levels (0, 1, 2)
    """
    bullets = []

    # Remove tables and code blocks from content first
    content_cleaned = re.sub(r"\|.+?\|", "", content)  # Remove table rows
    content_cleaned = re.sub(
        r"```.*?```", "", content_cleaned, flags=re.DOTALL
    )  # Remove code blocks

    for line in content_cleaned.split("\n"):
        # Skip empty lines
        if not line.strip():
            continue

        # Match bullet points: count leading spaces, then -, *
        bullet_match = re.match(r"^( *)[-*]\s+(.+)$", line)
        if bullet_match:
            indent_spaces = len(bullet_match.group(1))
            bullet_text = _clean_markdown_formatting(bullet_match.group(2).strip())

            # Determine indentation level
            if indent_spaces < 2:
                indent_level = 0
            elif indent_spaces < 4:
                indent_level = 1
            else:
                indent_level = 2

            bullets.append(BulletItem(text=bullet_text, level=indent_level))
            continue

        # Match numbered lists
        numbered_match = re.match(r"^( *)(\d+)\.\s+(.+)$", line)
        if numbered_match:
            indent_spaces = len(numbered_match.group(1))
            bullet_text = _clean_markdown_formatting(numbered_match.group(3).strip())

            if indent_spaces < 2:
                indent_level = 0
            elif indent_spaces < 4:
                indent_level = 1
            else:
                indent_level = 2

            bullets.append(BulletItem(text=bullet_text, level=indent_level))
            continue

        # Subsection labels like **Key Principle:** within content
        if line.strip().startswith("**") and ":" in line:
            # Check if it's a major section header (skip those)
            header_match = re.match(
                r"^\*{0,2}(Graphic|SPEAKER NOTES|BACKGROUND|Sources|IMPLEMENTATION GUIDANCE|GRAPHICS|Title|Subtitle|Content)\*{0,2}:",
                line.strip(),
                re.IGNORECASE,
            )
            if not header_match:
                # It's a subsection label, include it
                clean_text = _clean_markdown_formatting(line.strip())
                bullets.append(BulletItem(text=clean_text, level=0))

    return bullets


def _extract_plain_text(content: str) -> list[TextItem]:
    """
    Extract plain text paragraphs from content.

    Used when no structured content (bullets, tables, etc.) is found.
    """
    paragraphs = []

    # Remove table and code block sections
    content_cleaned = re.sub(r"\|.+?\|", "", content)
    content_cleaned = re.sub(r"```.*?```", "", content_cleaned, flags=re.DOTALL)

    # Split into paragraphs (double newline)
    for para in content_cleaned.split("\n\n"):
        para = para.strip()
        if para and not para.startswith("**") and not para.startswith("#"):
            clean_text = _clean_markdown_formatting(para)
            # Collapse multiple spaces
            clean_text = re.sub(r"\s+", " ", clean_text)
            if clean_text:
                paragraphs.append(TextItem(text=clean_text))

    return paragraphs


def get_slides_needing_images(slides: list[Slide]) -> list[Slide]:
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


def get_slide_summary(slides: list[Slide]) -> str:
    """
    Generate a summary of the parsed presentation.

    Args:
        slides: List of parsed slides

    Returns:
        Human-readable summary string
    """
    if not slides:
        return "No slides found in presentation."

    summary_lines = [f"Parsed {len(slides)} slides:", ""]

    slides_with_graphics = get_slides_needing_images(slides)

    for slide in slides:
        has_graphic = slide in slides_with_graphics
        graphic_marker = " [HAS GRAPHIC]" if has_graphic else ""
        summary_lines.append(
            f'  Slide {slide.number}: {slide.slide_type} - "{slide.title}"{graphic_marker}'
        )

    summary_lines.extend(
        ["", f"Slides with graphics: {len(slides_with_graphics)}/{len(slides)}"]
    )

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
            print(f"Content items: {len(first_slide.content)}")
            print(f"Legacy bullets: {len(first_slide.content_bullets)}")
            if first_slide.content:
                print("First 5 content items:")
                for item in first_slide.content[:5]:
                    if isinstance(item, BulletItem):
                        indent = "  " * item.level
                        print(f"  {indent}- {item.text[:60]}")
                    elif isinstance(item, TableItem):
                        print(
                            f"  [TABLE: {len(item.headers)} cols x {len(item.rows)} rows]"
                        )
                    elif isinstance(item, CodeBlockItem):
                        print(f"  [CODE: {item.language or 'text'}]")
                    elif isinstance(item, TextItem):
                        print(f"  [TEXT: {item.text[:60]}...]")
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
