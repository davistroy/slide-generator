---
name: slide-gen
description: Generate a complete presentation on any topic
arguments:
  - name: topic
    description: The presentation topic
    required: true
  - name: template
    description: Template to use (cfa, stratfield)
    required: false
    default: stratfield
  - name: audience
    description: Target audience description
    required: false
---

# Slide Generator

Generate a complete presentation using the 11-step AI-assisted workflow.

## Usage
```
/slide-gen "Topic" [--template cfa|stratfield] [--audience "description"]
```

## Examples
```
/slide-gen "Rochester 2GC Carburetor Rebuild" --template cfa
/slide-gen "AI Transformation Strategy" --template stratfield --audience "C-level executives"
```

## What This Does

1. **Research** - Autonomous web research with citations
2. **Insights** - Extract key findings and concepts
3. **Outline** - Generate presentation structure
4. **Content** - Draft titles, bullets, speaker notes
5. **Optimize** - Quality analysis and improvement
6. **Graphics** - Validate image descriptions
7. **Images** - Generate slide visuals (Gemini Pro)
8. **Validate** - Visual quality check (optional)
9. **Refine** - Iterative improvement
10. **Assemble** - Build PowerPoint file
11. **Output** - Final .pptx with brand styling

## Execution

Run:
```bash
python -m plugin.cli full-workflow "$TOPIC" --template $TEMPLATE --audience "$AUDIENCE"
```

## Output

Final output: `output/{topic}-presentation.pptx`
