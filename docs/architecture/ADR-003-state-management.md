# ADR-003: State Management Strategy

## Status
Accepted

## Date
2025-01-08

## Context

The slide-generator workflow is a multi-step process that can:
- Take significant time to complete (minutes to hours)
- Be interrupted (user abort, errors, system issues)
- Need to resume from a previous point
- Support manual editing between steps

We needed a strategy for managing workflow state that enables:
1. **Resumption**: Continue from where you left off
2. **Checkpointing**: Review and approve before proceeding
3. **Manual editing**: Modify artifacts between steps
4. **Caching**: Avoid re-running expensive operations

## Decision

We adopt a **file-based state management** approach with two mechanisms:

### 1. Checkpoint System (Workflow Orchestration)

The `WorkflowOrchestrator` manages checkpoints between workflow phases:

- **Phase boundaries**: Checkpoint after each phase (Research, Content, Visual, Assembly)
- **User interaction**: User can approve, retry, modify, or abort
- **State preservation**: Phase results saved for resumption

### 2. Artifact Detection (StateDetector)

The `StateDetector` scans for existing files to determine workflow state:

| Artifact | Workflow Step | Phase |
|----------|---------------|-------|
| `research.json` | Step 2 | Research |
| `insights.json` | Step 3 | Research |
| `outline.json` | Step 4 | Content Development |
| `presentation.md` | Step 5 | Content Development |
| `images/slide-*.jpg` | Step 8 | Visual Generation |
| `*.pptx` | Step 11 | Presentation Assembly |

## Rationale

### File-Based Over Database

1. **Simplicity**: No database setup or maintenance
2. **Portability**: Project directory is self-contained
3. **Editability**: Users can manually edit JSON/markdown files
4. **Transparency**: Easy to inspect current state
5. **Version control friendly**: Artifacts can be committed to git

### Artifact Detection Over Explicit State File

1. **Resilience**: Works even if state file is missing/corrupted
2. **Flexibility**: Supports starting from manually created artifacts
3. **No synchronization**: Artifact presence is the source of truth
4. **External compatibility**: Works with artifacts from other tools

## Consequences

### Positive

- **Resume from anywhere**: Start workflow at any step with existing artifacts
- **Manual intervention**: Edit files between steps without special handling
- **Recovery**: Restart workflow after errors without losing progress
- **Transparency**: User can see exactly what each step produced

### Negative

- **No atomic transactions**: Partial failures may leave inconsistent state
- **File system dependency**: Performance tied to I/O speed
- **Cleanup responsibility**: User must manage artifact cleanup
- **Limited concurrency**: Single project directory per workflow

### Mitigations

1. **Validation**: StateDetector validates artifact structure, not just existence
2. **Stale detection**: Compare modification times to detect outdated artifacts
3. **Force flags**: CLI options to regenerate despite existing artifacts
4. **Cleanup commands**: Utility to remove intermediate artifacts

## Implementation

### StateDetector

```python
class StateDetector:
    """Detect workflow state by scanning for artifacts."""

    ARTIFACT_PATTERNS = {
        "research": ("research.json", 2),
        "insights": ("insights.json", 3),
        "outline": (["outline.json", "outline.md"], 4),
        "presentation": ("presentation.md", 5),
        "images": ("images/", 8),
        "pptx": ("*.pptx", 11),
    }

    def detect_state(self) -> WorkflowState:
        # Scan directory for artifacts
        # Return highest completed step and recommendations
```

### CheckpointHandler

```python
class CheckpointHandler:
    """Handle user checkpoints in workflow."""

    def checkpoint(
        self, phase_name: str, phase_result: dict, artifacts: list
    ) -> CheckpointResult:
        # Show user the phase results
        # Get user decision: CONTINUE, RETRY, MODIFY, ABORT
```

### WorkflowOrchestrator

```python
class WorkflowOrchestrator:
    """Orchestrate multi-phase workflow with checkpoints."""

    def execute_workflow(self, topic: str, config: dict):
        for phase in WorkflowPhase:
            result = self.run_phase(phase, ...)
            checkpoint = self.checkpoint_handler.checkpoint(...)
            if checkpoint.decision == ABORT:
                return ...
```

### CLI Integration

```bash
# Check current state
sg status

# Output:
# Detected Artifacts:
#   [OK] research        (modified: 2025-01-08 10:30, 15 sources)
#   [OK] outline         (modified: 2025-01-08 10:35, 12 slides)
#   [--] presentation    (not found)
#
# Workflow Position: Step 4 of 11
# Next Step: Run: sg draft-content outline.md

# Resume workflow
sg resume

# Force regenerate
sg outline research.json --force
```

## Alternatives Considered

1. **SQLite database**: More complex, less portable
2. **Redis/in-memory**: Doesn't persist across sessions
3. **Cloud state storage**: Requires network, credentials
4. **Explicit state file**: Single point of failure, sync issues

## Related Decisions

- ADR-002: Skill vs Library Boundary (skills produce artifacts)
- ADR-001: Dual API Strategy (artifacts include API responses)

## References

- `plugin/lib/state_detector.py`: StateDetector implementation
- `plugin/checkpoint_handler.py`: CheckpointHandler implementation
- `plugin/workflow_orchestrator.py`: WorkflowOrchestrator implementation
- `plugin/cli.py`: `cmd_status()` and `cmd_resume()` commands
