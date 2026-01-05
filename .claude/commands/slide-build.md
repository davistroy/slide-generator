---
name: slide-build
description: Build PowerPoint from content file
arguments:
  - name: input
    description: Content markdown file
    required: true
  - name: template
    description: Template name
    required: false
    default: stratfield
---

# Build Presentation

## Execution

```bash
python -m plugin.cli build-presentation "$INPUT" --template $TEMPLATE
```
