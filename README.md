# AI-Assisted Presentation Generator

[![CI](https://github.com/davistroy/slide-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/davistroy/slide-generator/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Version:** 2.0.0 (Plugin System with Content Development)
**Status:** Production Ready ✅
**Updated:** January 4, 2026

A comprehensive Claude Code plugin system for AI-assisted presentation generation, from research through final PowerPoint assembly. Features autonomous research, intelligent content drafting, quality optimization, AI image generation, and brand-specific templates.

## Overview

This project provides a complete **11-step workflow** for creating professional presentations with AI assistance:

1. **Research** - Autonomous web research with Claude Agent SDK
2. **Insight Extraction** - AI-powered analysis of research sources
3. **Outline Generation** - Multi-presentation detection and structuring
4. **Content Drafting** - AI-generated titles, bullets, speaker notes, graphics descriptions
5. **Quality Optimization** - Automated quality analysis and improvement
6. **Graphics Validation** - Ensure descriptions are specific enough for image generation
7. **Image Generation** - AI-generated slide visuals (Gemini Pro)
8. **Visual Validation** - Optional quality verification (experimental)
9. **Refinement** - Iterative image improvement
10. **PowerPoint Assembly** - Programmatic presentation building
11. **Final Output** - Brand-specific .pptx files

Perfect for creating consistent, research-backed, professional presentations at scale with full AI assistance.

## ✨ What's New in v2.0.0

**🔌 Plugin Architecture (PRIORITY 1):**
- ✅ Modular skill-based system with registry and orchestration
- ✅ Base skill interface with standardized input/output
- ✅ Workflow orchestrator with checkpoint system
- ✅ CLI interface with 11 commands
- ✅ Configuration management (multi-source with validation)
- ✅ Start workflow at ANY step, resume from existing artifacts
- ✅ 30+ files, 8,000+ lines of infrastructure code

**🔍 Research & Discovery Tools (PRIORITY 2):**
- ✅ **Claude Agent SDK integration** - Autonomous multi-step research with tool use
- ✅ **Web search & content extraction** - Automatic source gathering and citation management
- ✅ **Insight extraction** - AI-powered analysis of research sources
- ✅ **Outline generation** - Multi-presentation detection for different audiences
- ✅ **Interactive research assistant** - Clarifying questions to refine scope
- ✅ 10 files, 3,500+ lines of research code
- ✅ 74 comprehensive unit tests with 92-96% coverage

**✍️ Content Development Tools (PRIORITY 3):**
- ✅ **AI-assisted content drafting** - Generate titles, bullets, speaker notes, graphics
- ✅ **Quality analysis** - 5-dimension scoring (readability, tone, structure, redundancy, citations)
- ✅ **Content optimization** - Automated quality improvement with before/after tracking
- ✅ **Graphics validation** - Rule-based + AI validation of image descriptions
- ✅ Hybrid approach: Claude API + textstat for comprehensive quality metrics
- ✅ 6 files, 2,500+ lines of content generation code

**🤖 AI Technology Stack:**
- **Claude Sonnet 4.5** - All text generation, research, analysis, optimization
- **Claude Agent SDK** - Autonomous research workflows with tool use
- **Gemini Pro** - Image generation only (gemini-3-pro-image-preview)
- **textstat** - Readability metrics (Flesch-Kincaid)

**🎯 Complete Workflow Coverage:**
```
User Topic
    ↓
Research (Claude Agent SDK) → Sources + Citations
    ↓
Insights (Claude API) → Key findings + Concepts
    ↓
Outline (Claude API) → Multi-presentation structure
    ↓
Content Drafting (Claude API) → Complete slide content
    ↓
Optimization (Claude API) → Quality-improved content
    ↓
Graphics Validation → Ready for image generation
    ↓
Image Generation (Gemini Pro) → Slide visuals
    ↓
PowerPoint Assembly → Final .pptx
```

## Features

### Research & Discovery
- 🔍 **Autonomous Research** - Claude Agent SDK conducts multi-step research with web search, content extraction, and citation management
- 🧠 **Insight Extraction** - AI-powered analysis identifies key insights, arguments, and concept relationships
- 📊 **Multi-Presentation Detection** - Automatically splits complex topics into presentations for different audiences
- 💬 **Interactive Refinement** - Clarifying questions to refine research scope and direction

### Content Development
- ✍️ **AI Content Drafting** - Generate engaging titles, parallel-structured bullets, and full speaker notes
- 📈 **Quality Analysis** - Comprehensive scoring across readability, tone, structure, redundancy, and citations
- ⚡ **Automatic Optimization** - Claude API improves content quality with detailed improvement tracking
- 🎨 **Graphics Description** - Detailed visual instructions validated for image generation quality

### Visual Assets
- 🎨 **AI Image Generation** - Batch generate slide images using Google Gemini Pro with style consistency
- 🧠 **Intelligent Classification** - Automatically determines optimal slide type using AI + rules
- 🔍 **Visual Validation** - Optional Gemini vision-based quality validation with iterative refinement (experimental)

### Presentation Building
- 🎯 **Brand Templates** - Pre-built PowerPoint builders for CFA and Stratfield branded presentations
- 🔧 **Programmatic Control** - Full python-pptx integration for precise layout and styling
- 📊 **Multiple Content Types** - Tables, bullets, numbered lists, code blocks, and mixed content
- 🌐 **Cross-Platform** - Works on Windows, macOS, and Linux

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI / API                                │
│                    (plugin/cli.py)                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator                         │
│              (plugin/workflow_orchestrator.py)                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Research    │   │   Content     │   │  PowerPoint   │
│    Skills     │   │    Skills     │   │    Skills     │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ • Research    │   │ • Drafting    │   │ • Parsing     │
│ • Insights    │   │ • Optimization│   │ • Assembly    │
│ • Outline     │   │ • Validation  │   │ • Images      │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        └─────────────────┬─┴───────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Core Libraries                             │
│                      (plugin/lib/)                               │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  API Clients    │    Utilities    │      Presentation           │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ • Claude        │ • Validators    │ • Parser                    │
│ • Gemini        │ • Retry         │ • Assembler                 │
│ • Async clients │ • Rate Limiter  │ • Templates                 │
│ • Conn. Pool    │ • Logging       │ • Type Classifier           │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **CLI** | `plugin/cli.py` | Command-line interface with 11+ commands |
| **Skills** | `plugin/skills/` | Modular task implementations |
| **Libraries** | `plugin/lib/` | Shared utilities and API clients |
| **Templates** | `plugin/templates/` | Brand templates (CFA, Stratfield) |
| **Types** | `plugin/types.py` | Centralized type definitions |

### Data Flow

1. **Research Phase**: Topic → Web research → Insights → Outline
2. **Content Phase**: Outline → Draft slides → Optimize → Validate graphics
3. **Assembly Phase**: Content → Generate images → Build PowerPoint

## Quick Start

### Installation

**1. Clone Repository:**
```bash
git clone https://github.com/davistroy/slide-generator.git
cd slide-generator
```

**2. Install Dependencies:**
```bash
pip install -r requirements.txt
```

**3. Set Up API Keys:**
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys:
# ANTHROPIC_API_KEY=your-claude-api-key
# GOOGLE_API_KEY=your-gemini-api-key
```

Get API keys from:
- **Claude:** https://console.anthropic.com/
- **Gemini:** https://aistudio.google.com/app/apikey

See [SETUP_APIS.md](SETUP_APIS.md) for detailed setup instructions.

### ⚠️ Security Warning: Protect Your API Keys

**CRITICAL:** Never commit your `.env` file or share it publicly!
- The `.env` file contains your API keys
- Exposing keys can lead to unauthorized usage and costs
- Always keep `.env` in `.gitignore`
- If you accidentally expose a key, revoke it immediately

## Usage

### Full AI-Assisted Workflow

Generate a complete presentation from a topic:

```bash
# Full workflow with all 11 steps
python -m plugin.cli full-workflow "Rochester 2GC Carburetor Rebuild" --template cfa

# With custom parameters
python -m plugin.cli full-workflow "AI in Healthcare" \
  --template stratfield \
  --audience "executives" \
  --duration 30 \
  --enable-validation
```

### Individual Skills

Run specific parts of the workflow:

```bash
# 1. Research a topic
python -m plugin.cli research "AI in Healthcare" --output research.json

# 2. Generate outline from research
python -m plugin.cli outline research.json --output outline.md

# 3. Draft content from outline
python -m plugin.cli draft-content outline.md --output presentation.md

# 4. Optimize content quality
python -m plugin.cli optimize-content presentation.md --output optimized.md

# 5. Generate images
python -m plugin.cli generate-images presentation.md --resolution high

# 6. Build PowerPoint
python -m plugin.cli build-presentation presentation.md --template cfa
```

### Using Existing Content

Start from manually created content:

```bash
# Generate images from existing markdown
python generate_images.py --resolution high

# Build PowerPoint from existing content
python generate_presentation.py presentation.md --template cfa
```

## Project Structure

```
slide-generator/
├── plugin/                          # Plugin system (v2.0)
│   ├── base_skill.py               # Base skill interface
│   ├── skill_registry.py           # Skill discovery and management
│   ├── workflow_orchestrator.py    # Multi-skill workflow execution
│   ├── checkpoint_handler.py       # User interaction checkpoints
│   ├── config_manager.py           # Configuration management
│   ├── cli.py                      # Command-line interface
│   ├── skills/                     # Individual skills
│   │   ├── research_skill.py       # Autonomous web research
│   │   ├── insight_extraction_skill.py
│   │   ├── outline_skill.py
│   │   ├── content_drafting_skill.py
│   │   ├── content_optimization_skill.py
│   │   └── ...
│   └── lib/                        # Core libraries
│       ├── claude_client.py        # Claude API client
│       ├── claude_agent.py         # Agent SDK integration
│       ├── content_generator.py    # AI content generation
│       ├── quality_analyzer.py     # Quality metrics
│       ├── graphics_validator.py   # Graphics validation
│       ├── citation_manager.py     # Citation management
│       └── ...
├── presentation-skill/             # PowerPoint generation (v1.2)
│   ├── lib/
│   │   ├── parser.py               # Markdown parsing
│   │   ├── type_classifier.py      # Slide type detection
│   │   ├── image_generator.py      # Gemini image generation
│   │   ├── assembler.py            # PowerPoint assembly
│   │   └── ...
│   └── templates/
│       ├── cfa.py                  # Chick-fil-A template
│       └── stratfield.py           # Stratfield template
├── lib/
│   ├── config_loader.py            # Unified configuration
│   ├── gemini_client.py            # Gemini API client
│   └── image_prompt_builder.py    # Prompt generation
├── templates/
│   ├── pres-template.md            # Slide definition template
│   ├── example-presentation.md     # Example content
│   └── cfa_style.json              # Brand style configs
├── tests/                          # Comprehensive test suite
├── generate_prompts.py             # Standalone prompt generator
├── generate_images.py              # Standalone image generator
├── generate_presentation.py        # Standalone PowerPoint builder
└── prompt_config.md                # Unified configuration file
```

## Documentation

### User Guides
- **[CLAUDE.md](CLAUDE.md)** - Complete guide for Claude Code (project instructions)
- **[SETUP_APIS.md](SETUP_APIS.md)** - Step-by-step API setup
- **[CLAUDE_AGENT_SDK.md](CLAUDE_AGENT_SDK.md)** - Agent SDK usage guide
- **[prompt_config.md](prompt_config.md)** - Configuration reference

### Architecture & Planning
- **[API_ARCHITECTURE.md](API_ARCHITECTURE.md)** - System architecture and API integration
- **[PLUGIN_IMPLEMENTATION_PLAN.md](PLUGIN_IMPLEMENTATION_PLAN.md)** - Complete implementation plan
- **[PLUGIN_TEST_PLAN.md](PLUGIN_TEST_PLAN.md)** - Testing strategy
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed project structure

### Development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[SECURITY.md](SECURITY.md)** - Security best practices

## Testing

The project includes comprehensive test coverage:

**PRIORITY 2 (Research & Discovery):**
- 74 unit tests
- 92-96% coverage across all components
- Integration test: `test_carburetor_research.py`

**PRIORITY 3 (Content Development):**
- Integration test: `test_content_development.py`
- Quality analysis validation
- Graphics description validation

Run tests:
```bash
# Run all plugin tests
pytest tests/

# Run specific integration test
python test_carburetor_research.py
python test_content_development.py

# Run with coverage
pytest tests/ --cov=plugin --cov-report=html
```

## Technology Stack

**AI & APIs:**
- **Claude Sonnet 4.5** (Anthropic) - Text generation, research, analysis, optimization
- **Claude Agent SDK** - Autonomous workflows with tool use
- **Gemini Pro** (Google) - Image generation (gemini-3-pro-image-preview)
- **textstat** - Readability metrics

**Python Libraries:**
- **python-pptx** - PowerPoint generation
- **anthropic** - Claude API client
- **google-genai** - Gemini API client
- **python-dotenv** - Environment variable management
- **python-frontmatter** - Configuration parsing
- **Pillow** - Image processing
- **pytest** - Testing framework

## Workflow Flexibility

The plugin system is designed for **maximum flexibility**:

**Entry Points:** Start at ANY of the 11 workflow steps:
- Have research? Start at outline generation
- Have an outline? Start at content drafting
- Have content? Start at image generation
- Have everything? Just build the PowerPoint

**Resumption:** Resume from existing artifacts:
```bash
# Resume from saved research
python -m plugin.cli outline existing_research.json

# Resume from manually edited outline
python -m plugin.cli draft-content my_outline.md

# Resume from edited content
python -m plugin.cli generate-images edited_presentation.md
```

**Checkpoints:** User review between phases:
- After research (approve sources)
- After outline (approve structure)
- After drafting (approve content)
- After images (approve visuals)

## Examples

**Research Workflow:**
```bash
# 1. Start with interactive research assistant
python -m plugin.cli research-assistant "Rochester 2GC Carburetor"
# → Asks clarifying questions about audience, depth, focus

# 2. Conduct autonomous research
python -m plugin.cli research "Rochester 2GC rebuild process" \
  --depth comprehensive \
  --max-sources 20

# 3. Extract insights
python -m plugin.cli extract-insights research.json \
  --focus "rebuild process, tool requirements"

# 4. Generate outline
python -m plugin.cli outline research.json --audience "DIY mechanics"
```

**Content Development:**
```bash
# 1. Draft content from outline
python -m plugin.cli draft-content outline.md \
  --style-guide "conversational, technical" \
  --max-bullets 5

# 2. Analyze quality
python -m plugin.cli analyze-quality draft.md
# → Reports readability, tone, structure, redundancy, citations

# 3. Optimize content
python -m plugin.cli optimize-content draft.md \
  --goals "readability, parallelism, citations"
# → Outputs improved content with before/after scores
```

## Version History

- **v2.0.0** (Jan 4, 2026) - Plugin system with research, content development, and AI assistance
- **v1.2.0** (Jan 3, 2026) - Intelligent classification and visual validation
- **v1.1.0** (Dec 2024) - Enhanced parsing and multi-resolution support
- **v1.0.0** (Dec 2024) - Initial release with basic generation

See [PLUGIN_IMPLEMENTATION_PLAN.md](PLUGIN_IMPLEMENTATION_PLAN.md) for complete development history.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

See [SECURITY.md](SECURITY.md) for security best practices and API key protection.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- See documentation in [CLAUDE.md](CLAUDE.md)
- Review [SETUP_APIS.md](SETUP_APIS.md) for API setup help

---

**Built with Claude Code** 🤖

*AI-assisted presentation generation from research to final PowerPoint*
