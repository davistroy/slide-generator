# PowerPoint Slide Generator

**Version:** 1.1.0 (Enhanced Release)
**Status:** Production Ready ✅
**Updated:** January 3, 2026

A comprehensive toolkit for generating professional PowerPoint presentations from markdown definitions, featuring AI-powered image generation and brand-specific templates.

## Overview

This project provides a complete workflow for creating branded presentations:

1. **Define** your presentation content in structured markdown format
2. **Generate** slide images using Google Gemini Pro API (optional)
3. **Build** PowerPoint files programmatically with python-pptx

Perfect for creating consistent, professional presentations at scale with full control over branding, layout, and content.

## ✨ What's New in v1.1.0

**Enhanced Parser (100% Functional):**
- ✅ Markdown table parsing
- ✅ Numbered list support (`1.`, `2.`, `3.`)
- ✅ Code block detection
- ✅ Plain text paragraphs
- ✅ Clean markdown (no `**` artifacts)
- ✅ Cross-platform (Windows, Mac, Linux)

**Major Improvements:**
- Complete parser rewrite with all content types
- Fixed Windows Unicode errors
- Enhanced content extraction
- Backward compatible with v1.0.0

[See full changelog →](docs/CHANGELOG.md)

## Features

- 📝 **Structured Content Definition** - Comprehensive markdown template for slides including speaker notes and research
- 🎨 **AI Image Generation** - Batch generate slide images using Google Gemini Pro with style consistency
- 🎯 **Brand Templates** - Pre-built PowerPoint builders for CFA and Stratfield branded presentations
- 🔧 **Programmatic Control** - Full python-pptx integration for precise layout and styling
- 📊 **Multiple Content Types** - Tables, bullets, numbered lists, code blocks, and mixed content
- 🌐 **Cross-Platform** - Works on Windows, macOS, and Linux

## Quick Start

### Installation

**Option 1: From Distribution Package (Recommended)**

```bash
# Download and extract
unzip dist/presentation-skill-v1.1.0.zip
cd presentation-skill

# Install dependencies
pip install python-pptx Pillow lxml google-genai

# Optional: Set Google API key for image generation
export GOOGLE_API_KEY="your-api-key-here"  # Linux/Mac
set GOOGLE_API_KEY=your-api-key-here       # Windows CMD
$env:GOOGLE_API_KEY="your-api-key-here"    # Windows PowerShell
```

**Option 2: Clone Repository**

```bash
git clone https://github.com/yourusername/slide-generator.git
cd slide-generator/presentation-skill
pip install python-pptx Pillow lxml google-genai
```

### Basic Usage

**Interactive Mode:**
```bash
python generate_presentation.py
```

**Command Line:**
```bash
# Generate with CFA template (without images)
python generate_presentation.py presentation.md --template cfa --skip-images

# Generate with Stratfield template (with images)
python generate_presentation.py presentation.md --template stratfield --output my-deck.pptx

# Preview slides without generating
python generate_presentation.py presentation.md --preview
```

### Create Your First Presentation

1. **Start with the template:**
   ```bash
   cp templates/pres-template.md my-presentation.md
   ```

2. **Edit the markdown:**
   ```markdown
   ### SLIDE 1: TITLE SLIDE

   **Title:** My Awesome Presentation

   **Subtitle:** Building Amazing Slides

   **Content:**
   - Professional presentation
   - Structured format
   - Easy to maintain

   **Graphic:** Modern tech illustration...
   ```

3. **Generate PowerPoint:**
   ```bash
   python presentation-skill/generate_presentation.py my-presentation.md \
     --template cfa --skip-images
   ```

## Supported Content Types

### ✅ Bullet Lists
```markdown
**Content:**
- First level item
  - Second level item
    - Third level item
```

### ✅ Numbered Lists (NEW in v1.1.0)
```markdown
**Content:**
1. First item
2. Second item
   - Sub-bullet
3. Third item
```

### ✅ Tables (NEW in v1.1.0)
```markdown
**Content:**

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |
```
*Note: Tables are currently rendered as formatted text. Native PowerPoint tables coming in v1.2.0.*

### ✅ Code Blocks (NEW in v1.1.0)
```markdown
**Content:**

```python
print("Hello, World!")
```
```

### ✅ Mixed Content
You can combine any content types on the same slide!

## Project Structure

```
slide-generator/
├── presentation-skill/     # SOURCE CODE (v1.1.0)
├── dist/                   # Distribution packages
├── docs/                   # Documentation
├── templates/              # Examples and templates
├── tests/                  # Test files and scripts
└── scripts/                # Utility scripts
```

[See detailed structure →](PROJECT_STRUCTURE.md)

## Available Templates

### CFA (Chick-fil-A Branded)
- Red (#DD0033) and blue (#004F71) color scheme
- Apercu font family
- Professional corporate styling
- File: `presentation-skill/templates/cfa.py`

### Stratfield (Consulting Branded)
- Green and teal color scheme
- Avenir font family
- Modern professional design
- File: `presentation-skill/templates/stratfield.py`

### Creating Custom Templates

See `docs/REGENERATE_SKILLS.md` for guidance on creating your own branded templates.

## Advanced Usage

### Image Generation

Generate images for slides with **Graphic** sections:

```bash
# With Google API key set
python presentation-skill/generate_presentation.py presentation.md \
  --template cfa --fast

# Without Google API key (skip images)
python presentation-skill/generate_presentation.py presentation.md \
  --template cfa --skip-images
```

### Batch Image Generation

Use the standalone image generator:

```bash
python scripts/generate_images_for_slides.py \
  --style brand_style.json \
  --slides presentation.md \
  --output ./images \
  --notext
```

### Preview Mode

Preview slide structure before generating:

```bash
python presentation-skill/generate_presentation.py presentation.md --preview
```

Output:
```
[PREVIEW] Presentation: presentation.md
   Total slides: 20

   Slides with graphics: 20
      - Slide 1: Block 1 Week 1: Markdown Fundamentals
      - Slide 2: This Week's Journey
      ...
```

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](docs/CHANGELOG.md) | Complete version history with technical details |
| [FIXES_SUMMARY.md](docs/FIXES_SUMMARY.md) | Quick reference for v1.1.0 fixes |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Project organization guide |
| [SKILL.md](presentation-skill/SKILL.md) | Skill documentation |
| [CLI_USAGE.md](presentation-skill/CLI_USAGE.md) | Command-line reference |

## Testing

Run the test suite:

```bash
# Test parser
python presentation-skill/lib/parser.py tests/testfiles/presentation.md

# Generate test presentations
python presentation-skill/generate_presentation.py tests/testfiles/presentation.md \
  --template cfa --output tests/artifacts/test.pptx --skip-images

# Inspect generated files
python tests/check_parser.py
python tests/inspect_presentations.py
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/slide-generator.git
cd slide-generator

# Install dependencies
pip install python-pptx Pillow lxml google-genai

# Run tests
python -m pytest tests/
```

### Making Changes

1. Edit source files in `presentation-skill/`
2. Test with `tests/testfiles/presentation.md`
3. Run validation scripts in `tests/`
4. Update documentation as needed
5. Rebuild distribution package

See [docs/REGENERATE_SKILLS.md](docs/REGENERATE_SKILLS.md) for detailed build instructions.

## API Reference

### Parser

```python
from presentation_skill.lib.parser import parse_presentation

slides = parse_presentation("presentation.md")
for slide in slides:
    print(f"Slide {slide.number}: {slide.title}")
    print(f"Content items: {len(slide.content)}")
```

### Assembler

```python
from presentation_skill.lib.assembler import assemble_presentation

output_path = assemble_presentation(
    markdown_path="presentation.md",
    template_id="cfa",
    output_name="my_deck.pptx",
    skip_images=True
)
```

## Dependencies

- **python-pptx** (1.0.2+) - PowerPoint file generation
- **Pillow** (12.0.0+) - Image processing
- **lxml** (6.0.2+) - XML processing
- **google-genai** (1.55.0+) - AI image generation (optional)

## Troubleshooting

### Common Issues

**Issue:** Unicode errors on Windows
**Solution:** This is fixed in v1.1.0. Upgrade from dist/presentation-skill-v1.1.0.zip

**Issue:** Slides have `**` markdown markers
**Solution:** This is fixed in v1.1.0. The parser now cleans all markdown formatting.

**Issue:** Tables not rendering
**Solution:** Tables are parsed and rendered as text bullets in v1.1.0. Native table support coming in v1.2.0.

**Issue:** No slides found
**Solution:** Ensure slide headers use `### SLIDE N:` format (v1.1.0 supports both `##` and `###`).

[See full troubleshooting guide →](docs/INSPECTION_REPORT.md)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

[Add your license here]

## Changelog

### v1.1.0 (2026-01-03) - Enhanced Release
- ✅ Complete parser rewrite
- ✅ Table parsing support
- ✅ Numbered lists
- ✅ Code blocks
- ✅ Clean markdown
- ✅ Windows compatibility
- ✅ 100% functional

### v1.0.0 - Initial Release
- Basic bullet point parsing
- CFA and Stratfield templates
- Image generation support

[See full changelog →](docs/CHANGELOG.md)

## Roadmap

### v1.2.0 (Planned)
- Native PowerPoint table rendering
- Code block syntax highlighting
- Additional slide layouts
- More templates

### v1.3.0 (Future)
- Interactive web UI
- Real-time preview
- Template builder
- Cloud storage integration

## Support

For questions, issues, or feature requests:
- **Issues:** [GitHub Issues](https://github.com/yourusername/slide-generator/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/slide-generator/discussions)
- **Email:** support@example.com

## Acknowledgments

- **Google Gemini Pro** - AI image generation
- **python-pptx** - PowerPoint file generation
- **AI Practitioner Training Program** - Original use case

---

**Built with ❤️ by the AI Practitioner Training Program**

**Status:** Production Ready ✅ | **Version:** 1.1.0 | **Last Updated:** January 3, 2026
