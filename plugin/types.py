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

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    TypeAlias,
    TypedDict,
    Union,
    runtime_checkable,
)


# =============================================================================
# Type Aliases
# =============================================================================

#: JSON-serializable value type
JSONValue: TypeAlias = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

#: JSON object type
JSONObject: TypeAlias = Dict[str, JSONValue]

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
    brand_colors: List[str]


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
    content: Optional[str]
    relevance_score: float
    accessed_date: str


class InsightData(TypedDict):
    """Extracted insight from research."""

    statement: str
    supporting_evidence: List[str]
    confidence: float
    sources: List[str]


class ArgumentData(TypedDict):
    """Argument extracted from research."""

    claim: str
    reasoning: str
    evidence: List[str]
    counter_arguments: List[str]


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

    concepts: List[ConceptNode]
    relationships: List[ConceptRelation]


class ResearchResult(TypedDict):
    """Complete research result."""

    topic: str
    research_date: str
    sources: List[SourceInfo]
    summary: str
    key_themes: List[str]
    insights: List[InsightData]
    arguments: List[ArgumentData]
    concept_map: Optional[ConceptMap]


# =============================================================================
# TypedDict Definitions - Content
# =============================================================================

class SlideOutline(TypedDict):
    """Outline for a single slide."""

    slide_number: int
    slide_type: str
    title: str
    purpose: str
    key_points: List[str]
    supporting_sources: List[str]


class PresentationOutline(TypedDict):
    """Complete presentation outline."""

    title: str
    subtitle: Optional[str]
    audience: str
    estimated_duration: int
    slides: List[SlideOutline]


class SlideContent(TypedDict, total=False):
    """Complete content for a slide."""

    slide_number: int
    slide_type: str
    title: str
    subtitle: Optional[str]
    bullets: List[str]
    speaker_notes: str
    graphics_description: str
    background_info: str
    citations: List[str]


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
    issues: List[str]
    suggestions: List[str]
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
    error: Optional[str]
    usage: Optional[APIUsage]


class ClarifyingQuestion(TypedDict):
    """Clarifying question for research refinement."""

    id: str
    question: str
    options: List[str]


# =============================================================================
# Protocol Classes
# =============================================================================

@runtime_checkable
class APIClientProtocol(Protocol):
    """Protocol for API client implementations."""

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
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

    def validate_input(self, input: Any) -> tuple[bool, List[str]]:
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
    author: Optional[str] = None
    date: Optional[str] = None
    accessed_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
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
    style: Optional[str] = None
    aspect_ratio: str = "16:9"
    background_color: Optional[str] = None

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
    completed_steps: List[str] = field(default_factory=list)
    artifacts: Dict[str, FilePath] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.completed_at is not None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get workflow duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
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
