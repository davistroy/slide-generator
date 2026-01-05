# Architecture Decision Record: Module Consolidation

## Status
Accepted

## Context
The `presentation-skill/` module existed as a separate component from the main
plugin system, leading to:
- Duplicate code patterns
- Inconsistent interfaces
- Difficulty integrating into workflows
- Maintenance overhead

## Decision
Consolidate `presentation-skill/` into the plugin skill system by:
1. Creating wrapper skills (MarkdownParsingSkill, PowerPointAssemblySkill)
2. Maintaining backward compatibility with deprecation warnings
3. Gradual migration path over 3 versions

## Consequences

### Positive
- Unified skill interface across all components
- Better integration with WorkflowOrchestrator
- Single source of truth for presentation generation
- Consistent error handling and progress reporting

### Negative
- Migration effort required for existing users
- Temporary code duplication during transition

## Implementation
- v2.1.0: Add wrapper skills and deprecation warnings
- v2.2.0: Update documentation, mark as deprecated
- v3.0.0: Remove deprecated module
