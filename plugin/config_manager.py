"""
Configuration manager for the presentation generation plugin.

Handles loading, validation, and merging of configuration from multiple sources.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ConfigSource:
    """Information about a configuration source."""

    path: str
    priority: int  # Higher priority overrides lower
    loaded: bool
    data: dict[str, Any]


class ConfigManager:
    """
    Manages plugin configuration from multiple sources.

    Configuration sources (in priority order):
    1. Command-line arguments (highest priority)
    2. Environment-specific config (e.g., config.dev.json)
    3. Project config (project root)
    4. User config (~/.config/presentation-plugin/)
    5. Default config (lowest priority)
    """

    DEFAULT_CONFIG = {
        "research": {
            "max_sources": 20,
            "search_depth": "comprehensive",
            "citation_format": "APA",
        },
        "content": {
            "tone": "professional",
            "reading_level": "college",
            "max_bullets_per_slide": 5,
        },
        "images": {
            "default_resolution": "high",
            "style_config": "templates/cfa_style.json",
        },
        "workflow": {
            "enable_checkpoints": True,
            "auto_split_presentations": True,
            "max_slides_per_presentation": 30,
        },
        "api": {
            "gemini_model": "gemini-3-pro-image-preview",
            "timeout_seconds": 60,
            "retry_attempts": 3,
        },
    }

    def __init__(self, config_dir: str | None = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Optional custom config directory
        """
        self.config_dir = (
            Path(config_dir) if config_dir else self._get_default_config_dir()
        )
        self.sources: list[ConfigSource] = []
        self.merged_config: dict[str, Any] = {}

    def _get_default_config_dir(self) -> Path:
        """Get default config directory based on platform."""
        import os
        import platform

        if platform.system() == "Windows":
            base = Path(os.environ.get("APPDATA", "~")).expanduser()
        else:
            base = Path.home() / ".config"

        return base / "presentation-plugin"

    def load_config(
        self,
        project_dir: str | None = None,
        env: str | None = None,
        cli_config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Load and merge configuration from all sources.

        Args:
            project_dir: Project directory (looks for config.json)
            env: Environment name (e.g., 'dev', 'prod')
            cli_config: Configuration from command-line arguments

        Returns:
            Merged configuration dictionary
        """
        self.sources.clear()

        # Load in priority order (lowest to highest)

        # 1. Default config
        self.sources.append(
            ConfigSource(
                path="<defaults>",
                priority=0,
                loaded=True,
                data=self.DEFAULT_CONFIG.copy(),
            )
        )

        # 2. User config
        user_config_path = self.config_dir / "config.json"
        if user_config_path.exists():
            try:
                data = self._load_json_file(user_config_path)
                self.sources.append(
                    ConfigSource(
                        path=str(user_config_path), priority=1, loaded=True, data=data
                    )
                )
            except Exception as e:
                print(f"Warning: Failed to load user config: {e}")

        # 3. Project config
        if project_dir:
            project_config_path = Path(project_dir) / "config.json"
            if project_config_path.exists():
                try:
                    data = self._load_json_file(project_config_path)
                    self.sources.append(
                        ConfigSource(
                            path=str(project_config_path),
                            priority=2,
                            loaded=True,
                            data=data,
                        )
                    )
                except Exception as e:
                    print(f"Warning: Failed to load project config: {e}")

        # 4. Environment-specific config
        if env and project_dir:
            env_config_path = Path(project_dir) / f"config.{env}.json"
            if env_config_path.exists():
                try:
                    data = self._load_json_file(env_config_path)
                    self.sources.append(
                        ConfigSource(
                            path=str(env_config_path),
                            priority=3,
                            loaded=True,
                            data=data,
                        )
                    )
                except Exception as e:
                    print(f"Warning: Failed to load env config: {e}")

        # 5. CLI config (highest priority)
        if cli_config:
            self.sources.append(
                ConfigSource(
                    path="<cli-args>", priority=4, loaded=True, data=cli_config
                )
            )

        # Merge all configs
        self.merged_config = self._merge_configs()

        return self.merged_config

    def _load_json_file(self, path: Path) -> dict[str, Any]:
        """Load JSON configuration file."""
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _merge_configs(self) -> dict[str, Any]:
        """
        Merge all config sources.

        Higher priority sources override lower priority.
        """
        merged = {}

        # Sort by priority
        sorted_sources = sorted(self.sources, key=lambda s: s.priority)

        for source in sorted_sources:
            merged = self._deep_merge(merged, source.data)

        return merged

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Args:
            key: Key in dot notation (e.g., 'research.max_sources')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.merged_config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key.

        Args:
            key: Key in dot notation
            value: Value to set
        """
        keys = key.split(".")
        target = self.merged_config

        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        target[keys[-1]] = value

    def validate(self, schema_path: str | None = None) -> tuple[bool, list[str]]:
        """
        Validate configuration against schema.

        Args:
            schema_path: Path to JSON schema file

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not schema_path:
            # No schema provided, skip validation
            return (True, [])

        try:
            import jsonschema
        except ImportError:
            return (True, ["jsonschema not installed, skipping validation"])

        try:
            with open(schema_path) as f:
                schema = json.load(f)

            jsonschema.validate(instance=self.merged_config, schema=schema)
            return (True, [])

        except jsonschema.ValidationError as e:
            return (False, [str(e)])
        except Exception as e:
            return (False, [f"Validation error: {e!s}"])

    def save_user_config(self, config: dict[str, Any] | None = None) -> None:
        """
        Save configuration to user config file.

        Args:
            config: Configuration to save (uses merged_config if None)
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        config_to_save = config or self.merged_config
        config_path = self.config_dir / "config.json"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_to_save, f, indent=2)

    def get_config_info(self) -> dict[str, Any]:
        """
        Get information about loaded configuration sources.

        Returns:
            Dictionary with config info
        """
        return {
            "config_dir": str(self.config_dir),
            "sources": [
                {
                    "path": source.path,
                    "priority": source.priority,
                    "loaded": source.loaded,
                }
                for source in sorted(self.sources, key=lambda s: s.priority)
            ],
            "merged_keys": list(self.merged_config.keys()),
        }

    def export_config(self, output_path: str, include_defaults: bool = False) -> None:
        """
        Export current configuration to a file.

        Args:
            output_path: Path to export to
            include_defaults: If True, include default values
        """
        if include_defaults:
            config_to_export = self.merged_config
        else:
            # Export only non-default values
            config_to_export = self._get_non_default_config()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config_to_export, f, indent=2)

    def _get_non_default_config(self) -> dict[str, Any]:
        """Get configuration with default values removed."""

        def remove_defaults(
            merged: dict[str, Any], defaults: dict[str, Any]
        ) -> dict[str, Any]:
            result = {}
            for key, value in merged.items():
                if key not in defaults:
                    result[key] = value
                elif isinstance(value, dict) and isinstance(defaults[key], dict):
                    nested = remove_defaults(value, defaults[key])
                    if nested:
                        result[key] = nested
                elif value != defaults[key]:
                    result[key] = value
            return result

        return remove_defaults(self.merged_config, self.DEFAULT_CONFIG)

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConfigManager sources={len(self.sources)} keys={len(self.merged_config)}>"
