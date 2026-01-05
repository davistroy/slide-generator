---
name: slide-health
description: Check slide-generator plugin health and configuration
---

# Slide Generator Health Check

Validate that the slide-generator plugin is properly configured.

## Usage
```
/slide-health
```

## Execution

```bash
python -m plugin.cli health-check
```

## Checks Performed

- ANTHROPIC_API_KEY validity
- GOOGLE_API_KEY validity
- Python version compatibility
- Required dependencies installed
- Template availability
- Skill registry status
