# Presentation Generator Skill

A comprehensive Claude Code skill for generating professional, branded PowerPoint presentations from markdown definitions, featuring AI-powered image generation and extensible brand templates.

## Overview

### What This Skill Does

The Presentation Generator skill transforms structured markdown slide definitions into polished PowerPoint presentations with:

- **Multiple Brand Templates**: Pre-built templates for Chick-fil-A, Stratfield Consulting, and extensible for custom brands
- **AI Image Generation**: Automatic slide image generation using Google Gemini Pro API for slides with graphic descriptions
- **Structured Markdown Format**: Comprehensive template system capturing titles, content, speaker notes, graphics, and background research
- **Programmatic Layout Control**: Precise positioning, typography, and styling using python-pptx

### Key Features

- 📝 Parse markdown presentations with complete slide definitions
- 🎨 Generate slide images only when needed (slides with `**Graphic**:` sections)
- 🎯 Select from multiple brand templates interactively
- 🔧 Precise control over fonts, colors, bullets, and layouts
- 📊 Support for 5+ slide types: title, section breaks, content, images, and combined layouts
- 🚀 Fast development mode with optional 4K production output
- ♻️ Extensible architecture for adding new brand templates

### Workflow

```
Markdown Definition → Parse Slides → Generate Images → Build PowerPoint
     (your content)      (parser)     (Gemini API)      (brand template)
                                                              ↓
                                                       presentation.pptx
```

---

## Quick Start

### Interactive Mode (Recommended)

```bash
# Run the interactive CLI
python generate_presentation.py

# You'll be prompted for:
# 1. Path to markdown file
# 2. Brand template selection (CFA, Stratfield, etc.)
# 3. Optional style JSON path
# 4. Output filename
```

### Basic Command-Line Usage

```bash
python generate_presentation.py \
  --markdown my_presentation.md \
  --template cfa \
  --output quarterly_review.pptx
```

---

## Installation

### Dependencies

Install required Python packages:

```bash
pip install python-pptx Pillow lxml google-genai
```

**Package versions:**
- `python-pptx >= 0.6.21` - PowerPoint file generation
- `Pillow >= 9.0.0` - Image processing
- `lxml >= 4.9.0` - XML manipulation for bullet formatting
- `google-genai >= 0.3.0` - Gemini API for image generation

### Environment Setup

Set your Google API key for image generation:

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**Windows Command Prompt:**
```cmd
set GOOGLE_API_KEY=your-api-key-here
```

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY="your-api-key-here"
```

> **Note:** Image generation requires a valid Google API key. Without it, the skill will skip image generation and use placeholder graphics where needed.

---

## Markdown Format Reference

### Template Structure

Presentations are defined using the format in `pres-template.md`. Each slide follows this structure:

```markdown
## **SLIDE 1: TITLE SLIDE**

**Title**: My Presentation Title

**Subtitle**: An engaging subtitle

**Content**:
- Key point one
- Key point two
  - Supporting detail (indented)

**Graphic**: Modern illustration showing a technology stack with gradient
background in brand colors. Include abstract geometric shapes representing
data flow. Clean, professional style.

**SPEAKER NOTES**:
"Welcome everyone. Today we'll explore..."
[Pause for effect]
[Point to the graphic]
"As you can see in this diagram..."

**BACKGROUND**:
**Rationale:** This slide sets the context...

**Sources:**
1. [Research citation with link] - Description
```

### Key Sections

| Section | Required | Purpose | Triggers Image Gen |
|---------|----------|---------|-------------------|
| `**Title**:` | Yes | Main slide heading | No |
| `**Subtitle**:` | No | Secondary heading (title slides) | No |
| `**Content**:` | Yes | Bullets, lists, tables | No |
| `**Graphic**:` | No | Visual description for AI | **YES** |
| `**SPEAKER NOTES**:` | No | Presenter narration | No |
| `**BACKGROUND**:` | No | Research and rationale | No |
| `**Sources**:` | No | Citations and references | No |

### Important Notes

- **Image generation is triggered ONLY when a slide has a `**Graphic**:` section**
- Bullet points support 3 indentation levels (0, 1, 2)
- Slide types are inferred from the header (e.g., "TITLE SLIDE", "CONTENT", "SECTION DIVIDER")
- Use markdown formatting: bold, lists, tables, code blocks

### Example Slide Definitions

**Title Slide:**
```markdown
## **SLIDE 1: TITLE SLIDE**

**Title**: Q4 Business Review

**Subtitle**: Operations & Strategy Update

**Graphic**: Professional background with geometric shapes in corporate colors
```

**Content Slide:**
```markdown
## **SLIDE 3: CONTENT**

**Title**: Key Achievements

**Content**:
- Revenue exceeded targets by 12%
  - North region: +15%
  - South region: +10%
- Customer satisfaction at all-time high
- New product launch successful
  - 10K units sold in first month
```

**Section Break:**
```markdown
## **SLIDE 5: SECTION DIVIDER**

**Title**: Financial Performance
```

**Image Slide:**
```markdown
## **SLIDE 7: DIAGRAM**

**Title**: System Architecture

**Graphic**: Technical architecture diagram showing microservices, API gateway,
and database layer. Use clean lines, minimal text, modern tech aesthetic.
```

---

## Available Templates

### CFA (Chick-fil-A)

Professional red and blue branded template.

**Brand Colors:**
- Primary Red: `#DD0033`
- Dark Blue: `#004F71`
- Text Gray: `#5B6770`
- Light Gray: `#EEEDEB`

**Typography:**
- Font Family: **Apercu**
- Bullets: Wingdings § character in gray

**Slide Types:**
1. **Title Slide** - Red background with white CFA compass logo
2. **Section Break** - Dark blue background with centered title
3. **Content Slide** - White background with title, subtitle, and bulleted content
4. **Image Slide** - White background with title and large image
5. **Text + Image Slide** - Gray left panel with bullets, image on right

**Usage:**
```python
from templates import get_template

prs = get_template("cfa")
prs.add_title_slide("Quarterly Review", "Q4 2025", "January 2026")
prs.add_section_break("Revenue Analysis")
prs.add_content_slide("Key Metrics", "Performance Overview", [
    ("Sales increased 15%", 0),
    ("Digital orders up 20%", 1),
])
prs.save("output.pptx")
```

---

### Stratfield Consulting

Professional green and teal template with modern aesthetic.

**Brand Colors:**
- Primary Green: `#00764F`
- Dark Teal: `#296057`
- Section Background: `#30555E`
- Background Light: `#F2F2F2`
- Text Dark: `#637878`

**Typography:**
- Font Family: **Avenir** (with Arial fallbacks)
- Bullets: Wingdings § character in green

**Slide Types:**
1. **Title Slide** - Gradient background with logo and cream-colored title
2. **Section Break** - Teal background with centered title and tree logo mark
3. **Content Slide** - Light gray background with green title and dark text
4. **Image Slide** - Light background with title and large image
5. **Text + Image Slide** - Dark teal left panel with white text, image on right

**Usage:**
```python
from templates import get_template

prs = get_template("stratfield")
prs.add_title_slide("Strategic Planning", "2026 Roadmap", "January 2026")
prs.add_section_break("Market Analysis")
prs.add_content_slide("Industry Trends", "", [
    ("Cloud adoption accelerating", 0),
    ("AI/ML integration growing", 0),
])
prs.save("output.pptx")
```

---

## Interactive Mode

When you run `python generate_presentation.py` without arguments, you'll be guided through the process:

### Step-by-Step Walkthrough

**1. Enter Markdown File Path**
```
Enter path to presentation markdown file: my_presentation.md
```
- Provide the path to your markdown file (can be relative or absolute)
- File must exist and be readable

**2. Select Brand Template**
```
Available templates:
1. Chick-fil-A (cfa) - Red and blue CFA branded template with Apercu font
2. Stratfield Consulting (stratfield) - Green and teal professional template with Avenir font

Select template (enter number): 1
```
- Enter the number corresponding to your desired template
- New templates appear automatically when added

**3. Optional Style Configuration**
```
Enter style JSON path (or press Enter for default): brand_style.json
```
- Provide path to custom style JSON for image generation
- Press Enter to use default style based on selected template
- Only needed if generating images

**4. Output Filename**
```
Output filename (default: presentation.pptx): quarterly_review.pptx
```
- Specify output filename (must end in `.pptx`)
- Press Enter to use default: `presentation.pptx`

**5. Confirmation**
```
Ready to generate. This will create images for 5 slides. Continue? [Y/n]: y
```
- Review the summary
- Type `y` or press Enter to proceed
- Type `n` to cancel

**6. Progress Display**
```
Parsing slides from my_presentation.md...
Found 12 slides (5 with graphics)

Generating images:
  [1/5] Slide 1: Generating 4K image... ✓
  [2/5] Slide 3: Generating 4K image... ✓
  ...

Building presentation:
  Adding Slide 1: Title slide
  Adding Slide 2: Content slide
  ...

✓ Saved: ./quarterly_review.pptx
```

---

## Command-Line Mode

For automation and scripting, use command-line arguments:

### Full Argument Reference

| Argument | Short | Required | Description | Default |
|----------|-------|----------|-------------|---------|
| `--markdown` | `-m` | Yes | Path to markdown slides file | - |
| `--template` | `-t` | Yes | Template ID (`cfa`, `stratfield`) | - |
| `--output` | `-o` | No | Output .pptx filename | `presentation.pptx` |
| `--style` | `-s` | No | Path to style JSON for images | Template default |
| `--skip-images` | - | No | Skip image generation entirely | `False` |
| `--fast` | - | No | Use standard resolution (not 4K) | `False` |
| `--force` | - | No | Overwrite existing images | `False` |
| `--notext` | - | No | Generate clean backgrounds | `True` |

### Common Use Cases

**Generate with CFA template:**
```bash
python generate_presentation.py \
  --markdown slides.md \
  --template cfa \
  --output q4_review.pptx
```

**Skip image generation (use existing images):**
```bash
python generate_presentation.py \
  --markdown slides.md \
  --template stratfield \
  --skip-images
```

**Fast mode for testing (standard resolution):**
```bash
python generate_presentation.py \
  --markdown slides.md \
  --template cfa \
  --fast
```

**Custom output path with style:**
```bash
python generate_presentation.py \
  --markdown presentations/deck.md \
  --template stratfield \
  --style styles/stratfield_style.json \
  --output outputs/final_presentation.pptx
```

**Force regenerate all images:**
```bash
python generate_presentation.py \
  --markdown slides.md \
  --template cfa \
  --force
```

---

## Image Generation

### Requirements

- **Google API Key**: Must be set via `GOOGLE_API_KEY` environment variable
- **Graphic Section**: Slide must have a `**Graphic**:` section in markdown
- **Internet Connection**: Required for Gemini API calls

### How It Works

1. **Selective Generation**: Only slides with `**Graphic**:` sections trigger image generation
2. **Context-Aware**: Uses slide title, content, and graphic description as context
3. **Style Consistency**: Applies brand colors and style guidelines from JSON config
4. **Smart Caching**: Skips existing images unless `--force` is specified

### Image Output

Generated images are saved to:
```
./images/
├── slide-1.jpg
├── slide-5.jpg
├── slide-7.jpg
└── slide-12.jpg
```

Only slides with graphics are generated (sparse numbering is normal).

### Flags Explained

**`--notext` (default: ON)**
- Generates clean background images without text or charts
- Allows PowerPoint to overlay text for better editability
- Recommended for most use cases

**`--fast` (default: OFF)**
- Uses standard resolution instead of 4K
- Faster generation (~15-20 seconds vs 30-60 seconds)
- Lower cost per image
- Use for development/testing

**`--force` (default: OFF)**
- Regenerates images even if they already exist
- Use when updating graphic descriptions
- Overwrites existing files in `./images/`

### Style JSON Format

Create a `style.json` file to customize image generation:

```json
{
  "brand_colors": ["#DD0033", "#004F71", "#FFFFFF"],
  "style": "professional, modern, clean, minimal",
  "tone": "corporate and approachable",
  "visual_elements": "geometric shapes, gradients, abstract illustrations",
  "typography": "sans-serif, modern fonts, minimal text",
  "imagery": "no photographs, vector-style graphics",
  "background": "subtle gradients, solid colors from brand palette"
}
```

### API Details

- **Model**: `gemini-3-pro-image-preview`
- **Aspect Ratio**: 16:9 (slide format)
- **Resolution**: 4K (or standard with `--fast`)
- **Timeout**: 5 minutes per image
- **Retries**: Up to 3 attempts with 5-second delays

---

## Adding New Templates

Follow these steps to create a custom brand template:

### 1. Create Directory Structure

```bash
mkdir -p presentation-skill/templates/acme/assets
```

### 2. Prepare Brand Assets

Place assets in `templates/acme/assets/`:
- Logos (PNG format, transparent background recommended)
- Background images
- Footer graphics
- Icons

Example assets:
```
templates/acme/assets/
├── logo_title.png      # For title slide
├── logo_footer.png     # For content slide footers
├── logo_mark.png       # For section breaks
└── background.png      # Optional background image
```

### 3. Create Template Module

Create `templates/acme/template.py`:

```python
"""
Acme Corporation PowerPoint Template
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pathlib import Path

from lib.template_base import PresentationTemplate
from templates import register_template


def hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert hex color to RGBColor."""
    hex_color = hex_color.lstrip('#')
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16)
    )


# Brand colors
COLORS = {
    'primary': '#003366',      # Navy blue
    'secondary': '#FF6600',    # Orange
    'text': '#333333',         # Dark gray
    'white': '#FFFFFF',
}

# Fonts
FONTS = {
    'heading': 'Helvetica Neue Bold',
    'body': 'Helvetica Neue',
}


@register_template
class AcmePresentation(PresentationTemplate):
    """
    Acme Corporation branded presentation template.
    """

    @property
    def name(self) -> str:
        return "Acme Corporation"

    @property
    def id(self) -> str:
        return "acme"

    @property
    def description(self) -> str:
        return "Navy and orange corporate template"

    def __init__(self, assets_dir: str = None):
        self.prs = Presentation()
        self.prs.slide_width = Inches(10)     # 16:9 aspect ratio
        self.prs.slide_height = Inches(5.625)

        if assets_dir:
            self.assets_dir = Path(assets_dir)
        else:
            self.assets_dir = Path(__file__).parent / 'assets'

        self._slide_count = 0

    def add_title_slide(self, title: str, subtitle: str = "", date: str = "") -> None:
        """Add title slide."""
        self._slide_count += 1
        # Implementation...
        pass

    def add_section_break(self, title: str) -> None:
        """Add section break slide."""
        self._slide_count += 1
        # Implementation...
        pass

    def add_content_slide(self, title: str, subtitle: str, bullets: list) -> None:
        """Add content slide with bullets."""
        self._slide_count += 1
        # Implementation...
        pass

    def add_image_slide(self, title: str, image_path: str, subtitle: str = "") -> None:
        """Add image slide."""
        self._slide_count += 1
        # Implementation...
        pass

    def add_text_and_image_slide(self, title: str, bullets: list, image_path: str) -> None:
        """Add split slide with text and image."""
        self._slide_count += 1
        # Implementation...
        pass

    def save(self, filepath: str) -> None:
        """Save presentation."""
        self.prs.save(filepath)
        print(f"Saved: {filepath}")

    def get_slide_count(self) -> int:
        """Get number of slides."""
        return self._slide_count

    def get_assets_dir(self) -> Path:
        """Get assets directory path."""
        return self.assets_dir
```

### 4. Register Template

Add import to `templates/__init__.py`:

```python
# Import all templates to register them
from templates.cfa.template import CFAPresentation
from templates.stratfield.template import StratfieldPresentation
from templates.acme.template import AcmePresentation  # Add this line
```

### 5. Test Template

```python
from templates import get_template

prs = get_template("acme")
prs.add_title_slide("Test Presentation")
prs.save("test.pptx")
```

The new template will automatically appear in the interactive menu!

### Tips for Template Development

1. **Study existing templates**: Review `cfa/template.py` and `stratfield/template.py` for patterns
2. **Define layout specs**: Use dictionaries for positioning (x, y, width, height in inches)
3. **Implement bullet formatting**: Use the XML-based approach shown in existing templates
4. **Handle missing assets gracefully**: Use placeholder rectangles if images don't exist
5. **Test all slide types**: Ensure each method works correctly

---

## File Structure

```
presentation-skill/
├── SKILL.md                    # This documentation file
├── generate_presentation.py    # Main entry point (interactive CLI)
│
├── lib/                        # Core library modules
│   ├── __init__.py
│   ├── parser.py              # Markdown slide parser
│   ├── image_generator.py     # Gemini API image generation
│   ├── template_base.py       # Abstract base class for templates
│   └── assembler.py           # PowerPoint assembly orchestration
│
└── templates/                  # Brand template packages
    ├── __init__.py            # Template registry
    │
    ├── cfa/                   # Chick-fil-A template
    │   ├── __init__.py
    │   ├── template.py        # CFA implementation
    │   └── assets/            # CFA brand assets
    │       ├── logo_white.png
    │       ├── chicken_red.png
    │       └── chicken_white.png
    │
    └── stratfield/            # Stratfield Consulting template
        ├── __init__.py
        ├── template.py        # Stratfield implementation
        └── assets/            # Stratfield brand assets
            ├── title_background.png
            ├── logo_title.png
            ├── logo_footer.png
            ├── logo_mark.png
            └── footer_bar.png
```

---

## Troubleshooting

### Common Errors and Solutions

#### Missing API Key

**Error:**
```
Warning: GOOGLE_API_KEY not set. Skipping image generation.
```

**Solution:**
Set the environment variable:
```bash
export GOOGLE_API_KEY="your-key-here"
```

Or use `--skip-images` to generate without images.

---

#### Font Not Found

**Error:**
```
Font 'Apercu' not found, using fallback
```

**Solution:**
- Install the required font on your system
- For CFA template: Install Apercu font
- For Stratfield: Install Avenir font (or accept Arial fallback)
- Fonts are specified in template files and can be customized

---

#### Image Generation Failure

**Error:**
```
Failed to generate image for Slide 5 after 3 retries
```

**Solution:**
1. Check internet connection
2. Verify API key is valid and has quota
3. Review graphic description (avoid very complex prompts)
4. Use `--fast` flag for faster, more reliable generation
5. Check Gemini API status

---

#### Invalid Markdown Format

**Error:**
```
Warning: Slide 7 has no title, skipping
```

**Solution:**
- Ensure each slide has `**Title**:` field
- Check slide header format: `## **SLIDE N: TYPE**` or `## Slide N`
- Validate markdown syntax (no missing asterisks)

---

#### Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: 'presentation.pptx'
```

**Solution:**
- Close the PowerPoint file if it's open
- Check write permissions in output directory
- Use a different output filename with `--output`

---

#### Template Not Found

**Error:**
```
ValueError: Unknown template: acme
```

**Solution:**
- Check template ID spelling (`cfa`, `stratfield`)
- Ensure template is imported in `templates/__init__.py`
- Run without arguments to see available templates

---

#### Missing Assets

**Warning:**
```
Asset not found: logo_white.png, using fallback
```

**Solution:**
- Check assets directory exists: `templates/{template}/assets/`
- Verify asset filenames match template code
- Templates use gray rectangles as fallbacks (presentation still generates)

---

## Complete Examples

### Example 1: Simple Presentation

**Markdown file (`simple.md`):**

```markdown
## **SLIDE 1: TITLE SLIDE**

**Title**: Company Overview

**Subtitle**: Building the Future

**Graphic**: Modern corporate background with geometric shapes in blue tones

---

## **SLIDE 2: SECTION DIVIDER**

**Title**: Our Mission

---

## **SLIDE 3: CONTENT**

**Title**: Core Values

**Content**:
- Innovation drives everything we do
  - Continuous improvement
  - Embrace new technologies
- Customer satisfaction is paramount
- Teamwork makes us stronger
  - Collaboration across departments
  - Open communication

---

## **SLIDE 4: CONTENT**

**Title**: Thank You

**Content**:
- Questions?
- Contact: info@company.com
```

**Generate:**

```bash
python generate_presentation.py \
  --markdown simple.md \
  --template cfa \
  --output company_overview.pptx
```

**Output:**
- `./company_overview.pptx` - 4 slides
- `./images/slide-1.jpg` - Title slide background

---

### Example 2: Technical Presentation with Images

**Markdown file (`technical.md`):**

```markdown
## **SLIDE 1: TITLE SLIDE**

**Title**: System Architecture Review

**Subtitle**: Microservices Migration Strategy

**Graphic**: Technical background with circuit board patterns and blue/teal gradient

---

## **SLIDE 2: SECTION DIVIDER**

**Title**: Current State

---

## **SLIDE 3: DIAGRAM**

**Title**: Legacy Architecture

**Graphic**: Architecture diagram showing monolithic application with database,
using clean lines and minimal text. Show single large box labeled "Monolith"
connected to database cylinder. Use gray and blue colors.

---

## **SLIDE 4: SECTION DIVIDER**

**Title**: Proposed Solution

---

## **SLIDE 5: DIAGRAM**

**Title**: Microservices Architecture

**Graphic**: Modern microservices architecture diagram showing API gateway,
multiple service boxes (Auth, Orders, Inventory, Payments), message queue,
and distributed databases. Clean, professional, minimal text, blue color scheme.

---

## **SLIDE 6: CONTENT**

**Title**: Migration Benefits

**Content**:
- Improved scalability
  - Independent service scaling
  - Better resource utilization
- Enhanced reliability
  - Fault isolation
  - Easier rollbacks
- Faster development
  - Parallel team development
  - Technology flexibility

---

## **SLIDE 7: CONTENT**

**Title**: Next Steps

**Content**:
- Phase 1: Extract authentication service (Q1)
- Phase 2: Break out payment processing (Q2)
- Phase 3: Migrate remaining services (Q3-Q4)
```

**With custom style (`tech_style.json`):**

```json
{
  "brand_colors": ["#0066CC", "#00CCFF", "#FFFFFF", "#333333"],
  "style": "technical, clean, modern, professional",
  "tone": "enterprise technology",
  "visual_elements": "architecture diagrams, flowcharts, boxes and arrows",
  "typography": "sans-serif, minimal labels",
  "imagery": "abstract technical illustrations, no photographs",
  "background": "subtle gradients, white or light blue backgrounds"
}
```

**Generate:**

```bash
python generate_presentation.py \
  --markdown technical.md \
  --template stratfield \
  --style tech_style.json \
  --output architecture_review.pptx
```

**Output:**
- `./architecture_review.pptx` - 7 slides
- `./images/slide-1.jpg` - Title background
- `./images/slide-3.jpg` - Legacy architecture diagram
- `./images/slide-5.jpg` - Microservices diagram

---

### Example 3: Fast Development Workflow

When iterating on presentations, use fast mode:

```bash
# First pass: fast mode for quick preview
python generate_presentation.py \
  --markdown draft.md \
  --template cfa \
  --fast \
  --output draft.pptx

# Review the presentation...

# Final version: 4K images
python generate_presentation.py \
  --markdown draft.md \
  --template cfa \
  --force \
  --output final.pptx
```

---

## Additional Resources

### Related Files

- **`pres-template.md`** - Comprehensive markdown template with all sections explained
- **`generate_images_for_slides.py`** - Standalone image generation script (legacy)
- **`CLAUDE.md`** - Project overview and development guidance

### Template Reference

For detailed template implementation examples:
- Study `templates/cfa/template.py` for CFA implementation
- Study `templates/stratfield/template.py` for Stratfield implementation
- Review `lib/template_base.py` for abstract interface

### Extending the System

To extend functionality:
1. **Add slide types**: Modify `SLIDE_TYPE_MAP` in `lib/assembler.py`
2. **Add templates**: Follow "Adding New Templates" section
3. **Customize parsing**: Modify `lib/parser.py` for additional markdown sections
4. **Enhance images**: Update `lib/image_generator.py` for different image models or providers

---

## Support

For issues or questions:
1. Check this documentation's Troubleshooting section
2. Review template source code for implementation details
3. Validate markdown format against `pres-template.md`
4. Test with simple examples first before complex presentations

---

**Version:** 1.0
**Last Updated:** January 2026
**License:** Internal Use
