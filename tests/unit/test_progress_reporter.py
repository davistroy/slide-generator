"""
Unit tests for progress reporter module.
"""

import pytest
import json
import io
import sys
from unittest.mock import patch

from plugin.lib.progress_reporter import (
    ProgressReporter, ProgressStatus, report_progress
)


class TestProgressStatus:
    """Tests for ProgressStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert ProgressStatus.STARTED.value == "started"
        assert ProgressStatus.IN_PROGRESS.value == "in_progress"
        assert ProgressStatus.CHECKPOINT.value == "checkpoint"
        assert ProgressStatus.COMPLETED.value == "completed"
        assert ProgressStatus.FAILED.value == "failed"
        assert ProgressStatus.SKIPPED.value == "skipped"


class TestProgressReporter:
    """Tests for ProgressReporter class."""

    def test_initialization(self):
        """Test reporter initialization."""
        reporter = ProgressReporter("test-workflow", 5)
        assert reporter.workflow_name == "test-workflow"
        assert reporter.total_steps == 5
        assert reporter.current_step == 0

    def test_start_workflow(self, capsys):
        """Test start_workflow emits correct JSON."""
        reporter = ProgressReporter("test", 3)

        # Capture stderr
        reporter.start_workflow()
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["type"] == "slide_generator_progress"
        assert output["status"] == "started"
        assert output["workflow"] == "test"
        assert output["total_steps"] == 3

    def test_start_step(self, capsys):
        """Test start_step emits correct JSON."""
        reporter = ProgressReporter("test", 4)

        reporter.start_step("Research", 1)
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "in_progress"
        assert output["step"] == 1
        assert output["step_name"] == "Research"
        assert output["total_steps"] == 4
        assert output["progress_percent"] == 0  # (1-1)/4 * 100

    def test_complete_step(self, capsys):
        """Test complete_step emits correct JSON."""
        reporter = ProgressReporter("test", 4)

        reporter.complete_step("Research", 1, {"output": "research.json"})
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "completed"
        assert output["step"] == 1
        assert output["artifacts"] == {"output": "research.json"}
        assert output["progress_percent"] == 25

    def test_checkpoint(self, capsys):
        """Test checkpoint emits correct JSON."""
        reporter = ProgressReporter("test", 4)

        reporter.checkpoint("Review", 2, "Please review research", requires_approval=True)
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "checkpoint"
        assert output["requires_approval"] is True
        assert "Please review research" in output["message"]

    def test_fail_step(self, capsys):
        """Test fail_step emits correct JSON."""
        reporter = ProgressReporter("test", 4)

        reporter.fail_step("API Call", 2, "Connection timeout", recoverable=True)
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "failed"
        assert output["error"] == "Connection timeout"
        assert output["recoverable"] is True

    def test_complete_workflow(self, capsys):
        """Test complete_workflow emits correct JSON."""
        reporter = ProgressReporter("test", 4)

        reporter.complete_workflow("output.pptx")
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "completed"
        assert output["progress_percent"] == 100
        assert output["output_file"] == "output.pptx"
        assert "elapsed_seconds" in output


class TestReportProgressFunction:
    """Tests for standalone report_progress function."""

    def test_basic_progress(self, capsys):
        """Test basic progress reporting."""
        report_progress(2, 5, "Processing slides")
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["step"] == 2
        assert output["total_steps"] == 5
        assert output["message"] == "Processing slides"
        assert output["progress_percent"] == 40

    def test_progress_with_status(self, capsys):
        """Test progress with custom status."""
        report_progress(3, 3, "Done!", status="completed")
        captured = capsys.readouterr()

        output = json.loads(captured.err.strip())
        assert output["status"] == "completed"
        assert output["progress_percent"] == 100
