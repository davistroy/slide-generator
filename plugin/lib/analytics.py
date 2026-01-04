"""
Workflow Analytics and Performance Tracking

Tracks metrics across workflow execution including:
- Phase timing and duration
- API usage and estimated costs
- Quality scores per slide
- Validation pass/fail rates
- Refinement attempt distribution
- User checkpoint decisions

Generates comprehensive reports for cost analysis and optimization.
"""

import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from plugin.lib.cost_estimator import CostEstimator


@dataclass
class PhaseMetrics:
    """Metrics for a single workflow phase."""

    phase_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None

    # Phase-specific metrics
    api_calls: Dict[str, int] = field(default_factory=dict)
    tokens_used: Dict[str, int] = field(default_factory=dict)
    items_processed: int = 0
    quality_scores: List[float] = field(default_factory=list)

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark phase as finished and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        if error:
            self.error_message = error


@dataclass
class CheckpointDecision:
    """User decision at a workflow checkpoint."""

    checkpoint_name: str
    timestamp: float
    decision: str  # "continue", "retry", "abort", "edit"
    notes: Optional[str] = None
    artifacts_reviewed: List[str] = field(default_factory=list)


@dataclass
class AnalyticsReport:
    """Comprehensive analytics report for workflow execution."""

    workflow_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None

    # Phases
    phases: List[PhaseMetrics] = field(default_factory=list)

    # Checkpoint decisions
    checkpoints: List[CheckpointDecision] = field(default_factory=list)

    # API usage and costs
    total_api_calls: Dict[str, int] = field(default_factory=dict)
    total_tokens: Dict[str, int] = field(default_factory=dict)
    estimated_cost: float = 0.0

    # Quality metrics
    average_quality_score: Optional[float] = None
    quality_improvement: Optional[float] = None  # Before vs after optimization

    # Validation and refinement
    validation_pass_rate: Optional[float] = None
    refinement_attempts: Dict[int, int] = field(default_factory=dict)  # slide_number -> attempts

    # Configuration
    configuration: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowAnalytics:
    """
    Track metrics across workflow execution.

    Usage:
        analytics = WorkflowAnalytics(workflow_id="presentation-001")

        # Start tracking a phase
        analytics.start_phase("research")

        # Track API calls within phase
        analytics.track_api_call("claude", tokens_input=5000, tokens_output=2000)

        # End phase
        analytics.end_phase("research", success=True, items_processed=15)

        # Track checkpoint
        analytics.track_checkpoint("research_approval", decision="continue")

        # Generate report
        report = analytics.generate_report()
        analytics.save_report("analytics_report.json")
    """

    def __init__(self, workflow_id: Optional[str] = None):
        """
        Initialize analytics tracker.

        Args:
            workflow_id: Unique identifier for this workflow run
        """
        self.workflow_id = workflow_id or f"workflow-{int(time.time())}"
        self.start_time = time.time()
        self.end_time: Optional[float] = None

        self.phases: List[PhaseMetrics] = []
        self.current_phase: Optional[PhaseMetrics] = None

        self.checkpoints: List[CheckpointDecision] = []

        self.total_api_calls: Dict[str, int] = {}
        self.total_tokens: Dict[str, Dict[str, int]] = {}

        self.configuration: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        self.cost_estimator = CostEstimator()

    def set_configuration(self, config: Dict[str, Any]) -> None:
        """Set workflow configuration for tracking."""
        self.configuration = config

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to analytics."""
        self.metadata[key] = value

    def start_phase(self, phase_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start tracking a new phase.

        Args:
            phase_name: Name of the phase (e.g., "research", "outline", "draft")
            metadata: Optional phase-specific metadata
        """
        if self.current_phase:
            # Auto-finish previous phase if not ended
            self.end_phase(self.current_phase.phase_name, success=True)

        self.current_phase = PhaseMetrics(
            phase_name=phase_name,
            start_time=time.time(),
            metadata=metadata or {}
        )

    def end_phase(
        self,
        phase_name: str,
        success: bool = True,
        error: Optional[str] = None,
        items_processed: int = 0,
        quality_scores: Optional[List[float]] = None
    ) -> None:
        """
        End tracking of current phase.

        Args:
            phase_name: Name of the phase
            success: Whether phase completed successfully
            error: Error message if failed
            items_processed: Number of items processed (slides, sources, etc.)
            quality_scores: Quality scores for items processed
        """
        if not self.current_phase or self.current_phase.phase_name != phase_name:
            raise ValueError(f"No active phase '{phase_name}' to end")

        self.current_phase.finish(success=success, error=error)
        self.current_phase.items_processed = items_processed

        if quality_scores:
            self.current_phase.quality_scores = quality_scores

        self.phases.append(self.current_phase)
        self.current_phase = None

    def track_api_call(
        self,
        api_name: str,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        call_count: int = 1
    ) -> None:
        """
        Track API usage.

        Args:
            api_name: API name (e.g., "claude", "gemini")
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            call_count: Number of API calls
        """
        # Update current phase
        if self.current_phase:
            if api_name not in self.current_phase.api_calls:
                self.current_phase.api_calls[api_name] = 0
                self.current_phase.tokens_used[api_name] = {"input": 0, "output": 0}

            self.current_phase.api_calls[api_name] += call_count

            if tokens_input:
                self.current_phase.tokens_used[api_name]["input"] += tokens_input
            if tokens_output:
                self.current_phase.tokens_used[api_name]["output"] += tokens_output

        # Update totals
        if api_name not in self.total_api_calls:
            self.total_api_calls[api_name] = 0
            self.total_tokens[api_name] = {"input": 0, "output": 0}

        self.total_api_calls[api_name] += call_count

        if tokens_input:
            self.total_tokens[api_name]["input"] += tokens_input
        if tokens_output:
            self.total_tokens[api_name]["output"] += tokens_output

    def track_checkpoint(
        self,
        checkpoint_name: str,
        decision: str,
        notes: Optional[str] = None,
        artifacts: Optional[List[str]] = None
    ) -> None:
        """
        Track user decision at checkpoint.

        Args:
            checkpoint_name: Name of checkpoint
            decision: User decision (continue, retry, abort, edit)
            notes: Optional notes about decision
            artifacts: Files reviewed at checkpoint
        """
        checkpoint = CheckpointDecision(
            checkpoint_name=checkpoint_name,
            timestamp=time.time(),
            decision=decision,
            notes=notes,
            artifacts_reviewed=artifacts or []
        )
        self.checkpoints.append(checkpoint)

    def track_refinement_attempt(self, slide_number: int) -> None:
        """Track refinement attempt for a slide."""
        if self.current_phase:
            if "refinement_attempts" not in self.current_phase.metadata:
                self.current_phase.metadata["refinement_attempts"] = {}

            attempts = self.current_phase.metadata["refinement_attempts"]
            if slide_number not in attempts:
                attempts[slide_number] = 0
            attempts[slide_number] += 1

    def finish_workflow(self, success: bool = True) -> None:
        """Mark workflow as finished."""
        if self.current_phase:
            self.end_phase(self.current_phase.phase_name, success=success)

        self.end_time = time.time()

    def calculate_estimated_cost(self) -> float:
        """Calculate estimated cost based on API usage."""
        total_cost = 0.0

        # Calculate Claude costs
        if "claude" in self.total_tokens:
            tokens = self.total_tokens["claude"]
            claude_cost = self.cost_estimator.estimate_claude_cost(
                input_tokens=tokens.get("input", 0),
                output_tokens=tokens.get("output", 0),
                model="claude-sonnet-4-5"
            )
            total_cost += claude_cost.total_cost

        # Calculate Gemini costs (if tracked)
        if "gemini_images" in self.total_api_calls:
            image_count = self.total_api_calls["gemini_images"]
            gemini_cost = self.cost_estimator.estimate_gemini_cost(
                image_count=image_count,
                resolution="4K"
            )
            total_cost += gemini_cost.total_cost

        return round(total_cost, 2)

    def generate_report(self) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.

        Returns:
            AnalyticsReport with all tracked metrics
        """
        if not self.end_time:
            self.finish_workflow()

        # Calculate quality metrics
        all_quality_scores = []
        for phase in self.phases:
            all_quality_scores.extend(phase.quality_scores)

        avg_quality = None
        if all_quality_scores:
            avg_quality = sum(all_quality_scores) / len(all_quality_scores)

        # Calculate validation pass rate
        validation_pass_rate = None
        for phase in self.phases:
            if phase.phase_name == "validation" and "pass_rate" in phase.metadata:
                validation_pass_rate = phase.metadata["pass_rate"]

        # Extract refinement attempts
        refinement_attempts = {}
        for phase in self.phases:
            if "refinement_attempts" in phase.metadata:
                refinement_attempts.update(phase.metadata["refinement_attempts"])

        # Calculate quality improvement (before vs after optimization)
        quality_improvement = None
        optimization_phase = next((p for p in self.phases if p.phase_name == "optimization"), None)
        if optimization_phase and "quality_improvement" in optimization_phase.metadata:
            quality_improvement = optimization_phase.metadata["quality_improvement"]

        estimated_cost = self.calculate_estimated_cost()

        return AnalyticsReport(
            workflow_id=self.workflow_id,
            start_time=self.start_time,
            end_time=self.end_time,
            total_duration=self.end_time - self.start_time if self.end_time else None,
            phases=self.phases,
            checkpoints=self.checkpoints,
            total_api_calls=self.total_api_calls,
            total_tokens=self.total_tokens,
            estimated_cost=estimated_cost,
            average_quality_score=avg_quality,
            quality_improvement=quality_improvement,
            validation_pass_rate=validation_pass_rate,
            refinement_attempts=refinement_attempts,
            configuration=self.configuration,
            metadata=self.metadata
        )

    def save_report(self, output_path: str) -> None:
        """
        Save analytics report to JSON file.

        Args:
            output_path: Path to save report
        """
        report = self.generate_report()

        # Convert to dict for JSON serialization
        report_dict = asdict(report)

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2)

    def format_summary(self) -> str:
        """
        Format analytics as human-readable summary.

        Returns:
            Formatted summary string
        """
        report = self.generate_report()

        lines = []
        lines.append("=" * 80)
        lines.append("WORKFLOW ANALYTICS REPORT")
        lines.append("=" * 80)
        lines.append(f"Workflow ID: {report.workflow_id}")

        if report.total_duration:
            minutes = int(report.total_duration // 60)
            seconds = int(report.total_duration % 60)
            lines.append(f"Total Duration: {minutes}m {seconds}s")

        lines.append("")

        # Phase breakdown
        lines.append("Phase Breakdown:")
        lines.append("-" * 80)

        for phase in report.phases:
            status = "✓" if phase.success else "✗"
            duration = f"{phase.duration:.1f}s" if phase.duration else "N/A"
            lines.append(f"  {status} {phase.phase_name:.<40} {duration:>10}")

            if phase.items_processed > 0:
                lines.append(f"      Items processed: {phase.items_processed}")

            if phase.quality_scores:
                avg_quality = sum(phase.quality_scores) / len(phase.quality_scores)
                lines.append(f"      Average quality: {avg_quality:.1f}/100")

        lines.append("")

        # API usage
        lines.append("API Usage:")
        lines.append("-" * 80)

        for api, count in report.total_api_calls.items():
            lines.append(f"  {api}: {count} calls")

            if api in report.total_tokens:
                tokens = report.total_tokens[api]
                lines.append(f"      Input tokens: {tokens.get('input', 0):,}")
                lines.append(f"      Output tokens: {tokens.get('output', 0):,}")

        lines.append("")

        # Cost estimate
        lines.append(f"Estimated Cost: ${report.estimated_cost:.2f}")
        lines.append("")

        # Quality metrics
        if report.average_quality_score:
            lines.append(f"Average Quality Score: {report.average_quality_score:.1f}/100")

        if report.quality_improvement:
            lines.append(f"Quality Improvement: +{report.quality_improvement:.1f} points")

        if report.validation_pass_rate is not None:
            lines.append(f"Validation Pass Rate: {report.validation_pass_rate:.1f}%")

        if report.refinement_attempts:
            total_refinements = sum(report.refinement_attempts.values())
            lines.append(f"Total Refinements: {total_refinements} (across {len(report.refinement_attempts)} slides)")

        lines.append("")

        # Checkpoints
        if report.checkpoints:
            lines.append("Checkpoint Decisions:")
            lines.append("-" * 80)
            for cp in report.checkpoints:
                lines.append(f"  {cp.checkpoint_name}: {cp.decision}")
                if cp.notes:
                    lines.append(f"      Notes: {cp.notes}")

        lines.append("=" * 80)

        return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    analytics = WorkflowAnalytics(workflow_id="test-presentation-001")

    # Configure
    analytics.set_configuration({
        "num_slides": 20,
        "enable_research": True,
        "enable_optimization": True
    })

    # Track phases
    analytics.start_phase("research")
    analytics.track_api_call("claude", tokens_input=50000, tokens_output=30000)
    analytics.end_phase("research", success=True, items_processed=15)

    analytics.track_checkpoint("research_approval", decision="continue")

    analytics.start_phase("outline")
    analytics.track_api_call("claude", tokens_input=15000, tokens_output=5000)
    analytics.end_phase("outline", success=True, items_processed=1)

    analytics.start_phase("draft")
    analytics.track_api_call("claude", tokens_input=40000, tokens_output=20000)
    analytics.end_phase("draft", success=True, items_processed=20, quality_scores=[75.0] * 20)

    analytics.finish_workflow()

    # Generate and display report
    print(analytics.format_summary())

    # Save report
    analytics.save_report("analytics_report.json")
    print("\nReport saved to analytics_report.json")
