"""
Unit tests for CheckpointHandler.

Tests the checkpoint system for user interaction during workflows.
"""

from plugin.checkpoint_handler import (
    BatchCheckpointHandler,
    CheckpointDecision,
    CheckpointHandler,
)


class TestCheckpointHandler:
    """Tests for CheckpointHandler."""

    def test_interactive_mode_prompts_user(self, mocker):
        """Test that interactive mode prompts for user input."""
        mock_input = mocker.patch("builtins.input", return_value="1")
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(
            phase_name="Test Phase",
            phase_result={"test": "data"},
            artifacts=["test.json"],
        )

        # Should have prompted for input
        mock_input.assert_called()
        assert result.decision == CheckpointDecision.CONTINUE

    def test_non_interactive_mode_auto_approves(self):
        """Test that non-interactive mode with auto_approve=True continues."""
        handler = CheckpointHandler(interactive=False, auto_approve=True)

        result = handler.checkpoint(
            phase_name="Test Phase", phase_result={"test": "data"}
        )

        assert result.decision == CheckpointDecision.CONTINUE
        assert "Auto-approved" in result.feedback

    def test_non_interactive_mode_aborts_without_approval(self):
        """Test that non-interactive mode without auto_approve aborts."""
        handler = CheckpointHandler(interactive=False, auto_approve=False)

        result = handler.checkpoint(
            phase_name="Test Phase", phase_result={"test": "data"}
        )

        assert result.decision == CheckpointDecision.ABORT

    def test_checkpoint_continue_decision(self, mocker):
        """Test user choosing to continue."""
        mocker.patch("builtins.input", return_value="1")
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        assert result.decision == CheckpointDecision.CONTINUE

    def test_checkpoint_retry_decision(self, mocker):
        """Test user choosing to retry."""
        inputs = iter(["2", "Change something"])
        mocker.patch("builtins.input", side_effect=inputs)
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        assert result.decision == CheckpointDecision.RETRY
        assert result.feedback == "Change something"
        assert result.modifications is not None

    def test_checkpoint_modify_decision(self, mocker):
        """Test user choosing to modify."""
        inputs = iter(["3", ""])  # Modify, then Enter to continue
        mocker.patch("builtins.input", side_effect=inputs)
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        assert result.decision == CheckpointDecision.MODIFY

    def test_checkpoint_abort_decision(self, mocker):
        """Test user choosing to abort."""
        inputs = iter(["4", "User cancelled"])
        mocker.patch("builtins.input", side_effect=inputs)
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        assert result.decision == CheckpointDecision.ABORT
        assert result.feedback == "User cancelled"

    def test_checkpoint_default_is_continue(self, mocker):
        """Test that pressing Enter defaults to continue."""
        mocker.patch("builtins.input", return_value="")
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        assert result.decision == CheckpointDecision.CONTINUE

    def test_display_result_summary(self, mocker, capsys):
        """Test that result summary is displayed correctly."""
        mocker.patch("builtins.input", return_value="1")
        handler = CheckpointHandler(interactive=True)

        handler.checkpoint(
            phase_name="Test Phase", phase_result={"result": "success", "count": 10}
        )

        captured = capsys.readouterr()
        assert "result: success" in captured.out
        assert "count: 10" in captured.out

    def test_display_artifacts(self, mocker, capsys):
        """Test that artifacts are displayed."""
        mocker.patch("builtins.input", return_value="1")
        handler = CheckpointHandler(interactive=True)

        handler.checkpoint(
            phase_name="Test Phase",
            phase_result={},
            artifacts=["file1.json", "file2.md"],
        )

        captured = capsys.readouterr()
        assert "file1.json" in captured.out
        assert "file2.md" in captured.out

    def test_display_suggestions(self, mocker, capsys):
        """Test that suggestions are displayed."""
        mocker.patch("builtins.input", return_value="1")
        handler = CheckpointHandler(interactive=True)

        handler.checkpoint(
            phase_name="Test Phase",
            phase_result={},
            suggestions=["Review the output", "Check for errors"],
        )

        captured = capsys.readouterr()
        assert "Review the output" in captured.out
        assert "Check for errors" in captured.out

    def test_confirm_action_yes(self, mocker):
        """Test confirm_action with yes."""
        mocker.patch("builtins.input", return_value="y")
        handler = CheckpointHandler(interactive=True)

        result = handler.confirm_action("Delete files?")

        assert result is True

    def test_confirm_action_no(self, mocker):
        """Test confirm_action with no."""
        mocker.patch("builtins.input", return_value="n")
        handler = CheckpointHandler(interactive=True)

        result = handler.confirm_action("Delete files?")

        assert result is False

    def test_confirm_action_default(self, mocker):
        """Test confirm_action with default."""
        mocker.patch("builtins.input", return_value="")
        handler = CheckpointHandler(interactive=True)

        result = handler.confirm_action("Proceed?", default=True)

        assert result is True

    def test_confirm_action_non_interactive(self):
        """Test confirm_action in non-interactive mode."""
        handler = CheckpointHandler(interactive=False, auto_approve=True)

        result = handler.confirm_action("Proceed?")

        assert result is True

    def test_show_message(self, capsys):
        """Test show_message displays correctly."""
        handler = CheckpointHandler(interactive=True)

        handler.show_message("Test message", "info")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_show_message_types(self, capsys):
        """Test different message types display correctly."""
        handler = CheckpointHandler(interactive=True)

        handler.show_message("Info message", "info")
        handler.show_message("Warning message", "warning")
        handler.show_message("Error message", "error")
        handler.show_message("Success message", "success")

        captured = capsys.readouterr()
        assert "Info message" in captured.out
        assert "Warning message" in captured.out
        assert "Error message" in captured.out
        assert "Success message" in captured.out

    def test_show_progress(self, capsys):
        """Test show_progress displays correctly."""
        handler = CheckpointHandler(interactive=True)

        handler.show_progress(5, 10, "Processing...")

        captured = capsys.readouterr()
        assert "50%" in captured.out
        assert "Processing..." in captured.out

    def test_show_progress_complete(self, capsys):
        """Test show_progress at 100%."""
        handler = CheckpointHandler(interactive=True)

        handler.show_progress(10, 10, "Done")

        captured = capsys.readouterr()
        assert "100%" in captured.out

    def test_parse_retry_feedback(self):
        """Test parsing user feedback into modifications."""
        handler = CheckpointHandler(interactive=True)

        result = handler._parse_retry_feedback("Change the research sources")

        assert result["user_feedback"] == "Change the research sources"
        assert "area" in result
        assert result["area"] == "research"

    def test_parse_retry_feedback_content(self):
        """Test parsing feedback about content."""
        handler = CheckpointHandler(interactive=True)

        result = handler._parse_retry_feedback("Update the content quality")

        assert result["area"] == "content"

    def test_invalid_choice_uses_default(self, mocker):
        """Test that invalid choice defaults to continue."""
        mocker.patch("builtins.input", return_value="99")
        handler = CheckpointHandler(interactive=True)

        result = handler.checkpoint(phase_name="Test Phase", phase_result={})

        # Invalid choice should default to continue
        assert result.decision == CheckpointDecision.CONTINUE


class TestBatchCheckpointHandler:
    """Tests for BatchCheckpointHandler."""

    def test_batch_accumulation(self, mocker):
        """Test that checkpoints are batched."""
        mocker.patch("builtins.input", return_value="1")
        handler = BatchCheckpointHandler(batch_size=3, interactive=True)

        # Add 2 checkpoints
        result1 = handler.checkpoint("Phase 1", {})
        result2 = handler.checkpoint("Phase 2", {})

        # Both should auto-continue (batched)
        assert result1.decision == CheckpointDecision.CONTINUE
        assert result2.decision == CheckpointDecision.CONTINUE
        assert "Batched" in result1.feedback

    def test_batch_flush_when_full(self, mocker, capsys):
        """Test that batch flushes when reaching batch_size."""
        mocker.patch("builtins.input", return_value="1")
        handler = BatchCheckpointHandler(batch_size=2, interactive=True)

        # Add checkpoints until batch is full
        handler.checkpoint("Phase 1", {})
        handler.checkpoint("Phase 2", {})  # This should trigger flush

        captured = capsys.readouterr()
        # Should show batch review
        assert "Batch Review" in captured.out or "BATCH" in captured.out

    def test_manual_flush(self, mocker, capsys):
        """Test manually flushing batch."""
        mocker.patch("builtins.input", return_value="1")
        handler = BatchCheckpointHandler(batch_size=5, interactive=True)

        # Add some checkpoints
        handler.checkpoint("Phase 1", {})
        handler.checkpoint("Phase 2", {})

        # Manually flush
        result = handler.flush_batch()

        captured = capsys.readouterr()
        assert "Phase 1" in captured.out
        assert "Phase 2" in captured.out
        assert result.decision == CheckpointDecision.CONTINUE

    def test_batch_displays_all_checkpoints(self, mocker, capsys):
        """Test that all batched checkpoints are displayed."""
        mocker.patch("builtins.input", return_value="1")
        handler = BatchCheckpointHandler(batch_size=2, interactive=True)

        handler.checkpoint("Phase 1", {}, artifacts=["file1.json"])
        handler.checkpoint("Phase 2", {}, artifacts=["file2.json"])

        captured = capsys.readouterr()
        # Should show both phases
        assert "Phase 1" in captured.out
        assert "Phase 2" in captured.out

    def test_empty_batch_flush(self):
        """Test flushing empty batch."""
        handler = BatchCheckpointHandler(batch_size=5, interactive=False)

        result = handler.flush_batch()

        # Should return continue decision
        assert result.decision == CheckpointDecision.CONTINUE

    def test_batch_clears_after_flush(self, mocker):
        """Test that batch is cleared after flush."""
        mocker.patch("builtins.input", return_value="1")
        handler = BatchCheckpointHandler(batch_size=2, interactive=True)

        # Fill and flush batch
        handler.checkpoint("Phase 1", {})
        handler.checkpoint("Phase 2", {})

        # pending_checkpoints should be cleared
        assert len(handler.pending_checkpoints) == 0
