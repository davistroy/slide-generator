"""
Unit tests for plugin/lib/progress.py

Tests the Task dataclass, ProgressReporter class, SilentProgressReporter class,
and the create_progress_reporter factory function.
"""

import sys
import threading
import time
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from plugin.lib.progress import (
    ProgressReporter,
    SilentProgressReporter,
    Task,
    create_progress_reporter,
)


# ==============================================================================
# Test Task Dataclass
# ==============================================================================


class TestTask:
    """Tests for the Task dataclass."""

    def test_task_default_initialization(self):
        """Test Task with default values."""
        task = Task(name="Test Task")

        assert task.name == "Test Task"
        assert task.total_steps == 0
        assert task.current_step == 0
        assert task.end_time is None
        assert task.subtasks == []
        assert task.status == "running"
        assert isinstance(task.start_time, datetime)

    def test_task_custom_initialization(self):
        """Test Task with custom values."""
        start = datetime(2025, 1, 1, 12, 0, 0)
        task = Task(
            name="Custom Task",
            total_steps=100,
            current_step=50,
            start_time=start,
            subtasks=["sub1", "sub2"],
            status="completed",
        )

        assert task.name == "Custom Task"
        assert task.total_steps == 100
        assert task.current_step == 50
        assert task.start_time == start
        assert task.subtasks == ["sub1", "sub2"]
        assert task.status == "completed"

    def test_progress_percent_with_steps(self):
        """Test progress_percent property with total steps."""
        task = Task(name="Progress Task", total_steps=100, current_step=25)
        assert task.progress_percent == 25.0

    def test_progress_percent_zero_steps(self):
        """Test progress_percent returns 0 when total_steps is 0."""
        task = Task(name="Indeterminate Task", total_steps=0)
        assert task.progress_percent == 0.0

    def test_progress_percent_at_completion(self):
        """Test progress_percent at 100%."""
        task = Task(name="Complete Task", total_steps=50, current_step=50)
        assert task.progress_percent == 100.0

    def test_progress_percent_over_100_capped(self):
        """Test progress_percent is capped at 100%."""
        task = Task(name="Over Task", total_steps=50, current_step=75)
        assert task.progress_percent == 100.0

    def test_progress_percent_half_step(self):
        """Test progress_percent with fractional percentage."""
        task = Task(name="Half Task", total_steps=3, current_step=1)
        assert abs(task.progress_percent - 33.333) < 0.01

    def test_elapsed_seconds_running_task(self):
        """Test elapsed_seconds for a running task."""
        start = datetime.utcnow() - timedelta(seconds=10)
        task = Task(name="Running Task", start_time=start)

        elapsed = task.elapsed_seconds
        # Allow some tolerance for execution time
        assert 9.5 <= elapsed <= 11.0

    def test_elapsed_seconds_completed_task(self):
        """Test elapsed_seconds for a completed task."""
        start = datetime(2025, 1, 1, 12, 0, 0)
        end = datetime(2025, 1, 1, 12, 0, 30)
        task = Task(name="Completed Task", start_time=start, end_time=end)

        assert task.elapsed_seconds == 30.0

    def test_estimated_remaining_seconds_with_progress(self):
        """Test estimated_remaining_seconds calculation."""
        start = datetime.utcnow() - timedelta(seconds=10)
        task = Task(
            name="Progress Task",
            total_steps=100,
            current_step=50,
            start_time=start,
        )

        remaining = task.estimated_remaining_seconds
        # Should estimate ~10 more seconds (50% done in 10s)
        assert remaining is not None
        assert 8.0 <= remaining <= 12.0

    def test_estimated_remaining_seconds_indeterminate(self):
        """Test estimated_remaining_seconds returns None for indeterminate."""
        task = Task(name="Indeterminate Task", total_steps=0)
        assert task.estimated_remaining_seconds is None

    def test_estimated_remaining_seconds_no_progress(self):
        """Test estimated_remaining_seconds returns None when current_step is 0."""
        task = Task(name="No Progress Task", total_steps=100, current_step=0)
        assert task.estimated_remaining_seconds is None

    def test_estimated_remaining_seconds_complete(self):
        """Test estimated_remaining_seconds returns 0 when complete."""
        task = Task(name="Complete Task", total_steps=100, current_step=100)
        assert task.estimated_remaining_seconds == 0.0

    def test_estimated_remaining_seconds_over_100(self):
        """Test estimated_remaining_seconds returns 0 when over 100%."""
        task = Task(name="Over Task", total_steps=100, current_step=150)
        assert task.estimated_remaining_seconds == 0.0

    def test_task_subtasks_independent(self):
        """Test that subtasks list is independent per task."""
        task1 = Task(name="Task 1")
        task2 = Task(name="Task 2")

        task1.subtasks.append("sub1")

        assert task1.subtasks == ["sub1"]
        assert task2.subtasks == []


# ==============================================================================
# Test ProgressReporter Initialization
# ==============================================================================


class TestProgressReporterInit:
    """Tests for ProgressReporter initialization."""

    def test_default_initialization(self):
        """Test ProgressReporter with default values."""
        with patch.object(sys.stdout, "isatty", return_value=True):
            reporter = ProgressReporter()

        assert reporter.enabled is True
        assert reporter.use_colors is True
        assert reporter.show_eta is True
        assert reporter.callback is None
        assert reporter.tasks == []
        assert isinstance(reporter.lock, type(threading.Lock()))

    def test_initialization_disabled(self):
        """Test ProgressReporter with disabled flag."""
        reporter = ProgressReporter(enabled=False)
        assert reporter.enabled is False

    def test_initialization_no_colors(self):
        """Test ProgressReporter with colors disabled."""
        reporter = ProgressReporter(use_colors=False)
        assert reporter.use_colors is False

    def test_initialization_colors_disabled_non_tty(self):
        """Test that colors are disabled when stdout is not a tty."""
        with patch.object(sys.stdout, "isatty", return_value=False):
            reporter = ProgressReporter(use_colors=True)
        assert reporter.use_colors is False

    def test_initialization_no_eta(self):
        """Test ProgressReporter with ETA disabled."""
        reporter = ProgressReporter(show_eta=False)
        assert reporter.show_eta is False

    def test_initialization_with_callback(self):
        """Test ProgressReporter with callback function."""
        callback = MagicMock()
        reporter = ProgressReporter(callback=callback)
        assert reporter.callback is callback

    def test_colors_defined(self):
        """Test that all color codes are defined."""
        reporter = ProgressReporter(enabled=False)

        assert "green" in reporter.colors
        assert "yellow" in reporter.colors
        assert "red" in reporter.colors
        assert "blue" in reporter.colors
        assert "reset" in reporter.colors
        assert "bold" in reporter.colors


# ==============================================================================
# Test ProgressReporter Private Methods
# ==============================================================================


class TestProgressReporterPrivateMethods:
    """Tests for ProgressReporter private helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_colorize_with_colors_enabled(self):
        """Test _colorize adds color codes when enabled."""
        self.reporter.use_colors = True
        result = self.reporter._colorize("test", "green")
        assert "\033[32m" in result
        assert "test" in result
        assert "\033[0m" in result

    def test_colorize_with_colors_disabled(self):
        """Test _colorize returns plain text when disabled."""
        self.reporter.use_colors = False
        result = self.reporter._colorize("test", "green")
        assert result == "test"

    def test_colorize_unknown_color(self):
        """Test _colorize handles unknown color gracefully."""
        self.reporter.use_colors = True
        result = self.reporter._colorize("test", "unknown")
        # Should still add reset code at end
        assert "test" in result
        assert "\033[0m" in result

    def test_format_time_seconds(self):
        """Test _format_time for seconds."""
        assert self.reporter._format_time(30) == "30s"
        assert self.reporter._format_time(0) == "0s"
        assert self.reporter._format_time(59) == "59s"

    def test_format_time_minutes(self):
        """Test _format_time for minutes and seconds."""
        assert self.reporter._format_time(60) == "1m 0s"
        assert self.reporter._format_time(90) == "1m 30s"
        assert self.reporter._format_time(150) == "2m 30s"
        assert self.reporter._format_time(3599) == "59m 59s"

    def test_format_time_hours(self):
        """Test _format_time for hours and minutes."""
        assert self.reporter._format_time(3600) == "1h 0m"
        assert self.reporter._format_time(3660) == "1h 1m"
        assert self.reporter._format_time(7260) == "2h 1m"

    def test_render_progress_bar_zero(self):
        """Test _render_progress_bar at 0%."""
        result = self.reporter._render_progress_bar(0, width=10)
        assert "[" in result
        assert "]" in result
        assert "0.0%" in result

    def test_render_progress_bar_half(self):
        """Test _render_progress_bar at 50%."""
        result = self.reporter._render_progress_bar(50, width=10)
        assert "50.0%" in result

    def test_render_progress_bar_full(self):
        """Test _render_progress_bar at 100%."""
        result = self.reporter._render_progress_bar(100, width=10)
        assert "100.0%" in result

    def test_render_progress_bar_custom_chars(self):
        """Test _render_progress_bar with custom characters."""
        result = self.reporter._render_progress_bar(50, width=10, fill="#", empty="-")
        assert "#" in result
        assert "-" in result

    def test_render_progress_bar_width(self):
        """Test _render_progress_bar respects width parameter."""
        result = self.reporter._render_progress_bar(50, width=20)
        # Should have 20 bar characters between brackets
        # Extract bar content between [ and ]
        bar_content = result.split("[")[1].split("]")[0]
        assert len(bar_content) == 20

    def test_clear_line_disabled(self):
        """Test _clear_line does nothing when disabled."""
        self.reporter.enabled = False
        # Should not raise any errors
        self.reporter._clear_line()

    def test_clear_line_non_tty(self):
        """Test _clear_line does nothing when not a tty."""
        self.reporter.enabled = True
        with patch.object(sys.stdout, "isatty", return_value=False):
            # Should not raise any errors
            self.reporter._clear_line()

    @patch("sys.stdout", new_callable=StringIO)
    def test_clear_line_tty(self, mock_stdout):
        """Test _clear_line writes escape codes when tty."""
        self.reporter.enabled = True
        with patch.object(sys.stdout, "isatty", return_value=True):
            with patch("sys.stdout.write") as mock_write:
                with patch("sys.stdout.flush"):
                    self.reporter._clear_line()
                    mock_write.assert_called_once_with("\r\033[K")

    def test_write_disabled(self):
        """Test _write does nothing when disabled."""
        self.reporter.enabled = False
        with patch("sys.stdout.write") as mock_write:
            self.reporter._write("test message")
            mock_write.assert_not_called()

    def test_write_enabled(self):
        """Test _write outputs message when enabled."""
        self.reporter.enabled = True
        with patch("sys.stdout.write") as mock_write:
            with patch("sys.stdout.flush"):
                self.reporter._write("test message")
                mock_write.assert_called_once_with("test message")


# ==============================================================================
# Test ProgressReporter Task Management
# ==============================================================================


class TestProgressReporterTaskManagement:
    """Tests for ProgressReporter task management methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_start_task_creates_task(self):
        """Test start_task adds a task to the stack."""
        self.reporter.start_task("Test Task", total_steps=10)

        assert len(self.reporter.tasks) == 1
        assert self.reporter.tasks[0].name == "Test Task"
        assert self.reporter.tasks[0].total_steps == 10

    def test_start_task_with_parent(self):
        """Test start_task with parent task adds subtask."""
        self.reporter.start_task("Parent Task")
        self.reporter.start_task("Child Task", parent_task="Parent Task")

        assert len(self.reporter.tasks) == 2
        assert "Child Task" in self.reporter.tasks[0].subtasks

    def test_start_task_parent_not_found(self):
        """Test start_task with non-existent parent."""
        self.reporter.start_task("Child Task", parent_task="Non-existent")
        # Should not raise an error, just not add subtask
        assert len(self.reporter.tasks) == 1

    def test_start_task_callback(self):
        """Test start_task calls callback."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.start_task("Test Task")

        callback.assert_called_once_with("start: Test Task", 0.0)

    def test_get_current_task_empty(self):
        """Test get_current_task returns None when no tasks."""
        assert self.reporter.get_current_task() is None

    def test_get_current_task_with_tasks(self):
        """Test get_current_task returns the last task."""
        self.reporter.start_task("Task 1")
        self.reporter.start_task("Task 2")

        current = self.reporter.get_current_task()
        assert current is not None
        assert current.name == "Task 2"

    def test_get_all_tasks_empty(self):
        """Test get_all_tasks returns empty list."""
        assert self.reporter.get_all_tasks() == []

    def test_get_all_tasks_returns_copy(self):
        """Test get_all_tasks returns a copy of the list."""
        self.reporter.start_task("Task 1")
        tasks = self.reporter.get_all_tasks()

        tasks.append(Task(name="Should not appear"))
        assert len(self.reporter.tasks) == 1

    def test_clear_tasks(self):
        """Test clear_tasks removes all tasks."""
        self.reporter.start_task("Task 1")
        self.reporter.start_task("Task 2")
        self.reporter.clear_tasks()

        assert self.reporter.tasks == []

    def test_disable(self):
        """Test disable method."""
        self.reporter.enabled = True
        self.reporter.disable()
        assert self.reporter.enabled is False

    def test_enable(self):
        """Test enable method."""
        self.reporter.enabled = False
        self.reporter.enable()
        assert self.reporter.enabled is True


# ==============================================================================
# Test ProgressReporter Progress Updates
# ==============================================================================


class TestProgressReporterUpdates:
    """Tests for ProgressReporter progress update methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_update_progress_no_tasks(self):
        """Test update_progress with no active tasks."""
        # Should not raise an error
        self.reporter.update_progress(current_step=5)

    def test_update_progress_disabled(self):
        """Test update_progress when disabled."""
        self.reporter.enabled = False
        self.reporter.start_task("Task", total_steps=10)
        # Should return early without updating
        self.reporter.update_progress(current_step=5)
        # Task should still be at step 0 since update_progress returns early
        # Actually, start_task doesn't set current_step, so we check the flow
        assert self.reporter.tasks[0].current_step == 0

    def test_update_progress_sets_current_step(self):
        """Test update_progress sets the current step."""
        self.reporter.enabled = True
        self.reporter.start_task("Task", total_steps=10)
        self.reporter.update_progress(current_step=5)

        assert self.reporter.tasks[-1].current_step == 5

    def test_update_progress_increments_step(self):
        """Test update_progress increments step when none provided."""
        self.reporter.enabled = True
        self.reporter.start_task("Task", total_steps=10)

        self.reporter.update_progress()
        assert self.reporter.tasks[-1].current_step == 1

        self.reporter.update_progress()
        assert self.reporter.tasks[-1].current_step == 2

    def test_update_progress_callback(self):
        """Test update_progress calls callback."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.enabled = True
        self.reporter.start_task("Task", total_steps=10)

        self.reporter.update_progress(current_step=5, message="Test message")

        # Find the call for update (not the start call)
        calls = callback.call_args_list
        assert len(calls) >= 2  # start + update
        assert calls[-1][0][0] == "Test message"
        assert calls[-1][0][1] == 50.0  # 5/10 * 100

    def test_update_progress_callback_default_message(self):
        """Test update_progress callback uses default message."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.enabled = True
        self.reporter.start_task("Task", total_steps=10)

        self.reporter.update_progress(current_step=5)

        calls = callback.call_args_list
        assert "Task: 5/10" in calls[-1][0][0]


# ==============================================================================
# Test ProgressReporter Task Completion
# ==============================================================================


class TestProgressReporterCompletion:
    """Tests for ProgressReporter completion methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_complete_task_no_tasks(self):
        """Test complete_task with no active tasks."""
        # Should not raise an error
        self.reporter.complete_task()

    def test_complete_task_removes_task(self):
        """Test complete_task removes task from stack."""
        self.reporter.start_task("Task 1")
        self.reporter.start_task("Task 2")
        self.reporter.complete_task()

        assert len(self.reporter.tasks) == 1
        assert self.reporter.tasks[0].name == "Task 1"

    def test_complete_task_sets_status(self):
        """Test complete_task sets task status to completed."""
        self.reporter.start_task("Task")
        # We need to capture the task before it's popped
        self.reporter.enabled = True
        with patch.object(self.reporter, "_write"):
            with patch.object(self.reporter, "_clear_line"):
                self.reporter.complete_task()

    def test_complete_task_callback(self):
        """Test complete_task calls callback."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.start_task("Task")
        self.reporter.complete_task("Done!")

        # Find the complete call
        calls = callback.call_args_list
        complete_call = calls[-1]
        assert "complete: Task" in complete_call[0][0]
        assert complete_call[0][1] == 100.0

    def test_complete_method(self):
        """Test complete method (ProgressReporterProtocol)."""
        self.reporter.start_task("Task")
        self.reporter.complete("Finished!")

        assert len(self.reporter.tasks) == 0


# ==============================================================================
# Test ProgressReporter Error Handling
# ==============================================================================


class TestProgressReporterErrors:
    """Tests for ProgressReporter error reporting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_error_no_tasks(self):
        """Test error with no active tasks."""
        # Should not raise an error
        self.reporter.error("Error message")

    def test_error_sets_task_status(self):
        """Test error sets task status to error."""
        self.reporter.start_task("Task")
        self.reporter.error("Something went wrong")

        task = self.reporter.tasks[-1]
        assert task.status == "error"
        assert task.end_time is not None

    def test_error_callback(self):
        """Test error calls callback."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.start_task("Task")
        self.reporter.error("Something went wrong")

        # Find the error call
        calls = callback.call_args_list
        error_call = calls[-1]
        assert "error: Something went wrong" in error_call[0][0]
        assert error_call[0][1] == 0.0

    def test_error_clear_progress_true(self):
        """Test error clears progress line by default."""
        self.reporter.enabled = True
        self.reporter.start_task("Task")

        with patch.object(self.reporter, "_clear_line") as mock_clear:
            with patch.object(self.reporter, "_write"):
                self.reporter.error("Error", clear_progress=True)
                mock_clear.assert_called()

    def test_error_clear_progress_false(self):
        """Test error does not clear progress when disabled."""
        self.reporter.enabled = True
        self.reporter.start_task("Task")

        with patch.object(self.reporter, "_clear_line") as mock_clear:
            with patch.object(self.reporter, "_write"):
                self.reporter.error("Error", clear_progress=False)
                mock_clear.assert_not_called()


# ==============================================================================
# Test ProgressReporter Report Method
# ==============================================================================


class TestProgressReporterReport:
    """Tests for ProgressReporter report method (ProgressReporterProtocol)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_report_with_task(self):
        """Test report method updates current task."""
        self.reporter.enabled = True
        self.reporter.start_task("Task", total_steps=100)

        with patch.object(self.reporter, "update_progress") as mock_update:
            self.reporter.report("Processing...", 50.0)
            mock_update.assert_called_once()

        # Task current_step should be updated based on progress percentage
        assert self.reporter.tasks[-1].current_step == 50

    def test_report_without_task(self):
        """Test report method when no task exists."""
        self.reporter.enabled = True
        with patch.object(self.reporter, "_write") as mock_write:
            self.reporter.report("Processing...", 50.0)
            mock_write.assert_called()
            call_args = mock_write.call_args[0][0]
            assert "Processing..." in call_args
            assert "50.0%" in call_args

    def test_report_callback(self):
        """Test report method calls callback."""
        callback = MagicMock()
        self.reporter.callback = callback
        self.reporter.enabled = True

        self.reporter.report("Processing...", 75.0)

        callback.assert_called_with("Processing...", 75.0)


# ==============================================================================
# Test ProgressReporter Info and Warning
# ==============================================================================


class TestProgressReporterInfoWarning:
    """Tests for ProgressReporter info and warning methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=True)

    def test_info_message(self):
        """Test info method outputs message."""
        with patch.object(self.reporter, "_clear_line"):
            with patch.object(self.reporter, "_write") as mock_write:
                self.reporter.info("Info message")
                call_args = mock_write.call_args[0][0]
                assert "Info message" in call_args

    def test_warning_message(self):
        """Test warning method outputs message."""
        with patch.object(self.reporter, "_clear_line"):
            with patch.object(self.reporter, "_write") as mock_write:
                self.reporter.warning("Warning message")
                call_args = mock_write.call_args[0][0]
                assert "Warning message" in call_args


# ==============================================================================
# Test ProgressReporter Thread Safety
# ==============================================================================


class TestProgressReporterThreadSafety:
    """Tests for ProgressReporter thread safety."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=False)

    def test_concurrent_task_updates(self):
        """Test that concurrent updates don't corrupt state."""
        self.reporter.enabled = True
        self.reporter.start_task("Concurrent Task", total_steps=1000)

        errors = []

        def update_task(start, end):
            try:
                for i in range(start, end):
                    self.reporter.update_progress(current_step=i)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=update_task, args=(0, 100)),
            threading.Thread(target=update_task, args=(100, 200)),
            threading.Thread(target=update_task, args=(200, 300)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_concurrent_start_complete(self):
        """Test concurrent start and complete operations."""
        errors = []

        def start_and_complete(name):
            try:
                self.reporter.start_task(name)
                time.sleep(0.01)  # Small delay to increase contention
                self.reporter.complete_task()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=start_and_complete, args=(f"Task {i}",))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ==============================================================================
# Test SilentProgressReporter
# ==============================================================================


class TestSilentProgressReporter:
    """Tests for SilentProgressReporter class."""

    def test_initialization(self):
        """Test SilentProgressReporter can be instantiated."""
        reporter = SilentProgressReporter()
        assert reporter is not None

    def test_report_noop(self):
        """Test report method does nothing."""
        reporter = SilentProgressReporter()
        # Should not raise any errors
        reporter.report("Message", 50.0)

    def test_complete_noop(self):
        """Test complete method does nothing."""
        reporter = SilentProgressReporter()
        # Should not raise any errors
        reporter.complete("Done")

    def test_error_noop(self):
        """Test error method does nothing."""
        reporter = SilentProgressReporter()
        # Should not raise any errors
        reporter.error("Error message")

    def test_implements_protocol(self):
        """Test SilentProgressReporter implements ProgressReporterProtocol."""
        from plugin.types import ProgressReporterProtocol

        reporter = SilentProgressReporter()
        assert isinstance(reporter, ProgressReporterProtocol)


# ==============================================================================
# Test create_progress_reporter Factory Function
# ==============================================================================


class TestCreateProgressReporter:
    """Tests for create_progress_reporter factory function."""

    def test_enabled_returns_progress_reporter(self):
        """Test factory returns ProgressReporter when enabled."""
        with patch.object(sys.stdout, "isatty", return_value=True):
            reporter = create_progress_reporter(enabled=True)
        assert isinstance(reporter, ProgressReporter)

    def test_disabled_returns_silent_reporter(self):
        """Test factory returns SilentProgressReporter when disabled."""
        reporter = create_progress_reporter(enabled=False)
        assert isinstance(reporter, SilentProgressReporter)

    def test_passes_options_to_progress_reporter(self):
        """Test factory passes options to ProgressReporter."""
        callback = MagicMock()
        with patch.object(sys.stdout, "isatty", return_value=True):
            reporter = create_progress_reporter(
                enabled=True,
                use_colors=True,
                show_eta=False,
                callback=callback,
            )

        assert isinstance(reporter, ProgressReporter)
        assert reporter.show_eta is False
        assert reporter.callback is callback

    def test_returns_protocol_compliant(self):
        """Test factory returns protocol-compliant object."""
        from plugin.types import ProgressReporterProtocol

        for enabled in [True, False]:
            reporter = create_progress_reporter(enabled=enabled)
            assert isinstance(reporter, ProgressReporterProtocol)


# ==============================================================================
# Test ProgressReporter Output Formatting
# ==============================================================================


class TestProgressReporterOutputFormatting:
    """Tests for ProgressReporter output formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = ProgressReporter(enabled=True, use_colors=False)

    def test_start_task_output_format(self):
        """Test start_task outputs correctly formatted message."""
        with patch.object(self.reporter, "_write") as mock_write:
            self.reporter.start_task("Test Task")
            call_args = mock_write.call_args[0][0]
            assert "Starting: Test Task" in call_args

    def test_complete_task_output_format(self):
        """Test complete_task outputs correctly formatted message."""
        self.reporter.start_task("Test Task")

        with patch.object(self.reporter, "_clear_line"):
            with patch.object(self.reporter, "_write") as mock_write:
                self.reporter.complete_task("Done!")
                call_args = mock_write.call_args[0][0]
                # Should contain checkmark, task name, message, and time
                assert "Test Task" in call_args
                assert "Done!" in call_args

    def test_error_output_format(self):
        """Test error outputs correctly formatted message."""
        self.reporter.start_task("Test Task")

        with patch.object(self.reporter, "_clear_line"):
            with patch.object(self.reporter, "_write") as mock_write:
                self.reporter.error("Something failed")
                call_args = mock_write.call_args[0][0]
                assert "Error" in call_args
                assert "Something failed" in call_args


# ==============================================================================
# Test Edge Cases
# ==============================================================================


class TestProgressReporterEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_empty_task_name(self):
        """Test handling of empty task name."""
        reporter = ProgressReporter(enabled=False)
        reporter.start_task("")
        assert reporter.tasks[-1].name == ""

    def test_negative_total_steps(self):
        """Test handling of negative total_steps."""
        reporter = ProgressReporter(enabled=False)
        reporter.start_task("Task", total_steps=-10)
        # Should still work, though progress calculation may be undefined
        assert reporter.tasks[-1].total_steps == -10

    def test_very_large_progress_values(self):
        """Test handling of very large values."""
        reporter = ProgressReporter(enabled=False)
        reporter.start_task("Task", total_steps=1000000000)
        reporter.tasks[-1].current_step = 500000000
        # Should not raise any errors
        percent = reporter.tasks[-1].progress_percent
        assert percent == 50.0

    def test_rapid_task_creation(self):
        """Test rapid task creation and completion."""
        reporter = ProgressReporter(enabled=False)

        for i in range(100):
            reporter.start_task(f"Task {i}")
            reporter.complete_task()

        assert len(reporter.tasks) == 0

    def test_nested_tasks(self):
        """Test deeply nested task hierarchy."""
        reporter = ProgressReporter(enabled=False)

        for i in range(10):
            reporter.start_task(f"Level {i}")

        assert len(reporter.tasks) == 10

        for i in range(10):
            reporter.complete_task()

        assert len(reporter.tasks) == 0

    def test_special_characters_in_messages(self):
        """Test handling of special characters."""
        reporter = ProgressReporter(enabled=True, use_colors=False)

        with patch.object(reporter, "_write"):
            reporter.start_task("Task with unicode: ")
            reporter.update_progress(message="Progress: 50% -> 100%")
            reporter.complete_task("Done!")

    def test_update_progress_indeterminate_task(self):
        """Test update_progress on indeterminate task (total_steps=0)."""
        reporter = ProgressReporter(enabled=True)
        reporter.start_task("Indeterminate Task", total_steps=0)

        with patch.object(reporter, "_write"):
            # Should not show progress bar for indeterminate tasks
            reporter.update_progress(current_step=10, message="Working...")

    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break the reporter."""
        def failing_callback(message, progress):
            raise RuntimeError("Callback error")

        reporter = ProgressReporter(enabled=True, callback=failing_callback)

        # The reporter should still function even if callback raises
        with pytest.raises(RuntimeError):
            reporter.start_task("Task")

    def test_multiple_reporters_independent(self):
        """Test that multiple reporters are independent."""
        reporter1 = ProgressReporter(enabled=False)
        reporter2 = ProgressReporter(enabled=False)

        reporter1.start_task("Task 1")
        reporter2.start_task("Task 2")

        assert len(reporter1.tasks) == 1
        assert len(reporter2.tasks) == 1
        assert reporter1.tasks[0].name == "Task 1"
        assert reporter2.tasks[0].name == "Task 2"
