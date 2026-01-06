"""
Unit tests for plugin/lib/presentation/image_generator.py

Tests the image generation functions for presentation slides using Google Gemini API.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


# Mock google.genai before importing the module
@pytest.fixture(autouse=True)
def mock_genai():
    """Mock google.genai module for all tests."""
    mock_types = MagicMock()
    mock_types.GenerateContentConfig = MagicMock
    mock_types.ImageConfig = MagicMock
    mock_types.HttpOptions = MagicMock

    mock_genai = MagicMock()
    mock_genai.types = mock_types
    mock_genai.Client = MagicMock

    with patch.dict("sys.modules", {"google": MagicMock(), "google.genai": mock_genai}):
        yield mock_genai


class TestLoadStyleConfig:
    """Tests for load_style_config function."""

    def test_load_style_config_valid_json(self, tmp_path):
        """Test loading a valid JSON style configuration."""
        from plugin.lib.presentation.image_generator import load_style_config

        style_content = {
            "style": "professional",
            "tone": "corporate",
            "visual_elements": "geometric shapes",
        }

        style_file = tmp_path / "style.json"
        style_file.write_text(json.dumps(style_content))

        result = load_style_config(str(style_file))
        assert result == style_content

    def test_load_style_config_with_trailing_commas(self, tmp_path):
        """Test loading JSON with trailing commas (common JSON error)."""
        from plugin.lib.presentation.image_generator import load_style_config

        # JSON with trailing commas - should be cleaned
        json_with_trailing = """{
            "style": "modern",
            "colors": ["blue", "red",],
            "settings": {"key": "value",},
        }"""

        style_file = tmp_path / "style_trailing.json"
        style_file.write_text(json_with_trailing)

        result = load_style_config(str(style_file))
        assert result["style"] == "modern"
        assert result["colors"] == ["blue", "red"]
        assert result["settings"] == {"key": "value"}

    def test_load_style_config_file_not_found(self):
        """Test FileNotFoundError when style file doesn't exist."""
        from plugin.lib.presentation.image_generator import load_style_config

        with pytest.raises(FileNotFoundError) as exc_info:
            load_style_config("/nonexistent/path/style.json")

        assert "Style configuration file not found" in str(exc_info.value)

    def test_load_style_config_invalid_json(self, tmp_path):
        """Test ValueError for invalid JSON content."""
        from plugin.lib.presentation.image_generator import load_style_config

        invalid_json = "{ this is not valid json }"

        style_file = tmp_path / "invalid.json"
        style_file.write_text(invalid_json)

        with pytest.raises(ValueError) as exc_info:
            load_style_config(str(style_file))

        assert "Invalid JSON in style file" in str(exc_info.value)

    def test_load_style_config_empty_file(self, tmp_path):
        """Test loading an empty JSON file."""
        from plugin.lib.presentation.image_generator import load_style_config

        style_file = tmp_path / "empty.json"
        style_file.write_text("{}")

        result = load_style_config(str(style_file))
        assert result == {}


class TestGetSlideField:
    """Tests for _get_slide_field helper function."""

    def test_get_slide_field_from_dict(self):
        """Test getting field from dictionary."""
        from plugin.lib.presentation.image_generator import _get_slide_field

        slide = {"number": 1, "title": "Test Title", "content": "Test content"}

        assert _get_slide_field(slide, "number") == 1
        assert _get_slide_field(slide, "title") == "Test Title"
        assert _get_slide_field(slide, "content") == "Test content"

    def test_get_slide_field_from_dict_with_default(self):
        """Test getting missing field returns default."""
        from plugin.lib.presentation.image_generator import _get_slide_field

        slide = {"number": 1}

        assert _get_slide_field(slide, "missing") is None
        assert _get_slide_field(slide, "missing", "default") == "default"

    def test_get_slide_field_from_object(self):
        """Test getting field from object with attributes."""
        from plugin.lib.presentation.image_generator import _get_slide_field

        class SlideObject:
            def __init__(self):
                self.number = 5
                self.title = "Object Title"

        slide = SlideObject()

        assert _get_slide_field(slide, "number") == 5
        assert _get_slide_field(slide, "title") == "Object Title"

    def test_get_slide_field_from_object_with_default(self):
        """Test getting missing attribute returns default."""
        from plugin.lib.presentation.image_generator import _get_slide_field

        class SlideObject:
            number = 1

        slide = SlideObject()

        assert _get_slide_field(slide, "missing") is None
        assert _get_slide_field(slide, "missing", "fallback") == "fallback"


class TestFormatStyleConfig:
    """Tests for _format_style_config helper function."""

    def test_format_style_config_basic(self):
        """Test formatting style config as JSON string."""
        from plugin.lib.presentation.image_generator import _format_style_config

        config = {"style": "modern", "tone": "professional"}

        result = _format_style_config(config)

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == config

    def test_format_style_config_nested(self):
        """Test formatting nested style config."""
        from plugin.lib.presentation.image_generator import _format_style_config

        config = {
            "style": "clean",
            "colors": {"primary": "#FF0000", "secondary": "#00FF00"},
            "elements": ["shapes", "lines"],
        }

        result = _format_style_config(config)

        parsed = json.loads(result)
        assert parsed == config
        # Should be indented
        assert "\n" in result

    def test_format_style_config_empty(self):
        """Test formatting empty config."""
        from plugin.lib.presentation.image_generator import _format_style_config

        result = _format_style_config({})
        assert result == "{}"


class TestGenerateSlideImage:
    """Tests for generate_slide_image function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_slide = {
            "number": 1,
            "title": "Test Slide",
            "content": "Test content here",
            "graphic": "A professional diagram showing data flow",
        }
        self.sample_style = {
            "style": "professional",
            "tone": "corporate",
        }

    def test_generate_slide_image_no_genai_available(self, tmp_path, capsys):
        """Test graceful handling when google-genai is not installed."""
        with patch(
            "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", False
        ):
            from plugin.lib.presentation.image_generator import generate_slide_image

            result = generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert result is None
            captured = capsys.readouterr()
            assert "google-genai package not installed" in captured.out

    def test_generate_slide_image_no_api_key(self, tmp_path, capsys):
        """Test handling when no API key is provided."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch.dict(os.environ, {}, clear=True),
        ):
            from plugin.lib.presentation.image_generator import generate_slide_image

            result = generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key=None,
            )

            assert result is None
            captured = capsys.readouterr()
            assert "GOOGLE_API_KEY not found" in captured.out

    def test_generate_slide_image_uses_env_api_key(self, tmp_path):
        """Test that API key is read from environment variable."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch.dict(os.environ, {"GOOGLE_API_KEY": "env-api-key"}),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.parts = []
            mock_response.candidates = []
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.image_generator import (
                generate_slide_image,
            )

            generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
            )

            # Verify client was created with env API key
            mock_genai.Client.assert_called()
            call_kwargs = mock_genai.Client.call_args
            assert call_kwargs[1]["api_key"] == "env-api-key"

    def test_generate_slide_image_no_graphic_description(self, tmp_path):
        """Test skipping when slide has no graphic description."""
        with patch(
            "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
        ):
            from plugin.lib.presentation.image_generator import generate_slide_image

            slide_no_graphic = {
                "number": 1,
                "title": "No Graphics",
                "graphic": "",  # Empty graphic
            }

            result = generate_slide_image(
                slide=slide_no_graphic,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert result is None

    def test_generate_slide_image_whitespace_only_graphic(self, tmp_path):
        """Test skipping when graphic description is whitespace only."""
        with patch(
            "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
        ):
            from plugin.lib.presentation.image_generator import generate_slide_image

            slide_whitespace = {
                "number": 1,
                "title": "Whitespace Graphics",
                "graphic": "   \n\t  ",  # Whitespace only
            }

            result = generate_slide_image(
                slide=slide_whitespace,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert result is None

    def test_generate_slide_image_file_exists_no_force(self, tmp_path, capsys):
        """Test skipping when file exists and force=False."""
        with patch(
            "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
        ):
            from plugin.lib.presentation.image_generator import generate_slide_image

            # Create existing file
            existing_file = tmp_path / "slide-1.jpg"
            existing_file.write_bytes(b"existing image data")

            result = generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
                force=False,
            )

            assert result == existing_file
            captured = capsys.readouterr()
            assert "Skipping" in captured.out
            assert "File exists" in captured.out

    def test_generate_slide_image_file_exists_with_force(self, tmp_path):
        """Test overwriting when file exists and force=True."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            # Set up mock client and response
            mock_client = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = MagicMock()
            mock_part.inline_data.data = b"new image data"
            mock_response = MagicMock()
            mock_response.parts = [mock_part]
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.image_generator import generate_slide_image

            # Create existing file
            existing_file = tmp_path / "slide-1.jpg"
            existing_file.write_bytes(b"old image data")

            result = generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
                force=True,
            )

            assert result == existing_file
            # Verify file was overwritten
            assert existing_file.read_bytes() == b"new image data"

    def test_generate_slide_image_successful_generation(self, tmp_path, capsys):
        """Test successful image generation."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
            patch("plugin.lib.presentation.image_generator.types") as mock_types,
        ):
            mock_types.GenerateContentConfig = MagicMock
            mock_types.ImageConfig = MagicMock
            mock_types.HttpOptions = MagicMock

            # Set up mock client and response
            mock_client = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = MagicMock()
            mock_part.inline_data.data = b"generated image bytes"
            mock_response = MagicMock()
            mock_response.parts = [mock_part]
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.image_generator import (
                generate_slide_image,
            )

            result = generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            expected_path = tmp_path / "slide-1.jpg"
            assert result == expected_path
            assert expected_path.exists()
            assert expected_path.read_bytes() == b"generated image bytes"

            captured = capsys.readouterr()
            assert "Success" in captured.out

    def test_generate_slide_image_uses_prompt_override(self, tmp_path):
        """Test that prompt_override is used instead of graphic field."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                refined_prompt = "A refined, improved visual description"

                generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                    prompt_override=refined_prompt,
                )

                # Verify the prompt used contains the override
                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert refined_prompt in prompt

    def test_generate_slide_image_notext_mode(self, tmp_path):
        """Test that notext=True adds instruction to avoid text."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                    notext=True,
                )

                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert "Do not render any text" in prompt

    def test_generate_slide_image_with_text_allowed(self, tmp_path):
        """Test that notext=False does not add text avoidance instruction."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                    notext=False,
                )

                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert "Do not render any text" not in prompt

    def test_generate_slide_image_fast_mode(self, tmp_path):
        """Test that fast_mode uses standard resolution."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
            patch("plugin.lib.presentation.image_generator.types") as mock_types,
        ):
            mock_image_config = MagicMock()
            mock_types.ImageConfig = mock_image_config

            mock_client = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = MagicMock()
            mock_part.inline_data.data = b"image data"
            mock_response = MagicMock()
            mock_response.parts = [mock_part]
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.image_generator import (
                generate_slide_image,
            )

            generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
                fast_mode=True,
            )

            # In fast mode, image_size should be None (not 4K)
            call_args = mock_image_config.call_args
            assert call_args[1]["image_size"] is None

    def test_generate_slide_image_4k_mode(self, tmp_path):
        """Test that fast_mode=False uses 4K resolution."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
            patch("plugin.lib.presentation.image_generator.types") as mock_types,
        ):
            mock_image_config = MagicMock()
            mock_types.ImageConfig = mock_image_config

            mock_client = MagicMock()
            mock_part = MagicMock()
            mock_part.inline_data = MagicMock()
            mock_part.inline_data.data = b"image data"
            mock_response = MagicMock()
            mock_response.parts = [mock_part]
            mock_client.models.generate_content.return_value = mock_response
            mock_genai.Client.return_value = mock_client

            from plugin.lib.presentation.image_generator import (
                generate_slide_image,
            )

            generate_slide_image(
                slide=self.sample_slide,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
                fast_mode=False,
            )

            # In default mode, image_size should be "4K"
            call_args = mock_image_config.call_args
            assert call_args[1]["image_size"] == "4K"

    def test_generate_slide_image_no_image_in_response(self, tmp_path, capsys):
        """Test handling when API returns no image."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                with patch("plugin.lib.presentation.image_generator.time.sleep"):
                    mock_client = MagicMock()
                    mock_response = MagicMock()
                    mock_response.parts = []  # No parts
                    mock_response.candidates = []
                    mock_client.models.generate_content.return_value = mock_response
                    mock_genai.Client.return_value = mock_client

                    from plugin.lib.presentation.image_generator import (
                        generate_slide_image,
                    )

                    result = generate_slide_image(
                        slide=self.sample_slide,
                        style_config=self.sample_style,
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                    assert result is None
                    captured = capsys.readouterr()
                    assert "No image returned" in captured.out
                    assert "Failed to generate" in captured.out

    def test_generate_slide_image_safety_block(self, tmp_path, capsys):
        """Test handling when image is blocked by safety filters."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.parts = []
                mock_candidate = MagicMock()
                mock_candidate.finish_reason = "SAFETY"
                mock_response.candidates = [mock_candidate]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                result = generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                )

                assert result is None
                captured = capsys.readouterr()
                assert "BLOCKED" in captured.out
                assert "safety filters" in captured.out

    def test_generate_slide_image_api_exception_retries(self, tmp_path, capsys):
        """Test retry logic on API exceptions."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                with patch(
                    "plugin.lib.presentation.image_generator.time.sleep"
                ) as mock_sleep:
                    mock_client = MagicMock()
                    # Fail twice, then succeed
                    mock_part = MagicMock()
                    mock_part.inline_data = MagicMock()
                    mock_part.inline_data.data = b"image data"
                    mock_success = MagicMock()
                    mock_success.parts = [mock_part]

                    mock_client.models.generate_content.side_effect = [
                        Exception("API Error 1"),
                        Exception("API Error 2"),
                        mock_success,
                    ]
                    mock_genai.Client.return_value = mock_client

                    from plugin.lib.presentation.image_generator import (
                        generate_slide_image,
                    )

                    result = generate_slide_image(
                        slide=self.sample_slide,
                        style_config=self.sample_style,
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                    assert result is not None
                    # Should have slept between retries
                    assert mock_sleep.call_count == 2

    def test_generate_slide_image_all_retries_fail(self, tmp_path, capsys):
        """Test failure after all retries exhausted."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                with patch("plugin.lib.presentation.image_generator.time.sleep"):
                    mock_client = MagicMock()
                    mock_client.models.generate_content.side_effect = Exception(
                        "Persistent API Error"
                    )
                    mock_genai.Client.return_value = mock_client

                    from plugin.lib.presentation.image_generator import (
                        generate_slide_image,
                    )

                    result = generate_slide_image(
                        slide=self.sample_slide,
                        style_config=self.sample_style,
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                    assert result is None
                    captured = capsys.readouterr()
                    assert "Failed to generate" in captured.out
                    assert "3 attempts" in captured.out

    def test_generate_slide_image_uses_slide_number_field(self, tmp_path):
        """Test that slide_number field is used if number is missing."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                slide = {
                    "slide_number": 5,
                    "title": "Test",
                    "graphic": "A visual",
                }

                result = generate_slide_image(
                    slide=slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                )

                expected_path = tmp_path / "slide-5.jpg"
                assert result == expected_path

    def test_generate_slide_image_creates_output_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                nested_output = tmp_path / "nested" / "output" / "dir"
                assert not nested_output.exists()

                generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=nested_output,
                    api_key="test-key",
                )

                assert nested_output.exists()

    def test_generate_slide_image_response_with_multiple_parts(self, tmp_path):
        """Test handling response with multiple parts (uses first image)."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()

                # First part without inline_data
                mock_part1 = MagicMock()
                mock_part1.inline_data = None

                # Second part with inline_data
                mock_part2 = MagicMock()
                mock_part2.inline_data = MagicMock()
                mock_part2.inline_data.data = b"actual image data"

                mock_response = MagicMock()
                mock_response.parts = [mock_part1, mock_part2]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                result = generate_slide_image(
                    slide=self.sample_slide,
                    style_config=self.sample_style,
                    output_dir=tmp_path,
                    api_key="test-key",
                )

                assert result is not None
                assert result.read_bytes() == b"actual image data"


class TestGenerateAllImages:
    """Tests for generate_all_images function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_slides = [
            {"number": 1, "title": "Slide 1", "graphic": "Visual 1"},
            {"number": 2, "title": "Slide 2", "graphic": "Visual 2"},
            {"number": 3, "title": "Slide 3", "graphic": "Visual 3"},
        ]
        self.sample_style = {"style": "professional"}

    def test_generate_all_images_empty_list(self, tmp_path, capsys):
        """Test generating images for empty slide list."""
        with patch(
            "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
        ):
            from plugin.lib.presentation.image_generator import generate_all_images

            result = generate_all_images(
                slides=[],
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert result == {}
            captured = capsys.readouterr()
            assert "Total Slides: 0" in captured.out

    def test_generate_all_images_calls_generate_slide_image(self, tmp_path):
        """Test that generate_all_images calls generate_slide_image for each slide."""
        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.side_effect = [
                tmp_path / "slide-1.jpg",
                tmp_path / "slide-2.jpg",
                tmp_path / "slide-3.jpg",
            ]

            from plugin.lib.presentation.image_generator import generate_all_images

            generate_all_images(
                slides=self.sample_slides,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert mock_generate.call_count == 3

    def test_generate_all_images_returns_results_dict(self, tmp_path):
        """Test that results dictionary maps slide numbers to paths."""
        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.side_effect = [
                tmp_path / "slide-1.jpg",
                tmp_path / "slide-2.jpg",
                None,  # Third slide fails
            ]

            from plugin.lib.presentation.image_generator import generate_all_images

            result = generate_all_images(
                slides=self.sample_slides,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            assert 1 in result
            assert 2 in result
            assert 3 not in result  # Failed slide not in results
            assert result[1] == tmp_path / "slide-1.jpg"

    def test_generate_all_images_with_callback(self, tmp_path):
        """Test callback is called after each slide."""
        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.side_effect = [
                tmp_path / "slide-1.jpg",
                None,
                tmp_path / "slide-3.jpg",
            ]

            callback_calls = []

            def test_callback(slide_num, success, path):
                callback_calls.append((slide_num, success, path))

            from plugin.lib.presentation.image_generator import generate_all_images

            generate_all_images(
                slides=self.sample_slides,
                style_config=self.sample_style,
                output_dir=tmp_path,
                callback=test_callback,
                api_key="test-key",
            )

            assert len(callback_calls) == 3
            assert callback_calls[0] == (1, True, tmp_path / "slide-1.jpg")
            assert callback_calls[1] == (2, False, None)
            assert callback_calls[2] == (3, True, tmp_path / "slide-3.jpg")

    def test_generate_all_images_passes_options(self, tmp_path):
        """Test that options are passed to generate_slide_image."""
        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.return_value = tmp_path / "slide-1.jpg"

            from plugin.lib.presentation.image_generator import generate_all_images

            generate_all_images(
                slides=[self.sample_slides[0]],
                style_config=self.sample_style,
                output_dir=tmp_path,
                fast_mode=True,
                notext=False,
                force=True,
                api_key="custom-key",
            )

            call_kwargs = mock_generate.call_args[1]
            assert call_kwargs["fast_mode"] is True
            assert call_kwargs["notext"] is False
            assert call_kwargs["force"] is True
            assert call_kwargs["api_key"] == "custom-key"

    def test_generate_all_images_prints_summary(self, tmp_path, capsys):
        """Test summary output after batch generation."""
        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.side_effect = [
                tmp_path / "slide-1.jpg",
                None,
                tmp_path / "slide-3.jpg",
            ]

            from plugin.lib.presentation.image_generator import generate_all_images

            generate_all_images(
                slides=self.sample_slides,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            captured = capsys.readouterr()
            assert "Batch Generation Complete" in captured.out
            assert "Successfully generated: 2/3" in captured.out

    def test_generate_all_images_uses_index_for_missing_number(self, tmp_path):
        """Test slides without number field use list index."""
        slides_no_number = [
            {"title": "Slide A", "graphic": "Visual A"},
            {"title": "Slide B", "graphic": "Visual B"},
        ]

        with patch(
            "plugin.lib.presentation.image_generator.generate_slide_image"
        ) as mock_generate:
            mock_generate.return_value = tmp_path / "slide.jpg"

            from plugin.lib.presentation.image_generator import generate_all_images

            generate_all_images(
                slides=slides_no_number,
                style_config=self.sample_style,
                output_dir=tmp_path,
                api_key="test-key",
            )

            # Check the slide numbers extracted
            # The function uses index (1-based) when number field is missing
            assert mock_generate.call_count == 2


class TestGetStyleInstruction:
    """Tests for get_style_instruction convenience function."""

    def test_get_style_instruction_returns_formatted_json(self, tmp_path):
        """Test get_style_instruction returns formatted JSON string."""
        from plugin.lib.presentation.image_generator import get_style_instruction

        style_content = {"style": "modern", "tone": "casual"}
        style_file = tmp_path / "style.json"
        style_file.write_text(json.dumps(style_content))

        result = get_style_instruction(str(style_file))

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == style_content

    def test_get_style_instruction_file_not_found(self):
        """Test FileNotFoundError is raised for missing file."""
        from plugin.lib.presentation.image_generator import get_style_instruction

        with pytest.raises(FileNotFoundError):
            get_style_instruction("/nonexistent/style.json")


class TestConstants:
    """Tests for module constants."""

    def test_model_id_constant(self):
        """Test MODEL_ID constant value."""
        from plugin.lib.presentation.image_generator import MODEL_ID

        assert MODEL_ID == "gemini-3-pro-image-preview"

    def test_max_retries_constant(self):
        """Test MAX_RETRIES constant value."""
        from plugin.lib.presentation.image_generator import MAX_RETRIES

        assert MAX_RETRIES == 3

    def test_retry_delay_constant(self):
        """Test RETRY_DELAY constant value."""
        from plugin.lib.presentation.image_generator import RETRY_DELAY

        assert RETRY_DELAY == 5

    def test_default_style_constant(self):
        """Test DEFAULT_STYLE constant structure."""
        from plugin.lib.presentation.image_generator import DEFAULT_STYLE

        assert "style" in DEFAULT_STYLE
        assert "tone" in DEFAULT_STYLE
        assert "visual_elements" in DEFAULT_STYLE


class TestSlideObjectSupport:
    """Tests for Slide object (dataclass) support."""

    def test_generate_slide_image_with_slide_object(self, tmp_path):
        """Test generate_slide_image works with Slide-like objects."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_part = MagicMock()
                mock_part.inline_data = MagicMock()
                mock_part.inline_data.data = b"image data"
                mock_response = MagicMock()
                mock_response.parts = [mock_part]
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                # Create a Slide-like object
                class MockSlide:
                    def __init__(self):
                        self.number = 7
                        self.title = "Object Slide"
                        self.content = "Object content"
                        self.graphic = "Object visual description"

                slide_obj = MockSlide()

                result = generate_slide_image(
                    slide=slide_obj,
                    style_config={"style": "modern"},
                    output_dir=tmp_path,
                    api_key="test-key",
                )

                expected_path = tmp_path / "slide-7.jpg"
                assert result == expected_path


class TestPromptConstruction:
    """Tests for proper prompt construction."""

    def test_prompt_includes_style_config(self, tmp_path):
        """Test that prompt includes formatted style configuration."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.parts = []
                mock_response.candidates = []
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                style_config = {
                    "style": "minimalist",
                    "brand_colors": ["#FF0000"],
                }

                slide = {
                    "number": 1,
                    "title": "Test",
                    "graphic": "A visual",
                }

                with patch("plugin.lib.presentation.image_generator.time.sleep"):
                    generate_slide_image(
                        slide=slide,
                        style_config=style_config,
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert "minimalist" in prompt
                assert "#FF0000" in prompt

    def test_prompt_includes_slide_context(self, tmp_path):
        """Test that prompt includes slide title and content."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.parts = []
                mock_response.candidates = []
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                slide = {
                    "number": 1,
                    "title": "Unique Test Title ABC",
                    "content": "Unique content XYZ",
                    "graphic": "A visual",
                }

                with patch("plugin.lib.presentation.image_generator.time.sleep"):
                    generate_slide_image(
                        slide=slide,
                        style_config={"style": "modern"},
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert "Unique Test Title ABC" in prompt
                assert "Unique content XYZ" in prompt

    def test_prompt_without_title_and_content(self, tmp_path):
        """Test prompt construction when slide has no title or content."""
        with (
            patch(
                "plugin.lib.presentation.image_generator.GOOGLE_GENAI_AVAILABLE", True
            ),
            patch("plugin.lib.presentation.image_generator.genai") as mock_genai,
        ):
            with patch("plugin.lib.presentation.image_generator.types"):
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.parts = []
                mock_response.candidates = []
                mock_client.models.generate_content.return_value = mock_response
                mock_genai.Client.return_value = mock_client

                from plugin.lib.presentation.image_generator import (
                    generate_slide_image,
                )

                slide = {
                    "number": 1,
                    "graphic": "A visual description only",
                }

                with patch("plugin.lib.presentation.image_generator.time.sleep"):
                    generate_slide_image(
                        slide=slide,
                        style_config={"style": "modern"},
                        output_dir=tmp_path,
                        api_key="test-key",
                    )

                call_args = mock_client.models.generate_content.call_args
                prompt = call_args[1]["contents"]
                assert "No additional context" in prompt
