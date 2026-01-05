"""
Presentation library - PowerPoint generation components.

This module contains the core presentation generation functionality:
- parser: Markdown parsing for slide definitions
- assembler: PowerPoint assembly workflow
- type_classifier: Slide type classification
- image_generator: AI image generation
- template_base: Base template class
- visual_validator: Visual validation (experimental)
- refinement_engine: Iterative refinement
- slide_exporter: Slide export utilities
"""

from .assembler import assemble_presentation
from .image_generator import generate_all_images, generate_slide_image
from .parser import (
    BulletItem,
    CodeBlockItem,
    Slide,
    TableItem,
    TextItem,
    parse_presentation,
)
from .template_base import PresentationTemplate as TemplateBase
from .type_classifier import SlideTypeClassifier, TypeClassification


__all__ = [
    "BulletItem",
    "CodeBlockItem",
    "Slide",
    # Type classifier
    "SlideTypeClassifier",
    "TableItem",
    # Template
    "TemplateBase",
    "TextItem",
    "TypeClassification",
    # Assembler
    "assemble_presentation",
    # Image generator
    "generate_all_images",
    "generate_slide_image",
    # Parser
    "parse_presentation",
]
