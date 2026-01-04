# Presentation Generator CLI Usage Guide

## Overview

`generate_presentation.py` is the main interactive CLI entry point for generating PowerPoint presentations from markdown files.

## Installation

First, ensure you have the required dependencies:

```bash
pip install python-pptx pillow lxml google-genai
```

For image generation, set your Google API key:

```bash
export GOOGLE_API_KEY="your-key-here"
```

## Usage Modes

### Interactive Mode

Run without arguments for a guided interactive experience:

```bash
python generate_presentation.py
```

The interactive flow includes 7 steps:

1. **Enter markdown file path** - Validates the file exists
2. **Preview presentation** - Shows slide count and graphics summary
3. **Select brand template** - Choose from available templates (CFA, Stratfield, etc.)
4. **Optional style config** - Provide custom style.json or use defaults
5. **Output filename** - Specify output name (default: presentation.pptx)
6. **Confirmation** - Review settings before generation
7. **Execute** - Generate the presentation with progress updates

### Non-Interactive Mode

Provide arguments for automated/scripted usage:

```bash
python generate_presentation.py presentation.md --template cfa --output output.pptx
```

## Command-Line Arguments

```
positional arguments:
  markdown              Path to markdown presentation file

options:
  -h, --help            Show help message and exit

  -t, --template TEMPLATE
                        Template ID (default: cfa)
                        Available: cfa, stratfield

  -o, --output OUTPUT   Output filename (default: presentation.pptx)

  -s, --style STYLE     Path to style.json for image generation

  --skip-images         Skip image generation entirely

  --fast                Use fast/low-resolution image generation
                        (Standard resolution instead of 4K)

  --force               Regenerate existing images

  --preview             Preview presentation without generating
                        Shows slide count and types

  --non-interactive     Disable interactive prompts
                        (requires markdown argument)
```

## Examples

### Example 1: Interactive Mode

```bash
$ python generate_presentation.py

============================================================
  📊 PowerPoint Presentation Generator
============================================================

📄 Enter path to presentation markdown file:
   > my-presentation.md

🔍 Analyzing presentation...
   ✅ Found 15 slides
   🎨 5 slides have graphics requiring image generation

   Slides with graphics:
      • Slide 3: Architecture Overview
      • Slide 5: Data Flow Diagram
      • Slide 8: Performance Metrics
      • Slide 11: Implementation Timeline
      • Slide 13: Cost Comparison

🎨 Select brand template:
   1. Chick-fil-A - Professional CFA branding
   2. Stratfield Consulting - Modern consulting theme

Enter number [1]: 1
   ✅ Selected: Chick-fil-A

📝 Path to style.json (or press Enter for default):
   >
   ℹ️  Using default style configuration

💾 Output filename [presentation.pptx]:
   > demo.pptx
   ✅ Output will be saved as: demo.pptx

============================================================
  Ready to generate presentation
============================================================

  📄 Input:    my-presentation.md (15 slides)
  🎨 Template: Chick-fil-A
  🖼️  Images:   5 slides will be generated
  💾 Output:   demo.pptx

Continue? [Y/n]: y

============================================================
  🚀 Generating presentation...
============================================================

📄 Parsing: my-presentation.md
   Found 15 slides

🎨 Generating images for 5 slides...
   ✓ Slide 3: slide-3.jpg
   ✓ Slide 5: slide-5.jpg
   ✓ Slide 8: slide-8.jpg
   ✓ Slide 11: slide-11.jpg
   ✓ Slide 13: slide-13.jpg

📊 Building presentation with 'cfa' template...
   + Slide 1: TITLE SLIDE - Innovation in Cloud Computing...
   + Slide 2: SECTION BREAK - Introduction...
   [...]

✅ Saved: /path/to/demo.pptx
📁 Images: /path/to/images

============================================================
  ✅ Generation complete!
============================================================

  📦 Output: /path/to/demo.pptx
```

### Example 2: Non-Interactive with All Options

```bash
python generate_presentation.py presentation.md \
  --template stratfield \
  --style brand_style.json \
  --output quarterly-review.pptx \
  --fast
```

### Example 3: Preview Only

```bash
python generate_presentation.py presentation.md --preview
```

Output:
```
📋 Presentation Preview: presentation.md
   Total slides: 15

   Slides with graphics: 5
      - Slide 3: Architecture Overview
      - Slide 5: Data Flow Diagram
      - Slide 8: Performance Metrics
      - Slide 11: Implementation Timeline
      - Slide 13: Cost Comparison

   Slide breakdown:
         1. [TITLE SLIDE        ] Innovation in Cloud Computing                (0 bullets)
         2. [SECTION BREAK      ] Introduction                                 (0 bullets)
      🎨  3. [ARCHITECTURE       ] System Architecture                          (3 bullets)
         4. [CONTENT            ] Key Benefits                                 (4 bullets)
      🎨  5. [DIAGRAM            ] Data Flow                                    (2 bullets)
      [...]
```

### Example 4: Skip Image Generation

Useful when images already exist or when testing layout:

```bash
python generate_presentation.py presentation.md \
  --template cfa \
  --skip-images
```

### Example 5: Regenerate Existing Images

Force regeneration even if images exist:

```bash
python generate_presentation.py presentation.md \
  --template cfa \
  --force
```

## Error Handling

The CLI handles common errors gracefully:

### File Not Found
```
📄 Enter path to presentation markdown file:
   > nonexistent.md
   ❌ File not found: /path/to/nonexistent.md
   Please check the path and try again.
```

### Invalid Template
```
Error: Unknown template 'invalid'
Available templates:
  • cfa: Chick-fil-A - Professional CFA branding
  • stratfield: Stratfield Consulting - Modern consulting theme
```

### Missing API Key Warning
```
⚠️  Warning: GOOGLE_API_KEY not set - image generation will be skipped
```

### Keyboard Interrupt
Clean exit on Ctrl+C:
```
^C
❌ Cancelled by user
```

## Tips

1. **Use --preview first** to verify slide structure before generation
2. **Use --fast during development** to speed up image generation
3. **Use --skip-images** when iterating on slide layout only
4. **Check for API key** if images aren't generating
5. **Use full paths** if running from different directories

## Integration

The CLI can be integrated into automated workflows:

```bash
#!/bin/bash
# Batch generate presentations

for md_file in presentations/*.md; do
  output="${md_file%.md}.pptx"
  python generate_presentation.py "$md_file" \
    --template cfa \
    --output "$output" \
    --non-interactive
done
```

## Troubleshooting

### Dependencies Missing
```bash
pip install python-pptx pillow lxml google-genai
```

### Import Errors
Ensure you're running from the correct directory or use full paths:
```bash
cd /path/to/presentation-skill
python generate_presentation.py
```

### Image Generation Failing
1. Check API key is set: `echo $GOOGLE_API_KEY`
2. Verify network connectivity
3. Try --fast mode for testing
4. Use --skip-images as fallback
