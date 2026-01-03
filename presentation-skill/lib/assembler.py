"""
Presentation Assembler

Orchestrates the full workflow:
1. Parse markdown presentation file
2. Classify slide types intelligently (rule-based + AI)
3. Generate images for slides with graphics
4. Build PowerPoint using selected brand template
5. Save final output

Usage:
    from lib.assembler import assemble_presentation

    output_path = assemble_presentation(
        markdown_path="presentation.md",
        template_id="cfa",
        output_name="my_presentation.pptx"
    )
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Callable, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import (
    parse_presentation,
    get_slides_needing_images,
    map_slide_type_to_method,
    Slide
)
from lib.image_generator import (
    generate_all_images,
    generate_slide_image,
    load_style_config,
    DEFAULT_STYLE
)
from lib.type_classifier import SlideTypeClassifier, TypeClassification
from lib.slide_exporter import SlideExporter
from lib.visual_validator import VisualValidator
from lib.refinement_engine import RefinementEngine
from templates import get_template, list_templates


def assemble_presentation(
    markdown_path: str,
    template_id: str,
    style_config_path: Optional[str] = None,
    output_name: Optional[str] = None,
    output_dir: Optional[str] = None,
    skip_images: bool = False,
    fast_mode: bool = False,
    notext: bool = True,
    force_images: bool = False,
    enable_validation: bool = False,
    max_refinement_attempts: int = 3,
    validation_dpi: int = 150,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> str:
    """
    Main workflow to assemble a presentation from markdown.

    Args:
        markdown_path: Path to the presentation markdown file
        template_id: Brand template to use (e.g., 'cfa', 'stratfield')
        style_config_path: Optional path to style.json for image generation
        output_name: Output filename (default: presentation.pptx)
        output_dir: Output directory (default: current directory)
        skip_images: If True, skip image generation entirely
        fast_mode: If True, use standard resolution instead of 4K
        notext: If True, generate clean backgrounds without text
        force_images: If True, regenerate existing images
        enable_validation: If True, validate slides and refine if needed (EXPERIMENTAL)
        max_refinement_attempts: Maximum refinement attempts per slide (default: 3)
        validation_dpi: DPI for slide export during validation (default: 150)
        progress_callback: Optional callback(stage, current, total) for progress

    Returns:
        Path to the generated PowerPoint file

    Raises:
        FileNotFoundError: If markdown file doesn't exist
        ValueError: If template_id is invalid
    """
    # Resolve paths
    markdown_path = Path(markdown_path).resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    output_dir = Path(output_dir) if output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    output_name = output_name or "presentation.pptx"
    if not output_name.endswith(".pptx"):
        output_name += ".pptx"
    output_path = output_dir / output_name

    images_dir = output_dir / "images"

    # Load style config
    if style_config_path:
        style_config = load_style_config(style_config_path)
    else:
        style_config = DEFAULT_STYLE

    # Step 1: Parse markdown
    _notify(progress_callback, "Parsing markdown", 1, 5)
    print(f"\n[*] Parsing: {markdown_path.name}")

    slides = parse_presentation(str(markdown_path))
    print(f"   Found {len(slides)} slides")

    if not slides:
        raise ValueError("No slides found in markdown file")

    # Step 2: Classify slide types
    _notify(progress_callback, "Classifying slide types", 2, 5)
    print(f"\n[*] Classifying slide types (rule-based + AI)...")

    classifier = SlideTypeClassifier()
    classifications: Dict[int, TypeClassification] = {}

    for slide in slides:
        classification = classifier.classify_slide(slide)
        classifications[slide.number] = classification

        # Log classification results
        confidence_pct = int(classification.confidence * 100)
        print(f"   Slide {slide.number:2d}: {classification.slide_type:12s} ({confidence_pct:3d}%) - {classification.reasoning[:60]}")

    # Step 3: Generate images (if needed)
    _notify(progress_callback, "Generating images", 3, 5)
    image_paths: Dict[int, Path] = {}

    if not skip_images:
        slides_needing_images = get_slides_needing_images(slides)
        if slides_needing_images:
            print(f"\n[*] Generating images for {len(slides_needing_images)} slides...")
            images_dir.mkdir(parents=True, exist_ok=True)

            def image_progress(slide_num: int, success: bool, path: Optional[Path]):
                status = "[OK]" if success else "[FAIL]"
                print(f"   {status} Slide {slide_num}: {path.name if path else 'skipped/failed'}")

            image_paths = generate_all_images(
                slides=slides,
                style_config=style_config,
                output_dir=images_dir,
                fast_mode=fast_mode,
                notext=notext,
                force=force_images,
                callback=image_progress
            )
        else:
            print("\n[*] No slides have **Graphic** sections - skipping image generation")
    else:
        print("\n[*] Image generation skipped (--skip-images)")

    # Step 4: Build presentation (with optional validation loop)
    _notify(progress_callback, "Building presentation", 4, 5)
    print(f"\n[*] Building presentation with '{template_id}' template...")

    template = get_template(template_id)

    # Initialize validation components if enabled
    validator = None
    refiner = None
    exporter = None
    validation_dir = None

    if enable_validation:
        try:
            validator = VisualValidator()
            refiner = RefinementEngine()
            exporter = SlideExporter(resolution=validation_dpi)
            validation_dir = output_dir / "validation"
            validation_dir.mkdir(parents=True, exist_ok=True)
            print(f"[*] Validation enabled (max {max_refinement_attempts} refinements per slide)")
        except Exception as e:
            print(f"[WARN] Validation initialization failed: {e}")
            print(f"[WARN] Continuing without validation")
            enable_validation = False

    # Build slides with optional validation loop
    for slide in slides:
        classification = classifications[slide.number]

        if enable_validation and slide.graphic:
            # Validation loop for slides with graphics
            _build_slide_with_validation(
                template=template,
                slide=slide,
                classification=classification,
                image_paths=image_paths,
                images_dir=images_dir,
                validator=validator,
                refiner=refiner,
                exporter=exporter,
                validation_dir=validation_dir,
                style_config=style_config,
                output_path=output_path,
                max_attempts=max_refinement_attempts,
                fast_mode=fast_mode,
                notext=notext
            )
        else:
            # Standard build without validation
            _add_slide_to_presentation(template, slide, classification, image_paths, images_dir)
            print(f"   + Slide {slide.number}: {classification.slide_type:12s} - {slide.title[:40]}...")

    # Step 5: Save
    _notify(progress_callback, "Saving", 5, 5)
    template.save(str(output_path))
    print(f"\n[SUCCESS] Saved: {output_path}")

    # Report image directory if images were generated
    if image_paths:
        print(f"[INFO] Images: {images_dir}")

    return str(output_path)


def _add_slide_to_presentation(
    template,
    slide: Slide,
    classification: TypeClassification,
    image_paths: Dict[int, Path],
    images_dir: Path
) -> None:
    """
    Add a single slide to the presentation using the appropriate template method.

    Args:
        template: The presentation template instance
        slide: The Slide object to add
        classification: TypeClassification determining which template method to use
        image_paths: Dict mapping slide numbers to generated image paths
        images_dir: Directory where images are stored
    """
    method_name = classification.template_method

    # Get image path if available
    image_path = None
    if slide.number in image_paths:
        image_path = str(image_paths[slide.number])
    elif slide.graphic:
        # Check if image file exists from previous run
        potential_path = images_dir / f"slide-{slide.number}.jpg"
        if potential_path.exists():
            image_path = str(potential_path)

    # Call appropriate template method based on slide type
    if method_name == "add_title_slide":
        # Title slide: title, subtitle, date
        # Use subtitle from slide, or first content item as subtitle
        subtitle = slide.subtitle or ""
        date = ""
        # Try to extract date from content if present
        for text, _ in slide.content_bullets:
            if any(month in text.lower() for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', '2024', '2025', '2026']):
                date = text
                break
        template.add_title_slide(slide.title, subtitle, date)

    elif method_name == "add_section_break":
        # Section break: just title
        template.add_section_break(slide.title)

    elif method_name == "add_image_slide":
        # Image slide: title, image_path, subtitle
        if image_path:
            template.add_image_slide(slide.title, image_path, slide.subtitle or "")
        else:
            # Fallback to content slide if no image
            template.add_content_slide(slide.title, slide.subtitle or "", slide.content_bullets)

    elif method_name == "add_text_and_image_slide":
        # Text and image: title, bullets, image_path
        if image_path:
            template.add_text_and_image_slide(slide.title, slide.content_bullets, image_path)
        else:
            # Fallback to content slide if no image
            template.add_content_slide(slide.title, slide.subtitle or "", slide.content_bullets)

    else:
        # Default: content slide with bullets
        template.add_content_slide(slide.title, slide.subtitle or "", slide.content_bullets)


def _build_slide_with_validation(
    template,
    slide: Slide,
    classification: TypeClassification,
    image_paths: Dict[int, Path],
    images_dir: Path,
    validator,
    refiner,
    exporter,
    validation_dir: Path,
    style_config: dict,
    output_path: Path,
    max_attempts: int,
    fast_mode: bool,
    notext: bool
) -> None:
    """
    Build slide with validation and refinement loop.

    Workflow per slide:
    1. Build slide in presentation
    2. Save temporary presentation
    3. Export slide to image
    4. Validate slide image
    5. If validation fails and attempts remain:
       - Generate refinement strategy
       - Regenerate image with refined prompt
       - Remove last slide from presentation
       - Loop back to step 1

    Args:
        template: Presentation template instance
        slide: Slide object
        classification: TypeClassification for this slide
        image_paths: Dict of existing image paths
        images_dir: Directory for images
        validator: VisualValidator instance
        refiner: RefinementEngine instance
        exporter: SlideExporter instance
        validation_dir: Directory for validation artifacts
        style_config: Style configuration dict
        output_path: Temporary output path for presentation
        max_attempts: Maximum refinement attempts
        fast_mode: Whether to use fast mode for images
        notext: Whether to generate text-free images
    """
    attempt = 0
    previous_score = None
    temp_pptx = output_path.parent / "_temp_validation.pptx"

    while attempt < max_attempts:
        attempt += 1

        # Build slide
        _add_slide_to_presentation(template, slide, classification, image_paths, images_dir)

        # Save temporary presentation for export
        template.save(str(temp_pptx))

        # Export slide to image
        slide_image_path = validation_dir / f"slide-{slide.number}-attempt-{attempt}.jpg"

        # Calculate slide index (1-based)
        slide_index = len(template.prs.slides)

        export_success = exporter.export_slide(
            pptx_path=str(temp_pptx),
            slide_number=slide_index,
            output_path=str(slide_image_path)
        )

        if not export_success:
            print(f"   [WARN] Slide {slide.number} export failed - accepting without validation")
            break

        # Validate slide
        try:
            result = validator.validate_slide(
                slide_image_path=str(slide_image_path),
                original_slide=slide,
                style_config=style_config,
                slide_type=classification.slide_type
            )

            score_pct = int(result.score * 100)
            status = "PASS" if result.passed else "FAIL"

            print(f"   + Slide {slide.number}: {classification.slide_type:12s} - Attempt {attempt} [{status} {score_pct}%] - {slide.title[:40]}...")

            # Check if we should accept this result
            if result.passed:
                # Passed validation
                if result.score >= refiner.DIMINISHING_RETURNS_THRESHOLD:
                    # Excellent score - accept
                    break

                # Good but could improve - check if we should refine
                if not refiner.should_retry(result, attempt, max_attempts, previous_score):
                    # Accept - minimal improvement expected
                    break

            # Check if we should retry
            if not refiner.should_retry(result, attempt, max_attempts, previous_score):
                # Max attempts or minimal improvement - accept current
                print(f"      [ACCEPT] Max attempts reached or minimal improvement")
                break

            # Generate refinement strategy
            refinement = refiner.generate_refinement(slide, result, attempt, previous_score)

            print(f"      [REFINE] Attempt {attempt + 1}: {refinement.reasoning[:60]}...")

            # Regenerate image with refined prompt
            new_image_path = generate_slide_image(
                slide=slide,
                style_config=style_config,
                output_dir=images_dir,
                fast_mode=refinement.parameter_adjustments.get('fast_mode', fast_mode),
                notext=refinement.parameter_adjustments.get('notext', notext),
                force=True,  # Force regeneration
                prompt_override=refinement.modified_prompt
            )

            if new_image_path:
                # Update image paths with refined image
                image_paths[slide.number] = new_image_path

            # Remove last slide to rebuild with new image
            _remove_last_slide(template)

            # Track score for improvement calculation
            previous_score = result.score

        except Exception as e:
            print(f"   [ERROR] Validation failed for slide {slide.number}: {e}")
            print(f"   [ACCEPT] Accepting slide without validation")
            break

    # Cleanup temp file
    if temp_pptx.exists():
        try:
            temp_pptx.unlink()
        except:
            pass


def _remove_last_slide(template) -> None:
    """
    Remove the last slide from a python-pptx presentation.

    This is needed for the refinement loop - when validation fails,
    we remove the slide and rebuild it with a refined image.

    Args:
        template: Template instance with prs (Presentation) attribute
    """
    try:
        # Get the presentation object
        prs = template.prs

        # Get slides collection
        slides = prs.slides

        # Get last slide index
        last_slide_idx = len(slides) - 1

        if last_slide_idx >= 0:
            # Access the underlying XML to remove the slide
            rId = slides._sldIdLst[last_slide_idx].rId
            prs.part.drop_rel(rId)
            del slides._sldIdLst[last_slide_idx]

    except Exception as e:
        print(f"[WARN] Failed to remove last slide: {e}")


def _notify(
    callback: Optional[Callable[[str, int, int], None]],
    stage: str,
    current: int,
    total: int
) -> None:
    """Call progress callback if provided."""
    if callback:
        callback(stage, current, total)


def preview_presentation(markdown_path: str) -> None:
    """
    Parse and display a summary of the presentation without generating anything.

    Args:
        markdown_path: Path to the presentation markdown file
    """
    slides = parse_presentation(markdown_path)

    print(f"\n[PREVIEW] Presentation: {Path(markdown_path).name}")
    print(f"   Total slides: {len(slides)}")
    print()

    slides_with_graphics = get_slides_needing_images(slides)
    print(f"   Slides with graphics: {len(slides_with_graphics)}")
    if slides_with_graphics:
        for slide in slides_with_graphics:
            print(f"      - Slide {slide.number}: {slide.title[:50]}")
    print()

    print("   Slide breakdown:")
    for slide in slides:
        has_graphic = "🎨" if slide.graphic else "  "
        bullet_count = len(slide.content)
        print(f"      {has_graphic} {slide.number:2d}. [{slide.slide_type:20s}] {slide.title[:40]:<40s} ({bullet_count} bullets)")


def get_available_templates() -> List[Tuple[str, str, str]]:
    """
    Get list of available templates.

    Returns:
        List of (id, name, description) tuples
    """
    return list_templates()


# CLI-friendly wrapper
def main():
    """Simple command-line interface for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Assemble presentation from markdown")
    parser.add_argument("markdown", help="Path to markdown presentation file")
    parser.add_argument("--template", "-t", default="cfa", help="Template ID (default: cfa)")
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument("--style", "-s", help="Path to style.json")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation")
    parser.add_argument("--fast", action="store_true", help="Use fast/low-res image generation")
    parser.add_argument("--force", action="store_true", help="Regenerate existing images")
    parser.add_argument("--preview", action="store_true", help="Preview only, don't generate")

    args = parser.parse_args()

    if args.preview:
        preview_presentation(args.markdown)
        return

    assemble_presentation(
        markdown_path=args.markdown,
        template_id=args.template,
        style_config_path=args.style,
        output_name=args.output,
        skip_images=args.skip_images,
        fast_mode=args.fast,
        force_images=args.force
    )


if __name__ == "__main__":
    main()
