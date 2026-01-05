"""
Unit tests for CLI module.

Tests the command-line interface argument parsing and command structure.
Note: Full CLI integration tests are in tests/integration/test_cli_integration.py
"""

import pytest

from plugin.cli import create_parser


class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_create_parser_returns_parser(self):
        """Test that create_parser returns an ArgumentParser."""
        parser = create_parser()

        assert parser is not None
        assert parser.prog == "presentation-plugin"

    def test_parser_has_version(self):
        """Test that parser has version argument."""
        parser = create_parser()

        # Should not raise error
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_has_debug_flag(self):
        """Test that parser has debug flag."""
        parser = create_parser()

        # Parse with debug flag
        args = parser.parse_args(["--debug", "list-skills"])
        assert args.debug is True

        # Parse without debug flag
        args = parser.parse_args(["list-skills"])
        assert args.debug is False

    def test_parser_has_subcommands(self):
        """Test that parser has expected subcommands."""
        parser = create_parser()

        # Parser should have subcommands registered
        # Test by checking that list-skills command works
        args = parser.parse_args(["list-skills"])
        assert args.command == "list-skills"

    def test_full_workflow_command_registered(self):
        """Test that full-workflow command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["full-workflow", "test topic"])
        assert args.command == "full-workflow"
        assert args.topic == "test topic"

    def test_research_command_registered(self):
        """Test that research command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["research", "test topic"])
        assert args.command == "research"
        assert args.topic == "test topic"

    def test_outline_command_registered(self):
        """Test that outline command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["outline", "research.json"])
        assert args.command == "outline"

    def test_draft_command_registered(self):
        """Test that draft-content command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["draft-content", "outline.md"])
        assert args.command == "draft-content"

    def test_generate_images_command_registered(self):
        """Test that generate-images command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["generate-images", "presentation.md"])
        assert args.command == "generate-images"

    def test_build_command_registered(self):
        """Test that build-presentation command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["build-presentation", "presentation.md"])
        assert args.command == "build-presentation"

    def test_list_skills_command_registered(self):
        """Test that list-skills command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["list-skills"])
        assert args.command == "list-skills"

    def test_validate_command_registered(self):
        """Test that validate command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["validate"])
        assert args.command == "validate"

    def test_status_command_registered(self):
        """Test that status command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["status"])
        assert args.command == "status"

    def test_resume_command_registered(self):
        """Test that resume command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["resume", "workflow-id"])
        assert args.command == "resume"

    def test_config_command_registered(self):
        """Test that config command is registered."""
        parser = create_parser()

        # Should not raise error
        args = parser.parse_args(["config", "show"])
        assert args.command == "config"

    def test_full_workflow_with_template_arg(self):
        """Test full-workflow command with template argument."""
        parser = create_parser()

        args = parser.parse_args(["full-workflow", "test topic", "--template", "cfa"])
        assert args.template == "cfa"

    def test_full_workflow_with_no_checkpoints(self):
        """Test full-workflow command with no-checkpoints flag."""
        parser = create_parser()

        args = parser.parse_args(["full-workflow", "test topic", "--no-checkpoints"])
        assert args.no_checkpoints is True

    def test_research_with_output_arg(self):
        """Test research command with output argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["research", "test topic", "--output", "research.json"]
        )
        assert args.output == "research.json"

    def test_outline_with_output_arg(self):
        """Test outline command with output argument."""
        parser = create_parser()

        args = parser.parse_args(["outline", "research.json", "--output", "outline.md"])
        assert args.output == "outline.md"

    def test_build_with_template_arg(self):
        """Test build command with template argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["build-presentation", "presentation.md", "--template", "stratfield"]
        )
        assert args.template == "stratfield"

    def test_build_with_output_arg(self):
        """Test build command with output argument."""
        parser = create_parser()

        args = parser.parse_args(
            ["build-presentation", "presentation.md", "--output", "output.pptx"]
        )
        assert args.output == "output.pptx"

    def test_list_skills_with_verbose_flag(self):
        """Test list-skills command with verbose flag."""
        parser = create_parser()

        args = parser.parse_args(["list-skills", "--verbose"])
        assert args.verbose is True

    def test_config_show_subcommand(self):
        """Test config show subcommand."""
        parser = create_parser()

        args = parser.parse_args(["config", "show"])
        assert args.config_action == "show"

    def test_config_set_subcommand(self):
        """Test config set subcommand."""
        parser = create_parser()

        args = parser.parse_args(["config", "set", "research.max_sources", "50"])
        assert args.config_action == "set"
        assert args.key == "research.max_sources"
        assert args.value == "50"

    def test_config_get_subcommand(self):
        """Test config get subcommand."""
        parser = create_parser()

        args = parser.parse_args(["config", "get", "research.max_sources"])
        assert args.config_action == "get"
        assert args.key == "research.max_sources"

    def test_parser_no_command_has_no_func(self):
        """Test that parser with no command has no func attribute."""
        parser = create_parser()

        args = parser.parse_args([])
        assert not hasattr(args, "func")

    def test_parser_with_invalid_command_fails(self):
        """Test that invalid command raises error."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args(["invalid-command"])


class TestCLICommands:
    """Tests for CLI command functions (mocked)."""

    def test_list_skills_command_exists(self):
        """Test that list-skills command function exists."""
        from plugin import cli

        # Command functions should exist
        assert hasattr(cli, "cmd_list_skills")

    def test_validate_command_exists(self):
        """Test that validate command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_validate")

    def test_status_command_exists(self):
        """Test that status command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_status")

    def test_resume_command_exists(self):
        """Test that resume command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_resume")

    def test_config_show_command_exists(self):
        """Test that config show command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_config_show")

    def test_config_get_command_exists(self):
        """Test that config get command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_config_get")

    def test_config_set_command_exists(self):
        """Test that config set command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_config_set")

    def test_full_workflow_command_exists(self):
        """Test that full-workflow command function exists."""
        from plugin import cli

        assert hasattr(cli, "cmd_full_workflow")
