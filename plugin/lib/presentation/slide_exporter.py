"""
Slide-to-image export using PowerShell COM automation.

Exports individual slides from PowerPoint presentations as JPG images
for visual validation workflows.

Requirements:
- Windows OS
- Microsoft PowerPoint 2013+ installed
- PowerShell 5.1+
"""

import contextlib
import os
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path


class SlideExporter:
    """
    Exports PowerPoint slides to images via PowerShell COM automation.

    Uses PowerPoint's COM API through PowerShell to export individual
    slides as JPG images at specified resolution.

    Requirements:
    - Windows OS (PowerShell COM automation)
    - Microsoft PowerPoint installed (Office 2013 or later)
    - PowerShell 5.1 or later
    """

    # PowerShell script template for slide export
    # This script:
    # 1. Opens PowerPoint COM object
    # 2. Opens presentation
    # 3. Exports specific slide to JPG
    # 4. Cleans up COM objects properly
    EXPORT_SCRIPT_TEMPLATE = """
param(
    [string]$PresentationPath,
    [int]$SlideNumber,
    [string]$OutputPath,
    [int]$Resolution = 150
)

$ErrorActionPreference = "Stop"

try {
    # Create PowerPoint COM object
    Write-Host "Initializing PowerPoint COM object..."
    $ppt = New-Object -ComObject PowerPoint.Application
    # Note: Cannot set Visible = False for PowerPoint COM (not supported)
    # PowerPoint will briefly appear during export

    # Open presentation (read-only, no repair prompt, no titlebar updates)
    Write-Host "Opening presentation: $PresentationPath"
    $presentation = $ppt.Presentations.Open($PresentationPath, $true, $false, $false)

    # Validate slide number
    $slideCount = $presentation.Slides.Count
    if ($SlideNumber -lt 1 -or $SlideNumber -gt $slideCount) {
        throw "Invalid slide number: $SlideNumber (presentation has $slideCount slides)"
    }

    # Export single slide
    Write-Host "Exporting slide $SlideNumber to: $OutputPath"
    $slide = $presentation.Slides.Item($SlideNumber)

    # Calculate dimensions (16:9 aspect ratio)
    # Width = Resolution * (16/9) * aspect factor
    # Height = Resolution
    $width = [int]($Resolution * 10.67)  # ~1600 pixels at 150 DPI
    $height = [int]($Resolution * 6)     # ~900 pixels at 150 DPI

    $slide.Export($OutputPath, "JPG", $width, $height)

    # Verify export succeeded
    if (Test-Path $OutputPath) {
        Write-Host "SUCCESS: Exported slide $SlideNumber"
    } else {
        throw "Export failed: Output file not created"
    }

    # Cleanup
    Write-Host "Closing presentation..."
    $presentation.Close()
    $ppt.Quit()

    # Release COM objects
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($slide) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($presentation) | Out-Null
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()

    Write-Host "Export complete!"
    exit 0

} catch {
    Write-Error "PowerPoint export failed: $($_.Exception.Message)"

    # Attempt cleanup on error
    try {
        if ($presentation) { $presentation.Close() }
        if ($ppt) { $ppt.Quit() }
    } catch {
        # Ignore cleanup errors
    }

    exit 1
}
"""

    def __init__(self, resolution: int = 150):
        """
        Initialize slide exporter.

        Args:
            resolution: DPI for exported images (default: 150)
                       Higher values = better quality but larger files
                       Recommended: 150 (validation), 300 (high-quality)

        Raises:
            EnvironmentError: If Windows, PowerShell, or PowerPoint not available
        """
        self.resolution = resolution
        self._validate_environment()

    def _validate_environment(self) -> None:
        """
        Check if Windows + PowerShell + PowerPoint are available.

        Raises:
            EnvironmentError: If environment requirements not met
        """
        # Check Windows OS
        if os.name != "nt":
            raise OSError(
                "SlideExporter requires Windows OS (uses PowerShell COM automation). "
                "Current OS: " + os.name
            )

        # Check PowerShell availability
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Write-Output 'test'"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise OSError(
                    "PowerShell not available or not functioning correctly. "
                    f"Return code: {result.returncode}"
                )
        except FileNotFoundError:
            raise OSError(
                "PowerShell not found. Ensure PowerShell is installed and in PATH."
            )
        except subprocess.TimeoutExpired:
            raise OSError(
                "PowerShell test command timed out. PowerShell may not be functioning."
            )

        # Check PowerPoint availability (via COM check)
        try:
            check_ppt_cmd = [
                "powershell",
                "-Command",
                "try { $ppt = New-Object -ComObject PowerPoint.Application; "
                "$ppt.Quit(); Write-Output 'OK' } catch { Write-Output 'FAIL' }",
            ]
            result = subprocess.run(
                check_ppt_cmd, check=False, capture_output=True, text=True, timeout=10
            )

            if "FAIL" in result.stdout or result.returncode != 0:
                raise OSError(
                    "Microsoft PowerPoint not found or COM registration broken. "
                    "Please install Microsoft Office with PowerPoint."
                )

        except subprocess.TimeoutExpired:
            raise OSError(
                "PowerPoint COM check timed out. PowerPoint may not be functioning."
            )

    def export_slide(self, pptx_path: str, slide_number: int, output_path: str) -> bool:
        """
        Export a single slide to JPG image.

        Args:
            pptx_path: Path to PowerPoint file (absolute path recommended)
            slide_number: Slide number to export (1-indexed, as in PowerPoint)
            output_path: Output JPG file path (will be created/overwritten)

        Returns:
            True if export succeeded, False otherwise

        Notes:
            - Slide numbering is 1-based (slide 1, 2, 3...)
            - Output directory must exist
            - Existing files at output_path will be overwritten
            - Function blocks until export completes (or timeout)
        """
        # Create temp script file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8"
        ) as script_file:
            script_file.write(self.EXPORT_SCRIPT_TEMPLATE)
            script_path = script_file.name

        try:
            # Resolve absolute paths
            pptx_abs = str(Path(pptx_path).resolve())
            output_abs = str(Path(output_path).resolve())

            # Ensure output directory exists
            Path(output_abs).parent.mkdir(parents=True, exist_ok=True)

            # Build PowerShell command
            cmd = [
                "powershell",
                "-ExecutionPolicy",
                "Bypass",  # Allow script execution
                "-File",
                script_path,
                "-PresentationPath",
                pptx_abs,
                "-SlideNumber",
                str(slide_number),
                "-OutputPath",
                output_abs,
                "-Resolution",
                str(self.resolution),
            ]

            # Execute with timeout (60 seconds per slide)
            result = subprocess.run(
                cmd, check=False, capture_output=True, text=True, timeout=60
            )

            # Check result
            if result.returncode == 0:
                # Verify output file exists
                if Path(output_abs).exists():
                    return True
                else:
                    print(
                        f"[ERROR] Export reported success but file not found: {output_abs}"
                    )
                    return False
            else:
                print(
                    f"[ERROR] PowerShell export failed (exit code {result.returncode})"
                )
                if result.stderr:
                    print(f"[ERROR] {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print(f"[ERROR] Export timeout for slide {slide_number} (>60 seconds)")
            return False

        except Exception as e:
            print(f"[ERROR] Unexpected export error: {e}")
            return False

        finally:
            # Cleanup temp script
            with contextlib.suppress(OSError):
                os.unlink(script_path)

    def export_all_slides(
        self,
        pptx_path: str,
        output_dir: str,
        callback: Callable[[int, bool, str], None] | None = None,
    ) -> dict[int, str]:
        """
        Export all slides from a presentation.

        Args:
            pptx_path: Path to PowerPoint file
            output_dir: Directory for output images
            callback: Optional callback(slide_num, success, output_path) for progress

        Returns:
            Dict mapping slide numbers to exported image paths (only successful exports)

        Notes:
            - Output files named: slide-1.jpg, slide-2.jpg, etc.
            - Continues on errors (best-effort export)
            - Returns only successfully exported slides
        """
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)

        # Get slide count
        slide_count = self._get_slide_count(pptx_path)
        if slide_count == 0:
            print(f"[ERROR] Could not determine slide count for: {pptx_path}")
            return {}

        exported_slides = {}

        for slide_num in range(1, slide_count + 1):
            output_path = output_dir_path / f"slide-{slide_num}.jpg"

            print(f"\n[EXPORT] Slide {slide_num}/{slide_count}: {output_path.name}")

            success = self.export_slide(
                pptx_path=pptx_path,
                slide_number=slide_num,
                output_path=str(output_path),
            )

            if success:
                exported_slides[slide_num] = str(output_path)
                print(f"[OK] Slide {slide_num} exported")
            else:
                print(f"[FAIL] Slide {slide_num} export failed")

            # Call progress callback if provided
            if callback:
                callback(slide_num, success, str(output_path))

        print(f"\n[SUMMARY] Exported {len(exported_slides)}/{slide_count} slides")
        return exported_slides

    def _get_slide_count(self, pptx_path: str) -> int:
        """
        Get the number of slides in a presentation.

        Args:
            pptx_path: Path to PowerPoint file

        Returns:
            Number of slides, or 0 if error
        """
        try:
            # Use python-pptx to quickly get slide count (faster than COM)
            from pptx import Presentation

            prs = Presentation(pptx_path)
            return len(prs.slides)
        except Exception as e:
            print(f"[WARN] Could not get slide count: {e}")
            return 0


# Test function for development
def main():
    """Test the exporter on a sample presentation."""
    import argparse

    parser = argparse.ArgumentParser(description="Test PowerPoint slide export")
    parser.add_argument("pptx_file", help="Path to PowerPoint file")
    parser.add_argument(
        "--output-dir",
        default="./exported-slides",
        help="Output directory (default: ./exported-slides)",
    )
    parser.add_argument(
        "--dpi", type=int, default=150, help="Export resolution DPI (default: 150)"
    )
    parser.add_argument(
        "--slide", type=int, help="Export single slide number (default: all slides)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print("PowerPoint Slide Exporter Test")
    print("=" * 80)

    # Initialize exporter
    try:
        exporter = SlideExporter(resolution=args.dpi)
        print(f"\n[OK] Exporter initialized (DPI: {args.dpi})")
    except OSError as e:
        print(f"\n[ERROR] Environment check failed: {e}")
        return 1

    # Export slide(s)
    if args.slide:
        # Single slide export
        output_path = Path(args.output_dir) / f"slide-{args.slide}.jpg"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n[EXPORT] Exporting slide {args.slide}...")
        success = exporter.export_slide(
            pptx_path=args.pptx_file,
            slide_number=args.slide,
            output_path=str(output_path),
        )

        if success:
            print(f"\n[SUCCESS] Exported to: {output_path}")
            return 0
        else:
            print("\n[FAILED] Export failed")
            return 1
    else:
        # All slides export
        print(f"\n[EXPORT] Exporting all slides to: {args.output_dir}")
        exported = exporter.export_all_slides(
            pptx_path=args.pptx_file, output_dir=args.output_dir
        )

        if exported:
            print(f"\n[SUCCESS] Exported {len(exported)} slides")
            return 0
        else:
            print("\n[FAILED] No slides exported")
            return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
