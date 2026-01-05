"""
Centralized type definitions for the slide-generator plugin system.

This module provides:
- Type aliases for common types
- TypedDict definitions for structured data
- Protocol classes for duck typing
- Dataclasses for domain objects

Usage:
    from plugin.types import (
        SkillConfig,
        ResearchResult,
        SlideContent,
        APIClientProtocol,
    )
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Literal,
    Protocol,
    TypeAlias,
    TypedDict,
    runtime_checkable,
)


# =============================================================================
# Type Aliases
# =============================================================================

#: JSON-serializable value type
JSONValue: TypeAlias = str | int | float | bool | None | dict[str, Any] | list[Any]

#: JSON object type
JSONObject: TypeAlias = dict[str, JSONValue]

#: File path as string
FilePath: TypeAlias = str

#: Skill identifier (lowercase with hyphens)
SkillID: TypeAlias = str

#: API key string
APIKey: TypeAlias = str

#: URL string
URL: TypeAlias = str

#: Markdown content string
MarkdownContent: TypeAlias = str

#: Callback function type for progress reporting
ProgressCallback: TypeAlias = Callable[[str, float], None]


# =============================================================================
# Enums
# =============================================================================


class ResearchDepth(str, Enum):
    """Depth level for research operations."""

    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


class SlideType(str, Enum):
    """Types of slides in a presentation."""

    TITLE = "title"
    SECTION = "section"
    CONTENT = "content"
    IMAGE = "image"
    TEXT_IMAGE = "text_image"
    COMPARISON = "comparison"
    QUOTE = "quote"
    CLOSING = "closing"


class ContentTone(str, Enum):
    """Tone options for content generation."""

    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"


class QualityLevel(str, Enum):
    """Quality assessment levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


# =============================================================================
# TypedDict Definitions - Configuration
# =============================================================================


class SkillConfig(TypedDict, total=False):
    """Configuration options for skills."""

    api_key: str
    model: str
    max_tokens: int
    temperature: float
    timeout: int
    retry_attempts: int
    verbose: bool


class StyleConfig(TypedDict, total=False):
    """Style configuration for content generation."""

    tone: str
    max_bullets_per_slide: int
    max_words_per_bullet: int
    include_speaker_notes: bool
    include_graphics: bool
    brand_colors: list[str]


class WorkflowConfig(TypedDict, total=False):
    """Configuration for workflow execution."""

    interactive: bool
    auto_approve: bool
    save_checkpoints: bool
    checkpoint_dir: str
    output_dir: str


# =============================================================================
# TypedDict Definitions - Research
# =============================================================================


class SourceInfo(TypedDict):
    """Information about a research source."""

    url: str
    title: str
    snippet: str
    content: str | None
    relevance_score: float
    accessed_date: str


class InsightData(TypedDict):
    """Extracted insight from research."""

    statement: str
    supporting_evidence: list[str]
    confidence: float
    sources: list[str]


class ArgumentData(TypedDict):
    """Argument extracted from research."""

    claim: str
    reasoning: str
    evidence: list[str]
    counter_arguments: list[str]


class ConceptNode(TypedDict):
    """Node in a concept map."""

    name: str
    description: str


class ConceptRelation(TypedDict):
    """Relationship in a concept map."""

    from_concept: str
    to_concept: str
    relation_type: str


class ConceptMap(TypedDict):
    """Concept map from research analysis."""

    concepts: list[ConceptNode]
    relationships: list[ConceptRelation]


class ResearchResult(TypedDict):
    """Complete research result."""

    topic: str
    research_date: str
    sources: list[SourceInfo]
    summary: str
    key_themes: list[str]
    insights: list[InsightData]
    arguments: list[ArgumentData]
    concept_map: ConceptMap | None


# =============================================================================
# TypedDict Definitions - Content
# =============================================================================


class SlideOutline(TypedDict):
    """Outline for a single slide."""

    slide_number: int
    slide_type: str
    title: str
    purpose: str
    key_points: list[str]
    supporting_sources: list[str]


class PresentationOutline(TypedDict):
    """Complete presentation outline."""

    title: str
    subtitle: str | None
    audience: str
    estimated_duration: int
    slides: list[SlideOutline]


class SlideContent(TypedDict, total=False):
    """Complete content for a slide."""

    slide_number: int
    slide_type: str
    title: str
    subtitle: str | None
    bullets: list[str]
    speaker_notes: str
    graphics_description: str
    background_info: str
    citations: list[str]


class QualityScore(TypedDict):
    """Quality analysis scores."""

    overall: float
    readability: float
    tone_consistency: float
    structure: float
    redundancy: float
    citations: float


class QualityAnalysis(TypedDict):
    """Complete quality analysis result."""

    scores: QualityScore
    issues: list[str]
    suggestions: list[str]
    passed: bool


# =============================================================================
# TypedDict Definitions - API Responses
# =============================================================================


class APIUsage(TypedDict):
    """API usage statistics."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float


class APIResponse(TypedDict):
    """Generic API response wrapper."""

    success: bool
    data: Any
    error: str | None
    usage: APIUsage | None


class ClarifyingQuestion(TypedDict):
    """Clarifying question for research refinement."""

    id: str
    question: str
    options: list[str]


# =============================================================================
# Protocol Classes
# =============================================================================


@runtime_checkable
class APIClientProtocol(Protocol):
    """Protocol for API client implementations."""

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
    ) -> str:
        """Generate text from a prompt."""
        ...


@runtime_checkable
class SkillProtocol(Protocol):
    """Protocol for skill implementations."""

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill."""
        ...

    @property
    def display_name(self) -> str:
        """Human-readable name."""
        ...

    @property
    def description(self) -> str:
        """Brief description."""
        ...

    def validate_input(self, input: Any) -> tuple[bool, list[str]]:
        """Validate input before execution."""
        ...

    def execute(self, input: Any) -> Any:
        """Execute the skill."""
        ...


@runtime_checkable
class ProgressReporterProtocol(Protocol):
    """Protocol for progress reporting."""

    def report(self, message: str, progress: float) -> None:
        """Report progress update."""
        ...

    def complete(self, message: str) -> None:
        """Report completion."""
        ...

    def error(self, message: str) -> None:
        """Report error."""
        ...


# =============================================================================
# Dataclasses - Domain Objects
# =============================================================================


@dataclass
class Citation:
    """A citation reference."""

    id: str
    source_url: str
    title: str
    author: str | None = None
    date: str | None = None
    accessed_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "source_url": self.source_url,
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "accessed_date": self.accessed_date,
        }


@dataclass
class ImageSpec:
    """Specification for image generation."""

    description: str
    resolution: Literal["low", "medium", "high"] = "medium"
    style: str | None = None
    aspect_ratio: str = "16:9"
    background_color: str | None = None

    @property
    def dimensions(self) -> tuple[int, int]:
        """Get dimensions based on resolution."""
        resolutions = {
            "low": (640, 360),
            "medium": (1280, 720),
            "high": (1920, 1080),
        }
        return resolutions.get(self.resolution, (1280, 720))


@dataclass
class WorkflowState:
    """State of a workflow execution."""

    workflow_id: str
    current_step: str
    completed_steps: list[str] = field(default_factory=list)
    artifacts: dict[str, FilePath] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.completed_at is not None

    @property
    def duration_seconds(self) -> float | None:
        """Get workflow duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(cls) -> ValidationResult:
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, errors: list[str]) -> ValidationResult:
        """Create a failed validation result."""
        return cls(is_valid=False, errors=errors)


# =============================================================================
# Type Guards
# =============================================================================


def is_source_info(obj: Any) -> bool:
    """Check if object matches SourceInfo structure."""
    if not isinstance(obj, dict):
        return False
    required_keys = {"url", "title", "snippet"}
    return required_keys.issubset(obj.keys())


def is_slide_content(obj: Any) -> bool:
    """Check if object matches SlideContent structure."""
    if not isinstance(obj, dict):
        return False
    required_keys = {"slide_number", "slide_type", "title"}
    return required_keys.issubset(obj.keys())


def is_valid_skill_id(skill_id: str) -> bool:
    """Check if skill_id follows naming convention."""
    import re

    return bool(re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", skill_id))
