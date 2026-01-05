"""
Pytest configuration and shared fixtures.

This file defines common fixtures and configuration for all tests.

Test Organization:
- tests/unit/         - Fast, isolated unit tests (mocked dependencies)
- tests/integration/  - Multi-component integration tests
- tests/fixtures/     - Test data files (JSON, MD, etc.)
- tests/helpers/      - Utility scripts (not pytest tests)
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ==============================================================================
# Directory Fixtures
# ==============================================================================


@pytest.fixture
def fixtures_dir():
    """Path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create temporary project directory for tests."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    return project_dir


# ==============================================================================
# Test Data Fixtures
# ==============================================================================


@pytest.fixture
def test_prompts(fixtures_dir):
    """Load all test prompts."""
    with open(fixtures_dir / "test_prompts.json") as f:
        data = json.load(f)
    return data["prompts"]


@pytest.fixture
def rochester_2gc_prompt(test_prompts):
    """
    Primary test prompt: Rochester 2GC carburetor rebuild.

    This is our main test case - complex, multi-presentation topic.
    Use this for comprehensive testing of the full workflow.
    """
    return test_prompts["rochester_2gc_carburetor"]


@pytest.fixture
def rochester_2gc_prompt_text(rochester_2gc_prompt):
    """Just the prompt text for Rochester 2GC."""
    return rochester_2gc_prompt["prompt"]


@pytest.fixture
def simple_prompt(test_prompts):
    """Simple prompt for quick tests."""
    return test_prompts["ai_healthcare_simple"]


@pytest.fixture
def simple_prompt_text(simple_prompt):
    """Just the prompt text for simple test."""
    return simple_prompt["prompt"]


@pytest.fixture
def complex_prompt(test_prompts):
    """Complex multi-presentation prompt."""
    return test_prompts["climate_change_complex"]


# ==============================================================================
# Sample Data Fixtures (to be populated as implementation progresses)
# ==============================================================================


@pytest.fixture
def sample_research(fixtures_dir):
    """Load sample research output."""
    research_file = fixtures_dir / "sample_research.json"
    if not research_file.exists():
        # Return mock data if file doesn't exist yet
        return {
            "sources": [],
            "summary": "Sample research summary",
            "key_themes": ["theme1", "theme2"],
        }

    with open(research_file) as f:
        return json.load(f)


@pytest.fixture
def sample_outline(fixtures_dir):
    """Load sample outline."""
    outline_file = fixtures_dir / "sample_outline.md"
    if not outline_file.exists():
        return "# Sample Outline\n\n## Slide 1: Title\n\n## Slide 2: Content"

    with open(outline_file) as f:
        return f.read()


@pytest.fixture
def sample_presentation(fixtures_dir):
    """Load sample presentation markdown."""
    pres_file = fixtures_dir / "sample_presentation.md"
    if not pres_file.exists():
        return "# Sample Presentation\n\n---\n\n## Slide 1\n\nContent here"

    with open(pres_file) as f:
        return f.read()


@pytest.fixture
def sample_images(fixtures_dir):
    """Path to sample images directory."""
    images_dir = fixtures_dir / "sample_images"
    if not images_dir.exists():
        images_dir.mkdir(parents=True)
    return images_dir


@pytest.fixture
def style_config(fixtures_dir):
    """Load sample style config."""
    style_file = fixtures_dir / "cfa_style.json"
    if not style_file.exists():
        # Return mock style config
        return {
            "brand_colors": ["#DD0033", "#004F71"],
            "style": "professional, clean, modern",
            "tone": "corporate",
        }

    with open(style_file) as f:
        return json.load(f)


# ==============================================================================
# Mock API Fixtures
# ==============================================================================


@pytest.fixture
def mock_gemini(mocker):
    """Mock Gemini API client."""
    mock = mocker.patch("plugin.lib.gemini_client.GeminiClient")

    # Configure default mock behavior
    mock_instance = mock.return_value
    mock_instance.generate.return_value = "Mock Gemini response"

    return mock_instance


@pytest.fixture
def mock_search_api(mocker):
    """Mock search API."""
    mock = mocker.patch("plugin.lib.web_search.WebSearch")

    # Configure default mock behavior
    mock_instance = mock.return_value
    mock_instance.search.return_value = [
        {
            "url": "https://example.com/result1",
            "title": "Mock Result 1",
            "snippet": "This is a mock search result",
        }
    ]

    return mock_instance


@pytest.fixture
def mock_apis(mock_gemini, mock_search_api, mock_claude):
    """Convenience fixture for all mocked APIs."""
    return {"gemini": mock_gemini, "search": mock_search_api, "claude": mock_claude}


@pytest.fixture
def mock_claude(mocker):
    """Mock Claude/Anthropic API client."""
    mock = mocker.patch("plugin.lib.claude_client.ClaudeClient")

    # Configure default mock behavior
    mock_instance = mock.return_value
    mock_instance.complete.return_value = "Mock Claude response"
    mock_instance.generate.return_value = "Mock Claude generated content"

    # Mock message response structure
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Mock response text")]
    mock_instance.messages.create.return_value = mock_message

    return mock_instance


@pytest.fixture
def mock_anthropic(mocker):
    """Mock the anthropic module directly."""
    mock = mocker.patch("anthropic.Anthropic")

    mock_instance = mock.return_value
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="Mock Anthropic response")]
    mock_instance.messages.create.return_value = mock_message

    return mock_instance


# ==============================================================================
# Environment Fixtures
# ==============================================================================


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set mock environment variables for API keys."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key-not-real")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key-not-real")


@pytest.fixture
def has_api_keys():
    """Check if real API keys are available."""
    return (
        os.environ.get("ANTHROPIC_API_KEY") is not None
        and os.environ.get("GOOGLE_API_KEY") is not None
        and not os.environ.get("ANTHROPIC_API_KEY", "").startswith("test-")
    )


# ==============================================================================
# User Input Mocking
# ==============================================================================


@pytest.fixture
def mock_input(mocker):
    """Mock user input for checkpoint testing."""
    return mocker.patch("builtins.input")


@pytest.fixture
def mock_input_continue(mock_input):
    """Mock user input to always continue at checkpoints."""
    mock_input.return_value = "1"  # Continue
    return mock_input


@pytest.fixture
def mock_input_abort(mock_input):
    """Mock user input to abort at checkpoints."""
    mock_input.return_value = "4"  # Abort
    return mock_input


# ==============================================================================
# CLI Testing
# ==============================================================================


@pytest.fixture
def cli_runner():
    """CLI test runner using click.testing."""
    try:
        from click.testing import CliRunner

        return CliRunner()
    except ImportError:
        # Fallback if click not installed
        return None


# ==============================================================================
# Plugin Component Fixtures
# ==============================================================================


@pytest.fixture
def skill_registry():
    """Clean SkillRegistry instance."""
    from plugin.skill_registry import SkillRegistry

    # Clear registry before test
    registry = SkillRegistry()
    registry.clear()

    yield registry

    # Clear after test
    registry.clear()


@pytest.fixture
def checkpoint_handler():
    """CheckpointHandler in non-interactive mode."""
    from plugin.checkpoint_handler import CheckpointHandler

    return CheckpointHandler(interactive=False, auto_approve=True)


@pytest.fixture
def config_manager(temp_project_dir):
    """ConfigManager instance."""
    from plugin.config_manager import ConfigManager

    return ConfigManager()


@pytest.fixture
def workflow_orchestrator(checkpoint_handler, config_manager):
    """WorkflowOrchestrator instance."""
    from plugin.workflow_orchestrator import WorkflowOrchestrator

    config = config_manager.load_config()
    return WorkflowOrchestrator(checkpoint_handler=checkpoint_handler, config=config)


# ==============================================================================
# Mock Skills for Testing
# ==============================================================================


@pytest.fixture
def mock_skill_class():
    """Mock skill class for testing."""
    from plugin.base_skill import BaseSkill, SkillInput, SkillOutput

    class MockSkill(BaseSkill):
        @property
        def skill_id(self) -> str:
            return "mock-skill"

        @property
        def display_name(self) -> str:
            return "Mock Skill"

        @property
        def description(self) -> str:
            return "A mock skill for testing"

        def validate_input(self, input: SkillInput) -> tuple[bool, list[str]]:
            return (True, [])

        def execute(self, input: SkillInput) -> SkillOutput:
            return SkillOutput.success_result(
                data={"result": "success"}, artifacts=["output.json"]
            )

    return MockSkill


@pytest.fixture
def mock_failing_skill_class():
    """Mock skill that always fails."""
    from plugin.base_skill import BaseSkill, SkillInput, SkillOutput

    class FailingSkill(BaseSkill):
        @property
        def skill_id(self) -> str:
            return "failing-skill"

        @property
        def display_name(self) -> str:
            return "Failing Skill"

        @property
        def description(self) -> str:
            return "A skill that always fails"

        def validate_input(self, input: SkillInput) -> tuple[bool, list[str]]:
            return (True, [])

        def execute(self, input: SkillInput) -> SkillOutput:
            return SkillOutput.failure_result(errors=["Mock failure"])

    return FailingSkill


# ==============================================================================
# Pytest Configuration
# ==============================================================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, multi-component)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full workflows)"
    )
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "quality: Quality validation tests")
    config.addinivalue_line("markers", "manual: Manual test procedures")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "api: Tests that call external APIs")
    config.addinivalue_line("markers", "windows_only: Tests that only run on Windows")
    config.addinivalue_line("markers", "experimental: Tests for experimental features")
