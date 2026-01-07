# Project Structure

**Version:** 2.0.0
**Updated:** January 4, 2026

```
slide-generator/
├── .git/                                  # Git repository
├── .gitignore                             # Git ignore rules
├── README.md                              # Main project documentation
├── CLAUDE.md                              # Claude Code instructions
├── PROJECT_STRUCTURE.md                   # This file
├── requirements.txt                       # Python dependencies
├── .env.example                           # API key template
│
├── plugin/                                # PLUGIN SYSTEM (v2.0) - NEW
│   ├── __init__.py
│   ├── base_skill.py                     # Base skill interface
│   ├── skill_registry.py                 # Skill discovery and management
│   ├── workflow_orchestrator.py          # Multi-skill workflow execution
│   ├── checkpoint_handler.py             # User interaction checkpoints
│   ├── config_manager.py                 # Configuration management
│   ├── cli.py                            # Command-line interface
│   ├── README.md                         # Plugin usage guide
│   │
│   ├── commands/                         # CLI command implementations
│   │   ├── __init__.py
│   │   ├── research.py
│   │   ├── outline.py
│   │   ├── draft.py
│   │   ├── generate_images.py
│   │   └── build.py
│   │
│   ├── skills/                           # Individual skills
│   │   ├── __init__.py
│   │   ├── research_assistant_skill.py   # Interactive research refinement
│   │   ├── research_skill.py             # Autonomous web research
│   │   ├── insight_extraction_skill.py   # AI insight analysis
│   │   ├── outline_skill.py              # Presentation outline generation
│   │   ├── content_drafting_skill.py     # AI content generation
│   │   ├── content_optimization_skill.py # Quality improvement
│   │   ├── validation_skill.py           # Visual validation (experimental)
│   │   └── refinement_skill.py           # Image refinement
│   │
│   └── lib/                              # Core libraries
│       ├── __init__.py
│       ├── claude_client.py              # Claude API client (plain API)
│       ├── claude_agent.py               # Claude Agent SDK integration
│       ├── content_generator.py          # AI content generation
│       ├── quality_analyzer.py           # Content quality metrics
│       ├── graphics_validator.py         # Graphics description validation
│       ├── citation_manager.py           # Citation management (APA, MLA, Chicago)
│       ├── web_search.py                 # Web search abstraction
│       └── content_extractor.py          # HTML content extraction
│
├── presentation-skill/                   # POWERPOINT GENERATION (v1.2)
│   ├── generate_presentation.py          # Main entry point
│   ├── lib/                              # Core libraries
│   │   ├── __init__.py
│   │   ├── parser.py                     # Enhanced markdown parser
│   │   ├── type_classifier.py            # Intelligent slide classification
│   │   ├── assembler.py                  # Presentation builder
│   │   ├── image_generator.py            # AI image generation
│   │   ├── visual_validator.py           # Gemini vision validation
│   │   ├── refinement_engine.py          # Feedback-driven refinement
│   │   └── slide_exporter.py             # PowerShell COM export (Windows)
│   └── templates/                        # Presentation templates
│       ├── __init__.py
│       ├── cfa.py                        # CFA branded template
│       └── stratfield.py                 # Stratfield branded template
│
├── lib/                                  # SHARED LIBRARIES
│   ├── __init__.py
│   ├── config_loader.py                  # Unified configuration
│   ├── gemini_client.py                  # Gemini API client
│   └── image_prompt_builder.py           # Prompt generation for images
│
├── templates/                            # TEMPLATE EXAMPLES
│   ├── pres-template.md                  # Presentation markdown template
│   ├── example-presentation.md           # Example presentation (20 slides)
│   ├── cfa_style.json                    # CFA brand style config
│   └── stratfield_style.json             # Stratfield brand style config
│
├── docs/                                 # DOCUMENTATION (Reference Materials)
│   ├── cfa_vis_identity.pdf              # CFA brand guidelines
│   └── flow.pdf                          # Workflow diagrams
│
├── tests/                                # TEST SUITE
│   ├── __init__.py
│   ├── conftest.py                       # Pytest configuration
│   ├── test_base_skill.py                # Base skill tests
│   ├── test_skill_registry.py            # Registry tests
│   ├── test_research_skill.py            # Research skill tests
│   ├── test_insight_extraction.py        # Insight extraction tests
│   ├── test_outline_skill.py             # Outline generation tests
│   ├── test_citation_manager.py          # Citation management tests
│   ├── test_web_search.py                # Web search tests
│   ├── test_content_extractor.py         # Content extraction tests
│   ├── fixtures/                         # Test fixtures
│   │   ├── README.md
│   │   └── sample_research.json
│   └── testfiles/                        # Test data
│       └── presentation.md               # 20-slide test file
│
├── test_carburetor_research.py           # Integration test (PRIORITY 2)
├── test_content_development.py           # Integration test (PRIORITY 3)
│
├── scripts/                              # UTILITY SCRIPTS
│   └── README.md                         # Script documentation
│
├── dist/                                 # DISTRIBUTION FILES
│   └── README.md                         # Distribution guide
│
├── generate_prompts.py                   # Standalone prompt generator
├── generate_images.py                    # Standalone image generator
├── generate_presentation.py              # Standalone PowerPoint builder
├── prompt_config.md                      # Unified configuration file
│
└── DOCUMENTATION FILES (Root)            # Planning and guides
    ├── API_ARCHITECTURE.md               # System architecture
    ├── CLAUDE_AGENT_SDK.md               # Agent SDK usage guide
    ├── CONTRIBUTING.md                   # Contribution guidelines
    ├── PLUGIN_IMPLEMENTATION_PLAN.md     # Complete implementation plan
    ├── PLUGIN_TEST_PLAN.md               # Testing strategy
    ├── SECURITY.md                       # Security best practices
    └── SETUP_APIS.md                     # API setup instructions
```

## Key Directories

### `plugin/` (Plugin System - v2.0)
**NEW:** Complete AI-assisted presentation generation plugin system.

**Core Infrastructure:**
- `base_skill.py` - Base skill interface (SkillInput, SkillOutput)
- `skill_registry.py` - Skill discovery and dependency resolution
- `workflow_orchestrator.py` - Multi-skill workflow execution with checkpoints
- `checkpoint_handler.py` - User interaction for approvals
- `config_manager.py` - Multi-source configuration with validation
- `cli.py` - Command-line interface

**Skills (`plugin/skills/`):**
- Research Assistant - Interactive scope refinement
- Research - Autonomous web research (Claude Agent SDK)
- Insight Extraction - AI-powered analysis
- Outline Generation - Multi-presentation detection
- Content Drafting - AI-generated slide content
- Content Optimization - Quality improvement
- Validation - Visual quality verification (experimental)
- Refinement - Iterative image improvement

**Libraries (`plugin/lib/`):**
- `claude_client.py` - Claude API client (plain API for simple operations)
- `claude_agent.py` - Claude Agent SDK (autonomous workflows with tool use)
- `content_generator.py` - AI content generation (titles, bullets, notes, graphics)
- `quality_analyzer.py` - 5-dimension quality metrics
- `graphics_validator.py` - Graphics description validation
- `citation_manager.py` - Citation management (APA, MLA, Chicago)
- `web_search.py` - Web search abstraction (mock for dev, real for prod)
- `content_extractor.py` - HTML content extraction and summarization

### `presentation-skill/` (PowerPoint Generation - v1.2)
Original presentation generation system, now integrated with plugin workflow.

**Core Files:**
- `generate_presentation.py` - Main CLI tool
- `lib/parser.py` - Enhanced markdown parser
- `lib/type_classifier.py` - Intelligent slide classification (hybrid AI + rules)
- `lib/assembler.py` - Presentation builder with workflow orchestration
- `lib/image_generator.py` - Gemini Pro image generation
- `lib/visual_validator.py` - Gemini vision-based validation (experimental)
- `lib/refinement_engine.py` - Pattern-based image refinement
- `lib/slide_exporter.py` - PowerShell COM export for Windows

**Templates:**
- `templates/cfa.py` - Chick-fil-A branded PowerPoint template
- `templates/stratfield.py` - Stratfield consulting template

### `lib/` (Shared Libraries)
Common utilities used by both plugin and presentation-skill.

- `config_loader.py` - Unified configuration from multiple sources
- `gemini_client.py` - Gemini API client for image generation
- `image_prompt_builder.py` - Prompt generation for image API

### `templates/` (Template Examples)
Markdown templates and examples for presentations.

- `pres-template.md` - Comprehensive slide definition template
- `example-presentation.md` - Example 20-slide presentation
- `cfa_style.json` - CFA brand colors and style config
- `stratfield_style.json` - Stratfield brand config

### `tests/` (Test Suite)
Comprehensive test coverage for all plugin components.

**Test Coverage:**
- PRIORITY 1 (Plugin Infrastructure): Base classes, registry, orchestration
- PRIORITY 2 (Research & Discovery): 74 tests, 92-96% coverage
- PRIORITY 3 (Content Development): Integration tests for drafting and optimization

**Integration Tests:**
- `test_carburetor_research.py` - Full research workflow (4 phases)
- `test_content_development.py` - Full content development workflow

### `docs/` (Documentation)
Reference materials and technical documentation.

- `cfa_vis_identity.pdf` - CFA brand guidelines
- `flow.pdf` - Workflow diagrams

### `dist/` (Distribution)
Distribution packages (ZIP files ignored in git).

### `scripts/` (Utility Scripts)
Additional utility scripts for development.

## File Conventions

### Generated Files (Not in Git)
- `research.json` - Research results with sources and citations
- `outline.md` - Presentation outline(s)
- `presentation.md` - Complete slide content
- `optimized.md` - Quality-improved presentation
- `slide-{N}.jpg` - Generated slide images
- `*.pptx` - Final PowerPoint presentations

### Configuration Files
- `.env` - API keys (NEVER commit!)
- `.env.example` - Template for API keys
- `prompt_config.md` - Unified configuration with YAML frontmatter
- `templates/*_style.json` - Brand-specific style configurations

## Documentation Structure

### User Guides
- `README.md` - Main project overview and quick start
- `CLAUDE.md` - Complete guide for Claude Code (project instructions)
- `SETUP_APIS.md` - Step-by-step API setup
- `CLAUDE_AGENT_SDK.md` - Agent SDK usage and examples

### Architecture & Planning
- `API_ARCHITECTURE.md` - System architecture and API integration
- `PLUGIN_IMPLEMENTATION_PLAN.md` - Complete implementation plan (3 priorities)
- `PLUGIN_TEST_PLAN.md` - Testing strategy and test data
- `PROJECT_STRUCTURE.md` - This file (project organization)

### Development
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security best practices and API key protection

### Component-Specific
- `plugin/README.md` - Plugin usage guide
- `presentation-skill/templates/` - Brand template implementations

## Technology Stack

### AI & APIs
- **Claude Sonnet 4.5** (Anthropic) - Text generation, research, analysis, optimization
- **Claude Agent SDK** - Autonomous workflows with tool use
- **Gemini Pro** (Google) - Image generation (gemini-3-pro-image-preview)
- **textstat** - Readability metrics (Flesch-Kincaid)

### Python Libraries
- **python-pptx** - PowerPoint generation
- **anthropic** - Claude API client
- **google-genai** - Gemini API client
- **python-dotenv** - Environment variable management
- **python-frontmatter** - Configuration parsing (YAML frontmatter)
- **Pillow** - Image processing
- **pytest** - Testing framework

## Workflow Overview

### 11-Step AI-Assisted Workflow

1. **Research Assistant** - Interactive clarifying questions
2. **Web Research** - Autonomous research (Claude Agent SDK with tool use)
3. **Insight Extraction** - AI-powered analysis of sources
4. **Outline Generation** - Multi-presentation detection
5. **Content Drafting** - AI-generated titles, bullets, speaker notes, graphics
6. **Quality Optimization** - Automated quality improvement
7. **Graphics Validation** - Ensure descriptions are specific enough
8. **Image Generation** - Gemini Pro AI image generation
9. **Visual Validation** - Quality verification (experimental)
10. **Refinement** - Iterative image improvement
11. **PowerPoint Assembly** - Final presentation building

### Entry Point Flexibility

**Start at ANY step:**
- Have research? → Start at outline
- Have outline? → Start at content drafting
- Have content? → Start at image generation
- Have images? → Start at PowerPoint assembly

**Resume from existing artifacts:**
- `research.json` → Outline generation
- `outline.md` → Content drafting
- `presentation.md` → Image generation or optimization
- Manual edits to any file fully supported

## Version History

- **v2.0.0** (Jan 4, 2026) - Plugin system with research, content development, AI assistance
  - PRIORITY 1: Plugin Infrastructure (30+ files, 8,000+ lines)
  - PRIORITY 2: Research & Discovery Tools (10 files, 3,500+ lines, 74 tests)
  - PRIORITY 3: Content Development Tools (6 files, 2,500+ lines)

- **v1.2.0** (Jan 3, 2026) - Intelligent classification and visual validation
  - Hybrid AI + rule-based slide type detection
  - Gemini vision-based validation (experimental)
  - Iterative refinement with pattern detection

- **v1.1.0** (Dec 2024) - Enhanced parsing and multi-resolution support
  - Enhanced markdown parser
  - Multi-resolution prompt generation
  - Unified configuration system

- **v1.0.0** (Dec 2024) - Initial release
  - Basic PowerPoint generation
  - Gemini image generation
  - Brand templates (CFA, Stratfield)

## Quick Navigation

**Getting Started:**
- Installation: See `README.md` → Quick Start
- API Setup: See `SETUP_APIS.md`
- First Presentation: See `README.md` → Usage

**Development:**
- Architecture: See `API_ARCHITECTURE.md`
- Implementation Plan: See `PLUGIN_IMPLEMENTATION_PLAN.md`
- Testing: See `PLUGIN_TEST_PLAN.md`
- Contributing: See `CONTRIBUTING.md`

**Usage Guides:**
- CLI Commands: See `plugin/README.md` or `README.md` → Usage
- Agent SDK: See `CLAUDE_AGENT_SDK.md`
- PowerPoint Generation: See `presentation-skill/SKILL.md`
- Configuration: See `prompt_config.md`
