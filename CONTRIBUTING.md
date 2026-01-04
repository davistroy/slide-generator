# Contributing to Slide Generator

Thank you for your interest in contributing to the Slide Generator project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project follows standard open source community guidelines:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Accept feedback gracefully
- Put the project's interests first

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Google Gemini API key (for testing image generation)
- Windows OS (for validation features)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/slide-generator.git
   cd slide-generator
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/slide-generator.git
   ```

### Keep Your Fork Updated

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

## Development Environment

### Initial Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install development dependencies:**
   ```bash
   # Core dependencies
   pip install python-dotenv google-genai pillow python-frontmatter
   pip install python-pptx lxml

   # Development tools (recommended)
   pip install black ruff mypy pytest pip-audit
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Google API key
   ```

4. **Verify setup:**
   ```bash
   # Test parser
   python presentation-skill/lib/parser.py tests/testfiles/presentation.md

   # Run basic generation test
   python presentation-skill/generate_presentation.py tests/testfiles/presentation.md \
     --template cfa --skip-images --output test-output.pptx
   ```

### Project Structure

```
slide-generator/
├── presentation-skill/     # Main source code
│   ├── lib/                # Core libraries
│   │   ├── parser.py       # Markdown parsing
│   │   ├── assembler.py    # Presentation assembly
│   │   ├── type_classifier.py  # Slide classification
│   │   └── ...
│   ├── templates/          # Brand templates
│   │   ├── cfa/            # CFA template
│   │   └── stratfield/     # Stratfield template
│   └── generate_presentation.py  # CLI entry point
├── templates/              # Style configs and examples
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with these specifics:

#### Code Formatting

```python
# Use Black for automatic formatting (recommended)
black presentation-skill/lib/*.py

# Line length: 100 characters (Black default: 88, we're flexible)
# Indentation: 4 spaces
# Quotes: Double quotes for strings, single quotes for dict keys when reasonable
```

#### Naming Conventions

```python
# Classes: PascalCase
class SlideGenerator:
    pass

# Functions and methods: snake_case
def parse_presentation(md_path: str) -> List[Slide]:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT_MS = 300000

# Private methods: _leading_underscore
def _parse_slide_section(self, content: str) -> dict:
    pass

# Module-level private: _leading_underscore
_DEFAULT_CONFIG = {}
```

#### Type Hints

Always use type hints for public functions and methods:

```python
from typing import Optional, List, Dict, Tuple
from pathlib import Path

def generate_slides(
    markdown_path: Path,
    template_id: str,
    skip_images: bool = False
) -> Optional[Path]:
    """Generate presentation from markdown.

    Args:
        markdown_path: Path to markdown file
        template_id: Template identifier (e.g., 'cfa', 'stratfield')
        skip_images: Skip image generation if True

    Returns:
        Path to generated PPTX file, or None if generation failed

    Raises:
        FileNotFoundError: If markdown file doesn't exist
        ValueError: If template_id is unknown
    """
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int, flag: bool = True) -> Dict[str, Any]:
    """Brief one-line description.

    More detailed explanation if needed. Can span multiple paragraphs.
    Explain what the function does, not how it does it (code shows that).

    Args:
        param1: Description of param1
        param2: Description of param2
        flag: Description of flag (default: True)

    Returns:
        Dictionary containing:
            - 'key1': Description of key1
            - 'key2': Description of key2

    Raises:
        ValueError: When param2 is negative
        KeyError: When required config key is missing

    Example:
        >>> result = complex_function("test", 42, flag=False)
        >>> print(result['key1'])
        'value'
    """
    pass
```

#### Import Organization

```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Third-party imports
from dotenv import load_dotenv
from google import genai
import frontmatter

# Local imports
from lib.parser import parse_presentation
from lib.assembler import assemble_presentation
```

### Error Handling

```python
# ✅ DO: Provide specific error messages
try:
    config = load_config(path)
except FileNotFoundError:
    raise FileNotFoundError(f"Config file not found: {path}")
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid JSON in config file {path}: {e}")

# ✅ DO: Use custom exceptions for domain-specific errors
class InvalidSlideFormatError(Exception):
    """Raised when slide format is invalid"""
    pass

# ❌ DON'T: Catch and ignore errors silently
try:
    process_slide(slide)
except:  # Too broad, hides bugs!
    pass
```

### Configuration Over Hardcoding

```python
# ❌ DON'T: Hardcode values
timeout = 300000
model_name = "gemini-3-pro-image-preview"

# ✅ DO: Use configuration
config = load_config('prompt_config.md')
timeout = config['api_settings']['api_timeout_ms']
model_name = config['image_generation']['model']
```

## Testing

### Running Tests

```bash
# Test parser
python presentation-skill/lib/parser.py tests/testfiles/presentation.md

# Test full generation workflow
python tests/test_generation.py

# Test specific template
python tests/test_branded_generation.py

# Run all test scripts
cd tests
python check_parser.py
python inspect_presentations.py
```

### Writing Tests

When adding new features, include tests:

```python
def test_parse_bullets():
    """Test bullet point parsing."""
    markdown = """
    ### SLIDE 1: Test

    **Content:**
    - Level 1
      - Level 2
        - Level 3
    """

    slides = parse_presentation_from_string(markdown)
    assert len(slides) == 1
    assert len(slides[0].content) == 1  # One bullet tree
    assert slides[0].content[0].startswith('- Level 1')
```

### Test Coverage

Aim for:
- All new functions have at least one test
- Edge cases are covered (empty input, malformed data, etc.)
- Error conditions are tested

## Documentation

### When to Update Documentation

Update documentation when:
- Adding new features
- Changing public APIs
- Modifying configuration options
- Fixing bugs that affect usage
- Improving error messages

### Documentation Files

- **README.md** - User-facing quick start and overview
- **CLAUDE.md** - Developer guide and architecture
- **CHANGELOG.md** - Version history and changes
- **SKILL.md** - Skill-specific documentation (in presentation-skill/)
- **API docstrings** - Inline code documentation

### Changelog Format

```markdown
### v1.3.0 (YYYY-MM-DD) - Feature Name

**Added:**
- New feature description
- Another new feature

**Changed:**
- Modified behavior description

**Fixed:**
- Bug fix description

**Deprecated:**
- Feature marked for removal

**Removed:**
- Removed feature description

**Security:**
- Security improvement description
```

## Pull Request Process

### Before Submitting

1. **Code quality:**
   - [ ] Code follows style guidelines
   - [ ] All functions have docstrings
   - [ ] Type hints added for public functions
   - [ ] No hardcoded values (use configuration)

2. **Testing:**
   - [ ] Existing tests still pass
   - [ ] New tests added for new features
   - [ ] Manual testing completed

3. **Documentation:**
   - [ ] README.md updated if needed
   - [ ] CHANGELOG.md entry added
   - [ ] Docstrings written for new functions
   - [ ] Comments added for complex logic

4. **Security:**
   - [ ] No API keys or secrets in code
   - [ ] `.env` not committed
   - [ ] Input validation added
   - [ ] Error messages don't leak sensitive data

5. **Code formatting:**
   ```bash
   # Run Black formatter
   black presentation-skill/

   # Run Ruff linter
   ruff check presentation-skill/

   # Run mypy type checker (optional but recommended)
   mypy presentation-skill/lib/ --ignore-missing-imports
   ```

### Creating a Pull Request

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, focused commits
   - Use descriptive commit messages
   - Keep commits atomic (one logical change per commit)

3. **Commit message format:**
   ```
   Short summary (50 chars or less)

   More detailed explanation if needed. Wrap at 72 characters.
   Explain what and why, not how (code shows how).

   - Bullet points are okay
   - Use present tense: "Add feature" not "Added feature"
   - Reference issues: "Fixes #123"
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open pull request:**
   - Provide clear description of changes
   - Link to related issues
   - Include screenshots for UI changes
   - List any breaking changes

### Pull Request Review

Your PR will be reviewed for:
- Code quality and style
- Test coverage
- Documentation completeness
- Security implications
- Performance impact
- Backward compatibility

### After Approval

Once approved and merged:
- Delete your feature branch (locally and on GitHub)
- Update your local main branch
- Close related issues if applicable

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Checklist

1. Update version numbers in:
   - README.md
   - CLAUDE.md
   - presentation-skill/SKILL.md
   - CLI help text

2. Update CHANGELOG.md with release notes

3. Create distribution package:
   ```bash
   # See docs/REGENERATE_SKILLS.md for full instructions
   cd presentation-skill
   zip -r ../dist/presentation-skill-vX.Y.Z.zip . -x "*.pyc" -x "__pycache__/*"
   ```

4. Test distribution package on clean environment

5. Create git tag:
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin vX.Y.Z
   ```

6. Create GitHub release with:
   - Release notes from CHANGELOG.md
   - Distribution package attached
   - Migration guide for breaking changes

## Getting Help

- **Documentation:** Check README.md and CLAUDE.md first
- **Issues:** Search existing issues on GitHub
- **Questions:** Open a GitHub Discussion
- **Bugs:** File a detailed bug report with reproduction steps

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- Git history with proper attribution

Thank you for contributing! 🎉

---

**Last Updated:** January 3, 2026
**Version:** 1.0
