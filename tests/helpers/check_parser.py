#!/usr/bin/env python3
"""
Check what the parser is actually extracting from the markdown.
"""

from plugin.lib.presentation.parser import parse_presentation


# Parse the test file
slides = parse_presentation("testfiles/presentation.md")

print(f"Parsed {len(slides)} slides\n")

# Inspect first 5 slides in detail
for slide in slides[:5]:
    print(f"{'=' * 80}")
    print(f"SLIDE {slide.number}: {slide.slide_type}")
    print(f"{'=' * 80}")
    print(f"Title: '{slide.title}'")
    print(f"Subtitle: '{slide.subtitle}'")
    print(f"Content items: {len(slide.content)}")

    if slide.content:
        print("Content:")
        for text, indent in slide.content[:10]:
            print(f"  [Level {indent}] {text[:80]}")
    else:
        print("  (NO CONTENT)")

    if slide.graphic:
        print(f"Graphic: {slide.graphic[:100]}...")
    else:
        print("Graphic: (none)")

    print("\nRaw content preview (first 500 chars):")
    print(slide.raw_content[:500])
    print("\n")
