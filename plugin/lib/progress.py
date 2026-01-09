"""
Progress reporting for CLI workflows.

This module provides:
- ProgressReporter class implementing ProgressReporterProtocol
- Text-based progress bars for CLI
- Overall workflow and sub-task progress tracking
- Estimated time remaining calculation
- Callback support for custom progress handling

Usage:
    from plugin.lib.progress import ProgressReporter

    reporter = ProgressReporter()
    reporter.start_task("Generating content", total_steps=100)
    for i in range(100):
        reporter.update_progress(i + 1)
    reporter.complete_task("Content generated")
"""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from plugin.types import ProgressReporterProtocol


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime for dataclass default factory."""
    return datetime.now(timezone.utc)


if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class Task:
    """
    Represents a task being tracked.

    Attributes:
        name: Task name
        total_steps: Total number of steps (0 for indeterminate)
        current_step: Current step number
        start_time: When task started
        end_time: When task completed (if finished)
        subtasks: List of subtask names
        status: Current status (running, completed, error)
    """

    name: str
    total_steps: int = 0
    current_step: int = 0
    start_time: datetime = field(default_factory=_utc_now)
    end_time: datetime | None = None
    subtasks: list[str] = field(default_factory=list)
    status: str = "running"

    @property
    def progress_percent(self) -> float:
        """
        Get progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.total_steps == 0:
            return 0.0
        return min(100.0, (self.current_step / self.total_steps) * 100)

    @property
    def elapsed_seconds(self) -> float:
        """
        Get elapsed time in seconds.

        Returns:
            Seconds elapsed since task started
        """
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    @property
    def estimated_remaining_seconds(self) -> float | None:
        """
        Estimate remaining time in seconds.

        Returns:
            Estimated seconds remaining, or None if indeterminate
        """
        if self.total_steps == 0 or self.current_step == 0:
            return None

        elapsed = self.elapsed_seconds
        progress_ratio = self.current_step / self.total_steps
        if progress_ratio >= 1.0:
            return 0.0

        total_estimated = elapsed / progress_ratio
        return total_estimated - elapsed


class ProgressReporter:
    """
    Thread-safe progress reporter for CLI workflows.

    Implements ProgressReporterProtocol and provides text-based progress
    bars, task tracking, and estimated time remaining.

    Attributes:
        enabled: Whether progress reporting is enabled
        use_colors: Whether to use ANSI colors
        show_eta: Whether to show estimated time remaining
        callback: Optional callback for custom progress handling
        tasks: Stack of active tasks
        lock: Thread lock for safe updates
    """

    def __init__(
        self,
        enabled: bool = True,
        use_colors: bool = True,
        show_eta: bool = True,
        callback: Callable[[str, float], None] | None = None,
    ) -> None:
        """
        Initialize progress reporter.

        Args:
            enabled: Whether to enable progress reporting
            use_colors: Whether to use ANSI color codes
            show_eta: Whether to show estimated time remaining
            callback: Optional callback function(message, progress)
        """
        self.enabled = enabled
        self.use_colors = use_colors and sys.stdout.isatty()
        self.show_eta = show_eta
        self.callback = callback

        self.tasks: list[Task] = []
        self.lock = threading.Lock()

        # ANSI color codes
        self.colors = {
            "green": "\033[32m",
            "yellow": "\033[33m",
            "red": "\033[31m",
            "blue": "\033[34m",
            "reset": "\033[0m",
            "bold": "\033[1m",
        }

        # Track terminal width
        self._terminal_width = 80

    def _colorize(self, text: str, color: str) -> str:
        """
        Add color to text if colors are enabled.

        Args:
            text: Text to colorize
            color: Color name

        Returns:
            Colorized text or plain text
        """
        if not self.use_colors:
            return text
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def _format_time(self, seconds: float) -> str:
        """
        Format seconds as human-readable time.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "2m 30s")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def _render_progress_bar(
        self, percent: float, width: int = 40, fill: str = "█", empty: str = "░"
    ) -> str:
        """
        Render a text-based progress bar.

        Args:
            percent: Progress percentage (0-100)
            width: Width of progress bar in characters
            fill: Character for filled portion
            empty: Character for empty portion

        Returns:
            Progress bar string

        Example:
            >>> reporter._render_progress_bar(50, width=20)
            '[██████████░░░░░░░░░░] 50.0%'
        """
        filled_width = int(width * (percent / 100))
        bar = fill * filled_width + empty * (width - filled_width)
        return f"[{bar}] {percent:5.1f}%"

    def _clear_line(self) -> None:
        """
        Clear the current terminal line.
        """
        if self.enabled and sys.stdout.isatty():
            sys.stdout.write("\r\033[K")
            sys.stdout.flush()

    def _write(self, message: str, clear: bool = False) -> None:
        """
        Write a message to stdout.

        Args:
            message: Message to write
            clear: Whether to clear line first
        """
        if not self.enabled:
            return

        if clear:
            self._clear_line()

        sys.stdout.write(message)
        sys.stdout.flush()

    def start_task(
        self,
        name: str,
        total_steps: int = 0,
        parent_task: str | None = None,
    ) -> None:
        """
        Start tracking a new task.

        Args:
            name: Task name
            total_steps: Total number of steps (0 for indeterminate)
            parent_task: Parent task name (for subtasks)

        Example:
            >>> reporter.start_task("Generating slides", total_steps=10)
        """
        with self.lock:
            task = Task(name=name, total_steps=total_steps)
            self.tasks.append(task)

            # Add as subtask if parent specified
            if parent_task:
                for t in self.tasks:
                    if t.name == parent_task:
                        t.subtasks.append(name)
                        break

        # Report start
        message = self._colorize(f"Starting: {name}", "blue")
        self._write(f"\n{message}\n")

        if self.callback:
            self.callback(f"start: {name}", 0.0)

    def update_progress(
        self,
        current_step: int | None = None,
        message: str | None = None,
    ) -> None:
        """
        Update progress for the current task.

        Args:
            current_step: Current step number (increments if None)
            message: Optional status message

        Example:
            >>> reporter.update_progress(5, "Processing slide 5")
        """
        if not self.enabled:
            return

        with self.lock:
            if not self.tasks:
                return

            task = self.tasks[-1]

            # Update step
            if current_step is not None:
                task.current_step = current_step
            else:
                task.current_step += 1

            # Build progress message
            parts = []

            # Add task name
            parts.append(self._colorize(task.name, "bold"))

            # Add progress bar if determinate
            if task.total_steps > 0:
                bar = self._render_progress_bar(task.progress_percent, width=30)
                parts.append(bar)

                # Add step counter
                parts.append(f"({task.current_step}/{task.total_steps})")

            # Add elapsed time
            elapsed = self._format_time(task.elapsed_seconds)
            parts.append(f"Elapsed: {elapsed}")

            # Add ETA if available
            if self.show_eta and task.estimated_remaining_seconds is not None:
                eta = self._format_time(task.estimated_remaining_seconds)
                parts.append(f"ETA: {eta}")

            # Add custom message
            if message:
                parts.append(f"- {message}")

            # Write progress line
            progress_line = " ".join(parts)
            self._write(f"\r{progress_line}", clear=True)

        # Call callback
        if self.callback:
            percent = task.progress_percent if task.total_steps > 0 else 0.0
            msg = message or f"{task.name}: {task.current_step}/{task.total_steps}"
            self.callback(msg, percent)

    def complete_task(self, message: str | None = None) -> None:
        """
        Mark the current task as completed.

        Args:
            message: Optional completion message

        Example:
            >>> reporter.complete_task("Slides generated successfully")
        """
        with self.lock:
            if not self.tasks:
                return

            task = self.tasks.pop()
            task.status = "completed"
            task.end_time = datetime.now(timezone.utc)
            task.current_step = task.total_steps

        # Clear progress line and write completion message
        self._clear_line()

        parts = [
            self._colorize("✓", "green"),
            self._colorize(task.name, "bold"),
        ]

        if message:
            parts.append(f"- {message}")

        # Add final timing
        elapsed = self._format_time(task.elapsed_seconds)
        parts.append(f"({elapsed})")

        completion_line = " ".join(parts)
        self._write(f"{completion_line}\n")

        if self.callback:
            self.callback(f"complete: {task.name}", 100.0)

    def error(self, message: str, clear_progress: bool = True) -> None:
        """
        Report an error.

        Args:
            message: Error message
            clear_progress: Whether to clear progress display

        Example:
            >>> reporter.error("Failed to generate slide 5")
        """
        with self.lock:
            # Mark current task as error if exists
            if self.tasks:
                task = self.tasks[-1]
                task.status = "error"
                task.end_time = datetime.now(timezone.utc)

        if clear_progress:
            self._clear_line()

        error_msg = self._colorize(f"✗ Error: {message}", "red")
        self._write(f"{error_msg}\n")

        if self.callback:
            self.callback(f"error: {message}", 0.0)

    def report(self, message: str, progress: float) -> None:
        """
        Report progress update (implements ProgressReporterProtocol).

        Args:
            message: Progress message
            progress: Progress value (0-100)

        Example:
            >>> reporter.report("Processing...", 50.0)
        """
        # Update current task if exists
        if self.tasks:
            with self.lock:
                task = self.tasks[-1]
                if task.total_steps > 0:
                    task.current_step = int(task.total_steps * (progress / 100))

            self.update_progress(message=message)
        else:
            # Just print the message
            self._write(f"\r{message} ({progress:.1f}%)", clear=True)

        if self.callback:
            self.callback(message, progress)

    def complete(self, message: str) -> None:
        """
        Report completion (implements ProgressReporterProtocol).

        Args:
            message: Completion message

        Example:
            >>> reporter.complete("Task finished successfully")
        """
        self.complete_task(message)

    def info(self, message: str) -> None:
        """
        Print an info message without affecting progress.

        Args:
            message: Info message

        Example:
            >>> reporter.info("Using cached data")
        """
        self._clear_line()
        info_msg = self._colorize(f"ℹ {message}", "blue")
        self._write(f"{info_msg}\n")

    def warning(self, message: str) -> None:
        """
        Print a warning message without affecting progress.

        Args:
            message: Warning message

        Example:
            >>> reporter.warning("API rate limit approaching")
        """
        self._clear_line()
        warning_msg = self._colorize(f"⚠ Warning: {message}", "yellow")
        self._write(f"{warning_msg}\n")

    def get_current_task(self) -> Task | None:
        """
        Get the current task being tracked.

        Returns:
            Current task or None
        """
        with self.lock:
            return self.tasks[-1] if self.tasks else None

    def get_all_tasks(self) -> list[Task]:
        """
        Get all tasks in the stack.

        Returns:
            List of tasks
        """
        with self.lock:
            return self.tasks.copy()

    def clear_tasks(self) -> None:
        """
        Clear all tasks from the stack.
        """
        with self.lock:
            self.tasks.clear()

    def disable(self) -> None:
        """
        Disable progress reporting.
        """
        self.enabled = False

    def enable(self) -> None:
        """
        Enable progress reporting.
        """
        self.enabled = True


class SilentProgressReporter(ProgressReporterProtocol):
    """
    Silent progress reporter that does nothing.

    Useful for non-interactive contexts or when progress reporting
    is not desired.
    """

    def report(self, message: str, progress: float) -> None:
        """No-op report method."""
        pass

    def complete(self, message: str) -> None:
        """No-op complete method."""
        pass

    def error(self, message: str) -> None:
        """No-op error method."""
        pass


def create_progress_reporter(
    enabled: bool = True,
    use_colors: bool = True,
    show_eta: bool = True,
    callback: Callable[[str, float], None] | None = None,
) -> ProgressReporterProtocol:
    """
    Create a progress reporter instance.

    Args:
        enabled: Whether to enable progress reporting
        use_colors: Whether to use ANSI colors
        show_eta: Whether to show estimated time remaining
        callback: Optional callback for custom progress handling

    Returns:
        ProgressReporter or SilentProgressReporter

    Example:
        >>> reporter = create_progress_reporter(enabled=True)
        >>> reporter.start_task("Processing", total_steps=100)
    """
    if enabled:
        return ProgressReporter(
            enabled=True,
            use_colors=use_colors,
            show_eta=show_eta,
            callback=callback,
        )
    else:
        return SilentProgressReporter()
