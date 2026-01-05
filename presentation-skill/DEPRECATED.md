# ⚠️ DEPRECATED: presentation-skill

**This module is deprecated and will be removed in v3.0.0.**

The functionality has been consolidated into the plugin skill system:

- `lib/parser.py` → `plugin.skills.MarkdownParsingSkill`
- `lib/assembler.py` → `plugin.skills.PowerPointAssemblySkill`

## Migration

See [Migration Guide](../docs/MIGRATION.md) for detailed instructions.

## Quick Start with New Skills

```python
from plugin.skills import PowerPointAssemblySkill
from plugin.base_skill import SkillInput

skill = PowerPointAssemblySkill()
result = skill.execute(SkillInput(data={
    "markdown_path": "presentation.md",
    "template": "cfa"
}))
print(f"Generated: {result.artifacts[0]}")
```

## CLI Usage

```bash
# New way
python -m plugin.cli build-presentation presentation.md --template cfa

# Old way (deprecated)
python presentation-skill/generate_presentation.py presentation.md --template cfa
```
