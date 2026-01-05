---
name: slide-research
description: Conduct autonomous research on a topic
arguments:
  - name: topic
    description: Research topic
    required: true
  - name: depth
    description: Research depth (quick, standard, comprehensive)
    required: false
    default: standard
---

# Slide Research

Conduct autonomous web research using Claude Agent SDK.

## Usage
```
/slide-research "Topic" [--depth quick|standard|comprehensive]
```

## Examples
```
/slide-research "Quantum Computing Applications"
/slide-research "Electric Vehicle Market Trends" --depth comprehensive
```

## Execution

```bash
python -m plugin.cli research "$TOPIC" --depth $DEPTH --output research.json
```

## Output

Creates `research.json` with:
- Source URLs and content
- Extracted insights
- Citation information
- Suggested presentation angles
