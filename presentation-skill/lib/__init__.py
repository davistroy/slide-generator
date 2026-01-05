"""
DEPRECATED: This module is deprecated and will be removed in v3.0.0.

Please use the new plugin skills instead:
- MarkdownParsingSkill for parsing
- PowerPointAssemblySkill for assembly

See docs/MIGRATION.md for migration instructions.
"""

import warnings

warnings.warn(
    "presentation-skill is deprecated and will be removed in v3.0.0. "
    "Use plugin.skills.MarkdownParsingSkill and plugin.skills.PowerPointAssemblySkill instead. "
    "See docs/MIGRATION.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)
