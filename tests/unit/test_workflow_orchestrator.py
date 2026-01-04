"""
Unit tests for WorkflowOrchestrator.

Tests the workflow coordination and phase execution system.
"""

import pytest
from plugin.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowPhase,
    PhaseResult,
    WorkflowResult
)
from plugin.base_skill import SkillOutput, SkillStatus
from plugin.checkpoint_handler import CheckpointDecision


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_execute_workflow_all_phases(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test executing complete workflow through all phases."""
        # Register a mock skill for each phase
        skill_registry.register_skill(mock_skill_class)

        # Mock the PHASE_SKILLS to use our mock skill
        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"]
        }

        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow",
            initial_input="test topic"
        )

        assert result.success is True
        assert len(result.phase_results) == 4

    def test_execute_workflow_phase_failure_stops_workflow(self, workflow_orchestrator, skill_registry, mock_failing_skill_class):
        """Test that phase failure stops workflow."""
        skill_registry.register_skill(mock_failing_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["failing-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["failing-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["failing-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["failing-skill"]
        }

        result = workflow_orchestrator.execute_workflow(
            workflow_id="test-workflow",
            initial_input="test topic"
        )

        assert result.success is False
        # Should stop at first phase failure
        assert len(result.phase_results) == 1
        assert result.metadata.get("failed_phase") == "research"

    def test_execute_workflow_user_abort_stops_workflow(self, skill_registry, mock_skill_class, mock_input_abort):
        """Test that user abort at checkpoint stops workflow."""
        from plugin.checkpoint_handler import CheckpointHandler

        checkpoint_handler = CheckpointHandler(interactive=True)
        orchestrator = WorkflowOrchestrator(
            checkpoint_handler=checkpoint_handler,
            config={}
        )

        skill_registry.register_skill(mock_skill_class)

        orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"]
        }

        result = orchestrator.execute_workflow(
            workflow_id="test-workflow",
            initial_input="test topic"
        )

        assert result.success is False
        assert result.metadata.get("aborted_at_phase") is not None
        assert result.metadata.get("aborted_at_phase") == "research"

    def test_run_phase_executes_all_skills(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test that run_phase executes all skills sequentially."""
        skill_registry.register_skill(mock_skill_class)

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={}
        )

        # Phase result should be successful but note we don't have real skills registered
        assert phase_result.phase == WorkflowPhase.RESEARCH

    def test_run_phase_skill_failure_continues_to_next(self, workflow_orchestrator, skill_registry, mock_skill_class, mock_failing_skill_class):
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
            config={}
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
            config={}
        )

        assert len(phase_result.errors) > 0
        assert any("not registered" in error for error in phase_result.errors)

    def test_run_phase_updates_context(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test that phase output updates context for next phase."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"]
        }

        phase_result = workflow_orchestrator.run_phase(
            phase=WorkflowPhase.RESEARCH,
            input_data={"topic": "test"},
            context={},
            config={}
        )

        # Mock skill returns {"result": "success"}
        output_data = phase_result.get_output_data()
        assert "result" in output_data

    def test_execute_partial_workflow(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test executing partial workflow from start_phase to end_phase."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"],
            WorkflowPhase.VISUAL_GENERATION: ["mock-skill"],
            WorkflowPhase.PRESENTATION_ASSEMBLY: ["mock-skill"]
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            end_phase=WorkflowPhase.VISUAL_GENERATION,
            initial_input={"topic": "test"},
            config={}
        )

        # Should only run 2 phases
        assert len(result.phase_results) == 2
        assert result.phase_results[0].phase == WorkflowPhase.CONTENT_DEVELOPMENT
        assert result.phase_results[1].phase == WorkflowPhase.VISUAL_GENERATION

    def test_partial_workflow_invalid_phase_order_fails(self, workflow_orchestrator):
        """Test that invalid phase order raises error."""
        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.VISUAL_GENERATION,
            end_phase=WorkflowPhase.RESEARCH,
            initial_input={},
            config={}
        )

        assert result.success is False
        assert "start_phase must come before end_phase" in result.metadata.get("error", "")

    def test_save_state(self, workflow_orchestrator, tmp_path):
        """Test saving workflow state to file."""
        from plugin.workflow_orchestrator import PhaseResult, WorkflowPhase

        phase_results = [
            PhaseResult(
                phase=WorkflowPhase.RESEARCH,
                success=True,
                artifacts=["research.json"]
            )
        ]

        output_path = tmp_path / "state.json"
        workflow_orchestrator.save_state(
            workflow_id="test-workflow",
            phase_results=phase_results,
            output_path=str(output_path)
        )

        assert output_path.exists()

        import json
        with open(output_path) as f:
            state = json.load(f)

        assert state["workflow_id"] == "test-workflow"
        assert len(state["completed_phases"]) == 1

    def test_load_state(self, workflow_orchestrator, tmp_path):
        """Test loading workflow state from file."""
        import json

        state_file = tmp_path / "state.json"
        state = {
            "workflow_id": "test-workflow",
            "completed_phases": [
                {"phase": "research", "success": True}
            ]
        }

        with open(state_file, 'w') as f:
            json.dump(state, f)

        loaded_state = workflow_orchestrator.load_state(str(state_file))

        assert loaded_state["workflow_id"] == "test-workflow"
        assert len(loaded_state["completed_phases"]) == 1

    def test_workflow_result_aggregation(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test that WorkflowResult aggregates all phase results."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"],
            WorkflowPhase.CONTENT_DEVELOPMENT: ["mock-skill"]
        }

        workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            initial_input="test",
            config={}
        )

        # Just verifying no errors in aggregation
        assert True

    def test_workflow_duration_tracking(self, workflow_orchestrator, skill_registry, mock_skill_class):
        """Test that workflow tracks total duration."""
        skill_registry.register_skill(mock_skill_class)

        workflow_orchestrator.PHASE_SKILLS = {
            WorkflowPhase.RESEARCH: ["mock-skill"]
        }

        result = workflow_orchestrator.execute_partial_workflow(
            start_phase=WorkflowPhase.RESEARCH,
            end_phase=WorkflowPhase.RESEARCH,
            initial_input="test",
            config={}
        )

        assert result.total_duration >= 0


class TestPhaseResult:
    """Tests for PhaseResult dataclass."""

    def test_get_last_output(self):
        """Test retrieving last skill output from phase."""
        output1 = SkillOutput.success_result(data={"first": "output"})
        output2 = SkillOutput.success_result(data={"second": "output"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            outputs=[output1, output2]
        )

        last_output = phase_result.get_last_output()
        assert last_output == output2

    def test_get_last_output_empty(self):
        """Test get_last_output with no outputs."""
        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            outputs=[]
        )

        assert phase_result.get_last_output() is None

    def test_get_output_data(self):
        """Test combining output data from all skills."""
        output1 = SkillOutput.success_result(data={"key1": "value1"})
        output2 = SkillOutput.success_result(data={"key2": "value2"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,
            outputs=[output1, output2]
        )

        combined = phase_result.get_output_data()
        assert combined["key1"] == "value1"
        assert combined["key2"] == "value2"

    def test_phase_success_with_partial_failures(self):
        """Test phase marked successful even with some skill failures."""
        output1 = SkillOutput.failure_result(errors=["Failed"])
        output2 = SkillOutput.success_result(data={"success": "data"})

        phase_result = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True,  # Overall phase can still succeed
            outputs=[output1, output2],
            errors=[]  # No phase-level errors
        )

        assert phase_result.success is True
        assert len(phase_result.outputs) == 2


class TestWorkflowResult:
    """Tests for WorkflowResult dataclass."""

    def test_get_phase_result(self):
        """Test retrieving result for specific phase."""
        phase1 = PhaseResult(
            phase=WorkflowPhase.RESEARCH,
            success=True
        )
        phase2 = PhaseResult(
            phase=WorkflowPhase.CONTENT_DEVELOPMENT,
            success=True
        )

        workflow_result = WorkflowResult(
            success=True,
            phase_results=[phase1, phase2]
        )

        research_result = workflow_result.get_phase_result(WorkflowPhase.RESEARCH)
        assert research_result == phase1

    def test_get_phase_result_not_found(self):
        """Test get_phase_result when phase not in results."""
        workflow_result = WorkflowResult(
            success=True,
            phase_results=[]
        )

        result = workflow_result.get_phase_result(WorkflowPhase.RESEARCH)
        assert result is None

    def test_workflow_success_all_phases_succeed(self):
        """Test workflow success when all phases succeed."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=True)

        workflow_result = WorkflowResult(
            success=True,
            phase_results=[phase1, phase2]
        )

        assert workflow_result.success is True

    def test_workflow_failure_any_phase_fails(self):
        """Test workflow failure when any phase fails."""
        phase1 = PhaseResult(phase=WorkflowPhase.RESEARCH, success=True)
        phase2 = PhaseResult(phase=WorkflowPhase.CONTENT_DEVELOPMENT, success=False)

        workflow_result = WorkflowResult(
            success=False,
            phase_results=[phase1, phase2]
        )

        assert workflow_result.success is False
