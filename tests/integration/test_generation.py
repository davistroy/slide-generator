#!/usr/bin/env python3
"""Direct test script for presentation generation."""

from plugin.lib.presentation import assemble_presentation


def main():
    print("Generating CFA presentation...")

    cfa_output = assemble_presentation(
        markdown_path="tests/testfiles/presentation.md",
        template_id="cfa",
        output_name="tests/artifacts/comprehensive-test-cfa.pptx",
        skip_images=False,
        fast_mode=False,
        force_images=False,
    )

    print(f"CFA presentation saved to: {cfa_output}")

    print("\nGenerating Stratfield presentation...")

    stratfield_output = assemble_presentation(
        markdown_path="tests/testfiles/presentation.md",
        template_id="stratfield",
        output_name="tests/artifacts/comprehensive-test-stratfield.pptx",
        skip_images=False,
        fast_mode=False,
        force_images=False,
    )

    print(f"Stratfield presentation saved to: {stratfield_output}")
    print("\nBoth presentations generated successfully!")


if __name__ == "__main__":
    main()
