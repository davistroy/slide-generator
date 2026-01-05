"""
Base skill interface for all presentation generation skills.

All skills must implement this abstract base class to ensure consistent
input/output contracts and enable workflow orchestration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SkillStatus(Enum):
    """Execution status for a skill."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


@dataclass
class SkillInput:
    """
    Input to a skill execution.

    Attributes:
        data: Primary input data (e.g., topic string, file paths, parsed content)
        context: Contextual information (e.g., previous skill outputs, user preferences)
        config: Configuration settings specific to this skill
    """

    data: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from data with fallback to default."""
        return self.data.get(key, default)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from context with fallback to default."""
        return self.context.get(key, default)

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get value from config with fallback to default."""
        return self.config.get(key, default)


@dataclass
class SkillOutput:
    """
    Output from a skill execution.

    Attributes:
        success: Whether the skill executed successfully
        status: Detailed execution status
        data: Primary output data
        artifacts: File paths created by this skill
        errors: List of error messages (if any)
        warnings: List of warning messages
        metadata: Additional metadata about execution
    """

    success: bool
    status: SkillStatus
    data: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls,
        data: dict[str, Any],
        artifacts: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SkillOutput":
        """Create a successful output result."""
        return cls(
            success=True,
            status=SkillStatus.SUCCESS,
            data=data,
            artifacts=artifacts or [],
            metadata=metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        errors: list[str],
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SkillOutput":
        """Create a failure output result."""
        return cls(
            success=False,
            status=SkillStatus.FAILURE,
            data=data or {},
            errors=errors,
            metadata=metadata or {},
        )

    @classmethod
    def partial_result(
        cls,
        data: dict[str, Any],
        warnings: list[str],
        artifacts: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "SkillOutput":
        """Create a partial success output result."""
        return cls(
            success=True,
            status=SkillStatus.PARTIAL,
            data=data,
            artifacts=artifacts or [],
            warnings=warnings,
            metadata=metadata or {},
        )


class BaseSkill(ABC):
    """
    Abstract base class for all presentation generation skills.

    All skills must implement this interface to participate in the
    workflow orchestration system.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize the skill with optional configuration.

        Args:
            config: Skill-specific configuration settings
        """
        self.config = config or {}
        self._is_initialized = False

    @property
    @abstractmethod
    def skill_id(self) -> str:
        """
        Unique identifier for this skill.

        Must be lowercase with hyphens (e.g., 'research', 'draft-content').
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for this skill.

        Example: 'Web Research', 'Content Drafting'
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Brief description of what this skill does.

        Example: 'Searches the web and gathers authoritative sources on a topic'
        """
        pass

    @property
    def version(self) -> str:
        """
        Skill version number.

        Default: '1.0.0'
        Override to specify different version.
        """
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """
        List of skill IDs that this skill depends on.

        Default: []
        Override to specify dependencies.
        """
        return []

    def initialize(self) -> None:
        """
        Initialize the skill (load resources, validate config, etc.).

        Called once before first execution.
        Override to add initialization logic.
        """
        self._is_initialized = True

    @abstractmethod
    def validate_input(self, input: SkillInput) -> tuple[bool, list[str]]:
        """
        Validate input before execution.

        Args:
            input: Input to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass

    @abstractmethod
    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Execute the skill with given input.

        Args:
            input: Validated input for execution

        Returns:
            Output with success status, data, and artifacts
        """
        pass

    def cleanup(self) -> None:
        """
        Optional cleanup after execution.

        Override to add cleanup logic (close connections, delete temp files, etc.).
        """
        pass

    def run(self, input: SkillInput) -> SkillOutput:
        """
        Main entry point that handles initialization, validation, execution, and cleanup.

        This method should not be overridden. Instead, override:
        - validate_input() for input validation
        - execute() for core logic
        - cleanup() for resource cleanup

        Args:
            input: Input for execution

        Returns:
            Output from execution
        """
        try:
            # Initialize if needed
            if not self._is_initialized:
                self.initialize()

            # Validate input
            is_valid, errors = self.validate_input(input)
            if not is_valid:
                return SkillOutput.failure_result(
                    errors=errors,
                    metadata={"skill_id": self.skill_id, "stage": "validation"},
                )

            # Execute
            output = self.execute(input)

            # Add skill metadata
            output.metadata.update(
                {
                    "skill_id": self.skill_id,
                    "skill_version": self.version,
                }
            )

            return output

        except Exception as e:
            return SkillOutput.failure_result(
                errors=[f"Unexpected error in {self.skill_id}: {e!s}"],
                metadata={
                    "skill_id": self.skill_id,
                    "stage": "execution",
                    "exception_type": type(e).__name__,
                },
            )

        finally:
            # Always attempt cleanup
            try:
                self.cleanup()
            except Exception as e:
                # Log cleanup errors but don't fail the execution
                print(f"Warning: Cleanup failed for {self.skill_id}: {e!s}")

    def __repr__(self) -> str:
        """String representation of the skill."""
        return (
            f"<{self.__class__.__name__} id='{self.skill_id}' version='{self.version}'>"
        )
