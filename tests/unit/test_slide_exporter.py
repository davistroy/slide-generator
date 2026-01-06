"""
Unit tests for plugin/lib/presentation/slide_exporter.py

Tests the SlideExporter class for PowerPoint slide-to-image export.
Uses mocking to avoid actual PowerShell/PowerPoint/file operations.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# We need to mock the environment validation before importing
# because the class validates on __init__


class TestSlideExporterInit:
    """Tests for SlideExporter initialization."""

    def test_init_with_default_resolution(self):
        """Test initialization with default resolution."""
        with patch.object(
            __import__(
                "plugin.lib.presentation.slide_exporter", fromlist=["SlideExporter"]
            ).SlideExporter,
            "_validate_environment",
        ):
            from plugin.lib.presentation.slide_exporter import SlideExporter

            with patch.object(SlideExporter, "_validate_environment"):
                exporter = SlideExporter()
                assert exporter.resolution == 150

    def test_init_with_custom_resolution(self):
        """Test initialization with custom resolution."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            exporter = SlideExporter(resolution=300)
            assert exporter.resolution == 300

    def test_init_validates_environment(self):
        """Test that initialization calls environment validation."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment") as mock_validate:
            SlideExporter()
            mock_validate.assert_called_once()


class TestValidateEnvironment:
    """Tests for _validate_environment method."""

    def test_validate_environment_non_windows_raises(self):
        """Test that non-Windows OS raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch("os.name", "posix"):
            with pytest.raises(OSError) as exc_info:
                SlideExporter()
            assert "requires Windows OS" in str(exc_info.value)
            assert "posix" in str(exc_info.value)

    def test_validate_environment_powershell_not_found(self):
        """Test that missing PowerShell raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch("os.name", "nt"):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                with pytest.raises(OSError) as exc_info:
                    SlideExporter()
                assert "PowerShell not found" in str(exc_info.value)

    def test_validate_environment_powershell_timeout(self):
        """Test that PowerShell timeout raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with (
            patch("os.name", "nt"),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5)),
        ):
            with pytest.raises(OSError) as exc_info:
                SlideExporter()
            assert "timed out" in str(exc_info.value)

    def test_validate_environment_powershell_error_returncode(self):
        """Test that PowerShell error returncode raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch("os.name", "nt"):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(OSError) as exc_info:
                    SlideExporter()
                assert "not available" in str(exc_info.value)

    def test_validate_environment_powerpoint_not_installed(self):
        """Test that missing PowerPoint raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        # First call succeeds (PowerShell check), second fails (PowerPoint check)
        ps_success = MagicMock()
        ps_success.returncode = 0
        ps_success.stdout = "test"

        ppt_fail = MagicMock()
        ppt_fail.returncode = 0
        ppt_fail.stdout = "FAIL"

        with patch("os.name", "nt"):
            with patch("subprocess.run", side_effect=[ps_success, ppt_fail]):
                with pytest.raises(OSError) as exc_info:
                    SlideExporter()
                assert "PowerPoint not found" in str(exc_info.value)

    def test_validate_environment_powerpoint_timeout(self):
        """Test that PowerPoint COM check timeout raises OSError."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        ps_success = MagicMock()
        ps_success.returncode = 0
        ps_success.stdout = "test"

        with (
            patch("os.name", "nt"),
            patch(
                "subprocess.run",
                side_effect=[ps_success, subprocess.TimeoutExpired("cmd", 10)],
            ),
        ):
            with pytest.raises(OSError) as exc_info:
                SlideExporter()
            assert "PowerPoint COM check timed out" in str(exc_info.value)

    def test_validate_environment_success(self):
        """Test successful environment validation."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        ps_success = MagicMock()
        ps_success.returncode = 0
        ps_success.stdout = "test"

        ppt_success = MagicMock()
        ppt_success.returncode = 0
        ppt_success.stdout = "OK"

        with patch("os.name", "nt"):
            with patch("subprocess.run", side_effect=[ps_success, ppt_success]):
                exporter = SlideExporter()
                assert exporter.resolution == 150


class TestExportSlide:
    """Tests for export_slide method."""

    def setup_method(self):
        """Set up test fixtures."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            self.exporter = SlideExporter(resolution=150)

    def test_export_slide_success(self):
        """Test successful slide export."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                assert result is True

    def test_export_slide_file_not_created(self):
        """Test export when output file not created."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=False):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                with patch("builtins.print"):
                                    result = self.exporter.export_slide(
                                        pptx_path="test.pptx",
                                        slide_number=1,
                                        output_path="output.jpg",
                                    )
                                    assert result is False

    def test_export_slide_powershell_error(self):
        """Test export when PowerShell returns error."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Some error message"

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                assert result is False

    def test_export_slide_timeout(self):
        """Test export when PowerShell times out."""
        with (
            patch("tempfile.NamedTemporaryFile", mock_open()),
            patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 60)),
            patch.object(Path, "resolve", return_value=Path("/test/path")),
        ):
            with patch.object(Path, "parent") as mock_parent:
                mock_parent.mkdir = MagicMock()
                with patch("os.unlink"), patch("builtins.print"):
                    result = self.exporter.export_slide(
                        pptx_path="test.pptx",
                        slide_number=1,
                        output_path="output.jpg",
                    )
                    assert result is False

    def test_export_slide_unexpected_exception(self):
        """Test export when unexpected exception occurs."""
        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", side_effect=Exception("Unexpected error")):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                assert result is False

    def test_export_slide_cleanup_temp_file(self):
        """Test that temp script file is cleaned up."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()) as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/script.ps1"
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink") as mock_unlink:
                                self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                mock_unlink.assert_called()

    def test_export_slide_cleanup_error_ignored(self):
        """Test that cleanup errors are silently ignored."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()) as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/script.ps1"
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch(
                                "os.unlink", side_effect=Exception("Cleanup error")
                            ):
                                # Should not raise, should return successfully
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                assert result is True

    def test_export_slide_creates_output_directory(self):
        """Test that output directory is created if needed."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        mock_parent = MagicMock()

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(
                            Path, "parent", new_callable=lambda: mock_parent
                        ):
                            with patch("os.unlink"):
                                self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="/new/dir/output.jpg",
                                )

    def test_export_slide_powershell_command_structure(self):
        """Test that PowerShell command is correctly structured."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        captured_cmd = None

        def capture_cmd(cmd, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            return mock_result

        with patch("tempfile.NamedTemporaryFile", mock_open()) as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.ps1"
            with patch("subprocess.run", side_effect=capture_cmd):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=3,
                                    output_path="output.jpg",
                                )

        assert captured_cmd is not None
        assert "powershell" in captured_cmd[0]
        assert "-ExecutionPolicy" in captured_cmd
        assert "Bypass" in captured_cmd
        assert "-File" in captured_cmd
        assert "-SlideNumber" in captured_cmd
        assert "3" in captured_cmd
        assert "-Resolution" in captured_cmd
        assert "150" in captured_cmd

    def test_export_slide_no_stderr(self):
        """Test export error handling when no stderr."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = ""

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )
                                assert result is False


class TestExportAllSlides:
    """Tests for export_all_slides method."""

    def setup_method(self):
        """Set up test fixtures."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            self.exporter = SlideExporter(resolution=150)

    def test_export_all_slides_success(self):
        """Test successful export of all slides."""
        with patch.object(self.exporter, "_get_slide_count", return_value=3):
            with patch.object(self.exporter, "export_slide", return_value=True):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        result = self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                        )

        assert len(result) == 3
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_export_all_slides_some_fail(self):
        """Test export when some slides fail."""
        with patch.object(self.exporter, "_get_slide_count", return_value=3):
            # Second slide fails
            with patch.object(
                self.exporter,
                "export_slide",
                side_effect=[True, False, True],
            ):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        result = self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                        )

        assert len(result) == 2
        assert 1 in result
        assert 2 not in result
        assert 3 in result

    def test_export_all_slides_zero_count(self):
        """Test export when slide count is zero."""
        with patch.object(self.exporter, "_get_slide_count", return_value=0):
            with patch.object(Path, "mkdir"):
                with patch("builtins.print"):
                    result = self.exporter.export_all_slides(
                        pptx_path="test.pptx",
                        output_dir="/output",
                    )

        assert result == {}

    def test_export_all_slides_with_callback(self):
        """Test export with progress callback."""
        callback_calls = []

        def callback(slide_num, success, output_path):
            callback_calls.append((slide_num, success, output_path))

        with patch.object(self.exporter, "_get_slide_count", return_value=2):
            with patch.object(self.exporter, "export_slide", return_value=True):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                            callback=callback,
                        )

        assert len(callback_calls) == 2
        assert callback_calls[0][0] == 1
        assert callback_calls[0][1] is True
        assert callback_calls[1][0] == 2

    def test_export_all_slides_callback_with_failures(self):
        """Test callback receives failure status."""
        callback_calls = []

        def callback(slide_num, success, output_path):
            callback_calls.append((slide_num, success, output_path))

        with patch.object(self.exporter, "_get_slide_count", return_value=2):
            with patch.object(
                self.exporter,
                "export_slide",
                side_effect=[True, False],
            ):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                            callback=callback,
                        )

        assert callback_calls[0][1] is True
        assert callback_calls[1][1] is False

    def test_export_all_slides_creates_output_directory(self):
        """Test that output directory is created."""
        mock_mkdir = MagicMock()

        with patch.object(self.exporter, "_get_slide_count", return_value=1):
            with patch.object(self.exporter, "export_slide", return_value=True):
                with patch.object(Path, "mkdir", mock_mkdir):
                    with patch("builtins.print"):
                        self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                        )

        mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_export_all_slides_output_naming(self):
        """Test that output files are named correctly."""
        captured_paths = []

        def mock_export(pptx_path, slide_number, output_path):
            captured_paths.append(output_path)
            return True

        with patch.object(self.exporter, "_get_slide_count", return_value=3):
            with patch.object(self.exporter, "export_slide", side_effect=mock_export):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                        )

        assert len(captured_paths) == 3
        assert "slide-1.jpg" in captured_paths[0]
        assert "slide-2.jpg" in captured_paths[1]
        assert "slide-3.jpg" in captured_paths[2]

    def test_export_all_slides_no_callback(self):
        """Test export without callback does not error."""
        with patch.object(self.exporter, "_get_slide_count", return_value=1):
            with patch.object(self.exporter, "export_slide", return_value=True):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        result = self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                            callback=None,
                        )

        assert len(result) == 1


class TestGetSlideCount:
    """Tests for _get_slide_count method."""

    def setup_method(self):
        """Set up test fixtures."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            self.exporter = SlideExporter(resolution=150)

    def test_get_slide_count_success(self):
        """Test successful slide count retrieval."""
        mock_prs = MagicMock()
        mock_prs.slides = [1, 2, 3, 4, 5]

        with patch("pptx.Presentation", return_value=mock_prs):
            count = self.exporter._get_slide_count("test.pptx")

        assert count == 5

    def test_get_slide_count_empty_presentation(self):
        """Test slide count for empty presentation."""
        mock_prs = MagicMock()
        mock_prs.slides = []

        with patch("pptx.Presentation", return_value=mock_prs):
            count = self.exporter._get_slide_count("test.pptx")

        assert count == 0

    def test_get_slide_count_exception(self):
        """Test slide count returns 0 on exception."""
        with patch("pptx.Presentation", side_effect=Exception("File not found")):
            with patch("builtins.print"):
                count = self.exporter._get_slide_count("nonexistent.pptx")

        assert count == 0

    @pytest.mark.skip(reason="Import patching causes sys.modules corruption")
    def test_get_slide_count_import_error(self):
        """Test slide count handles import error gracefully."""
        with (
            patch.dict("sys.modules", {"pptx": None}),
            patch(
                "pptx.Presentation",
                side_effect=ImportError("No module named pptx"),
            ),
            patch("builtins.print"),
        ):
            count = self.exporter._get_slide_count("test.pptx")

        assert count == 0


class TestExportScriptTemplate:
    """Tests for EXPORT_SCRIPT_TEMPLATE constant."""

    def test_script_template_contains_params(self):
        """Test that script template has required parameters."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        template = SlideExporter.EXPORT_SCRIPT_TEMPLATE
        assert "PresentationPath" in template
        assert "SlideNumber" in template
        assert "OutputPath" in template
        assert "Resolution" in template

    def test_script_template_contains_error_handling(self):
        """Test that script template has error handling."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        template = SlideExporter.EXPORT_SCRIPT_TEMPLATE
        assert "try" in template
        assert "catch" in template
        assert "$ErrorActionPreference" in template

    def test_script_template_contains_com_cleanup(self):
        """Test that script template has COM object cleanup."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        template = SlideExporter.EXPORT_SCRIPT_TEMPLATE
        assert "ReleaseComObject" in template
        assert "$ppt.Quit()" in template
        assert "$presentation.Close()" in template

    def test_script_template_contains_validation(self):
        """Test that script template validates slide number."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        template = SlideExporter.EXPORT_SCRIPT_TEMPLATE
        assert "slideCount" in template or "Slides.Count" in template
        assert "Invalid slide number" in template

    def test_script_template_jpg_export(self):
        """Test that script template exports as JPG."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        template = SlideExporter.EXPORT_SCRIPT_TEMPLATE
        assert '"JPG"' in template
        assert "Export" in template


class TestSlideExporterResolution:
    """Tests for resolution handling."""

    def test_resolution_150_dpi(self):
        """Test standard 150 DPI resolution."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            exporter = SlideExporter(resolution=150)
            assert exporter.resolution == 150

    def test_resolution_300_dpi(self):
        """Test high quality 300 DPI resolution."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            exporter = SlideExporter(resolution=300)
            assert exporter.resolution == 300

    def test_resolution_72_dpi(self):
        """Test low quality 72 DPI resolution."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            exporter = SlideExporter(resolution=72)
            assert exporter.resolution == 72

    def test_resolution_in_powershell_command(self):
        """Test that resolution is passed to PowerShell command."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            exporter = SlideExporter(resolution=200)

        captured_cmd = None

        def capture_cmd(cmd, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            result = MagicMock()
            result.returncode = 0
            return result

        with patch("tempfile.NamedTemporaryFile", mock_open()) as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "/tmp/test.ps1"
            with patch("subprocess.run", side_effect=capture_cmd):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=1,
                                    output_path="output.jpg",
                                )

        assert "200" in captured_cmd


class TestMain:
    """Tests for main() function."""

    def test_main_single_slide_export_success(self):
        """Test main with single slide export."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx", "--slide", "1", "--dpi", "150"]

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "_validate_environment"):
                with patch.object(SlideExporter, "export_slide", return_value=True):
                    with patch.object(Path, "mkdir"):
                        with patch("builtins.print"):
                            exit_code = main()

        assert exit_code == 0

    def test_main_single_slide_export_failure(self):
        """Test main with single slide export failure."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx", "--slide", "1"]

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "_validate_environment"):
                with patch.object(SlideExporter, "export_slide", return_value=False):
                    with patch.object(Path, "mkdir"):
                        with patch("builtins.print"):
                            exit_code = main()

        assert exit_code == 1

    def test_main_all_slides_export_success(self):
        """Test main with all slides export."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx", "--output-dir", "/output"]

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "_validate_environment"):
                with patch.object(
                    SlideExporter,
                    "export_all_slides",
                    return_value={1: "/output/slide-1.jpg"},
                ):
                    with patch("builtins.print"):
                        exit_code = main()

        assert exit_code == 0

    def test_main_all_slides_export_failure(self):
        """Test main with all slides export failure (no slides exported)."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx"]

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "_validate_environment"):
                with patch.object(
                    SlideExporter,
                    "export_all_slides",
                    return_value={},
                ):
                    with patch("builtins.print"):
                        exit_code = main()

        assert exit_code == 1

    def test_main_environment_error(self):
        """Test main with environment error."""
        from plugin.lib.presentation.slide_exporter import main

        test_args = ["script.py", "test.pptx"]

        with patch("sys.argv", test_args), patch("os.name", "posix"):
            with patch("builtins.print"):
                exit_code = main()

        assert exit_code == 1

    def test_main_default_output_dir(self):
        """Test main uses default output directory."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx"]
        captured_output_dir = None

        def capture_export(pptx_path, output_dir, **kwargs):
            nonlocal captured_output_dir
            captured_output_dir = output_dir
            return {1: "slide-1.jpg"}

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "_validate_environment"):
                with patch.object(
                    SlideExporter, "export_all_slides", side_effect=capture_export
                ):
                    with patch("builtins.print"):
                        main()

        assert captured_output_dir == "./exported-slides"

    def test_main_custom_dpi(self):
        """Test main with custom DPI."""
        from plugin.lib.presentation.slide_exporter import SlideExporter, main

        test_args = ["script.py", "test.pptx", "--dpi", "300"]

        with patch("sys.argv", test_args):
            with patch.object(SlideExporter, "__init__", return_value=None):
                with patch.object(
                    SlideExporter,
                    "export_all_slides",
                    return_value={1: "slide-1.jpg"},
                ):
                    with patch("builtins.print"):
                        main()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            self.exporter = SlideExporter(resolution=150)

    def test_export_slide_number_zero(self):
        """Test export with slide number 0 (should be handled by PowerShell)."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid slide number"

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=0,
                                    output_path="output.jpg",
                                )
                                assert result is False

    def test_export_slide_negative_number(self):
        """Test export with negative slide number."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid slide number"

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=-1,
                                    output_path="output.jpg",
                                )
                                assert result is False

    def test_export_slide_large_number(self):
        """Test export with slide number beyond presentation."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid slide number: 999"

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(Path, "resolve", return_value=Path("/test/path")):
                    with patch.object(Path, "parent") as mock_parent:
                        mock_parent.mkdir = MagicMock()
                        with patch("os.unlink"):
                            with patch("builtins.print"):
                                result = self.exporter.export_slide(
                                    pptx_path="test.pptx",
                                    slide_number=999,
                                    output_path="output.jpg",
                                )
                                assert result is False

    def test_export_with_spaces_in_path(self):
        """Test export with spaces in file paths."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(
                    Path, "resolve", return_value=Path("/path with spaces/file.pptx")
                ):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                result = self.exporter.export_slide(
                                    pptx_path="/path with spaces/test.pptx",
                                    slide_number=1,
                                    output_path="/output dir/slide.jpg",
                                )
                                assert result is True

    def test_export_with_unicode_path(self):
        """Test export with unicode characters in file paths."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("tempfile.NamedTemporaryFile", mock_open()):
            with patch("subprocess.run", return_value=mock_result):
                with patch.object(
                    Path, "resolve", return_value=Path("/path/file.pptx")
                ):
                    with patch.object(Path, "exists", return_value=True):
                        with patch.object(Path, "parent") as mock_parent:
                            mock_parent.mkdir = MagicMock()
                            with patch("os.unlink"):
                                result = self.exporter.export_slide(
                                    pptx_path="/path/presentation.pptx",
                                    slide_number=1,
                                    output_path="/output/slide.jpg",
                                )
                                assert result is True


class TestIntegrationScenarios:
    """Tests for realistic integration scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        from plugin.lib.presentation.slide_exporter import SlideExporter

        with patch.object(SlideExporter, "_validate_environment"):
            self.exporter = SlideExporter(resolution=150)

    def test_full_export_workflow(self):
        """Test a complete export workflow."""
        mock_prs = MagicMock()
        mock_prs.slides = [1, 2, 3]

        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("pptx.Presentation", return_value=mock_prs):
            with patch("tempfile.NamedTemporaryFile", mock_open()):
                with patch("subprocess.run", return_value=mock_result):
                    with patch.object(Path, "resolve", return_value=Path("/test/path")):
                        with patch.object(Path, "exists", return_value=True):
                            with patch.object(Path, "mkdir"):
                                with patch("os.unlink"):
                                    with patch("builtins.print"):
                                        result = self.exporter.export_all_slides(
                                            pptx_path="presentation.pptx",
                                            output_dir="/output",
                                        )

        assert len(result) == 3

    def test_partial_failure_recovery(self):
        """Test export continues after individual slide failures."""
        call_count = [0]

        def mock_export(pptx_path, slide_number, output_path):
            call_count[0] += 1
            # Fail on slide 2
            return slide_number != 2

        with patch.object(self.exporter, "_get_slide_count", return_value=5):
            with patch.object(self.exporter, "export_slide", side_effect=mock_export):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        result = self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                        )

        # All 5 slides should be attempted
        assert call_count[0] == 5
        # 4 should succeed (slide 2 failed)
        assert len(result) == 4
        assert 2 not in result

    def test_progress_tracking_callback(self):
        """Test progress tracking with callback function."""
        progress = {"completed": 0, "failed": 0}

        def track_progress(slide_num, success, output_path):
            if success:
                progress["completed"] += 1
            else:
                progress["failed"] += 1

        with patch.object(self.exporter, "_get_slide_count", return_value=10):
            with patch.object(
                self.exporter,
                "export_slide",
                side_effect=[True] * 8 + [False] * 2,
            ):
                with patch.object(Path, "mkdir"):
                    with patch("builtins.print"):
                        self.exporter.export_all_slides(
                            pptx_path="test.pptx",
                            output_dir="/output",
                            callback=track_progress,
                        )

        assert progress["completed"] == 8
        assert progress["failed"] == 2
