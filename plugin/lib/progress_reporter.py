"""
Progress reporting for Claude Code integration.
Outputs structured JSON that Claude can parse and present to users.
"""

import json
import sys
from datetime import datetime
from enum import Enum
from typing import Any


class ProgressStatus(Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    CHECKPOINT = "checkpoint"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProgressReporter:
    """Reports workflow progress in structured format for Claude Code."""

    def __init__(self, workflow_name: str, total_steps: int):
        self.workflow_name = workflow_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = datetime.now()

    def _emit(self, data: dict[str, Any]) -> None:
        """Emit progress data as JSON to stderr."""
        output = {
            "type": "slide_generator_progress",
            "timestamp": datetime.now().isoformat(),
            "workflow": self.workflow_name,
            **data,
        }
        print(json.dumps(output), file=sys.stderr)

    def start_workflow(self) -> None:
        """Signal workflow start."""
        self._emit(
            {
                "status": ProgressStatus.STARTED.value,
                "message": f"Starting {self.workflow_name}",
                "total_steps": self.total_steps,
            }
        )

    def start_step(self, step_name: str, step_number: int) -> None:
        """Signal step start."""
        self.current_step = step_number
        self._emit(
            {
                "status": ProgressStatus.IN_PROGRESS.value,
                "step": step_number,
                "step_name": step_name,
                "total_steps": self.total_steps,
                "message": f"Step {step_number}/{self.total_steps}: {step_name}",
                "progress_percent": int((step_number - 1) / self.total_steps * 100),
            }
        )

    def complete_step(
        self, step_name: str, step_number: int, artifacts: dict[str, str] | None = None
    ) -> None:
        """Signal step completion."""
        self._emit(
            {
                "status": ProgressStatus.COMPLETED.value,
                "step": step_number,
                "step_name": step_name,
                "message": f"Completed: {step_name}",
                "progress_percent": int(step_number / self.total_steps * 100),
                "artifacts": artifacts or {},
            }
        )

    def checkpoint(
        self,
        step_name: str,
        step_number: int,
        message: str,
        requires_approval: bool = True,
    ) -> None:
        """Signal checkpoint requiring user decision."""
        self._emit(
            {
                "status": ProgressStatus.CHECKPOINT.value,
                "step": step_number,
                "step_name": step_name,
                "message": message,
                "requires_approval": requires_approval,
                "progress_percent": int(step_number / self.total_steps * 100),
            }
        )

    def fail_step(
        self, step_name: str, step_number: int, error: str, recoverable: bool = True
    ) -> None:
        """Signal step failure."""
        self._emit(
            {
                "status": ProgressStatus.FAILED.value,
                "step": step_number,
                "step_name": step_name,
                "error": error,
                "recoverable": recoverable,
                "message": f"Failed: {step_name} - {error}",
            }
        )

    def complete_workflow(self, output_file: str | None = None) -> None:
        """Signal workflow completion."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self._emit(
            {
                "status": ProgressStatus.COMPLETED.value,
                "message": f"Workflow completed in {elapsed:.1f}s",
                "progress_percent": 100,
                "elapsed_seconds": elapsed,
                "output_file": output_file,
            }
        )


def report_progress(
    step: int, total: int, message: str, status: str = "in_progress"
) -> None:
    """Simple progress reporting function."""
    output = {
        "type": "slide_generator_progress",
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "step": step,
        "total_steps": total,
        "message": message,
        "progress_percent": int(step / total * 100),
    }
    print(json.dumps(output), file=sys.stderr)
