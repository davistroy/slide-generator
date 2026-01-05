# Migration Guide: presentation-skill to Plugin Skills

This guide explains how to transition from the standalone `presentation-skill/` module
to the integrated plugin skill system.

## Overview

The `presentation-skill/` module has been consolidated into the plugin architecture
as two new skills:

| Old Module | New Skill | Purpose |
|------------|-----------|---------|
| `lib/parser.py` | `MarkdownParsingSkill` | Parse markdown presentations |
| `lib/assembler.py` | `PowerPointAssemblySkill` | Build PowerPoint files |

## Benefits of Migration

1. **Unified Interface**: Same SkillInput/SkillOutput contract as other skills
2. **Workflow Integration**: Seamlessly use in WorkflowOrchestrator pipelines
3. **Better Error Handling**: Consistent error reporting and recovery
4. **Progress Tracking**: Integrated with metrics and progress reporting
5. **Type Safety**: Full type hints and validation

## Migration Steps

### Before (Old Way)

```python
from presentation_skill.lib.assembler import assemble_presentation
from presentation_skill.lib.parser import parse_presentation

# Parse markdown
slides = parse_presentation("presentation.md")

# Build PowerPoint
output = assemble_presentation(
    markdown_path="presentation.md",
    template_id="cfa",
    output_name="output.pptx"
)
```

### After (New Way)

```python
from plugin.skills import MarkdownParsingSkill, PowerPointAssemblySkill
from plugin.base_skill import SkillInput

# Parse markdown
parser = MarkdownParsingSkill()
parse_result = parser.execute(SkillInput(
    data={"markdown_path": "presentation.md"}
))
slides = parse_result.data["slides"]

# Build PowerPoint
assembler = PowerPointAssemblySkill()
build_result = assembler.execute(SkillInput(
    data={
        "markdown_path": "presentation.md",
        "template": "cfa",
        "output_name": "output.pptx"
    }
))
output_path = build_result.artifacts[0]
```

## CLI Migration

### Before
```bash
python presentation-skill/generate_presentation.py presentation.md --template cfa
```

### After
```bash
python -m plugin.cli build-presentation presentation.md --template cfa
```

## Deprecation Timeline

- **v2.1.0**: Deprecation warnings added to old module
- **v2.2.0**: Old module marked as deprecated in documentation
- **v3.0.0**: Old module will be removed

## Getting Help

If you encounter issues migrating, please open an issue on GitHub.
