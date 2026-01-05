# API Documentation

## Generating Documentation

This project uses [pdoc](https://pdoc.dev/) for API documentation generation.

### Install pdoc

```bash
pip install pdoc
```

### Generate HTML Documentation

```bash
# Generate docs for all modules
pdoc --html --output-dir docs/api/html plugin

# Or use Make
make docs
```

### Serve Documentation Locally

```bash
pdoc --http : plugin
# Then open http://localhost:8080
```

## Module Structure

- **plugin.base_skill** - Base skill interface (SkillInput, SkillOutput, BaseSkill)
- **plugin.skills** - Skill implementations (Research, Content, PowerPoint)
- **plugin.lib** - Core libraries
  - **plugin.lib.presentation** - PowerPoint generation
  - **plugin.lib.claude_client** - Claude API client
  - **plugin.lib.async_claude_client** - Async Claude client
  - **plugin.lib.validators** - Input validation
  - **plugin.lib.retry** - Retry logic
  - **plugin.lib.rate_limiter** - Rate limiting
  - **plugin.lib.logging_config** - Logging setup
  - **plugin.lib.metrics** - Metrics collection
- **plugin.templates** - Brand templates (CFA, Stratfield)

## Quick Links

After generating docs, key entry points:
- `plugin/index.html` - Main module
- `plugin/skills/index.html` - All skills
- `plugin/lib/index.html` - Library modules
