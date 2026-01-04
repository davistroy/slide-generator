"""
Claude Code Plugin: AI-Assisted Presentation Generation

This plugin implements a comprehensive workflow for generating professional
presentations from research through final PowerPoint output.

Version: 2.0.0
Author: Stratfield
"""

__version__ = "2.0.0"
__author__ = "Stratfield"

from .skill_registry import SkillRegistry
from .base_skill import BaseSkill, SkillInput, SkillOutput
from .workflow_orchestrator import WorkflowOrchestrator
from .config_manager import ConfigManager

__all__ = [
    "SkillRegistry",
    "BaseSkill",
    "SkillInput",
    "SkillOutput",
    "WorkflowOrchestrator",
    "ConfigManager",
]
