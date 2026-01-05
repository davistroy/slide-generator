"""
Template Registry

This module provides automatic discovery and registration of brand templates.
Templates register themselves using the @register_template decorator.

Usage:
    from templates import get_template, list_templates

    # List available templates
    for template_id, template_name, desc in list_templates():
        print(f"{template_id}: {template_name}")

    # Get a template instance
    template = get_template("cfa")
    template.add_title_slide("My Presentation", "Subtitle", "2025")
    template.save("output.pptx")
"""

from typing import Dict, Type, List, Tuple
from pathlib import Path

from plugin.lib.presentation.template_base import PresentationTemplate


# Registry of available templates
_TEMPLATES: Dict[str, Type[PresentationTemplate]] = {}


def register_template(template_class: Type[PresentationTemplate]) -> Type[PresentationTemplate]:
    """
    Decorator to register a template class.

    Usage:
        @register_template
        class MyTemplate(PresentationTemplate):
            ...

    Args:
        template_class: The template class to register

    Returns:
        The same class (unchanged)
    """
    # Create a temporary instance to get the id
    # We need to be careful here - some templates might need assets
    # So we'll get the id from the class property if possible
    template_id = template_class.id.fget(template_class)  # Get property without instance
    _TEMPLATES[template_id] = template_class
    return template_class


def get_template(template_id: str, **kwargs) -> PresentationTemplate:
    """
    Get an instance of the specified template.

    Args:
        template_id: The template identifier (e.g., 'cfa', 'stratfield')
        **kwargs: Additional arguments passed to template constructor

    Returns:
        An instance of the requested template

    Raises:
        ValueError: If template_id is not registered
    """
    if template_id not in _TEMPLATES:
        available = ", ".join(_TEMPLATES.keys())
        raise ValueError(
            f"Unknown template: '{template_id}'. "
            f"Available templates: {available}"
        )
    return _TEMPLATES[template_id](**kwargs)


def list_templates() -> List[Tuple[str, str, str]]:
    """
    List all registered templates.

    Returns:
        List of (id, name, description) tuples for all registered templates
    """
    result = []
    for template_id, template_class in _TEMPLATES.items():
        # Get name and description from class
        name = template_class.name.fget(template_class)
        desc = getattr(template_class, 'description', property(lambda s: ""))
        if isinstance(desc, property):
            desc = desc.fget(template_class) if desc.fget else ""
        result.append((template_id, name, desc))
    return result


def get_template_ids() -> List[str]:
    """
    Get list of all template IDs.

    Returns:
        List of template identifiers
    """
    return list(_TEMPLATES.keys())


# Import templates to trigger registration
# These imports must come AFTER the register_template function is defined
from plugin.templates.cfa.template import CFAPresentation
from plugin.templates.stratfield.template import StratfieldPresentation
