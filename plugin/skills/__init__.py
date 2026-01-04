"""
Skills for the presentation generation plugin.
"""

from .research_skill import ResearchSkill
from .insight_extraction_skill import InsightExtractionSkill
from .outline_skill import OutlineSkill
from .research_assistant_skill import ResearchAssistantSkill

__all__ = [
    "ResearchSkill",
    "InsightExtractionSkill",
    "OutlineSkill",
    "ResearchAssistantSkill"
]
