# AI-Assisted Presentation Generation Plugin - Implementation Plan

**Status:** PRIORITY 1 COMPLETE ✅ | PRIORITY 2 IN PROGRESS 🚧

**Last Updated:** 2026-01-04

**Current Milestone:** Milestone 2 - Research & Discovery Tools

## Executive Summary

Build a comprehensive Claude Code plugin system for AI-assisted presentation generation, implementing all 11 workflow steps from research through final presentation assembly. Development proceeds in 4 major phases:

1. **Plugin Infrastructure** - Foundation for all tools ✅ **COMPLETE**
2. **Phase 1: Research & Discovery** - Web research, insight extraction, outline generation 🚧 **IN PROGRESS**
3. **Phase 2: Content Development** - AI-assisted drafting and optimization 📋 **PLANNED**
4. **Phases 3-4: Production Enhancements** - Robust validation and quality assurance 📋 **PLANNED**

**User Interaction Model:** Hybrid with checkpoints (automated within phases, user review between phases)

**Multi-Presentation:** Auto-detection and automatic splitting for different audiences

**Workflow Flexibility:** Start at ANY point in the 11-step workflow, run skills independently, or resume from existing artifacts

---

## Implementation Status

### ✅ COMPLETED: PRIORITY 1 - Plugin Infrastructure Foundation

**Completion Date:** 2026-01-04

**What Was Built:**
- Complete plugin directory structure (plugin/, commands/, skills/, lib/)
- Base skill interface (BaseSkill, SkillInput, SkillOutput)
- Skill registry with dependency resolution
- Workflow orchestrator with checkpoint system
- Checkpoint handler (interactive and batch modes)
- Configuration manager (multi-source with validation)
- CLI interface with 11 commands
- Plugin manifest and configuration schema
- Comprehensive test plan (PLUGIN_TEST_PLAN.md)
- Test infrastructure (pytest config, fixtures, conftest.py)
- Primary test data (Rochester 2GC carburetor rebuild prompt)
- Complete documentation (plugin/README.md)

**Files Created:** 30 files, 8,000+ lines of code

**Branch:** feature/plugin-infrastructure

**Pull Request:** #3

### 🚧 IN PROGRESS: PRIORITY 2 - Research & Discovery Tools

**Current Focus:** Implementing web research, citation management, and outline generation

**Next Steps:**
1. Implement unit tests for infrastructure
2. Implement web research skill
3. Implement citation manager
4. Implement insight extraction
5. Implement outline generation with multi-presentation detection

---

## Workflow Entry Points & Resumption

### Design Principle: Start Anywhere, Run Anything

The plugin architecture is designed for **maximum flexibility** - users can:
- Start the workflow at ANY of the 11 steps
- Resume workflow from existing artifacts (research.json, outline.md, presentation.md, etc.)
- Run individual skills standalone without full workflow
- Jump in after manual edits to any intermediate file
- Chain partial workflows (e.g., "outline → presentation" without research)

### Entry Point Architecture

Each skill is **completely self-contained** with:
- **Input validation** - Can validate if required inputs exist (files or data)
- **Output contracts** - Produces standardized output others can consume
- **State detection** - Can detect its own inputs from filesystem
- **Idempotency** - Can be re-run safely without duplicating work

### 11 Workflow Entry Points

| Entry Point | Starting Artifact | Skills Executed | Use Case |
|-------------|-------------------|-----------------|----------|
| **1. From topic** | User prompt | research → outline → draft → images → build | Full end-to-end (most common) |
| **2. From research** | `research.json` | outline → draft → images → build | Skip research, use existing sources |
| **3. From insights** | `insights.json` | outline → draft → images → build | Skip research & extraction |
| **4. From outline** | `outline.md` | draft → images → build | Manual outline, AI generates content |
| **5. From draft** | `presentation.md` | optimize → images → build | Manual draft, AI polishes |
| **6. From optimized content** | `presentation.md` | images → build | Content ready, generate visuals |
| **7. From prompts** | `prompts/*.md` | generate-images → build | Regenerate images only |
| **8. From images** | `images/*.jpg` | build | Rebuild presentation with existing images |
| **9. After manual edit** | Modified `presentation.md` | images → build | User edited content, regenerate rest |
| **10. Validation only** | Existing `.pptx` | validate → refine | Quality check existing presentation |
| **11. Individual skills** | Varies | Single skill | Run one step in isolation |

### Auto-Detection & Smart Resumption

**File:** `plugin/lib/state_detector.py`

Automatically detect workflow state from filesystem:

```python
class StateDetector:
    """Detect current workflow state from existing artifacts."""

    def detect_state(self, project_dir: str) -> WorkflowState:
        """
        Scan directory for artifacts and determine workflow position.

        Returns:
        - WorkflowState with:
          - current_step: int (1-11)
          - available_artifacts: Dict[str, str]
          - next_recommended_step: str
          - can_resume: bool
        """

        # Scan for artifacts in priority order:
        # 1. presentation.pptx → Workflow complete
        # 2. images/*.jpg → Ready for build
        # 3. prompts/*.md → Ready for image generation
        # 4. presentation.md → Ready for image generation
        # 5. outline.md → Ready for content drafting
        # 6. insights.json → Ready for outline
        # 7. research.json → Ready for insight extraction
        # 8. None → Start from beginning

    def validate_artifact(self, artifact_path: str, artifact_type: str) -> bool:
        """Validate artifact is well-formed and usable."""

    def suggest_entry_point(self, state: WorkflowState) -> str:
        """Recommend which skill to run next."""
```

**Detection Rules:**
- Check modification times (detect manual edits)
- Validate file formats (ensure artifacts are well-formed)
- Detect missing dependencies (e.g., images exist but presentation.md missing)
- Suggest repair actions (e.g., "presentation.md corrupted, regenerate from outline.md")

### CLI Commands for Each Entry Point

**File:** `plugin/cli.py` (enhanced)

```bash
# Full workflow from topic
python -m plugin.cli full-workflow "AI in Healthcare"

# Auto-detect and resume
python -m plugin.cli resume
# → Scans directory, detects presentation.md exists
# → Suggests: "Found presentation.md. Run 'generate-images' next? [Y/n]"

# Start from specific step
python -m plugin.cli from-research research.json
python -m plugin.cli from-outline outline.md
python -m plugin.cli from-draft presentation.md
python -m plugin.cli from-images images/

# Run individual skills standalone
python -m plugin.cli research "AI in Healthcare" --output research.json
python -m plugin.cli outline research.json --output outline.md
python -m plugin.cli draft outline.md --output presentation.md
python -m plugin.cli optimize presentation.md --output presentation-optimized.md
python -m plugin.cli generate-images presentation.md
python -m plugin.cli build presentation.md --template cfa --output final.pptx

# Validate existing presentation
python -m plugin.cli validate final.pptx

# Refine specific slides
python -m plugin.cli refine final.pptx --slides 3,5,7

# Check what can be done
python -m plugin.cli status
# → "Detected: presentation.md (modified 2 hours ago)"
# → "Next steps: generate-images, build"
# → "Can resume: Yes"
```

### Partial Workflow Chains

**File:** `plugin/workflow_orchestrator.py` (enhanced)

Support partial workflow execution:

```python
class WorkflowOrchestrator:
    """Enhanced with partial workflow support."""

    def execute_partial_workflow(
        self,
        start_step: str,
        end_step: str,
        initial_input: Union[str, Dict[str, Any]],
        config: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute workflow from start_step to end_step.

        Examples:
        - ("outline", "build") - Generate outline through final presentation
        - ("draft", "images") - Draft content and generate images only
        - ("images", "images") - Regenerate images only
        """

    def resume_workflow(
        self,
        project_dir: str,
        config: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Auto-detect state and resume workflow.

        1. Detect current state
        2. Validate existing artifacts
        3. Suggest next step
        4. Execute from there
        """
```

### Standalone Skill Usage

Each skill can be imported and used programmatically:

```python
# Example 1: Use research skill standalone
from plugin.skills.research_skill import ResearchSkill
from plugin.base_skill import SkillInput

research = ResearchSkill()
result = research.execute(SkillInput(
    data={"topic": "AI in Healthcare", "max_sources": 15},
    context={},
    config={"search_depth": "comprehensive"}
))

# Example 2: Use content drafting standalone
from plugin.skills.content_drafting_skill import ContentDraftingSkill

drafter = ContentDraftingSkill()
result = drafter.execute(SkillInput(
    data={
        "outline": "outline.md",
        "research": "research.json"
    },
    context={},
    config={"tone": "professional", "max_bullets_per_slide": 5}
))

# Example 3: Chain skills manually
research_result = ResearchSkill().execute(research_input)
insights_result = InsightExtractionSkill().execute(SkillInput(
    data={"research_output": research_result.data},
    context={},
    config={}
))
outline_result = OutlineSkill().execute(SkillInput(
    data={
        "research": research_result.data,
        "insights": insights_result.data
    },
    context={},
    config={}
))
```

### Modified Artifact Detection

**File:** `plugin/lib/change_detector.py`

Detect when user manually edits intermediate artifacts:

```python
class ChangeDetector:
    """Detect manual edits to workflow artifacts."""

    def detect_changes(
        self,
        artifact_path: str,
        last_generated_hash: str
    ) -> ChangeReport:
        """
        Compare artifact against last known state.

        Returns:
        - has_changed: bool
        - change_type: "manual_edit" | "regenerated" | "unchanged"
        - affected_downstream: List[str]  # Which artifacts need regeneration
        """

    def invalidate_downstream(
        self,
        changed_artifact: str,
        project_dir: str
    ) -> List[str]:
        """
        Determine which downstream artifacts are now stale.

        Example:
        - If presentation.md changed → images/*.jpg are stale
        - If outline.md changed → presentation.md, images/*.jpg stale
        """

    def suggest_regeneration(
        self,
        stale_artifacts: List[str]
    ) -> RegenerationPlan:
        """Suggest which skills to re-run."""
```

**Use Case:**
```bash
# User manually edits presentation.md
vim presentation.md  # Adds new slide, modifies graphics description

# Plugin detects changes
python -m plugin.cli status
# → "presentation.md modified (manual edit detected)"
# → "Stale artifacts: images/slide-*.jpg, final.pptx"
# → "Recommend: Run 'generate-images' to update visuals"

# Resume from there
python -m plugin.cli resume --auto
# → Regenerates images for changed slides only
# → Rebuilds presentation
```

### Incremental Regeneration

**Smart regeneration** - only update what changed:

```python
class IncrementalGenerator:
    """Regenerate only changed artifacts."""

    def detect_slide_changes(
        self,
        old_md: str,
        new_md: str
    ) -> List[int]:
        """Return slide numbers that changed."""

    def regenerate_slides(
        self,
        changed_slides: List[int],
        presentation_md: str
    ) -> List[str]:
        """Regenerate images only for changed slides."""

    def rebuild_presentation(
        self,
        changed_slides: List[int],
        existing_pptx: str
    ) -> str:
        """Update only changed slides in existing .pptx."""
```

**Example:**
```bash
# User edits slide 5 in presentation.md
python -m plugin.cli generate-images presentation.md --incremental
# → Detects only slide 5 changed
# → Regenerates slide-05.jpg only (saves time & cost)
# → Preserves slide-01.jpg through slide-04.jpg, slide-06.jpg onwards

python -m plugin.cli build presentation.md --incremental
# → Updates slide 5 in existing.pptx
# → Preserves all other slides
```

### Error Recovery & Rollback

**File:** `plugin/lib/recovery_manager.py`

Handle failures gracefully with rollback:

```python
class RecoveryManager:
    """Manage error recovery and rollback."""

    def checkpoint_state(self, project_dir: str) -> str:
        """Save current state before risky operation."""

    def rollback_to_checkpoint(self, checkpoint_id: str) -> None:
        """Restore previous state if operation fails."""

    def suggest_recovery(self, error: Exception, context: Dict) -> str:
        """Suggest how to recover from error."""
```

**Example:**
```bash
# Image generation fails on slide 7
python -m plugin.cli generate-images presentation.md
# → Slides 1-6 generated successfully
# → Slide 7 fails (API error)
# → "Error on slide 7. Generated images saved. Retry? [Y/n]"

python -m plugin.cli resume
# → Detects slides 1-6 complete
# → Resumes from slide 7 only
```

### Configuration: Entry Point Defaults

**File:** `plugin/config_schema.json` (enhanced)

```json
{
  "workflow": {
    "enable_auto_resume": true,
    "detect_manual_edits": true,
    "incremental_regeneration": true,
    "checkpoint_before_risky_ops": true,
    "auto_invalidate_stale_artifacts": true
  },
  "entry_points": {
    "research": {
      "default_output": "research.json"
    },
    "outline": {
      "default_input": "research.json",
      "default_output": "outline.md"
    },
    "draft": {
      "default_input": "outline.md",
      "default_output": "presentation.md"
    },
    "images": {
      "default_input": "presentation.md",
      "default_output": "images/"
    },
    "build": {
      "default_input": "presentation.md",
      "default_output": "presentation.pptx"
    }
  }
}
```

---

## Current State Analysis

### ✅ What Exists (75% of workflow)
- ✅ **Plugin Infrastructure** - Complete skill system, registry, lifecycle management (PRIORITY 1 ✅)
- ✅ **Checkpoint System** - Interactive user review with batch support (PRIORITY 1 ✅)
- ✅ **Configuration System** - Multi-source config with validation (PRIORITY 1 ✅)
- ✅ **CLI Interface** - Unified command-line with 11 entry points (PRIORITY 1 ✅)
- ✅ **Test Infrastructure** - Comprehensive test plan, fixtures, primary test data (PRIORITY 1 ✅)
- ✅ **Phase 3: Visual Asset Generation** - Fully implemented (image generation, experimental validation/refinement)
- ✅ **Phase 4: Presentation Assembly** - Fully implemented (classification, template system, PowerPoint generation)
- ✅ **Template System** - Modular brand templates (CFA, Stratfield)
- ✅ **Parsing** - Rich markdown parsing with multiple content types

### 🚧 What's In Progress (15% of workflow)
- 🚧 **Phase 1: Research & Discovery** - Starting implementation (PRIORITY 2 🚧)

### 📋 What's Planned (10% of workflow)
- 📋 **Phase 2: Content Development** - AI-assisted drafting, optimization (PRIORITY 3 📋)
- 📋 **Production Enhancements** - Production-ready validation, analytics (PRIORITY 4 📋)

---

## PRIORITY 1: Plugin Infrastructure Foundation

**Goal:** Create a robust Claude Code plugin architecture that registers, manages, and orchestrates all presentation generation tools.

### 1.1 Plugin Architecture Design

**File:** `plugin/plugin_manifest.json`

Define plugin metadata following Claude Code plugin specification:
```json
{
  "name": "presentation-generator",
  "version": "2.0.0",
  "description": "AI-assisted presentation generation from research to final deck",
  "author": "Stratfield",
  "main": "plugin/main.py",
  "skills": [
    "research",
    "outline",
    "draft-content",
    "generate-images",
    "build-presentation",
    "full-workflow"
  ],
  "dependencies": {
    "python": ">=3.8",
    "google-genai": ">=1.0.0",
    "python-pptx": ">=0.6.21"
  },
  "config_schema": "plugin/config_schema.json"
}
```

**Critical Files:**
- Create: `plugin/` directory structure
- Create: `plugin/__init__.py` - Plugin entry point
- Create: `plugin/plugin_manifest.json` - Metadata
- Create: `plugin/config_schema.json` - Configuration validation schema

### 1.2 Skill Registry System

**File:** `plugin/skill_registry.py`

Implement centralized registry for discovering and managing skills:

```python
class SkillRegistry:
    """Centralized registry for all presentation generation skills."""

    def register_skill(skill_id: str, skill_class: Type[BaseSkill]) -> None:
        """Register a skill with the plugin system."""

    def get_skill(skill_id: str) -> BaseSkill:
        """Retrieve a registered skill by ID."""

    def list_skills() -> List[SkillMetadata]:
        """List all registered skills with metadata."""

    def validate_skill(skill: BaseSkill) -> bool:
        """Validate skill implements required interface."""
```

**Skills to Register:**
- `research` - Web research and source gathering
- `outline` - Outline generation from research
- `draft-content` - AI-assisted content drafting
- `generate-images` - Visual asset generation (existing, wrapped)
- `build-presentation` - PowerPoint assembly (existing, wrapped)
- `full-workflow` - End-to-end orchestrator

**Critical Files:**
- Create: `plugin/skill_registry.py`
- Create: `plugin/base_skill.py` - Abstract base class for all skills

### 1.3 Base Skill Interface

**File:** `plugin/base_skill.py`

Define standard interface all skills must implement:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class SkillInput:
    """Input to a skill execution."""
    data: Dict[str, Any]
    context: Dict[str, Any]
    config: Dict[str, Any]

@dataclass
class SkillOutput:
    """Output from a skill execution."""
    success: bool
    data: Dict[str, Any]
    artifacts: List[str]  # File paths created
    errors: List[str]
    metadata: Dict[str, Any]

class BaseSkill(ABC):
    """Base class for all presentation generation skills."""

    @property
    @abstractmethod
    def skill_id(self) -> str:
        """Unique identifier for this skill."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """What this skill does."""

    @abstractmethod
    def execute(self, input: SkillInput) -> SkillOutput:
        """Execute the skill with given input."""

    @abstractmethod
    def validate_input(self, input: SkillInput) -> bool:
        """Validate input before execution."""

    def cleanup(self) -> None:
        """Optional cleanup after execution."""
        pass
```

### 1.4 Workflow Orchestrator

**File:** `plugin/workflow_orchestrator.py`

Coordinate multi-skill workflows with checkpoints:

```python
class WorkflowOrchestrator:
    """Manages execution of multi-skill workflows with user checkpoints."""

    def __init__(self, checkpoint_handler: CheckpointHandler):
        self.checkpoint_handler = checkpoint_handler
        self.skill_registry = SkillRegistry()

    def execute_workflow(
        self,
        workflow_id: str,
        initial_input: Dict[str, Any],
        config: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Execute a multi-phase workflow with checkpoints.

        Workflow phases:
        1. Research & Discovery (checkpoint)
        2. Content Development (checkpoint)
        3. Visual Asset Generation (checkpoint)
        4. Presentation Assembly (final output)
        """

    def run_phase(
        self,
        phase_name: str,
        skills: List[str],
        input: Dict[str, Any]
    ) -> PhaseResult:
        """Execute all skills in a phase sequentially."""

    def checkpoint(
        self,
        phase_name: str,
        phase_result: PhaseResult
    ) -> CheckpointDecision:
        """
        Stop workflow for user review.

        Returns:
        - CONTINUE: Proceed to next phase
        - RETRY: Re-run current phase with modifications
        - ABORT: Cancel workflow
        """
```

**Checkpoint System:**
- After Research: Review research output, approve outline direction
- After Content Development: Review slide drafts, approve content
- After Visual Generation: Review images, approve quality
- Final: Deliver presentation

**Critical Files:**
- Create: `plugin/workflow_orchestrator.py`
- Create: `plugin/checkpoint_handler.py` - User interaction for approvals

### 1.5 Unified CLI Entry Point

**File:** `plugin/cli.py`

Create single entry point for all plugin operations:

```bash
# Full workflow with checkpoints
python -m plugin.cli full-workflow "AI in Healthcare" --template cfa

# Individual skills
python -m plugin.cli research "AI in Healthcare" --output research.json
python -m plugin.cli outline research.json --output outline.md
python -m plugin.cli draft-content outline.md --output presentation.md
python -m plugin.cli generate-images presentation.md --resolution high
python -m plugin.cli build-presentation presentation.md --template cfa

# List available skills
python -m plugin.cli list-skills

# Validate plugin
python -m plugin.cli validate
```

**CLI Features:**
- Skill discovery and listing
- Individual skill execution
- Full workflow with checkpoint prompts
- Configuration management
- Progress reporting
- Error handling and recovery

**Critical Files:**
- Create: `plugin/cli.py` - Main CLI interface
- Create: `plugin/commands/` - Individual command implementations

### 1.6 Plugin Configuration System

**File:** `plugin/config_schema.json`

Define configuration schema for all plugin settings:

```json
{
  "research": {
    "max_sources": 20,
    "search_depth": "comprehensive",
    "citation_format": "APA"
  },
  "content": {
    "tone": "professional",
    "reading_level": "college",
    "max_bullets_per_slide": 5
  },
  "images": {
    "default_resolution": "high",
    "style_config": "templates/cfa_style.json"
  },
  "workflow": {
    "enable_checkpoints": true,
    "auto_split_presentations": true,
    "max_slides_per_presentation": 30
  }
}
```

**Critical Files:**
- Create: `plugin/config_schema.json`
- Create: `plugin/config_manager.py` - Configuration loading and validation

---

## PRIORITY 2: Phase 1 - Research & Discovery Tools

**Goal:** Build automated research, insight extraction, and outline generation capabilities.

### 2.1 Web Research Skill

**File:** `plugin/skills/research_skill.py`

Implement web search and content gathering:

```python
class ResearchSkill(BaseSkill):
    """Conducts web research and gathers sources on a topic."""

    skill_id = "research"
    display_name = "Web Research"
    description = "Search the web and gather authoritative sources"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Input: {
            "topic": str,
            "context": str (optional),
            "max_sources": int,
            "search_depth": "quick" | "standard" | "comprehensive"
        }

        Output: {
            "sources": [
                {
                    "url": str,
                    "title": str,
                    "content": str,
                    "relevance_score": float,
                    "citations": str
                }
            ],
            "summary": str,
            "key_themes": List[str]
        }
        """

        # 1. Execute web searches (Google/Bing API)
        # 2. Extract content from top results
        # 3. Score relevance using AI
        # 4. Summarize each source
        # 5. Identify key themes across sources
```

**Dependencies:**
- Web search API (Google Custom Search or Bing API)
- Content extraction library (BeautifulSoup, Newspaper3k, or Readability)
- Gemini API for relevance scoring and summarization

**Implementation Steps:**
1. Integrate search API (Google Custom Search as primary)
2. Build content extractor with fallback strategies
3. Implement relevance scoring using Gemini
4. Create source summarization pipeline
5. Add theme extraction across sources

**Critical Files:**
- Create: `plugin/skills/research_skill.py`
- Create: `plugin/lib/web_search.py` - Search API integration
- Create: `plugin/lib/content_extractor.py` - Web content extraction
- Update: `requirements.txt` - Add `beautifulsoup4`, `requests`, `google-api-python-client`

### 2.2 Citation Management

**File:** `plugin/lib/citation_manager.py`

Automatic citation formatting and tracking:

```python
class CitationManager:
    """Manages citations and references throughout workflow."""

    def format_citation(
        self,
        source: Dict[str, Any],
        style: str = "APA"
    ) -> str:
        """Format a source as a citation (APA, MLA, Chicago)."""

    def track_citation(
        self,
        source: Dict[str, Any],
        used_in: str
    ) -> str:
        """Track where a citation is used, return citation ID."""

    def generate_bibliography(
        self,
        citations: List[str]
    ) -> str:
        """Generate formatted bibliography from citation IDs."""

    def validate_citations(
        self,
        citations: List[str]
    ) -> List[ValidationIssue]:
        """Check citations for completeness and formatting."""
```

**Features:**
- Multiple citation formats (APA, MLA, Chicago)
- Automatic deduplication
- Citation tracking per slide
- Bibliography generation
- Fact-checking against sources

**Critical Files:**
- Create: `plugin/lib/citation_manager.py`

### 2.3 Insight Extraction Skill

**File:** `plugin/skills/insight_extraction_skill.py`

Extract key insights and arguments from research:

```python
class InsightExtractionSkill(BaseSkill):
    """Extracts key insights, arguments, and concepts from research."""

    skill_id = "extract-insights"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Input: {
            "research_output": ResearchOutput,
            "focus_areas": List[str] (optional)
        }

        Output: {
            "insights": [
                {
                    "statement": str,
                    "supporting_evidence": List[str],
                    "confidence": float,
                    "sources": List[str]
                }
            ],
            "arguments": [
                {
                    "claim": str,
                    "reasoning": str,
                    "evidence": List[str],
                    "counter_arguments": List[str]
                }
            ],
            "concept_map": {
                "nodes": List[Concept],
                "edges": List[Relationship]
            }
        }
        """

        # 1. Analyze research content using Gemini
        # 2. Identify key claims and supporting evidence
        # 3. Extract counter-arguments and address them
        # 4. Build concept hierarchy
        # 5. Score insight importance
```

**AI Tasks:**
- Claim extraction from sources
- Evidence mapping to claims
- Counter-argument identification
- Concept relationship detection
- Importance scoring

**Critical Files:**
- Create: `plugin/skills/insight_extraction_skill.py`
- Create: `plugin/lib/concept_mapper.py` - Knowledge graph builder

### 2.4 Outline Generation Skill

**File:** `plugin/skills/outline_skill.py`

Generate presentation outline from research and insights:

```python
class OutlineSkill(BaseSkill):
    """Generates presentation outline from research and insights."""

    skill_id = "outline"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Input: {
            "research": ResearchOutput,
            "insights": InsightOutput,
            "audience": str,
            "duration_minutes": int,
            "objectives": List[str]
        }

        Output: {
            "presentation_count": int,
            "presentations": [
                {
                    "audience": str,
                    "title": str,
                    "subtitle": str,
                    "slides": [
                        {
                            "slide_number": int,
                            "slide_type": str,
                            "title": str,
                            "purpose": str,
                            "key_points": List[str],
                            "supporting_sources": List[str]
                        }
                    ],
                    "estimated_duration": int
                }
            ]
        }
        """

        # 1. Analyze topic scope for multi-presentation detection
        # 2. Determine presentation count and audiences
        # 3. For each presentation:
        #    a. Generate narrative arc
        #    b. Determine slide sequence
        #    c. Assign content to slides
        #    d. Map sources to slides
        # 4. Optimize flow and pacing
```

**Multi-Presentation Logic:**
- Detect if topic warrants multiple presentations
- Auto-generate presentations for different audiences:
  - Executive summary (high-level, visual, 10-15 slides)
  - Detailed presentation (comprehensive, 20-30 slides)
  - Technical deep-dive (data-heavy, 30-40 slides)
- Different narrative arcs per audience
- Content reuse across presentations

**Critical Files:**
- Create: `plugin/skills/outline_skill.py`
- Create: `plugin/lib/narrative_engine.py` - Story arc optimization
- Create: `plugin/lib/presentation_splitter.py` - Multi-presentation detection

### 2.5 Interactive Research Assistant

**File:** `plugin/skills/research_assistant_skill.py`

Conversational AI for refining research scope:

```python
class ResearchAssistantSkill(BaseSkill):
    """Interactive assistant for refining research scope and direction."""

    skill_id = "research-assistant"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Conversational workflow:
        1. Analyze initial topic
        2. Ask clarifying questions:
           - What is the audience?
           - What is the presentation goal?
           - What level of detail is needed?
           - Are there specific subtopics to focus on?
           - Are there viewpoints to avoid or emphasize?
        3. Suggest research direction
        4. Get user approval
        5. Return refined research parameters
        """
```

**Clarifying Questions:**
- Audience characteristics (technical level, role, goals)
- Presentation objectives (inform, persuade, train, inspire)
- Content scope (broad overview vs. deep dive)
- Time constraints (presentation length, preparation time)
- Controversial topics (how to handle counter-arguments)
- Visual preferences (data-heavy vs. conceptual)

**Critical Files:**
- Create: `plugin/skills/research_assistant_skill.py`
- Create: `plugin/lib/conversation_manager.py` - Multi-turn dialogue handling

---

## PRIORITY 3: Phase 2 - Content Development Tools

**Goal:** AI-assisted content drafting, optimization, and quality assurance.

### 3.1 Content Drafting Skill

**File:** `plugin/skills/content_drafting_skill.py`

Generate slide content from outline:

```python
class ContentDraftingSkill(BaseSkill):
    """AI-assisted drafting of slide content."""

    skill_id = "draft-content"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Input: {
            "outline": OutlineOutput,
            "research": ResearchOutput,
            "style_guide": Dict[str, Any]
        }

        Output: {
            "presentation_files": List[str],  # presentation-{audience}.md
            "slides": [
                {
                    "slide_number": int,
                    "type": str,
                    "title": str,
                    "subtitle": str,
                    "content": List[ContentItem],
                    "graphics_description": str,
                    "speaker_notes": str,
                    "citations": List[str]
                }
            ]
        }
        """

        # For each slide in outline:
        # 1. Generate title and subtitle
        # 2. Draft bullet points from research
        # 3. Create graphics description
        # 4. Write speaker notes with narration
        # 5. Add citations for claims
        # 6. Format as markdown following pres-template.md
```

**AI Content Generation Tasks:**
- Title generation (clear, engaging, accurate)
- Bullet point drafting (concise, parallel structure)
- Speaker notes (full narration with stage directions)
- Graphics descriptions (detailed visual instructions)
- Table generation (from data in sources)
- Code examples (if relevant to topic)

**Quality Rules:**
- Max 5 bullets per slide
- Max 15 words per bullet
- Parallel grammatical structure
- Active voice preferred
- Cite claims with evidence

**Critical Files:**
- Create: `plugin/skills/content_drafting_skill.py`
- Create: `plugin/lib/content_generator.py` - AI content generation
- Reuse: `presentation-skill/lib/parser.py` (existing markdown parser)

### 3.2 Content Optimization Skill

**File:** `plugin/skills/content_optimization_skill.py`

Improve content quality through AI analysis:

```python
class ContentOptimizationSkill(BaseSkill):
    """Analyzes and optimizes slide content for quality."""

    skill_id = "optimize-content"

    def execute(self, input: SkillInput) -> SkillOutput:
        """
        Input: {
            "presentation_file": str,
            "optimization_goals": List[str]
        }

        Output: {
            "optimized_presentation": str,
            "improvements": [
                {
                    "slide_number": int,
                    "issue_type": str,
                    "original": str,
                    "improved": str,
                    "reasoning": str
                }
            ],
            "quality_score": float
        }
        """

        # Quality checks:
        # 1. Readability analysis (Flesch-Kincaid)
        # 2. Tone consistency
        # 3. Grammar and spelling
        # 4. Bullet parallelism
        # 5. Redundancy detection
        # 6. Citation completeness
        # 7. Visual description clarity
```

**Optimization Areas:**
- **Readability:** Target reading level, sentence complexity
- **Tone:** Professional, conversational, academic (configurable)
- **Structure:** Parallel bullets, logical flow
- **Redundancy:** Remove duplicate concepts across slides
- **Citations:** Ensure all claims are sourced
- **Visuals:** Validate graphic descriptions are specific

**Critical Files:**
- Create: `plugin/skills/content_optimization_skill.py`
- Create: `plugin/lib/quality_analyzer.py` - Content quality metrics
- Update: `requirements.txt` - Add `textstat` for readability

### 3.3 Graphics Description Validator

**File:** `plugin/lib/graphics_validator.py`

Validate graphic descriptions before image generation:

```python
class GraphicsValidator:
    """Validates graphic descriptions for image generation quality."""

    def validate_description(
        self,
        description: str,
        slide_context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Check graphic description for:
        - Specificity (concrete vs. vague)
        - Visual elements (what to actually draw)
        - Brand alignment (mentions brand colors, style)
        - Layout hints (composition, framing)
        - Text avoidance (no text in image)

        Returns suggestions for improvement.
        """

    def suggest_improvements(
        self,
        description: str,
        issues: List[str]
    ) -> str:
        """Generate improved description addressing issues."""
```

**Validation Rules:**
- Must specify visual elements (not just concepts)
- Should reference brand colors from style config
- Should avoid text/labels in image
- Should specify composition (centered, split-screen, etc.)
- Should be 2-4 sentences minimum

**Critical Files:**
- Create: `plugin/lib/graphics_validator.py`

---

## PRIORITY 4: Production Enhancements (Phases 3-4)

**Goal:** Make experimental features production-ready and enhance quality.

### 4.1 Production Validation System

**File:** `plugin/skills/validation_skill.py`

Make visual validation production-default:

**Changes:**
1. Remove experimental flag, enable by default
2. Add platform detection (skip on non-Windows gracefully)
3. Improve error handling and recovery
4. Add validation confidence scoring
5. Create validation report with metrics

**Enhancements:**
- Cross-platform slide export (use PowerPoint Online API as fallback)
- Validation caching (skip re-validation of unchanged slides)
- Parallel validation (validate multiple slides concurrently)
- Cost estimation before validation
- Quality trend tracking

**Critical Files:**
- Update: `presentation-skill/lib/visual_validator.py`
- Create: `plugin/lib/slide_export_cloud.py` - Cloud-based export for non-Windows

### 4.2 Enhanced Refinement Engine

**File:** `plugin/skills/refinement_skill.py`

Improve refinement with user feedback:

**Enhancements:**
1. Expand issue pattern library (10+ new patterns)
2. Add interactive refinement (user approves/rejects)
3. Cost-aware refinement (estimate before generation)
4. Multi-round refinement (iterative improvement)
5. A/B comparison (show before/after)

**New Issue Patterns:**
- Aspect ratio mismatch
- Brand color dominance (too much/too little)
- Visual complexity (too busy/too simple)
- Image clarity (blurry, pixelated)
- Composition balance (off-center, awkward)

**Critical Files:**
- Update: `presentation-skill/lib/refinement_engine.py`
- Create: `plugin/lib/refinement_ui.py` - Interactive approval

### 4.3 Workflow Analytics

**File:** `plugin/lib/analytics.py`

Track workflow performance and quality:

```python
class WorkflowAnalytics:
    """Track metrics across workflow execution."""

    def track_phase(
        self,
        phase_name: str,
        duration: float,
        success: bool,
        metrics: Dict[str, Any]
    ) -> None:
        """Record phase execution metrics."""

    def track_api_usage(
        self,
        api_name: str,
        call_count: int,
        estimated_cost: float
    ) -> None:
        """Track API calls and costs."""

    def generate_report(self) -> AnalyticsReport:
        """
        Generate comprehensive report:
        - Phase timing breakdown
        - API usage and estimated costs
        - Quality scores per slide
        - Validation pass/fail rates
        - Refinement attempt distribution
        - Total workflow duration
        """
```

**Metrics Tracked:**
- Phase timing (research, outline, draft, images, build)
- API calls per phase (Gemini, search, etc.)
- Estimated costs (API usage × pricing)
- Quality scores (validation rubric)
- Refinement success rate
- User checkpoint decisions

**Critical Files:**
- Create: `plugin/lib/analytics.py`
- Create: `plugin/lib/cost_estimator.py` - API cost calculation

---

## Implementation Roadmap

### ✅ Milestone 1: Plugin Infrastructure (COMPLETED 2026-01-04)

**Status:** ✅ COMPLETE

**Deliverables:**
- ✅ Plugin manifest and directory structure
- ✅ Base skill interface and registry
- ✅ Workflow orchestrator with checkpoint system
- ✅ Unified CLI with entry point commands
- ✅ Configuration management
- ✅ Comprehensive test plan and infrastructure
- ✅ Primary test data (Rochester 2GC prompt)
- ✅ Complete documentation
- 📋 State detection and resumption system (foundation laid, full implementation in PRIORITY 2)
- 📋 Incremental regeneration capabilities (foundation laid, full implementation in PRIORITY 2)
- 📋 Error recovery and rollback (foundation laid, full implementation in PRIORITY 2)

**Success Criteria:**
- ✅ Can register and discover skills
- ✅ Can execute individual skills via CLI
- ✅ Can orchestrate multi-skill workflows
- ✅ Checkpoints pause for user input
- ✅ Configuration validates correctly
- ✅ Test infrastructure complete with 100+ test cases defined
- ✅ Primary test data stored and documented
- 📋 Can auto-detect workflow state from artifacts (foundation in place)
- 📋 Can resume from any intermediate file (foundation in place)
- 📋 Can start workflow from any of 11 entry points (CLI commands created, skills TBD)
- 📋 Detects manual edits and suggests next steps (foundation in place)

**Notes:**
- State detection, resumption, and incremental regeneration foundations are in place in WorkflowOrchestrator
- Full implementations of StateDetector, ChangeDetector, IncrementalGenerator will be completed alongside skill implementations in PRIORITY 2-3
- This allows us to test these features with real skills rather than mocks

**Pull Request:** #3

**Branch:** feature/plugin-infrastructure

**Commits:** 6 commits, 8,000+ lines

### Milestone 2: Research Tools (3-4 weeks)
**Deliverables:**
- Web research skill with search API
- Content extraction and summarization
- Citation management system
- Insight extraction skill
- Outline generation with multi-presentation detection
- Interactive research assistant

**Success Criteria:**
- Can research a topic and gather 10-20 sources
- Can extract key insights from sources
- Can generate presentation outlines
- Can detect and split into multiple presentations
- Can format citations correctly

### Milestone 3: Content Development (2-3 weeks)
**Deliverables:**
- Content drafting skill
- Content optimization skill
- Graphics description validator
- Quality analyzer

**Success Criteria:**
- Can generate complete presentation markdown from outline
- Can optimize content for readability and tone
- Can validate graphic descriptions before image generation
- Can produce quality scores

### Milestone 4: Production Polish (2-3 weeks)
**Deliverables:**
- Production-ready validation
- Enhanced refinement with user feedback
- Workflow analytics and reporting
- Cross-platform compatibility
- Comprehensive error handling

**Success Criteria:**
- Validation works on Windows by default
- Refinement offers user approval workflow
- Analytics report shows costs and quality metrics
- Graceful degradation on all platforms
- End-to-end workflow completes successfully

### Milestone 5: Integration & Testing (1-2 weeks)
**Deliverables:**
- End-to-end workflow testing
- Multi-presentation scenario testing
- Edge case handling
- Documentation updates
- Example workflows

**Success Criteria:**
- Full 11-step workflow completes without errors
- Multi-presentation generation works
- All checkpoints function correctly
- Comprehensive documentation exists
- Example presentations generated

---

## Critical Files Summary

### New Files to Create (Plugin Infrastructure)
```
plugin/
├── __init__.py
├── plugin_manifest.json
├── config_schema.json
├── cli.py
├── base_skill.py
├── skill_registry.py
├── workflow_orchestrator.py
├── checkpoint_handler.py
├── config_manager.py
├── commands/
│   ├── __init__.py
│   ├── research.py
│   ├── outline.py
│   ├── draft.py
│   ├── generate_images.py
│   ├── build.py
│   ├── resume.py               # NEW: Auto-resume workflow
│   ├── status.py               # NEW: Show current state
│   ├── from_research.py        # NEW: Start from research.json
│   ├── from_outline.py         # NEW: Start from outline.md
│   ├── from_draft.py           # NEW: Start from presentation.md
│   └── from_images.py          # NEW: Start from images/
├── skills/
│   ├── __init__.py
│   ├── research_skill.py
│   ├── insight_extraction_skill.py
│   ├── outline_skill.py
│   ├── research_assistant_skill.py
│   ├── content_drafting_skill.py
│   ├── content_optimization_skill.py
│   ├── validation_skill.py
│   └── refinement_skill.py
└── lib/
    ├── __init__.py
    ├── web_search.py
    ├── content_extractor.py
    ├── citation_manager.py
    ├── concept_mapper.py
    ├── narrative_engine.py
    ├── presentation_splitter.py
    ├── conversation_manager.py
    ├── content_generator.py
    ├── quality_analyzer.py
    ├── graphics_validator.py
    ├── slide_export_cloud.py
    ├── refinement_ui.py
    ├── analytics.py
    ├── cost_estimator.py
    ├── state_detector.py          # NEW: Auto-detect workflow state
    ├── change_detector.py          # NEW: Detect manual edits
    ├── incremental_generator.py    # NEW: Smart regeneration
    └── recovery_manager.py         # NEW: Error recovery & rollback
```

### Files to Update
```
presentation-skill/lib/visual_validator.py  (production-ready)
presentation-skill/lib/refinement_engine.py (enhanced patterns)
requirements.txt (new dependencies)
README.md (plugin documentation)
CLAUDE.md (updated workflow documentation)
```

### Files to Reuse (No Changes)
```
lib/config_loader.py
lib/gemini_client.py
lib/image_prompt_builder.py
presentation-skill/lib/parser.py
presentation-skill/lib/type_classifier.py
presentation-skill/lib/image_generator.py
presentation-skill/lib/assembler.py
presentation-skill/templates/ (all existing templates)
```

---

## Dependencies to Add

**requirements.txt additions:**
```
# Web research
beautifulsoup4>=4.12.0
requests>=2.31.0
google-api-python-client>=2.100.0
newspaper3k>=0.2.8

# Content analysis
textstat>=0.7.3
spacy>=3.7.0

# Data validation
jsonschema>=4.19.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## Testing Strategy

### Unit Tests
- Each skill implements `test_execute()` method
- Mock API calls for reproducibility
- Validate input/output contracts
- Test error handling

### Integration Tests
- End-to-end workflow tests
- Multi-presentation scenarios
- Checkpoint interactions
- Platform compatibility

### Quality Tests
- Content quality validation
- Image generation quality
- Citation accuracy
- Readability metrics

---

## Risk Mitigation

### API Rate Limits
- Implement exponential backoff
- Queue management for batch operations
- Cost estimation before execution
- Configurable retry policies

### Content Quality
- Validation at every step
- User checkpoints for approval
- Automated quality scoring
- Fallback to manual editing

### Platform Compatibility
- Windows-specific features gracefully degraded
- Cloud-based alternatives for slide export
- Platform detection and feature flags
- Comprehensive error messages

### Cost Management
- Upfront cost estimation
- Budget limits per workflow
- API usage tracking and reporting
- Efficient caching strategies

---

## Success Metrics

### Functional
- ✅ All 11 workflow steps implemented
- ✅ Multi-presentation detection works
- ✅ Checkpoints pause for user approval
- ✅ End-to-end workflow completes successfully

### Quality
- ✅ Research produces 10-20 relevant sources
- ✅ Content quality score > 80%
- ✅ Validation pass rate > 75%
- ✅ User checkpoint approval rate > 90%

### Performance
- ✅ Research phase: < 5 minutes
- ✅ Outline generation: < 2 minutes
- ✅ Content drafting: < 5 minutes
- ✅ Image generation: < 10 minutes
- ✅ Total workflow: < 30 minutes

### Cost
- ✅ Average workflow cost: < $5
- ✅ Cost estimation accuracy: +/- 20%
- ✅ API usage within budget limits

---

## Future Enhancements (Post-v2.0)

### Advanced Features
- Multi-modal content (video, audio)
- Real-time collaboration
- Audience analytics integration
- A/B testing of presentations
- Auto-translation for international audiences

### AI Improvements
- Custom fine-tuned models
- Reinforcement learning from user feedback
- Style transfer from example presentations
- Predictive audience engagement scoring

### Integration
- Google Slides export
- Keynote export
- PDF generation with animations
- Learning management system (LMS) integration
- CRM integration for sales presentations

---

## Conclusion

This plan provides a comprehensive roadmap for building a production-ready Claude Code plugin for AI-assisted presentation generation. The phased approach ensures solid foundations (plugin infrastructure) before building advanced features (research, content development).

**Key Strengths:**
- Leverages 70% of existing, proven codebase
- Modular architecture for maintainability
- User checkpoints for control and quality
- Auto-detection of multi-presentation needs
- Production-ready validation and refinement
- **Start at any workflow step - maximum flexibility**
- **Smart resumption with manual edit detection**
- **Incremental regeneration saves time and cost**

**Next Steps:**
1. Review and approve this plan
2. Begin Milestone 1 (Plugin Infrastructure)
3. Iterate on checkpoints for user feedback
4. Progress through research and content tools
5. Deliver complete plugin system
