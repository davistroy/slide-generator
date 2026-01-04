"""
Command-line interface for the presentation generation plugin.

Provides unified CLI entry point for all plugin operations:
- Full workflow execution
- Individual skill execution
- Workflow resumption and state management
- Configuration management
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any

from .config_manager import ConfigManager
from .skill_registry import SkillRegistry
from .workflow_orchestrator import WorkflowOrchestrator, WorkflowPhase
from .checkpoint_handler import CheckpointHandler


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Execute command
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {str(e)}", file=sys.stderr)
            if args.debug:
                raise
            sys.exit(1)
    else:
        parser.print_help()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all commands."""
    parser = argparse.ArgumentParser(
        prog="presentation-plugin",
        description="AI-assisted presentation generation plugin"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )

    # Subcommands
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Full workflow command
    add_full_workflow_command(subparsers)

    # Individual skill commands
    add_research_command(subparsers)
    add_outline_command(subparsers)
    add_draft_command(subparsers)
    add_generate_images_command(subparsers)
    add_build_command(subparsers)

    # Utility commands
    add_list_skills_command(subparsers)
    add_validate_command(subparsers)
    add_status_command(subparsers)
    add_resume_command(subparsers)

    # Config commands
    add_config_command(subparsers)

    return parser


def add_full_workflow_command(subparsers):
    """Add full-workflow command."""
    parser = subparsers.add_parser(
        "full-workflow",
        help="Execute complete end-to-end workflow"
    )

    parser.add_argument(
        "topic",
        help="Presentation topic"
    )

    parser.add_argument(
        "--template",
        default="cfa",
        choices=["cfa", "stratfield"],
        help="Presentation template"
    )

    parser.add_argument(
        "--config",
        help="Path to config file"
    )

    parser.add_argument(
        "--no-checkpoints",
        action="store_true",
        help="Disable checkpoints"
    )

    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory"
    )

    parser.set_defaults(func=cmd_full_workflow)


def add_research_command(subparsers):
    """Add research command."""
    parser = subparsers.add_parser(
        "research",
        help="Conduct web research on a topic"
    )

    parser.add_argument(
        "topic",
        help="Research topic"
    )

    parser.add_argument(
        "--output",
        default="research.json",
        help="Output file for research results"
    )

    parser.add_argument(
        "--max-sources",
        type=int,
        default=20,
        help="Maximum number of sources"
    )

    parser.set_defaults(func=cmd_research)


def add_outline_command(subparsers):
    """Add outline command."""
    parser = subparsers.add_parser(
        "outline",
        help="Generate presentation outline from research"
    )

    parser.add_argument(
        "research_file",
        help="Research JSON file"
    )

    parser.add_argument(
        "--output",
        default="outline.md",
        help="Output file for outline"
    )

    parser.set_defaults(func=cmd_outline)


def add_draft_command(subparsers):
    """Add draft-content command."""
    parser = subparsers.add_parser(
        "draft-content",
        help="Draft slide content from outline"
    )

    parser.add_argument(
        "outline_file",
        help="Outline markdown file"
    )

    parser.add_argument(
        "--output",
        default="presentation.md",
        help="Output file for presentation"
    )

    parser.set_defaults(func=cmd_draft_content)


def add_generate_images_command(subparsers):
    """Add generate-images command."""
    parser = subparsers.add_parser(
        "generate-images",
        help="Generate images for presentation"
    )

    parser.add_argument(
        "presentation_file",
        help="Presentation markdown file"
    )

    parser.add_argument(
        "--resolution",
        default="high",
        choices=["small", "medium", "high"],
        help="Image resolution"
    )

    parser.add_argument(
        "--output-dir",
        default="./images",
        help="Output directory for images"
    )

    parser.set_defaults(func=cmd_generate_images)


def add_build_command(subparsers):
    """Add build-presentation command."""
    parser = subparsers.add_parser(
        "build-presentation",
        help="Build PowerPoint presentation"
    )

    parser.add_argument(
        "presentation_file",
        help="Presentation markdown file"
    )

    parser.add_argument(
        "--template",
        default="cfa",
        choices=["cfa", "stratfield"],
        help="Presentation template"
    )

    parser.add_argument(
        "--output",
        default="presentation.pptx",
        help="Output PowerPoint file"
    )

    parser.set_defaults(func=cmd_build_presentation)


def add_list_skills_command(subparsers):
    """Add list-skills command."""
    parser = subparsers.add_parser(
        "list-skills",
        help="List all registered skills"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed information"
    )

    parser.set_defaults(func=cmd_list_skills)


def add_validate_command(subparsers):
    """Add validate command."""
    parser = subparsers.add_parser(
        "validate",
        help="Validate plugin installation"
    )

    parser.set_defaults(func=cmd_validate)


def add_status_command(subparsers):
    """Add status command."""
    parser = subparsers.add_parser(
        "status",
        help="Show current workflow status"
    )

    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory"
    )

    parser.set_defaults(func=cmd_status)


def add_resume_command(subparsers):
    """Add resume command."""
    parser = subparsers.add_parser(
        "resume",
        help="Auto-detect and resume workflow"
    )

    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Project directory"
    )

    parser.set_defaults(func=cmd_resume)


def add_config_command(subparsers):
    """Add config command."""
    parser = subparsers.add_parser(
        "config",
        help="Manage configuration"
    )

    config_subparsers = parser.add_subparsers(dest="config_action")

    # config show
    show_parser = config_subparsers.add_parser("show", help="Show current config")
    show_parser.set_defaults(func=cmd_config_show)

    # config get
    get_parser = config_subparsers.add_parser("get", help="Get config value")
    get_parser.add_argument("key", help="Config key (dot notation)")
    get_parser.set_defaults(func=cmd_config_get)

    # config set
    set_parser = config_subparsers.add_parser("set", help="Set config value")
    set_parser.add_argument("key", help="Config key (dot notation)")
    set_parser.add_argument("value", help="Config value")
    set_parser.set_defaults(func=cmd_config_set)


# Command implementations

def cmd_full_workflow(args):
    """Execute full workflow."""
    print(f"🚀 Starting full workflow for topic: {args.topic}\n")

    # Load config
    config_mgr = ConfigManager()
    config = config_mgr.load_config(
        project_dir=args.output,
        cli_config={"templates": {"default_template": args.template}}
    )

    # Create checkpoint handler
    checkpoint_handler = CheckpointHandler(
        interactive=not args.no_checkpoints
    )

    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        checkpoint_handler=checkpoint_handler,
        config=config
    )

    # Execute workflow
    result = orchestrator.execute_workflow(
        workflow_id=f"workflow-{args.topic.replace(' ', '-').lower()}",
        initial_input=args.topic,
        config=config
    )

    # Report results
    if result.success:
        print(f"\n✅ Workflow completed successfully!")
        print(f"📁 Artifacts: {', '.join(result.final_artifacts)}")
        print(f"⏱️  Duration: {result.total_duration:.1f} seconds")
    else:
        print(f"\n❌ Workflow failed")
        if result.metadata.get("failed_phase"):
            print(f"Failed at phase: {result.metadata['failed_phase']}")


def cmd_research(args):
    """Execute research skill."""
    print(f"🔍 Researching topic: {args.topic}\n")
    print("Note: Research skill not yet implemented.")
    print("See PLUGIN_IMPLEMENTATION_PLAN.md for implementation details.")


def cmd_outline(args):
    """Execute outline skill."""
    print(f"📝 Generating outline from: {args.research_file}\n")
    print("Note: Outline skill not yet implemented.")
    print("See PLUGIN_IMPLEMENTATION_PLAN.md for implementation details.")


def cmd_draft_content(args):
    """Execute draft-content skill."""
    print(f"✍️  Drafting content from: {args.outline_file}\n")
    print("Note: Draft-content skill not yet implemented.")
    print("See PLUGIN_IMPLEMENTATION_PLAN.md for implementation details.")


def cmd_generate_images(args):
    """Execute generate-images skill."""
    print(f"🎨 Generating images from: {args.presentation_file}\n")
    print("Note: This will use existing generate_images.py script.")
    print("Integration with plugin system is in progress.")


def cmd_build_presentation(args):
    """Execute build-presentation skill."""
    print(f"🏗️  Building presentation from: {args.presentation_file}\n")
    print("Note: This will use existing presentation-skill.")
    print("Integration with plugin system is in progress.")


def cmd_list_skills(args):
    """List all registered skills."""
    print("📋 Registered Skills:\n")

    # Load manifest to show available skills
    manifest_path = Path(__file__).parent / "plugin_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    for skill in manifest["skills"]:
        status_icon = {
            "implemented": "✅",
            "experimental": "🧪",
            "planned": "📋"
        }.get(skill["status"], "❓")

        print(f"{status_icon} {skill['id']}")
        if args.verbose:
            print(f"   Name: {skill['name']}")
            print(f"   Description: {skill['description']}")
            print(f"   Status: {skill['status']}")
            print()


def cmd_validate(args):
    """Validate plugin installation."""
    print("✅ Validating plugin installation...\n")

    # Check Python version
    import sys
    print(f"Python version: {sys.version}")

    # Check dependencies
    print("\nChecking dependencies:")
    dependencies = [
        "google.genai",
        "pptx",
        "dotenv",
        "PIL",
        "frontmatter"
    ]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} (not installed)")

    # Check manifest
    manifest_path = Path(__file__).parent / "plugin_manifest.json"
    if manifest_path.exists():
        print(f"\n✅ Plugin manifest found")
    else:
        print(f"\n❌ Plugin manifest not found")

    print("\n✅ Validation complete")


def cmd_status(args):
    """Show workflow status."""
    print(f"📊 Workflow Status for: {args.project_dir}\n")
    print("Note: Status detection not yet implemented.")
    print("See PLUGIN_IMPLEMENTATION_PLAN.md for StateDetector design.")


def cmd_resume(args):
    """Resume workflow."""
    print(f"▶️  Resuming workflow in: {args.project_dir}\n")
    print("Note: Resume functionality not yet implemented.")
    print("See PLUGIN_IMPLEMENTATION_PLAN.md for resumption design.")


def cmd_config_show(args):
    """Show current configuration."""
    config_mgr = ConfigManager()
    config = config_mgr.load_config()

    print("⚙️  Current Configuration:\n")
    print(json.dumps(config, indent=2))


def cmd_config_get(args):
    """Get configuration value."""
    config_mgr = ConfigManager()
    config_mgr.load_config()

    value = config_mgr.get(args.key)
    if value is not None:
        print(value)
    else:
        print(f"Key '{args.key}' not found", file=sys.stderr)
        sys.exit(1)


def cmd_config_set(args):
    """Set configuration value."""
    config_mgr = ConfigManager()
    config_mgr.load_config()

    # Try to parse value as JSON
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value

    config_mgr.set(args.key, value)
    config_mgr.save_user_config()

    print(f"✅ Set {args.key} = {value}")


if __name__ == "__main__":
    main()
