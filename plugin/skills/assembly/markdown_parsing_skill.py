"""
Markdown Parsing Skill - Parse presentation markdown files.

Transforms markdown presentation files into structured slide data
that can be used by other skills in the workflow.
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path

from plugin.base_skill import BaseSkill, SkillInput, SkillOutput, SkillStatus
from plugin.lib.presentation.parser import (
    parse_presentation, Slide, BulletItem, TableItem, CodeBlockItem, TextItem
)


class MarkdownParsingSkill(BaseSkill):
    """
    Parse markdown presentation files into structured slide data.

    Uses plugin.lib.presentation.parser for markdown parsing.

    Input:
        - markdown_path: Path to the markdown presentation file

    Output:
        - slides: List of parsed slide dictionaries
        - slide_count: Total number of slides
        - has_graphics: Whether any slides have graphics
    """

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        return "parse-markdown"

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        return "Markdown Parsing"

    @property
    def description(self) -> str:
        """What this skill does."""
        return "Parse presentation markdown files into structured slide data"

    @property
    def version(self) -> str:
        """Skill version."""
        return "1.0.0"

    @property
    def dependencies(self) -> List[str]:
        """List of skill IDs this skill depends on."""
        return []  # No dependencies

    def validate_input(self, input_data: SkillInput) -> Tuple[bool, List[str]]:
        """
        Validate that markdown_path is provided and file exists.

        Args:
            input_data: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        markdown_path = input_data.get("markdown_path")
        if not markdown_path:
            errors.append("markdown_path is required")
            return False, errors

        path = Path(markdown_path)
        if not path.exists():
            errors.append(f"File not found: {markdown_path}")
            return False, errors

        if not path.suffix.lower() in [".md", ".markdown"]:
            errors.append(f"File must be markdown (.md): {markdown_path}")
            return False, errors

        return True, errors

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute markdown parsing.

        Args:
            input_data: Skill input containing markdown_path

        Returns:
            SkillOutput with parsed slide data
        """
        markdown_path = input_data.get("markdown_path")

        try:
            print(f"\n[*] Parsing markdown: {markdown_path}")

            # Parse the markdown file
            slides = parse_presentation(str(markdown_path))

            if not slides:
                return SkillOutput.failure_result(
                    errors=["No slides found in markdown file"],
                    metadata={"markdown_path": str(markdown_path)}
                )

            # Convert slides to dictionaries for serialization
            slides_data = [self._slide_to_dict(slide) for slide in slides]

            # Count slides with graphics
            slides_with_graphics = sum(1 for slide in slides if slide.graphic)

            print(f"   Parsed {len(slides)} slides ({slides_with_graphics} with graphics)")

            return SkillOutput.success_result(
                data={
                    "slides": slides_data,
                    "slide_count": len(slides),
                    "has_graphics": slides_with_graphics > 0,
                    "graphics_count": slides_with_graphics
                },
                artifacts=[str(markdown_path)],
                metadata={
                    "markdown_path": str(markdown_path),
                    "slide_count": len(slides),
                    "graphics_count": slides_with_graphics
                }
            )

        except FileNotFoundError as e:
            return SkillOutput.failure_result(
                errors=[f"File not found: {e}"],
                metadata={"markdown_path": str(markdown_path)}
            )
        except Exception as e:
            return SkillOutput.failure_result(
                errors=[f"Failed to parse markdown: {str(e)}"],
                metadata={
                    "markdown_path": str(markdown_path),
                    "exception_type": type(e).__name__
                }
            )

    def _slide_to_dict(self, slide: Slide) -> Dict[str, Any]:
        """
        Convert a Slide object to a dictionary.

        Args:
            slide: Slide dataclass object

        Returns:
            Dictionary representation of the slide
        """
        return {
            "number": slide.number,
            "slide_type": slide.slide_type,
            "title": slide.title,
            "subtitle": slide.subtitle,
            "content": [self._content_item_to_dict(item) for item in slide.content],
            "content_bullets": slide.content_bullets,
            "graphic": slide.graphic,
            "speaker_notes": slide.speaker_notes,
            "raw_content": slide.raw_content
        }

    def _content_item_to_dict(self, item) -> Dict[str, Any]:
        """
        Convert a ContentItem to a dictionary.

        Args:
            item: ContentItem (BulletItem, TableItem, CodeBlockItem, or TextItem)

        Returns:
            Dictionary representation with type field
        """
        if isinstance(item, BulletItem):
            return {
                "type": "bullet",
                "text": item.text,
                "level": item.level
            }
        elif isinstance(item, TableItem):
            return {
                "type": "table",
                "headers": item.headers,
                "rows": item.rows
            }
        elif isinstance(item, CodeBlockItem):
            return {
                "type": "code",
                "code": item.code,
                "language": item.language
            }
        elif isinstance(item, TextItem):
            return {
                "type": "text",
                "text": item.text
            }
        else:
            # Fallback for unknown types
            return {
                "type": "unknown",
                "raw": str(item)
            }
