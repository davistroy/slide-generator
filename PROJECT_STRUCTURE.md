# Project Structure

```
slide-generator/
├── .git/                           # Git repository
├── .gitignore                      # Git ignore rules
├── README.md                       # Main project documentation
├── CLAUDE.md                       # Claude Code instructions
├── PROJECT_STRUCTURE.md            # This file
│
├── presentation-skill/             # SOURCE CODE (v1.1.0)
│   ├── SKILL.md                    # Skill documentation
│   ├── CLI_USAGE.md                # Command-line usage guide
│   ├── generate_presentation.py    # Main entry point
│   ├── lib/                        # Core libraries
│   │   ├── __init__.py
│   │   ├── parser.py               # Enhanced markdown parser
│   │   ├── assembler.py            # Presentation builder
│   │   └── image_generator.py      # AI image generation
│   └── templates/                  # Presentation templates
│       ├── __init__.py
│       ├── cfa.py                  # CFA branded template
│       └── stratfield.py           # Stratfield branded template
│
├── docs/                           # DOCUMENTATION
│   ├── CHANGELOG.md                # Complete change history
│   ├── FIXES_SUMMARY.md            # Quick reference
│   ├── REGENERATE_SKILLS.md        # Build instructions
│   ├── INSPECTION_REPORT.md        # Issue analysis
│   ├── TEST_RESULTS.md             # Test results
│   └── PLAN.md                     # Development plan
│
├── dist/                           # DISTRIBUTION FILES
│   ├── README.md                   # Distribution guide
│   ├── presentation-skill-v1.1.0.zip    # Main package (RECOMMENDED)
│   ├── cfa-ppt-v1.0.zip                 # CFA template (reference)
│   └── stratfield-ppt-v1.0.zip          # Stratfield template (reference)
│
├── templates/                      # TEMPLATE EXAMPLES
│   ├── pres-template.md            # Presentation markdown template
│   └── example-presentation.md     # Example presentation (20 slides)
│
├── tests/                          # TEST FILES
│   ├── check_parser.py             # Parser test script
│   ├── detailed_inspect.py         # Detailed inspection
│   ├── inspect_fixed.py            # Fixed version inspector
│   ├── inspect_presentations.py    # General inspector
│   ├── artifacts/                  # Generated test files
│   │   ├── final-test-cfa.pptx
│   │   └── final-test-stratfield.pptx
│   └── testfiles/                  # Test data
│       └── presentation.md         # 20-slide test file
│
└── scripts/                        # UTILITY SCRIPTS
    └── generate_images_for_slides.py   # Standalone image generator
```

## Key Directories

### `presentation-skill/` (Source Code)
The main source code for the presentation generator. This is the active development directory.

**Core Files:**
- `generate_presentation.py` - Main CLI tool
- `lib/parser.py` - Markdown parser (v1.1.0 - enhanced)
- `lib/assembler.py` - Presentation builder
- `lib/image_generator.py` - AI image generation

**Templates:**
- `templates/cfa.py` - CFA branded PowerPoint template
- `templates/stratfield.py` - Stratfield consulting template

### `dist/` (Distribution)
Packaged ZIP files ready for distribution.

**Main Package:**
- `presentation-skill-v1.1.0.zip` - Complete package (722 KB)

**Reference Packages:**
- `cfa-ppt-v1.0.zip` - Original CFA template
- `stratfield-ppt-v1.0.zip` - Original Stratfield template

### `docs/` (Documentation)
All project documentation and technical details.

**Key Documents:**
- `CHANGELOG.md` - Complete version history
- `FIXES_SUMMARY.md` - Quick reference for fixes
- `INSPECTION_REPORT.md` - Technical analysis

### `tests/` (Testing)
Test scripts and test data.

**Test Scripts:**
- `check_parser.py` - Parser validation
- `inspect_*.py` - Various inspection tools

**Test Data:**
- `testfiles/presentation.md` - 20-slide test file
- `artifacts/` - Generated test presentations

### `templates/` (Examples)
Template and example files for creating presentations.

**Files:**
- `pres-template.md` - Slide definition template
- `example-presentation.md` - Complete example (20 slides)

### `scripts/` (Utilities)
Standalone utility scripts.

**Tools:**
- `generate_images_for_slides.py` - Batch image generation

## Version Information

**Current Version:** 1.1.0 (Enhanced Release)
**Release Date:** January 3, 2026
**Status:** Production Ready ✅

## Quick Navigation

| Task | Location |
|------|----------|
| Install skill | `dist/presentation-skill-v1.1.0.zip` |
| View source | `presentation-skill/` |
| Read docs | `docs/CHANGELOG.md` |
| Run tests | `tests/` |
| See examples | `templates/example-presentation.md` |
| Generate images | `scripts/generate_images_for_slides.py` |

## Development

**To modify the skill:**
1. Edit files in `presentation-skill/`
2. Test with `tests/testfiles/presentation.md`
3. Run test scripts in `tests/`
4. Rebuild distribution: `docs/REGENERATE_SKILLS.md`

**To add a new template:**
1. Create template in `presentation-skill/templates/`
2. Follow existing template patterns (cfa.py, stratfield.py)
3. Update `presentation-skill/templates/__init__.py`

## File Organization Rules

**Source Code:**
- All active code in `presentation-skill/`
- No temporary files in source
- Well-documented and tested

**Documentation:**
- Technical docs in `docs/`
- User docs in root README.md
- Template examples in `templates/`

**Distribution:**
- Packaged files in `dist/`
- README.md in dist/ explains packages
- Version numbers in filenames

**Testing:**
- Test scripts in `tests/`
- Test data in `tests/testfiles/`
- Generated artifacts in `tests/artifacts/`

---

**Last Updated:** January 3, 2026
**Project:** AI Practitioner Training - Presentation Generator
**Version:** 1.1.0
