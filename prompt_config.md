---
# ============================================================================
# PROMPT CONFIGURATION - Image Generation Prompt Builder
# ============================================================================
# This configuration file controls how the ImagePromptBuilder generates
# prompts for AI image generation. All hardcoded instructions, templates,
# and rules have been externalized here for easy customization.
#
# Format: YAML frontmatter (this section) + Markdown documentation (below)
# Dependencies: python-frontmatter
# ============================================================================

# Resolution Definitions
# ----------------------------------------------------------------------------
# Defines available output resolutions with dimensions and aspect ratios.
# Used to determine image size and composition rules.

resolutions:
  high:
    width: 3200
    height: 1900
    aspect_ratio: "16:9"
    label: "High Resolution 4K"
    description: "High-quality 4K images for final presentations"

  medium:
    width: 1940
    height: 940
    aspect_ratio: "16:9"
    label: "Medium Resolution HD"
    description: "Medium-quality HD images for web or draft presentations"

  small:
    width: 1240
    height: 1000
    aspect_ratio: "5:4"
    label: "Small Resolution (No Titles)"
    description: "Compact images designed for text overlay (no embedded titles)"


# Prompt Template Structure
# ----------------------------------------------------------------------------
# Defines the overall structure and sections of generated prompts.
# Sections are rendered in order and can be enabled/disabled.

prompt_template:
  preamble: "Generate a professional presentation concept image."

  sections:
    - name: "SLIDE"
      format: "{number} - \"{title}\""
      enabled: true
      description: "Slide number and title for context"

    - name: "CONCEPT"
      format: "{visual_concept}"
      enabled: true
      description: "One-sentence visual concept description"

    - name: "VISUAL ELEMENTS"
      format: "numbered_list"
      enabled: true
      description: "List of key visual elements to include"

    - name: "VISUAL HIERARCHY"
      format: "{primary} > supporting elements"
      enabled: true
      description: "Visual priority hierarchy"
      embedded_in_composition: true  # Rendered within COMPOSITION section

    - name: "COMPOSITION"
      format: "key_value_list"
      enabled: true
      description: "Layout and composition instructions"

    - name: "STYLE"
      format: "See attached style guide: {style_path}"
      enabled: true
      description: "Reference to style configuration"
      note: "(All style details including colors, fonts, and visual treatment are defined in the style configuration)"

    - name: "FORMAT"
      format: "bulleted_list"
      enabled: true
      description: "Technical format specifications and constraints"


# Resolution-Specific Composition Rules
# ----------------------------------------------------------------------------
# Different composition instructions for each resolution.
# "small" resolution has special rules for no-title backgrounds.

composition_rules:
  small:
    instructions:
      - "Fill entire canvas edge-to-edge with visual content"
      - "NO header space reserved - use full vertical height"
      - "CRITICAL: DO NOT include ANY titles or slide numbers in the image"
      - "No \"Slide X\", no titles like \"{title}\""
      - "Diagram labels and callouts are acceptable"
      - "Use entire canvas without reserved header/title space"
      - "Full-bleed visual composition"

    layout_defaults:
      header_space: false
      edge_to_edge: true
      title_allowed: false
      slide_number_allowed: false

    format_instructions:
      - "Resolution: {width}x{height} ({aspect_ratio} aspect ratio)"
      - "CRITICAL: DO NOT include ANY titles or slide numbers in the image"
      - "No \"Slide X\", no titles like \"{title}\""
      - "Diagram labels and callouts are acceptable"
      - "Use entire canvas without reserved header/title space"
      - "Full-bleed visual composition"

  high:
    instructions:
      - "Title: {title_treatment} at top"
      - "Reserve top 15% for slide title"
      - "Title must be clearly readable"
      - "Main content: centered in remaining space"
      - "Professional presentation hierarchy"

    layout_defaults:
      header_space: true
      edge_to_edge: false
      title_allowed: true
      slide_number_allowed: true

    format_instructions:
      - "Resolution: {width}x{height} ({aspect_ratio} aspect ratio)"
      - "Title must be clearly readable"

  medium:
    instructions:
      - "Title: {title_treatment} at top"
      - "Reserve top 15% for slide title"
      - "Title must be clearly readable"
      - "Main content: centered in remaining space"
      - "Professional presentation hierarchy"

    layout_defaults:
      header_space: true
      edge_to_edge: false
      title_allowed: true
      slide_number_allowed: true

    format_instructions:
      - "Resolution: {width}x{height} ({aspect_ratio} aspect ratio)"
      - "Title must be clearly readable"


# Generic Prompt Instructions
# ----------------------------------------------------------------------------
# Universal instructions applied to ALL resolutions.
# These appear in the FORMAT section of every prompt.

generic_instructions:
  - "No verbatim bullet points from the slide content"
  - "Use diagrams, icons, visual metaphors instead of text"
  - "Professional presentation quality"
  - "High visual impact"
  - "Clear visual communication"


# Layout Detection Patterns
# ----------------------------------------------------------------------------
# Regex patterns to detect optimal layout from slide content.
# First match wins (order matters).

layout_detection:
  split_screen:
    patterns:
      - "comparison"
      - "side-by-side"
      - "before.*after"
      - "split"
      - "versus"
    description: "Divide canvas vertically for comparative content"
    layout_name: "split_screen"

  diagram_focused:
    patterns:
      - "diagram"
      - "flow"
      - "chart"
      - "process"
      - "cycle"
    description: "Center large diagram with supporting labels"
    layout_name: "diagram_focused"

  centered:
    patterns:
      - "centered"
      - "title slide"
      - "hero"
      - "focus"
    description: "Single centered focal point"
    layout_name: "centered"

  # Default fallback (used if no pattern matches)
  default:
    layout_name: "title_top_visual_below"
    description: "Standard layout with title at top, visual below"


# Element Extraction Patterns
# ----------------------------------------------------------------------------
# Markers and patterns for extracting structured data from slide content.
# Used to parse graphics descriptions and content sections.

element_extraction:
  purpose:
    markers:
      - "Purpose:"
      - "Purpose of visual:"
      - "Visual purpose:"
    fallback_extract: true
    description: "Extract visual purpose statement"

  elements:
    markers:
      - "Elements:"
      - "Visual elements:"
      - "Include:"
    list_format: "bullet_or_numbered"
    description: "Extract list of visual elements to include"
    end_markers:
      - "Labels:"
      - "Relationships:"
      - "\n\n"  # Double newline

  type:
    markers:
      - "Type:"
      - "Visual type:"
      - "Layout:"
    valid_types:
      - "diagram"
      - "chart"
      - "graph"
      - "illustration"
      - "photo"
      - "icon_set"
      - "split_screen"
      - "before/after"
      - "comparison"
    description: "Extract visual type classification"

  # Content extraction settings
  content_parsing:
    max_concepts: 5
    min_concept_length: 10
    max_concept_length: 200
    bullet_markers: ["-", "•"]
    numbered_pattern: "^\\d+\\."

  # Table data extraction
  table_parsing:
    enabled: true
    skip_header: true
    cell_separator: " - "
    max_rows: 10


# Visual Hierarchy Templates
# ----------------------------------------------------------------------------
# Templates for rendering visual hierarchy in prompts.

visual_hierarchy:
  primary_format: "{primary_element} > supporting elements"
  fallback_format: "Primary: {primary_element}"
  max_elements_shown: 5
  description: "Define visual priority order"


# Metadata Section Labels
# ----------------------------------------------------------------------------
# Labels used in output files and console output.

metadata_labels:
  header_title: "IMAGE GENERATION PROMPT"
  structured_data_header: "Structured Data"
  text_prompt_header: "Text Prompt (sent to Gemini)"
  resolution_label: "Resolution:"
  aspect_ratio_label: "Aspect Ratio:"
  special_instructions_label: "Special:"


# Default Title Treatment
# ----------------------------------------------------------------------------
# How slide titles should be rendered in standard resolutions.

title_treatment:
  default: "prominent_header"
  options:
    - "prominent_header"
    - "subtle_header"
    - "centered_title"
    - "overlay_text"


# API Settings and Timeouts
# ----------------------------------------------------------------------------
# Configuration for API models, retry behavior, and timeout values.
# These values were previously hardcoded throughout the codebase.

api_settings:
  # Model configuration - which AI models to use for different tasks
  classification_model: "gemini-2.0-flash-exp"     # Fast model for slide type classification
  validation_model: "gemini-2.0-flash-exp"         # Fast model for slide validation
  image_generation_model: "gemini-3-pro-image-preview"  # Specialized image generation model

  # Retry and timeout configuration
  max_retries: 3                  # How many times to retry failed API calls
  retry_delay_seconds: 5          # How long to wait between retries
  api_timeout_ms: 300000          # API request timeout (300,000 ms = 5 minutes)

  # Validation thresholds
  validation_threshold: 0.75              # Minimum score (75%) for slide to pass validation
  min_improvement_threshold: 0.05         # Minimum improvement needed to try refinement (5%)
  diminishing_returns_threshold: 0.90     # Stop refining if score is already this high (90%)


# Slide Export Settings (Windows Only)
# ----------------------------------------------------------------------------
# Configuration for PowerPoint slide export via PowerShell COM automation.
# Used for visual validation - exports PPTX slides to JPG images.

slide_export:
  default_dpi: 150                   # DPI for exported slide images (150 is good quality)
  export_timeout_seconds: 60         # Timeout for slide export operation
  powerpoint_timeout_seconds: 10     # Timeout for PowerPoint application to open
  aspect_ratio_multiplier_16_9:      # Calculation constants for 16:9 aspect ratio
    width: 10.67                     # Width multiplier (DPI * 10.67)
    height: 6                        # Height multiplier (DPI * 6)


# Image Generation API Settings
# ----------------------------------------------------------------------------
# Configuration for actual image generation via Gemini API.
# Controls model selection, generation parameters, and timing.

image_generation:
  # Gemini API Configuration
  model: "gemini-3-pro-image-preview"

  # Resolution-specific generation parameters
  generation_params:
    small:
      aspect_ratio: "5:4"
      image_size: "STANDARD"
      delay_seconds: 4
      description: "Small res for PowerPoint backgrounds (no text)"

    medium:
      aspect_ratio: "16:9"
      image_size: "STANDARD"
      delay_seconds: 5
      description: "Medium res for web presentations"

    high:
      aspect_ratio: "16:9"
      image_size: "4K"
      delay_seconds: 6
      description: "High res 4K for print and final presentations"

  # Prompt file parsing
  prompt_parsing:
    # Section header to extract from prompt markdown files
    text_prompt_header: "## Text Prompt (sent to Gemini)"

    # Validation check - warn if missing from prompt
    required_validation_text: "DO NOT include ANY titles or slide numbers"

  # File naming patterns
  file_patterns:
    prompt_file: "prompt-{number:02d}.md"
    output_file: "slide-{number:02d}.jpg"

  # Console output settings
  console_output:
    success_message: "Saved: {filename} ({size_mb:.2f} MB)"
    skip_message: "SKIPPED (already exists)"
    generating_message: "Generating image (no titles/numbers)..."
    warning_validation: "NO titles/slide numbers instruction not found in prompt!"

---

# Prompt Configuration Guide

## Overview

This configuration file controls the **ImagePromptBuilder** system, which generates AI image prompts from structured slide data. By externalizing all hardcoded instructions, templates, and rules, you can easily customize prompt generation without modifying Python code.

## Quick Start

### Customizing for Your Brand

1. **Modify composition rules** for your preferred visual style
2. **Adjust generic instructions** to match your quality standards
3. **Add layout detection patterns** for your common slide types
4. **Customize metadata labels** for your output format

### Example: Add a New Layout Type

```yaml
layout_detection:
  quote_focused:
    patterns:
      - "quote"
      - "testimonial"
      - "customer story"
    description: "Large centered quote with attribution"
    layout_name: "quote_focused"
```

## Resolution Strategy

### When to Use Each Resolution

**High (3200x1900, 16:9):**
- Final presentations for large screens
- Print materials
- High-stakes client presentations
- Cost: ~$0.05 per image (4K generation)

**Medium (1940x940, 16:9):**
- Web presentations
- Draft/review versions
- Internal meetings
- Cost: ~$0.02 per image

**Small (1240x1000, 5:4):**
- Background images for text overlay
- PowerPoint slides with programmatic text
- Situations where you'll add titles separately
- Special: NO embedded titles or slide numbers
- Cost: ~$0.01 per image

### Why Small Resolution Has No Titles

The `small` resolution is specifically designed for PowerPoint templates where text is added programmatically. This avoids:
- Duplicate titles (one from AI, one from PowerPoint)
- Misalignment between AI-generated and template text
- Inflexible text positioning

## Prompt Engineering Tips

### Writing Effective Composition Instructions

**Good Instructions:**
- Clear, specific, actionable
- Use imperative mood ("Fill entire canvas", "Reserve top 15%")
- Include visual measurements when helpful
- Emphasize critical constraints with "CRITICAL:" prefix

**Poor Instructions:**
- Vague ("Make it look good")
- Contradictory ("Center the image" + "Fill entire canvas")
- Overly detailed (AI needs creative freedom)

### Layout Detection Patterns

**Regex Patterns:**
- Use `.*` for fuzzy matching: `"before.*after"` matches "before and after"
- Order matters: First match wins
- Test patterns against your actual slide content

**Pattern Examples:**
```yaml
# Matches: "comparison chart", "side-by-side comparison", "compare"
patterns:
  - "compar"  # Catches comparison, compare, comparative
  - "side-by-side"
  - "versus"
```

## Customization Examples

### Example 1: More Aggressive "No Text" Rule

If AI keeps adding text despite instructions:

```yaml
composition_rules:
  small:
    instructions:
      - "ABSOLUTELY NO TEXT OF ANY KIND"
      - "NO titles, NO labels, NO slide numbers, NO captions"
      - "Pure visual content only"
      - "Diagram callouts and legends are FORBIDDEN"
```

### Example 2: Cinematic Style Prompts

Add more creative direction:

```yaml
generic_instructions:
  - "No verbatim bullet points from the slide content"
  - "Use diagrams, icons, visual metaphors instead of text"
  - "Professional presentation quality"
  - "Cinematic composition with dramatic lighting"
  - "Bold, confident visual statements"
  - "Apple-keynote level visual polish"
```

### Example 3: Industry-Specific Layouts

Add patterns for your domain:

```yaml
layout_detection:
  medical_diagram:
    patterns:
      - "anatomy"
      - "medical"
      - "physiological"
    description: "Medical/anatomical diagram with labels"
    layout_name: "medical_diagram"

  financial_chart:
    patterns:
      - "revenue"
      - "profit"
      - "financial performance"
    description: "Financial data visualization"
    layout_name: "financial_chart"
```

## Troubleshooting

### Issue: AI Ignores "No Titles" Instruction

**Symptoms:** Small resolution images still have titles

**Solutions:**
1. Make instruction more emphatic (use "CRITICAL:", "ABSOLUTELY", "FORBIDDEN")
2. Add negative examples: "No 'Slide X', no titles like '{title}'"
3. Increase repetition: State the rule 3+ times in different sections
4. Try different phrasing: "Text-free background image for overlay"

### Issue: Wrong Layout Detected

**Symptoms:** Slide content matches multiple patterns

**Solutions:**
1. Reorder patterns (first match wins)
2. Make patterns more specific
3. Add exclusion patterns
4. Review your slide content for keyword consistency

### Issue: Inconsistent Visual Quality

**Symptoms:** Some images look great, others look amateurish

**Solutions:**
1. Add more specific quality instructions
2. Reference style guides more explicitly
3. Use comparative language: "Similar to Apple keynote quality"
4. Add negative constraints: "Avoid clipart, avoid stock photo look"

### Issue: Prompts Too Long/Too Short

**Symptoms:** API errors or insufficient context

**Solutions:**
1. Adjust `max_elements_shown` in visual_hierarchy
2. Modify `max_concepts` in content_parsing
3. Simplify composition instructions
4. Disable optional prompt sections

## Advanced Configuration

### Creating Brand-Specific Configs

You can maintain multiple config files for different brands:

```bash
prompt_config_cfa.md      # Chick-fil-A style
prompt_config_acme.md     # Acme Corp style
prompt_config_minimal.md  # Minimal/clean style
```

Then specify which config to use:

```python
builder = ImagePromptBuilder(
    style_path="cfa_style.json",
    config_path="prompt_config_cfa.md",
    resolution='small'
)
```

### Template Variables Reference

Available variables in prompt templates:

- `{number}` - Slide number
- `{title}` - Slide title
- `{visual_concept}` - Extracted visual concept
- `{primary_element}` - First/primary visual element
- `{width}` - Image width in pixels
- `{height}` - Image height in pixels
- `{aspect_ratio}` - Aspect ratio string (e.g., "16:9")
- `{style_path}` - Path to style configuration file
- `{title_treatment}` - Title rendering style (e.g., "prominent_header")

### Validation Rules

The system validates your config and provides helpful errors:

- Required sections: `resolutions`, `composition_rules`, `prompt_template`
- Resolution names must match keys in `composition_rules`
- Layout pattern regexes must be valid
- Element extraction markers must be non-empty

## Version History

- **v1.0** (Initial): All hardcoded values extracted to config
- **v1.1** (Planned): Support for custom sections, conditional logic

## Support

For issues or questions:
- Review this documentation thoroughly
- Check the troubleshooting section above
- Examine example configs in `prompt_config_examples/`
- Test changes with `--dry-run` flag first

## License

Same license as parent project (slide-generator).
