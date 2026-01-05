#!/usr/bin/env python3
"""Test script for generating presentations with brand-specific images."""

import shutil
from pathlib import Path

from plugin.lib.presentation import assemble_presentation


def main():
    base_dir = Path(__file__).parent
    artifacts_dir = base_dir / "artifacts"

    # Generate CFA presentation with CFA-branded images
    print("\n" + "=" * 80)
    print("GENERATING CFA PRESENTATION WITH CFA-BRANDED IMAGES")
    print("=" * 80)

    # Copy CFA images to standard images directory
    cfa_images_src = artifacts_dir / "images-cfa"
    images_dir = artifacts_dir / "images"

    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True, exist_ok=True)

    # Copy all CFA images
    for img in cfa_images_src.glob("slide-*.jpg"):
        shutil.copy(img, images_dir / img.name)
        print(f"   Copied {img.name} from CFA images")

    cfa_output = assemble_presentation(
        markdown_path="tests/testfiles/presentation.md",
        template_id="cfa",
        output_name="branded-test-cfa.pptx",
        output_dir="tests/artifacts",
        skip_images=True,  # Use existing images
        fast_mode=False,
        force_images=False,
    )

    print(f"\n[SUCCESS] CFA presentation saved to: {cfa_output}")

    # Generate Stratfield presentation with Stratfield-branded images
    print("\n" + "=" * 80)
    print("GENERATING STRATFIELD PRESENTATION WITH STRATFIELD-BRANDED IMAGES")
    print("=" * 80)

    # Replace with Stratfield images
    stratfield_images_src = artifacts_dir / "images-stratfield"

    # Remove old images
    for img in images_dir.glob("slide-*.jpg"):
        img.unlink()

    # Copy all Stratfield images
    for img in stratfield_images_src.glob("slide-*.jpg"):
        shutil.copy(img, images_dir / img.name)
        print(f"   Copied {img.name} from Stratfield images")

    stratfield_output = assemble_presentation(
        markdown_path="tests/testfiles/presentation.md",
        template_id="stratfield",
        output_name="branded-test-stratfield.pptx",
        output_dir="tests/artifacts",
        skip_images=True,  # Use existing images
        fast_mode=False,
        force_images=False,
    )

    print(f"\n[SUCCESS] Stratfield presentation saved to: {stratfield_output}")

    print("\n" + "=" * 80)
    print("BOTH BRANDED PRESENTATIONS GENERATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"CFA (with CFA-branded images):        {cfa_output}")
    print(f"Stratfield (with Stratfield images):  {stratfield_output}")


if __name__ == "__main__":
    main()
