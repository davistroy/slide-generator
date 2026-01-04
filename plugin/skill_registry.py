"""
Centralized registry for discovering and managing skills.

The SkillRegistry provides a single point of registration and discovery
for all presentation generation skills.
"""

from typing import Dict, List, Type, Optional
from dataclasses import dataclass
from .base_skill import BaseSkill


@dataclass
class SkillMetadata:
    """
    Metadata about a registered skill.

    Attributes:
        skill_id: Unique identifier
        display_name: Human-readable name
        description: Brief description
        version: Skill version
        skill_class: Python class implementing the skill
        dependencies: List of skill IDs this skill depends on
    """
    skill_id: str
    display_name: str
    description: str
    version: str
    skill_class: Type[BaseSkill]
    dependencies: List[str]

    def __repr__(self) -> str:
        return f"<SkillMetadata id='{self.skill_id}' version='{self.version}'>"


class SkillRegistry:
    """
    Centralized registry for all presentation generation skills.

    Singleton pattern - only one registry instance exists per application.
    """

    _instance: Optional["SkillRegistry"] = None
    _skills: Dict[str, SkillMetadata] = {}

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._skills = {}
        return cls._instance

    @classmethod
    def register_skill(
        cls,
        skill_class: Type[BaseSkill],
        override: bool = False
    ) -> None:
        """
        Register a skill with the plugin system.

        Args:
            skill_class: Class implementing BaseSkill
            override: If True, allow overriding existing registration

        Raises:
            ValueError: If skill_id already registered and override=False
            TypeError: If skill_class doesn't inherit from BaseSkill
        """
        # Validate skill class
        if not issubclass(skill_class, BaseSkill):
            raise TypeError(
                f"Skill class {skill_class.__name__} must inherit from BaseSkill"
            )

        # Create temporary instance to get metadata
        temp_skill = skill_class()

        skill_id = temp_skill.skill_id

        # Check for duplicate registration
        if skill_id in cls._instance._skills and not override:
            raise ValueError(
                f"Skill '{skill_id}' is already registered. "
                f"Use override=True to replace."
            )

        # Create metadata
        metadata = SkillMetadata(
            skill_id=skill_id,
            display_name=temp_skill.display_name,
            description=temp_skill.description,
            version=temp_skill.version,
            skill_class=skill_class,
            dependencies=temp_skill.dependencies
        )

        # Register
        cls._instance._skills[skill_id] = metadata

    @classmethod
    def unregister_skill(cls, skill_id: str) -> bool:
        """
        Unregister a skill.

        Args:
            skill_id: ID of skill to unregister

        Returns:
            True if skill was unregistered, False if not found
        """
        if skill_id in cls._instance._skills:
            del cls._instance._skills[skill_id]
            return True
        return False

    @classmethod
    def get_skill(
        cls,
        skill_id: str,
        config: Optional[Dict] = None
    ) -> BaseSkill:
        """
        Retrieve and instantiate a registered skill.

        Args:
            skill_id: ID of skill to retrieve
            config: Optional configuration to pass to skill constructor

        Returns:
            Instantiated skill

        Raises:
            KeyError: If skill_id not found
        """
        if skill_id not in cls._instance._skills:
            raise KeyError(
                f"Skill '{skill_id}' not found. "
                f"Available skills: {list(cls._instance._skills.keys())}"
            )

        metadata = cls._instance._skills[skill_id]
        return metadata.skill_class(config=config)

    @classmethod
    def get_metadata(cls, skill_id: str) -> SkillMetadata:
        """
        Get metadata for a registered skill without instantiating it.

        Args:
            skill_id: ID of skill

        Returns:
            Skill metadata

        Raises:
            KeyError: If skill_id not found
        """
        if skill_id not in cls._instance._skills:
            raise KeyError(f"Skill '{skill_id}' not found")

        return cls._instance._skills[skill_id]

    @classmethod
    def list_skills(cls, include_dependencies: bool = False) -> List[SkillMetadata]:
        """
        List all registered skills.

        Args:
            include_dependencies: If True, include dependency information

        Returns:
            List of skill metadata
        """
        skills = list(cls._instance._skills.values())

        if include_dependencies:
            return skills

        # Filter out dependency info if not needed
        return [
            SkillMetadata(
                skill_id=s.skill_id,
                display_name=s.display_name,
                description=s.description,
                version=s.version,
                skill_class=s.skill_class,
                dependencies=[]
            )
            for s in skills
        ]

    @classmethod
    def is_registered(cls, skill_id: str) -> bool:
        """
        Check if a skill is registered.

        Args:
            skill_id: ID to check

        Returns:
            True if registered, False otherwise
        """
        return skill_id in cls._instance._skills

    @classmethod
    def validate_skill(cls, skill: BaseSkill) -> tuple[bool, List[str]]:
        """
        Validate that a skill properly implements the BaseSkill interface.

        Args:
            skill: Skill instance to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required properties
        if not hasattr(skill, 'skill_id') or not skill.skill_id:
            errors.append("Skill must have a non-empty skill_id")

        if not hasattr(skill, 'display_name') or not skill.display_name:
            errors.append("Skill must have a non-empty display_name")

        if not hasattr(skill, 'description') or not skill.description:
            errors.append("Skill must have a non-empty description")

        # Check required methods
        required_methods = ['validate_input', 'execute']
        for method_name in required_methods:
            if not hasattr(skill, method_name):
                errors.append(f"Skill must implement {method_name}() method")

        return (len(errors) == 0, errors)

    @classmethod
    def resolve_dependencies(cls, skill_id: str) -> List[str]:
        """
        Resolve the dependency chain for a skill.

        Args:
            skill_id: ID of skill to resolve dependencies for

        Returns:
            Ordered list of skill IDs (dependencies first, then skill_id)

        Raises:
            KeyError: If skill or any dependency not found
            ValueError: If circular dependency detected
        """
        if skill_id not in cls._instance._skills:
            raise KeyError(f"Skill '{skill_id}' not found")

        resolved = []
        seen = set()

        def resolve(current_id: str, chain: List[str]):
            if current_id in chain:
                raise ValueError(
                    f"Circular dependency detected: {' -> '.join(chain + [current_id])}"
                )

            if current_id in seen:
                return

            metadata = cls._instance._skills[current_id]
            chain.append(current_id)

            for dep_id in metadata.dependencies:
                if dep_id not in cls._instance._skills:
                    raise KeyError(
                        f"Dependency '{dep_id}' for skill '{current_id}' not found"
                    )
                resolve(dep_id, chain[:])

            seen.add(current_id)
            resolved.append(current_id)

        resolve(skill_id, [])
        return resolved

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered skills.

        Primarily for testing purposes.
        """
        cls._instance._skills.clear()

    def __repr__(self) -> str:
        """String representation of the registry."""
        return f"<SkillRegistry skills={len(self._skills)}>"
