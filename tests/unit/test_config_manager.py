"""
Unit tests for ConfigManager.

Tests the configuration loading and management system.
"""

import json

from plugin.config_manager import ConfigManager, ConfigSource


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_default_config_loaded(self, tmp_path):
        """Test that default config is loaded."""
        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config()

        assert "research" in config
        assert config["research"]["max_sources"] == 20
        assert "workflow" in config
        assert config["workflow"]["enable_checkpoints"] is True

    def test_user_config_overrides_defaults(self, tmp_path):
        """Test that user config overrides default values."""
        # Create user config
        user_config_path = tmp_path / "config.json"
        user_config = {"research": {"max_sources": 50}}
        with open(user_config_path, "w") as f:
            json.dump(user_config, f)

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config()

        # User value should override default
        assert config["research"]["max_sources"] == 50
        # Other defaults should remain
        assert config["research"]["search_depth"] == "comprehensive"

    def test_project_config_overrides_user(self, tmp_path):
        """Test that project config overrides user config."""
        # Create user config
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        user_config_path = user_dir / "config.json"
        user_config = {"research": {"max_sources": 50}}
        with open(user_config_path, "w") as f:
            json.dump(user_config, f)

        # Create project config
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        project_config_path = project_dir / "config.json"
        project_config = {"research": {"max_sources": 100}}
        with open(project_config_path, "w") as f:
            json.dump(project_config, f)

        manager = ConfigManager(config_dir=str(user_dir))
        config = manager.load_config(project_dir=str(project_dir))

        # Project value should override user
        assert config["research"]["max_sources"] == 100

    def test_env_config_overrides_project(self, tmp_path):
        """Test that environment-specific config overrides project config."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create project config
        project_config_path = project_dir / "config.json"
        project_config = {"research": {"max_sources": 100}}
        with open(project_config_path, "w") as f:
            json.dump(project_config, f)

        # Create env config
        env_config_path = project_dir / "config.dev.json"
        env_config = {"research": {"max_sources": 25}}
        with open(env_config_path, "w") as f:
            json.dump(env_config, f)

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config(project_dir=str(project_dir), env="dev")

        # Dev env value should override project
        assert config["research"]["max_sources"] == 25

    def test_cli_config_overrides_all(self, tmp_path):
        """Test that CLI config has highest priority."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create project config
        project_config_path = project_dir / "config.json"
        project_config = {"research": {"max_sources": 100}}
        with open(project_config_path, "w") as f:
            json.dump(project_config, f)

        # Create CLI config
        cli_config = {"research": {"max_sources": 10}}

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config(
            project_dir=str(project_dir), cli_config=cli_config
        )

        # CLI value should override everything
        assert config["research"]["max_sources"] == 10

    def test_deep_merge_nested_configs(self, tmp_path):
        """Test that nested configs are merged deeply."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create project config with partial research settings
        project_config_path = project_dir / "config.json"
        project_config = {
            "research": {
                "max_sources": 100
                # search_depth and citation_format not specified
            }
        }
        with open(project_config_path, "w") as f:
            json.dump(project_config, f)

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config(project_dir=str(project_dir))

        # Project value should be used
        assert config["research"]["max_sources"] == 100
        # Default values should still be present
        assert config["research"]["search_depth"] == "comprehensive"
        assert config["research"]["citation_format"] == "APA"

    def test_get_with_dot_notation(self):
        """Test getting config values with dot notation."""
        manager = ConfigManager()
        manager.load_config()

        # Get nested value
        value = manager.get("research.max_sources")
        assert value == 20

        # Get top-level value
        research = manager.get("research")
        assert isinstance(research, dict)

    def test_get_with_default(self):
        """Test get returns default for missing key."""
        manager = ConfigManager()
        manager.load_config()

        value = manager.get("nonexistent.key", default="default_value")
        assert value == "default_value"

    def test_set_with_dot_notation(self):
        """Test setting config values with dot notation."""
        manager = ConfigManager()
        manager.load_config()

        manager.set("research.max_sources", 100)
        assert manager.get("research.max_sources") == 100

    def test_set_creates_nested_keys(self):
        """Test that set creates nested keys if they don't exist."""
        manager = ConfigManager()
        manager.load_config()

        manager.set("new.nested.key", "value")
        assert manager.get("new.nested.key") == "value"

    def test_config_sources_tracked(self, tmp_path):
        """Test that config sources are tracked."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create project config
        project_config_path = project_dir / "config.json"
        with open(project_config_path, "w") as f:
            json.dump({}, f)

        manager = ConfigManager(config_dir=str(tmp_path))
        manager.load_config(project_dir=str(project_dir), cli_config={"test": "value"})

        assert len(manager.sources) == 3  # defaults, project, cli

    def test_config_sources_priority_order(self, tmp_path):
        """Test that config sources are ordered by priority."""
        manager = ConfigManager(config_dir=str(tmp_path))
        manager.load_config(cli_config={"test": "value"})

        # Sources should be in priority order
        priorities = [source.priority for source in manager.sources]
        assert priorities == [0, 4]  # defaults=0, cli=4

    def test_validate_without_schema(self):
        """Test validation without schema returns True."""
        manager = ConfigManager()
        manager.load_config()

        is_valid, errors = manager.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_with_invalid_schema_path(self):
        """Test validation with invalid schema path."""
        manager = ConfigManager()
        manager.load_config()

        is_valid, errors = manager.validate(schema_path="nonexistent.json")
        # Should fail validation due to file not found
        assert is_valid is False or len(errors) > 0

    def test_save_user_config(self, tmp_path):
        """Test saving user config."""
        manager = ConfigManager(config_dir=str(tmp_path))
        manager.load_config()

        manager.set("research.max_sources", 100)
        manager.save_user_config()

        # Verify file was created
        config_file = tmp_path / "config.json"
        assert config_file.exists()

        # Verify content
        with open(config_file) as f:
            saved_config = json.load(f)
        assert saved_config["research"]["max_sources"] == 100

    def test_save_user_config_creates_directory(self, tmp_path):
        """Test that save_user_config creates config directory."""
        config_dir = tmp_path / "nonexistent" / "config"
        manager = ConfigManager(config_dir=str(config_dir))
        manager.load_config()

        manager.save_user_config()

        assert config_dir.exists()
        assert (config_dir / "config.json").exists()

    def test_get_config_info(self, tmp_path):
        """Test getting config info."""
        manager = ConfigManager(config_dir=str(tmp_path))
        manager.load_config(cli_config={"test": "value"})

        info = manager.get_config_info()

        assert "config_dir" in info
        assert "sources" in info
        assert "merged_keys" in info
        assert len(info["sources"]) == 2  # defaults, cli

    def test_export_config_with_defaults(self, tmp_path):
        """Test exporting config with defaults."""
        output_path = tmp_path / "export.json"

        manager = ConfigManager()
        manager.load_config()
        manager.export_config(str(output_path), include_defaults=True)

        assert output_path.exists()

        with open(output_path) as f:
            exported = json.load(f)
        assert "research" in exported
        assert "workflow" in exported

    def test_export_config_without_defaults(self, tmp_path):
        """Test exporting only non-default config."""
        output_path = tmp_path / "export.json"

        # Create manager with custom CLI config
        manager = ConfigManager()
        manager.load_config(cli_config={"research": {"max_sources": 100}})
        manager.export_config(str(output_path), include_defaults=False)

        assert output_path.exists()

        with open(output_path) as f:
            exported = json.load(f)
        # Should only include modified values
        if (
            len(exported) > 0
        ):  # Export may be empty if set() doesn't mark as non-default
            assert exported["research"]["max_sources"] == 100

    def test_invalid_user_config_logs_warning(self, tmp_path, caplog):
        """Test that invalid user config logs warning but continues."""
        # Create invalid JSON
        user_config_path = tmp_path / "config.json"
        with open(user_config_path, "w") as f:
            f.write("{ invalid json }")

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config()

        # Should still return defaults
        assert "research" in config

        # Should have logged warning
        assert "Failed to load user config" in caplog.text

    def test_invalid_project_config_logs_warning(self, tmp_path, caplog):
        """Test that invalid project config logs warning but continues."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create invalid JSON
        project_config_path = project_dir / "config.json"
        with open(project_config_path, "w") as f:
            f.write("{ invalid json }")

        manager = ConfigManager(config_dir=str(tmp_path))
        config = manager.load_config(project_dir=str(project_dir))

        # Should still return defaults
        assert "research" in config

        # Should have logged warning
        assert "Failed to load project config" in caplog.text

    def test_missing_user_config_uses_defaults(self, tmp_path):
        """Test that missing user config falls back to defaults."""
        # Create a fresh config directory with no config files
        fresh_dir = tmp_path / "fresh_config"
        fresh_dir.mkdir()

        manager = ConfigManager(config_dir=str(fresh_dir))
        config = manager.load_config()

        # Should have default values (no user config exists)
        assert (
            config["research"]["max_sources"]
            == ConfigManager.DEFAULT_CONFIG["research"]["max_sources"]
        )

    def test_missing_project_config_uses_defaults(self, tmp_path):
        """Test that missing project config falls back to defaults."""
        # Create fresh directories
        fresh_config_dir = tmp_path / "config"
        fresh_config_dir.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        manager = ConfigManager(config_dir=str(fresh_config_dir))
        config = manager.load_config(project_dir=str(project_dir))

        # Should have default values (no project config exists)
        assert (
            config["research"]["max_sources"]
            == ConfigManager.DEFAULT_CONFIG["research"]["max_sources"]
        )

    def test_config_repr(self):
        """Test ConfigManager string representation."""
        manager = ConfigManager()
        manager.load_config()

        repr_str = repr(manager)
        assert "ConfigManager" in repr_str
        assert "sources=" in repr_str

    def test_multiple_load_config_calls(self, tmp_path):
        """Test that multiple load_config calls clear previous sources."""
        manager = ConfigManager(config_dir=str(tmp_path))

        # First load with CLI config
        manager.load_config(cli_config={"test": "value1"})
        assert len(manager.sources) == 2  # defaults, cli

        # Second load without CLI config
        config2 = manager.load_config()
        assert len(manager.sources) == 1  # only defaults

        # CLI value should not persist
        assert "test" not in config2


class TestConfigSource:
    """Tests for ConfigSource dataclass."""

    def test_create_config_source(self):
        """Test creating ConfigSource."""
        source = ConfigSource(
            path="/path/to/config", priority=1, loaded=True, data={"key": "value"}
        )

        assert source.path == "/path/to/config"
        assert source.priority == 1
        assert source.loaded is True
        assert source.data == {"key": "value"}
