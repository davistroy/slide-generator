"""
Skills for the presentation generation plugin.

Organized into subdirectories by function:
- research/: Research and insight extraction skills
- content/: Content drafting, optimization, and outline skills
- images/: Image validation and generation skills
- assembly/: PowerPoint building and refinement skills
"""

# Research skills
from .research.research_skill import ResearchSkill
from .research.insight_extraction_skill import InsightExtractionSkill
from .research.research_assistant_skill import ResearchAssistantSkill

# Content skills
from .content.content_drafting_skill import ContentDraftingSkill
from .content.content_optimization_skill import ContentOptimizationSkill
from .content.outline_skill import OutlineSkill

# Image skills
from .images.validation_skill import ValidationSkill

# Assembly skills
from .assembly.powerpoint_assembly_skill import PowerPointAssemblySkill
from .assembly.markdown_parsing_skill import MarkdownParsingSkill
from .assembly.refinement_skill import RefinementSkill

__all__ = [
    # Research
    "ResearchSkill",
    "InsightExtractionSkill",
    "ResearchAssistantSkill",
    # Content
    "ContentDraftingSkill",
    "ContentOptimizationSkill",
    "OutlineSkill",
    # Images
    "ValidationSkill",
    # Assembly
    "PowerPointAssemblySkill",
    "MarkdownParsingSkill",
    "RefinementSkill",
]
