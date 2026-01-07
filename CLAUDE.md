# CLAUDE.md

**Version:** 2.0.0 (Plugin System with Content Development)

This file provides guidance to Claude Code when working with this AI-assisted presentation generation system.

## Project Overview

**11-step AI-assisted workflow** from research to final PowerPoint:
1. Research Assistant → Interactive scope refinement
2. Web Research → Autonomous research (Claude Agent SDK)
3. Insight Extraction → AI analysis
4. Outline Generation → Multi-presentation detection
5. Content Drafting → AI-generated slides
6. Quality Optimization → Automated improvement
7. Graphics Validation → Image description quality
8. Image Generation → Gemini Pro visuals
9. Visual Validation → Quality verification (experimental)
10. Refinement → Iterative improvement
11. PowerPoint Assembly → Final .pptx

**Technology Stack:**
- **Claude Sonnet 4.5** - All text operations (research, content, analysis)
- **Claude Agent SDK** - Autonomous workflows with tool use
- **Gemini Pro** - Image generation ONLY (gemini-3-pro-image-preview)
- **textstat** - Readability metrics (optional, has fallbacks)

## Architecture

### Project Structure
```
slide-generator/
├── plugin/                    # Plugin system (v2.0) - NEW
│   ├── base_skill.py          # Skill interface
│   ├── skill_registry.py      # Skill management
│   ├── workflow_orchestrator.py
│   ├── cli.py                 # CLI entry point
│   ├── skills/                # Individual skills
│   │   ├── research_skill.py  # Claude Agent SDK
│   │   ├── content_drafting_skill.py
│   │   ├── content_optimization_skill.py
│   │   └── ...
│   └── lib/                   # Core libraries
│       ├── claude_client.py   # Plain API
│       ├── claude_agent.py    # Agent SDK
│       ├── content_generator.py
│       ├── quality_analyzer.py
│       ├── graphics_validator.py
│       └── ...
├── presentation-skill/        # PowerPoint generation (v1.2)
│   ├── lib/
│   │   ├── parser.py          # Markdown parsing
│   │   ├── type_classifier.py # Slide type detection
│   │   ├── assembler.py       # PowerPoint building
│   │   └── ...
│   └── templates/
│       ├── cfa.py             # Brand templates
│       └── stratfield.py
├── lib/                       # Shared utilities
├── templates/                 # Markdown templates
│   ├── pres-template.md       # Slide definition format
│   └── *_style.json           # Brand configs
├── tests/                     # Test suite
└── *.py                       # Standalone scripts
```

### Key Patterns

**Skill Interface:**
- All skills extend `BaseSkill` (SkillInput → SkillOutput)
- Implement: `skill_id`, `display_name`, `description`, `validate_input()`, `execute()`
- Register in `plugin/skill_registry.py`

**API Usage:**
- **Plain API** - Simple single-turn operations (insights, outlines, optimization)
- **Agent SDK** - Multi-step workflows with tool use (research)
- **Gemini** - Image generation only, NOT for text

**Slide Definition Format** (`pres-template.md`):
- Markdown with structured sections per slide
- **Content:** Bullets, tables, code blocks
- **Graphics:** Detailed visual descriptions for AI generation
- **Speaker Notes:** Full narration with [stage directions]
- **Background:** Citations, rationale, Q&A prep

## CLI Usage

**Full Workflow:**
```bash
python -m plugin.cli full-workflow "Topic" --template cfa
```

**Individual Skills:**
```bash
# Research workflow
python -m plugin.cli research "Topic" --output research.json
python -m plugin.cli outline research.json --output outline.md

# Content development
python -m plugin.cli draft-content outline.md --output presentation.md

# Image and assembly
python -m plugin.cli generate-images presentation.md --resolution high
python -m plugin.cli build-presentation presentation.md --template cfa

# Utility commands
python -m plugin.cli health-check       # Verify configuration
python -m plugin.cli list-skills        # Show available skills
python -m plugin.cli status             # Check workflow state
```

**Standalone Scripts:**
```bash
# Generate prompts and images (any resolution: high/medium/small)
python generate_prompts.py --resolution high
python generate_images.py --resolution high

# Build PowerPoint with optional validation (Windows only)
python generate_presentation.py presentation.md --template cfa
python generate_presentation.py presentation.md --enable-validation  # Experimental
```

## Development Guidelines

### Adding New Skills
1. Extend `BaseSkill` in `plugin/base_skill.py`
2. Implement required interface (skill_id, execute, validate_input)
3. Register in `plugin/skill_registry.py`
4. Add CLI command in `plugin/cli.py`
5. Write tests in `tests/`

### Content Generation
```python
from plugin.lib.content_generator import ContentGenerator

generator = ContentGenerator(style_guide={
    "tone": "professional",
    "max_bullets_per_slide": 5,
    "max_words_per_bullet": 15
})

# Generate complete slide content
slide_content = generator.generate_slide_content(
    slide=outline_slide,
    slide_number=1,
    research_context=research_data,
    style_config=brand_style
)
```

### Quality Analysis
```python
from plugin.lib.quality_analyzer import QualityAnalyzer

analyzer = QualityAnalyzer()
analysis = analyzer.analyze_presentation(slides, style_guide)
# Returns: overall_score (0-100), readability, tone, structure, redundancy, citations
```

### Graphics Validation
```python
from plugin.lib.graphics_validator import GraphicsValidator

validator = GraphicsValidator()
result = validator.validate_description(description, slide_context, style_config)
# Returns: passed (bool), score, issues, suggestions, improved_description
```

## PowerPoint Generation

### Slide Type Classification (Hybrid AI + Rules)
- **Rule-based** (~80%): Fast deterministic for obvious cases
- **AI-powered** (~20%): Gemini semantic analysis for ambiguous cases
- **5 Templates:** title, section, content, image, text_image

### Visual Validation (Experimental - Windows Only)
- Gemini vision-based quality assessment
- 5-category rubric (content, hierarchy, brand, image, layout)
- Iterative refinement (max 3 attempts)
- Requires PowerShell COM export (Windows + PowerPoint)

### Brand Templates
- **CFA:** Red (#DD0033) titles, blue (#004F71) sections, Apercu font
- **Stratfield:** Custom branded template
- Located in `presentation-skill/templates/`

## Configuration

### API Keys (Required)
```bash
# .env file (NEVER commit!)
ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_API_KEY=your-gemini-api-key
```

Get keys:
- Claude: https://console.anthropic.com/
- Gemini: https://aistudio.google.com/app/apikey

### Unified Configuration (`prompt_config.md`)
Controls prompt generation and image generation parameters:
- Resolution definitions (high/medium/small)
- Composition rules ("no titles" for small)
- Generic quality instructions
- Gemini API model and parameters
- Delays and file naming

## File Conventions

**Generated Files (gitignored):**
- `research.json` - Research results
- `outline.md` - Presentation outline(s)
- `presentation.md` - Complete slide content
- `optimized.md` - Quality-improved version
- `slide-{N}.jpg` - Generated images
- `*.pptx` - Final presentations

**Multiple Presentations:**
- Auto-detected for complex topics
- One file per audience: `presentation-{audience}.md`
- E.g., `presentation-executive.md`, `presentation-technical.md`

## Testing

```bash
# Run all plugin tests
pytest tests/

# Integration tests
python test_carburetor_research.py       # Research workflow
python test_content_development.py       # Content development

# Coverage
pytest tests/ --cov=plugin --cov-report=html
```

## Important Notes

### Security
- **NEVER commit .env files** - Contains API keys
- `.gitignore` excludes .env, but always verify
- If key exposed, revoke immediately at API console

### Workflow Flexibility
- **Start anywhere:** Have research? Start at outline. Have content? Start at images.
- **Resume from artifacts:** All intermediate files (research.json, outline.md, etc.) can be used as entry points
- **Manual edits supported:** Edit any intermediate file and continue workflow

### API Best Practices
- **Claude:** Use plain API for simple tasks, Agent SDK for complex workflows
- **Gemini:** Image generation only - NOT for text operations
- **Rate limits:** Configured delays in `prompt_config.md`
- **Cost tracking:** Monitor API usage, especially with validation enabled

### Platform-Specific Features
- **Visual validation:** Windows + PowerPoint only (graceful degradation elsewhere)
- **Slide export:** Uses PowerShell COM automation on Windows
- **Core functionality:** Cross-platform (Windows, macOS, Linux)

## Documentation References

**For detailed information, see:**
- `README.md` - Quick start and feature overview
- `PLUGIN_IMPLEMENTATION_PLAN.md` - Complete implementation details (3 priorities)
- `API_ARCHITECTURE.md` - System architecture and API integration
- `CLAUDE_AGENT_SDK.md` - Agent SDK usage guide with examples
- `SETUP_APIS.md` - Step-by-step API setup
- `PROJECT_STRUCTURE.md` - Detailed directory organization
- `prompt_config.md` - Configuration reference and customization

**Component-specific:**
- `plugin/README.md` - Plugin system usage
- `presentation-skill/templates/` - Brand template implementations

---

**This project uses Claude Code for AI-assisted presentation generation from research to final PowerPoint.**
