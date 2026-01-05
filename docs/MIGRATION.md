# Migration Guide: Presentation Library Location

This guide explains the consolidated presentation library structure.

## Overview

The presentation generation functionality is now located in the plugin architecture:

| Component | New Location | Purpose |
|-----------|--------------|---------|
| Parser | `plugin.lib.presentation.parser` | Parse markdown presentations |
| Assembler | `plugin.lib.presentation.assembler` | Build PowerPoint files |
| Templates | `plugin.templates` | Brand templates (cfa, stratfield) |
| Type Classifier | `plugin.lib.presentation.type_classifier` | Slide type detection |
| Image Generator | `plugin.lib.presentation.image_generator` | AI image generation |

## Skills

Two high-level skills wrap the presentation library:

- **MarkdownParsingSkill**: Parse markdown into structured slide data
- **PowerPointAssemblySkill**: Build complete PowerPoint presentations

## Usage Examples

### Using Skills (Recommended)

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

### Using Library Directly

```python
from plugin.lib.presentation import parse_presentation, assemble_presentation

# Parse markdown
slides = parse_presentation("presentation.md")

# Build PowerPoint
output = assemble_presentation(
    markdown_path="presentation.md",
    template_id="cfa",
    output_name="output.pptx"
)
```

## CLI Usage

```bash
# Parse markdown and inspect structure
python -m plugin.cli parse-markdown presentation.md -o slides.json

# Build PowerPoint presentation
python -m plugin.cli build-presentation presentation.md --template cfa

# Build with options
python -m plugin.cli build-presentation presentation.md \
    --template stratfield \
    --output my-deck.pptx \
    --fast
```

## Templates

Available brand templates:
- `cfa`: Chick-fil-A branded template
- `stratfield`: Stratfield Consulting template

Templates are registered in `plugin.templates` and can be accessed via:

```python
from plugin.templates import get_template, list_templates

# List available templates
for template_id, name, description in list_templates():
    print(f"{template_id}: {name}")

# Get template instance
template = get_template("cfa")
```

## Getting Help

If you encounter issues, please open an issue on GitHub.
