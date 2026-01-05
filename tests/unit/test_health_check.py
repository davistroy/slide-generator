"""
Unit tests for health check module.
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock

from plugin.lib.health_check import (
    HealthChecker, HealthCheckResult, HealthStatus, run_health_check
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.WARNING.value == "warning"
        assert HealthStatus.ERROR.value == "error"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestHealthCheckResult:
    """Tests for HealthCheckResult dataclass."""

    def test_healthy_result(self):
        """Test healthy result creation."""
        result = HealthCheckResult(
            name="Test Check",
            status=HealthStatus.HEALTHY,
            message="All good"
        )
        assert result.icon == "✅"
        assert result.details is None

    def test_warning_result(self):
        """Test warning result creation."""
        result = HealthCheckResult(
            name="Test Check",
            status=HealthStatus.WARNING,
            message="Minor issue",
            details="Check XYZ"
        )
        assert result.icon == "⚠️"
        assert result.details == "Check XYZ"

    def test_error_result(self):
        """Test error result creation."""
        result = HealthCheckResult(
            name="Test Check",
            status=HealthStatus.ERROR,
            message="Critical error"
        )
        assert result.icon == "❌"


class TestHealthChecker:
    """Tests for HealthChecker class."""

    def test_initialization(self):
        """Test checker initialization."""
        checker = HealthChecker()
        assert checker.results == []

    def test_python_version_check(self):
        """Test Python version checking."""
        checker = HealthChecker()
        checker._check_python_version()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.name == "Python Version"
        # Should be healthy for Python 3.10+
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.ERROR]

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test123'})
    def test_anthropic_key_valid_format(self):
        """Test Anthropic key with valid format."""
        checker = HealthChecker()
        checker._check_anthropic_api_key()

        result = checker.results[0]
        assert result.status == HealthStatus.HEALTHY

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}, clear=False)
    def test_anthropic_key_missing(self):
        """Test missing Anthropic key."""
        checker = HealthChecker()
        # Remove key if it exists
        if 'ANTHROPIC_API_KEY' in os.environ:
            del os.environ['ANTHROPIC_API_KEY']
        checker._check_anthropic_api_key()

        result = checker.results[0]
        assert result.status == HealthStatus.ERROR

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'AIzaSyTest123'})
    def test_google_key_valid_format(self):
        """Test Google key with valid format."""
        checker = HealthChecker()
        checker._check_google_api_key()

        result = checker.results[0]
        assert result.status == HealthStatus.HEALTHY

    def test_dependencies_check(self):
        """Test dependencies checking."""
        checker = HealthChecker()
        checker._check_dependencies()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.name == "Dependencies"
        # Status depends on installed packages
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.ERROR]

    def test_templates_check(self):
        """Test templates checking."""
        checker = HealthChecker()
        checker._check_templates()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.name == "Templates"

    def test_skill_registry_check(self):
        """Test skill registry checking."""
        checker = HealthChecker()
        checker._check_skill_registry()

        assert len(checker.results) == 1
        result = checker.results[0]
        assert result.name == "Skill Registry"

    def test_check_all_runs_all_checks(self):
        """Test that check_all runs all checks."""
        checker = HealthChecker()
        is_healthy, results = checker.check_all()

        # Should have run multiple checks
        assert len(results) >= 6
        assert isinstance(is_healthy, bool)

    def test_to_json(self):
        """Test JSON output generation."""
        checker = HealthChecker()
        checker.results = [
            HealthCheckResult("Test", HealthStatus.HEALTHY, "OK"),
            HealthCheckResult("Test2", HealthStatus.WARNING, "Warn")
        ]

        json_output = checker.to_json()
        data = json.loads(json_output)

        assert "results" in data
        assert "summary" in data
        assert data["summary"]["total"] == 2
        assert data["summary"]["healthy"] == 1
        assert data["summary"]["warnings"] == 1


class TestRunHealthCheck:
    """Tests for run_health_check function."""

    def test_run_health_check_returns_bool(self, capsys):
        """Test that run_health_check returns boolean."""
        result = run_health_check(output_json=False)
        assert isinstance(result, bool)

    def test_run_health_check_json_output(self, capsys):
        """Test JSON output mode."""
        run_health_check(output_json=True)
        captured = capsys.readouterr()

        # Should be valid JSON
        data = json.loads(captured.out)
        assert "results" in data
        assert "summary" in data
