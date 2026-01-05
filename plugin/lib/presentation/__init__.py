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

from .parser import (
    parse_presentation,
    Slide,
    BulletItem,
    TableItem,
    CodeBlockItem,
    TextItem,
)
from .assembler import assemble_presentation
from .type_classifier import SlideTypeClassifier, TypeClassification
from .image_generator import generate_all_images, generate_slide_image
from .template_base import TemplateBase

__all__ = [
    # Parser
    "parse_presentation",
    "Slide",
    "BulletItem",
    "TableItem",
    "CodeBlockItem",
    "TextItem",
    # Assembler
    "assemble_presentation",
    # Type classifier
    "SlideTypeClassifier",
    "TypeClassification",
    # Image generator
    "generate_all_images",
    "generate_slide_image",
    # Template
    "TemplateBase",
]
