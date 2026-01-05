"""
User interaction handler for workflow checkpoints.

Provides interactive approval points between workflow phases,
allowing users to review outputs and make decisions.
"""

import functools
import operator
from dataclasses import dataclass
from enum import Enum
from typing import Any


class CheckpointDecision(Enum):
    """User decision at a checkpoint."""

    CONTINUE = "continue"  # Proceed to next phase
    RETRY = "retry"  # Re-run current phase with modifications
    ABORT = "abort"  # Cancel workflow
    MODIFY = "modify"  # Pause for manual edits


@dataclass
class CheckpointResult:
    """
    Result from a checkpoint interaction.

    Attributes:
        decision: User's decision
        feedback: Optional user feedback or instructions
        modifications: Optional modifications to apply
        metadata: Additional metadata
    """

    decision: CheckpointDecision
    feedback: str | None = None
    modifications: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


class CheckpointHandler:
    """
    Manages user checkpoints during workflow execution.

    Provides interactive prompts for users to review phase outputs
    and make decisions about workflow continuation.
    """

    def __init__(self, interactive: bool = True, auto_approve: bool = False):
        """
        Initialize checkpoint handler.

        Args:
            interactive: If True, prompt user for input. If False, use defaults.
            auto_approve: If True and interactive=False, auto-approve all checkpoints
        """
        self.interactive = interactive
        self.auto_approve = auto_approve

    def checkpoint(
        self,
        phase_name: str,
        phase_result: dict[str, Any],
        artifacts: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> CheckpointResult:
        """
        Execute a workflow checkpoint.

        Args:
            phase_name: Name of the phase being reviewed
            phase_result: Output data from the phase
            artifacts: List of file paths created
            suggestions: Optional suggestions for review

        Returns:
            CheckpointResult with user decision
        """
        if not self.interactive:
            return self._auto_decision()

        return self._interactive_checkpoint(
            phase_name, phase_result, artifacts or [], suggestions or []
        )

    def _auto_decision(self) -> CheckpointResult:
        """
        Generate automatic decision for non-interactive mode.

        Returns:
            Auto-approve if enabled, otherwise abort
        """
        if self.auto_approve:
            return CheckpointResult(
                decision=CheckpointDecision.CONTINUE,
                feedback="Auto-approved (non-interactive mode)",
            )
        else:
            return CheckpointResult(
                decision=CheckpointDecision.ABORT,
                feedback="Workflow stopped (non-interactive mode without auto-approve)",
            )

    def _interactive_checkpoint(
        self,
        phase_name: str,
        phase_result: dict[str, Any],
        artifacts: list[str],
        suggestions: list[str],
    ) -> CheckpointResult:
        """
        Execute interactive checkpoint with user prompts.

        Args:
            phase_name: Name of the phase
            phase_result: Output data from the phase
            artifacts: List of file paths created
            suggestions: Optional suggestions

        Returns:
            CheckpointResult with user decision
        """
        print("\n" + "=" * 70)
        print(f"CHECKPOINT: {phase_name}")
        print("=" * 70)

        # Display phase summary
        print(f"\n✓ {phase_name} completed successfully")

        # Display artifacts
        if artifacts:
            print("\n📁 Artifacts created:")
            for artifact in artifacts:
                print(f"   - {artifact}")

        # Display key results
        if phase_result:
            print("\n📊 Results:")
            self._display_result_summary(phase_result)

        # Display suggestions
        if suggestions:
            print("\n💡 Suggestions:")
            for suggestion in suggestions:
                print(f"   - {suggestion}")

        # Prompt for decision
        print("\n" + "-" * 70)
        print("What would you like to do?")
        print("  [1] Continue to next phase (default)")
        print("  [2] Retry this phase with modifications")
        print("  [3] Pause for manual edits")
        print("  [4] Abort workflow")
        print("-" * 70)

        choice = input("\nEnter choice [1-4] (or press Enter for 1): ").strip()

        # Map choice to decision
        decision_map = {
            "1": CheckpointDecision.CONTINUE,
            "2": CheckpointDecision.RETRY,
            "3": CheckpointDecision.MODIFY,
            "4": CheckpointDecision.ABORT,
            "": CheckpointDecision.CONTINUE,  # Default
        }

        decision = decision_map.get(choice, CheckpointDecision.CONTINUE)

        # Get feedback if needed
        feedback = None
        modifications = None

        if decision == CheckpointDecision.RETRY:
            feedback = input("\nWhat would you like to change? ").strip()
            modifications = self._parse_retry_feedback(feedback)

        elif decision == CheckpointDecision.MODIFY:
            print("\nWorkflow paused. Make your edits and then resume.")
            feedback = input("Press Enter when ready to continue... ")

        elif decision == CheckpointDecision.ABORT:
            feedback = input("\nReason for aborting (optional): ").strip()

        return CheckpointResult(
            decision=decision,
            feedback=feedback if feedback else None,
            modifications=modifications,
        )

    def _display_result_summary(self, result: dict[str, Any], indent: int = 0) -> None:
        """
        Display a summary of phase results.

        Args:
            result: Result dictionary
            indent: Indentation level
        """
        indent_str = "   " * indent

        for key, value in result.items():
            if isinstance(value, dict):
                print(f"{indent_str}{key}:")
                self._display_result_summary(value, indent + 1)
            elif isinstance(value, list):
                if len(value) <= 3:
                    print(f"{indent_str}{key}: {value}")
                else:
                    print(f"{indent_str}{key}: [{len(value)} items]")
            elif isinstance(value, str) and len(value) > 100:
                print(f"{indent_str}{key}: {value[:100]}...")
            else:
                print(f"{indent_str}{key}: {value}")

    def _parse_retry_feedback(self, feedback: str) -> dict[str, Any]:
        """
        Parse user feedback into structured modifications.

        Args:
            feedback: User feedback string

        Returns:
            Dictionary of modifications
        """
        # Basic parsing - can be enhanced with more sophisticated parsing
        modifications = {"user_feedback": feedback, "timestamp": self._get_timestamp()}

        # Try to detect common modification patterns
        feedback_lower = feedback.lower()

        if "research" in feedback_lower or "sources" in feedback_lower:
            modifications["area"] = "research"
        elif "outline" in feedback_lower or "structure" in feedback_lower:
            modifications["area"] = "outline"
        elif "content" in feedback_lower or "writing" in feedback_lower:
            modifications["area"] = "content"
        elif "images" in feedback_lower or "visuals" in feedback_lower:
            modifications["area"] = "images"

        return modifications

    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime

        return datetime.now().isoformat()

    def confirm_action(
        self, action: str, details: str | None = None, default: bool = True
    ) -> bool:
        """
        Simple yes/no confirmation prompt.

        Args:
            action: Action to confirm
            details: Optional additional details
            default: Default choice if user presses Enter

        Returns:
            True if confirmed, False otherwise
        """
        if not self.interactive:
            return self.auto_approve

        print(f"\n❓ {action}")
        if details:
            print(f"   {details}")

        default_str = "Y/n" if default else "y/N"
        choice = input(f"\nConfirm? [{default_str}]: ").strip().lower()

        if choice == "":
            return default
        return choice in ["y", "yes"]

    def show_message(self, message: str, message_type: str = "info") -> None:
        """
        Display a message to the user.

        Args:
            message: Message to display
            message_type: Type of message (info, warning, error, success)
        """
        icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}

        icon = icons.get(message_type, "ℹ️")
        print(f"\n{icon} {message}")

    def show_progress(self, current: int, total: int, message: str = "") -> None:
        """
        Display progress indicator.

        Args:
            current: Current step
            total: Total steps
            message: Optional progress message
        """
        percentage = int((current / total) * 100)
        bar_length = 40
        filled = int((current / total) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(f"\r[{bar}] {percentage}% {message}", end="", flush=True)

        if current == total:
            print()  # New line when complete


class BatchCheckpointHandler(CheckpointHandler):
    """
    Checkpoint handler that batches multiple checkpoints.

    Useful for workflows with many small checkpoints - batches them
    into a single review session.
    """

    def __init__(self, batch_size: int = 5, **kwargs):
        """
        Initialize batch checkpoint handler.

        Args:
            batch_size: Number of checkpoints to batch before prompting
            **kwargs: Additional arguments for CheckpointHandler
        """
        super().__init__(**kwargs)
        self.batch_size = batch_size
        self.pending_checkpoints = []

    def checkpoint(
        self,
        phase_name: str,
        phase_result: dict[str, Any],
        artifacts: list[str] | None = None,
        suggestions: list[str] | None = None,
    ) -> CheckpointResult:
        """
        Add checkpoint to batch or execute if batch is full.

        Args:
            phase_name: Name of the phase
            phase_result: Output data
            artifacts: Artifacts created
            suggestions: Suggestions

        Returns:
            CheckpointResult
        """
        self.pending_checkpoints.append(
            {
                "phase_name": phase_name,
                "phase_result": phase_result,
                "artifacts": artifacts or [],
                "suggestions": suggestions or [],
            }
        )

        if len(self.pending_checkpoints) >= self.batch_size:
            return self.flush_batch()

        # Auto-continue for batched checkpoints
        return CheckpointResult(
            decision=CheckpointDecision.CONTINUE, feedback="Batched for review"
        )

    def flush_batch(self) -> CheckpointResult:
        """
        Execute all pending checkpoints as a batch review.

        Returns:
            CheckpointResult for the batch
        """
        if not self.pending_checkpoints:
            return CheckpointResult(decision=CheckpointDecision.CONTINUE)

        print("\n" + "=" * 70)
        print(f"BATCH CHECKPOINT: {len(self.pending_checkpoints)} phases")
        print("=" * 70)

        for i, cp in enumerate(self.pending_checkpoints, 1):
            print(f"\n{i}. {cp['phase_name']}")
            if cp["artifacts"]:
                print(f"   Artifacts: {', '.join(cp['artifacts'])}")

        result = super().checkpoint(
            phase_name=f"Batch Review ({len(self.pending_checkpoints)} phases)",
            phase_result={
                "phases": [cp["phase_name"] for cp in self.pending_checkpoints]
            },
            artifacts=functools.reduce(
                operator.iadd, [cp["artifacts"] for cp in self.pending_checkpoints], []
            ),
            suggestions=functools.reduce(
                operator.iadd,
                [cp["suggestions"] for cp in self.pending_checkpoints],
                [],
            ),
        )

        self.pending_checkpoints.clear()
        return result
