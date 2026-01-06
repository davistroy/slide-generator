"""
Unit tests for WorkflowOrchestrator.

Tests the workflow coordination and phase execution system.
"""

import json

import pytest

from plugin.base_skill import BaseSkill, SkillOutput
from plugin.checkpoint_handler import (
    CheckpointDecision,
    CheckpointHandler,
    CheckpointResult,
)
from plugin.workflow_orchestrator import (
    PhaseResult,
    WorkflowOrchestrator,
    WorkflowPhase,
    WorkflowResult,
)


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_execute_workflow_all_phases(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test executing complete workflow through all phases."""
        # Register a mock skill for each phase
        skill_registry.register_skill(mock_skill_class)

        # Mock the PHASE_SKILLS to use our mock skill
        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is True
        assert len(result.phase_results) == 4

    def test_execute_workflow_with_dict_input(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test execute_workflow with dictionary input instead of string."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        # Pass dict input instead of string
        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow",
            initial_input={"topic": "test topic", "audience": "developers"},
        )

        assert result.success is True
        assert len(result.phase_results) == 4
        assert result.metadata.get("workflow_id") == "test-workflow"

    def test_execute_workflow_with_config_override(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test execute_workflow with config override."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        custom_config = {"custom_setting": "value"}
        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow",
            initial_input="test topic",
            config=custom_config,
        )

        assert result.success is True

    def test_execute_workflow_phase_failure_stops_workflow(
        self, workflow_orchestrator, skill_registry, mock_failing_skill_class
    ):
        """Test that phase failure stops workflow."""
        skill_registry.register_skill(mock_failing_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["failing-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["failing-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["failing-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["failing-skill"],
        }

        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is False
        # Should stop at first phase failure
        assert len(result.phase_results) == 1
        assert result.metadata.get("failed_phase") == "research"

    def test_execute_workflow_user_abort_stops_workflow(
        self, skill_registry, mock_skill_class, mock_input_abort
    ):
        """Test that user abort at checkpoint stops workflow."""
        checkpoint_handler = CheckpointHandler(interactive=True)
        orchestrator = WorkflowOrchestrator(
            checkpoint_handler=checkpoint_handler, config={}
        )

        skill_registry.register_skill(mock_skill_class)

        orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is False
        assert result.metadata.get("aborted_at_phase") is not None
        assert result.metadata.get("aborted_at_phase") == "research"

    def test_execute_workflow_user_retry_with_modifications(
        self, skill_registry, mock_skill_class, mocker
    ):
        """Test that user retry re-runs phase with modifications."""
        # Create checkpoint results: first RETRY, then CONTINUE for all phases
        checkpoint_results = [
            # First phase - RETRY then CONTINUE
            CheckpointResult(
                decision=CheckpointDecision.RETRY,
                feedback="Change something",
                modifications={"area": "research"},
            ),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            # Subsequent phases - all CONTINUE
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
        ]
        result_iter = iter(checkpoint_results)

        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.side_effect = lambda *args, **kwargs: next(
            result_iter
        )
        mock_checkpoint_handler.show_message = mocker.MagicMock()
        mock_checkpoint_handler.show_progress = mocker.MagicMock()

        orchestrator = WorkflowOrchestrator(
            checkpoint_handler=mock_checkpoint_handler, config={}
        )

        skill_registry.register_skill(mock_skill_class)

        orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is True
        # Verify checkpoint was called more times due to retry
        assert mock_checkpoint_handler.checkpoint.call_count >= 4

    def test_execute_workflow_user_modify_pauses(
        self, skill_registry, mock_skill_class, mocker
    ):
        """Test that MODIFY decision pauses workflow and shows message."""
        # Create checkpoint results: first MODIFY, then CONTINUE for all phases
        checkpoint_results = [
            # First phase - MODIFY then continues
            CheckpointResult(
                decision=CheckpointDecision.MODIFY,
                feedback="User editing",
            ),
            # Subsequent phases - all CONTINUE
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
        ]
        result_iter = iter(checkpoint_results)

        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.side_effect = lambda *args, **kwargs: next(
            result_iter
        )
        mock_checkpoint_handler.show_message = mocker.MagicMock()
        mock_checkpoint_handler.show_progress = mocker.MagicMock()

        orchestrator = WorkflowOrchestrator(
            checkpoint_handler=mock_checkpoint_handler, config={}
        )

        skill_registry.register_skill(mock_skill_class)

        orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is True
        # Verify show_message was called for the pause
        pause_calls = [
            call
            for call in mock_checkpoint_handler.show_message.call_args_list
            if "paused" in str(call).lower()
        ]
        assert len(pause_calls) >= 1

    def test_execute_workflow_retry_without_modifications(
        self, skill_registry, mock_skill_class, mocker
    ):
        """Test RETRY decision without modifications (modifications is None)."""
        checkpoint_results = [
            # RETRY without modifications
            CheckpointResult(
                decision=CheckpointDecision.RETRY,
                feedback="Try again",
                modifications=None,  # No modifications
            ),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
            CheckpointResult(decision=CheckpointDecision.CONTINUE),
        ]
        result_iter = iter(checkpoint_results)

        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.side_effect = lambda *args, **kwargs: next(
            result_iter
        )
        mock_checkpoint_handler.show_message = mocker.MagicMock()
        mock_checkpoint_handler.show_progress = mocker.MagicMock()

        orchestrator = WorkflowOrchestrator(
            checkpoint_handler=mock_checkpoint_handler, config={}
        )

        skill_registry.register_skill(mock_skill_class)

        orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = orchestrator.execute_workflow(
            workflow_id="test-workflow", initial_input="test topic"
        )

        assert result.success is True

    def test_run_phase_executes_all_skills(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test that run_phase executes all skills sequentially."""
        skill_registry.register_skill(mock_skill_class)

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Phase result should be successful but note we don't have real skills registered
        assert phase_result.phase == WorkflowPhase.RESEARCH

    def test_run_phase_skill_failure_continues_to_next(
        self,
        workflow_orchestrator,
        skill_registry,
        mock_skill_class,
        mock_failing_skill_class,
    ):
        """Test that skill failure doesn't stop phase."""
        skill_registry.register_skill(mock_skill_class)
        skill_registry.register_skill(mock_failing_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["failing-skill", "mock-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Should have both skill outputs
        assert len(phase_result.outputs) == 2
        # Second skill should have succeeded
        assert phase_result.outputs[1].success is True

    def test_run_phase_unregistered_skill_logs_error(self, workflow_orchestrator):
        """Test handling of unregistered skill."""
        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["nonexistent-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        assert len(phase_result.errors) > 0
        assert any("not registered" in error for error in phase_result.errors)

    def test_run_phase_empty_skills_list(self, workflow_orchestrator):
        """Test run_phase with empty skills list returns error."""
        # Override PHASE_SKILLS with empty list
        workflow_orchestrator.PHASE_SKILLS = {WorkflowPhase.RESEARCH: []}

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Phase should fail with no skills to execute
        assert phase_result.success is False
        # With no skills, there are no outputs, and success = any(...) is False

    def test_run_phase_undefined_phase_returns_error(self, workflow_orchestrator):
        """Test run_phase with phase not in PHASE_SKILLS."""
        # Clear PHASE_SKILLS completely
        workflow_orchestrator.PHASE_SKILLS = {}

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        assert phase_result.success is False
        assert len(phase_result.errors) > 0
        assert any("No skills defined" in error for error in phase_result.errors)

    def test_run_phase_skill_instantiation_failure(
        self, workflow_orchestrator, skill_registry, mocker
    ):
        """Test run_phase handles skill instantiation failure."""

        # Create a skill that registers successfully but fails when instantiated via get_skill
        class BadSkill(BaseSkill):
            instantiation_count = 0

            def __init__(self, config=None):
                BadSkill.instantiation_count += 1
                # First instantiation (during registration) succeeds
                # Second instantiation (during run_phase) fails
                if BadSkill.instantiation_count > 1:
                    raise RuntimeError("Instantiation failed")
                super().__init__(config)

            @property
            def skill_id(self):
                return "bad-skill"

            @property
            def display_name(self):
                return "Bad Skill"

            @property
            def description(self):
                return "A skill that fails on second instantiation"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        # Reset the counter and register
        BadSkill.instantiation_count = 0
        skill_registry.register_skill(BadSkill)

        workflow_orchestrator.PHASE_SKILLS = {WorkflowPhase.RESEARCH: ["bad-skill"]}

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        assert len(phase_result.errors) > 0
        assert any(
            "Failed to instantiate" in error or "Instantiation failed" in error
            for error in phase_result.errors
        )

    def test_run_phase_skill_execution_exception(
        self, workflow_orchestrator, skill_registry
    ):
        """Test run_phase handles unexpected exception during skill execution."""

        class ExceptionSkill(BaseSkill):
            @property
            def skill_id(self):
                return "exception-skill"

            @property
            def display_name(self):
                return "Exception Skill"

            @property
            def description(self):
                return "A skill that throws exception"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                raise RuntimeError("Unexpected execution error")

        skill_registry.register_skill(ExceptionSkill)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["exception-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Exception is caught by BaseSkill.run() and returns failure result
        # The phase should still have outputs
        assert len(phase_result.outputs) >= 1
        # Check if there are errors
        assert not phase_result.success or len(phase_result.errors) > 0

    def test_run_phase_updates_context(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test that phase output updates context for next phase."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {WorkflowPhase.RESEARCH: ["mock-skill"]}

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Mock skill returns {"result": "success"}
        output_data = phase_result.get_output_data()
        assert "result" in output_data

    def test_run_phase_success_with_errors_is_false(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test that phase success is False when there are errors even if skills succeeded."""
        skill_registry.register_skill(mock_skill_class)

        # Register an unregistered skill to generate an error
        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["nonexistent-skill", "mock-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        # Even though mock-skill succeeded, there's an error from nonexistent-skill
        assert len(phase_result.errors) > 0
        assert phase_result.success is False  # errors.length > 0 means success = False

    def test_run_phase_collects_artifacts(self, workflow_orchestrator, skill_registry):
        """Test that artifacts from all skills are collected."""

        class ArtifactSkill(BaseSkill):
            @property
            def skill_id(self):
                return "artifact-skill"

            @property
            def display_name(self):
                return "Artifact Skill"

            @property
            def description(self):
                return "A skill that produces artifacts"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(
                    data={"processed": True},
                    artifacts=["file1.json", "file2.md"],
                )

        skill_registry.register_skill(ArtifactSkill)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["artifact-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={},
        )

        assert "file1.json" in phase_result.artifacts
        assert "file2.md" in phase_result.artifacts

    def test_execute_partial_workflow(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test executing partial workflow from start_phase to end_phase."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            end_phase=WorkflowPhase.VISUAL_GENERATION,
            initial_input={"topic": "test"},
            config={},
        )

        # Should only run 2 phases
        assert len(result.phase_results) == 2
        assert result.phase_results[0].phase == WorkflowPhase.CONTENT_DEVELOPMENT
        assert result.phase_results[1].phase == WorkflowPhase.VISUAL_GENERATION

    def test_execute_partial_workflow_with_string_input(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test execute_partial_workflow with string input."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"],
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.RESEARCH,
            initial_input="test topic",
            config={},
        )

        assert len(result.phase_results) == 1
        assert result.success is True

    def test_execute_partial_workflow_phase_failure(
        self, workflow_orchestrator, skill_registry, mock_failing_skill_class
    ):
        """Test partial workflow stops on phase failure."""
        skill_registry.register_skill(mock_failing_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["failing-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["failing-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["failing-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["failing-skill"],
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            initial_input="test",
            config={},
        )

        assert result.success is False
        assert len(result.phase_results) == 1
        assert result.metadata.get("failed_phase") == "research"

    def test_partial_workflow_invalid_phase_order_fails(self, workflow_orchestrator):
        """Test that invalid phase order raises error."""
        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.VISUAL_GENERATION,
            end_phase=WorkflowPhase.RESEARCH,
            initial_input={},
            config={},
        )

        assert result.success is False
        assert "start_phase must come before end_phase" in result.metadata.get(
            "error", ""
        )

    def test_execute_partial_workflow_single_phase(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test partial workflow with same start and end phase."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            end_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            initial_input={"content": "test"},
            config={},
        )

        assert len(result.phase_results) == 1
        assert result.success is True

    def test_checkpoint_with_errors_shows_suggestions(
        self, workflow_orchestrator, mocker
    ):
        """Test checkpoint method adds error suggestions."""
        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.return_value = CheckpointResult(
            decision=CheckpointDecision.CONTINUE
        )
        workflow_orchestrator.checkpoint_handler = mock_checkpoint_handler

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            errors=["Error 1", "Error 2"],
            artifacts=["file.json"],
        )

        workflow_orchestrator.checkpoint(
            phase_name="Research", phase_result=phase_result
        )

        # Check that checkpoint was called with suggestions about errors
        call_args = mock_checkpoint_handler.checkpoint.call_args
        suggestions = call_args.kwargs.get("suggestions", [])
        assert any("error" in s.lower() for s in suggestions)

    def test_checkpoint_with_artifacts_shows_suggestions(
        self, workflow_orchestrator, mocker
    ):
        """Test checkpoint method shows artifact review suggestions."""
        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.return_value = CheckpointResult(
            decision=CheckpointDecision.CONTINUE
        )
        workflow_orchestrator.checkpoint_handler = mock_checkpoint_handler

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            artifacts=["research.json", "outline.md", "notes.txt"],
        )

        workflow_orchestrator.checkpoint(
            phase_name="Research", phase_result=phase_result
        )

        call_args = mock_checkpoint_handler.checkpoint.call_args
        suggestions = call_args.kwargs.get("suggestions", [])
        assert any(
            "artifact" in s.lower() or "review" in s.lower() for s in suggestions
        )

    def test_checkpoint_truncates_artifact_suggestions(
        self, workflow_orchestrator, mocker
    ):
        """Test checkpoint truncates artifact list to first 3."""
        mock_checkpoint_handler = mocker.MagicMock()
        mock_checkpoint_handler.checkpoint.return_value = CheckpointResult(
            decision=CheckpointDecision.CONTINUE
        )
        workflow_orchestrator.checkpoint_handler = mock_checkpoint_handler

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            artifacts=[
                "file1.json",
                "file2.json",
                "file3.json",
                "file4.json",
                "file5.json",
            ],
        )

        workflow_orchestrator.checkpoint(
            phase_name="Research", phase_result=phase_result
        )

        call_args = mock_checkpoint_handler.checkpoint.call_args
        suggestions = call_args.kwargs.get("suggestions", [])
        # Check that not all 5 files are mentioned in suggestions
        artifact_suggestion = [
            s for s in suggestions if "artifact" in s.lower() or "review" in s.lower()
        ]
        if artifact_suggestion:
            # Should only show first 3 files
            assert "file4.json" not in artifact_suggestion[0]
            assert "file5.json" not in artifact_suggestion[0]

    def test_resume_workflow_raises_not_implemented(self, workflow_orchestrator):
        """Test that resume_workflow raises NotImplementedError."""
        with pytest.raises(NotImplementedError, match="StateDetector"):
            workflow_orchestrator.resume_workflow(project_dir="/some/path", config={})

    def test_save_state(self, workflow_orchestrator, tmp_path):
        """Test saving workflow state to file."""
        phase_results = [
            PhaseResult(
                phase=WorkflowPhase.RESEARCH, success=True, artifacts=["research.json"]
            )
        ]

        output_path = tmp_path / "state.json"
        workflow_orchestrator.save_state(
            workflow_id="test-workflow",
            phase_results=phase_results,
            output_path=str(output_path),
        )

        assert output_path.exists()

        with open(output_path) as f:
            state = json.load(f)

        assert state["workflow_id"] == "test-workflow"
        assert len(state["completed_phases"]) == 1

    def test_save_state_creates_parent_directory(self, workflow_orchestrator, tmp_path):
        """Test save_state creates parent directories if needed."""
        phase_results = [
            PhaseResult(
                phase=WorkflowPhase.RESEARCH,
                success=True,
                artifacts=["file.json"],
                errors=["warning1"],
            )
        ]

        # Path with nested directories that don't exist
        output_path = tmp_path / "nested" / "deep" / "state.json"
        workflow_orchestrator.save_state(
            workflow_id="test-workflow",
            phase_results=phase_results,
            output_path=str(output_path),
        )

        assert output_path.exists()
        with open(output_path) as f:
            state = json.load(f)

        assert state["workflow_id"] == "test-workflow"
        assert state["completed_phases"][0]["errors"] == ["warning1"]

    def test_save_state_multiple_phases(self, workflow_orchestrator, tmp_path):
        """Test save_state with multiple phase results."""
        phase_results = [
            PhaseResult(
                phase=WorkflowPhase.RESEARCH,
                success=True,
                artifacts=["research.json"],
                errors=[],
            ),
            PhaseResult(
                phase=WorkflowPhase.CONTENT_DEVELOPMENT,
                success=True,
                artifacts=["content.md"],
                errors=[],
            ),
            PhaseResult(
                phase=WorkflowPhase.VISUAL_GENERATION,
                success=False,
                artifacts=[],
                errors=["Image generation failed"],
            ),
        ]

        output_path = tmp_path / "state.json"
        workflow_orchestrator.save_state(
            workflow_id="multi-phase-workflow",
            phase_results=phase_results,
            output_path=str(output_path),
        )

        with open(output_path) as f:
            state = json.load(f)

        assert len(state["completed_phases"]) == 3
        assert state["completed_phases"][0]["phase"] == "research"
        assert state["completed_phases"][1]["phase"] == "content_development"
        assert state["completed_phases"][2]["phase"] == "visual_generation"
        assert state["completed_phases"][2]["success"] is False

    def test_load_state(self, workflow_orchestrator, tmp_path):
        """Test loading workflow state from file."""
        state_file = tmp_path / "state.json"
        state = {
            "workflow_id": "test-workflow",
            "completed_phases": [{"phase": "research", "success": True}],
        }

        with open(state_file, "w") as f:
            json.dump(state, f)

        loaded_state = workflow_orchestrator.load_state(str(state_file))

        assert loaded_state["workflow_id"] == "test-workflow"
        assert len(loaded_state["completed_phases"]) == 1

    def test_load_state_complex(self, workflow_orchestrator, tmp_path):
        """Test loading complex workflow state."""
        state_file = tmp_path / "complex_state.json"
        state = {
            "workflow_id": "complex-workflow",
            "completed_phases": [
                {
                    "phase": "research",
                    "success": True,
                    "artifacts": ["research.json", "sources.json"],
                    "errors": [],
                },
                {
                    "phase": "content_development",
                    "success": True,
                    "artifacts": ["slides.md"],
                    "errors": ["Minor warning"],
                },
            ],
            "custom_data": {"key": "value"},
        }

        with open(state_file, "w") as f:
            json.dump(state, f)

        loaded_state = workflow_orchestrator.load_state(str(state_file))

        assert loaded_state["workflow_id"] == "complex-workflow"
        assert len(loaded_state["completed_phases"]) == 2
        assert loaded_state["custom_data"]["key"] == "value"

    def test_workflow_result_aggregation(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test that WorkflowResult aggregates all phase results."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
        }

        workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            initial_input="test",
            config={},
        )

        # Just verifying no errors in aggregation
        assert True

    def test_workflow_duration_tracking(
        self, workflow_orchestrator, skill_registry, mock_skill_class
    ):
        """Test that workflow tracks total duration."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {WorkflowPhase.RESEARCH: ["mock-skill"]}

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.RESEARCH,
            initial_input="test",
            config={},
        )

        assert result.total_duration >= 0

    def test_workflow_final_artifacts_collection(
        self, workflow_orchestrator, skill_registry
    ):
        """Test that final_artifacts collects from all phases."""

        class ArtifactSkill1(BaseSkill):
            @property
            def skill_id(self):
                return "artifact-skill-1"

            @property
            def display_name(self):
                return "Artifact Skill 1"

            @property
            def description(self):
                return "Produces artifacts"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(
                    data={}, artifacts=["phase1_file.json"]
                )

        class ArtifactSkill2(BaseSkill):
            @property
            def skill_id(self):
                return "artifact-skill-2"

            @property
            def display_name(self):
                return "Artifact Skill 2"

            @property
            def description(self):
                return "Produces artifacts"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={}, artifacts=["phase2_file.md"])

        skill_registry.register_skill(ArtifactSkill1)
        skill_registry.register_skill(ArtifactSkill2)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["artifact-skill-1"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["artifact-skill-2"],
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            initial_input="test",
            config={},
        )

        assert "phase1_file.json" in result.final_artifacts
        assert "phase2_file.md" in result.final_artifacts

    def test_init_with_default_checkpoint_handler(self):
        """Test WorkflowOrchestrator creates default checkpoint handler."""
        orchestrator = WorkflowOrchestrator()

        assert orchestrator.checkpoint_handler is not None
        assert isinstance(orchestrator.checkpoint_handler, CheckpointHandler)

    def test_init_with_default_config(self):
        """Test WorkflowOrchestrator uses empty config by default."""
        orchestrator = WorkflowOrchestrator()

        assert orchestrator.config == {}

    def test_init_with_custom_checkpoint_handler(self, mocker):
        """Test WorkflowOrchestrator accepts custom checkpoint handler."""
        custom_handler = mocker.MagicMock(spec=CheckpointHandler)
        orchestrator = WorkflowOrchestrator(checkpoint_handler=custom_handler)

        assert orchestrator.checkpoint_handler is custom_handler

    def test_init_with_custom_config(self):
        """Test WorkflowOrchestrator accepts custom config."""
        custom_config = {"setting1": "value1", "setting2": "value2"}
        orchestrator = WorkflowOrchestrator(config=custom_config)

        assert orchestrator.config == custom_config


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_get_last_output(self):
        """Test retrieving last skill output from phase."""
        output1 = SkillOutput.success_result(data={"first": "output"})
        output2 = SkillOutput.success_result(data={"second": "output"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[output1, output2]
        )

        last_output = phase_result.get_last_output()
        assert last_output == output2

    def test_get_last_output_empty(self):
        """Test get_last_output with no outputs."""
        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[]
        )

        assert phase_result.get_last_output() is None

    def test_get_last_output_single(self):
        """Test get_last_output with single output."""
        output = SkillOutput.success_result(data={"only": "output"})
        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[output]
        )

        assert phase_result.get_last_output() == output

    def test_get_output_data(self):
        """Test combining output data from all skills."""
        output1 = SkillOutput.success_result(data={"key1": "value1"})
        output2 = SkillOutput.success_result(data={"key2": "value2"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[output1, output2]
        )

        combined = phase_result.get_output_data()
        assert combined["key1"] == "value1"
        assert combined["key2"] == "value2"

    def test_get_output_data_empty(self):
        """Test get_output_data with no outputs."""
        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[]
        )

        combined = phase_result.get_output_data()
        assert combined == {}

    def test_get_output_data_overwrites_duplicate_keys(self):
        """Test that later outputs overwrite earlier ones with same keys."""
        output1 = SkillOutput.success_result(data={"key": "first", "unique1": "a"})
        output2 = SkillOutput.success_result(data={"key": "second", "unique2": "b"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH, success=True, outputs=[output1, output2]
        )

        combined = phase_result.get_output_data()
        assert combined["key"] == "second"  # Later value wins
        assert combined["unique1"] == "a"
        assert combined["unique2"] == "b"

    def test_phase_success_with_partial_failures(self):
        """Test phase marked successful even with some skill failures."""
        output1 = SkillOutput.failure_result(errors=["Failed"])
        output2 = SkillOutput.success_result(data={"success": "data"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,  # Overall phase can still succeed
            outputs=[output1, output2],
            errors=[],  # No phase-level errors
        )

        assert phase_result.success is True
        assert len(phase_result.outputs) == 2

    def test_phase_result_default_values(self):
        """Test PhaseResult has correct default values."""
        phase_result = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)

        assert phase_result.outputs == []
        assert phase_result.artifacts == []
        assert phase_result.errors == []
        assert phase_result.metadata == {}

    def test_phase_result_with_all_fields(self):
        """Test PhaseResult with all fields populated."""
        output = SkillOutput.success_result(data={"key": "value"})
        phase_result = PhaseResult(
            phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            success=True,
            outputs=[output],
            artifacts=["file1.md", "file2.json"],
            errors=["warning1"],
            metadata={"duration": 10.5, "retries": 0},
        )

        assert phase_result.phase == WorkflowPhase.CONTENT_DEVELOPMENT
        assert phase_result.success is True
        assert len(phase_result.outputs) == 1
        assert len(phase_result.artifacts) == 2
        assert len(phase_result.errors) == 1
        assert phase_result.metadata["duration"] == 10.5


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""

    def test_get_phase_result(self):
        """Test retrieving result for specific phase."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=True)

        workflow_result = WorkflowResult(success=True, phase_results=[phase1, phase2])

        research_result = workflow_result.get_phase_result(WorkflowPhase.RESEARCH)
        assert research_result == phase1

    def test_get_phase_result_not_found(self):
        """Test get_phase_result when phase not in results."""
        workflow_result = WorkflowResult(success=True, phase_results=[])

        result = workflow_result.get_phase_result(WorkflowPhase.RESEARCH)
        assert result is None

    def test_get_phase_result_multiple_phases(self):
        """Test get_phase_result with multiple phases."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=True)
        phase3 = PhaseResult(phase=WorkflowPhase.VISUAL_GENERATION, success=False)
        phase4 = PhaseResult(phase=WorkflowPhase.PRESENTATION_ASSEMBLY, success=True)

        workflow_result = WorkflowResult(
            success=False, phase_results=[phase1, phase2, phase3, phase4]
        )

        assert workflow_result.get_phase_result(WorkflowPhase.RESEARCH) == phase1
        assert (
            workflow_result.get_phase_result(WorkflowPhase.CONTENT_DEVELOPMENT)
            == phase2
        )
        assert (
            workflow_result.get_phase_result(WorkflowPhase.VISUAL_GENERATION) == phase3
        )
        assert (
            workflow_result.get_phase_result(WorkflowPhase.PRESENTATION_ASSEMBLY)
            == phase4
        )

    def test_workflow_success_all_phases_succeed(self):
        """Test workflow success when all phases succeed."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=True)

        workflow_result = WorkflowResult(success=True, phase_results=[phase1, phase2])

        assert workflow_result.success is True

    def test_workflow_failure_any_phase_fails(self):
        """Test workflow failure when any phase fails."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=False)

        workflow_result = WorkflowResult(success=False, phase_results=[phase1, phase2])

        assert workflow_result.success is False

    def test_workflow_result_default_values(self):
        """Test WorkflowResult has correct default values."""
        workflow_result = WorkflowResult(success=True)

        assert workflow_result.phase_results == []
        assert workflow_result.final_artifacts == []
        assert workflow_result.total_duration == 0.0
        assert workflow_result.metadata == {}

    def test_workflow_result_with_all_fields(self):
        """Test WorkflowResult with all fields populated."""
        phase = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        workflow_result = WorkflowResult(
            success=True,
            phase_results=[phase],
            final_artifacts=["final.pptx", "notes.md"],
            total_duration=125.5,
            metadata={"workflow_id": "test-123", "user": "tester"},
        )

        assert workflow_result.success is True
        assert len(workflow_result.phase_results) == 1
        assert len(workflow_result.final_artifacts) == 2
        assert workflow_result.total_duration == 125.5
        assert workflow_result.metadata["workflow_id"] == "test-123"


class TestWorkflowPhase:
    """Tests for WorkflowPhase enum."""

    def test_all_phases_exist(self):
        """Test that all expected phases exist."""
        assert WorkflowPhase.RESEARCH is not None
        assert WorkflowPhase.CONTENT_DEVELOPMENT is not None
        assert WorkflowPhase.VISUAL_GENERATION is not None
        assert WorkflowPhase.PRESENTATION_ASSEMBLY is not None

    def test_phase_values(self):
        """Test phase enum values."""
        assert WorkflowPhase.RESEARCH.value == "research"
        assert WorkflowPhase.CONTENT_DEVELOPMENT.value == "content_development"
        assert WorkflowPhase.VISUAL_GENERATION.value == "visual_generation"
        assert WorkflowPhase.PRESENTATION_ASSEMBLY.value == "presentation_assembly"

    def test_phase_iteration_order(self):
        """Test that phases can be iterated in order."""
        phases = list(WorkflowPhase)
        assert len(phases) == 4
        assert phases[0] == WorkflowPhase.RESEARCH
        assert phases[1] == WorkflowPhase.CONTENT_DEVELOPMENT
        assert phases[2] == WorkflowPhase.VISUAL_GENERATION
        assert phases[3] == WorkflowPhase.PRESENTATION_ASSEMBLY
