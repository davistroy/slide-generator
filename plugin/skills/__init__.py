"""
Skills for the presentation generation plugin.
"""

from .research_skill import ResearchSkill
from .insight_extraction_skill import InsightExtractionSkill
from .outline_skill import OutlineSkill
from .research_assistant_skill import ResearchAssistantSkill
from .markdown_parsing_skill import MarkdownParsingSkill
from .powerpoint_assembly_skill import PowerPointAssemblySkill

__all__ = [
    "ResearchSkill",
    "InsightExtractionSkill",
    "OutlineSkill",
    "ResearchAssistantSkill",
    # Consolidation skills
    "MarkdownParsingSkill",
    "PowerPointAssemblySkill",
]
