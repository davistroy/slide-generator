# Distribution Files

This folder contains packaged distribution files for the Presentation Generator project.

## Files

### `presentation-skill-v1.1.0.zip` (722 KB) - **RECOMMENDED**
**Version:** 1.1.0 (Enhanced Release)
**Date:** January 3, 2026
**Status:** Production Ready ✅

Complete presentation generator skill with all fixes and enhancements:
- Full markdown parsing (tables, numbered lists, code blocks, bullets)
- Clean markdown formatting (no `**` artifacts)
- Cross-platform compatible (Windows, Mac, Linux)
- Both CFA and Stratfield templates included
- Interactive and CLI modes
- Image generation support (Google Gemini API)

**What's New in v1.1.0:**
- ✅ Fixed title/subtitle markdown artifacts
- ✅ Added table parsing support
- ✅ Added numbered list support
- ✅ Added code block detection
- ✅ Added plain text support
- ✅ Fixed Windows Unicode errors
- ✅ Enhanced content extraction
- ✅ 100% functional (was ~20%)

**Installation:**
```bash
unzip presentation-skill-v1.1.0.zip
cd presentation-skill
pip install python-pptx Pillow lxml google-genai
```

**Usage:**
```bash
# Interactive mode
python generate_presentation.py

# CLI mode
python generate_presentation.py presentation.md --template cfa --skip-images
```

---

### `cfa-ppt-v1.0.zip` (31 KB)
**Template:** Chick-fil-A Branded
**Version:** 1.0.0
**Status:** Reference Only

Original CFA template package. This is included for reference but is superseded by the templates in `presentation-skill-v1.1.0.zip`.

**Note:** Use the CFA template through the main presentation-skill package instead.

---

### `stratfield-ppt-v1.0.zip` (614 KB)
**Template:** Stratfield Consulting Branded
**Version:** 1.0.0
**Status:** Reference Only

Original Stratfield template package. This is included for reference but is superseded by the templates in `presentation-skill-v1.1.0.zip`.

**Note:** Use the Stratfield template through the main presentation-skill package instead.

---

## Quick Start

**For new users:**
1. Download `presentation-skill-v1.1.0.zip`
2. Extract to your desired location
3. Install dependencies: `pip install python-pptx Pillow lxml google-genai`
4. Run: `python generate_presentation.py`

**For existing users upgrading from v1.0.0:**
- All markdown files are fully compatible
- No breaking changes - everything works as before
- New features are automatically available

---

## Version History

**v1.1.0 (2026-01-03)** - Enhanced Release ✅
- Complete parser rewrite
- Table support
- Numbered lists
- Code blocks
- Clean markdown
- Windows compatible
- 100% functional

**v1.0.0 (Initial)** - Original Release
- Basic bullet parsing
- Simple slides
- ~20% functional
- Unicode issues on Windows

---

## Documentation

Full documentation is available in the parent `docs/` folder:
- `CHANGELOG.md` - Complete change history
- `FIXES_SUMMARY.md` - Quick reference
- `REGENERATE_SKILLS.md` - Package build guide

---

## Support

For issues, questions, or contributions, see the main repository README.

**Repository:** slide-generator
**License:** See LICENSE file
**Maintainer:** AI Practitioner Training Program
