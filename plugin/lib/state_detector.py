"""
State detection for workflow resumption.

Scans a project directory for existing artifacts and determines the current
workflow state, enabling users to resume from any checkpoint.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plugin.workflow_orchestrator import WorkflowPhase


logger = logging.getLogger(__name__)


@dataclass
class ArtifactInfo:
    """Information about a detected artifact."""

    path: Path
    exists: bool
    modified_time: datetime | None = None
    is_valid: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class WorkflowState:
    """Current workflow state based on detected artifacts."""

    current_step: int  # 1-11 based on 11-step workflow
    last_completed_phase: WorkflowPhase | None
    available_artifacts: dict[str, ArtifactInfo]
    next_recommended_step: str
    can_resume: bool
    stale_artifacts: list[str] = field(default_factory=list)


class StateDetector:
    """
    Detect workflow state by scanning for artifacts.

    Scans a project directory for known artifact patterns and determines
    which workflow phase was last completed.

    Artifact mapping:
    - research.json -> Research phase complete
    - insights.json -> Insight extraction complete
    - outline.json/outline.md -> Outline generation complete
    - presentation.md / presentation-*.md -> Content drafting complete
    - images/slide-*.jpg -> Image generation (partial or complete)
    - *.pptx -> Final presentation assembled
    """

    # Artifact patterns and their corresponding workflow steps
    ARTIFACT_PATTERNS = {
        "research": ("research.json", 2),  # Step 2: Web Research
        "insights": ("insights.json", 3),  # Step 3: Insight Extraction
        "outline": (["outline.json", "outline.md"], 4),  # Step 4: Outline Generation
        "presentation": ("presentation.md", 5),  # Step 5: Content Drafting
        "optimized": ("optimized.md", 6),  # Step 6: Quality Optimization
        "images": ("images/", 8),  # Step 8: Image Generation
        "pptx": ("*.pptx", 11),  # Step 11: PowerPoint Assembly
    }

    def __init__(self, project_dir: str | Path | None = None):
        """
        Initialize state detector.

        Args:
            project_dir: Project directory to scan. Defaults to current directory.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()

    def detect_state(self) -> WorkflowState:
        """
        Detect current workflow state by scanning for artifacts.

        Returns:
            WorkflowState with detected artifacts and recommendations
        """
        artifacts: dict[str, ArtifactInfo] = {}
        highest_step = 0
        last_phase = None

        # Check for each artifact type
        artifacts["research"] = self._check_research()
        if artifacts["research"].exists and artifacts["research"].is_valid:
            highest_step = max(highest_step, 2)
            last_phase = WorkflowPhase.RESEARCH

        artifacts["insights"] = self._check_insights()
        if artifacts["insights"].exists and artifacts["insights"].is_valid:
            highest_step = max(highest_step, 3)
            last_phase = WorkflowPhase.RESEARCH

        artifacts["outline"] = self._check_outline()
        if artifacts["outline"].exists and artifacts["outline"].is_valid:
            highest_step = max(highest_step, 4)
            last_phase = WorkflowPhase.CONTENT_DEVELOPMENT

        artifacts["presentation"] = self._check_presentation()
        if artifacts["presentation"].exists and artifacts["presentation"].is_valid:
            highest_step = max(highest_step, 5)
            last_phase = WorkflowPhase.CONTENT_DEVELOPMENT

        artifacts["images"] = self._check_images()
        if artifacts["images"].exists:
            if artifacts["images"].metadata.get("complete", False):
                highest_step = max(highest_step, 8)
                last_phase = WorkflowPhase.VISUAL_GENERATION
            else:
                # Partial image generation
                highest_step = max(highest_step, 7)
                last_phase = WorkflowPhase.VISUAL_GENERATION

        artifacts["pptx"] = self._check_pptx()
        if artifacts["pptx"].exists and artifacts["pptx"].is_valid:
            highest_step = 11
            last_phase = WorkflowPhase.PRESENTATION_ASSEMBLY

        # Determine next step and recommendations
        next_step = self._get_next_step(highest_step, artifacts)
        can_resume = highest_step > 0

        return WorkflowState(
            current_step=highest_step,
            last_completed_phase=last_phase,
            available_artifacts=artifacts,
            next_recommended_step=next_step,
            can_resume=can_resume,
        )

    def _check_research(self) -> ArtifactInfo:
        """Check for research.json artifact."""
        path = self.project_dir / "research.json"
        if not path.exists():
            return ArtifactInfo(path=path, exists=False)

        try:
            with open(path) as f:
                data = json.load(f)

            # Validate structure
            sources = data.get("sources", [])
            return ArtifactInfo(
                path=path,
                exists=True,
                modified_time=self._get_mtime(path),
                is_valid=True,
                metadata={
                    "source_count": len(sources),
                    "topic": data.get("topic", "unknown"),
                },
            )
        except (json.JSONDecodeError, OSError) as e:
            return ArtifactInfo(
                path=path,
                exists=True,
                is_valid=False,
                error=str(e),
            )

    def _check_insights(self) -> ArtifactInfo:
        """Check for insights.json artifact."""
        path = self.project_dir / "insights.json"
        if not path.exists():
            return ArtifactInfo(path=path, exists=False)

        try:
            with open(path) as f:
                data = json.load(f)

            return ArtifactInfo(
                path=path,
                exists=True,
                modified_time=self._get_mtime(path),
                is_valid=True,
                metadata={
                    "insight_count": len(data.get("insights", [])),
                },
            )
        except (json.JSONDecodeError, OSError) as e:
            return ArtifactInfo(
                path=path,
                exists=True,
                is_valid=False,
                error=str(e),
            )

    def _check_outline(self) -> ArtifactInfo:
        """Check for outline.json or outline.md artifact."""
        # Check JSON first, then markdown
        for filename in ["outline.json", "outline.md"]:
            path = self.project_dir / filename
            if path.exists():
                try:
                    if filename.endswith(".json"):
                        with open(path) as f:
                            data = json.load(f)
                        slide_count = len(data.get("slides", []))
                    else:
                        with open(path) as f:
                            content = f.read()
                        # Count slides by counting ## headers
                        slide_count = content.count("\n## ")

                    return ArtifactInfo(
                        path=path,
                        exists=True,
                        modified_time=self._get_mtime(path),
                        is_valid=True,
                        metadata={"slide_count": slide_count},
                    )
                except (json.JSONDecodeError, OSError) as e:
                    return ArtifactInfo(
                        path=path,
                        exists=True,
                        is_valid=False,
                        error=str(e),
                    )

        return ArtifactInfo(path=self.project_dir / "outline.json", exists=False)

    def _check_presentation(self) -> ArtifactInfo:
        """Check for presentation.md artifact."""
        path = self.project_dir / "presentation.md"
        if not path.exists():
            # Check for audience-specific presentations
            patterns = list(self.project_dir.glob("presentation-*.md"))
            if patterns:
                path = patterns[0]  # Use first found
            else:
                return ArtifactInfo(path=path, exists=False)

        try:
            with open(path) as f:
                content = f.read()

            # Count slides
            slide_count = content.count("\n# Slide") + content.count("\n## Slide")
            if slide_count == 0:
                # Alternative: count major sections
                slide_count = content.count("\n# ") + content.count("\n## ")

            return ArtifactInfo(
                path=path,
                exists=True,
                modified_time=self._get_mtime(path),
                is_valid=slide_count > 0,
                metadata={"slide_count": slide_count},
            )
        except OSError as e:
            return ArtifactInfo(
                path=path,
                exists=True,
                is_valid=False,
                error=str(e),
            )

    def _check_images(self) -> ArtifactInfo:
        """Check for generated images."""
        images_dir = self.project_dir / "images"
        if not images_dir.exists():
            # Also check for images in root directory
            images = list(self.project_dir.glob("slide-*.jpg"))
            if not images:
                return ArtifactInfo(path=images_dir, exists=False)
            images_dir = self.project_dir

        images = list(images_dir.glob("slide-*.jpg"))
        if not images:
            return ArtifactInfo(path=images_dir, exists=False)

        # Get expected count from presentation.md if available
        presentation_info = self._check_presentation()
        expected_count = presentation_info.metadata.get("slide_count", 0)

        return ArtifactInfo(
            path=images_dir,
            exists=True,
            modified_time=self._get_mtime(max(images, key=lambda p: p.stat().st_mtime)),
            is_valid=True,
            metadata={
                "image_count": len(images),
                "expected_count": expected_count,
                "complete": expected_count > 0 and len(images) >= expected_count,
            },
        )

    def _check_pptx(self) -> ArtifactInfo:
        """Check for PowerPoint output."""
        pptx_files = list(self.project_dir.glob("*.pptx"))
        if not pptx_files:
            return ArtifactInfo(path=self.project_dir / "presentation.pptx", exists=False)

        # Use most recent pptx
        latest = max(pptx_files, key=lambda p: p.stat().st_mtime)
        return ArtifactInfo(
            path=latest,
            exists=True,
            modified_time=self._get_mtime(latest),
            is_valid=True,
            metadata={"filename": latest.name},
        )

    def _get_mtime(self, path: Path) -> datetime:
        """Get modification time of a file."""
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)

    def _get_next_step(
        self, current_step: int, artifacts: dict[str, ArtifactInfo]
    ) -> str:
        """Determine the next recommended step based on current state."""
        if current_step == 0:
            return "Run: sg research 'Your Topic'"

        if current_step == 2:  # Research done
            return "Run: sg outline research.json"

        if current_step in (3, 4):  # Insights/Outline done
            return "Run: sg draft-content outline.md"

        if current_step in (5, 6):  # Content done
            return "Run: sg generate-images presentation.md"

        if current_step in (7, 8):  # Images done
            image_info = artifacts.get("images")
            if image_info and not image_info.metadata.get("complete", False):
                return "Run: sg generate-images presentation.md (continue generation)"
            return "Run: sg build presentation.md --template cfa"

        if current_step == 11:
            return "Workflow complete! Output available."

        return "Run: sg full-workflow 'Your Topic'"

    def suggest_entry_point(self, state: WorkflowState) -> str:
        """
        Generate a human-readable suggestion for entry point.

        Args:
            state: Current workflow state

        Returns:
            Human-readable suggestion string
        """
        if not state.can_resume:
            return (
                "No artifacts found. Start a new workflow with:\n"
                "  sg full-workflow 'Your Topic' --template cfa"
            )

        suggestions = [f"Workflow can resume from step {state.current_step}."]

        if state.last_completed_phase:
            suggestions.append(f"Last completed phase: {state.last_completed_phase.value}")

        suggestions.append(f"\nNext step: {state.next_recommended_step}")

        return "\n".join(suggestions)


def detect_project_state(project_dir: str | Path | None = None) -> WorkflowState:
    """
    Convenience function to detect project state.

    Args:
        project_dir: Project directory to scan

    Returns:
        WorkflowState object
    """
    detector = StateDetector(project_dir)
    return detector.detect_state()
