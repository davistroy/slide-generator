"""
Workflow orchestrator for multi-phase presentation generation.

Coordinates execution of multiple skills across workflow phases,
manages checkpoints, handles errors, and supports resumption.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .base_skill import SkillInput, SkillOutput
from .checkpoint_handler import CheckpointDecision, CheckpointHandler, CheckpointResult
from .skill_registry import SkillRegistry


logger = logging.getLogger(__name__)


class WorkflowPhase(Enum):
    """Workflow phases."""

    RESEARCH = "research"
    CONTENT_DEVELOPMENT = "content_development"
    VISUAL_GENERATION = "visual_generation"
    PRESENTATION_ASSEMBLY = "presentation_assembly"


@dataclass
class PhaseResult:
    """
    Result from executing a workflow phase.

    Attributes:
        phase: Phase that was executed
        success: Whether phase completed successfully
        outputs: List of SkillOutputs from all skills in the phase
        artifacts: All artifacts created during the phase
        errors: Any errors encountered
        metadata: Additional metadata
    """

    phase: WorkflowPhase
    success: bool
    outputs: list[SkillOutput] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_last_output(self) -> SkillOutput | None:
        """Get the last skill output from this phase."""
        return self.outputs[-1] if self.outputs else None

    def get_output_data(self) -> dict[str, Any]:
        """Get combined output data from all skills."""
        combined = {}
        for output in self.outputs:
            combined.update(output.data)
        return combined


@dataclass
class WorkflowResult:
    """
    Result from complete workflow execution.

    Attributes:
        success: Whether workflow completed successfully
        phase_results: Results from each phase
        final_artifacts: Final output artifacts
        total_duration: Total execution time in seconds
        metadata: Additional metadata
    """

    success: bool
    phase_results: list[PhaseResult] = field(default_factory=list)
    final_artifacts: list[str] = field(default_factory=list)
    total_duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_phase_result(self, phase: WorkflowPhase) -> PhaseResult | None:
        """Get result for a specific phase."""
        for result in self.phase_results:
            if result.phase == phase:
                return result
        return None


class WorkflowOrchestrator:
    """
    Orchestrates multi-skill workflows with user checkpoints.

    Manages execution of presentation generation workflow across 4 phases:
    1. Research & Discovery
    2. Content Development
    3. Visual Asset Generation
    4. Presentation Assembly

    Supports:
    - Checkpoint-based user review
    - Partial workflow execution (start from any phase)
    - Resumption from existing artifacts
    - Error recovery
    """

    # Define workflow phases and their skills
    PHASE_SKILLS = {
        WorkflowPhase.RESEARCH: ["research", "extract-insights", "outline"],
        WorkflowPhase.CONTENT_DEVELOPMENT: ["draft-content", "optimize-content"],
        WorkflowPhase.VISUAL_GENERATION: [
            "generate-images",
            "validate-images",
            "refine-images",
        ],
        WorkflowPhase.PRESENTATION_ASSEMBLY: ["build-presentation"],
    }

    def __init__(
        self,
        checkpoint_handler: CheckpointHandler | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize workflow orchestrator.

        Args:
            checkpoint_handler: Handler for user checkpoints
            config: Global configuration
        """
        self.checkpoint_handler = checkpoint_handler or CheckpointHandler()
        self.config = config or {}
        self.skill_registry = SkillRegistry()

    def execute_workflow(
        self,
        workflow_id: str,
        initial_input: str | dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        Execute complete 4-phase workflow with checkpoints.

        Args:
            workflow_id: Unique identifier for this workflow execution
            initial_input: Initial input (topic string or structured data)
            config: Optional workflow-specific configuration

        Returns:
            WorkflowResult with all phase results and artifacts
        """
        import time

        start_time = time.time()

        # Merge configs
        merged_config = {**self.config, **(config or {})}

        # Prepare initial input
        if isinstance(initial_input, str):
            input_data = {"topic": initial_input}
        else:
            input_data = initial_input

        phase_results = []
        context = {"workflow_id": workflow_id}

        # Execute each phase with checkpoints
        for phase in WorkflowPhase:
            self.checkpoint_handler.show_message(
                f"Starting Phase: {phase.value.replace('_', ' ').title()}", "info"
            )

            # Execute phase
            phase_result = self.run_phase(
                phase=phase,
                input_data=input_data,
                context=context,
                config=merged_config,
            )

            phase_results.append(phase_result)

            if not phase_result.success:
                # Phase failed
                return WorkflowResult(
                    success=False,
                    phase_results=phase_results,
                    total_duration=time.time() - start_time,
                    metadata={"failed_phase": phase.value, "workflow_id": workflow_id},
                )

            # Checkpoint after phase
            checkpoint_result = self.checkpoint(
                phase_name=phase.value.replace("_", " ").title(),
                phase_result=phase_result,
            )

            if checkpoint_result.decision == CheckpointDecision.ABORT:
                # User aborted
                return WorkflowResult(
                    success=False,
                    phase_results=phase_results,
                    total_duration=time.time() - start_time,
                    metadata={
                        "aborted_at_phase": phase.value,
                        "abort_reason": checkpoint_result.feedback,
                        "workflow_id": workflow_id,
                    },
                )

            elif checkpoint_result.decision == CheckpointDecision.RETRY:
                # Retry phase with modifications
                if checkpoint_result.modifications:
                    merged_config.update(checkpoint_result.modifications)

                # Re-run phase
                phase_result = self.run_phase(
                    phase=phase,
                    input_data=input_data,
                    context=context,
                    config=merged_config,
                )

                # Replace last phase result
                phase_results[-1] = phase_result

            elif checkpoint_result.decision == CheckpointDecision.MODIFY:
                # Pause for manual edits
                self.checkpoint_handler.show_message(
                    "Workflow paused. Resume when ready.", "info"
                )
                # In a real implementation, this would save state and exit
                # For now, we just continue

            # Update context with phase output
            context.update(phase_result.get_output_data())

            # Update input_data for next phase
            input_data = phase_result.get_output_data()

        # Workflow complete
        final_artifacts = []
        for phase_result in phase_results:
            final_artifacts.extend(phase_result.artifacts)

        return WorkflowResult(
            success=True,
            phase_results=phase_results,
            final_artifacts=final_artifacts,
            total_duration=time.time() - start_time,
            metadata={"workflow_id": workflow_id},
        )

    def run_phase(
        self,
        phase: WorkflowPhase,
        input_data: dict[str, Any],
        context: dict[str, Any],
        config: dict[str, Any],
    ) -> PhaseResult:
        """
        Execute all skills in a phase sequentially.

        Args:
            phase: Phase to execute
            input_data: Input data for the phase
            context: Contextual information
            config: Configuration

        Returns:
            PhaseResult with outputs and artifacts
        """
        skill_ids = self.PHASE_SKILLS.get(phase, [])
        if not skill_ids:
            return PhaseResult(
                phase=phase,
                success=False,
                errors=[f"No skills defined for phase: {phase.value}"],
            )

        outputs = []
        artifacts = []
        errors = []

        current_data = input_data.copy()

        # Execute skills sequentially
        for i, skill_id in enumerate(skill_ids):
            # Check if skill is registered
            if not self.skill_registry.is_registered(skill_id):
                errors.append(f"Skill '{skill_id}' not registered")
                continue

            # Get skill instance
            try:
                skill = self.skill_registry.get_skill(
                    skill_id, config=config.get(skill_id, {})
                )
            except (KeyError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.warning("Failed to instantiate skill '%s': %s", skill_id, e)
                errors.append(f"Failed to instantiate skill '{skill_id}': {e!s}")
                continue

            # Prepare input
            skill_input = SkillInput(
                data=current_data, context=context, config=config.get(skill_id, {})
            )

            # Execute skill
            self.checkpoint_handler.show_progress(
                current=i + 1,
                total=len(skill_ids),
                message=f"Running {skill.display_name}...",
            )

            try:
                output = skill.run(skill_input)
                outputs.append(output)

                if output.success:
                    # Update current_data for next skill
                    current_data.update(output.data)
                    artifacts.extend(output.artifacts)
                else:
                    errors.extend(output.errors)
                    # Continue even if skill failed (partial phase success)

            except Exception as e:
                logger.exception("Unexpected error in skill '%s'", skill_id)
                error_msg = f"Unexpected error in skill '{skill_id}': {e!s}"
                errors.append(error_msg)
                # Continue to next skill

        # Phase succeeds if at least one skill succeeded
        success = any(output.success for output in outputs) and len(errors) == 0

        return PhaseResult(
            phase=phase,
            success=success,
            outputs=outputs,
            artifacts=artifacts,
            errors=errors,
            metadata={"skill_count": len(skill_ids)},
        )

    def checkpoint(
        self, phase_name: str, phase_result: PhaseResult
    ) -> CheckpointResult:
        """
        Execute checkpoint after a phase.

        Args:
            phase_name: Human-readable phase name
            phase_result: Result from the phase

        Returns:
            CheckpointResult with user decision
        """
        # Prepare suggestions based on phase result
        suggestions = []

        if phase_result.errors:
            suggestions.append(f"⚠️ Phase had {len(phase_result.errors)} error(s)")

        if phase_result.artifacts:
            suggestions.append(
                f"Review generated artifacts: {', '.join(phase_result.artifacts[:3])}"
            )

        return self.checkpoint_handler.checkpoint(
            phase_name=phase_name,
            phase_result=phase_result.get_output_data(),
            artifacts=phase_result.artifacts,
            suggestions=suggestions,
        )

    def execute_partial_workflow(
        self,
        start_phase: WorkflowPhase,
        end_phase: WorkflowPhase,
        initial_input: str | dict[str, Any],
        config: dict[str, Any] | None = None,
    ) -> WorkflowResult:
        """
        Execute workflow from start_phase to end_phase.

        Args:
            start_phase: Phase to start from
            end_phase: Phase to end at (inclusive)
            initial_input: Input data
            config: Configuration

        Returns:
            WorkflowResult
        """
        import time

        start_time = time.time()

        # Get phase sequence
        all_phases = list(WorkflowPhase)
        start_idx = all_phases.index(start_phase)
        end_idx = all_phases.index(end_phase)

        if start_idx > end_idx:
            return WorkflowResult(
                success=False,
                metadata={"error": "start_phase must come before end_phase"},
            )

        phases_to_run = all_phases[start_idx : end_idx + 1]

        # Execute selected phases
        merged_config = {**self.config, **(config or {})}

        if isinstance(initial_input, str):
            input_data = {"topic": initial_input}
        else:
            input_data = initial_input

        phase_results = []
        context = {}

        for phase in phases_to_run:
            phase_result = self.run_phase(
                phase=phase,
                input_data=input_data,
                context=context,
                config=merged_config,
            )

            phase_results.append(phase_result)

            if not phase_result.success:
                return WorkflowResult(
                    success=False,
                    phase_results=phase_results,
                    total_duration=time.time() - start_time,
                    metadata={"failed_phase": phase.value},
                )

            # Update for next phase
            context.update(phase_result.get_output_data())
            input_data = phase_result.get_output_data()

        final_artifacts = []
        for phase_result in phase_results:
            final_artifacts.extend(phase_result.artifacts)

        return WorkflowResult(
            success=True,
            phase_results=phase_results,
            final_artifacts=final_artifacts,
            total_duration=time.time() - start_time,
        )

    def resume_workflow(
        self, project_dir: str, config: dict[str, Any] | None = None
    ) -> WorkflowResult:
        """
        Auto-detect state and resume workflow.

        Args:
            project_dir: Project directory with artifacts
            config: Configuration

        Returns:
            WorkflowResult

        Note: This is a placeholder. Full implementation requires StateDetector.
        """
        # TODO: Implement with StateDetector from lib/state_detector.py
        raise NotImplementedError(
            "Resume workflow requires StateDetector implementation. "
            "See PLUGIN_IMPLEMENTATION_PLAN.md for design."
        )

    def save_state(
        self, workflow_id: str, phase_results: list[PhaseResult], output_path: str
    ) -> None:
        """
        Save workflow state for resumption.

        Args:
            workflow_id: Workflow identifier
            phase_results: Results from completed phases
            output_path: Path to save state file
        """
        state = {
            "workflow_id": workflow_id,
            "completed_phases": [
                {
                    "phase": result.phase.value,
                    "success": result.success,
                    "artifacts": result.artifacts,
                    "errors": result.errors,
                }
                for result in phase_results
            ],
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, state_path: str) -> dict[str, Any]:
        """
        Load saved workflow state.

        Args:
            state_path: Path to state file

        Returns:
            State dictionary
        """
        with open(state_path) as f:
            return json.load(f)
