"""
Unit tests for plugin/lib/presentation/assembler.py

Tests the presentation assembler which orchestrates the full workflow:
1. Parse markdown presentation file
2. Classify slide types intelligently (rule-based + AI)
3. Generate images for slides with graphics
4. Build PowerPoint using selected brand template
5. Save final output
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from plugin.lib.presentation.parser import Slide
from plugin.lib.presentation.type_classifier import TypeClassification


class TestAssemblePresentation:
    """Tests for assemble_presentation function."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create sample slides
        self.sample_slides = [
            Slide(
                number=1,
                slide_type="TITLE SLIDE",
                title="Test Presentation",
                subtitle="A Subtitle",
                content_bullets=[],
            ),
            Slide(
                number=2,
                slide_type="CONTENT",
                title="Content Slide",
                content_bullets=[("Point 1", 0), ("Point 2", 0)],
            ),
            Slide(
                number=3,
                slide_type="CONTENT",
                title="Visual Slide",
                content_bullets=[("Item", 0)],
                graphic="A diagram showing system architecture",
            ),
        ]

        # Create sample classification results
        self.sample_classifications = {
            1: TypeClassification(
                slide_type="title",
                confidence=1.0,
                reasoning="Title slide marker",
                template_method="add_title_slide",
            ),
            2: TypeClassification(
                slide_type="content",
                confidence=0.95,
                reasoning="Has bullets, no graphic",
                template_method="add_content_slide",
            ),
            3: TypeClassification(
                slide_type="text_image",
                confidence=0.9,
                reasoning="Has bullets and graphic",
                template_method="add_text_and_image_slide",
            ),
        }

    def test_assemble_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        from plugin.lib.presentation.assembler import assemble_presentation

        with pytest.raises(FileNotFoundError, match="Markdown file not found"):
            assemble_presentation(
                markdown_path="/nonexistent/path/file.md",
                template_id="cfa",
            )

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_empty_slides_raises_error(self, mock_parse, mock_get_template):
        """Test that ValueError is raised when no slides found."""
        from plugin.lib.presentation.assembler import assemble_presentation

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Empty presentation\n")
            temp_path = f.name

        try:
            mock_parse.return_value = []

            with pytest.raises(ValueError, match="No slides found"):
                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                )
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_basic_workflow(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test basic assembly workflow without images."""
        from plugin.lib.presentation.assembler import assemble_presentation

        # Set up mocks
        mock_parse.return_value = self.sample_slides[:2]  # No graphics

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.side_effect = [
            self.sample_classifications[1],
            self.sample_classifications[2],
        ]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        # Create temp markdown file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_name="test.pptx",
                    output_dir=output_dir,
                    skip_images=True,
                )

                # Verify output path
                assert result.endswith("test.pptx")
                assert Path(result).parent == Path(output_dir)

                # Verify template methods were called
                mock_template.add_title_slide.assert_called_once()
                mock_template.add_content_slide.assert_called_once()
                mock_template.save.assert_called_once()
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_creates_output_directory(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test that output directory is created if it doesn't exist."""
        from plugin.lib.presentation.assembler import assemble_presentation

        mock_parse.return_value = [self.sample_slides[0]]

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.return_value = self.sample_classifications[1]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as base_dir:
                nested_output = Path(base_dir) / "new" / "nested" / "dir"

                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=str(nested_output),
                    skip_images=True,
                )

                assert nested_output.exists()
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_adds_pptx_extension(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test that .pptx extension is added if missing."""
        from plugin.lib.presentation.assembler import assemble_presentation

        mock_parse.return_value = [self.sample_slides[0]]

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.return_value = self.sample_classifications[1]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_name="my_presentation",  # No .pptx
                    output_dir=output_dir,
                    skip_images=True,
                )

                assert result.endswith(".pptx")
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.generate_all_images")
    @patch("plugin.lib.presentation.assembler.get_slides_needing_images")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_with_image_generation(
        self,
        mock_parse,
        mock_classifier_class,
        mock_get_needing_images,
        mock_generate_images,
        mock_get_template,
    ):
        """Test assembly with image generation enabled."""
        from plugin.lib.presentation.assembler import assemble_presentation

        # Include slide with graphic
        mock_parse.return_value = self.sample_slides

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.side_effect = [
            self.sample_classifications[1],
            self.sample_classifications[2],
            self.sample_classifications[3],
        ]
        mock_classifier_class.return_value = mock_classifier

        # Simulate slides needing images
        mock_get_needing_images.return_value = [self.sample_slides[2]]

        # Simulate image generation
        mock_generate_images.return_value = {3: Path("/tmp/images/slide-3.jpg")}

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=output_dir,
                    skip_images=False,  # Enable image generation
                )

                # Verify image generation was called
                mock_generate_images.assert_called_once()
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_skip_images_flag(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test that skip_images=True skips image generation."""
        from plugin.lib.presentation.assembler import assemble_presentation

        mock_parse.return_value = self.sample_slides

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.side_effect = list(
            self.sample_classifications.values()
        )
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with (
                tempfile.TemporaryDirectory() as output_dir,
                patch(
                    "plugin.lib.presentation.assembler.generate_all_images"
                ) as mock_gen,
            ):
                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=output_dir,
                    skip_images=True,
                )

                # Verify image generation was NOT called
                mock_gen.assert_not_called()
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_assemble_with_progress_callback(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test that progress callback is called during assembly."""
        from plugin.lib.presentation.assembler import assemble_presentation

        mock_parse.return_value = [self.sample_slides[0]]

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.return_value = self.sample_classifications[1]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        progress_calls = []

        def progress_callback(stage, current, total):
            progress_calls.append((stage, current, total))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=output_dir,
                    skip_images=True,
                    progress_callback=progress_callback,
                )

                # Verify callback was called for each stage
                assert (
                    len(progress_calls) >= 4
                )  # At least parsing, classifying, building, saving
                stages = [c[0] for c in progress_calls]
                assert "Parsing markdown" in stages
                assert "Classifying slide types" in stages
                assert "Building presentation" in stages
                assert "Saving" in stages
        finally:
            os.unlink(temp_path)

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    @patch("plugin.lib.presentation.assembler.load_style_config")
    def test_assemble_with_style_config(
        self, mock_load_style, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test assembly with custom style config."""
        from plugin.lib.presentation.assembler import assemble_presentation

        mock_parse.return_value = [self.sample_slides[0]]

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.return_value = self.sample_classifications[1]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        custom_style = {"style": "custom", "tone": "informal"}
        mock_load_style.return_value = custom_style

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=output_dir,
                    style_config_path="/path/to/style.json",
                    skip_images=True,
                )

                mock_load_style.assert_called_once_with("/path/to/style.json")
        finally:
            os.unlink(temp_path)


class TestAddSlideToPresentation:
    """Tests for _add_slide_to_presentation function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_template = MagicMock()

    def test_add_title_slide(self):
        """Test adding a title slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Main Title",
            subtitle="Subtitle Here",
            content_bullets=[],
        )

        classification = TypeClassification(
            slide_type="title",
            confidence=1.0,
            reasoning="Title slide",
            template_method="add_title_slide",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        self.mock_template.add_title_slide.assert_called_once_with(
            "Main Title", "Subtitle Here", ""
        )

    def test_add_title_slide_with_date_in_content(self):
        """Test that date is extracted from content for title slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Main Title",
            subtitle="Subtitle",
            content_bullets=[("January 2025", 0), ("Other content", 0)],
        )

        classification = TypeClassification(
            slide_type="title",
            confidence=1.0,
            reasoning="Title slide",
            template_method="add_title_slide",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        # Verify date was extracted
        call_args = self.mock_template.add_title_slide.call_args
        assert call_args[0][2] == "January 2025"  # Date parameter

    def test_add_title_slide_with_year_in_content(self):
        """Test that year is extracted from content for title slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Main Title",
            subtitle="Subtitle",
            content_bullets=[("Conference 2025", 0)],
        )

        classification = TypeClassification(
            slide_type="title",
            confidence=1.0,
            reasoning="Title slide",
            template_method="add_title_slide",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        call_args = self.mock_template.add_title_slide.call_args
        assert call_args[0][2] == "Conference 2025"

    def test_add_section_break(self):
        """Test adding a section break slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=5,
            slide_type="SECTION DIVIDER",
            title="New Section",
            content_bullets=[],
        )

        classification = TypeClassification(
            slide_type="section",
            confidence=1.0,
            reasoning="Section break",
            template_method="add_section_break",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        self.mock_template.add_section_break.assert_called_once_with("New Section")

    def test_add_image_slide_with_image_path(self):
        """Test adding an image slide with generated image."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            subtitle="Description",
            content_bullets=[],
            graphic="A chart",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image-focused slide",
            template_method="add_image_slide",
        )

        image_paths = {3: Path("/tmp/images/slide-3.jpg")}

        _add_slide_to_presentation(
            self.mock_template, slide, classification, image_paths, Path("/tmp/images")
        )

        # Check the call was made with correct arguments
        # Use os.path.normpath to handle platform-specific path separators
        call_args = self.mock_template.add_image_slide.call_args[0]
        assert call_args[0] == "Visual Slide"
        assert os.path.normpath(call_args[1]) == os.path.normpath(
            "/tmp/images/slide-3.jpg"
        )
        assert call_args[2] == "Description"

    def test_add_image_slide_fallback_to_existing_file(self):
        """Test fallback to existing image file when not in image_paths."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            subtitle="",
            content_bullets=[],
            graphic="A chart",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image slide",
            template_method="add_image_slide",
        )

        with tempfile.TemporaryDirectory() as images_dir:
            # Create existing image file
            image_path = Path(images_dir) / "slide-3.jpg"
            image_path.write_text("fake image")

            _add_slide_to_presentation(
                self.mock_template, slide, classification, {}, Path(images_dir)
            )

            self.mock_template.add_image_slide.assert_called_once()
            call_args = self.mock_template.add_image_slide.call_args
            assert "slide-3.jpg" in call_args[0][1]

    def test_add_image_slide_fallback_to_content_when_no_image(self):
        """Test fallback to content slide when image is not available."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            subtitle="Subtitle",
            content_bullets=[("Point", 0)],
            graphic="A chart",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image slide",
            template_method="add_image_slide",
        )

        # No images available
        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/nonexistent")
        )

        # Should fall back to content slide
        self.mock_template.add_content_slide.assert_called_once_with(
            "Visual Slide", "Subtitle", [("Point", 0)]
        )
        self.mock_template.add_image_slide.assert_not_called()

    def test_add_text_and_image_slide(self):
        """Test adding a text and image slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=4,
            slide_type="CONTENT",
            title="Mixed Slide",
            content_bullets=[("Point 1", 0), ("Point 2", 0)],
            graphic="Supporting image",
        )

        classification = TypeClassification(
            slide_type="text_image",
            confidence=0.9,
            reasoning="Balanced content",
            template_method="add_text_and_image_slide",
        )

        image_paths = {4: Path("/tmp/images/slide-4.jpg")}

        _add_slide_to_presentation(
            self.mock_template, slide, classification, image_paths, Path("/tmp/images")
        )

        # Check the call was made with correct arguments
        # Use os.path.normpath to handle platform-specific path separators
        call_args = self.mock_template.add_text_and_image_slide.call_args[0]
        assert call_args[0] == "Mixed Slide"
        assert call_args[1] == [("Point 1", 0), ("Point 2", 0)]
        assert os.path.normpath(call_args[2]) == os.path.normpath(
            "/tmp/images/slide-4.jpg"
        )

    def test_add_text_and_image_slide_fallback_when_no_image(self):
        """Test fallback to content slide for text_image when no image."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=4,
            slide_type="CONTENT",
            title="Mixed Slide",
            subtitle="Sub",
            content_bullets=[("Point", 0)],
            graphic="Image",
        )

        classification = TypeClassification(
            slide_type="text_image",
            confidence=0.9,
            reasoning="Mixed",
            template_method="add_text_and_image_slide",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/nonexistent")
        )

        self.mock_template.add_content_slide.assert_called_once()
        self.mock_template.add_text_and_image_slide.assert_not_called()

    def test_add_content_slide_default(self):
        """Test adding a content slide (default case)."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Content Slide",
            subtitle="Summary",
            content_bullets=[("Point 1", 0), ("Point 2", 1), ("Point 3", 0)],
        )

        classification = TypeClassification(
            slide_type="content",
            confidence=0.95,
            reasoning="Text content",
            template_method="add_content_slide",
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        self.mock_template.add_content_slide.assert_called_once_with(
            "Content Slide",
            "Summary",
            [("Point 1", 0), ("Point 2", 1), ("Point 3", 0)],
        )

    def test_add_slide_unknown_method_defaults_to_content(self):
        """Test that unknown methods default to content slide."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        slide = Slide(
            number=2,
            slide_type="UNKNOWN",
            title="Unknown Slide",
            subtitle="",
            content_bullets=[("Point", 0)],
        )

        classification = TypeClassification(
            slide_type="unknown",
            confidence=0.5,
            reasoning="Unknown type",
            template_method="add_unknown_slide",  # Unknown method
        )

        _add_slide_to_presentation(
            self.mock_template, slide, classification, {}, Path("/tmp")
        )

        # Should fall back to content slide
        self.mock_template.add_content_slide.assert_called_once()


class TestBuildSlideWithValidation:
    """Tests for _build_slide_with_validation function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_template = MagicMock()
        self.mock_template.prs = MagicMock()
        self.mock_template.prs.slides = MagicMock()

    @patch("plugin.lib.presentation.assembler._add_slide_to_presentation")
    @patch("plugin.lib.presentation.assembler.generate_slide_image")
    def test_validation_passes_first_attempt(self, mock_generate_image, mock_add_slide):
        """Test validation loop when slide passes on first attempt."""
        from plugin.lib.presentation.assembler import _build_slide_with_validation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            content_bullets=[],
            graphic="A diagram",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image slide",
            template_method="add_image_slide",
        )

        mock_validator = MagicMock()
        mock_validation_result = MagicMock()
        mock_validation_result.passed = True
        mock_validation_result.score = 0.95
        mock_validator.validate_slide.return_value = mock_validation_result

        mock_refiner = MagicMock()
        mock_refiner.DIMINISHING_RETURNS_THRESHOLD = 0.9

        mock_exporter = MagicMock()
        mock_exporter.export_slide.return_value = True

        self.mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir) / "validation"
            validation_dir.mkdir()
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir()
            output_path = Path(temp_dir) / "output.pptx"

            _build_slide_with_validation(
                template=self.mock_template,
                slide=slide,
                classification=classification,
                image_paths={},
                images_dir=images_dir,
                validator=mock_validator,
                refiner=mock_refiner,
                exporter=mock_exporter,
                validation_dir=validation_dir,
                style_config={"style": "test"},
                output_path=output_path,
                max_attempts=3,
                fast_mode=False,
                notext=True,
            )

            # Verify slide was added
            mock_add_slide.assert_called_once()

            # Verify validation was performed
            mock_validator.validate_slide.assert_called_once()

            # Verify no refinement was needed (passed first time)
            mock_refiner.generate_refinement.assert_not_called()

    @patch("plugin.lib.presentation.assembler._add_slide_to_presentation")
    @patch("plugin.lib.presentation.assembler._remove_last_slide")
    @patch("plugin.lib.presentation.assembler.generate_slide_image")
    def test_validation_fails_then_passes(
        self, mock_generate_image, mock_remove_slide, mock_add_slide
    ):
        """Test validation loop with refinement on failure."""
        from plugin.lib.presentation.assembler import _build_slide_with_validation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual Slide",
            content_bullets=[],
            graphic="A diagram",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image slide",
            template_method="add_image_slide",
        )

        # First attempt fails, second passes
        mock_validator = MagicMock()
        fail_result = MagicMock()
        fail_result.passed = False
        fail_result.score = 0.5

        pass_result = MagicMock()
        pass_result.passed = True
        pass_result.score = 0.92

        mock_validator.validate_slide.side_effect = [fail_result, pass_result]

        mock_refiner = MagicMock()
        mock_refiner.DIMINISHING_RETURNS_THRESHOLD = 0.9
        mock_refiner.should_retry.return_value = True
        mock_refinement = MagicMock()
        mock_refinement.reasoning = "Improve contrast"
        mock_refinement.modified_prompt = "Enhanced prompt"
        mock_refinement.parameter_adjustments = {}
        mock_refiner.generate_refinement.return_value = mock_refinement

        mock_exporter = MagicMock()
        mock_exporter.export_slide.return_value = True

        mock_generate_image.return_value = Path("/tmp/refined.jpg")

        self.mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir) / "validation"
            validation_dir.mkdir()
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir()
            output_path = Path(temp_dir) / "output.pptx"

            _build_slide_with_validation(
                template=self.mock_template,
                slide=slide,
                classification=classification,
                image_paths={},
                images_dir=images_dir,
                validator=mock_validator,
                refiner=mock_refiner,
                exporter=mock_exporter,
                validation_dir=validation_dir,
                style_config={"style": "test"},
                output_path=output_path,
                max_attempts=3,
                fast_mode=False,
                notext=True,
            )

            # Verify refinement was called
            mock_refiner.generate_refinement.assert_called_once()

            # Verify image was regenerated
            mock_generate_image.assert_called_once()

            # Verify slide was removed and rebuilt
            mock_remove_slide.assert_called_once()

    @patch("plugin.lib.presentation.assembler._add_slide_to_presentation")
    def test_validation_export_fails_accepts_without_validation(self, mock_add_slide):
        """Test that slide is accepted when export fails."""
        from plugin.lib.presentation.assembler import _build_slide_with_validation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual",
            content_bullets=[],
            graphic="Diagram",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image",
            template_method="add_image_slide",
        )

        mock_validator = MagicMock()
        mock_refiner = MagicMock()

        mock_exporter = MagicMock()
        mock_exporter.export_slide.return_value = False  # Export fails

        self.mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir) / "validation"
            validation_dir.mkdir()
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir()
            output_path = Path(temp_dir) / "output.pptx"

            _build_slide_with_validation(
                template=self.mock_template,
                slide=slide,
                classification=classification,
                image_paths={},
                images_dir=images_dir,
                validator=mock_validator,
                refiner=mock_refiner,
                exporter=mock_exporter,
                validation_dir=validation_dir,
                style_config={},
                output_path=output_path,
                max_attempts=3,
                fast_mode=False,
                notext=True,
            )

            # Verify slide was added but validation was skipped
            mock_add_slide.assert_called_once()
            mock_validator.validate_slide.assert_not_called()

    @patch("plugin.lib.presentation.assembler._add_slide_to_presentation")
    def test_validation_exception_accepts_slide(self, mock_add_slide):
        """Test that slide is accepted when validation throws exception."""
        from plugin.lib.presentation.assembler import _build_slide_with_validation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual",
            content_bullets=[],
            graphic="Diagram",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image",
            template_method="add_image_slide",
        )

        mock_validator = MagicMock()
        mock_validator.validate_slide.side_effect = Exception("Validation error")

        mock_refiner = MagicMock()

        mock_exporter = MagicMock()
        mock_exporter.export_slide.return_value = True

        self.mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir) / "validation"
            validation_dir.mkdir()
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir()
            output_path = Path(temp_dir) / "output.pptx"

            # Should not raise, just accept the slide
            _build_slide_with_validation(
                template=self.mock_template,
                slide=slide,
                classification=classification,
                image_paths={},
                images_dir=images_dir,
                validator=mock_validator,
                refiner=mock_refiner,
                exporter=mock_exporter,
                validation_dir=validation_dir,
                style_config={},
                output_path=output_path,
                max_attempts=3,
                fast_mode=False,
                notext=True,
            )

            mock_add_slide.assert_called_once()

    @patch("plugin.lib.presentation.assembler._add_slide_to_presentation")
    def test_validation_max_attempts_reached(self, mock_add_slide):
        """Test validation loop stops at max attempts."""
        from plugin.lib.presentation.assembler import _build_slide_with_validation

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Visual",
            content_bullets=[],
            graphic="Diagram",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image",
            template_method="add_image_slide",
        )

        mock_validator = MagicMock()
        fail_result = MagicMock()
        fail_result.passed = False
        fail_result.score = 0.4
        mock_validator.validate_slide.return_value = fail_result

        mock_refiner = MagicMock()
        mock_refiner.DIMINISHING_RETURNS_THRESHOLD = 0.9
        mock_refiner.should_retry.return_value = False  # Stop after first attempt

        mock_exporter = MagicMock()
        mock_exporter.export_slide.return_value = True

        self.mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        with tempfile.TemporaryDirectory() as temp_dir:
            validation_dir = Path(temp_dir) / "validation"
            validation_dir.mkdir()
            images_dir = Path(temp_dir) / "images"
            images_dir.mkdir()
            output_path = Path(temp_dir) / "output.pptx"

            _build_slide_with_validation(
                template=self.mock_template,
                slide=slide,
                classification=classification,
                image_paths={},
                images_dir=images_dir,
                validator=mock_validator,
                refiner=mock_refiner,
                exporter=mock_exporter,
                validation_dir=validation_dir,
                style_config={},
                output_path=output_path,
                max_attempts=1,  # Only 1 attempt
                fast_mode=False,
                notext=True,
            )

            # Should only attempt once
            assert mock_add_slide.call_count == 1
            mock_refiner.generate_refinement.assert_not_called()


class TestRemoveLastSlide:
    """Tests for _remove_last_slide function."""

    def test_remove_last_slide_success(self):
        """Test successfully removing the last slide."""
        from plugin.lib.presentation.assembler import _remove_last_slide

        mock_template = MagicMock()
        mock_prs = MagicMock()
        mock_template.prs = mock_prs

        mock_slides = MagicMock()
        mock_slides.__len__ = MagicMock(return_value=3)

        mock_sld_id = MagicMock()
        mock_sld_id.rId = "rId5"
        mock_slides._sldIdLst = [MagicMock(), MagicMock(), mock_sld_id]

        mock_prs.slides = mock_slides

        _remove_last_slide(mock_template)

        mock_prs.part.drop_rel.assert_called_once_with("rId5")

    def test_remove_last_slide_empty_presentation(self):
        """Test removing from empty presentation does nothing."""
        from plugin.lib.presentation.assembler import _remove_last_slide

        mock_template = MagicMock()
        mock_prs = MagicMock()
        mock_template.prs = mock_prs

        mock_slides = MagicMock()
        mock_slides.__len__ = MagicMock(return_value=0)
        mock_slides._sldIdLst = []
        mock_prs.slides = mock_slides

        # Should not raise
        _remove_last_slide(mock_template)

        mock_prs.part.drop_rel.assert_not_called()

    def test_remove_last_slide_handles_exception(self):
        """Test that exceptions are handled gracefully."""
        from plugin.lib.presentation.assembler import _remove_last_slide

        mock_template = MagicMock()
        mock_template.prs.slides._sldIdLst.__getitem__.side_effect = Exception(
            "Test error"
        )
        mock_template.prs.slides.__len__ = MagicMock(return_value=1)

        # Should not raise, just print warning
        _remove_last_slide(mock_template)


class TestNotify:
    """Tests for _notify function."""

    def test_notify_calls_callback(self):
        """Test that callback is called with correct arguments."""
        from plugin.lib.presentation.assembler import _notify

        callback_args = []

        def callback(stage, current, total):
            callback_args.append((stage, current, total))

        _notify(callback, "Testing", 2, 5)

        assert callback_args == [("Testing", 2, 5)]

    def test_notify_with_none_callback(self):
        """Test that None callback is handled gracefully."""
        from plugin.lib.presentation.assembler import _notify

        # Should not raise
        _notify(None, "Testing", 1, 1)


class TestPreviewPresentation:
    """Tests for preview_presentation function."""

    @patch("plugin.lib.presentation.assembler.parse_presentation")
    @patch("plugin.lib.presentation.assembler.get_slides_needing_images")
    def test_preview_displays_summary(self, mock_get_needing, mock_parse, capsys):
        """Test that preview displays presentation summary."""
        from plugin.lib.presentation.assembler import preview_presentation

        slides = [
            Slide(number=1, slide_type="TITLE", title="Test Presentation"),
            Slide(
                number=2,
                slide_type="CONTENT",
                title="Content Slide",
                content_bullets=[("P1", 0)],
            ),
            Slide(
                number=3,
                slide_type="CONTENT",
                title="Visual Slide",
                graphic="A chart",
                content_bullets=[("P2", 0), ("P3", 0)],
            ),
        ]
        mock_parse.return_value = slides
        mock_get_needing.return_value = [slides[2]]

        preview_presentation("/path/to/presentation.md")

        captured = capsys.readouterr()
        assert "[PREVIEW]" in captured.out
        assert "presentation.md" in captured.out
        assert "3" in captured.out  # Total slides
        assert "Slides with graphics: 1" in captured.out

    @patch("plugin.lib.presentation.assembler.parse_presentation")
    @patch("plugin.lib.presentation.assembler.get_slides_needing_images")
    def test_preview_empty_presentation(self, mock_get_needing, mock_parse, capsys):
        """Test preview with no slides."""
        from plugin.lib.presentation.assembler import preview_presentation

        mock_parse.return_value = []
        mock_get_needing.return_value = []

        preview_presentation("/path/to/empty.md")

        captured = capsys.readouterr()
        assert "[PREVIEW]" in captured.out
        assert "0" in captured.out


class TestGetAvailableTemplates:
    """Tests for get_available_templates function."""

    @patch("plugin.lib.presentation.assembler.list_templates")
    def test_returns_template_list(self, mock_list):
        """Test that available templates are returned."""
        from plugin.lib.presentation.assembler import get_available_templates

        mock_list.return_value = [
            ("cfa", "CFA Template", "CFA branded presentation"),
            ("stratfield", "Stratfield Template", "Stratfield branded"),
        ]

        result = get_available_templates()

        assert len(result) == 2
        assert result[0][0] == "cfa"
        assert result[1][0] == "stratfield"


class TestMainCLI:
    """Tests for main CLI function."""

    @patch("plugin.lib.presentation.assembler.preview_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_preview_mode(self, mock_parse_args, mock_preview):
        """Test CLI preview mode."""
        from plugin.lib.presentation.assembler import main

        mock_args = MagicMock()
        mock_args.preview = True
        mock_args.markdown = "/path/to/presentation.md"
        mock_parse_args.return_value = mock_args

        main()

        mock_preview.assert_called_once_with("/path/to/presentation.md")

    @patch("plugin.lib.presentation.assembler.assemble_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_assemble_mode(self, mock_parse_args, mock_assemble):
        """Test CLI assemble mode."""
        from plugin.lib.presentation.assembler import main

        mock_args = MagicMock()
        mock_args.preview = False
        mock_args.markdown = "/path/to/presentation.md"
        mock_args.template = "cfa"
        mock_args.style = None
        mock_args.output = "output.pptx"
        mock_args.skip_images = True
        mock_args.fast = False
        mock_args.force = False
        mock_parse_args.return_value = mock_args

        main()

        mock_assemble.assert_called_once_with(
            markdown_path="/path/to/presentation.md",
            template_id="cfa",
            style_config_path=None,
            output_name="output.pptx",
            skip_images=True,
            fast_mode=False,
            force_images=False,
        )

    @patch("plugin.lib.presentation.assembler.assemble_presentation")
    @patch("argparse.ArgumentParser.parse_args")
    def test_main_with_all_options(self, mock_parse_args, mock_assemble):
        """Test CLI with all options specified."""
        from plugin.lib.presentation.assembler import main

        mock_args = MagicMock()
        mock_args.preview = False
        mock_args.markdown = "/path/to/pres.md"
        mock_args.template = "stratfield"
        mock_args.style = "/path/to/style.json"
        mock_args.output = "my_output"
        mock_args.skip_images = False
        mock_args.fast = True
        mock_args.force = True
        mock_parse_args.return_value = mock_args

        main()

        mock_assemble.assert_called_once_with(
            markdown_path="/path/to/pres.md",
            template_id="stratfield",
            style_config_path="/path/to/style.json",
            output_name="my_output",
            skip_images=False,
            fast_mode=True,
            force_images=True,
        )


class TestIntegration:
    """Integration tests for assembler workflow."""

    @patch("plugin.lib.presentation.assembler.get_template")
    @patch("plugin.lib.presentation.assembler.SlideTypeClassifier")
    @patch("plugin.lib.presentation.assembler.parse_presentation")
    def test_full_workflow_without_images(
        self, mock_parse, mock_classifier_class, mock_get_template
    ):
        """Test complete workflow without image generation."""
        from plugin.lib.presentation.assembler import assemble_presentation

        # Create comprehensive slide set
        slides = [
            Slide(
                number=1,
                slide_type="TITLE SLIDE",
                title="Test Presentation",
                subtitle="Subtitle",
                content_bullets=[("January 2025", 0)],
            ),
            Slide(
                number=2,
                slide_type="SECTION DIVIDER",
                title="First Section",
                content_bullets=[],
            ),
            Slide(
                number=3,
                slide_type="CONTENT",
                title="Content Slide",
                subtitle="Overview",
                content_bullets=[("Point 1", 0), ("Point 2", 1), ("Point 3", 0)],
            ),
            Slide(
                number=4,
                slide_type="CONTENT",
                title="Visual Slide",
                content_bullets=[("Key insight", 0)],
                graphic="A diagram",
            ),
            Slide(
                number=5,
                slide_type="Q&A",
                title="Questions?",
                content_bullets=[],
            ),
        ]
        mock_parse.return_value = slides

        classifications = {
            1: TypeClassification("title", 1.0, "Title", "add_title_slide"),
            2: TypeClassification("section", 1.0, "Section", "add_section_break"),
            3: TypeClassification("content", 0.95, "Content", "add_content_slide"),
            4: TypeClassification(
                "text_image", 0.9, "Text+Image", "add_text_and_image_slide"
            ),
            5: TypeClassification("section", 1.0, "Q&A", "add_section_break"),
        }

        mock_classifier = MagicMock()
        mock_classifier.classify_slide.side_effect = [
            classifications[i] for i in range(1, 6)
        ]
        mock_classifier_class.return_value = mock_classifier

        mock_template = MagicMock()
        mock_get_template.return_value = mock_template

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as output_dir:
                result = assemble_presentation(
                    markdown_path=temp_path,
                    template_id="cfa",
                    output_dir=output_dir,
                    skip_images=True,
                )

                # Verify all slides were processed
                assert mock_classifier.classify_slide.call_count == 5

                # Verify correct template methods called
                mock_template.add_title_slide.assert_called_once()
                assert mock_template.add_section_break.call_count == 2
                mock_template.add_content_slide.assert_called()

                # Verify save was called
                mock_template.save.assert_called_once()
                assert result.endswith(".pptx")
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_slide_with_no_subtitle(self):
        """Test adding slide without subtitle."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        mock_template = MagicMock()

        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Title Only",
            subtitle=None,
            content_bullets=[],
        )

        classification = TypeClassification(
            slide_type="title",
            confidence=1.0,
            reasoning="Title",
            template_method="add_title_slide",
        )

        _add_slide_to_presentation(
            mock_template, slide, classification, {}, Path("/tmp")
        )

        # Verify empty string used for subtitle
        call_args = mock_template.add_title_slide.call_args
        assert call_args[0][1] == ""  # subtitle should be empty string

    def test_slide_with_empty_content_bullets(self):
        """Test adding content slide with no bullets."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        mock_template = MagicMock()

        slide = Slide(
            number=2,
            slide_type="CONTENT",
            title="Empty Content",
            subtitle="No points",
            content_bullets=[],
        )

        classification = TypeClassification(
            slide_type="content",
            confidence=0.8,
            reasoning="Content",
            template_method="add_content_slide",
        )

        _add_slide_to_presentation(
            mock_template, slide, classification, {}, Path("/tmp")
        )

        mock_template.add_content_slide.assert_called_once_with(
            "Empty Content", "No points", []
        )

    def test_title_slide_with_multiple_date_candidates(self):
        """Test title slide with multiple date-like strings."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        mock_template = MagicMock()

        slide = Slide(
            number=1,
            slide_type="TITLE SLIDE",
            title="Conference",
            subtitle="",
            content_bullets=[
                ("March 2024", 0),  # First match should be used
                ("Conference in April 2025", 0),
            ],
        )

        classification = TypeClassification(
            slide_type="title",
            confidence=1.0,
            reasoning="Title",
            template_method="add_title_slide",
        )

        _add_slide_to_presentation(
            mock_template, slide, classification, {}, Path("/tmp")
        )

        call_args = mock_template.add_title_slide.call_args
        assert call_args[0][2] == "March 2024"  # First match

    def test_image_path_conversion_to_string(self):
        """Test that Path objects are converted to strings for image paths."""
        from plugin.lib.presentation.assembler import _add_slide_to_presentation

        mock_template = MagicMock()

        slide = Slide(
            number=3,
            slide_type="CONTENT",
            title="Image Slide",
            subtitle="",
            content_bullets=[],
            graphic="A chart",
        )

        classification = TypeClassification(
            slide_type="image",
            confidence=0.95,
            reasoning="Image",
            template_method="add_image_slide",
        )

        image_paths = {3: Path("/tmp/images/slide-3.jpg")}

        _add_slide_to_presentation(
            mock_template, slide, classification, image_paths, Path("/tmp/images")
        )

        # Verify string path was passed
        call_args = mock_template.add_image_slide.call_args
        assert isinstance(call_args[0][1], str)
        # Use os.path.normpath to handle platform-specific path separators
        assert os.path.normpath(call_args[0][1]) == os.path.normpath(
            "/tmp/images/slide-3.jpg"
        )
