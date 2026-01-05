---
name: slide-outline
description: Generate presentation outline from research
arguments:
  - name: input
    description: Research JSON file path
    required: true
---

# Generate Outline

## Execution

```bash
python -m plugin.cli outline "$INPUT" --output outline.md
```
