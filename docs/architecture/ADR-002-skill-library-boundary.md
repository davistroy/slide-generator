# ADR-002: Skill vs Library Boundary

## Status
Accepted

## Date
2025-01-08

## Context

The slide-generator architecture has two primary code organization patterns:

1. **Skills**: Workflow steps exposed via CLI (e.g., `research`, `outline`, `draft-content`)
2. **Libraries**: Reusable components used by skills (e.g., `claude_client`, `quality_analyzer`)

We needed clear guidelines for when functionality should be a skill versus a library.

## Decision

### Skills (`plugin/skills/`)

A **skill** is appropriate when:

1. **User-facing operation**: The functionality is exposed via CLI command
2. **Workflow step**: It represents a discrete step in the presentation workflow
3. **Input/Output contract**: Has well-defined SkillInput → SkillOutput transformation
4. **State transition**: Produces artifacts that can be consumed by subsequent skills
5. **Checkpointable**: User may want to review output before proceeding

### Libraries (`plugin/lib/`)

A **library** is appropriate when:

1. **Reusable utility**: Used by multiple skills or components
2. **No CLI exposure**: Not directly invoked by users
3. **Stateless operation**: Operates on inputs without producing workflow artifacts
4. **Technical infrastructure**: Provides foundational capabilities (API clients, rate limiting, etc.)
5. **Cross-cutting concern**: Logging, metrics, configuration

## Rationale

### Clear Separation of Concerns

- Skills focus on **orchestrating** workflow steps
- Libraries focus on **implementing** technical capabilities

### Maintainability

- Skills can be added/removed without affecting core infrastructure
- Libraries can be improved without changing skill interfaces

### Testability

- Skills test workflow behavior and integration
- Libraries test individual components in isolation

## Consequences

### Positive

- **Clear organization**: Developers know where to find and add code
- **Reduced coupling**: Skills depend on libraries, not other skills
- **Easier testing**: Small, focused test scopes
- **CLI consistency**: All user-facing operations follow the same pattern

### Negative

- **Potential duplication**: Some logic may appear in multiple skills
- **Abstraction overhead**: Simple operations may need skill wrapper

## Implementation

### Skill Structure

```python
# plugin/skills/research/research_skill.py
class ResearchSkill(BaseSkill):
    skill_id = "research"
    display_name = "Web Research"

    def validate_input(self, input: SkillInput) -> tuple[bool, list[str]]:
        # Validate topic exists
        ...

    def execute(self, input: SkillInput) -> SkillOutput:
        # Use libraries to perform research
        client = get_claude_client()
        agent = create_research_agent(client)
        results = agent.research(input.data["topic"])
        return SkillOutput(success=True, data=results)
```

### Library Structure

```python
# plugin/lib/quality_analyzer.py
class QualityAnalyzer:
    """Analyzes presentation content quality."""

    def analyze_presentation(self, slides, style_guide):
        # Pure analysis logic, no CLI interaction
        ...
```

### Dependency Rules

```
Skills → Libraries: ✓ Allowed
Libraries → Libraries: ✓ Allowed
Skills → Skills: ✗ NOT Allowed (use orchestrator)
Libraries → Skills: ✗ NOT Allowed
```

## Examples

### This Should Be a Skill

- **Research**: User runs `sg research "Topic"`, produces `research.json`
- **Outline**: User runs `sg outline research.json`, produces `outline.md`
- **Build**: User runs `sg build presentation.md`, produces `*.pptx`

### This Should Be a Library

- **ClaudeClient**: Wraps Claude API, used by multiple skills
- **QualityAnalyzer**: Analyzes content quality, used by optimization skill
- **GraphicsValidator**: Validates image descriptions, used by image skill
- **RateLimiter**: Controls API request rates, used by all API clients

### Edge Cases

| Functionality | Decision | Rationale |
|--------------|----------|-----------|
| Health check | Skill | User-invoked, CLI exposed |
| Status display | Skill | User-invoked, shows workflow state |
| JSON parsing | Library | Pure utility, no workflow state |
| Progress reporting | Library | Cross-cutting UI concern |

## Alternatives Considered

1. **Flat structure**: All code in single directory
   - Rejected: Poor organization at scale

2. **Feature-based structure**: Group by presentation section
   - Rejected: Doesn't match workflow-oriented design

3. **Layer-based structure**: controllers/services/repositories
   - Rejected: Web framework pattern doesn't fit CLI tool

## References

- `plugin/base_skill.py`: Skill interface definition
- `plugin/skill_registry.py`: Skill registration and discovery
- `CLAUDE.md`: Project structure documentation
