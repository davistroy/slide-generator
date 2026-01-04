"""
Unit tests for BaseSkill interface.

Tests the abstract base class that all skills must implement.
"""

import pytest
from plugin.base_skill import (
    BaseSkill,
    SkillInput,
    SkillOutput,
    SkillStatus
)


# ==============================================================================
# Test SkillInput
# ==============================================================================

class TestSkillInput:
    """Tests for SkillInput dataclass."""

    def test_create_skill_input_with_data(self):
        """Test creating SkillInput with data."""
        input_data = SkillInput(
            data={"topic": "test topic"},
            context={"workflow_id": "test-123"},
            config={"max_sources": 20}
        )

        assert input_data.data == {"topic": "test topic"}
        assert input_data.context == {"workflow_id": "test-123"}
        assert input_data.config == {"max_sources": 20}

    def test_create_skill_input_minimal(self):
        """Test creating SkillInput with only required data."""
        input_data = SkillInput(data={"topic": "test"})

        assert input_data.data == {"topic": "test"}
        assert input_data.context == {}
        assert input_data.config == {}

    def test_get_method_returns_value(self):
        """Test get() method returns correct value."""
        input_data = SkillInput(data={"topic": "test topic"})

        assert input_data.get("topic") == "test topic"

    def test_get_method_returns_default(self):
        """Test get() returns default when key missing."""
        input_data = SkillInput(data={"topic": "test"})

        assert input_data.get("nonexistent", "default") == "default"

    def test_get_context_method(self):
        """Test get_context() method."""
        input_data = SkillInput(
            data={},
            context={"workflow_id": "test-123"}
        )

        assert input_data.get_context("workflow_id") == "test-123"
        assert input_data.get_context("missing", "default") == "default"

    def test_get_config_method(self):
        """Test get_config() method."""
        input_data = SkillInput(
            data={},
            config={"max_sources": 20}
        )

        assert input_data.get_config("max_sources") == 20
        assert input_data.get_config("missing", 10) == 10


# ==============================================================================
# Test SkillOutput
# ==============================================================================

class TestSkillOutput:
    """Tests for SkillOutput dataclass."""

    def test_create_success_result(self):
        """Test creating successful SkillOutput."""
        output = SkillOutput(
            success=True,
            status=SkillStatus.SUCCESS,
            data={"result": "success"},
            artifacts=["output.json"]
        )

        assert output.success is True
        assert output.status == SkillStatus.SUCCESS
        assert output.data == {"result": "success"}
        assert output.artifacts == ["output.json"]
        assert output.errors == []
        assert output.warnings == []

    def test_create_failure_result(self):
        """Test creating failure SkillOutput."""
        output = SkillOutput(
            success=False,
            status=SkillStatus.FAILURE,
            errors=["Mock failure"]
        )

        assert output.success is False
        assert output.status == SkillStatus.FAILURE
        assert output.errors == ["Mock failure"]

    def test_create_partial_result(self):
        """Test creating partial success SkillOutput."""
        output = SkillOutput(
            success=True,
            status=SkillStatus.PARTIAL,
            data={"partial": "data"},
            warnings=["Some warnings"]
        )

        assert output.success is True
        assert output.status == SkillStatus.PARTIAL
        assert output.warnings == ["Some warnings"]

    def test_success_result_factory(self):
        """Test SkillOutput.success_result() factory method."""
        output = SkillOutput.success_result(
            data={"result": "success"},
            artifacts=["output.json"],
            metadata={"duration": 1.5}
        )

        assert output.success is True
        assert output.status == SkillStatus.SUCCESS
        assert output.data == {"result": "success"}
        assert output.artifacts == ["output.json"]
        assert output.metadata == {"duration": 1.5}

    def test_failure_result_factory(self):
        """Test SkillOutput.failure_result() factory method."""
        output = SkillOutput.failure_result(
            errors=["Error 1", "Error 2"],
            metadata={"stage": "validation"}
        )

        assert output.success is False
        assert output.status == SkillStatus.FAILURE
        assert output.errors == ["Error 1", "Error 2"]
        assert output.metadata == {"stage": "validation"}

    def test_partial_result_factory(self):
        """Test SkillOutput.partial_result() factory method."""
        output = SkillOutput.partial_result(
            data={"partial": "result"},
            warnings=["Warning 1"],
            artifacts=["partial.json"]
        )

        assert output.success is True
        assert output.status == SkillStatus.PARTIAL
        assert output.warnings == ["Warning 1"]
        assert output.data == {"partial": "result"}


# ==============================================================================
# Test BaseSkill
# ==============================================================================

class TestBaseSkill:
    """Tests for BaseSkill abstract base class."""

    def test_abstract_class_cannot_instantiate(self):
        """Test that BaseSkill cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSkill()

    def test_skill_requires_skill_id(self, mock_skill_class):
        """Test that skill must implement skill_id property."""
        skill = mock_skill_class()
        assert hasattr(skill, 'skill_id')
        assert skill.skill_id == "mock-skill"

    def test_skill_requires_display_name(self, mock_skill_class):
        """Test that skill must implement display_name property."""
        skill = mock_skill_class()
        assert hasattr(skill, 'display_name')
        assert skill.display_name == "Mock Skill"

    def test_skill_requires_description(self, mock_skill_class):
        """Test that skill must implement description property."""
        skill = mock_skill_class()
        assert hasattr(skill, 'description')
        assert skill.description == "A mock skill for testing"

    def test_skill_requires_validate_input(self, mock_skill_class):
        """Test that skill must implement validate_input() method."""
        skill = mock_skill_class()
        assert hasattr(skill, 'validate_input')
        assert callable(skill.validate_input)

    def test_skill_requires_execute(self, mock_skill_class):
        """Test that skill must implement execute() method."""
        skill = mock_skill_class()
        assert hasattr(skill, 'execute')
        assert callable(skill.execute)

    def test_run_method_validates_input(self, mock_skill_class, mocker):
        """Test that run() calls validate_input()."""
        skill = mock_skill_class()
        spy = mocker.spy(skill, 'validate_input')

        input_data = SkillInput(data={"test": "data"})
        skill.run(input_data)

        spy.assert_called_once_with(input_data)

    def test_run_method_executes_skill(self, mock_skill_class, mocker):
        """Test that run() calls execute()."""
        skill = mock_skill_class()
        spy = mocker.spy(skill, 'execute')

        input_data = SkillInput(data={"test": "data"})
        skill.run(input_data)

        spy.assert_called_once_with(input_data)

    def test_run_method_handles_exceptions(self, mock_skill_class, mocker):
        """Test that run() catches and handles exceptions."""
        skill = mock_skill_class()

        # Make execute() raise an exception
        mocker.patch.object(
            skill,
            'execute',
            side_effect=RuntimeError("Test error")
        )

        input_data = SkillInput(data={"test": "data"})
        result = skill.run(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert len(result.errors) > 0
        assert "Test error" in result.errors[0]

    def test_run_method_calls_cleanup(self, mock_skill_class, mocker):
        """Test that run() calls cleanup() even on error."""
        skill = mock_skill_class()
        spy = mocker.spy(skill, 'cleanup')

        # Make execute() raise an exception
        mocker.patch.object(
            skill,
            'execute',
            side_effect=RuntimeError("Test error")
        )

        input_data = SkillInput(data={"test": "data"})
        skill.run(input_data)

        # Cleanup should still be called
        spy.assert_called_once()

    def test_initialization_called_once(self, mock_skill_class, mocker):
        """Test that initialize() is called only once."""
        skill = mock_skill_class()
        spy = mocker.spy(skill, 'initialize')

        input_data = SkillInput(data={"test": "data"})

        # Run twice
        skill.run(input_data)
        skill.run(input_data)

        # Initialize should only be called once
        spy.assert_called_once()

    def test_skill_with_dependencies(self):
        """Test skill with dependency list."""
        class SkillWithDeps(BaseSkill):
            @property
            def skill_id(self) -> str:
                return "skill-with-deps"

            @property
            def display_name(self) -> str:
                return "Skill With Dependencies"

            @property
            def description(self) -> str:
                return "A skill with dependencies"

            @property
            def dependencies(self):
                return ["dep-1", "dep-2"]

            def validate_input(self, input: SkillInput):
                return (True, [])

            def execute(self, input: SkillInput):
                return SkillOutput.success_result(data={})

        skill = SkillWithDeps()
        assert skill.dependencies == ["dep-1", "dep-2"]

    def test_skill_metadata_added_to_output(self, mock_skill_class):
        """Test that skill metadata is added to output."""
        skill = mock_skill_class()
        input_data = SkillInput(data={"test": "data"})

        result = skill.run(input_data)

        assert "skill_id" in result.metadata
        assert result.metadata["skill_id"] == "mock-skill"
        assert "skill_version" in result.metadata

    def test_validation_failure_stops_execution(self):
        """Test that validation failure prevents execution."""
        class FailingValidationSkill(BaseSkill):
            @property
            def skill_id(self) -> str:
                return "failing-validation"

            @property
            def display_name(self) -> str:
                return "Failing Validation"

            @property
            def description(self) -> str:
                return "Skill with failing validation"

            def validate_input(self, input: SkillInput):
                return (False, ["Validation error"])

            def execute(self, input: SkillInput):
                # This should never be called
                raise AssertionError("Execute should not be called")

        skill = FailingValidationSkill()
        input_data = SkillInput(data={})

        result = skill.run(input_data)

        assert result.success is False
        assert result.status == SkillStatus.FAILURE
        assert "Validation error" in result.errors

    def test_skill_with_custom_version(self):
        """Test skill with custom version."""
        class CustomVersionSkill(BaseSkill):
            @property
            def skill_id(self) -> str:
                return "custom-version"

            @property
            def display_name(self) -> str:
                return "Custom Version"

            @property
            def description(self) -> str:
                return "Skill with custom version"

            @property
            def version(self) -> str:
                return "2.0.0"

            def validate_input(self, input: SkillInput):
                return (True, [])

            def execute(self, input: SkillInput):
                return SkillOutput.success_result(data={})

        skill = CustomVersionSkill()
        assert skill.version == "2.0.0"

    def test_skill_repr(self, mock_skill_class):
        """Test skill string representation."""
        skill = mock_skill_class()
        repr_str = repr(skill)

        assert "MockSkill" in repr_str
        assert "mock-skill" in repr_str
        assert "1.0.0" in repr_str
