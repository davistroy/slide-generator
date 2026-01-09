"""
Command-line interface for the presentation generation plugin.

Provides unified CLI entry point for all plugin operations:
- Full workflow execution
- Individual skill execution
- Workflow resumption and state management
- Configuration management
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .checkpoint_handler import CheckpointHandler
from .config_manager import ConfigManager
from .workflow_orchestrator import WorkflowOrchestrator


logger = logging.getLogger(__name__)


def _print_error(message: str) -> None:
    """Print standardized error message to stderr."""
    print(f"[ERROR] {message}", file=sys.stderr)


def _print_success(message: str) -> None:
    """Print standardized success message."""
    print(f"[OK] {message}")


def _print_info(message: str) -> None:
    """Print standardized info message."""
    print(f"[INFO] {message}")


# Input validation constants
MAX_TOPIC_LENGTH = 500  # Maximum topic length in characters
MAX_FILE_PATH_LENGTH = 260  # Windows MAX_PATH


def _sanitize_topic(topic: str) -> str:
    """
    Sanitize user-provided topic string.

    Args:
        topic: Raw topic string from user

    Returns:
        Sanitized topic string

    Raises:
        ValueError: If topic is invalid
    """
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty")

    # Strip whitespace
    topic = topic.strip()

    # Check length
    if len(topic) > MAX_TOPIC_LENGTH:
        raise ValueError(f"Topic too long (max {MAX_TOPIC_LENGTH} characters)")

    # Remove control characters (except newlines and tabs)
    sanitized = "".join(
        char for char in topic
        if char.isprintable() or char in "\n\t"
    )

    # Collapse excessive whitespace
    import re
    sanitized = re.sub(r"\s+", " ", sanitized).strip()

    if not sanitized:
        raise ValueError("Topic contains no valid content after sanitization")

    return sanitized


def _validate_file_path(path: str, must_exist: bool = False) -> Path:
    """
    Validate and resolve a file path.

    Args:
        path: File path string
        must_exist: Whether file must exist

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid
    """
    if not path or not path.strip():
        raise ValueError("File path cannot be empty")

    if len(path) > MAX_FILE_PATH_LENGTH:
        raise ValueError(f"File path too long (max {MAX_FILE_PATH_LENGTH} characters)")

    # Resolve path
    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid file path: {e}") from e

    if must_exist and not resolved.exists():
        raise ValueError(f"File not found: {resolved}")

    return resolved


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Execute command
    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            _print_error(str(e))
            logger.exception("Command failed with exception")
            if args.debug:
                raise
            sys.exit(1)
    else:
        parser.print_help()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser with all commands."""
    parser = argparse.ArgumentParser(
        prog="presentation-plugin",
        description="AI-assisted presentation generation plugin",
    )

    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Subcommands
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Full workflow command
    add_full_workflow_command(subparsers)

    # Individual skill commands
    add_research_command(subparsers)
    add_outline_command(subparsers)
    add_draft_command(subparsers)
    add_generate_images_command(subparsers)
    add_parse_markdown_command(subparsers)
    add_build_command(subparsers)

    # Utility commands
    add_list_skills_command(subparsers)
    add_validate_command(subparsers)
    add_status_command(subparsers)
    add_resume_command(subparsers)

    # Config commands
    add_config_command(subparsers)

    # Health check command
    add_health_check_command(subparsers)

    return parser


def add_full_workflow_command(subparsers):
    """Add full-workflow command."""
    parser = subparsers.add_parser(
        "full-workflow", help="Execute complete end-to-end workflow"
    )

    parser.add_argument("topic", help="Presentation topic")

    parser.add_argument(
        "--template",
        default="cfa",
        choices=["cfa", "stratfield"],
        help="Presentation template",
    )

    parser.add_argument("--config", help="Path to config file")

    parser.add_argument(
        "--no-checkpoints", action="store_true", help="Disable checkpoints"
    )

    parser.add_argument("--output", default="./output", help="Output directory")

    parser.set_defaults(func=cmd_full_workflow)


def add_research_command(subparsers):
    """Add research command."""
    parser = subparsers.add_parser("research", help="Conduct web research on a topic")

    parser.add_argument("topic", help="Research topic")

    parser.add_argument(
        "--output", default="research.json", help="Output file for research results"
    )

    parser.add_argument(
        "--max-sources", type=int, default=20, help="Maximum number of sources"
    )

    parser.set_defaults(func=cmd_research)


def add_outline_command(subparsers):
    """Add outline command."""
    parser = subparsers.add_parser(
        "outline", help="Generate presentation outline from research"
    )

    parser.add_argument("research_file", help="Research JSON file")

    parser.add_argument(
        "--output", default="outline.md", help="Output file for outline"
    )

    parser.set_defaults(func=cmd_outline)


def add_draft_command(subparsers):
    """Add draft-content command."""
    parser = subparsers.add_parser(
        "draft-content", help="Draft slide content from outline"
    )

    parser.add_argument("outline_file", help="Outline markdown file")

    parser.add_argument(
        "--output", default="presentation.md", help="Output file for presentation"
    )

    parser.set_defaults(func=cmd_draft_content)


def add_generate_images_command(subparsers):
    """Add generate-images command."""
    parser = subparsers.add_parser(
        "generate-images", help="Generate images for presentation"
    )

    parser.add_argument("presentation_file", help="Presentation markdown file")

    parser.add_argument(
        "--resolution",
        default="high",
        choices=["small", "medium", "high"],
        help="Image resolution",
    )

    parser.add_argument(
        "--output-dir", default=None, help="Output directory for images (default: <presentation_dir>/images)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing images",
    )

    parser.set_defaults(func=cmd_generate_images)


def add_parse_markdown_command(subparsers):
    """Add parse-markdown command."""
    parser = subparsers.add_parser(
        "parse-markdown", help="Parse presentation markdown into structured data"
    )

    parser.add_argument("markdown_file", help="Presentation markdown file")

    parser.add_argument("--output", "-o", help="Output JSON file path")

    parser.set_defaults(func=cmd_parse_markdown)


def add_build_command(subparsers):
    """Add build-presentation command."""
    parser = subparsers.add_parser(
        "build-presentation", help="Build PowerPoint presentation"
    )

    parser.add_argument("presentation_file", help="Presentation markdown file")

    parser.add_argument(
        "--template",
        "-t",
        default="cfa",
        choices=["cfa", "stratfield"],
        help="Presentation template",
    )

    parser.add_argument("--output", "-o", help="Output PowerPoint filename")

    parser.add_argument("--output-dir", help="Output directory")

    parser.add_argument(
        "--skip-images", action="store_true", help="Skip image generation"
    )

    parser.add_argument(
        "--fast", action="store_true", help="Use standard resolution (faster)"
    )

    parser.add_argument(
        "--enable-validation",
        action="store_true",
        help="Enable visual validation (experimental, Windows only)",
    )

    parser.set_defaults(func=cmd_build_presentation)


def add_list_skills_command(subparsers):
    """Add list-skills command."""
    parser = subparsers.add_parser("list-skills", help="List all registered skills")

    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed information"
    )

    parser.set_defaults(func=cmd_list_skills)


def add_validate_command(subparsers):
    """Add validate command."""
    parser = subparsers.add_parser("validate", help="Validate plugin installation")

    parser.set_defaults(func=cmd_validate)


def add_status_command(subparsers):
    """Add status command."""
    parser = subparsers.add_parser("status", help="Show current workflow status")

    parser.add_argument("project_dir", nargs="?", default=".", help="Project directory")

    parser.set_defaults(func=cmd_status)


def add_resume_command(subparsers):
    """Add resume command."""
    parser = subparsers.add_parser("resume", help="Auto-detect and resume workflow")

    parser.add_argument("project_dir", nargs="?", default=".", help="Project directory")

    parser.set_defaults(func=cmd_resume)


def add_health_check_command(subparsers):
    """Add health-check command."""
    parser = subparsers.add_parser(
        "health-check", help="Check plugin health and configuration"
    )

    parser.add_argument(
        "--json", dest="output_json", action="store_true", help="Output as JSON"
    )

    parser.set_defaults(func=cmd_health_check)


def add_config_command(subparsers):
    """Add config command."""
    parser = subparsers.add_parser("config", help="Manage configuration")

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
    # Sanitize input
    topic = _sanitize_topic(args.topic)

    print(f"Starting full workflow for topic: {topic}\n")

    # Load config
    config_mgr = ConfigManager()
    config = config_mgr.load_config(
        project_dir=args.output,
        cli_config={"templates": {"default_template": args.template}},
    )

    # Create checkpoint handler
    checkpoint_handler = CheckpointHandler(interactive=not args.no_checkpoints)

    # Create orchestrator
    orchestrator = WorkflowOrchestrator(
        checkpoint_handler=checkpoint_handler, config=config
    )

    # Execute workflow
    result = orchestrator.execute_workflow(
        workflow_id=f"workflow-{topic.replace(' ', '-').lower()}",
        initial_input=topic,
        config=config,
    )

    # Report results
    if result.success:
        _print_success("Workflow completed successfully!")
        print(f"Artifacts: {', '.join(result.final_artifacts)}")
        print(f"Duration: {result.total_duration:.1f} seconds")
    else:
        _print_error("Workflow failed")
        if result.metadata.get("failed_phase"):
            print(f"Failed at phase: {result.metadata['failed_phase']}")
        sys.exit(1)


def cmd_research(args):
    """Execute research skill."""
    import json

    from .base_skill import SkillInput
    from .skills.research.research_skill import ResearchSkill

    # Sanitize input
    topic = _sanitize_topic(args.topic)

    print(f"[RESEARCH] Researching topic: {topic}\n")

    skill = ResearchSkill()

    input_data = SkillInput(
        data={"topic": topic, "max_sources": args.max_sources},
        context={},
        config={},
    )

    result = skill.execute(input_data)

    if result.success:
        # Save research results to file
        with open(args.output, "w") as f:
            json.dump(result.data, f, indent=2)

        _print_success("Research completed successfully")
        print(f"Output saved to: {args.output}")
        print(f"Sources found: {result.data.get('sources_count', 0)}")
        print(f"Key themes: {len(result.data.get('key_themes', []))}")
    else:
        _print_error("Research failed")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_outline(args):
    """Execute outline skill."""
    import json

    from .base_skill import SkillInput
    from .skills.content.outline_skill import OutlineSkill

    # Validate input file
    research_path = _validate_file_path(args.research_file, must_exist=True)

    print(f"[OUTLINE] Generating outline from: {research_path}\n")

    # Load research results
    with open(research_path) as f:
        research = json.load(f)

    skill = OutlineSkill()

    input_data = SkillInput(data={"research": research}, context={}, config={})

    result = skill.execute(input_data)

    if result.success:
        # Save outline to file (as JSON)
        with open(args.output.replace(".md", ".json"), "w") as f:
            json.dump(result.data, f, indent=2)

        _print_success("Outline generated successfully")
        print(f"Output saved to: {args.output.replace('.md', '.json')}")
        print(f"Presentations: {result.data.get('presentation_count', 0)}")
        if result.data.get("presentations"):
            for pres in result.data["presentations"]:
                print(f"  - {pres['title']}: {len(pres['slides'])} slides")
    else:
        _print_error("Outline generation failed")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_draft_content(args):
    """Execute draft-content skill."""
    import json

    from .base_skill import SkillInput
    from .skills.content.content_drafting_skill import ContentDraftingSkill

    # Validate input file
    outline_path = _validate_file_path(args.outline_file, must_exist=True)

    print(f"[DRAFT] Drafting content from: {outline_path}\n")

    # Load outline
    with open(outline_path) as f:
        outline = json.load(f)

    skill = ContentDraftingSkill()

    input_data = SkillInput(
        data={
            "outline": outline,
            "output_dir": Path(args.output).parent if args.output else Path(),
        },
        context={},
        config={},
    )

    result = skill.execute(input_data)

    if result.success:
        _print_success("Content drafted successfully")
        print(f"Slides generated: {result.data.get('slides_generated', 0)}")
    else:
        _print_error("Content drafting failed")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_generate_images(args):
    """Execute generate-images skill - generate images for slides."""
    from plugin.lib.presentation.image_generator import (
        generate_all_images,
        load_style_config,
    )
    from plugin.lib.presentation.parser import parse_presentation

    # Validate input file
    presentation_path = _validate_file_path(args.presentation_file, must_exist=True)

    print(f"[IMAGES] Generating images for: {presentation_path}\n")

    # Parse presentation
    try:
        slides = parse_presentation(str(presentation_path))
    except (OSError, ValueError) as e:
        _print_error(f"Failed to parse presentation: {e}")
        sys.exit(1)

    # Filter slides that need images (have graphics descriptions)
    slides_with_graphics = [s for s in slides if s.graphic]

    if not slides_with_graphics:
        _print_info("No slides with graphics descriptions found.")
        print("Add graphics descriptions to your presentation.md slides.")
        sys.exit(0)

    print(f"Found {len(slides_with_graphics)} slides requiring images")
    print(f"Resolution: {args.resolution}")
    print()

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else presentation_path.parent / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load style config
    style_config = load_style_config()

    # Set resolution parameters
    fast_mode = args.resolution != "high"

    # Generate images
    print(f"Generating images to: {output_dir}\n")

    try:
        results = generate_all_images(
            slides=slides_with_graphics,
            style_config=style_config,
            output_dir=str(output_dir),
            fast_mode=fast_mode,
            notext=True,
            force=args.force,
        )

        success_count = len(results)
        _print_success(f"Generated {success_count}/{len(slides_with_graphics)} images")
        print(f"Output directory: {output_dir}")

    except (OSError, ValueError, RuntimeError) as e:
        _print_error(f"Image generation failed: {e}")
        logger.exception("Image generation failed")
        sys.exit(1)

    sys.exit(0)


def cmd_parse_markdown(args):
    """Execute parse-markdown skill."""
    import json

    from .base_skill import SkillInput
    from .skills.assembly.markdown_parsing_skill import MarkdownParsingSkill

    # Validate input file
    markdown_path = _validate_file_path(args.markdown_file, must_exist=True)

    print(f"[PARSE] Parsing markdown: {markdown_path}\n")

    skill = MarkdownParsingSkill()

    input_data = SkillInput(
        data={"markdown_path": str(markdown_path)}, context={}, config={}
    )

    result = skill.execute(input_data)

    if result.success:
        _print_success("Parsed successfully!")
        print(f"Slides: {result.data['slide_count']}")
        print(f"Has graphics: {result.data['has_graphics']}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result.data, f, indent=2)
            print(f"Output saved to: {args.output}")
        else:
            # Print summary of each slide
            print("\nSlide Summary:")
            for slide in result.data["slides"]:
                slide_type = slide.get("slide_type", "unknown")
                title = slide.get("title", "Untitled")
                number = slide.get("number", "?")
                print(f"  Slide {number}: {title} ({slide_type})")
    else:
        _print_error("Failed to parse markdown")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_build_presentation(args):
    """Execute build-presentation skill."""
    from .base_skill import SkillInput
    from .skills.assembly.powerpoint_assembly_skill import PowerPointAssemblySkill

    # Validate input file
    presentation_path = _validate_file_path(args.presentation_file, must_exist=True)

    print(f"[BUILD] Building presentation from: {presentation_path}\n")

    skill = PowerPointAssemblySkill()

    # Build input data
    input_data = {
        "markdown_path": str(presentation_path),
        "template": args.template,
        "skip_images": args.skip_images,
        "fast_mode": args.fast,
        "enable_validation": args.enable_validation,
    }

    if args.output:
        input_data["output_name"] = args.output
    if args.output_dir:
        input_data["output_dir"] = args.output_dir

    # Create skill input
    skill_input = SkillInput(data=input_data, context={}, config={})

    # Execute skill
    result = skill.execute(skill_input)

    if result.success:
        _print_success("Presentation generated successfully!")
        print(f"Output: {result.data['output_path']}")
        if result.data.get("slide_count"):
            print(f"Slides: {result.data['slide_count']}")
        if result.data.get("images_generated"):
            print(f"Images: {result.data['images_generated']}")
    else:
        _print_error("Failed to generate presentation")
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)


def cmd_list_skills(args):
    """List all registered skills."""
    print("📋 Registered Skills:\n")

    # Load manifest to show available skills
    manifest_path = Path(__file__).parent / "plugin_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    for skill in manifest["skills"]:
        status_icon = {"implemented": "✅", "experimental": "🧪", "planned": "📋"}.get(
            skill["status"], "❓"
        )

        print(f"{status_icon} {skill['id']}")
        if args.verbose:
            print(f"   Name: {skill['name']}")
            print(f"   Description: {skill['description']}")
            print(f"   Status: {skill['status']}")
            print()


def cmd_health_check(args):
    """Run comprehensive health check."""
    from .lib.health_check import run_health_check

    is_healthy = run_health_check(output_json=args.output_json)
    sys.exit(0 if is_healthy else 1)


def cmd_validate(args):
    """Validate plugin installation."""
    print("✅ Validating plugin installation...\n")

    # Check Python version
    import sys

    print(f"Python version: {sys.version}")

    # Check dependencies
    print("\nChecking dependencies:")
    dependencies = ["google.genai", "pptx", "dotenv", "PIL", "frontmatter"]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep} (not installed)")

    # Check manifest
    manifest_path = Path(__file__).parent / "plugin_manifest.json"
    if manifest_path.exists():
        print("\n✅ Plugin manifest found")
    else:
        print("\n❌ Plugin manifest not found")

    print("\n✅ Validation complete")


def cmd_status(args):
    """Show workflow status."""
    from pathlib import Path

    from plugin.lib.state_detector import StateDetector

    project_dir = Path(args.project_dir).resolve()
    print(f"[STATUS] Workflow Status for: {project_dir}\n")

    detector = StateDetector(project_dir)
    state = detector.detect_state()

    # Display detected artifacts
    print("Detected Artifacts:")
    for name, info in state.available_artifacts.items():
        if info.exists:
            status = "[OK]" if info.is_valid else "[INVALID]"
            mtime = info.modified_time.strftime("%Y-%m-%d %H:%M") if info.modified_time else "unknown"
            details = ""
            if info.metadata:
                if "source_count" in info.metadata:
                    details = f", {info.metadata['source_count']} sources"
                elif "slide_count" in info.metadata:
                    details = f", {info.metadata['slide_count']} slides"
                elif "image_count" in info.metadata:
                    count = info.metadata["image_count"]
                    expected = info.metadata.get("expected_count", "?")
                    details = f", {count}/{expected} images"
            print(f"  {status} {name:15} (modified: {mtime}{details})")
        else:
            print(f"  [--] {name:15} (not found)")

    print()
    if state.last_completed_phase:
        print(f"Workflow Position: Step {state.current_step} of 11")
        print(f"Last Completed Phase: {state.last_completed_phase.value}")
    else:
        print("Workflow Position: Not started")

    print()
    print("Next Steps:")
    print(f"  {state.next_recommended_step}")

    print()
    print(f"Can Resume: {'Yes' if state.can_resume else 'No'}")
    sys.exit(0)


def cmd_resume(args):
    """Resume workflow from detected state."""
    from pathlib import Path

    from plugin.lib.state_detector import StateDetector

    project_dir = Path(args.project_dir).resolve()
    print(f"[RESUME] Analyzing workflow state in: {project_dir}\n")

    detector = StateDetector(project_dir)
    state = detector.detect_state()

    if not state.can_resume:
        print("No workflow artifacts found.")
        print("Start a new workflow with: sg full-workflow 'Your Topic' --template cfa")
        sys.exit(0)

    print("Detected State:")
    print(f"  Last completed: {state.last_completed_phase.value if state.last_completed_phase else 'None'}")
    print(f"  Current step: {state.current_step} of 11")
    print()

    # Determine what to resume
    if state.current_step >= 11:
        print("[OK] Workflow already complete!")
        pptx_info = state.available_artifacts.get("pptx")
        if pptx_info and pptx_info.exists:
            print(f"Output: {pptx_info.path}")
        sys.exit(0)

    # Show resume plan
    print("Resume Plan:")
    if state.current_step <= 2:
        print("  1. Generate outline from research")
        print("  2. Draft content from outline")
        print("  3. Generate images")
        print("  4. Build PowerPoint")
    elif state.current_step <= 4:
        print("  1. Draft content from outline")
        print("  2. Generate images")
        print("  3. Build PowerPoint")
    elif state.current_step <= 6:
        print("  1. Generate images")
        print("  2. Build PowerPoint")
    else:
        print("  1. Build PowerPoint")

    print()

    # Provide the specific command
    print(f"Next Step: {state.next_recommended_step}")
    print()
    print("Run with --execute to automatically resume (coming soon)")
    sys.exit(0)


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
