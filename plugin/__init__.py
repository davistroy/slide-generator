"""
Claude Code Plugin: AI-Assisted Presentation Generation

This plugin implements a comprehensive workflow for generating professional
presentations from research through final PowerPoint output.

Version: 2.0.0
Author: Stratfield

Type Support:
    This package is PEP 561 compliant and includes type annotations.
    Import types from plugin.types for TypedDict and Protocol definitions.
"""

# Load environment variables early, before any other imports that might need them
from dotenv import load_dotenv

load_dotenv()

__version__ = "2.0.0"
__author__ = "Stratfield"

from .base_skill import BaseSkill, SkillInput, SkillOutput, SkillStatus
from .config_manager import ConfigManager
from .skill_registry import SkillMetadata, SkillRegistry
from .workflow_orchestrator import WorkflowOrchestrator


__all__ = [
    "BaseSkill",
    "ConfigManager",
    "SkillInput",
    "SkillMetadata",
    "SkillOutput",
    # Core classes
    "SkillRegistry",
    "SkillStatus",
    "WorkflowOrchestrator",
]
