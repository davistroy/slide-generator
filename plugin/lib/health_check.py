"""
Health check module for slide-generator plugin.
Validates configuration, dependencies, and API connectivity.
"""

import importlib
import json
import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    name: str
    status: HealthStatus
    message: str
    details: str | None = None

    @property
    def icon(self) -> str:
        icons = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.ERROR: "❌",
            HealthStatus.UNKNOWN: "❓",
        }
        return icons.get(self.status, "❓")


class HealthChecker:
    """Comprehensive health checker for slide-generator plugin."""

    def __init__(self):
        self.results: list[HealthCheckResult] = []

    def check_all(self) -> tuple[bool, list[HealthCheckResult]]:
        """Run all health checks and return overall status."""
        self.results = []

        # Run all checks
        self._check_python_version()
        self._check_anthropic_api_key()
        self._check_google_api_key()
        self._check_dependencies()
        self._check_templates()
        self._check_skill_registry()
        self._check_api_connectivity()

        # Determine overall health
        has_errors = any(r.status == HealthStatus.ERROR for r in self.results)

        return not has_errors, self.results

    def _check_python_version(self) -> None:
        """Check Python version compatibility."""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"

        if version >= (3, 11):
            status = HealthStatus.HEALTHY
            message = f"Python {version_str} (recommended)"
        elif version >= (3, 10):
            status = HealthStatus.HEALTHY
            message = f"Python {version_str} (supported)"
        else:
            status = HealthStatus.ERROR
            message = f"Python {version_str} (requires >=3.10)"

        self.results.append(
            HealthCheckResult(name="Python Version", status=status, message=message)
        )

    def _check_anthropic_api_key(self) -> None:
        """Check Anthropic API key configuration."""
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        if not api_key:
            status = HealthStatus.ERROR
            message = "Not configured"
            details = "Set ANTHROPIC_API_KEY environment variable"
        elif api_key.startswith("sk-ant-"):
            status = HealthStatus.HEALTHY
            message = f"Configured ({api_key[:12]}...)"
            details = None
        else:
            status = HealthStatus.WARNING
            message = "Configured (unusual format)"
            details = "Key doesn't match expected sk-ant-* pattern"

        self.results.append(
            HealthCheckResult(
                name="ANTHROPIC_API_KEY",
                status=status,
                message=message,
                details=details,
            )
        )

    def _check_google_api_key(self) -> None:
        """Check Google API key configuration."""
        api_key = os.environ.get("GOOGLE_API_KEY", "")

        if not api_key:
            status = HealthStatus.ERROR
            message = "Not configured"
            details = "Set GOOGLE_API_KEY environment variable"
        elif api_key.startswith("AIza"):
            status = HealthStatus.HEALTHY
            message = f"Configured ({api_key[:8]}...)"
            details = None
        else:
            status = HealthStatus.WARNING
            message = "Configured (unusual format)"
            details = "Key doesn't match expected AIza* pattern"

        self.results.append(
            HealthCheckResult(
                name="GOOGLE_API_KEY", status=status, message=message, details=details
            )
        )

    def _check_dependencies(self) -> None:
        """Check required Python packages."""
        required_packages = {
            "anthropic": "anthropic",
            "google.generativeai": "google-genai",
            "pptx": "python-pptx",
            "PIL": "Pillow",
            "frontmatter": "python-frontmatter",
            "dotenv": "python-dotenv",
        }

        # Note: Optional packages like textstat, circuitbreaker, tenacity
        # are checked separately if needed for specific features

        missing = []
        installed = []

        for import_name, package_name in required_packages.items():
            try:
                importlib.import_module(import_name.split(".")[0])
                installed.append(package_name)
            except ImportError:
                missing.append(package_name)

        if not missing:
            status = HealthStatus.HEALTHY
            message = f"All {len(installed)} required packages installed"
            details = None
        else:
            status = HealthStatus.ERROR
            message = f"{len(missing)} required packages missing"
            details = f"Missing: {', '.join(missing)}"

        self.results.append(
            HealthCheckResult(
                name="Dependencies", status=status, message=message, details=details
            )
        )

    def _check_templates(self) -> None:
        """Check available presentation templates."""
        template_dirs = ["presentation-skill/templates", "plugin/templates"]

        templates = []
        for template_dir in template_dirs:
            template_path = Path(template_dir)
            if template_path.is_dir():
                for item_path in template_path.iterdir():
                    item = item_path.name
                    if item_path.is_dir() and not item.startswith("_"):
                        templates.append(item)
                    elif item.endswith(".py") and not item.startswith("_"):
                        templates.append(item.replace(".py", ""))

        templates = list(set(templates))  # Remove duplicates

        if templates:
            status = HealthStatus.HEALTHY
            message = f"{len(templates)} templates available"
            details = f"Templates: {', '.join(sorted(templates))}"
        else:
            status = HealthStatus.WARNING
            message = "No templates found"
            details = None

        self.results.append(
            HealthCheckResult(
                name="Templates", status=status, message=message, details=details
            )
        )

    def _check_skill_registry(self) -> None:
        """Check skill registry status."""
        try:
            from plugin.skill_registry import SkillRegistry  # noqa: PLC0415

            registry = SkillRegistry()
            skills = registry.list_skills()

            if skills:
                status = HealthStatus.HEALTHY
                message = f"{len(skills)} skills registered"
                skill_names = [s.skill_id for s in skills]
                details = f"Skills: {', '.join(skill_names[:5])}"
                if len(skill_names) > 5:
                    details += f" (+{len(skill_names) - 5} more)"
            else:
                status = HealthStatus.WARNING
                message = "No skills registered"
                details = None
        except Exception as e:
            status = HealthStatus.WARNING
            message = "Registry not loaded"
            details = str(e)[:100]

        self.results.append(
            HealthCheckResult(
                name="Skill Registry", status=status, message=message, details=details
            )
        )

    def _check_api_connectivity(self) -> None:
        """Check API connectivity (lightweight test)."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        google_key = os.environ.get("GOOGLE_API_KEY")

        if not anthropic_key or not google_key:
            status = HealthStatus.WARNING
            message = "Skipped (keys not configured)"
            details = None
        else:
            try:
                import anthropic  # noqa: PLC0415

                # Just verify client can be initialized (no actual API call)
                anthropic.Anthropic(api_key=anthropic_key)
                status = HealthStatus.HEALTHY
                message = "Clients initialized"
                details = "Full connectivity test skipped to save API costs"
            except Exception as e:
                status = HealthStatus.ERROR
                message = "Client initialization failed"
                details = str(e)[:100]

        self.results.append(
            HealthCheckResult(
                name="API Connectivity", status=status, message=message, details=details
            )
        )

    def print_report(self) -> None:
        """Print formatted health check report."""
        print("\n" + "=" * 60)
        print("       SLIDE-GENERATOR HEALTH CHECK")
        print("=" * 60 + "\n")

        for result in self.results:
            print(f"{result.icon} {result.name}: {result.message}")
            if result.details:
                print(f"   └─ {result.details}")

        print("\n" + "-" * 60)

        errors = sum(1 for r in self.results if r.status == HealthStatus.ERROR)
        warnings = sum(1 for r in self.results if r.status == HealthStatus.WARNING)

        if errors == 0 and warnings == 0:
            print("✅ All checks passed. Plugin ready for use.")
        elif errors == 0:
            print(f"⚠️  {warnings} warning(s). Plugin functional with limitations.")
        else:
            print(
                f"❌ {errors} error(s), {warnings} warning(s). Fix errors before use."
            )

        print("=" * 60 + "\n")

    def to_json(self) -> str:
        """Return health check results as JSON."""
        return json.dumps(
            {
                "results": [
                    {
                        "name": r.name,
                        "status": r.status.value,
                        "message": r.message,
                        "details": r.details,
                    }
                    for r in self.results
                ],
                "summary": {
                    "total": len(self.results),
                    "healthy": sum(
                        1 for r in self.results if r.status == HealthStatus.HEALTHY
                    ),
                    "warnings": sum(
                        1 for r in self.results if r.status == HealthStatus.WARNING
                    ),
                    "errors": sum(
                        1 for r in self.results if r.status == HealthStatus.ERROR
                    ),
                },
            },
            indent=2,
        )


def run_health_check(output_json: bool = False) -> bool:
    """Run health check and return success status."""
    checker = HealthChecker()
    is_healthy, _results = checker.check_all()

    if output_json:
        print(checker.to_json())
    else:
        checker.print_report()

    return is_healthy
