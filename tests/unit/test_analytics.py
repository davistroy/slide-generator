"""
Unit tests for plugin/lib/analytics.py

Tests the workflow analytics and performance tracking system.
"""

import time

import pytest

from plugin.lib.analytics import (
    AnalyticsReport,
    CheckpointDecision,
    PhaseMetrics,
    WorkflowAnalytics,
)


class TestPhaseMetrics:
    """Tests for PhaseMetrics dataclass."""

    def test_create_phase_metrics(self):
        """Test creating PhaseMetrics with basic fields."""
        metrics = PhaseMetrics(phase_name="research", start_time=time.time())

        assert metrics.phase_name == "research"
        assert metrics.end_time is None
        assert metrics.duration is None
        assert metrics.success is True
        assert metrics.error_message is None

    def test_phase_metrics_finish_success(self):
        """Test finishing a phase successfully."""
        start = time.time()
        metrics = PhaseMetrics(phase_name="test", start_time=start)

        time.sleep(0.01)
        metrics.finish(success=True)

        assert metrics.end_time is not None
        assert metrics.duration is not None
        assert metrics.duration > 0
        assert metrics.success is True
        assert metrics.error_message is None

    def test_phase_metrics_finish_with_error(self):
        """Test finishing a phase with error."""
        metrics = PhaseMetrics(phase_name="test", start_time=time.time())

        metrics.finish(success=False, error="Something went wrong")

        assert metrics.success is False
        assert metrics.error_message == "Something went wrong"

    def test_phase_metrics_default_collections(self):
        """Test default collections are empty."""
        metrics = PhaseMetrics(phase_name="test", start_time=time.time())

        assert metrics.api_calls == {}
        assert metrics.tokens_used == {}
        assert metrics.items_processed == 0
        assert metrics.quality_scores == []
        assert metrics.metadata == {}


class TestCheckpointDecision:
    """Tests for CheckpointDecision dataclass."""

    def test_create_checkpoint_decision(self):
        """Test creating a checkpoint decision."""
        decision = CheckpointDecision(
            checkpoint_name="research_approval",
            timestamp=time.time(),
            decision="continue",
            notes="Looks good",
            artifacts_reviewed=["research.json"],
        )

        assert decision.checkpoint_name == "research_approval"
        assert decision.decision == "continue"
        assert decision.notes == "Looks good"
        assert "research.json" in decision.artifacts_reviewed


class TestAnalyticsReport:
    """Tests for AnalyticsReport dataclass."""

    def test_create_analytics_report(self):
        """Test creating an analytics report."""
        report = AnalyticsReport(workflow_id="test-001", start_time=time.time())

        assert report.workflow_id == "test-001"
        assert report.end_time is None
        assert report.phases == []
        assert report.checkpoints == []
        assert report.estimated_cost == 0.0


class TestWorkflowAnalytics:
    """Tests for WorkflowAnalytics class."""

    def test_init_with_workflow_id(self):
        """Test initialization with workflow ID."""
        analytics = WorkflowAnalytics(workflow_id="test-123")

        assert analytics.workflow_id == "test-123"
        assert analytics.start_time is not None

    def test_init_without_workflow_id(self):
        """Test initialization generates workflow ID."""
        analytics = WorkflowAnalytics()

        assert analytics.workflow_id.startswith("workflow-")

    def test_set_configuration(self):
        """Test setting configuration."""
        analytics = WorkflowAnalytics(workflow_id="test")

        config = {"template": "cfa", "duration": 30}
        analytics.set_configuration(config)

        assert analytics.configuration == config

    def test_add_metadata(self):
        """Test adding metadata."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.add_metadata("topic", "Machine Learning")
        analytics.add_metadata("audience", "developers")

        assert analytics.metadata["topic"] == "Machine Learning"
        assert analytics.metadata["audience"] == "developers"

    def test_start_phase(self):
        """Test starting a phase."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research", metadata={"depth": "comprehensive"})

        assert analytics.current_phase is not None
        assert analytics.current_phase.phase_name == "research"
        assert analytics.current_phase.metadata["depth"] == "comprehensive"

    def test_start_new_phase_auto_ends_previous(self):
        """Test starting a new phase auto-ends the previous one."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")
        analytics.start_phase("outline")

        assert len(analytics.phases) == 1
        assert analytics.phases[0].phase_name == "research"
        assert analytics.current_phase.phase_name == "outline"

    def test_end_phase(self):
        """Test ending a phase."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")
        analytics.end_phase(
            "research", success=True, items_processed=10, quality_scores=[85.0, 90.0]
        )

        assert len(analytics.phases) == 1
        assert analytics.phases[0].items_processed == 10
        assert analytics.phases[0].quality_scores == [85.0, 90.0]
        assert analytics.current_phase is None

    def test_end_phase_wrong_name_raises(self):
        """Test ending wrong phase raises error."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")

        with pytest.raises(ValueError, match="No active phase"):
            analytics.end_phase("outline")

    def test_end_phase_no_current_raises(self):
        """Test ending phase when none active raises error."""
        analytics = WorkflowAnalytics(workflow_id="test")

        with pytest.raises(ValueError, match="No active phase"):
            analytics.end_phase("research")

    def test_track_api_call(self):
        """Test tracking API calls."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")
        analytics.track_api_call(
            "claude", call_count=1, tokens_input=1000, tokens_output=500
        )
        analytics.track_api_call(
            "claude", call_count=1, tokens_input=2000, tokens_output=1000
        )

        assert analytics.total_api_calls.get("claude", 0) == 2
        assert analytics.current_phase.api_calls.get("claude", 0) == 2

    def test_track_checkpoint(self):
        """Test tracking checkpoint decisions."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.track_checkpoint(
            checkpoint_name="research_review",
            decision="continue",
            notes="Data looks comprehensive",
            artifacts=["research.json"],
        )

        assert len(analytics.checkpoints) == 1
        assert analytics.checkpoints[0].decision == "continue"

    def test_track_refinement_attempt(self):
        """Test tracking refinement attempts within a phase."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("refinement")
        analytics.track_refinement_attempt(slide_number=1)
        analytics.track_refinement_attempt(slide_number=1)
        analytics.track_refinement_attempt(slide_number=2)

        # Refinements are tracked in phase metadata
        attempts = analytics.current_phase.metadata.get("refinement_attempts", {})
        assert attempts.get(1, 0) == 2
        assert attempts.get(2, 0) == 1

    def test_generate_report(self):
        """Test generating analytics report."""
        analytics = WorkflowAnalytics(workflow_id="test-report")

        analytics.set_configuration({"template": "cfa"})
        analytics.start_phase("research")
        analytics.track_api_call("claude", call_count=1)
        analytics.end_phase(
            "research",
            success=True,
            items_processed=5,
            quality_scores=[80.0, 85.0, 90.0],
        )

        report = analytics.generate_report()

        assert report.workflow_id == "test-report"
        assert len(report.phases) == 1
        assert report.configuration["template"] == "cfa"

    def test_generate_report_calculates_averages(self):
        """Test report calculates average quality scores."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("draft")
        analytics.end_phase("draft", success=True, quality_scores=[80.0, 90.0, 100.0])

        report = analytics.generate_report()

        # Average of 80, 90, 100 = 90
        assert report.average_quality_score == 90.0

    def test_save_and_load_report(self, tmp_path):
        """Test saving and loading report."""
        analytics = WorkflowAnalytics(workflow_id="save-test")

        analytics.start_phase("test")
        analytics.end_phase("test", success=True)

        report_path = tmp_path / "analytics.json"
        analytics.save_report(str(report_path))

        assert report_path.exists()

        # Verify content
        import json

        with open(report_path) as f:
            loaded = json.load(f)

        assert loaded["workflow_id"] == "save-test"

    def test_track_api_call_no_current_phase(self):
        """Test tracking API call without active phase still tracks total."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.track_api_call("gemini", call_count=1)

        assert analytics.total_api_calls.get("gemini", 0) == 1

    def test_finish_workflow(self):
        """Test finishing workflow."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")
        analytics.finish_workflow(success=True)

        assert analytics.end_time is not None
        assert len(analytics.phases) == 1
        assert analytics.current_phase is None

    def test_calculate_estimated_cost(self):
        """Test cost estimation calculation."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("test")
        analytics.track_api_call(
            "claude", call_count=1, tokens_input=1000, tokens_output=500
        )
        analytics.end_phase("test", success=True)

        cost = analytics.calculate_estimated_cost()

        assert cost >= 0  # Cost should be non-negative

    def test_format_summary(self):
        """Test formatting summary as string."""
        analytics = WorkflowAnalytics(workflow_id="test")

        analytics.start_phase("research")
        analytics.end_phase("research", success=True, items_processed=5)

        summary = analytics.format_summary()

        assert isinstance(summary, str)
        assert "test" in summary or "research" in summary
