# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains a Claude Code skill for generating PowerPoint presentations from markdown presentation definitions. The system uses:
- Python scripts to generate slide images via Google Gemini API
- Python-pptx based presentation builders with brand-specific templates
- Markdown-based slide content definition format (see `pres-template.md`)

## Key Components

### 1. Presentation Template Format (`pres-template.md`)

This is a comprehensive template that defines the structure for presentation slide definitions. It includes:
- **Slide metadata**: Type classification (TITLE SLIDE, PROBLEM STATEMENT, INSIGHT, etc.)
- **Content**: Visible slide content with bullets, tables, quotes, code blocks
- **Graphics**: Detailed visual descriptions for AI image generation
- **Speaker Notes**: Full narration with stage directions and transitions
- **Background**: Research citations, rationale, and Q&A preparation
- **Implementation Guidance**: Actionable next steps for the audience

Each slide follows a complete structure capturing everything needed for both slide generation and presenter preparation.

### 2. Image Generation Script (`generate_images_for_slides.py`)

Batch generates presentation slide images using Google Gemini Pro API.

**Usage:**
```bash
python generate_images_for_slides.py --style style.json --slides presentation.md --output ./images
```

**Key flags:**
- `--style`: JSON file defining visual style guidelines
- `--slides`: Markdown file with slide definitions (follows `pres-template.md` format)
- `--output`: Directory for generated images (default: current directory)
- `--fast`: Use standard resolution instead of 4K (faster, cheaper)
- `--dry-run`: Parse slides without calling API
- `--force`: Overwrite existing images
- `--notext`: Generate clean backgrounds without text/charts (for text overlay later)

**Environment:**
- Requires `GOOGLE_API_KEY` environment variable
- Uses model: `gemini-3-pro-image-preview`
- Max 3 retries with 5-second delay
- 5-minute timeout for 4K generation

**Slide parsing:**
- Extracts slides by detecting headers containing "Slide N" (case-insensitive)
- Handles markdown formats: `## **SLIDE 1: TITLE**`, `## Slide 1`, `Slide 1`
- Generates images as `slide-{N}.jpg` in output directory

### 3. Brand Template Packages

Two example PowerPoint template implementations are included as zip files:

**CFA Template** (`cfa-ppt-v1.0.zip`):
- Chick-fil-A branded presentation builder
- Red (#DD0033) title slides, dark blue (#004F71) section breaks
- Apercu font, Wingdings § bullets
- 5 slide types: title, section break, content, image, text+image
- Assets: logo_white.png, chicken_red.png, chicken_white.png

**Stratfield Template** (`stratfield-ppt-v1.0.zip`):
- Custom branded presentation builder
- Assets: title_background.png, logo variants, footer_bar.png

Both use python-pptx and follow similar architecture patterns.

## Development Tasks

### Setting Up for Development

1. Install Python dependencies:
```bash
pip install google-genai pillow
pip install python-pptx pillow lxml  # For PPT generation
```

2. Set Google API key:
```bash
export GOOGLE_API_KEY="your-key-here"  # Linux/Mac
set GOOGLE_API_KEY=your-key-here       # Windows CMD
$env:GOOGLE_API_KEY="your-key-here"    # Windows PowerShell
```

### Creating a New Brand Template

When creating a new PowerPoint skill package:

1. **Study existing templates** (`cfa.py` in cfa-ppt-v1.0.zip or `stratfield.py` in stratfield-ppt-v1.0.zip)

2. **Define brand constants**:
   - Colors (hex values)
   - Fonts (heading, body)
   - Slide dimensions (typically 16:9 widescreen: 13.33" × 7.50")

3. **Specify layout specs** for each slide type:
   - Position/size of title, subtitle, body text (x, y, w, h in inches)
   - Background colors
   - Logo/asset positions
   - Footer elements (slide numbers, icons)

4. **Implement slide type methods**:
   - Title slide
   - Section break
   - Content slide (with bullets)
   - Image slide
   - Text + image slide
   - Any custom layouts

5. **Include assets**:
   - Brand logos (PNG format)
   - Background images
   - Footer icons
   - Organize in `assets/` subdirectory

6. **Create SKILL.md documentation**:
   - Overview and installation
   - Brand colors/fonts reference
   - Usage examples for each slide type
   - Complete working example
   - Dependencies list

### Generating Slide Images

1. **Create style definition** (JSON):
```json
{
  "brand_colors": ["#DD0033", "#004F71"],
  "style": "professional, clean, modern",
  "tone": "corporate",
  "visual_elements": "geometric shapes, minimal text"
}
```

2. **Write presentation markdown** following `pres-template.md` structure

3. **Generate images**:
```bash
python generate_images_for_slides.py \
  --style brand_style.json \
  --slides presentation.md \
  --output ./slide-images \
  --notext
```

4. **Test with different flags**:
   - Use `--dry-run` first to verify slide parsing
   - Use `--fast` during development
   - Remove `--fast` for final 4K generation
   - Use `--force` to regenerate specific slides

### Building Claude Code Skills

To package a new presentation skill:

1. Create directory structure:
```
skill-name/
├── SKILL.md          # Documentation
├── skill_module.py   # Main Python module
└── assets/           # Brand assets
    ├── logo.png
    └── ...
```

2. Implement main class with methods for each slide type

3. Follow naming convention: `SkillNamePresentation` class with `add_*_slide()` methods

4. Package as zip: `zip -r skill-name-v1.0.zip skill-name/`

## Architecture Notes

### Presentation Definition Flow
1. **Content Definition** → Markdown file following pres-template.md structure
2. **Image Generation** → generate_images_for_slides.py + Gemini API → slide-{N}.jpg files
3. **PowerPoint Assembly** → Brand-specific Python module (e.g., cfa.py) → final .pptx

### Bullet Formatting Pattern
All templates use XML-level bullet formatting for proper indentation:
- Define BULLET_SPECS dict with marL/indent/size for levels 0-2
- Use `_apply_bullet_formatting()` method to inject XML elements
- Insert buClr, buFont, buChar before defRPr in strict order

### Image Handling Pattern
- Use PIL to calculate aspect-fit dimensions
- Center images within bounding boxes
- Fall back to gray placeholder rectangles if image missing

## API Reference

**Gemini Pro Image Generation:**
- Model: `gemini-3-pro-image-preview`
- Response modality: `IMAGE`
- Aspect ratio: `16:9` for slides
- Image size: `4K` (or standard with --fast)
- Typical generation time: 30-60 seconds per 4K image

**Python-pptx Key Components:**
- `Presentation()`: Main presentation object
- `slide_layouts[6]`: Blank layout (no placeholders)
- Dimensions: Set via `prs.slide_width` / `prs.slide_height`
- Colors: Use `RGBColor(r, g, b)` from hex conversion
- Text: Position via `add_textbox()`, format via `font` properties
- Images: Add via `add_picture()` with explicit dimensions

## File Conventions

- **Slide images**: `slide-{number}.jpg` (e.g., slide-1.jpg, slide-12.jpg)
- **Style definitions**: `{brand}_style.json`
- **Presentation content**: `{topic}.md` or `{topic}_slides.md`
- **Generated presentations**: `{topic}.pptx`
- **Skill packages**: `{brand}-ppt-v{version}.zip`

## Intelligent Presentation Generation (v1.1.0+)

The presentation generator now includes intelligent slide type classification and optional visual validation with iterative refinement.

### Workflow Architecture

**Standard Workflow (5 stages):**
1. **Parse** → Extract slides from markdown
2. **Classify** → Intelligently determine optimal slide type for each slide
3. **Generate Images** → Create AI-generated graphics (if needed)
4. **Build** → Assemble PowerPoint with appropriate templates
5. **Save** → Output final presentation

**With Validation (7 stages - EXPERIMENTAL):**
1-3. Same as above
4. **Build + Validate Loop** → For each slide:
   - Build slide in presentation
   - Export slide to JPG
   - Validate against intent using Gemini vision
   - If validation fails: refine and regenerate (max 3 attempts)
5. **Save** → Output final presentation

### Intelligent Slide Type Classification

**Module:** `lib/type_classifier.py`

**Hybrid Approach:**
- **Rule-based (~80%)**: Fast, deterministic classification for obvious cases
  - Explicit markers: "TITLE SLIDE" → title, "SECTION DIVIDER" → section
  - Position heuristics: slide 1 + no content → title
  - Content structure: graphic+bullets → text_image, graphic only → image

- **AI-powered (~20%)**: Gemini semantic analysis for ambiguous cases
  - Analyzes slide content, structure, and intent
  - Returns JSON classification with confidence score

**5 Template Types:**
- `title`: Cover slide with logo, centered title, subtitle
- `section`: Section divider with single heading
- `content`: Text-heavy slide with bullets (no image)
- `image`: Visual-first slide with full-width image
- `text_image`: Balanced slide with text panel + image panel

**Usage:**
```python
from lib.type_classifier import SlideTypeClassifier

classifier = SlideTypeClassifier()
classification = classifier.classify_slide(slide)
# Returns: TypeClassification(slide_type, confidence, reasoning, template_method)
```

### Visual Validation System

**Module:** `lib/visual_validator.py`

**Validation Rubric (100 points):**
- Content Accuracy (30%): Title, bullets, key info present
- Visual Hierarchy (20%): Readable, well-structured
- Brand Alignment (20%): Colors, fonts, style consistency
- Image Quality (15%): Relevant, properly sized, clear
- Layout Effectiveness (15%): Spacing, balance, polish

**Threshold:** 75% score to pass

**Usage:**
```python
from lib.visual_validator import VisualValidator

validator = VisualValidator()
result = validator.validate_slide(
    slide_image_path="slide-1.jpg",
    original_slide=slide,
    style_config=style_config,
    slide_type="content"
)
# Returns: ValidationResult(passed, score, issues, suggestions, rubric_scores)
```

### Refinement Engine

**Module:** `lib/refinement_engine.py`

**Pattern-Based Refinement:**
- Detects common issues (size, color, text, clarity)
- Generates enhanced prompts with specific fixes
- Progressive escalation: Attempt 1 (prompt enhancement), Attempt 2+ (force 4K)
- Smart stopping: Max 3 attempts, diminishing returns threshold

**Issue Patterns:**
- Image too small → "Make visual element LARGE and PROMINENT"
- Colors mismatch → "STRICTLY use brand colors from style guide"
- Text in image → "ABSOLUTELY NO TEXT in generated image"
- Quality issues → Force 4K generation

**Usage:**
```python
from lib.refinement_engine import RefinementEngine

refiner = RefinementEngine()
refinement = refiner.generate_refinement(slide, validation_result, attempt=1)
# Returns: RefinementStrategy(modified_prompt, parameter_adjustments, reasoning, confidence)
```

### Slide Export (Windows Only)

**Module:** `lib/slide_exporter.py`

Exports PowerPoint slides to JPG images for validation using PowerShell COM automation.

**Requirements:**
- Windows OS
- Microsoft PowerPoint 2013+ installed
- PowerShell 5.1+

**Usage:**
```python
from lib.slide_exporter import SlideExporter

exporter = SlideExporter(resolution=150)
success = exporter.export_slide(
    pptx_path="presentation.pptx",
    slide_number=1,
    output_path="slide-1.jpg"
)
```

### Command Line Usage

**Standard Generation:**
```bash
python generate_presentation.py presentation.md --template cfa
```

**With Validation (EXPERIMENTAL - Windows + PowerPoint required):**
```bash
python generate_presentation.py presentation.md \
  --template cfa \
  --enable-validation \
  --max-refinements 3 \
  --validation-dpi 150
```

**Validation Flags:**
- `--enable-validation`: Enable slide validation and refinement
- `--max-refinements`: Maximum refinement attempts per slide (default: 3)
- `--validation-dpi`: DPI for slide export (default: 150)

### Graceful Degradation

All validation features include comprehensive error handling:
- Classification failure → Use rule-based only
- Export failure → Skip validation for that slide
- Validation API failure → Accept slide without validation
- Max attempts reached → Accept best attempt
- Any component failure → Continue without validation

The system will **always produce a presentation**, even if validation fails.

### Performance Considerations

**API Usage (20-slide presentation with validation):**
- Classification: ~4 calls (20% of slides)
- Image generation: 20-60 calls (initial + refinements)
- Validation: 20-60 calls (1-3 per slide)
- **Total:** ~100-150 API calls
- **Estimated cost:** $1.50 - $3.00

**Time Estimates:**
- Without validation: 5-10 minutes (depends on image generation)
- With validation: 15-30 minutes (adds export + validation per slide)

### File Organization

```
presentation-skill/
├── lib/
│   ├── assembler.py              # Main workflow orchestration
│   ├── parser.py                 # Markdown parsing
│   ├── type_classifier.py        # Intelligent slide classification
│   ├── image_generator.py        # AI image generation
│   ├── slide_exporter.py         # PowerShell COM export (Windows)
│   ├── visual_validator.py       # Gemini vision validation
│   └── refinement_engine.py      # Feedback-driven refinement
├── templates/                     # Brand templates (CFA, Stratfield)
└── generate_presentation.py      # CLI entry point

output/
├── presentation.pptx              # Final output
├── images/
│   └── slide-{1..N}.jpg          # Generated images
└── validation/                    # (if validation enabled)
    ├── slide-1-attempt-1.jpg
    ├── slide-2-attempt-1.jpg
    ├── slide-2-attempt-2.jpg      # Refined version
    └── ...
```

### Development Notes

**Adding New Validation Patterns:**

Edit `lib/refinement_engine.py` to add new issue detection patterns:

```python
ISSUE_PATTERNS = {
    r'your_issue_pattern': {
        'prompt_addition': 'Specific fix instruction',
        'param': {'parameter_name': value},  # Optional
        'reasoning': 'Why this fix helps'
    }
}
```

**Testing Classification:**

```bash
cd presentation-skill
python lib/type_classifier.py presentation.md
```

**Testing Validation:**

```bash
cd presentation-skill
python lib/visual_validator.py slide-1.jpg presentation.md --slide-number 1 --type content
```

**Testing Slide Export:**

```bash
cd presentation-skill
python lib/slide_exporter.py presentation.pptx --slide 1 --output-dir ./exported
```

