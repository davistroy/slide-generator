# PRIORITY 3: Content Development Tools - Implementation Plan

## Current Status

**Branch:** `feature/content-development`
**Base:** `main` (includes PRIORITY 1 + PRIORITY 2 + Agent SDK)
**Goal:** AI-assisted content drafting, optimization, and quality assurance

---

## What's Already Complete

### ✅ PRIORITY 1: Plugin Infrastructure
- Base skill system
- Skill registry
- Workflow orchestrator
- CLI commands
- Configuration management

### ✅ PRIORITY 2: Research & Discovery
- ResearchAgent (Agent SDK with tool use)
- InsightAgent (API)
- OutlineAgent (API)
- CitationManager
- WebSearch
- ContentExtractor

### ✅ Agent SDK Integration
- Autonomous research workflows
- Tool use (web_search, extract_content, add_citation)
- Multi-turn conversations with state management

---

## PRIORITY 3: What We're Building

### Goal
Transform research and outlines into **polished presentation content** ready for image generation and PowerPoint assembly.

### Workflow Position
```
Research → Insights → Outline → [CONTENT DRAFTING] → Images → PowerPoint
                                    ↑ PRIORITY 3
```

---

## Components to Implement

### 1. ContentDraftingSkill

**File:** `plugin/skills/content_drafting_skill.py`

**Purpose:** Generate complete slide content from outlines

**Input:**
- Outline from OutlineSkill
- Research from ResearchSkill
- Style guide (tone, audience, constraints)

**Output:**
- Presentation markdown file(s)
- Per-slide content:
  - Title & subtitle
  - Bullet points (max 5, max 15 words each)
  - Graphics description (detailed visual instructions)
  - Speaker notes (full narration)
  - Citations

**AI Tasks:**
- Title generation (clear, engaging, accurate)
- Bullet drafting (concise, parallel structure)
- Graphics descriptions (specific visual details)
- Speaker notes (conversational narration)
- Citation placement

**Use:** Claude Agent SDK or Plain API
- **Recommendation:** Agent SDK if needs tool access (citation lookup, research reference)
- **Recommendation:** Plain API for straightforward generation

---

### 2. ContentOptimizationSkill

**File:** `plugin/skills/content_optimization_skill.py`

**Purpose:** Improve quality through AI analysis

**Input:**
- Presentation markdown file
- Optimization goals (readability, tone, etc.)

**Output:**
- Optimized presentation file
- List of improvements made
- Quality score (0-100)

**Quality Checks:**
1. **Readability** - Flesch-Kincaid analysis
2. **Tone Consistency** - Professional/conversational/academic
3. **Grammar & Spelling** - Language correctness
4. **Bullet Parallelism** - Consistent structure
5. **Redundancy** - Remove duplicates across slides
6. **Citation Completeness** - All claims sourced
7. **Visual Clarity** - Graphics descriptions specific

**Use:** Claude API (single-turn analysis and optimization)

---

### 3. GraphicsValidator

**File:** `plugin/lib/graphics_validator.py`

**Purpose:** Validate graphics descriptions before image generation

**Validation Rules:**
- ✅ Specificity (concrete vs vague)
- ✅ Visual elements (what to actually draw)
- ✅ Brand alignment (mentions brand colors/style)
- ✅ Layout hints (composition, framing)
- ✅ Text avoidance (no text in images)
- ✅ Length (2-4 sentences minimum)

**Output:**
- Validation result (pass/fail)
- Issues found
- Suggested improvements

**Use:** Claude API or rule-based validation
- **Recommendation:** Hybrid (rules first, Claude for improvement suggestions)

---

### 4. Supporting Libraries

#### content_generator.py
**Purpose:** Core content generation logic

**Functions:**
- `generate_title()` - Create slide titles
- `generate_bullets()` - Draft bullet points
- `generate_speaker_notes()` - Write narration
- `generate_graphics_description()` - Create visual instructions
- `format_slide_markdown()` - Output in pres-template.md format

#### quality_analyzer.py
**Purpose:** Content quality metrics

**Functions:**
- `calculate_readability()` - Flesch-Kincaid score
- `check_tone_consistency()` - Analyze tone
- `check_bullet_parallelism()` - Grammar structure
- `detect_redundancy()` - Find duplicate concepts
- `validate_citations()` - Check citation completeness

**Dependencies:**
- `textstat` - Readability metrics
- Claude API - Tone and grammar analysis

---

## Implementation Strategy

### Phase 1: Core Content Drafting (Priority)
1. Implement `content_generator.py` with Claude API
2. Implement `ContentDraftingSkill`
3. Test with carburetor outline
4. Verify output follows pres-template.md format

### Phase 2: Quality & Validation
5. Implement `quality_analyzer.py`
6. Implement `ContentOptimizationSkill`
7. Implement `graphics_validator.py`
8. Test optimization on drafted content

### Phase 3: Integration & Testing
9. Write comprehensive unit tests
10. Test end-to-end: Research → Outline → Draft → Optimize
11. Update documentation
12. Create PR

---

## Example Workflow

**Input:** Rochester 2GC Carburetor Outline (from OutlineSkill)

```yaml
Presentation: "Rochester 2GC: Operation & Rebuild"
Slides:
  - slide_number: 1
    slide_type: TITLE SLIDE
    title: "Rochester 2GC Carburetor"
    purpose: "Introduce the topic"
    key_points: []

  - slide_number: 2
    slide_type: CONTENT
    title: "How the 2GC Works"
    purpose: "Explain carburetor operation"
    key_points:
      - "Air-fuel mixing principles"
      - "Venturi effect"
      - "Float system operation"
```

**ContentDraftingSkill Output:**

```markdown
## SLIDE 1: TITLE SLIDE

**Title:** Rochester 2GC Carburetor: Operation & Rebuild Guide

**Subtitle:** Complete teardown, rebuild, and testing for DIY mechanics

**Content:**
- Presented by: [Presenter Name]
- Target Audience: DIY mechanics with basic tools

**GRAPHICS:**

**Graphic 1: Rochester 2GC Hero Image**
- Purpose: Establish subject and visual appeal
- Type: Product photograph with professional lighting
- Elements: Fully assembled Rochester 2GC carburetor, chrome finish prominently visible, positioned at slight angle showing air horn and linkage, dark background for contrast
- Labels: None (clean product shot)
- Brand Colors: Chrome/silver primary, deep blue background (#004F71)

**SPEAKER NOTES:**

"Welcome! Today we're diving deep into one of the most reliable carburetors ever made - the Rochester 2GC. Whether you've pulled one off a classic Chevy or found one at a swap meet, this guide will walk you through complete disassembly, rebuild, and testing.

[Transition: Click to next slide]"

---

## SLIDE 2: CONTENT

**Title:** How the Rochester 2GC Works

**Content:**

**The Basics:**
- Two-barrel design provides balanced air-fuel mixture
- Venturi effect creates vacuum for fuel draw
- Float system maintains consistent fuel level
- Choke system enriches mixture for cold starts
- Secondary throttle opens under load

**GRAPHICS:**

**Graphic 1: Cutaway Diagram of 2GC Operation**
- Purpose: Show internal airflow and fuel pathways
- Type: Technical cutaway illustration
- Elements: Cross-section view showing venturi, float bowl, main jets, choke plate, throttle plates, air passages (shown as blue arrows), fuel passages (shown as red), internal chambers visible
- Labels: Venturi, Float Bowl, Main Jet, Choke Plate, Throttle Plates, Air Flow, Fuel Flow
- Brand Colors: Red (#DD0033) for fuel paths, blue for air paths, gray/silver for metal components

**SPEAKER NOTES:**

"Let's understand how this carburetor actually works before we tear it apart.

The 2GC is a two-barrel design - that means it has two separate air passages called venturis. As air rushes through these narrowing passages, it creates a vacuum. That vacuum pulls fuel up through the main jets, mixing it with the incoming air.

The float system works just like your toilet tank - as fuel is consumed, the float drops, opening a valve to let more fuel in. When the level is right, the float rises and shuts the valve off. Simple, reliable, mechanical.

[Pause]

Understanding this operation will help you diagnose problems during rebuild.

[Transition]"

**BACKGROUND:**

**Citations:**
- cite-001: Rochester Products Division Service Manual (Choke and float operation)
- cite-003: Rebuilding Rochester Carburetors (Venturi principles)

---
```

**ContentOptimizationSkill Improvements:**

```yaml
improvements:
  - slide_number: 2
    issue_type: "Bullet length"
    original: "Two-barrel design provides balanced air-fuel mixture"
    improved: "Two-barrel design balances air-fuel mixture"
    reasoning: "Reduced from 7 to 5 words while maintaining meaning"

  - slide_number: 2
    issue_type: "Graphics clarity"
    original: "air passages (shown as blue arrows)"
    improved: "air passages shown as flowing blue arrows with directional indicators"
    reasoning: "More specific visual instruction for image generation"

quality_score: 87.5
```

---

## Technology Stack

### AI/LLM:
- **Claude Agent SDK** - Content drafting with tool use (if needed)
- **Claude API** - Optimization, analysis, validation
- **Gemini API** - Image generation (existing, unchanged)

### Libraries:
- **textstat** - Readability metrics (Flesch-Kincaid, etc.)
- **anthropic** - Claude API integration (existing)
- **Existing:** CitationManager, parser.py, etc.

---

## Testing Strategy

### Unit Tests

**ContentDraftingSkill:**
- Test title generation
- Test bullet point generation
- Test speaker notes generation
- Test graphics description generation
- Test markdown formatting
- Test citation integration

**ContentOptimizationSkill:**
- Test readability analysis
- Test tone detection
- Test redundancy detection
- Test citation validation
- Test improvement suggestions
- Test quality scoring

**GraphicsValidator:**
- Test specificity detection
- Test brand alignment checking
- Test layout hint validation
- Test improvement suggestions

### Integration Tests

**End-to-End:**
1. ResearchSkill → sources
2. InsightExtractionSkill → insights
3. OutlineSkill → outline
4. **ContentDraftingSkill** → markdown
5. **ContentOptimizationSkill** → optimized markdown
6. ImageGenerator → slide images (existing)
7. Assembler → PowerPoint (existing)

---

## Success Criteria

✅ ContentDraftingSkill generates valid markdown following pres-template.md
✅ All slides have titles, content, graphics, speaker notes
✅ Citations properly integrated
✅ ContentOptimizationSkill improves quality score by 10+ points
✅ GraphicsValidator catches vague descriptions
✅ Unit test coverage >90%
✅ End-to-end workflow: research → final presentation works

---

## Estimated Effort

**ContentDraftingSkill:** 2-3 hours
- Implement content_generator.py
- Implement skill with Claude API
- Format markdown output

**ContentOptimizationSkill:** 1-2 hours
- Implement quality_analyzer.py
- Implement skill with Claude API
- Quality scoring logic

**GraphicsValidator:** 1 hour
- Rule-based validation
- Claude API for improvements

**Testing:** 2 hours
- Unit tests for all components
- Integration test for workflow

**Total:** 6-8 hours

---

## Next Steps

1. **Start with content_generator.py** - Core generation logic
2. **Implement ContentDraftingSkill** - Use content_generator
3. **Test with carburetor outline** - Verify output quality
4. **Implement optimization** - Quality improvements
5. **Integration test** - Full workflow
6. **PR** - Merge to main

---

## Questions to Address

1. **Should ContentDraftingSkill use Agent SDK or plain API?**
   - Agent SDK if needs tool access (citation lookup)
   - Plain API if straightforward generation
   - **Recommendation:** Start with plain API, add agent capabilities if needed

2. **How strict should quality rules be?**
   - Max bullets per slide (5)
   - Max words per bullet (15)
   - Required citation rate (every claim?)
   - **Recommendation:** Configurable via style guide

3. **Should we support multiple output formats?**
   - Currently: pres-template.md format
   - Future: Google Slides format, Keynote format?
   - **Recommendation:** Start with markdown, add formats later

---

## Documentation to Create

- [ ] `CONTENT_GENERATION_GUIDE.md` - How content drafting works
- [ ] Update `API_ARCHITECTURE.md` - Add content development phase
- [ ] Update `PLUGIN_IMPLEMENTATION_PLAN.md` - Mark PRIORITY 3 complete
- [ ] Add examples to skill documentation

---

Ready to start implementing! 🚀
