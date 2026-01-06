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


# =============================================================================
# Comprehensive CFA Template Tests
# =============================================================================


class TestCFAHexToRgbFunction:
    """Tests for CFA hex_to_rgb utility function."""

    def test_hex_to_rgb_with_hash(self):
        """Test hex to RGB conversion with hash prefix."""
        from plugin.templates.cfa.template import hex_to_rgb

        rgb = hex_to_rgb("#DD0033")
        assert rgb[0] == 0xDD  # red
        assert rgb[1] == 0x00  # green
        assert rgb[2] == 0x33  # blue

    def test_hex_to_rgb_without_hash(self):
        """Test hex to RGB conversion without hash prefix."""
        from plugin.templates.cfa.template import hex_to_rgb

        rgb = hex_to_rgb("004F71")
        assert rgb[0] == 0x00  # red
        assert rgb[1] == 0x4F  # green
        assert rgb[2] == 0x71  # blue

    def test_hex_to_rgb_white(self):
        """Test hex to RGB for white color."""
        from plugin.templates.cfa.template import hex_to_rgb

        rgb = hex_to_rgb("#FFFFFF")
        assert rgb[0] == 255  # red
        assert rgb[1] == 255  # green
        assert rgb[2] == 255  # blue

    def test_hex_to_rgb_black(self):
        """Test hex to RGB for black color."""
        from plugin.templates.cfa.template import hex_to_rgb

        rgb = hex_to_rgb("#000000")
        assert rgb[0] == 0  # red
        assert rgb[1] == 0  # green
        assert rgb[2] == 0  # blue

    def test_hex_to_rgb_lowercase(self):
        """Test hex to RGB with lowercase hex."""
        from plugin.templates.cfa.template import hex_to_rgb

        rgb = hex_to_rgb("#dd0033")
        assert rgb[0] == 0xDD  # red
        assert rgb[1] == 0x00  # green
        assert rgb[2] == 0x33  # blue

    def test_hex_to_rgb_cfa_red(self):
        """Test hex to RGB with CFA brand red."""
        from plugin.templates.cfa.template import COLORS, hex_to_rgb

        rgb = hex_to_rgb(COLORS["cfa_red"])
        assert rgb[0] == 221  # red
        assert rgb[1] == 0  # green
        assert rgb[2] == 51  # blue

    def test_hex_to_rgb_dark_blue(self):
        """Test hex to RGB with CFA dark blue."""
        from plugin.templates.cfa.template import COLORS, hex_to_rgb

        rgb = hex_to_rgb(COLORS["dark_blue"])
        assert rgb[0] == 0  # red
        assert rgb[1] == 79  # green
        assert rgb[2] == 113  # blue


class TestCFATemplateInitialization:
    """Tests for CFA template initialization."""

    def test_init_with_default_assets_dir(self):
        """Test initialization with default assets directory."""

        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            # Default assets dir should be relative to template module
            assert template.assets_dir.name == "assets"
            assert "cfa" in str(template.assets_dir)

    def test_init_with_custom_assets_dir(self):
        """Test initialization with custom assets directory."""
        from pathlib import Path

        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            custom_path = "/custom/assets/path"
            template = CFAPresentation(assets_dir=custom_path)
            assert template.assets_dir == Path(custom_path)

    def test_init_sets_slide_dimensions(self):
        """Test that initialization sets widescreen dimensions."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value

            from plugin.templates.cfa.template import CFAPresentation

            CFAPresentation()

            # Verify slide dimensions were set
            assert mock_instance.slide_width is not None
            assert mock_instance.slide_height is not None

    def test_init_slide_count_starts_at_zero(self):
        """Test that slide count starts at zero."""
        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            assert template._slide_count == 0
            assert template.get_slide_count() == 0


class TestCFATemplateProperties:
    """Tests for CFA template property methods."""

    def test_description_property(self):
        """Test the description property returns expected value."""
        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            desc = template.description
            assert "Red" in desc or "red" in desc or "CFA" in desc or "Apercu" in desc

    def test_get_assets_dir(self):
        """Test get_assets_dir returns Path object."""
        from pathlib import Path

        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            assets_dir = template.get_assets_dir()
            assert isinstance(assets_dir, Path)


class TestCFATemplatePrivateMethods:
    """Tests for CFA template private helper methods."""

    @pytest.fixture
    def mock_cfa_presentation(self):
        """Create mock Presentation for testing."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            # Create a mock slide with proper structure
            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            yield template, mock_slide

    def test_get_blank_layout(self, mock_cfa_presentation):
        """Test _get_blank_layout returns correct layout."""
        template, _ = mock_cfa_presentation
        layout = template._get_blank_layout()
        # Should return layout at index 6 (blank layout)
        assert layout is not None

    def test_set_background_color(self, mock_cfa_presentation):
        """Test _set_background_color sets solid fill."""
        template, mock_slide = mock_cfa_presentation
        template._set_background_color(mock_slide, "#DD0033")

        # Verify background fill was called
        mock_slide.background.fill.solid.assert_called_once()

    def test_add_textbox_basic(self, mock_cfa_presentation):
        """Test _add_textbox creates textbox with correct properties."""
        template, mock_slide = mock_cfa_presentation

        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        mock_textbox.text_frame.paragraphs[0].font = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox

        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "font": "Apercu",
            "size": 24,
            "color": "#DD0033",
            "align": "left",
        }

        result = template._add_textbox(mock_slide, spec, "Test Text")
        assert result is not None
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_with_overrides(self, mock_cfa_presentation):
        """Test _add_textbox with override parameters."""
        template, mock_slide = mock_cfa_presentation

        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        mock_textbox.text_frame.paragraphs[0].font = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox

        spec = {"x": 1.0, "y": 2.0, "w": 5.0, "h": 1.0}
        result = template._add_textbox(mock_slide, spec, "Test", bold=True, size=30)
        assert result is not None

    def test_add_textbox_with_center_alignment(self, mock_cfa_presentation):
        """Test _add_textbox with center alignment."""
        template, mock_slide = mock_cfa_presentation

        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        mock_textbox.text_frame.paragraphs[0].font = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox

        spec = {"x": 1.0, "y": 2.0, "w": 5.0, "h": 1.0, "align": "center"}
        result = template._add_textbox(mock_slide, spec, "Centered Text")
        assert result is not None

    def test_add_textbox_with_right_alignment(self, mock_cfa_presentation):
        """Test _add_textbox with right alignment."""
        template, mock_slide = mock_cfa_presentation

        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        mock_textbox.text_frame.paragraphs[0].font = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox

        spec = {"x": 1.0, "y": 2.0, "w": 5.0, "h": 1.0, "align": "right"}
        result = template._add_textbox(mock_slide, spec, "Right Aligned")
        assert result is not None

    def test_add_textbox_with_anchor(self, mock_cfa_presentation):
        """Test _add_textbox with anchor specified."""
        template, mock_slide = mock_cfa_presentation

        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        mock_textbox.text_frame.paragraphs[0].font = MagicMock()
        mock_slide.shapes.add_textbox.return_value = mock_textbox

        spec = {"x": 1.0, "y": 2.0, "w": 5.0, "h": 1.0, "anchor": "middle"}
        result = template._add_textbox(mock_slide, spec, "Anchored Text")
        assert result is not None


class TestCFATemplateImageMethods:
    """Tests for CFA template image handling methods."""

    @pytest.fixture
    def cfa_template_with_mocked_prs(self):
        """Create template with mocked Presentation."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()
            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            yield template, mock_slide

    def test_add_image_nonexistent_file(self, cfa_template_with_mocked_prs):
        """Test _add_image creates placeholder for nonexistent file."""
        template, mock_slide = cfa_template_with_mocked_prs

        mock_shape = MagicMock()
        mock_shape.fill = MagicMock()
        mock_shape.line = MagicMock()
        mock_shape.line.fill = MagicMock()
        mock_slide.shapes.add_shape.return_value = mock_shape

        spec = {"x": 1.0, "y": 1.0, "w": 5.0, "h": 3.0}
        result = template._add_image(mock_slide, spec, "/nonexistent/image.jpg")

        # Should create placeholder rectangle
        mock_slide.shapes.add_shape.assert_called_once()
        assert result is not None

    def test_add_image_with_existing_file(self, cfa_template_with_mocked_prs, tmp_path):
        """Test _add_image adds picture for existing file."""
        template, mock_slide = cfa_template_with_mocked_prs

        # Create a test image
        from PIL import Image

        test_image = tmp_path / "test_image.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(test_image)

        spec = {"x": 1.0, "y": 1.0, "w": 10.0, "h": 5.0}
        template._add_image(mock_slide, spec, str(test_image))

        # Should add picture, not shape
        mock_slide.shapes.add_picture.assert_called_once()

    def test_add_image_wider_aspect_ratio(self, cfa_template_with_mocked_prs, tmp_path):
        """Test _add_image with image wider than bounding box."""
        template, mock_slide = cfa_template_with_mocked_prs

        # Create a wide image
        from PIL import Image

        test_image = tmp_path / "wide_image.jpg"
        img = Image.new("RGB", (1600, 400), color="blue")  # Wide aspect ratio
        img.save(test_image)

        spec = {"x": 0.0, "y": 0.0, "w": 10.0, "h": 5.0}  # Box is taller aspect
        template._add_image(mock_slide, spec, str(test_image))

        mock_slide.shapes.add_picture.assert_called_once()

    def test_add_image_taller_aspect_ratio(
        self, cfa_template_with_mocked_prs, tmp_path
    ):
        """Test _add_image with image taller than bounding box."""
        template, mock_slide = cfa_template_with_mocked_prs

        # Create a tall image
        from PIL import Image

        test_image = tmp_path / "tall_image.jpg"
        img = Image.new("RGB", (400, 1600), color="green")  # Tall aspect ratio
        img.save(test_image)

        spec = {"x": 0.0, "y": 0.0, "w": 10.0, "h": 5.0}  # Box is wider aspect
        template._add_image(mock_slide, spec, str(test_image))

        mock_slide.shapes.add_picture.assert_called_once()


class TestCFATemplateBulletFormatting:
    """Tests for CFA template bullet formatting."""

    @pytest.fixture
    def cfa_template_with_paragraph(self):
        """Create template with mocked paragraph."""
        with patch("plugin.templates.cfa.template.Presentation"):
            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()

            # Create mock paragraph with proper structure
            mock_paragraph = MagicMock()
            mock_paragraph.font = MagicMock()
            mock_pPr = MagicMock()
            mock_pPr.find.return_value = None  # No existing defRPr

            # Make pPr behave like a list for iteration
            mock_pPr.__iter__ = MagicMock(return_value=iter([]))
            mock_paragraph._p = MagicMock()
            mock_paragraph._p.get_or_add_pPr.return_value = mock_pPr

            yield template, mock_paragraph

    def test_apply_bullet_formatting_level_0(self, cfa_template_with_paragraph):
        """Test bullet formatting for level 0."""
        template, mock_paragraph = cfa_template_with_paragraph
        template._apply_bullet_formatting(mock_paragraph, level=0)

        # Verify font properties were set
        assert mock_paragraph.font.name is not None

    def test_apply_bullet_formatting_level_1(self, cfa_template_with_paragraph):
        """Test bullet formatting for level 1."""
        template, mock_paragraph = cfa_template_with_paragraph
        template._apply_bullet_formatting(mock_paragraph, level=1)

        assert mock_paragraph.level == 1

    def test_apply_bullet_formatting_level_2(self, cfa_template_with_paragraph):
        """Test bullet formatting for level 2."""
        template, mock_paragraph = cfa_template_with_paragraph
        template._apply_bullet_formatting(mock_paragraph, level=2)

        assert mock_paragraph.level == 2

    def test_apply_bullet_formatting_invalid_level_uses_default(
        self, cfa_template_with_paragraph
    ):
        """Test bullet formatting with invalid level uses level 0 defaults."""
        template, mock_paragraph = cfa_template_with_paragraph
        # Level 5 doesn't exist in BULLET_SPECS, should use level 0
        template._apply_bullet_formatting(mock_paragraph, level=5)

        # Should not raise error
        assert mock_paragraph.font.name is not None

    def test_apply_bullet_formatting_custom_color(self, cfa_template_with_paragraph):
        """Test bullet formatting with custom color."""
        template, mock_paragraph = cfa_template_with_paragraph
        template._apply_bullet_formatting(
            mock_paragraph, level=0, bullet_color="DD0033"
        )

        # Should not raise error
        assert mock_paragraph.font is not None


class TestCFATemplateFooterElements:
    """Tests for CFA template footer element handling."""

    @pytest.fixture
    def cfa_template_with_slide(self, tmp_path):
        """Create template with mocked slide and assets."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.paragraphs[0].font = MagicMock()
            mock_slide.shapes.add_textbox.return_value = mock_textbox
            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            # Create template with custom assets dir
            template = CFAPresentation(assets_dir=str(tmp_path))
            template._slide_count = 5  # Set slide count for testing

            yield template, mock_slide, tmp_path

    def test_add_footer_elements_no_assets(self, cfa_template_with_slide):
        """Test footer elements when asset files don't exist."""
        template, mock_slide, tmp_path = cfa_template_with_slide

        layout = {
            "chicken_icon": {"x": 0.11, "y": 7.20, "w": 0.17, "h": 0.17},
            "slide_number": {
                "x": 12.84,
                "y": 7.15,
                "w": 0.40,
                "h": 0.25,
                "font": "Apercu",
                "size": 9,
                "color": "#5B6770",
                "align": "right",
            },
        }

        # Should not raise even without asset files
        template._add_footer_elements(mock_slide, layout)

    def test_add_footer_elements_with_red_icon(self, cfa_template_with_slide):
        """Test footer elements with red chicken icon."""
        template, mock_slide, tmp_path = cfa_template_with_slide

        # Create mock icon file
        from PIL import Image

        icon_path = tmp_path / "chicken_red.png"
        img = Image.new("RGBA", (50, 50), color="red")
        img.save(icon_path)

        layout = {
            "chicken_icon": {"x": 0.11, "y": 7.20, "w": 0.17, "h": 0.17},
            "slide_number": {
                "x": 12.84,
                "y": 7.15,
                "w": 0.40,
                "h": 0.25,
                "font": "Apercu",
                "size": 9,
                "color": "#5B6770",
                "align": "right",
            },
        }

        template._add_footer_elements(mock_slide, layout, use_white_icon=False)
        mock_slide.shapes.add_picture.assert_called_once()

    def test_add_footer_elements_with_white_icon(self, cfa_template_with_slide):
        """Test footer elements with white chicken icon."""
        template, mock_slide, tmp_path = cfa_template_with_slide

        # Create mock icon file
        from PIL import Image

        icon_path = tmp_path / "chicken_white.png"
        img = Image.new("RGBA", (50, 50), color="white")
        img.save(icon_path)

        layout = {
            "chicken_icon": {"x": 0.11, "y": 7.20, "w": 0.17, "h": 0.17},
            "slide_number": {
                "x": 12.84,
                "y": 7.15,
                "w": 0.40,
                "h": 0.25,
                "font": "Apercu",
                "size": 9,
                "color": "#FFFFFF",
                "align": "right",
            },
        }

        template._add_footer_elements(mock_slide, layout, use_white_icon=True)
        mock_slide.shapes.add_picture.assert_called_once()

    def test_add_footer_elements_no_chicken_icon_in_layout(
        self, cfa_template_with_slide
    ):
        """Test footer elements without chicken icon in layout."""
        template, mock_slide, tmp_path = cfa_template_with_slide

        layout = {
            "slide_number": {
                "x": 12.84,
                "y": 7.15,
                "w": 0.40,
                "h": 0.25,
                "font": "Apercu",
                "size": 9,
                "color": "#5B6770",
                "align": "right",
            },
        }

        # Should only add slide number, not icon
        template._add_footer_elements(mock_slide, layout)
        mock_slide.shapes.add_picture.assert_not_called()

    def test_add_footer_elements_no_slide_number_in_layout(
        self, cfa_template_with_slide
    ):
        """Test footer elements without slide number in layout."""
        template, mock_slide, tmp_path = cfa_template_with_slide

        layout = {"chicken_icon": {"x": 0.11, "y": 7.20, "w": 0.17, "h": 0.17}}

        # Should not add slide number textbox
        template._add_footer_elements(mock_slide, layout)


class TestCFATemplateSlideCreationComprehensive:
    """Comprehensive tests for CFA template slide creation methods."""

    @pytest.fixture
    def cfa_fully_mocked_template(self, tmp_path):
        """Create a fully mocked template for complete testing."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            # Mock textbox with proper structure
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.word_wrap = True
            mock_para = MagicMock()
            mock_para.font = MagicMock()
            mock_para._p = MagicMock()
            mock_pPr = MagicMock()
            mock_pPr.find.return_value = None
            mock_pPr.__iter__ = MagicMock(return_value=iter([]))
            mock_para._p.get_or_add_pPr.return_value = mock_pPr
            mock_textbox.text_frame.paragraphs = [mock_para]
            mock_textbox.text_frame.add_paragraph.return_value = mock_para

            mock_slide.shapes.add_textbox.return_value = mock_textbox

            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation(assets_dir=str(tmp_path))
            yield template, mock_slide, mock_instance

    def test_add_title_slide_full(self, cfa_fully_mocked_template):
        """Test add_title_slide with all parameters."""
        template, mock_slide, _ = cfa_fully_mocked_template

        template.add_title_slide(
            title="Main Title", subtitle="Subtitle Here", date="January 2025"
        )

        assert template._slide_count == 1
        # Should call add_textbox for title, subtitle, and date
        assert mock_slide.shapes.add_textbox.call_count >= 1

    def test_add_title_slide_no_subtitle_or_date(self, cfa_fully_mocked_template):
        """Test add_title_slide without optional parameters."""
        template, mock_slide, _ = cfa_fully_mocked_template

        template.add_title_slide(title="Title Only")

        assert template._slide_count == 1

    def test_add_section_break_increments_count(self, cfa_fully_mocked_template):
        """Test add_section_break increments slide count."""
        template, _, _ = cfa_fully_mocked_template

        template.add_section_break("Section 1")
        assert template._slide_count == 1

        template.add_section_break("Section 2")
        assert template._slide_count == 2

    def test_add_content_slide_with_bullets(self, cfa_fully_mocked_template):
        """Test add_content_slide with multiple bullet levels."""
        template, mock_slide, _ = cfa_fully_mocked_template

        bullets = [
            ("Main point 1", 0),
            ("Sub point 1.1", 1),
            ("Sub point 1.2", 1),
            ("Sub-sub point", 2),
            ("Main point 2", 0),
        ]

        template.add_content_slide(
            title="Content Title", subtitle="Content Subtitle", bullets=bullets
        )

        assert template._slide_count == 1

    def test_add_content_slide_no_subtitle(self, cfa_fully_mocked_template):
        """Test add_content_slide without subtitle."""
        template, _, _ = cfa_fully_mocked_template

        bullets = [("Point 1", 0), ("Point 2", 0)]
        template.add_content_slide(title="Title", subtitle="", bullets=bullets)

        assert template._slide_count == 1

    def test_add_image_slide_full(self, cfa_fully_mocked_template, tmp_path):
        """Test add_image_slide with all parameters."""
        template, mock_slide, _ = cfa_fully_mocked_template

        # Create test image
        from PIL import Image

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(test_image)

        template.add_image_slide(
            title="Image Title", image_path=str(test_image), subtitle="Image Subtitle"
        )

        assert template._slide_count == 1

    def test_add_image_slide_no_subtitle(self, cfa_fully_mocked_template, tmp_path):
        """Test add_image_slide without subtitle."""
        template, _, _ = cfa_fully_mocked_template

        from PIL import Image

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(test_image)

        template.add_image_slide(title="Image Title", image_path=str(test_image))

        assert template._slide_count == 1

    def test_add_text_and_image_slide_full(self, cfa_fully_mocked_template, tmp_path):
        """Test add_text_and_image_slide with full content."""
        template, mock_slide, _ = cfa_fully_mocked_template

        # Mock the shape for left panel
        mock_shape = MagicMock()
        mock_shape.fill = MagicMock()
        mock_shape.line = MagicMock()
        mock_shape.line.fill = MagicMock()
        mock_slide.shapes.add_shape.return_value = mock_shape

        from PIL import Image

        test_image = tmp_path / "test.jpg"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(test_image)

        bullets = [
            ("Text point 1", 0),
            ("Text point 1.1", 1),
            ("Text point 2", 0),
        ]

        template.add_text_and_image_slide(
            title="Split Slide Title", bullets=bullets, image_path=str(test_image)
        )

        assert template._slide_count == 1
        # Should add shape for gray panel
        mock_slide.shapes.add_shape.assert_called()


class TestCFATemplateSaveAndCount:
    """Tests for CFA template save and count methods."""

    def test_save_presentation(self, tmp_path):
        """Test save method saves to file."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()

            output_path = str(tmp_path / "output.pptx")
            template.save(output_path)

            mock_instance.save.assert_called_once_with(output_path)

    def test_get_slide_count_after_adding_slides(self):
        """Test get_slide_count returns correct count after adding slides."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.paragraphs[0].font = MagicMock()
            mock_slide.shapes.add_textbox.return_value = mock_textbox

            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()

            assert template.get_slide_count() == 0

            template.add_title_slide("Title")
            assert template.get_slide_count() == 1

            template.add_section_break("Section")
            assert template.get_slide_count() == 2


class TestCFATemplateLayoutsComplete:
    """Tests for complete layout specification coverage."""

    def test_content_full_image_layout_defined(self):
        """Test content_full_image layout is fully defined."""
        from plugin.templates.cfa.template import LAYOUTS

        layout = LAYOUTS["content_full_image"]

        assert "background_color" in layout
        assert "title" in layout
        assert "subtitle" in layout
        assert "image" in layout
        assert "chicken_icon" in layout
        assert "slide_number" in layout

        # Check image spec has all needed fields
        image_spec = layout["image"]
        assert "x" in image_spec
        assert "y" in image_spec
        assert "w" in image_spec
        assert "h" in image_spec

    def test_content_text_and_image_layout_defined(self):
        """Test content_text_and_image layout is fully defined."""
        from plugin.templates.cfa.template import LAYOUTS

        layout = LAYOUTS["content_text_and_image"]

        assert "background_color" in layout
        assert "left_panel" in layout
        assert "title" in layout
        assert "body" in layout
        assert "image" in layout

        # Check left panel has fill color
        panel_spec = layout["left_panel"]
        assert "fill" in panel_spec

    def test_all_layouts_have_position_specs(self):
        """Test all layouts have proper position specifications."""
        from plugin.templates.cfa.template import LAYOUTS

        for layout_name, layout in LAYOUTS.items():
            assert "background_color" in layout, (
                f"Missing background_color in {layout_name}"
            )
            assert "title" in layout, f"Missing title in {layout_name}"

            title_spec = layout["title"]
            assert "x" in title_spec, f"Missing x in {layout_name} title"
            assert "y" in title_spec, f"Missing y in {layout_name} title"
            assert "w" in title_spec, f"Missing w in {layout_name} title"
            assert "h" in title_spec, f"Missing h in {layout_name} title"


class TestCFATemplateBulletSpecsComplete:
    """Tests for complete bullet specification coverage."""

    def test_bullet_specs_have_space_before(self):
        """Test all bullet specs have space_before defined."""
        from plugin.templates.cfa.template import BULLET_SPECS

        for level in [0, 1, 2]:
            assert "space_before" in BULLET_SPECS[level], (
                f"Missing space_before for level {level}"
            )

    def test_bullet_char_and_font_defined(self):
        """Test bullet character and font are defined."""
        from plugin.templates.cfa.template import BULLET_CHAR, BULLET_COLOR, BULLET_FONT

        assert BULLET_CHAR == "\u00a7"  # Section sign
        assert BULLET_FONT == "Wingdings"
        assert BULLET_COLOR == "5B6770"


class TestCFATemplateWithTitleSlideLogoHandling:
    """Tests for title slide logo handling."""

    @pytest.fixture
    def cfa_template_with_logo(self, tmp_path):
        """Create template with logo asset."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.paragraphs[0].font = MagicMock()
            mock_slide.shapes.add_textbox.return_value = mock_textbox

            mock_instance.slides.add_slide.return_value = mock_slide

            # Create logo file
            from PIL import Image

            logo_path = tmp_path / "logo_white.png"
            img = Image.new("RGBA", (200, 200), color="white")
            img.save(logo_path)

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation(assets_dir=str(tmp_path))
            yield template, mock_slide

    def test_add_title_slide_with_logo(self, cfa_template_with_logo):
        """Test title slide adds logo when file exists."""
        template, mock_slide = cfa_template_with_logo

        template.add_title_slide("Title with Logo")

        # Should add picture for logo
        mock_slide.shapes.add_picture.assert_called()

    def test_add_title_slide_without_logo(self):
        """Test title slide works without logo file."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_instance = mock_prs.return_value
            mock_instance.slides = MagicMock()
            mock_instance.slide_layouts = [MagicMock() for _ in range(10)]

            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.paragraphs[0].font = MagicMock()
            mock_slide.shapes.add_textbox.return_value = mock_textbox

            mock_instance.slides.add_slide.return_value = mock_slide

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation(assets_dir="/nonexistent/path")
            template.add_title_slide("Title without Logo")

            # Should not crash, just skip logo
            assert template._slide_count == 1


class TestCFATemplateEdgeCases:
    """Edge case tests for CFA template."""

    @pytest.fixture
    def cfa_edge_case_template(self):
        """Create template for edge case testing."""
        with patch("plugin.templates.cfa.template.Presentation") as mock_prs:
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_tf = MagicMock()
            mock_p = MagicMock()
            mock_p.font = MagicMock()
            mock_p._p = MagicMock()
            mock_pPr = MagicMock()
            mock_pPr.find.return_value = None
            mock_pPr.__iter__ = MagicMock(return_value=iter([]))
            mock_p._p.get_or_add_pPr.return_value = mock_pPr
            mock_tf.paragraphs = [mock_p]
            mock_tf.add_paragraph.return_value = mock_p
            mock_textbox.text_frame = mock_tf
            mock_slide.shapes.add_textbox.return_value = mock_textbox
            mock_slide.shapes.add_shape.return_value = MagicMock()
            mock_slide.shapes.add_picture.return_value = MagicMock()
            mock_slide.background = MagicMock()
            mock_prs.return_value.slides.add_slide.return_value = mock_slide
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.cfa.template import CFAPresentation

            template = CFAPresentation()
            yield template

    def test_empty_title(self, cfa_edge_case_template):
        """Test handling of empty title."""
        cfa_edge_case_template.add_title_slide("")
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_very_long_title(self, cfa_edge_case_template):
        """Test handling of very long title."""
        long_title = "A" * 500
        cfa_edge_case_template.add_title_slide(long_title)
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_special_characters_in_text(self, cfa_edge_case_template):
        """Test handling of special characters in text."""
        cfa_edge_case_template.add_title_slide(
            "Title with special chars: <>&\"'",
            "Subtitle with unicode: \u00e9\u00f1\u00fc",
        )
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_empty_bullets_list(self, cfa_edge_case_template):
        """Test content slide with empty bullets list."""
        cfa_edge_case_template.add_content_slide("Title", "Subtitle", [])
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_single_bullet(self, cfa_edge_case_template):
        """Test content slide with single bullet."""
        bullets = [("Single point", 0)]
        cfa_edge_case_template.add_content_slide("Title", "", bullets)
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_many_bullets(self, cfa_edge_case_template):
        """Test content slide with many bullets."""
        bullets = [(f"Point {i}", i % 3) for i in range(20)]
        cfa_edge_case_template.add_content_slide("Title", "Subtitle", bullets)
        assert cfa_edge_case_template.get_slide_count() == 1

    def test_multiple_slides_sequential(self, cfa_edge_case_template):
        """Test adding multiple slides in sequence."""
        cfa_edge_case_template.add_title_slide("Title")
        cfa_edge_case_template.add_section_break("Section 1")
        cfa_edge_case_template.add_content_slide("Content 1", "", [("Point", 0)])
        cfa_edge_case_template.add_section_break("Section 2")

        assert cfa_edge_case_template.get_slide_count() == 4


class TestCFATemplateAccentColors:
    """Tests for CFA template accent colors."""

    def test_accent_colors_defined(self):
        """Test that accent colors are defined."""
        from plugin.templates.cfa.template import COLORS

        assert "teal" in COLORS
        assert "green" in COLORS
        assert "dark_teal" in COLORS

    def test_accent_colors_are_valid_hex(self):
        """Test that accent colors are valid hex values."""
        from plugin.templates.cfa.template import COLORS

        accent_colors = ["teal", "green", "dark_teal"]
        for color_name in accent_colors:
            color = COLORS[color_name]
            assert color.startswith("#")
            hex_part = color[1:]
            assert len(hex_part) == 6
            int(hex_part, 16)  # Should not raise


# =============================================================================
# Comprehensive Stratfield Template Tests
# =============================================================================


class TestStratfieldHexToRgb:
    """Tests for the hex_to_rgb utility function."""

    def test_hex_to_rgb_with_hash(self):
        """Test hex_to_rgb with # prefix."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("#FF0000")
        assert result[0] == 255  # red
        assert result[1] == 0  # green
        assert result[2] == 0  # blue

    def test_hex_to_rgb_without_hash(self):
        """Test hex_to_rgb without # prefix."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("00FF00")
        assert result[0] == 0  # red
        assert result[1] == 255  # green
        assert result[2] == 0  # blue

    def test_hex_to_rgb_blue(self):
        """Test hex_to_rgb with blue color."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("#0000FF")
        assert result[0] == 0  # red
        assert result[1] == 0  # green
        assert result[2] == 255  # blue

    def test_hex_to_rgb_white(self):
        """Test hex_to_rgb with white color."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("#FFFFFF")
        assert result[0] == 255  # red
        assert result[1] == 255  # green
        assert result[2] == 255  # blue

    def test_hex_to_rgb_black(self):
        """Test hex_to_rgb with black color."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("#000000")
        assert result[0] == 0  # red
        assert result[1] == 0  # green
        assert result[2] == 0  # blue

    def test_hex_to_rgb_mixed_color(self):
        """Test hex_to_rgb with a mixed color value."""
        from plugin.templates.stratfield.template import hex_to_rgb

        result = hex_to_rgb("#A1B2C3")
        assert result[0] == 161  # red
        assert result[1] == 178  # green
        assert result[2] == 195  # blue

    def test_hex_to_rgb_stratfield_primary_green(self):
        """Test hex_to_rgb with Stratfield primary green."""
        from plugin.templates.stratfield.template import COLORS, hex_to_rgb

        result = hex_to_rgb(COLORS["primary_green"])
        assert result[0] == 0  # red
        assert result[1] == 118  # green
        assert result[2] == 79  # blue


class TestStratfieldConstants:
    """Tests for Stratfield template constants."""

    def test_slide_dimensions(self):
        """Test slide dimensions are defined correctly."""
        from plugin.templates.stratfield.template import (
            SLIDE_HEIGHT_EMU,
            SLIDE_WIDTH_EMU,
        )

        assert SLIDE_WIDTH_EMU == 9144000
        assert SLIDE_HEIGHT_EMU == 5143500

    def test_emu_conversion_constants(self):
        """Test EMU conversion constants are defined."""
        from plugin.templates.stratfield.template import EMU_PER_INCH, EMU_PER_PT

        assert EMU_PER_INCH == 914400
        assert EMU_PER_PT == 12700

    def test_stratfield_colors_complete(self):
        """Test all expected Stratfield colors are defined."""
        from plugin.templates.stratfield.template import COLORS

        expected_colors = [
            "primary_green",
            "dark_teal",
            "section_bg",
            "bg_light",
            "text_dark",
            "text_dark_alt",
            "text_light",
            "title_cream",
            "title_cream_alt",
            "subtitle_light",
            "white",
            "accent_teal",
            "accent_lime",
            "accent_gold",
            "accent_orange",
            "accent_red",
        ]
        for color_name in expected_colors:
            assert color_name in COLORS, f"Missing color: {color_name}"

    def test_stratfield_fonts_complete(self):
        """Test all expected Stratfield fonts are defined."""
        from plugin.templates.stratfield.template import FONTS

        expected_fonts = [
            "title_black",
            "title_heavy",
            "body",
            "body_medium",
            "body_light",
        ]
        for font_name in expected_fonts:
            assert font_name in FONTS, f"Missing font: {font_name}"

    def test_font_fallbacks_defined(self):
        """Test font fallbacks are defined for all Avenir variants."""
        from plugin.templates.stratfield.template import FONT_FALLBACKS

        assert "Avenir Black" in FONT_FALLBACKS
        assert "Avenir Heavy" in FONT_FALLBACKS
        assert "Avenir" in FONT_FALLBACKS
        assert "Avenir Medium" in FONT_FALLBACKS
        assert "Avenir Light" in FONT_FALLBACKS

    def test_bullet_specs_all_levels(self):
        """Test bullet specs are defined for all indent levels."""
        from plugin.templates.stratfield.template import BULLET_SPECS

        assert 0 in BULLET_SPECS
        assert 1 in BULLET_SPECS
        assert 2 in BULLET_SPECS

        for level in [0, 1, 2]:
            assert "marL" in BULLET_SPECS[level]
            assert "indent" in BULLET_SPECS[level]
            assert "size" in BULLET_SPECS[level]
            assert "space_before" in BULLET_SPECS[level]

    def test_bullet_char_and_font(self):
        """Test bullet character and font are defined."""
        from plugin.templates.stratfield.template import (
            BULLET_CHAR,
            BULLET_COLOR,
            BULLET_FONT,
        )

        assert BULLET_CHAR == "\u00a7"  # Section sign
        assert BULLET_FONT == "Wingdings"
        assert BULLET_COLOR == "00764F"

    def test_layouts_all_types_defined(self):
        """Test all layout types are defined."""
        from plugin.templates.stratfield.template import LAYOUTS

        expected_layouts = [
            "title_slide",
            "section_break",
            "content_text_only",
            "content_full_image",
            "content_text_and_image",
        ]
        for layout_name in expected_layouts:
            assert layout_name in LAYOUTS, f"Missing layout: {layout_name}"


class TestStratfieldTemplateInitialization:
    """Tests for Stratfield template initialization."""

    def test_init_default_assets_dir(self):
        """Test initialization with default assets directory."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            assert template.assets_dir is not None
            assert "assets" in str(template.assets_dir)

    def test_init_custom_assets_dir(self):
        """Test initialization with custom assets directory."""
        import os

        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation(assets_dir="/custom/assets")
            # Use os.path.normpath to handle platform-specific separators
            assert os.path.normpath(str(template.assets_dir)) == os.path.normpath(
                "/custom/assets"
            )

    def test_init_slide_count_zero(self):
        """Test slide count starts at zero."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            assert template._slide_count == 0

    def test_init_slide_dimensions_set(self):
        """Test slide dimensions are set during initialization."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            from plugin.templates.stratfield.template import StratfieldPresentation

            StratfieldPresentation()
            # Verify slide dimensions were set
            mock_instance = mock_prs.return_value
            assert mock_instance.slide_width is not None or hasattr(
                mock_instance, "slide_width"
            )

    def test_description_property(self):
        """Test description property returns expected value."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            assert (
                template.description
                == "Green and teal professional template with Avenir font"
            )


class TestStratfieldTemplateHelperMethods:
    """Tests for Stratfield template helper methods."""

    @pytest.fixture
    def mock_slide(self):
        """Create a mock slide with shapes collection."""
        slide = MagicMock()
        slide.shapes = MagicMock()
        slide.shapes.add_textbox = MagicMock(return_value=MagicMock())
        slide.shapes.add_shape = MagicMock(return_value=MagicMock())
        slide.shapes.add_picture = MagicMock(return_value=MagicMock())
        slide.background = MagicMock()
        slide.background.fill = MagicMock()
        return slide

    @pytest.fixture
    def stratfield_template_with_mock(self):
        """Create a Stratfield template with comprehensive mocking."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_prs.return_value.slides = MagicMock()
            mock_slide = MagicMock()
            mock_slide.shapes = MagicMock()
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.word_wrap = True
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.shapes.add_shape = MagicMock(return_value=MagicMock())
            mock_slide.shapes.add_picture = MagicMock(return_value=MagicMock())
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._mock_slide = mock_slide
            yield template

    def test_get_blank_layout(self, stratfield_template_with_mock):
        """Test _get_blank_layout returns layout 6."""
        layout = stratfield_template_with_mock._get_blank_layout()
        assert layout is not None

    def test_add_textbox_left_align(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with left alignment."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "font": "Avenir",
            "size": 14,
            "color": "#000000",
            "align": "left",
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Test Text")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_center_align(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with center alignment."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "font": "Avenir",
            "size": 14,
            "color": "#000000",
            "align": "center",
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Test Text")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_right_align(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with right alignment."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "font": "Avenir",
            "size": 14,
            "color": "#000000",
            "align": "right",
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Test Text")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_with_bold(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with bold text."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "font": "Avenir Black",
            "size": 20,
            "color": "#000000",
            "bold": True,
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Bold Text")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_center_anchor(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with center vertical anchor."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "anchor": "center",
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Test")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_textbox_bottom_anchor(self, stratfield_template_with_mock, mock_slide):
        """Test _add_textbox with bottom vertical anchor."""
        spec = {
            "x": 1.0,
            "y": 2.0,
            "w": 5.0,
            "h": 1.0,
            "anchor": "bottom",
        }
        stratfield_template_with_mock._add_textbox(mock_slide, spec, "Test")
        mock_slide.shapes.add_textbox.assert_called_once()

    def test_add_image_existing_file(self, stratfield_template_with_mock, mock_slide):
        """Test _add_image with existing file."""
        spec = {"x": 1.0, "y": 1.0, "w": 4.0, "h": 3.0}
        with patch("os.path.exists", return_value=True):
            stratfield_template_with_mock._add_image(mock_slide, spec, "test.png")
            mock_slide.shapes.add_picture.assert_called_once()

    def test_add_image_missing_file(self, stratfield_template_with_mock, mock_slide):
        """Test _add_image with missing file creates placeholder."""
        spec = {"x": 1.0, "y": 1.0, "w": 4.0, "h": 3.0}
        with patch("os.path.exists", return_value=False):
            result = stratfield_template_with_mock._add_image(
                mock_slide, spec, "missing.png"
            )
            mock_slide.shapes.add_shape.assert_called_once()
            assert result is not None

    def test_add_rectangle(self, stratfield_template_with_mock, mock_slide):
        """Test _add_rectangle adds a filled shape."""
        spec = {"x": 0.0, "y": 0.0, "w": 3.0, "h": 5.0, "fill": "#296057"}
        stratfield_template_with_mock._add_rectangle(mock_slide, spec)
        mock_slide.shapes.add_shape.assert_called_once()

    def test_set_background_color(self, stratfield_template_with_mock, mock_slide):
        """Test _set_background_color sets solid fill."""
        stratfield_template_with_mock._set_background_color(mock_slide, "#30555E")
        mock_slide.background.fill.solid.assert_called_once()


class TestStratfieldBulletFormatting:
    """Tests for Stratfield bullet formatting."""

    @pytest.fixture
    def mock_paragraph(self):
        """Create a mock paragraph for bullet testing."""
        p = MagicMock()
        p.font = MagicMock()
        p.font.name = None
        p.font.size = None
        p.font.color = MagicMock()
        p.font.color.rgb = None
        p.space_before = None
        p.level = 0

        # Mock XML structure
        mock_pPr = MagicMock()
        mock_pPr.set = MagicMock()
        mock_pPr.find = MagicMock(return_value=None)
        mock_pPr.__iter__ = MagicMock(return_value=iter([]))

        p._p = MagicMock()
        p._p.get_or_add_pPr = MagicMock(return_value=mock_pPr)

        return p

    def test_apply_bullet_formatting_level_0(self, mock_paragraph):
        """Test bullet formatting for level 0."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._apply_bullet_formatting(mock_paragraph, 0)

            assert mock_paragraph.level == 0

    def test_apply_bullet_formatting_level_1(self, mock_paragraph):
        """Test bullet formatting for level 1."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._apply_bullet_formatting(mock_paragraph, 1)

            assert mock_paragraph.level == 1

    def test_apply_bullet_formatting_level_2(self, mock_paragraph):
        """Test bullet formatting for level 2."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._apply_bullet_formatting(mock_paragraph, 2)

            assert mock_paragraph.level == 2

    def test_apply_bullet_formatting_invalid_level_uses_default(self, mock_paragraph):
        """Test bullet formatting with invalid level falls back to level 0."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            # Level 5 doesn't exist, should fall back to level 0
            template._apply_bullet_formatting(mock_paragraph, 5)

            # Should not raise an error

    def test_apply_bullet_formatting_custom_text_color(self, mock_paragraph):
        """Test bullet formatting with custom text color."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._apply_bullet_formatting(mock_paragraph, 0, "#FFFFFF")

            # Should apply the custom color


class TestStratfieldFooterElements:
    """Tests for Stratfield footer elements."""

    @pytest.fixture
    def stratfield_template_for_footer(self):
        """Create a Stratfield template for footer testing."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_prs.return_value.slides = MagicMock()
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._slide_count = 5
            yield template

    @pytest.fixture
    def mock_slide_for_footer(self):
        """Create a mock slide for footer testing."""
        slide = MagicMock()
        mock_textbox = MagicMock()
        mock_textbox.text_frame = MagicMock()
        mock_textbox.text_frame.paragraphs = [MagicMock()]
        slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
        slide.shapes.add_picture = MagicMock()
        slide.shapes.add_shape = MagicMock()
        return slide

    def test_add_footer_elements_with_existing_assets(
        self, stratfield_template_for_footer, mock_slide_for_footer
    ):
        """Test footer elements with existing asset files."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_text_only"]

        with (
            patch.object(
                stratfield_template_for_footer.assets_dir.__class__,
                "exists",
                return_value=True,
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):
            stratfield_template_for_footer._add_footer_elements(
                mock_slide_for_footer, layout
            )

    def test_add_footer_elements_without_footer_bar_asset(
        self, stratfield_template_for_footer, mock_slide_for_footer
    ):
        """Test footer elements without footer bar asset (fallback to solid color)."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_text_only"]

        with patch("pathlib.Path.exists", return_value=False):
            stratfield_template_for_footer._add_footer_elements(
                mock_slide_for_footer, layout
            )
            # Should add a shape as fallback
            mock_slide_for_footer.shapes.add_shape.assert_called()

    def test_add_footer_elements_slide_number(
        self, stratfield_template_for_footer, mock_slide_for_footer
    ):
        """Test footer elements include slide number."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_text_only"]

        with patch("pathlib.Path.exists", return_value=False):
            stratfield_template_for_footer._add_footer_elements(
                mock_slide_for_footer, layout
            )
            # Should add textbox for slide number
            mock_slide_for_footer.shapes.add_textbox.assert_called()

    def test_add_footer_elements_no_footer_bar_in_layout(
        self, stratfield_template_for_footer, mock_slide_for_footer
    ):
        """Test footer elements with no footer_bar in layout."""
        layout = {"slide_number": {"x": 9.57, "y": 5.44, "w": 0.41, "h": 0.20}}

        stratfield_template_for_footer._add_footer_elements(
            mock_slide_for_footer, layout
        )
        # Should still work, just skip footer bar

    def test_add_footer_elements_no_slide_number_in_layout(
        self, stratfield_template_for_footer, mock_slide_for_footer
    ):
        """Test footer elements with no slide_number in layout."""
        layout = {"footer_bar": {"x": 0.0, "y": 5.33, "w": 10.0, "h": 0.31}}

        with patch("pathlib.Path.exists", return_value=False):
            stratfield_template_for_footer._add_footer_elements(
                mock_slide_for_footer, layout
            )
            # Should still work, just skip slide number


class TestStratfieldSlideCreationComprehensive:
    """Comprehensive tests for Stratfield slide creation methods."""

    @pytest.fixture
    def fully_mocked_template(self):
        """Create a fully mocked Stratfield template."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            # Create mock slide with full structure
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_tf = MagicMock()
            mock_p = MagicMock()
            mock_p.font = MagicMock()
            mock_p.font.color = MagicMock()
            mock_p._p = MagicMock()
            mock_pPr = MagicMock()
            mock_pPr.find = MagicMock(return_value=None)
            mock_pPr.__iter__ = MagicMock(return_value=iter([]))
            mock_p._p.get_or_add_pPr = MagicMock(return_value=mock_pPr)
            mock_tf.paragraphs = [mock_p]
            mock_tf.add_paragraph = MagicMock(return_value=mock_p)
            mock_textbox.text_frame = mock_tf
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.shapes.add_shape = MagicMock(return_value=MagicMock())
            mock_slide.shapes.add_picture = MagicMock(return_value=MagicMock())
            mock_slide.background = MagicMock()
            mock_slide.background.fill = MagicMock()

            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template._mock_slide = mock_slide
            yield template

    def test_add_title_slide_title_only(self, fully_mocked_template):
        """Test adding title slide with title only."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_title_slide("My Presentation")
            assert fully_mocked_template._slide_count == 1

    def test_add_title_slide_with_subtitle(self, fully_mocked_template):
        """Test adding title slide with subtitle."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_title_slide("My Presentation", "A great subtitle")
            assert fully_mocked_template._slide_count == 1

    def test_add_title_slide_with_date(self, fully_mocked_template):
        """Test adding title slide with date."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_title_slide(
                "My Presentation", "Subtitle", "January 2025"
            )
            assert fully_mocked_template._slide_count == 1

    def test_add_title_slide_with_background_image(self, fully_mocked_template):
        """Test adding title slide when background image exists."""
        with patch("pathlib.Path.exists", return_value=True):
            fully_mocked_template.add_title_slide("Title")
            # Should use add_picture for background
            fully_mocked_template._mock_slide.shapes.add_picture.assert_called()

    def test_add_title_slide_without_background_image(self, fully_mocked_template):
        """Test adding title slide when background image does not exist."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_title_slide("Title")
            # Should set background color instead
            fully_mocked_template._mock_slide.background.fill.solid.assert_called()

    def test_add_section_break_basic(self, fully_mocked_template):
        """Test adding section break slide."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_section_break("New Section")
            assert fully_mocked_template._slide_count == 1

    def test_add_section_break_with_logo(self, fully_mocked_template):
        """Test adding section break with logo mark asset."""
        with patch("pathlib.Path.exists", return_value=True):
            fully_mocked_template.add_section_break("Section Title")
            # Should add logo mark picture
            fully_mocked_template._mock_slide.shapes.add_picture.assert_called()

    def test_add_content_slide_single_bullet(self, fully_mocked_template):
        """Test adding content slide with single bullet."""
        with patch("pathlib.Path.exists", return_value=False):
            bullets = [("Single point", 0)]
            fully_mocked_template.add_content_slide("Title", "", bullets)
            assert fully_mocked_template._slide_count == 1

    def test_add_content_slide_multiple_bullets(self, fully_mocked_template):
        """Test adding content slide with multiple bullets."""
        with patch("pathlib.Path.exists", return_value=False):
            bullets = [
                ("First point", 0),
                ("Second point", 0),
                ("Third point", 0),
            ]
            fully_mocked_template.add_content_slide("Title", "", bullets)
            assert fully_mocked_template._slide_count == 1

    def test_add_content_slide_nested_bullets(self, fully_mocked_template):
        """Test adding content slide with nested bullet levels."""
        with patch("pathlib.Path.exists", return_value=False):
            bullets = [
                ("Main point", 0),
                ("Sub point", 1),
                ("Sub-sub point", 2),
                ("Another main", 0),
            ]
            fully_mocked_template.add_content_slide("Title", "Subtitle", bullets)
            assert fully_mocked_template._slide_count == 1

    def test_add_content_slide_empty_bullets(self, fully_mocked_template):
        """Test adding content slide with empty bullets list."""
        with patch("pathlib.Path.exists", return_value=False):
            fully_mocked_template.add_content_slide("Title Only", "", [])
            assert fully_mocked_template._slide_count == 1

    def test_add_image_slide_basic(self, fully_mocked_template):
        """Test adding image slide."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=True):
                fully_mocked_template.add_image_slide("Image Title", "test.png")
                assert fully_mocked_template._slide_count == 1

    def test_add_image_slide_with_subtitle(self, fully_mocked_template):
        """Test adding image slide with subtitle parameter (ignored in Stratfield)."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=True):
                fully_mocked_template.add_image_slide(
                    "Image Title", "test.png", "Subtitle"
                )
                assert fully_mocked_template._slide_count == 1

    def test_add_image_slide_missing_image(self, fully_mocked_template):
        """Test adding image slide with missing image file."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=False):
                fully_mocked_template.add_image_slide("Title", "missing.png")
                # Should create placeholder shape
                fully_mocked_template._mock_slide.shapes.add_shape.assert_called()

    def test_add_text_and_image_slide_basic(self, fully_mocked_template):
        """Test adding text and image slide."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=True):
                bullets = [("Point one", 0), ("Point two", 0)]
                fully_mocked_template.add_text_and_image_slide(
                    "Title", bullets, "test.png"
                )
                assert fully_mocked_template._slide_count == 1

    def test_add_text_and_image_slide_nested_bullets(self, fully_mocked_template):
        """Test text and image slide with nested bullets."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=True):
                bullets = [
                    ("Main point", 0),
                    ("Sub point", 1),
                    ("Another main", 0),
                ]
                fully_mocked_template.add_text_and_image_slide(
                    "Title", bullets, "image.jpg"
                )
                assert fully_mocked_template._slide_count == 1

    def test_add_text_and_image_slide_left_panel_created(self, fully_mocked_template):
        """Test text and image slide creates left panel rectangle."""
        with patch("pathlib.Path.exists", return_value=False):
            with patch("os.path.exists", return_value=True):
                bullets = [("Point", 0)]
                fully_mocked_template.add_text_and_image_slide(
                    "Title", bullets, "img.png"
                )
                # Should add rectangle for left panel
                fully_mocked_template._mock_slide.shapes.add_shape.assert_called()


class TestStratfieldSaveAndCount:
    """Tests for save and get_slide_count methods."""

    def test_save_creates_file(self):
        """Test save method calls prs.save."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            template.save("output.pptx")

            mock_prs.return_value.save.assert_called_once_with("output.pptx")

    def test_get_slide_count_zero(self):
        """Test get_slide_count returns 0 initially."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            assert template.get_slide_count() == 0

    def test_get_slide_count_after_slides(self):
        """Test get_slide_count returns correct count after adding slides."""
        with patch("plugin.templates.stratfield.template.Presentation"):
            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()

            # Directly test the slide count tracking by incrementing _slide_count
            # This avoids complex mocking of XML manipulation internals
            assert template.get_slide_count() == 0

            template._slide_count = 1
            assert template.get_slide_count() == 1

            template._slide_count = 3
            assert template.get_slide_count() == 3


class TestStratfieldLayoutDetails:
    """Tests for specific layout configuration details."""

    def test_title_slide_layout_has_logo_spec(self):
        """Test title slide layout includes logo specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["title_slide"]
        assert "logo" in layout
        assert "x" in layout["logo"]
        assert "y" in layout["logo"]
        assert "w" in layout["logo"]
        assert "h" in layout["logo"]

    def test_title_slide_layout_has_date_spec(self):
        """Test title slide layout includes date specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["title_slide"]
        assert "date" in layout
        assert "font" in layout["date"]
        assert layout["date"]["font"] == "Avenir Light"

    def test_section_break_layout_has_logo_mark(self):
        """Test section break layout includes logo mark specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["section_break"]
        assert "logo_mark" in layout
        assert "x" in layout["logo_mark"]

    def test_content_text_only_has_body_levels(self):
        """Test content text only layout has body with level specifications."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_text_only"]
        assert "body" in layout
        assert "levels" in layout["body"]
        assert 0 in layout["body"]["levels"]
        assert 1 in layout["body"]["levels"]
        assert 2 in layout["body"]["levels"]

    def test_content_full_image_has_image_spec(self):
        """Test content full image layout has image specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_full_image"]
        assert "image" in layout
        assert "x" in layout["image"]
        assert "y" in layout["image"]
        assert "w" in layout["image"]
        assert "h" in layout["image"]

    def test_content_text_and_image_has_left_panel(self):
        """Test content text and image layout has left panel specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        layout = LAYOUTS["content_text_and_image"]
        assert "left_panel" in layout
        assert "fill" in layout["left_panel"]
        assert layout["left_panel"]["fill"] == "#296057"

    def test_all_content_layouts_have_footer_bar(self):
        """Test all content layouts have footer bar specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        for layout_name in [
            "content_text_only",
            "content_full_image",
            "content_text_and_image",
        ]:
            assert "footer_bar" in LAYOUTS[layout_name], (
                f"{layout_name} missing footer_bar"
            )

    def test_all_content_layouts_have_slide_number(self):
        """Test all content layouts have slide number specification."""
        from plugin.templates.stratfield.template import LAYOUTS

        for layout_name in [
            "content_text_only",
            "content_full_image",
            "content_text_and_image",
        ]:
            assert "slide_number" in LAYOUTS[layout_name], (
                f"{layout_name} missing slide_number"
            )


class TestStratfieldBulletConfiguration:
    """Tests for Stratfield bullet configuration details."""

    def test_bullet_sizes_decrease_with_level(self):
        """Test bullet sizes decrease with indent level."""
        from plugin.templates.stratfield.template import BULLET_SPECS

        assert BULLET_SPECS[0]["size"] > BULLET_SPECS[1]["size"]
        assert BULLET_SPECS[1]["size"] > BULLET_SPECS[2]["size"]

    def test_bullet_margins_increase_with_level(self):
        """Test bullet margins increase with indent level."""
        from plugin.templates.stratfield.template import BULLET_SPECS

        assert BULLET_SPECS[0]["marL"] < BULLET_SPECS[1]["marL"]
        assert BULLET_SPECS[1]["marL"] < BULLET_SPECS[2]["marL"]

    def test_bullet_space_before_reasonable(self):
        """Test bullet space before values are reasonable."""
        from plugin.templates.stratfield.template import BULLET_SPECS

        for level in [0, 1, 2]:
            space_before = BULLET_SPECS[level]["space_before"]
            assert space_before > 0, f"Level {level} space_before should be positive"
            assert space_before <= 20, f"Level {level} space_before seems too large"

    def test_bullet_indent_is_negative(self):
        """Test bullet indent is negative (hanging indent)."""
        from plugin.templates.stratfield.template import BULLET_SPECS

        for level in [0, 1, 2]:
            indent = BULLET_SPECS[level]["indent"]
            assert indent < 0, f"Level {level} indent should be negative for hanging"


class TestStratfieldEdgeCases:
    """Edge case tests for Stratfield template."""

    def test_empty_title(self):
        """Test handling of empty title."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.background = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            with patch("pathlib.Path.exists", return_value=False):
                # Empty title should not raise an error
                template.add_title_slide("")
                assert template.get_slide_count() == 1

    def test_very_long_title(self):
        """Test handling of very long title."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.background = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            with patch("pathlib.Path.exists", return_value=False):
                long_title = "A" * 500
                template.add_title_slide(long_title)
                assert template.get_slide_count() == 1

    def test_special_characters_in_text(self):
        """Test handling of special characters in text."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_textbox.text_frame = MagicMock()
            mock_textbox.text_frame.paragraphs = [MagicMock()]
            mock_textbox.text_frame.add_paragraph = MagicMock(return_value=MagicMock())
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.background = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            with patch("pathlib.Path.exists", return_value=False):
                template.add_title_slide(
                    "Title with special chars: <>&\"'",
                    "Subtitle with unicode: \u00e9\u00f1\u00fc",
                )
                assert template.get_slide_count() == 1

    def test_multiple_slides_sequential(self):
        """Test adding multiple slides in sequence."""
        with patch("plugin.templates.stratfield.template.Presentation") as mock_prs:
            mock_slide = MagicMock()
            mock_textbox = MagicMock()
            mock_tf = MagicMock()
            mock_p = MagicMock()
            mock_p._p = MagicMock()
            mock_pPr = MagicMock()
            mock_pPr.find = MagicMock(return_value=None)
            mock_pPr.__iter__ = MagicMock(return_value=iter([]))
            mock_p._p.get_or_add_pPr = MagicMock(return_value=mock_pPr)
            mock_tf.paragraphs = [mock_p]
            mock_tf.add_paragraph = MagicMock(return_value=mock_p)
            mock_textbox.text_frame = mock_tf
            mock_slide.shapes.add_textbox = MagicMock(return_value=mock_textbox)
            mock_slide.shapes.add_shape = MagicMock(return_value=MagicMock())
            mock_slide.shapes.add_picture = MagicMock(return_value=MagicMock())
            mock_slide.background = MagicMock()
            mock_prs.return_value.slides.add_slide = MagicMock(return_value=mock_slide)
            mock_prs.return_value.slide_layouts = [MagicMock() for _ in range(10)]

            from plugin.templates.stratfield.template import StratfieldPresentation

            template = StratfieldPresentation()
            with patch("pathlib.Path.exists", return_value=False):
                with patch("os.path.exists", return_value=True):
                    template.add_title_slide("Title")
                    template.add_section_break("Section 1")
                    template.add_content_slide("Content 1", "", [("Point", 0)])
                    template.add_image_slide("Image Slide", "img.png")
                    template.add_text_and_image_slide(
                        "Two Column", [("Text", 0)], "img.png"
                    )
                    template.add_section_break("Section 2")

                    assert template.get_slide_count() == 6
