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

### 2. Prompt & Image Generation Scripts

**Two main utilities** for generating prompts and images with full CLI support:

#### A. `generate_prompts.py` - Prompt Generation

Generates AI image prompts from presentation markdown for ANY resolution (high/medium/small).

**Basic Usage:**
```bash
# Generate prompts with defaults (small resolution, no titles)
python generate_prompts.py

# Generate high-resolution prompts (with titles)
python generate_prompts.py --resolution high

# Specify custom paths
python generate_prompts.py \
  --resolution medium \
  --presentation my_presentation.md \
  --style templates/cfa_style.json \
  --output ./prompts/medium
```

**Command-Line Options:**
- `--resolution, -r` - Resolution: small/medium/high (default: small)
- `--presentation, -p` - Path to presentation markdown
- `--style, -s` - Path to style JSON file
- `--config, -c` - Path to prompt_config.md
- `--output, -o` - Output directory for prompts

**What It Does:**
1. Parses presentation markdown
2. Loads unified config from `prompt_config.md`
3. Generates prompts using resolution-specific rules
4. Saves prompt files (prompt-01.md, prompt-02.md, etc.)

#### B. `generate_images.py` - Image Generation

Generates actual images from prompts using Gemini API for ANY resolution.

**Basic Usage:**
```bash
# Generate images with defaults (small resolution)
python generate_images.py

# Generate high-resolution 4K images
python generate_images.py --resolution high

# Specify custom paths
python generate_images.py \
  --resolution medium \
  --input ./prompts/medium \
  --output ./images/medium \
  --style templates/cfa_style.json
```

**Command-Line Options:**
- `--resolution, -r` - Resolution: small/medium/high (default: small)
- `--input, -i` - Input directory with prompt files
- `--output, -o` - Output directory for images (default: same as input)
- `--style, -s` - Path to style JSON file
- `--config, -c` - Path to prompt_config.md

**What It Does:**
1. Reads prompt files from input directory
2. Loads unified config for API parameters
3. Generates images via Gemini API
4. Saves images (slide-01.jpg, slide-02.jpg, etc.)
5. Respects config-driven delays and validation

**Complete Workflow Example:**
```bash
# 1. Generate prompts for high resolution
python generate_prompts.py --resolution high --output ./high-res/prompts

# 2. Generate images from those prompts
python generate_images.py --resolution high --input ./high-res/prompts --output ./high-res/images

# 3. Use a custom config for brand-specific settings
python generate_prompts.py --config prompt_config_acme.md --resolution small
python generate_images.py --config prompt_config_acme.md --resolution small
```

**Backward Compatibility Note:**

These scripts were renamed in v1.1 for clarity:
- `generate_small_prompts.py` → `generate_prompts.py` (now supports all resolutions)
- `generate_small_images.py` → `generate_images.py` (now supports all resolutions)

If you have existing scripts or documentation referencing the old names, simply update the filenames. The functionality and command-line options are identical.

---

### 3. Unified Configuration System (`prompt_config.md`)

**New in v1.1:** All prompt generation AND image generation settings externalized to a single configuration file for easy customization without code changes.

**Configuration File:** `prompt_config.md`
- Format: Markdown file with YAML frontmatter
- Location: Project root directory
- Dependency: `python-frontmatter` (included in requirements.txt)
- **Used by:** `generate_prompts.py` AND `generate_images.py`

**What's Configurable:**

**Prompt Generation:**
1. **Resolution Definitions** - Dimensions and aspect ratios for high/medium/small outputs
2. **Prompt Templates** - Structure and sections of generated prompts
3. **Composition Rules** - Resolution-specific layout instructions (especially "no titles" for small res)
4. **Generic Instructions** - Universal quality guidelines applied to all prompts
5. **Layout Detection Patterns** - Regex patterns to auto-detect optimal layouts
6. **Element Extraction** - Markers and parsing rules for slide content
7. **Visual Hierarchy** - Templates for priority ordering
8. **Metadata Labels** - Output file headers and labels

**Image Generation (NEW):**
9. **Gemini API Model** - Model name (e.g., `gemini-3-pro-image-preview`)
10. **Generation Parameters** - Per-resolution aspect ratio, image size, API delays
11. **Prompt Parsing** - Section headers and validation text patterns
12. **File Naming** - Input/output filename patterns
13. **Console Output** - Customizable status messages

**Key Benefits:**

- ✅ **Single source of truth** - One config for prompts AND images
- ✅ Modify prompts & generation params without editing Python code
- ✅ Create brand-specific config variations
- ✅ Document prompt engineering decisions inline
- ✅ Version control your entire generation strategy
- ✅ Quick A/B testing of different instructions

**Usage Examples:**

```python
# Prompt generation (generate_prompts.py)
from lib.image_prompt_builder import ImagePromptBuilder

builder = ImagePromptBuilder(
    style_config_path='templates/cfa_style.json',
    config_path='prompt_config.md',  # Uses unified config
    resolution='small'
)
prompt = builder.build_prompt(slide_data)

# Image generation (generate_images.py)
import frontmatter

# Load same config
with open('prompt_config.md', 'r') as f:
    config = frontmatter.load(f).metadata

# Use image generation settings
model = config['image_generation']['model']
params = config['image_generation']['generation_params']['small']
# aspect_ratio, image_size, delay_seconds all from config
```

**Customization Examples:**

```yaml
# Example 1: Make "no text" rule more aggressive (prompt generation)
composition_rules:
  small:
    instructions:
      - "ABSOLUTELY NO TEXT OF ANY KIND"
      - "Pure visual content only - NO titles, labels, or captions"

# Example 2: Add industry-specific layout detection (prompt generation)
layout_detection:
  medical_diagram:
    patterns: ["anatomy", "medical", "physiological"]
    layout_name: "medical_diagram"

# Example 3: Adjust API timing for rate limits (image generation)
image_generation:
  generation_params:
    small:
      delay_seconds: 8  # Increase delay to avoid rate limits

# Example 4: Use different model (image generation)
image_generation:
  model: "gemini-pro-vision-2"  # Switch to different model
```

**Validation & Fallback:**
- Missing config file → Uses embedded defaults (preserves original behavior)
- Malformed YAML → Warning message + fallback to defaults
- Missing sections → Per-section fallback to defaults

**See Also:** `prompt_config.md` contains comprehensive documentation including:
- Quick start guide
- Resolution strategy recommendations
- Prompt engineering tips
- Troubleshooting common issues
- Template variable reference

### 4. Brand Template Packages

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
# Install all dependencies from requirements.txt
pip install -r requirements.txt

# Or install individually:
pip install python-dotenv google-genai pillow python-frontmatter  # Core + config
pip install python-pptx lxml  # PowerPoint generation
```

2. **CRITICAL - Set up API Key securely:**

**DO NOT hardcode API keys in code!** Use environment variables:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your actual Google API key
# GOOGLE_API_KEY=your-actual-key-here
```

The `.env` file is git-ignored and will never be committed. All scripts load from `.env` automatically using `python-dotenv`.

**Security Features:**
- ✅ `.env` excluded in `.gitignore`
- ✅ `.env.example` provided as template
- ✅ API keys never hardcoded in source
- ✅ Automatic validation on script startup
- ✅ Clear error messages if key missing

### Security Best Practices

**API Key Protection:**
1. NEVER commit `.env` files to version control
2. NEVER include API keys in code, comments, or documentation
3. Revoke and regenerate keys immediately if exposed
4. Use separate API keys for development and production
5. Monitor API usage regularly for unauthorized activity

**Distribution Safety:**
- Ensure `.env` excluded from ZIP distributions
- Add `.env` to exclusion patterns in packaging scripts
- Verify no secrets in packaged files before distribution
- Never share `.env` files via email, chat, or file sharing services
- When sharing code snippets, always redact API keys and secrets

**Environment Variable Best Practices:**
- Always use `load_dotenv()` before accessing environment variables with `os.getenv()`
- Provide clear error messages when required environment variables are missing
- Document all required environment variables in `.env.example`
- Use `python-dotenv` for local development, native environment variables for production

**If You Accidentally Expose a Key:**
1. Revoke the exposed key immediately at https://aistudio.google.com/app/apikey
2. Generate a new API key
3. Update your `.env` file with the new key
4. Review recent API usage for unauthorized activity
5. If committed to git, consider the key permanently compromised (revoking history doesn't remove it from clones)

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


## Plugin System Architecture (v2.0)

The project has evolved from a standalone presentation generator to a comprehensive **Claude Code plugin system** with AI-assisted research, content development, and presentation generation capabilities.

### Plugin Structure

**Complete 11-Step AI-Assisted Workflow:**
1. Research Assistant - Interactive scope refinement
2. Web Research - Autonomous research with Claude Agent SDK
3. Insight Extraction - AI-powered analysis
4. Outline Generation - Multi-presentation detection
5. Content Drafting - AI-generated slide content
6. Quality Optimization - Automated improvement
7. Graphics Validation - Image description quality
8. Image Generation - Gemini Pro visuals
9. Visual Validation - Quality verification (experimental)
10. Refinement - Iterative improvement
11. PowerPoint Assembly - Final presentation

### Key Plugin Components

#### plugin/ Directory

**Core Infrastructure:**
- `base_skill.py` - Base skill interface (SkillInput, SkillOutput)
- `skill_registry.py` - Skill discovery and dependency resolution
- `workflow_orchestrator.py` - Multi-skill workflow execution with checkpoints
- `checkpoint_handler.py` - User interaction for approvals
- `config_manager.py` - Multi-source configuration with validation
- `cli.py` - Command-line interface with 11 commands

**Skills (plugin/skills/):**
- `research_assistant_skill.py` - Interactive clarifying questions
- `research_skill.py` - Autonomous web research (Claude Agent SDK)
- `insight_extraction_skill.py` - AI insight analysis
- `outline_skill.py` - Presentation outline generation
- `content_drafting_skill.py` - AI content generation
- `content_optimization_skill.py` - Quality improvement

**Libraries (plugin/lib/):**
- `claude_client.py` - Claude API client (plain API)
- `claude_agent.py` - Claude Agent SDK integration (autonomous workflows)
- `content_generator.py` - AI content generation (titles, bullets, notes, graphics)
- `quality_analyzer.py` - Content quality metrics (5 dimensions)
- `graphics_validator.py` - Graphics description validation
- `citation_manager.py` - Citation management (APA, MLA, Chicago)
- `web_search.py` - Web search abstraction
- `content_extractor.py` - HTML content extraction

### API Architecture

**Claude API Usage:**
- **Claude Sonnet 4.5** - All text generation, research, analysis, optimization
- **Plain API** - Simple single-turn operations (insights, outlines, optimization)
- **Agent SDK** - Complex multi-step workflows with tool use (research)

**Gemini API Usage:**
- **Gemini Pro** - Image generation ONLY (gemini-3-pro-image-preview)
- NOT used for text operations

**See [API_ARCHITECTURE.md](API_ARCHITECTURE.md) for complete architecture details.**
**See [CLAUDE_AGENT_SDK.md](CLAUDE_AGENT_SDK.md) for Agent SDK usage guide.**

### Content Development Workflow

#### 1. Content Drafting

Generate complete slide content from outlines using AI:

**From Python:**
```python
from plugin.skills.content_drafting_skill import ContentDraftingSkill
from plugin.base_skill import SkillInput

skill = ContentDraftingSkill()

input_data = SkillInput(
    data={
        "outline": outline_output,  # From OutlineSkill
        "research": research_output,  # From ResearchSkill (optional)
        "style_guide": {
            "tone": "conversational",
            "audience": "DIY mechanics",
            "max_bullets_per_slide": 5,
            "max_words_per_bullet": 15
        },
        "style_config": {
            "brand_colors": ["#DD0033", "#004F71"],
            "style": "professional, clean, technical"
        }
    },
    context={},
    config={}
)

result = skill.execute(input_data)

# result.data contains:
# - presentation_files: List of markdown file paths
# - presentations: List of presentation data
# - slides_generated: Total number of slides
```

**From CLI:**
```bash
python -m plugin.cli draft-content outline.md \
  --style-guide "conversational, technical" \
  --max-bullets 5 \
  --output ./output/presentation.md
```

**What It Generates:**
- **Titles**: Context-aware, audience-appropriate slide titles
- **Bullets**: Parallel-structured bullet points with word limit enforcement
- **Speaker Notes**: Full narration with stage directions ([Pause], [Transition])
- **Graphics Descriptions**: Detailed visual instructions for image generation
- **Citations**: Properly integrated from research sources

#### 2. Quality Optimization

Analyze and improve content quality:

**From Python:**
```python
from plugin.skills.content_optimization_skill import ContentOptimizationSkill

skill = ContentOptimizationSkill()

input_data = SkillInput(
    data={
        "slides": slides,  # From ContentDraftingSkill
        "style_guide": {
            "tone": "conversational",
            "reading_level": "high school"
        },
        "optimization_goals": ["readability", "parallelism", "citations"]
    },
    context={},
    config={}
)

result = skill.execute(input_data)

# result.data contains:
# - optimized_file: Path to optimized presentation
# - improvements: List of improvements made
# - quality_score_before: Score before (0-100)
# - quality_score_after: Score after (0-100)
# - quality_improvement: Delta
```

**From CLI:**
```bash
python -m plugin.cli optimize-content draft.md \
  --goals "readability, parallelism, citations" \
  --output optimized.md
```

**Quality Dimensions:**
1. **Readability** (20%) - Flesch-Kincaid scoring (with textstat fallback)
2. **Tone Consistency** (20%) - Claude API analysis for tone matching
3. **Structure/Parallelism** (25%) - Bullet point grammatical structure
4. **Redundancy** (15%) - Duplicate concept detection across slides
5. **Citations** (20%) - Citation completeness for all claims

#### 3. Graphics Validation

Validate graphics descriptions before image generation:

**From Python:**
```python
from plugin.lib.graphics_validator import GraphicsValidator

validator = GraphicsValidator()

result = validator.validate_description(
    description=graphics_description,
    slide_context={"title": slide_title, "bullets": bullets},
    style_config={"brand_colors": ["#DD0033", "#004F71"]}
)

# result contains:
# - passed: bool (threshold: 75/100)
# - score: float (0-100)
# - issues: List[Dict] (validation problems)
# - suggestions: List[str] (improvements)
# - description_improved: Optional[str] (AI-improved version)
```

**Validation Rules:**
1. **Length** - Minimum 2-4 sentences for adequate detail
2. **Specificity** - Concrete visual elements vs vague concepts
3. **Visual Elements** - Specific shapes, colors, composition
4. **Layout Hints** - Composition guidance (centered, split-screen, etc.)
5. **Text Avoidance** - No text/labels in images (added in PowerPoint)
6. **Brand Alignment** - References brand colors from style config

**Hybrid Validation:**
- Rule-based checks for fast validation
- Claude API for improvement suggestions when validation fails

### Testing Content Development

**Integration Test:**
```bash
python test_content_development.py
```

**What It Tests:**
1. ContentDraftingSkill - Generate slide content from outline
2. GraphicsValidator - Validate graphics descriptions
3. QualityAnalyzer - Comprehensive quality metrics
4. ContentOptimizationSkill - Quality improvement workflow

**Test Data:** Rochester 2GC carburetor rebuild (3 slides)

### Plugin CLI Commands

**Full Workflow:**
```bash
# Complete 11-step workflow from topic to PowerPoint
python -m plugin.cli full-workflow "Topic" --template cfa
```

**Individual Skills:**
```bash
# 1. Research Assistant (interactive)
python -m plugin.cli research-assistant "Topic"

# 2. Web Research (autonomous)
python -m plugin.cli research "Topic" --depth comprehensive

# 3. Extract Insights
python -m plugin.cli extract-insights research.json

# 4. Generate Outline
python -m plugin.cli outline research.json --audience "DIY mechanics"

# 5. Draft Content
python -m plugin.cli draft-content outline.md

# 6. Optimize Content
python -m plugin.cli optimize-content draft.md

# 7. Validate Graphics
python -m plugin.cli validate-graphics draft.md

# 8. Generate Images
python -m plugin.cli generate-images presentation.md

# 9. Build PowerPoint
python -m plugin.cli build-presentation presentation.md --template cfa
```

**Workflow Flexibility:**
- Start at ANY step (have research? Start at outline)
- Resume from existing artifacts (research.json, outline.md, etc.)
- Run skills standalone without full workflow
- Manual edits to intermediate files fully supported

### Dependencies

**Core APIs:**
- `anthropic>=0.39.0` - Claude API and Agent SDK
- `google-genai` - Gemini image generation

**Content Analysis:**
- `textstat` - Readability metrics (Flesch-Kincaid)
- Optional - has fallback approximations if unavailable

**Existing:**
- `python-pptx` - PowerPoint generation
- `python-dotenv` - Environment variables
- `python-frontmatter` - Configuration parsing

### Environment Setup

**API Keys Required:**
```bash
# .env file
ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_API_KEY=your-gemini-api-key
```

**Get Keys:**
- Claude: https://console.anthropic.com/
- Gemini: https://aistudio.google.com/app/apikey

**See [SETUP_APIS.md](SETUP_APIS.md) for detailed setup.**

### Development Tips

**Adding New Skills:**
1. Extend `BaseSkill` in `plugin/base_skill.py`
2. Implement required properties: `skill_id`, `display_name`, `description`
3. Implement required methods: `validate_input()`, `execute()`
4. Register in `plugin/skill_registry.py`
5. Add CLI command in `plugin/cli.py`
6. Write unit tests in `tests/`

**Content Generator Usage:**
```python
from plugin.lib.content_generator import ContentGenerator

generator = ContentGenerator(style_guide={
    "tone": "professional",
    "max_bullets_per_slide": 5,
    "max_words_per_bullet": 15
})

# Generate individual components
title = generator.generate_title(slide, research_context)
bullets = generator.generate_bullets(slide, research_context)
notes = generator.generate_speaker_notes(slide, title, bullets)
graphics = generator.generate_graphics_description(slide, title, bullets, style_config)

# Or generate all at once
slide_content = generator.generate_slide_content(
    slide=outline_slide,
    slide_number=1,
    research_context=research_data,
    style_config=brand_style
)
```

**Quality Analysis:**
```python
from plugin.lib.quality_analyzer import QualityAnalyzer

analyzer = QualityAnalyzer()
analysis = analyzer.analyze_presentation(slides, style_guide)

# Returns:
# - overall_score: 0-100
# - readability_score, tone_consistency_score, structure_score, etc.
# - issues: List of problems found
# - recommendations: List of actionable suggestions
```

### File Conventions

**Generated Files:**
- `research.json` - Research results with sources and citations
- `outline.md` - Presentation outline(s) in markdown
- `presentation.md` - Complete slide content following pres-template.md
- `optimized.md` - Quality-improved presentation
- `slide-{N}.jpg` - Generated slide images
- `final.pptx` - Assembled PowerPoint presentation

**Multiple Presentations:**
- `presentation-{audience}.md` - One file per detected audience
- E.g., `presentation-executive.md`, `presentation-technical.md`

### Documentation References

**Plugin System:**
- [PLUGIN_IMPLEMENTATION_PLAN.md](PLUGIN_IMPLEMENTATION_PLAN.md) - Complete implementation plan
- [PLUGIN_TEST_PLAN.md](PLUGIN_TEST_PLAN.md) - Testing strategy
- [plugin/README.md](plugin/README.md) - Plugin usage guide

**APIs:**
- [API_ARCHITECTURE.md](API_ARCHITECTURE.md) - System architecture
- [CLAUDE_AGENT_SDK.md](CLAUDE_AGENT_SDK.md) - Agent SDK guide
- [SETUP_APIS.md](SETUP_APIS.md) - API setup instructions

**Original Presentation Skill:**
- [presentation-skill/SKILL.md](presentation-skill/SKILL.md) - PowerPoint generation
- [presentation-skill/CLI_USAGE.md](presentation-skill/CLI_USAGE.md) - CLI reference
