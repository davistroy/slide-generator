"""
Unit tests for SkillRegistry.

Tests the centralized registry for skill discovery and management.
"""

import pytest

from plugin.base_skill import BaseSkill, SkillOutput
from plugin.skill_registry import SkillMetadata, SkillRegistry


class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def test_singleton_instance(self):
        """Test that SkillRegistry is a singleton."""
        registry1 = SkillRegistry()
        registry2 = SkillRegistry()

        assert registry1 is registry2

    def test_register_skill_success(self, skill_registry, mock_skill_class):
        """Test successful skill registration."""
        skill_registry.register_skill(mock_skill_class)

        assert skill_registry.is_registered("mock-skill")

    def test_register_skill_stores_metadata(self, skill_registry, mock_skill_class):
        """Test that registration stores skill metadata."""
        skill_registry.register_skill(mock_skill_class)

        metadata = skill_registry.get_metadata("mock-skill")
        assert metadata.skill_id == "mock-skill"
        assert metadata.display_name == "Mock Skill"
        assert metadata.description == "A mock skill for testing"
        assert metadata.skill_class == mock_skill_class

    def test_register_skill_duplicate_without_override_fails(
        self, skill_registry, mock_skill_class
    ):
        """Test that duplicate registration without override raises ValueError."""
        skill_registry.register_skill(mock_skill_class)

        with pytest.raises(ValueError, match="already registered"):
            skill_registry.register_skill(mock_skill_class)

    def test_register_skill_duplicate_with_override_succeeds(
        self, skill_registry, mock_skill_class
    ):
        """Test that duplicate registration with override=True succeeds."""
        skill_registry.register_skill(mock_skill_class)
        skill_registry.register_skill(mock_skill_class, override=True)

        # Should not raise error
        assert skill_registry.is_registered("mock-skill")

    def test_register_invalid_skill_raises_error(self, skill_registry):
        """Test that registering non-BaseSkill raises TypeError."""

        class NotASkill:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseSkill"):
            skill_registry.register_skill(NotASkill)

    def test_unregister_skill_success(self, skill_registry, mock_skill_class):
        """Test successful skill unregistration."""
        skill_registry.register_skill(mock_skill_class)
        result = skill_registry.unregister_skill("mock-skill")

        assert result is True
        assert not skill_registry.is_registered("mock-skill")

    def test_unregister_nonexistent_skill_returns_false(self, skill_registry):
        """Test that unregistering non-existent skill returns False."""
        result = skill_registry.unregister_skill("nonexistent")

        assert result is False

    def test_get_skill_success(self, skill_registry, mock_skill_class):
        """Test retrieving registered skill."""
        skill_registry.register_skill(mock_skill_class)

        skill = skill_registry.get_skill("mock-skill")

        assert isinstance(skill, mock_skill_class)
        assert skill.skill_id == "mock-skill"

    def test_get_skill_with_config(self, skill_registry, mock_skill_class):
        """Test retrieving skill with custom config."""
        skill_registry.register_skill(mock_skill_class)

        config = {"test_config": "value"}
        skill = skill_registry.get_skill("mock-skill", config=config)

        assert skill.config == config

    def test_get_skill_not_found_raises_keyerror(self, skill_registry):
        """Test that getting non-existent skill raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            skill_registry.get_skill("nonexistent")

    def test_get_skill_error_message_lists_available(
        self, skill_registry, mock_skill_class
    ):
        """Test that KeyError message lists available skills."""
        skill_registry.register_skill(mock_skill_class)

        with pytest.raises(KeyError, match="mock-skill"):
            skill_registry.get_skill("nonexistent")

    def test_get_metadata_success(self, skill_registry, mock_skill_class):
        """Test retrieving skill metadata."""
        skill_registry.register_skill(mock_skill_class)

        metadata = skill_registry.get_metadata("mock-skill")

        assert isinstance(metadata, SkillMetadata)
        assert metadata.skill_id == "mock-skill"

    def test_get_metadata_not_found_raises_keyerror(self, skill_registry):
        """Test that getting metadata for non-existent skill raises KeyError."""
        with pytest.raises(KeyError):
            skill_registry.get_metadata("nonexistent")

    def test_list_skills(self, skill_registry, mock_skill_class):
        """Test listing all registered skills."""
        skill_registry.register_skill(mock_skill_class)

        skills = skill_registry.list_skills()

        assert len(skills) == 1
        assert skills[0].skill_id == "mock-skill"

    def test_list_skills_multiple(
        self, skill_registry, mock_skill_class, mock_failing_skill_class
    ):
        """Test listing multiple registered skills."""
        skill_registry.register_skill(mock_skill_class)
        skill_registry.register_skill(mock_failing_skill_class)

        skills = skill_registry.list_skills()

        assert len(skills) == 2
        skill_ids = [s.skill_id for s in skills]
        assert "mock-skill" in skill_ids
        assert "failing-skill" in skill_ids

    def test_list_skills_with_dependencies(self, skill_registry):
        """Test listing skills with dependency info."""

        class SkillWithDeps(BaseSkill):
            @property
            def skill_id(self):
                return "skill-with-deps"

            @property
            def display_name(self):
                return "Skill With Deps"

            @property
            def description(self):
                return "Test skill"

            @property
            def dependencies(self):
                return ["dep-1", "dep-2"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill_registry.register_skill(SkillWithDeps)

        skills = skill_registry.list_skills(include_dependencies=True)

        skill_with_deps = next(s for s in skills if s.skill_id == "skill-with-deps")
        assert skill_with_deps.dependencies == ["dep-1", "dep-2"]

    def test_list_skills_without_dependencies(self, skill_registry):
        """Test that dependencies can be filtered out."""

        class SkillWithDeps(BaseSkill):
            @property
            def skill_id(self):
                return "skill-with-deps"

            @property
            def display_name(self):
                return "Skill With Deps"

            @property
            def description(self):
                return "Test skill"

            @property
            def dependencies(self):
                return ["dep-1"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill_registry.register_skill(SkillWithDeps)

        skills = skill_registry.list_skills(include_dependencies=False)

        skill_with_deps = next(s for s in skills if s.skill_id == "skill-with-deps")
        assert skill_with_deps.dependencies == []

    def test_is_registered(self, skill_registry, mock_skill_class):
        """Test checking if skill is registered."""
        assert not skill_registry.is_registered("mock-skill")

        skill_registry.register_skill(mock_skill_class)

        assert skill_registry.is_registered("mock-skill")

    def test_validate_skill_success(self, skill_registry, mock_skill_class):
        """Test validating a valid skill."""
        skill = mock_skill_class()

        is_valid, errors = skill_registry.validate_skill(skill)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_skill_missing_skill_id(self, skill_registry):
        """Test validation fails for skill without skill_id."""

        class InvalidSkill(BaseSkill):
            # Missing skill_id property

            @property
            def display_name(self):
                return "Invalid"

            @property
            def description(self):
                return "Test"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        # Can't instantiate because skill_id is abstract
        # So we'll create a mock that has the property but it's empty
        class SkillWithEmptyId(BaseSkill):
            @property
            def skill_id(self):
                return ""

            @property
            def display_name(self):
                return "Test"

            @property
            def description(self):
                return "Test"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill = SkillWithEmptyId()
        is_valid, errors = skill_registry.validate_skill(skill)

        assert is_valid is False
        assert any("skill_id" in error for error in errors)

    def test_validate_skill_missing_methods(self, skill_registry, mocker):
        """Test validation fails for skill without required methods."""

        # Create a skill and mock away a required method
        class SkillMissingMethods(BaseSkill):
            @property
            def skill_id(self):
                return "test"

            @property
            def display_name(self):
                return "Test"

            @property
            def description(self):
                return "Test"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill = SkillMissingMethods()

        # Mock hasattr to return False for validate_input
        original_hasattr = hasattr

        def mock_hasattr(obj, name):
            if obj is skill and name == "validate_input":
                return False
            return original_hasattr(obj, name)

        mocker.patch("builtins.hasattr", side_effect=mock_hasattr)

        is_valid, errors = skill_registry.validate_skill(skill)

        assert is_valid is False
        assert any("validate_input" in error for error in errors)

    def test_resolve_dependencies_no_deps(self, skill_registry, mock_skill_class):
        """Test dependency resolution for skill with no dependencies."""
        skill_registry.register_skill(mock_skill_class)

        resolved = skill_registry.resolve_dependencies("mock-skill")

        assert resolved == ["mock-skill"]

    def test_resolve_dependencies_with_deps(self, skill_registry):
        """Test dependency resolution for skill with dependencies."""

        class Dep1(BaseSkill):
            @property
            def skill_id(self):
                return "dep-1"

            @property
            def display_name(self):
                return "Dep 1"

            @property
            def description(self):
                return "Dependency 1"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        class Dep2(BaseSkill):
            @property
            def skill_id(self):
                return "dep-2"

            @property
            def display_name(self):
                return "Dep 2"

            @property
            def description(self):
                return "Dependency 2"

            @property
            def dependencies(self):
                return ["dep-1"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        class MainSkill(BaseSkill):
            @property
            def skill_id(self):
                return "main"

            @property
            def display_name(self):
                return "Main"

            @property
            def description(self):
                return "Main skill"

            @property
            def dependencies(self):
                return ["dep-2"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill_registry.register_skill(Dep1)
        skill_registry.register_skill(Dep2)
        skill_registry.register_skill(MainSkill)

        resolved = skill_registry.resolve_dependencies("main")

        # Should be in order: dep-1, dep-2, main
        assert resolved == ["dep-1", "dep-2", "main"]

    def test_resolve_dependencies_circular_raises_error(self, skill_registry):
        """Test that circular dependencies raise ValueError."""

        class SkillA(BaseSkill):
            @property
            def skill_id(self):
                return "skill-a"

            @property
            def display_name(self):
                return "Skill A"

            @property
            def description(self):
                return "Test"

            @property
            def dependencies(self):
                return ["skill-b"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        class SkillB(BaseSkill):
            @property
            def skill_id(self):
                return "skill-b"

            @property
            def display_name(self):
                return "Skill B"

            @property
            def description(self):
                return "Test"

            @property
            def dependencies(self):
                return ["skill-a"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill_registry.register_skill(SkillA)
        skill_registry.register_skill(SkillB)

        with pytest.raises(ValueError, match="Circular dependency"):
            skill_registry.resolve_dependencies("skill-a")

    def test_resolve_dependencies_missing_dep_raises_error(self, skill_registry):
        """Test that missing dependency raises KeyError."""

        class SkillWithMissingDep(BaseSkill):
            @property
            def skill_id(self):
                return "skill"

            @property
            def display_name(self):
                return "Skill"

            @property
            def description(self):
                return "Test"

            @property
            def dependencies(self):
                return ["nonexistent"]

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        skill_registry.register_skill(SkillWithMissingDep)

        with pytest.raises(KeyError, match="not found"):
            skill_registry.resolve_dependencies("skill")

    def test_clear_registry(self, skill_registry, mock_skill_class):
        """Test clearing the registry."""
        skill_registry.register_skill(mock_skill_class)
        assert skill_registry.is_registered("mock-skill")

        skill_registry.clear()

        assert not skill_registry.is_registered("mock-skill")
        assert len(skill_registry.list_skills()) == 0

    def test_skill_metadata_repr(self):
        """Test SkillMetadata string representation."""
        from plugin.base_skill import BaseSkill, SkillOutput

        class TestSkill(BaseSkill):
            @property
            def skill_id(self):
                return "test"

            @property
            def display_name(self):
                return "Test"

            @property
            def description(self):
                return "Test"

            @property
            def version(self):
                return "2.0.0"

            def validate_input(self, input):
                return (True, [])

            def execute(self, input):
                return SkillOutput.success_result(data={})

        metadata = SkillMetadata(
            skill_id="test",
            display_name="Test",
            description="Test",
            version="2.0.0",
            skill_class=TestSkill,
            dependencies=[],
        )

        repr_str = repr(metadata)
        assert "test" in repr_str
        assert "2.0.0" in repr_str

    def test_registry_repr(self, skill_registry, mock_skill_class):
        """Test SkillRegistry string representation."""
        skill_registry.register_skill(mock_skill_class)

        repr_str = repr(skill_registry)
        assert "SkillRegistry" in repr_str
        assert "1" in repr_str or "skills=1" in repr_str
