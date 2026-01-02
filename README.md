# PowerPoint Slide Generator

A comprehensive toolkit for generating professional PowerPoint presentations from markdown definitions, featuring AI-powered image generation and brand-specific templates.

## Overview

This project provides a complete workflow for creating branded presentations:

1. **Define** your presentation content in structured markdown format
2. **Generate** slide images using Google Gemini Pro API
3. **Build** PowerPoint files programmatically with python-pptx

Perfect for creating consistent, professional presentations at scale with full control over branding, layout, and content.

## Features

- 📝 **Structured Content Definition** - Comprehensive markdown template for slides including speaker notes, background research, and implementation guidance
- 🎨 **AI Image Generation** - Batch generate slide images using Google Gemini Pro with style consistency
- 🎯 **Brand Templates** - Pre-built PowerPoint builders for consistent branded presentations
- 🔧 **Programmatic Control** - Full python-pptx integration for precise layout and styling
- 📊 **Multiple Slide Types** - Title slides, section breaks, content slides, image slides, and combination layouts

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install google-genai pillow python-pptx lxml

# Set your Google API key
export GOOGLE_API_KEY="your-api-key-here"
```

### Basic Usage

**1. Define your presentation content:**

Create a markdown file following the template in `pres-template.md`:

```markdown
## Slide 1: TITLE SLIDE

**Title**: My Awesome Presentation

**Content**:
- Professional presentation content
- With structured format

**Graphic**: Modern tech illustration with gradient background...
```

**2. Generate slide images:**

```bash
python generate_images_for_slides.py \
  --style brand_style.json \
  --slides presentation.md \
  --output ./images
```

**3. Build PowerPoint presentation:**

```python
from cfa import CFAPresentation  # Or your custom brand template

prs = CFAPresentation()
prs.add_title_slide("My Presentation", "Subtitle", "January 2026")
prs.add_content_slide("Key Points", "Overview", [
    ("First major point", 0),
    ("Supporting detail", 1),
    ("Another key point", 0),
])
prs.save("output.pptx")
```

## Image Generation Script

The `generate_images_for_slides.py` script batch-generates presentation images using Google Gemini Pro.

### Command Line Options

| Flag | Description |
|------|-------------|
| `--style` | Path to JSON style definition (required) |
| `--slides` | Path to markdown slides file (required) |
| `--output` | Output directory for images (default: current dir) |
| `--fast` | Use standard resolution instead of 4K (faster/cheaper) |
| `--dry-run` | Parse slides without calling API |
| `--force` | Overwrite existing image files |
| `--notext` | Generate clean backgrounds without text overlays |

### Example Style Definition

Create a `style.json` file:

```json
{
  "brand_colors": ["#DD0033", "#004F71", "#FFFFFF"],
  "style": "professional, modern, clean",
  "tone": "corporate and approachable",
  "visual_elements": "geometric shapes, minimal text, bold colors",
  "typography": "sans-serif, modern fonts",
  "imagery": "abstract illustrations, no photographs"
}
```

### Complete Generation Example

```bash
# Development mode (fast, standard resolution)
python generate_images_for_slides.py \
  --style brand_style.json \
  --slides presentation.md \
  --output ./slide-images \
  --fast \
  --notext

# Production mode (4K, high quality)
python generate_images_for_slides.py \
  --style brand_style.json \
  --slides presentation.md \
  --output ./slide-images \
  --force
```

## Brand Templates

Two example brand templates are included:

### CFA Template (`cfa-ppt-v1.0.zip`)

Chick-fil-A branded presentations with:
- Red title slides with white compass logo
- Dark blue section breaks
- Apercu font family
- Custom bullet formatting (Wingdings §)
- 5 slide layout types

```python
from cfa import CFAPresentation

prs = CFAPresentation()
prs.add_title_slide("Title", "Subtitle", "Date")
prs.add_section_break("Section Name")
prs.add_content_slide("Title", "Subtitle", [("Bullet", 0)])
prs.add_image_slide("Title", "path/to/image.jpg")
prs.add_text_and_image_slide("Title", [("Bullet", 0)], "image.jpg")
prs.save("output.pptx")
```

### Stratfield Template (`stratfield-ppt-v1.0.zip`)

Custom branded template with professional styling and multiple layout options.

## Presentation Template Format

The `pres-template.md` file provides a comprehensive structure for defining presentation slides:

### Slide Components

Each slide definition includes:

- **Slide Header** - Type classification (TITLE, PROBLEM STATEMENT, INSIGHT, etc.)
- **Content** - Visible slide content with bullets, tables, code blocks
- **Graphic/Visual** - Detailed description for AI image generation
- **Speaker Notes** - Full narration with stage directions and transitions
- **Background** - Research citations, rationale, Q&A preparation
- **Sources** - Full citations with hyperlinks
- **Implementation Guidance** - Actionable next steps for the audience

### Slide Types Supported

- Title Slide
- Problem Statement
- Insight/Revelation
- Concept Introduction
- Framework/Model
- Comparison
- Deep Dive
- Case Study
- Pattern/Best Practice
- Metrics/Data
- Architecture/Diagram
- Objection Handling
- Action/Next Steps
- Summary/Recap
- Section Divider
- Closing/Call to Action
- Q&A/Contact
- Appendix

## Project Structure

```
slide-generator/
├── README.md                      # This file
├── CLAUDE.md                      # Documentation for Claude Code
├── pres-template.md               # Comprehensive slide template
├── generate_images_for_slides.py  # Gemini API image generation
├── cfa-ppt-v1.0.zip              # CFA brand template package
├── stratfield-ppt-v1.0.zip       # Stratfield brand template package
└── .gitignore                     # Git ignore rules
```

### Brand Template Package Structure

```
brand-ppt/
├── SKILL.md           # Documentation and usage guide
├── brand.py           # Python-pptx presentation builder
└── assets/            # Brand assets (logos, icons, backgrounds)
    ├── logo.png
    └── ...
```

## Creating Custom Brand Templates

To create your own brand template:

1. **Extract an existing template** as a starting point:
```bash
unzip cfa-ppt-v1.0.zip -d my-brand-ppt
```

2. **Customize brand constants** in the Python file:
   - Colors (hex values)
   - Fonts (heading and body)
   - Slide dimensions
   - Layout specifications

3. **Replace assets** in the `assets/` folder:
   - Logos (PNG format)
   - Background images
   - Icons and decorative elements

4. **Update layout specs** for each slide type:
   - Positions (x, y coordinates in inches)
   - Sizes (width, height in inches)
   - Font sizes and colors
   - Alignment and spacing

5. **Test your template**:
```python
from my_brand import MyBrandPresentation

prs = MyBrandPresentation()
prs.add_title_slide("Test", "Subtitle", "Date")
prs.save("test.pptx")
```

6. **Package for distribution**:
```bash
zip -r my-brand-ppt-v1.0.zip my-brand-ppt/
```

## Advanced Features

### Multi-level Bullets

Support for 3 levels of bullet indentation:

```python
prs.add_content_slide("Title", "Subtitle", [
    ("Main point", 0),        # Level 0 - main bullet
    ("Sub-point", 1),         # Level 1 - indented
    ("Detail", 2),            # Level 2 - double indented
    ("Another main point", 0),
])
```

### Image Handling

Images are automatically aspect-fitted within slide bounds:

```python
# Full image slide
prs.add_image_slide("Chart Analysis", "path/to/chart.png", "Q4 Results")

# Split text and image
prs.add_text_and_image_slide(
    "Key Features",
    [("Feature 1", 0), ("Feature 2", 0)],
    "path/to/screenshot.png"
)
```

### Custom Slide Layouts

Extend the base template class to add custom layouts:

```python
def add_custom_slide(self, title: str, custom_content):
    self._slide_count += 1
    slide = self.prs.slides.add_slide(self._get_blank_layout())
    # Custom layout implementation
    return slide
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key for image generation | Yes (for image generation) |

## Dependencies

**Image Generation:**
- `google-genai` - Google Gemini API client
- `pillow` - Image processing

**PowerPoint Generation:**
- `python-pptx` - PowerPoint file creation
- `pillow` - Image handling
- `lxml` - XML manipulation for advanced formatting

Install all dependencies:
```bash
pip install google-genai pillow python-pptx lxml
```

## API Usage and Costs

The image generation uses **Google Gemini 3 Pro Image Preview** model:

- Standard resolution: ~$0.002 per image
- 4K resolution: ~$0.008 per image
- Generation time: 30-60 seconds per 4K image
- Max retries: 3 attempts with 5-second delays
- Timeout: 5 minutes (for 4K generation)

Use `--fast` flag during development to reduce costs.

## Tips and Best Practices

### For Content Definition

- Follow the `pres-template.md` structure for consistency
- Include detailed graphic descriptions for better AI generation
- Write speaker notes in natural speech patterns
- Add Q&A preparation for common questions

### For Image Generation

- Start with `--dry-run` to verify slide parsing
- Use `--fast` during development iterations
- Use `--notext` to generate clean backgrounds for text overlay
- Include brand colors and style keywords in style.json
- Review generated images before final 4K generation

### For PowerPoint Generation

- Test your brand template with sample content first
- Verify font availability on target systems
- Check image file paths before building
- Use consistent naming for slide image files (`slide-1.jpg`, `slide-2.jpg`, etc.)

## Troubleshooting

### Common Issues

**"GOOGLE_API_KEY environment variable not found"**
- Set your API key: `export GOOGLE_API_KEY="your-key"`
- Verify: `echo $GOOGLE_API_KEY` (Linux/Mac) or `echo %GOOGLE_API_KEY%` (Windows)

**"No slides found"**
- Ensure slide headers contain "Slide N" (e.g., `## Slide 1` or `## **SLIDE 1: TITLE**`)
- Check markdown formatting in your slides file

**"Image blocked by safety filters"**
- Review prompt content in slide definition
- Adjust style.json to avoid problematic keywords
- Try regenerating with different phrasing

**Font not found errors**
- Install required fonts on your system
- Or update brand template to use system-available fonts

## Contributing

Contributions are welcome! Areas for enhancement:

- Additional brand template packages
- New slide layout types
- Enhanced image generation prompts
- Export to other formats (Google Slides, Keynote)
- Web-based slide editor

## License

This project is provided as-is for creating professional presentations.

## Acknowledgments

- Built with [python-pptx](https://python-pptx.readthedocs.io/)
- Image generation powered by [Google Gemini Pro](https://ai.google.dev/)
- Slide template structure inspired by professional presentation best practices

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Made with Claude Code** 🤖
>>>>>>> 251e61e (Add comprehensive README.md documentation)
