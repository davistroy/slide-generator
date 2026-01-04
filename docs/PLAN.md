# Presentation Generator Skill - Implementation Plan

## Overview

Create a Claude Code **skill** that generates branded PowerPoint presentations from markdown slide definitions. The skill will:

1. Parse a presentation markdown file (pres-template.md format)
2. Interactively prompt user to select brand template (CFA, Stratfield, or future templates)
3. Generate images ONLY for slides with `**Graphic**:` sections (via Google Gemini API)
4. Assemble final PowerPoint using the selected brand template
5. Output files to current working directory

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    presentation-skill/                          │
├─────────────────────────────────────────────────────────────────┤
│  SKILL.md              # Skill documentation & usage            │
│  generate_presentation.py  # Main entry point                   │
│                                                                 │
│  lib/                                                           │
│  ├── parser.py         # Markdown slide parser                  │
│  ├── image_generator.py # Gemini API image generation           │
│  ├── template_base.py  # Abstract base class for brand templates│
│  └── assembler.py      # PowerPoint assembly orchestration      │
│                                                                 │
│  templates/            # Extensible brand templates             │
│  ├── __init__.py       # Template registry                      │
│  ├── cfa/                                                       │
│  │   ├── template.py   # CFA implementation                     │
│  │   └── assets/       # CFA logos, icons                       │
│  └── stratfield/                                                │
│      ├── template.py   # Stratfield implementation              │
│      └── assets/       # Stratfield logos, backgrounds          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Markdown Parser (`lib/parser.py`)

**Purpose**: Extract structured slide data from pres-template.md format.

**Input**: Path to markdown file following pres-template.md format

**Output**: List of `Slide` dataclass objects:

```python
@dataclass
class Slide:
    number: int
    slide_type: str          # "TITLE SLIDE", "CONTENT", "SECTION DIVIDER", etc.
    title: str
    subtitle: Optional[str]
    content: List[str]       # Bullet points
    graphic: Optional[str]   # Graphic description (triggers image generation)
    speaker_notes: Optional[str]
    raw_content: str         # Full slide markdown for image generation context
```

**Parsing Logic**:
- Detect slide headers: `## **SLIDE N: TYPE**` or `## Slide N`
- Extract `**Title**:` value
- Extract `**Subtitle**:` value (if present)
- Extract `**Content**:` section (parse bullets with indentation levels)
- Extract `**Graphic**:` section (key trigger for image generation)
- Extract `**SPEAKER NOTES**:` section
- Map slide type to template method (TITLE SLIDE → add_title_slide, etc.)

---

### 2. Template Base Class (`lib/template_base.py`)

**Purpose**: Define abstract interface that all brand templates must implement. Enables easy addition of new brands.

```python
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from pathlib import Path

class PresentationTemplate(ABC):
    """Abstract base class for brand templates."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable template name (e.g., 'Chick-fil-A')"""
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """Template identifier (e.g., 'cfa')"""
        pass

    @abstractmethod
    def add_title_slide(self, title: str, subtitle: str = "", date: str = "") -> None:
        pass

    @abstractmethod
    def add_section_break(self, title: str) -> None:
        pass

    @abstractmethod
    def add_content_slide(self, title: str, subtitle: str, bullets: List[Tuple[str, int]]) -> None:
        pass

    @abstractmethod
    def add_image_slide(self, title: str, image_path: str, subtitle: str = "") -> None:
        pass

    @abstractmethod
    def add_text_and_image_slide(self, title: str, bullets: List[Tuple[str, int]], image_path: str) -> None:
        pass

    @abstractmethod
    def save(self, filepath: str) -> None:
        pass
```

---

### 3. Template Registry (`templates/__init__.py`)

**Purpose**: Auto-discover and register available brand templates.

```python
from typing import Dict, Type
from lib.template_base import PresentationTemplate

# Registry populated by template modules
TEMPLATES: Dict[str, Type[PresentationTemplate]] = {}

def register_template(template_class: Type[PresentationTemplate]):
    """Decorator to register a template."""
    TEMPLATES[template_class.id] = template_class
    return template_class

def get_template(template_id: str) -> PresentationTemplate:
    """Get an instance of the specified template."""
    if template_id not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_id}")
    return TEMPLATES[template_id]()

def list_templates() -> List[Tuple[str, str]]:
    """Return list of (id, name) for all registered templates."""
    return [(t.id, t.name) for t in TEMPLATES.values()]
```

---

### 4. Image Generator (`lib/image_generator.py`)

**Purpose**: Generate slide images using Google Gemini API for slides with `**Graphic**:` sections.

**Key Features**:
- Only generates images when slide has `graphic` field populated
- Uses slide content + graphic description as context
- Outputs to `./images/slide-{N}.jpg`
- Supports `--notext` mode for clean backgrounds
- Handles API errors gracefully with retries

```python
def generate_slide_image(
    slide: Slide,
    style_config: dict,
    output_dir: Path,
    fast_mode: bool = False,
    notext: bool = True,
    force: bool = False
) -> Optional[Path]:
    """
    Generate image for a slide if it has a graphic description.

    Returns path to generated image, or None if no graphic defined.
    """
    if not slide.graphic:
        return None

    # ... implementation using Gemini API
```

---

### 5. Presentation Assembler (`lib/assembler.py`)

**Purpose**: Orchestrate the full workflow - parse, generate images, build PowerPoint.

```python
def assemble_presentation(
    markdown_path: str,
    template_id: str,
    style_config: Optional[dict] = None,
    output_name: Optional[str] = None,
    skip_images: bool = False,
    fast_mode: bool = False
) -> str:
    """
    Main workflow:
    1. Parse markdown file into Slide objects
    2. For each slide with graphic: generate image
    3. Create presentation using selected template
    4. Add slides based on type mapping
    5. Save and return output path
    """
```

**Slide Type Mapping**:
```python
SLIDE_TYPE_MAP = {
    "TITLE SLIDE": "add_title_slide",
    "TITLE": "add_title_slide",
    "SECTION DIVIDER": "add_section_break",
    "SECTION BREAK": "add_section_break",
    "CONTENT": "add_content_slide",
    "PROBLEM STATEMENT": "add_content_slide",
    "INSIGHT": "add_content_slide",
    "CONCEPT INTRODUCTION": "add_content_slide",
    "FRAMEWORK": "add_content_slide",
    "COMPARISON": "add_content_slide",
    "DEEP DIVE": "add_content_slide",
    "CASE STUDY": "add_content_slide",
    "PATTERN": "add_content_slide",
    "METRICS": "add_content_slide",  # Could also be image slide
    "ARCHITECTURE": "add_image_slide",
    "DIAGRAM": "add_image_slide",
    "ACTION": "add_content_slide",
    "SUMMARY": "add_content_slide",
    "CLOSING": "add_content_slide",
    "Q&A": "add_section_break",
    "APPENDIX": "add_content_slide",
}
```

---

### 6. Interactive CLI (`generate_presentation.py`)

**Purpose**: Main entry point with interactive prompts.

**Flow**:
```
1. Prompt: "Enter path to presentation markdown file:"
   → Validate file exists and is readable

2. Prompt: "Select brand template:"
   → Display numbered list of available templates
   → User enters number (e.g., "1" for CFA, "2" for Stratfield)

3. Prompt: "Enter style JSON path (or press Enter for default):"
   → Optional custom style config for image generation

4. Prompt: "Output filename (default: presentation.pptx):"
   → Optional custom output name

5. Confirm: "Ready to generate. This will create images for X slides. Continue? [Y/n]"

6. Execute:
   → Show progress for each slide
   → "Generating image for Slide 3..."
   → "Adding Slide 4: Content slide..."
   → "Saved: ./presentation.pptx"
```

---

## File Outputs

All outputs go to **current working directory**:

```
./
├── presentation.pptx      # Final PowerPoint file
└── images/                # Generated slide images
    ├── slide-1.jpg
    ├── slide-3.jpg        # Only slides with **Graphic** sections
    └── slide-7.jpg
```

---

## Adding New Brand Templates

To add a new brand template (e.g., "Acme Corp"):

1. Create directory: `templates/acme/`

2. Add assets: `templates/acme/assets/` (logos, backgrounds, icons)

3. Create `templates/acme/template.py`:

```python
from lib.template_base import PresentationTemplate
from templates import register_template

@register_template
class AcmePresentation(PresentationTemplate):

    @property
    def name(self) -> str:
        return "Acme Corporation"

    @property
    def id(self) -> str:
        return "acme"

    # ... implement all abstract methods
```

4. Import in `templates/__init__.py`:
```python
from templates.acme.template import AcmePresentation
```

The template will automatically appear in the interactive selection menu.

---

## Dependencies

```
python-pptx>=0.6.21    # PowerPoint generation
Pillow>=9.0.0          # Image handling
lxml>=4.9.0            # XML manipulation for bullet formatting
google-genai>=0.3.0    # Gemini API for image generation
```

---

## Error Handling

1. **Missing markdown file**: Clear error message with path
2. **Invalid markdown format**: Warn and skip malformed slides
3. **Missing GOOGLE_API_KEY**: Skip image generation with warning, continue with placeholder
4. **Image generation failure**: Retry 3x, then continue without image
5. **Missing template assets**: Use fallback colors/shapes

---

## SKILL.md Documentation

The skill will include comprehensive documentation:
- Installation instructions
- Usage examples
- Markdown format reference
- Brand template options
- Troubleshooting guide

---

## Implementation Order

1. **Phase 1: Core Structure**
   - Create directory structure
   - Implement `template_base.py` (abstract class)
   - Port CFA template to new structure
   - Port Stratfield template to new structure

2. **Phase 2: Parser**
   - Implement `parser.py` with Slide dataclass
   - Test with sample markdown files

3. **Phase 3: Image Generation**
   - Implement `image_generator.py`
   - Integrate with existing generate_images_for_slides.py logic

4. **Phase 4: Assembler**
   - Implement `assembler.py` workflow
   - Add slide type mapping logic

5. **Phase 5: CLI & Polish**
   - Implement interactive `generate_presentation.py`
   - Write SKILL.md documentation
   - Test end-to-end workflow

---

## Questions Resolved

| Question | Decision |
|----------|----------|
| Plugin type | Skill (conversational) |
| Brand selection | Interactive prompt at runtime |
| Image generation | Only for slides with `**Graphic**:` section |
| Output location | Current working directory |
| Extensibility | Abstract base class + registry pattern |
