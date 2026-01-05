# Presentation Generator Plugin

AI-assisted presentation generation plugin for Claude Code.

**Version:** 2.0.0
**Status:** Infrastructure Complete (PRIORITY 1 ✅)

## Overview

This plugin implements a comprehensive 11-step workflow for generating professional presentations from research through final PowerPoint output, organized into 4 phases:

1. **Research & Discovery** (Steps 1-4) - 📋 Planned
2. **Content Development** (Steps 5-6) - 📋 Planned
3. **Visual Asset Generation** (Steps 7-9) - 🧪 Experimental
4. **Presentation Assembly** (Steps 10-11) - ✅ Implemented

## Architecture

### Core Components

**Base Infrastructure:**
- `base_skill.py` - Abstract base class for all skills with standardized input/output contracts
- `skill_registry.py` - Singleton registry for skill discovery and dependency resolution
- `workflow_orchestrator.py` - Multi-phase workflow coordination with checkpoint support
- `checkpoint_handler.py` - Interactive user approval system with batch capabilities
- `config_manager.py` - Multi-source configuration loading (defaults, user, project, env, CLI)

**Plugin Definition:**
- `plugin_manifest.json` - Plugin metadata, dependencies, and skill definitions
- `config_schema.json` - JSON schema for configuration validation

**CLI Interface:**
- `cli.py` - Unified command-line entry point
- `commands/` - Individual command implementations for each entry point

### Directory Structure

```
plugin/
├── __init__.py                    # Plugin entry point
├── base_skill.py                  # BaseSkill abstract class
├── skill_registry.py              # Skill registry
├── workflow_orchestrator.py       # Workflow coordination
├── checkpoint_handler.py          # User checkpoints
├── config_manager.py              # Configuration management
├── cli.py                         # CLI entry point
├── plugin_manifest.json           # Plugin metadata
├── config_schema.json             # Configuration schema
├── commands/                      # CLI commands
│   ├── __init__.py
│   ├── research.py                # 📋 Planned
│   ├── outline.py                 # 📋 Planned
│   ├── draft.py                   # 📋 Planned
│   ├── generate_images.py         # 🔄 Integration in progress
│   ├── build.py                   # 🔄 Integration in progress
│   ├── resume.py                  # 📋 Planned
│   ├── status.py                  # 📋 Planned
│   ├── from_research.py           # 📋 Planned
│   ├── from_outline.py            # 📋 Planned
│   ├── from_draft.py              # 📋 Planned
│   └── from_images.py             # 📋 Planned
├── skills/                        # Skill implementations
│   └── __init__.py
└── lib/                           # Library modules
    └── __init__.py
```

## Usage

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Validate installation
python -m plugin.cli validate
```

### Commands

#### Full Workflow
```bash
# Complete end-to-end workflow
python -m plugin.cli full-workflow "AI in Healthcare" --template cfa

# Skip checkpoints for automation
python -m plugin.cli full-workflow "Your Topic" --no-checkpoints
```

#### Individual Skills
```bash
# Research (Phase 1 - Planned)
python -m plugin.cli research "AI in Healthcare" --output research.json

# Outline (Phase 1 - Planned)
python -m plugin.cli outline research.json --output outline.md

# Draft content (Phase 2 - Planned)
python -m plugin.cli draft-content outline.md --output presentation.md

# Generate images (Phase 3 - Integration in progress)
python -m plugin.cli generate-images presentation.md --resolution high

# Build presentation (Phase 4 - Integration in progress)
python -m plugin.cli build-presentation presentation.md --template cfa
```

#### Workflow Management
```bash
# Show current workflow status
python -m plugin.cli status

# Auto-detect and resume workflow
python -m plugin.cli resume

# List all available skills
python -m plugin.cli list-skills --verbose
```

#### Configuration
```bash
# Show current config
python -m plugin.cli config show

# Get specific value
python -m plugin.cli config get research.max_sources

# Set value
python -m plugin.cli config set research.max_sources 30
```

## Configuration

Configuration is loaded from multiple sources (in priority order):

1. **Command-line arguments** (highest priority)
2. **Environment config** (`config.{env}.json`)
3. **Project config** (`config.json` in project root)
4. **User config** (`~/.config/presentation-plugin/config.json`)
5. **Default config** (built-in)

### Example Configuration

```json
{
  "research": {
    "max_sources": 20,
    "search_depth": "comprehensive",
    "citation_format": "APA"
  },
  "content": {
    "tone": "professional",
    "reading_level": "college",
    "max_bullets_per_slide": 5
  },
  "images": {
    "default_resolution": "high",
    "enable_validation": false,
    "max_refinement_attempts": 3
  },
  "workflow": {
    "enable_checkpoints": true,
    "auto_split_presentations": true,
    "max_slides_per_presentation": 30
  }
}
```

See `config_schema.json` for complete schema.

## Workflow Phases

### Phase 1: Research & Discovery (📋 Planned)
**Skills:** `research`, `extract-insights`, `outline`
- Web search and source gathering
- Insight extraction and concept mapping
- Multi-presentation outline generation
- **Checkpoint:** Review research and approve direction

### Phase 2: Content Development (📋 Planned)
**Skills:** `draft-content`, `optimize-content`
- AI-assisted slide content drafting
- Quality optimization (readability, tone, structure)
- Graphics description generation
- **Checkpoint:** Review and approve content

### Phase 3: Visual Asset Generation (🧪 Experimental)
**Skills:** `generate-images`, `validate-images`, `refine-images`
- AI image generation via Gemini API
- Visual validation against intent
- Iterative refinement based on feedback
- **Checkpoint:** Review and approve visuals

### Phase 4: Presentation Assembly (✅ Implemented)
**Skills:** `build-presentation`
- PowerPoint generation with brand templates
- Slide classification and layout selection
- Final presentation output

## Entry Points

The plugin supports starting at any point in the workflow:

| Entry Point | Starting Artifact | Skills Executed | Use Case |
|-------------|-------------------|-----------------|----------|
| From topic | User prompt | research → outline → draft → images → build | Full end-to-end |
| From research | `research.json` | outline → draft → images → build | Skip research |
| From outline | `outline.md` | draft → images → build | Manual outline |
| From draft | `presentation.md` | images → build | Manual content |
| From images | `images/*.jpg` | build | Rebuild only |

## Development Status

### ✅ Implemented (PRIORITY 1)
- Plugin infrastructure foundation
- Skill registry and base classes
- Workflow orchestrator with checkpoints
- Configuration management
- CLI interface with all commands
- Plugin manifest and schema

### 🧪 Experimental
- Visual validation (Windows + PowerPoint required)
- Image refinement engine
- Intelligent slide type classification

### 📋 Planned

**PRIORITY 2: Research & Discovery Tools**
- Web research skill
- Citation management
- Insight extraction
- Outline generation
- Interactive research assistant

**PRIORITY 3: Content Development Tools**
- Content drafting skill
- Content optimization
- Graphics description validation

**PRIORITY 4: Production Enhancements**
- Production-ready validation
- Enhanced refinement
- Workflow analytics
- Cost estimation

## Contributing

See `PLUGIN_IMPLEMENTATION_PLAN.md` for detailed implementation roadmap.

### Adding a New Skill

1. Create skill class implementing `BaseSkill`:
```python
from plugin.base_skill import BaseSkill, SkillInput, SkillOutput

class MySkill(BaseSkill):
    @property
    def skill_id(self) -> str:
        return "my-skill"

    @property
    def display_name(self) -> str:
        return "My Skill"

    @property
    def description(self) -> str:
        return "What my skill does"

    def validate_input(self, input: SkillInput) -> tuple[bool, list[str]]:
        # Validate input
        return (True, [])

    def execute(self, input: SkillInput) -> SkillOutput:
        # Execute skill logic
        return SkillOutput.success_result(
            data={"result": "success"},
            artifacts=["output.json"]
        )
```

2. Register skill:
```python
from plugin.skill_registry import SkillRegistry
# Import from appropriate skill subdirectory based on skill category
from plugin.skills.research.my_skill import MySkill  # For research skills
# from plugin.skills.content.my_skill import MySkill  # For content skills
# from plugin.skills.images.my_skill import MySkill  # For image skills
# from plugin.skills.assembly.my_skill import MySkill  # For assembly skills

SkillRegistry.register_skill(MySkill)
```

3. Add to `plugin_manifest.json`

4. Create command in `commands/my_skill.py`

## License

MIT

## Links

- **Repository:** https://github.com/davistroy/slide-generator
- **Implementation Plan:** [PLUGIN_IMPLEMENTATION_PLAN.md](../PLUGIN_IMPLEMENTATION_PLAN.md)
- **Project Documentation:** [CLAUDE.md](../CLAUDE.md)
