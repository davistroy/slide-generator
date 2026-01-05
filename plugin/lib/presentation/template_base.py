"""
Abstract base class for presentation templates.

All brand templates must extend this class and implement the abstract methods.
This enables easy addition of new brand templates while ensuring consistent API.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class PresentationTemplate(ABC):
    """
    Abstract base class for brand presentation templates.

    To create a new brand template:
    1. Create a new directory in templates/ (e.g., templates/mybrand/)
    2. Create template.py extending this class
    3. Implement all abstract methods
    4. Add assets to templates/mybrand/assets/
    5. Register in templates/__init__.py

    Example:
        from lib.template_base import PresentationTemplate
        from templates import register_template

        @register_template
        class MyBrandPresentation(PresentationTemplate):
            @property
            def name(self) -> str:
                return "My Brand"

            @property
            def id(self) -> str:
                return "mybrand"

            # ... implement other methods
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable template name.

        Returns:
            Display name (e.g., 'Chick-fil-A', 'Stratfield Consulting')
        """
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Template identifier (lowercase, no spaces).

        Returns:
            Short ID (e.g., 'cfa', 'stratfield')
        """
        pass

    @property
    def description(self) -> str:
        """
        Optional description of the template.

        Returns:
            Brief description of the brand/template style
        """
        return ""

    @abstractmethod
    def add_title_slide(self, title: str, subtitle: str = "", date: str = "") -> None:
        """
        Add a title/cover slide.

        Args:
            title: Main presentation title
            subtitle: Optional subtitle or tagline
            date: Optional date string
        """
        pass

    @abstractmethod
    def add_section_break(self, title: str) -> None:
        """
        Add a section divider slide.

        Args:
            title: Section title text
        """
        pass

    @abstractmethod
    def add_content_slide(
        self, title: str, subtitle: str, bullets: list[tuple[str, int]]
    ) -> None:
        """
        Add a content slide with bullet points.

        Args:
            title: Slide title
            subtitle: Slide subtitle (can be empty string)
            bullets: List of (text, level) tuples where level is 0, 1, or 2
                     Level 0 = main bullet
                     Level 1 = sub-bullet (indented)
                     Level 2 = sub-sub-bullet (double indented)

        Example:
            template.add_content_slide("Key Points", "Overview", [
                ("First main point", 0),
                ("Supporting detail", 1),
                ("Another main point", 0),
            ])
        """
        pass

    @abstractmethod
    def add_image_slide(self, title: str, image_path: str, subtitle: str = "") -> None:
        """
        Add a slide with a large image.

        Args:
            title: Slide title
            image_path: Path to image file
            subtitle: Optional subtitle/caption
        """
        pass

    @abstractmethod
    def add_text_and_image_slide(
        self, title: str, bullets: list[tuple[str, int]], image_path: str
    ) -> None:
        """
        Add a two-column slide with text and image.

        Args:
            title: Slide title (usually in text panel)
            bullets: List of (text, level) tuples for text panel
            image_path: Path to image file for image panel
        """
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        """
        Save the presentation to a file.

        Args:
            filepath: Output file path (should end in .pptx)
        """
        pass

    def get_slide_count(self) -> int:
        """
        Get the current number of slides.

        Returns:
            Number of slides in the presentation
        """
        return 0  # Override in subclass if tracking is needed

    def get_assets_dir(self) -> Path:
        """
        Get the path to this template's assets directory.

        Returns:
            Path to assets folder
        """
        # Default implementation assumes assets/ is next to the template module
        return Path(__file__).parent / "assets"
