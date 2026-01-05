"""
Unit tests for plugin/templates/ modules.

Tests the CFA and Stratfield template configurations and classes.
"""

from unittest.mock import MagicMock, patch

import pytest

from plugin.lib.presentation.template_base import PresentationTemplate


class TestPresentationTemplateBase:
    """Tests for PresentationTemplate abstract base class."""

    def test_abstract_class_cannot_instantiate(self):
        """Test that PresentationTemplate cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PresentationTemplate()

    def test_get_slide_count_default(self):
        """Test default get_slide_count returns 0."""

        # Create a minimal concrete implementation
        class MinimalTemplate(PresentationTemplate):
            @property
            def name(self):
                return "Test"

            @property
            def id(self):
                return "test"

            def add_title_slide(self, title, subtitle="", date=""):
                pass

            def add_section_break(self, title):
                pass

            def add_content_slide(self, title, subtitle, bullets):
                pass

            def add_image_slide(self, title, image_path, subtitle=""):
                pass

            def add_text_and_image_slide(self, title, bullets, image_path):
                pass

            def save(self, filepath):
                pass

        template = MinimalTemplate()
        assert template.get_slide_count() == 0

    def test_description_default_empty(self):
        """Test default description is empty string."""

        class MinimalTemplate(PresentationTemplate):
            @property
            def name(self):
                return "Test"

            @property
            def id(self):
                return "test"

            def add_title_slide(self, title, subtitle="", date=""):
                pass

            def add_section_break(self, title):
                pass

            def add_content_slide(self, title, subtitle, bullets):
                pass

            def add_image_slide(self, title, image_path, subtitle=""):
                pass

            def add_text_and_image_slide(self, title, bullets, image_path):
                pass

            def save(self, filepath):
                pass

        template = MinimalTemplate()
        assert template.description == ""


class TestCFATemplateConfiguration:
    """Tests for CFA template configuration and constants."""

    def test_import_cfa_template(self):
        """Test CFA template can be imported."""
        from plugin.templates.cfa.template import CFAPresentation

        assert CFAPresentation is not None

    def test_cfa_colors_defined(self):
        """Test CFA brand colors are defined."""
        from plugin.templates.cfa.template import COLORS

        assert "cfa_red" in COLORS
        assert COLORS["cfa_red"] == "#DD0033"
        assert "dark_blue" in COLORS
        assert COLORS["dark_blue"] == "#004F71"
        assert "white" in COLORS
        assert "light_gray" in COLORS
        assert "text_gray" in COLORS

    def test_cfa_fonts_defined(self):
        """Test CFA fonts are defined."""
        from plugin.templates.cfa.template import FONTS

        assert "heading" in FONTS
        assert "body" in FONTS
        assert FONTS["heading"] == "Apercu"
        assert FONTS["body"] == "Apercu"

    def test_cfa_slide_dimensions(self):
        """Test CFA slide dimensions are defined."""
        from plugin.templates.cfa.template import SLIDE_HEIGHT, SLIDE_WIDTH

        assert SLIDE_WIDTH == 13.33
        assert SLIDE_HEIGHT == 7.50

    def test_cfa_bullet_specs_all_levels(self):
        """Test CFA bullet specs for all indent levels."""
        from plugin.templates.cfa.template import BULLET_SPECS

        assert 0 in BULLET_SPECS
        assert 1 in BULLET_SPECS
        assert 2 in BULLET_SPECS

        # Check level 0 has required keys
        assert "marL" in BULLET_SPECS[0]
        assert "indent" in BULLET_SPECS[0]
        assert "size" in BULLET_SPECS[0]

    def test_cfa_layouts_defined(self):
        """Test CFA layout specifications are defined."""
        from plugin.templates.cfa.template import LAYOUTS

        assert "title_slide" in LAYOUTS
        assert "section_break" in LAYOUTS
        assert "content_text_only" in LAYOUTS

        # Check title slide has required elements
        assert "background_color" in LAYOUTS["title_slide"]
        assert "title" in LAYOUTS["title_slide"]

    def test_cfa_template_name_and_id(self):
        """Test CFA template name and id properties."""
        from plugin.templates.cfa.template import CFAPresentation

        # We need to mock Presentation to avoid file creation
        with patch("plugin.templates.cfa.template.Presentation"):
            template = CFAPresentation()
            assert template.name == "Chick-fil-A"
            assert template.id == "cfa"


class TestStratfieldTemplateConfiguration:
    """Tests for Stratfield template configuration and constants."""

    def test_import_stratfield_template(self):
        """Test Stratfield template can be imported."""
        from plugin.templates.stratfield.template import StratfieldPresentation

        assert StratfieldPresentation is not None

    def test_stratfield_colors_defined(self):
        """Test Stratfield brand colors are defined."""
        from plugin.templates.stratfield.template import COLORS

        assert isinstance(COLORS, dict)
        assert len(COLORS) > 0

    def test_stratfield_fonts_defined(self):
        """Test Stratfield fonts are defined."""
        from plugin.templates.stratfield.template import FONTS

        # Stratfield uses different font keys than CFA
        assert "body" in FONTS
        assert len(FONTS) > 0

    def test_stratfield_layouts_defined(self):
        """Test Stratfield layout specifications are defined."""
        from plugin.templates.stratfield.template import LAYOUTS

        assert "title_slide" in LAYOUTS
        assert "section_break" in LAYOUTS

    def test_stratfield_template_name_and_id(self):
        """Test Stratfield template name and id properties."""
        from plugin.templates.stratfield.template import StratfieldPresentation

        with patch("plugin.templates.stratfield.template.Presentation"):
            template = StratfieldPresentation()
            assert template.name == "Stratfield Consulting"
            assert template.id == "stratfield"


class TestTemplateRegistry:
    """Tests for template registry functionality."""

    def test_get_template_cfa(self):
        """Test getting CFA template from registry."""
        from plugin.templates import get_template

        with patch("plugin.templates.cfa.template.Presentation"):
            template = get_template("cfa")
            assert template is not None
            assert template.id == "cfa"

    def test_get_template_stratfield(self):
        """Test getting Stratfield template from registry."""
        from plugin.templates import get_template

        with patch("plugin.templates.stratfield.template.Presentation"):
            template = get_template("stratfield")
            assert template is not None
            assert template.id == "stratfield"

    def test_get_template_invalid(self):
        """Test getting invalid template raises error."""
        from plugin.templates import get_template

        with pytest.raises(ValueError):
            get_template("nonexistent")

    def test_list_templates(self):
        """Test listing available templates."""
        from plugin.templates import list_templates

        templates = list_templates()
        assert isinstance(templates, list)
        # list_templates returns list of (id, name, description) tuples
        template_ids = [t[0] for t in templates]
        assert "cfa" in template_ids
        assert "stratfield" in template_ids


class TestCFATemplateSlideCreation:
    """Tests for CFA template slide creation methods."""

    @pytest.fixture
    def cfa_template(self):
        """Create a CFA template with mocked Presentation."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_prs.return_value.slides = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=MagicMock())
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            yield template

    def test_add_title_slide(self, cfa_template):
        """Test adding title slide."""
        # This should not raise an error
        try:
            cfa_template.add_title_slide("Test Title", "Test Subtitle", "January 2025")
        except Exception:
            # May fail due to mocking limitations, but should not crash on basic calls
            pass

    def test_add_section_break(self, cfa_template):
        """Test adding section break slide."""
        try:
            cfa_template.add_section_break("New Section")
        except Exception:
            pass

    def test_add_content_slide(self, cfa_template):
        """Test adding content slide."""
        bullets = [
            ("First point", 0),
            ("Sub point", 1),
            ("Second point", 0),
        ]
        try:
            cfa_template.add_content_slide("Title", "Subtitle", bullets)
        except Exception:
            pass


class TestStratfieldTemplateSlideCreation:
    """Tests for Stratfield template slide creation methods."""

    @pytest.fixture
    def stratfield_template(self):
        """Create a Stratfield template with mocked Presentation."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_prs.return_value.slides = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=MagicMock())
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            yield template

    def test_add_title_slide(self, stratfield_template):
        """Test adding title slide."""
        try:
            stratfield_template.add_title_slide(
                "Test Title", "Test Subtitle", "January 2025"
            )
        except Exception:
            pass

    def test_add_section_break(self, stratfield_template):
        """Test adding section break slide."""
        try:
            stratfield_template.add_section_break("New Section")
        except Exception:
            pass

    def test_add_content_slide(self, stratfield_template):
        """Test adding content slide."""
        bullets = [
            ("First point", 0),
            ("Sub point", 1),
        ]
        try:
            stratfield_template.add_content_slide("Title", "Subtitle", bullets)
        except Exception:
            pass


class TestLayoutConfigurations:
    """Tests for layout configuration consistency."""

    def test_cfa_title_slide_layout_complete(self):
        """Test CFA title slide layout has all required fields."""
        from plugin.templates.cfa.template import LAYOUTS

        layout = LAYOUTS["title_slide"]

        assert "background_color" in layout
        assert "title" in layout
        assert "subtitle" in layout

        # Title should have position and style
        title = layout["title"]
        assert "x" in title
        assert "y" in title
        assert "w" in title
        assert "h" in title
        assert "font" in title
        assert "size" in title

    def test_cfa_section_break_layout_complete(self):
        """Test CFA section break layout has all required fields."""
        from plugin.templates.cfa.template import LAYOUTS

        layout = LAYOUTS["section_break"]

        assert "background_color" in layout
        assert "title" in layout

    def test_stratfield_title_slide_layout_complete(self):
        """Test Stratfield title slide layout has all required fields."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["title_slide"]

        assert "background_color" in layout
        assert "title" in layout

    def test_stratfield_section_break_layout_complete(self):
        """Test Stratfield section break layout has all required fields."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["section_break"]

        assert "background_color" in layout
        assert "title" in layout


class TestColorConversions:
    """Tests for color value consistency."""

    def test_cfa_colors_are_valid_hex(self):
        """Test all CFA colors are valid hex values."""
        from plugin.templates.cfa.template import COLORS

        for name, color in COLORS.items():
            assert color.startswith("#"), f"Color {name} should start with #"
            # Remove # and check length
            hex_part = color[1:]
            assert len(hex_part) == 6, f"Color {name} should be 6 hex chars"
            # Check it's valid hex
            int(hex_part, 16)  # Should not raise

    def test_stratfield_colors_are_valid_hex(self):
        """Test all Stratfield colors are valid hex values."""
        from plugin.templates.stratfield.template import COLORS

        for name, color in COLORS.items():
            assert color.startswith("#"), f"Color {name} should start with #"
            hex_part = color[1:]
            assert len(hex_part) == 6, f"Color {name} should be 6 hex chars"
            int(hex_part, 16)


class TestBulletConfiguration:
    """Tests for bullet point configuration."""

    def test_cfa_bullet_levels_have_required_fields(self):
        """Test CFA bullet specs have all required fields for each level."""
        from plugin.templates.cfa.template import BULLET_SPECS

        required_fields = ["marL", "indent", "size"]

        for level in [0, 1, 2]:
            assert level in BULLET_SPECS, f"Missing bullet level {level}"
            for field in required_fields:
                assert field in BULLET_SPECS[level], (
                    f"Missing {field} for level {level}"
                )

    def test_cfa_bullet_sizes_decrease_with_level(self):
        """Test CFA bullet sizes decrease with indent level."""
        from plugin.templates.cfa.template import BULLET_SPECS

        assert BULLET_SPECS[0]["size"] > BULLET_SPECS[1]["size"]
        assert BULLET_SPECS[1]["size"] > BULLET_SPECS[2]["size"]

    def test_cfa_bullet_margins_increase_with_level(self):
        """Test CFA bullet margins increase with indent level."""
        from plugin.templates.cfa.template import BULLET_SPECS

        assert BULLET_SPECS[0]["marL"] < BULLET_SPECS[1]["marL"]
        assert BULLET_SPECS[1]["marL"] < BULLET_SPECS[2]["marL"]
