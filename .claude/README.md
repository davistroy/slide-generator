# Claude Code Skills for Slide Generator

This directory contains custom Claude Code skills for testing and working with the presentation generator.

## Available Skills

### `/test-pres-gen` - Comprehensive Presentation Testing

**Purpose:** Perform complete end-to-end testing of the presentation generator skill with detailed inspection and reporting.

**What it does:**
1. ✅ Parse test presentation.md file
2. ✅ Generate slide images (if GOOGLE_API_KEY available)
3. ✅ Generate CFA template presentation
4. ✅ Generate Stratfield template presentation
5. ✅ Deep inspection of both presentations
6. ✅ Compare results to expected content
7. ✅ Create detailed test report
8. ✅ Generate fix plan for any issues found

**Usage:**
```
/test-pres-gen
```

**Requirements:**
- Python dependencies installed (python-pptx, Pillow, lxml, google-genai)
- Optional: GOOGLE_API_KEY environment variable for image generation

**Output:**
- `tests/artifacts/comprehensive-test-cfa.pptx` - CFA template test
- `tests/artifacts/comprehensive-test-stratfield.pptx` - Stratfield template test
- `tests/artifacts/images/` - Generated slide images (if applicable)
- `tests/COMPREHENSIVE_TEST_REPORT.md` - Detailed test results
- `tests/FIX_PLAN.md` - Issue fix plan (if issues found)

**Testing Coverage:**
- Parser functionality
- Image generation
- Both templates (CFA and Stratfield)
- All content types (bullets, numbered lists, tables, code blocks, text)
- Markdown artifact detection
- Content completeness verification
- Slide-by-slide analysis

**Use Cases:**
- Verifying fixes after code changes
- Regression testing
- Quality assurance before releases
- Identifying new issues
- Performance benchmarking

---

## Adding New Skills

To add a new skill to this project:

1. Create a new `.md` file in `.claude/skills/`
2. Name it with your skill command (e.g., `my-skill.md` for `/my-skill`)
3. Structure it with:
   - `# Skill Name` (heading)
   - `## Description` (what it does)
   - `## Instructions` (detailed steps for Claude to follow)

4. Follow the pattern in `test-pres-gen.md` for reference

---

**Project:** Slide Generator v1.1.0
**Last Updated:** January 3, 2026
