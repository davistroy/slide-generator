# Example Workflow Outputs

This directory contains sample outputs from each stage of the presentation generation workflow.

## Sample Workflow: Machine Learning Fundamentals

| Step | File | Description |
|------|------|-------------|
| 1 | `sample-workflow/1-research.json` | Research output with sources and insights |
| 2 | `sample-workflow/2-outline.md` | Structured presentation outline |
| 3 | `sample-workflow/3-content.md` | Full slide content with speaker notes |

## Using Examples

These examples can be used to:
- Understand expected input/output formats
- Test individual pipeline stages
- Debug workflow issues
- Train on the system before live use

## Running from Examples

```bash
# Start from existing research
python -m plugin.cli outline examples/sample-workflow/1-research.json

# Start from existing outline
python -m plugin.cli draft-content examples/sample-workflow/2-outline.md

# Build from existing content
python -m plugin.cli build-presentation examples/sample-workflow/3-content.md --template stratfield
```
