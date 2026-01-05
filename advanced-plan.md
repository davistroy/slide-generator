# Slide-Generator: Ultra-Detailed Implementation Plan

**Project:** davistroy/slide-generator  
**Plan Version:** 2.0 (Granular Edition)  
**Created:** January 4, 2026  
**Total Estimated Duration:** 45-65 hours across 6 weeks

-----

## How to Use This Plan

Each task includes:

- ⏱️ **Time Estimate** - Expected duration
- 📋 **Prerequisites** - What must be done first
- 📝 **Steps** - Numbered actions to take
- ✅ **Verification** - Specific commands with expected output
- 🔄 **Rollback** - How to undo if something breaks
- 📁 **Files Changed** - What files are created/modified

-----

## Master Dependency Graph

```
Phase 1 (Foundation)
    ↓
Phase 2 (CI/CD) ←──────────────────┐
    ↓                              │
Phase 3 (Tests) ───────────────────┤
    ↓                              │
Phase 4 (Type Safety) ─────────────┤
    ↓                              │
Phase 5 (Security) ────────────────┘
    ↓
Phase 6 (Logging)
    ↓
Phase 7 (Async)
    ↓
Phase 8 (Consolidation)
    ↓
Phase 9 (Documentation)
```

-----

# PHASE 1: Foundation & Quick Wins

**Total Duration:** 2.5-3.5 hours  
**Goal:** Establish project hygiene baseline  
**Branch:** `feature/phase-1-foundation`

-----

## Task 1.1: Create Git Branch

⏱️ **Time:** 2 minutes  
📋 **Prerequisites:** Git installed, repo cloned

### Steps:

```bash
# Step 1: Ensure you're on main and up to date
git checkout main
git pull origin main

# Step 2: Create develop branch if it doesn't exist
git checkout -b develop
git push -u origin develop

# Step 3: Create feature branch
git checkout -b feature/phase-1-foundation
```

### ✅ Verification:

```bash
git branch --show-current
```

**Expected output:** `feature/phase-1-foundation`

```bash
git status
```

**Expected output:** `nothing to commit, working tree clean`

### 🔄 Rollback:

```bash
git checkout main
git branch -D feature/phase-1-foundation
```

-----

## Task 1.2: Add LICENSE File

⏱️ **Time:** 5 minutes  
📋 **Prerequisites:** Task 1.1 complete  
📁 **Files Changed:** `LICENSE` (created)

### Steps:

**Step 1:** Create the LICENSE file:

```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 Troy Davis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

**Step 2:** Verify file contents:

```bash
head -3 LICENSE
```

**Expected output:**

```
MIT License

Copyright (c) 2026 Troy Davis
```

**Step 3:** Commit the change:

```bash
git add LICENSE
git commit -m "chore: add MIT LICENSE file"
```

### ✅ Verification:

```bash
# Check file exists and has correct line count
wc -l LICENSE
```

**Expected output:** `21 LICENSE`

```bash
# Check git status
git log --oneline -1
```

**Expected output:** Contains “add MIT LICENSE file”

### 🔄 Rollback:

```bash
git reset --hard HEAD~1
```

-----

## Task 1.3: Update README License Section

⏱️ **Time:** 5 minutes  
📋 **Prerequisites:** Task 1.2 complete  
📁 **Files Changed:** `README.md` (modified)

### Steps:

**Step 1:** Check if license section exists:

```bash
grep -n "License" README.md | head -5
```

**Step 2:** If “[Specify your license here]” exists, replace it:

```bash
# On macOS:
sed -i '' 's/\[Specify your license here\]/This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details./g' README.md

# On Linux:
sed -i 's/\[Specify your license here\]/This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details./g' README.md
```

**Step 3:** Verify the change:

```bash
grep -A1 "## License" README.md
```

**Expected output:**

```
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

**Step 4:** Commit:

```bash
git add README.md
git commit -m "docs: update README with license reference"
```

### ✅ Verification:

```bash
grep "MIT License" README.md
```

**Expected output:** Line containing “MIT License”

### 🔄 Rollback:

```bash
git checkout HEAD~1 -- README.md
git commit -m "revert: README license change"
```

-----

## Task 1.4: Pin Dependency Versions

⏱️ **Time:** 25 minutes  
📋 **Prerequisites:** Python 3.10+ installed, Task 1.1 complete  
📁 **Files Changed:** `requirements.txt`, `requirements-dev.txt`, `requirements-test.txt`

### Steps:

**Step 1:** Create clean virtual environment:

```bash
# Remove existing venv if present
rm -rf venv

# Create fresh venv
python3 -m venv venv

# Activate it
source venv/bin/activate  # Linux/macOS
# OR: venv\Scripts\activate  # Windows
```

**Step 2:** Install current dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Step 3:** Capture exact versions:

```bash
pip freeze > requirements.lock
cat requirements.lock
```

**Step 4:** Create new pinned `requirements.txt`:

```bash
cat > requirements.txt << 'EOF'
# requirements.txt - Production dependencies
# Last updated: 2026-01-04
# Python version: 3.10+
#
# To update: pip install -r requirements.txt && pip freeze > requirements.lock

# Anthropic Claude API
anthropic>=0.39.0,<1.0.0

# Google Gemini API
google-generativeai>=0.8.0,<1.0.0

# PowerPoint generation
python-pptx>=0.6.23,<1.0.0

# Environment and configuration
python-dotenv>=1.0.0,<2.0.0
python-frontmatter>=1.1.0,<2.0.0

# Text analysis
textstat>=0.7.3,<1.0.0

# Image processing
Pillow>=10.0.0,<11.0.0

# HTTP requests
requests>=2.31.0,<3.0.0
httpx>=0.27.0,<1.0.0
EOF
```

**Step 5:** Create `requirements-dev.txt`:

```bash
cat > requirements-dev.txt << 'EOF'
# requirements-dev.txt - Development dependencies
# Includes all production dependencies
-r requirements.txt

# Code formatting and linting
ruff>=0.1.11,<1.0.0

# Type checking
mypy>=1.8.0,<2.0.0
types-requests>=2.31.0
types-Pillow>=10.0.0

# Pre-commit hooks
pre-commit>=3.6.0,<4.0.0

# Documentation
pdoc>=14.0.0,<15.0.0
EOF
```

**Step 6:** Create `requirements-test.txt`:

```bash
cat > requirements-test.txt << 'EOF'
# requirements-test.txt - Testing dependencies
# Includes all dev dependencies
-r requirements-dev.txt

# Testing framework
pytest>=7.4.0,<8.0.0
pytest-cov>=4.1.0,<5.0.0
pytest-asyncio>=0.23.0,<1.0.0
pytest-mock>=3.12.0,<4.0.0
pytest-xdist>=3.5.0,<4.0.0

# Test utilities
responses>=0.24.0,<1.0.0
freezegun>=1.4.0,<2.0.0
faker>=22.0.0,<30.0.0

# Coverage
coverage[toml]>=7.4.0,<8.0.0
EOF
```

**Step 7:** Verify installations work:

```bash
# Fresh install test
pip uninstall -y -r requirements.txt 2>/dev/null || true
pip install -r requirements-test.txt
```

**Step 8:** Commit changes:

```bash
git add requirements.txt requirements-dev.txt requirements-test.txt
git commit -m "build: pin all dependency versions with ranges"
```

### ✅ Verification:

```bash
# Check no conflicts
pip check
```

**Expected output:** `No broken requirements found.`

```bash
# Verify key packages installed
python -c "import anthropic; print(f'anthropic: {anthropic.__version__}')"
python -c "import pptx; print('python-pptx: OK')"
python -c "import pytest; print(f'pytest: {pytest.__version__}')"
```

**Expected output:** Version numbers for each package

```bash
# Count dependencies in each file
wc -l requirements*.txt
```

**Expected output:** Reasonable line counts (15-25 per file)

### 🔄 Rollback:

```bash
git checkout HEAD~1 -- requirements.txt requirements-dev.txt requirements-test.txt
pip install -r requirements.txt
```

-----

## Task 1.5: Create CHANGELOG.md

⏱️ **Time:** 15 minutes  
📋 **Prerequisites:** Task 1.1 complete  
📁 **Files Changed:** `CHANGELOG.md` (created)

### Steps:

**Step 1:** Create CHANGELOG.md:

```bash
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Dependency version pinning with ranges
- MIT License file
- This changelog

### Changed
- Updated README with license reference

## [2.0.0] - 2026-01-04

### Added
- **Plugin Architecture**: Modular skill-based system with registry and orchestration
- **Research Skills**: Claude Agent SDK integration for autonomous web research
- **Content Development**: AI-assisted drafting, quality analysis, and optimization
- **Graphics Validation**: Rule-based and AI validation of image descriptions
- **CLI Interface**: 11 commands for full workflow control
- **Checkpoint System**: Resume workflows from any step
- **Quality Metrics**: 5-dimension scoring (readability, tone, structure, redundancy, citations)
- 74 unit tests with 92-96% coverage

### Changed
- Migrated from monolithic architecture to plugin-based system
- Updated to Claude Sonnet 4.5 for all text generation
- Switched image generation to Gemini Pro (gemini-3-pro-image-preview)

### Technical Details
- 30+ files, 8,000+ lines of infrastructure code
- 10 files, 3,500+ lines of research code
- 6 files, 2,500+ lines of content generation code

## [1.2.0] - 2026-01-03

### Added
- Intelligent slide type classification using AI + rules hybrid
- Visual validation for generated images (experimental)
- Iterative image refinement workflow

## [1.1.0] - 2024-12

### Added
- Enhanced markdown parsing with frontmatter support
- Multi-resolution image generation (low, medium, high)
- Improved error handling for API failures

## [1.0.0] - 2024-12

### Added
- Initial release
- Basic presentation generation from markdown
- CFA and Stratfield branded templates
- Gemini-powered image generation
- python-pptx integration for PowerPoint assembly

---

[Unreleased]: https://github.com/davistroy/slide-generator/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/davistroy/slide-generator/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/davistroy/slide-generator/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/davistroy/slide-generator/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/davistroy/slide-generator/releases/tag/v1.0.0
EOF
```

**Step 2:** Verify format:

```bash
head -20 CHANGELOG.md
```

**Step 3:** Commit:

```bash
git add CHANGELOG.md
git commit -m "docs: add CHANGELOG.md following Keep a Changelog format"
```

### ✅ Verification:

```bash
# Check file exists and has content
test -f CHANGELOG.md && echo "✓ CHANGELOG.md exists"
grep -c "##" CHANGELOG.md
```

**Expected output:**

```
✓ CHANGELOG.md exists
6
```

(6 or more ## headers)

```bash
# Validate markdown links
grep -E "^\[.+\]: https" CHANGELOG.md | wc -l
```

**Expected output:** `5` (or number of version links)

### 🔄 Rollback:

```bash
rm CHANGELOG.md
git checkout HEAD~1
```

-----

## Task 1.6: Create .editorconfig

⏱️ **Time:** 5 minutes  
📋 **Prerequisites:** Task 1.1 complete  
📁 **Files Changed:** `.editorconfig` (created)

### Steps:

**Step 1:** Create .editorconfig:

```bash
cat > .editorconfig << 'EOF'
# EditorConfig helps maintain consistent coding styles
# https://editorconfig.org

root = true

# Default settings for all files
[*]
indent_style = space
indent_size = 4
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true
max_line_length = 88

# Python files
[*.py]
indent_size = 4

# YAML files (GitHub Actions, configs)
[*.{yml,yaml}]
indent_size = 2

# JSON and TOML
[*.{json,toml}]
indent_size = 2

# Markdown - preserve trailing whitespace for line breaks
[*.md]
trim_trailing_whitespace = false
max_line_length = 100

# Makefiles require tabs
[Makefile]
indent_style = tab

# Shell scripts
[*.sh]
indent_size = 2

# Git config files
[.git*]
indent_size = 2
EOF
```

**Step 2:** Commit:

```bash
git add .editorconfig
git commit -m "chore: add .editorconfig for consistent formatting"
```

### ✅ Verification:

```bash
cat .editorconfig | grep "root = true"
```

**Expected output:** `root = true`

```bash
wc -l .editorconfig
```

**Expected output:** Approximately `40 .editorconfig`

-----

## Task 1.7: Create Makefile

⏱️ **Time:** 20 minutes  
📋 **Prerequisites:** Task 1.4 complete (dependencies installed)  
📁 **Files Changed:** `Makefile` (created)

### Steps:

**Step 1:** Create Makefile:

```bash
cat > Makefile << 'MAKEFILE_EOF'
# Makefile for slide-generator
# Run 'make help' to see available commands

.PHONY: help install install-dev install-test lint format type-check \
        test test-unit test-integration test-cov clean security docs \
        run-research run-full check all

# Variables
PYTHON := python3
PIP := pip
PYTEST := pytest
RUFF := ruff
MYPY := mypy

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Default target
.DEFAULT_GOAL := help

#---------------------------------------------------------------------------
# Help
#---------------------------------------------------------------------------

help:  ## Show this help message
	@echo "$(BLUE)slide-generator$(RESET) - AI-Assisted Presentation Generator"
	@echo ""
	@echo "$(GREEN)Usage:$(RESET)"
	@echo "  make $(YELLOW)<target>$(RESET)"
	@echo ""
	@echo "$(GREEN)Targets:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(RESET) %s\n", $$1, $$2}'

#---------------------------------------------------------------------------
# Installation
#---------------------------------------------------------------------------

install:  ## Install production dependencies only
	@echo "$(BLUE)Installing production dependencies...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Production dependencies installed$(RESET)"

install-dev:  ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	@echo "$(BLUE)Setting up pre-commit hooks...$(RESET)"
	pre-commit install || echo "$(YELLOW)⚠ pre-commit not configured yet$(RESET)"
	@echo "$(GREEN)✓ Development environment ready$(RESET)"

install-test:  ## Install all dependencies including test
	@echo "$(BLUE)Installing all dependencies...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-test.txt
	@echo "$(GREEN)✓ Test environment ready$(RESET)"

#---------------------------------------------------------------------------
# Code Quality
#---------------------------------------------------------------------------

lint:  ## Run linters (ruff)
	@echo "$(BLUE)Running ruff linter...$(RESET)"
	$(RUFF) check .
	@echo "$(BLUE)Checking code formatting...$(RESET)"
	$(RUFF) format --check .
	@echo "$(GREEN)✓ Linting passed$(RESET)"

format:  ## Auto-format code
	@echo "$(BLUE)Formatting code with ruff...$(RESET)"
	$(RUFF) format .
	$(RUFF) check --fix .
	@echo "$(GREEN)✓ Code formatted$(RESET)"

type-check:  ## Run type checker (mypy)
	@echo "$(BLUE)Running mypy type checker...$(RESET)"
	$(MYPY) plugin/ --ignore-missing-imports --no-error-summary || true
	@echo "$(GREEN)✓ Type checking complete$(RESET)"

#---------------------------------------------------------------------------
# Testing
#---------------------------------------------------------------------------

test:  ## Run all tests (excluding API tests)
	@echo "$(BLUE)Running tests...$(RESET)"
	$(PYTEST) tests/ -v -m "not api"
	@echo "$(GREEN)✓ Tests passed$(RESET)"

test-unit:  ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(RESET)"
	$(PYTEST) tests/unit/ -v
	@echo "$(GREEN)✓ Unit tests passed$(RESET)"

test-integration:  ## Run integration tests (may need API keys)
	@echo "$(BLUE)Running integration tests...$(RESET)"
	$(PYTEST) tests/integration/ -v -m "not api"
	@echo "$(GREEN)✓ Integration tests passed$(RESET)"

test-cov:  ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(RESET)"
	$(PYTEST) tests/ -v \
		--cov=plugin \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-fail-under=80 \
		-m "not api"
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(RESET)"

test-fast:  ## Run tests in parallel (faster)
	@echo "$(BLUE)Running tests in parallel...$(RESET)"
	$(PYTEST) tests/ -v -n auto -m "not api and not slow"
	@echo "$(GREEN)✓ Fast tests passed$(RESET)"

#---------------------------------------------------------------------------
# Security
#---------------------------------------------------------------------------

security:  ## Run security scans
	@echo "$(BLUE)Running pip-audit...$(RESET)"
	pip-audit -r requirements.txt || echo "$(YELLOW)⚠ Some vulnerabilities found$(RESET)"
	@echo "$(BLUE)Running bandit...$(RESET)"
	bandit -r plugin/ -ll -q || echo "$(YELLOW)⚠ Some issues found$(RESET)"
	@echo "$(GREEN)✓ Security scan complete$(RESET)"

#---------------------------------------------------------------------------
# Documentation
#---------------------------------------------------------------------------

docs:  ## Generate API documentation
	@echo "$(BLUE)Generating documentation...$(RESET)"
	pdoc --html --output-dir docs/api plugin/ --force
	@echo "$(GREEN)✓ Documentation generated in docs/api/$(RESET)"

docs-serve:  ## Serve documentation locally
	@echo "$(BLUE)Starting documentation server...$(RESET)"
	pdoc --http : plugin/

#---------------------------------------------------------------------------
# Cleanup
#---------------------------------------------------------------------------

clean:  ## Remove build artifacts and caches
	@echo "$(BLUE)Cleaning up...$(RESET)"
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage coverage.xml
	rm -rf dist build *.egg-info
	rm -rf .eggs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage.*" -delete
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

clean-all: clean  ## Remove all generated files including venv
	rm -rf venv
	rm -rf node_modules
	@echo "$(GREEN)✓ Full cleanup complete$(RESET)"

#---------------------------------------------------------------------------
# Application Commands
#---------------------------------------------------------------------------

run-research:  ## Run research workflow example
	@echo "$(BLUE)Running research example...$(RESET)"
	$(PYTHON) -m plugin.cli research "Example Topic" --output output/research.json

run-full:  ## Run full workflow example
	@echo "$(BLUE)Running full workflow example...$(RESET)"
	$(PYTHON) -m plugin.cli full-workflow "Example Topic" --template cfa

#---------------------------------------------------------------------------
# CI/CD Helpers
#---------------------------------------------------------------------------

check: lint type-check test  ## Run all checks (lint, type-check, test)
	@echo "$(GREEN)✓ All checks passed$(RESET)"

all: clean install-test check  ## Full rebuild and check
	@echo "$(GREEN)✓ Full build complete$(RESET)"

ci: install-test lint test-cov  ## Run CI pipeline locally
	@echo "$(GREEN)✓ CI pipeline complete$(RESET)"

#---------------------------------------------------------------------------
# Git Helpers
#---------------------------------------------------------------------------

pre-commit:  ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update:  ## Update pre-commit hooks
	pre-commit autoupdate
MAKEFILE_EOF
```

**Step 2:** Test Makefile:

```bash
make help
```

**Step 3:** Commit:

```bash
git add Makefile
git commit -m "build: add Makefile with common development commands"
```

### ✅ Verification:

```bash
# Check help works
make help | head -10
```

**Expected output:** Colored help text with target descriptions

```bash
# Check specific targets exist
grep -c "^[a-z].*:.*##" Makefile
```

**Expected output:** `20` or more (number of documented targets)

```bash
# Test a simple target (if dependencies installed)
make clean
```

**Expected output:** “✓ Cleanup complete”

### 🔄 Rollback:

```bash
rm Makefile
git checkout HEAD~1
```

-----

## Task 1.8: Create pyproject.toml

⏱️ **Time:** 25 minutes  
📋 **Prerequisites:** Task 1.4 complete  
📁 **Files Changed:** `pyproject.toml` (created), `pytest.ini` (deleted)

### Steps:

**Step 1:** Create pyproject.toml:

```bash
cat > pyproject.toml << 'EOF'
# pyproject.toml - Project configuration
# https://packaging.python.org/en/latest/specifications/pyproject-toml/

[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

#-----------------------------------------------------------------------------
# Project Metadata
#-----------------------------------------------------------------------------

[project]
name = "slide-generator"
version = "2.0.0"
description = "AI-assisted presentation generator with plugin architecture"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Troy Davis"}
]
maintainers = [
    {name = "Troy Davis"}
]
keywords = [
    "presentation",
    "powerpoint",
    "pptx",
    "ai",
    "claude",
    "gemini",
    "automation",
    "slides",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Intended Audience :: End Users/Desktop",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business",
    "Topic :: Multimedia :: Graphics :: Presentation",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/davistroy/slide-generator"
Documentation = "https://github.com/davistroy/slide-generator#readme"
Repository = "https://github.com/davistroy/slide-generator.git"
Issues = "https://github.com/davistroy/slide-generator/issues"
Changelog = "https://github.com/davistroy/slide-generator/blob/main/CHANGELOG.md"

[project.scripts]
slide-generator = "plugin.cli:main"
sg = "plugin.cli:main"

[project.optional-dependencies]
dev = [
    "ruff>=0.1.11",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
    "pdoc>=14.0.0",
]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.5.0",
    "responses>=0.24.0",
    "freezegun>=1.4.0",
]
all = [
    "slide-generator[dev,test]",
]

#-----------------------------------------------------------------------------
# Setuptools Configuration
#-----------------------------------------------------------------------------

[tool.setuptools]
packages = ["plugin", "plugin.skills", "plugin.lib", "lib", "presentation_skill"]
include-package-data = true

[tool.setuptools.package-data]
"*" = ["*.md", "*.json", "*.yaml", "*.yml"]

#-----------------------------------------------------------------------------
# Ruff - Linting & Formatting
#-----------------------------------------------------------------------------

[tool.ruff]
target-version = "py310"
line-length = 88
fix = true
src = ["plugin", "lib", "presentation_skill", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented code)
    "PL",     # pylint
    "RUF",    # ruff-specific
]
ignore = [
    "E501",     # line too long (handled by formatter)
    "B008",     # function calls in argument defaults
    "PLR0913",  # too many arguments
    "PLR2004",  # magic value comparison
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ARG", "S101", "PLR2004"]
"__init__.py" = ["F401"]
"conftest.py" = ["ARG"]

[tool.ruff.lint.isort]
known-first-party = ["plugin", "presentation_skill", "lib"]
force-single-line = false
lines-after-imports = 2

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"

#-----------------------------------------------------------------------------
# MyPy - Type Checking
#-----------------------------------------------------------------------------

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true
show_column_numbers = true

# Start permissive, tighten over time
disallow_untyped_defs = false
check_untyped_defs = true
disallow_any_generics = false

# Ignore missing imports for third-party libs without stubs
ignore_missing_imports = true

exclude = [
    "tests/",
    "docs/",
    "build/",
    "dist/",
    "venv/",
]

# Per-module overrides for stricter checking
[[tool.mypy.overrides]]
module = "plugin.types"
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = "plugin.base_skill"
disallow_untyped_defs = true

#-----------------------------------------------------------------------------
# Pytest - Testing
#-----------------------------------------------------------------------------

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Default options
addopts = [
    "-ra",                    # Show summary of all test outcomes
    "-q",                     # Quiet mode
    "--strict-markers",       # Error on unknown markers
    "--strict-config",        # Error on config issues
    "-m", "not api",          # Skip API tests by default
]

# Custom markers
markers = [
    "unit: Unit tests (fast, isolated, no external deps)",
    "integration: Integration tests (may use mocked external services)",
    "api: Tests requiring real API keys (skipped by default)",
    "slow: Slow-running tests (> 5 seconds)",
    "smoke: Quick sanity check tests",
]

# Filter warnings
filterwarnings = [
    "ignore::DeprecationWarning",
    "ignore::PendingDeprecationWarning",
]

# Async mode
asyncio_mode = "auto"

# Logging
log_cli = false
log_cli_level = "INFO"

#-----------------------------------------------------------------------------
# Coverage - Test Coverage
#-----------------------------------------------------------------------------

[tool.coverage.run]
branch = true
source = ["plugin"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/.venv/*",
    "*/venv/*",
]
parallel = true

[tool.coverage.paths]
source = [
    "plugin/",
]

[tool.coverage.report]
exclude_lines = [
    # Standard exclusions
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    
    # Type checking exclusions
    "if TYPE_CHECKING:",
    "if typing.TYPE_CHECKING:",
    
    # Debug/logging exclusions
    "if self.debug:",
    "if settings.DEBUG",
    
    # Main guard
    'if __name__ == .__main__.:',
    
    # Abstract methods
    "@abstractmethod",
]
fail_under = 80
show_missing = true
skip_covered = false
precision = 2

[tool.coverage.html]
directory = "htmlcov"
title = "Slide Generator Coverage Report"

[tool.coverage.xml]
output = "coverage.xml"

#-----------------------------------------------------------------------------
# Bandit - Security
#-----------------------------------------------------------------------------

[tool.bandit]
exclude_dirs = ["tests", "docs", "scripts", "venv"]
skips = ["B101"]  # Skip assert warnings

#-----------------------------------------------------------------------------
# Black - Formatting (if used alongside ruff)
#-----------------------------------------------------------------------------

[tool.black]
line-length = 88
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
    \.eggs
    | \.git
    | \.mypy_cache
    | \.ruff_cache
    | \.venv
    | venv
    | build
    | dist
)/
'''
EOF
```

**Step 2:** Remove old pytest.ini if it exists:

```bash
rm -f pytest.ini
```

**Step 3:** Verify configuration works:

```bash
# Check TOML is valid
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('✓ Valid TOML')"
```

**Step 4:** Test editable install:

```bash
pip install -e .
```

**Step 5:** Commit:

```bash
git add pyproject.toml
git rm -f pytest.ini 2>/dev/null || true
git commit -m "build: add comprehensive pyproject.toml configuration"
```

### ✅ Verification:

```bash
# TOML validity
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK')"
```

**Expected output:** `OK`

```bash
# Editable install works
pip show slide-generator | grep -E "^(Name|Version|Location)"
```

**Expected output:**

```
Name: slide-generator
Version: 2.0.0
Location: /path/to/your/repo
```

```bash
# Pytest uses config
pytest --markers | grep -E "^@pytest.mark\.(unit|integration|api)"
```

**Expected output:** Three custom markers listed

### 🔄 Rollback:

```bash
pip uninstall slide-generator -y
git checkout HEAD~1 -- pyproject.toml
git checkout HEAD~1 -- pytest.ini 2>/dev/null || true
```

-----

## Task 1.9: Commit and Push Phase 1

⏱️ **Time:** 5 minutes  
📋 **Prerequisites:** All Phase 1 tasks complete

### Steps:

**Step 1:** Review all changes:

```bash
git status
git log --oneline -10
```

**Step 2:** Push feature branch:

```bash
git push -u origin feature/phase-1-foundation
```

**Step 3:** Create Pull Request (via GitHub UI or CLI):

```bash
# Using GitHub CLI (if installed)
gh pr create \
  --title "Phase 1: Foundation & Quick Wins" \
  --body "## Changes
- Added MIT LICENSE file
- Updated README with license reference
- Pinned all dependency versions
- Added CHANGELOG.md
- Added .editorconfig
- Added Makefile with common commands
- Added comprehensive pyproject.toml

## Verification
- [ ] All files present
- [ ] Dependencies install successfully
- [ ] Make commands work
- [ ] pyproject.toml is valid" \
  --base develop
```

### ✅ Verification:

```bash
# Verify branch is pushed
git log origin/feature/phase-1-foundation --oneline -1
```

```bash
# Verify all expected files exist
ls -la LICENSE CHANGELOG.md .editorconfig Makefile pyproject.toml
```

**Expected output:** All 5 files listed

-----

## Phase 1 Final Checklist

Before proceeding to Phase 2, verify:

- [ ] `LICENSE` file exists with MIT license
- [ ] `README.md` references the license
- [ ] `requirements.txt` has pinned versions
- [ ] `requirements-dev.txt` has pinned versions
- [ ] `requirements-test.txt` has pinned versions
- [ ] `CHANGELOG.md` exists with version history
- [ ] `.editorconfig` exists
- [ ] `Makefile` exists and `make help` works
- [ ] `pyproject.toml` exists and is valid
- [ ] `pip install -e .` succeeds
- [ ] Feature branch pushed to origin
- [ ] PR created targeting `develop`

**Run this verification script:**

```bash
#!/bin/bash
echo "=== Phase 1 Verification ==="

check() {
    if [ $? -eq 0 ]; then
        echo "✓ $1"
    else
        echo "✗ $1"
        FAILED=1
    fi
}

FAILED=0

test -f LICENSE; check "LICENSE exists"
test -f CHANGELOG.md; check "CHANGELOG.md exists"
test -f .editorconfig; check ".editorconfig exists"
test -f Makefile; check "Makefile exists"
test -f pyproject.toml; check "pyproject.toml exists"
grep -q "MIT" LICENSE; check "LICENSE contains MIT"
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" 2>/dev/null; check "pyproject.toml is valid TOML"
make help >/dev/null 2>&1; check "make help works"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo "=== All Phase 1 checks passed! ==="
else
    echo ""
    echo "=== Some checks failed ==="
    exit 1
fi
```

-----

# PHASE 2: CI/CD Implementation

**Total Duration:** 4-6 hours  
**Goal:** Automated quality gates on every PR  
**Branch:** `feature/phase-2-cicd`  
**Prerequisites:** Phase 1 merged to `develop`

-----

## Task 2.1: Create Branch

⏱️ **Time:** 2 minutes

```bash
git checkout develop
git pull origin develop
git checkout -b feature/phase-2-cicd
```

-----

## Task 2.2: Create GitHub Actions Directory

⏱️ **Time:** 2 minutes

```bash
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p .github/PULL_REQUEST_TEMPLATE
```

-----

## Task 2.3: Create Main CI Workflow

⏱️ **Time:** 45 minutes  
📁 **Files Changed:** `.github/workflows/ci.yml` (created)

### Steps:

**Step 1:** Create the CI workflow file:

```bash
cat > .github/workflows/ci.yml << 'EOF'
# =============================================================================
# CI Workflow - Runs on every push and PR
# =============================================================================
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  workflow_dispatch:  # Allow manual trigger

# Cancel in-progress runs for same ref
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: "3.11"
  PIP_DISABLE_PIP_VERSION_CHECK: 1
  PIP_NO_WARN_SCRIPT_LOCATION: 1

jobs:
  # ===========================================================================
  # Lint - Code style and formatting checks
  # ===========================================================================
  lint:
    name: 🔍 Lint
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v4

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 📦 Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-lint-${{ hashFiles('requirements-dev.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-lint-
            ${{ runner.os }}-pip-

      - name: 📥 Install linting tools
        run: |
          python -m pip install --upgrade pip
          pip install ruff

      - name: 🔍 Run Ruff linter
        run: ruff check . --output-format=github

      - name: 🎨 Check formatting
        run: ruff format --check --diff .

  # ===========================================================================
  # Type Check - Static type analysis
  # ===========================================================================
  type-check:
    name: 📝 Type Check
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v4

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 📦 Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-mypy-${{ hashFiles('requirements-dev.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-mypy-
            ${{ runner.os }}-pip-

      - name: 📥 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install mypy types-requests types-Pillow

      - name: 📝 Run mypy
        run: |
          mypy plugin/ --ignore-missing-imports --no-error-summary 2>&1 | head -50 || true
        continue-on-error: true  # Non-blocking until types added

  # ===========================================================================
  # Test - Run test suite across Python versions
  # ===========================================================================
  test:
    name: 🧪 Test (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    timeout-minutes: 20
    
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v4

      - name: 🐍 Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: 📦 Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-test-${{ matrix.python-version }}-${{ hashFiles('requirements-test.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-test-${{ matrix.python-version }}-
            ${{ runner.os }}-pip-

      - name: 📥 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-test.txt
          pip install -e .

      - name: 🧪 Run tests
        run: |
          pytest tests/ \
            --cov=plugin \
            --cov-report=xml \
            --cov-report=term-missing \
            --junitxml=junit.xml \
            -v \
            -m "not api"
        env:
          ANTHROPIC_API_KEY: "test-key-not-real"
          GOOGLE_API_KEY: "test-key-not-real"

      - name: 📊 Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        if: matrix.python-version == '3.11' && github.event_name != 'pull_request'
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
          verbose: true
        env:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

      - name: 📤 Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-${{ matrix.python-version }}
          path: |
            junit.xml
            coverage.xml
          retention-days: 7

  # ===========================================================================
  # Security - Dependency vulnerability scanning
  # ===========================================================================
  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 10
    
    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v4

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 📥 Install security tools
        run: |
          python -m pip install --upgrade pip
          pip install pip-audit safety bandit

      - name: 🔍 Run pip-audit
        run: pip-audit -r requirements.txt --desc on || true
        continue-on-error: true

      - name: 🔍 Run safety check
        run: safety check -r requirements.txt --output json > safety-report.json || true
        continue-on-error: true

      - name: 🔍 Run bandit
        run: |
          bandit -r plugin/ -f json -o bandit-report.json || true
          bandit -r plugin/ -ll --exit-zero

      - name: 📤 Upload security reports
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            safety-report.json
            bandit-report.json
          retention-days: 30

  # ===========================================================================
  # Build - Verify package builds correctly
  # ===========================================================================
  build:
    name: 📦 Build
    runs-on: ubuntu-latest
    timeout-minutes: 10
    needs: [lint, test]
    
    steps:
      - name: 📥 Checkout code
        uses: actions/checkout@v4

      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: 📥 Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: 📦 Build package
        run: python -m build

      - name: ✅ Check package
        run: twine check dist/*

      - name: 📤 Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7

  # ===========================================================================
  # Summary - Final status check
  # ===========================================================================
  ci-success:
    name: ✅ CI Success
    runs-on: ubuntu-latest
    needs: [lint, test, security, build]
    if: always()
    
    steps:
      - name: Check all jobs
        run: |
          if [[ "${{ needs.lint.result }}" != "success" ]]; then
            echo "❌ Lint failed"
            exit 1
          fi
          if [[ "${{ needs.test.result }}" != "success" ]]; then
            echo "❌ Tests failed"
            exit 1
          fi
          if [[ "${{ needs.build.result }}" != "success" ]]; then
            echo "❌ Build failed"
            exit 1
          fi
          echo "✅ All required checks passed!"
EOF
```

**Step 2:** Commit:

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add main CI workflow with lint, test, security, and build"
```

### ✅ Verification:

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo "✓ Valid YAML"
```

```bash
# Check file size (should be substantial)
wc -l .github/workflows/ci.yml
```

**Expected output:** `180-250` lines

-----

## Task 2.4: Create Pre-commit Configuration

⏱️ **Time:** 20 minutes  
📁 **Files Changed:** `.pre-commit-config.yaml`, `.secrets.baseline`

### Steps:

**Step 1:** Create .pre-commit-config.yaml:

```bash
cat > .pre-commit-config.yaml << 'EOF'
# Pre-commit hooks configuration
# https://pre-commit.com
#
# Install: pip install pre-commit && pre-commit install
# Run all: pre-commit run --all-files
# Update:  pre-commit autoupdate

default_language_version:
  python: python3.11

default_stages: [commit]

repos:
  # ===========================================================================
  # General file hygiene
  # ===========================================================================
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      # File content checks
      - id: trailing-whitespace
        exclude: ^(docs/|.*\.md$)
      - id: end-of-file-fixer
        exclude: ^docs/
      - id: mixed-line-ending
        args: [--fix=lf]
      
      # File format validation
      - id: check-yaml
        args: [--unsafe]  # Allow custom tags
      - id: check-toml
      - id: check-json
      - id: check-xml
      
      # Git checks
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-added-large-files
        args: ['--maxkb=1000']
      
      # Python checks
      - id: debug-statements
      - id: check-docstring-first
      - id: check-ast
      
      # Security
      - id: detect-private-key

  # ===========================================================================
  # Python - Ruff (linting + formatting)
  # ===========================================================================
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.11
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        types_or: [python, pyi]
      - id: ruff-format
        types_or: [python, pyi]

  # ===========================================================================
  # Security - Secret detection
  # ===========================================================================
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: 
          - --baseline
          - .secrets.baseline
        exclude: |
          (?x)^(
            .*\.lock$|
            .*-lock\.json$|
            \.secrets\.baseline$|
            \.env\.example$
          )$

  # ===========================================================================
  # Markdown
  # ===========================================================================
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.38.0
    hooks:
      - id: markdownlint
        args: [--fix, --disable, MD013, MD033, MD041, --]

  # ===========================================================================
  # YAML
  # ===========================================================================
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.33.0
    hooks:
      - id: yamllint
        args: [-d, "{extends: relaxed, rules: {line-length: {max: 120}}}"]

  # ===========================================================================
  # Commit message format (Conventional Commits)
  # ===========================================================================
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert]

# CI configuration for pre-commit.ci
ci:
  autofix_commit_msg: |
    style: auto-fix from pre-commit hooks
    
    [pre-commit.ci]
  autofix_prs: true
  autoupdate_branch: 'develop'
  autoupdate_commit_msg: 'build: update pre-commit hooks'
  autoupdate_schedule: weekly
  skip: [detect-secrets]  # Requires baseline file
  submodules: false
EOF
```

**Step 2:** Create secrets baseline:

```bash
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline
```

**Step 3:** Install hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

**Step 4:** Initial run:

```bash
pre-commit run --all-files || true  # May have fixes
```

**Step 5:** Commit:

```bash
git add .pre-commit-config.yaml .secrets.baseline
git commit -m "build: add pre-commit hooks configuration"
```

### ✅ Verification:

```bash
pre-commit --version
```

**Expected output:** `pre-commit X.Y.Z`

```bash
pre-commit run --all-files 2>&1 | tail -5
```

**Expected output:** Should show hook results

-----

## Task 2.5: Create Dependabot Configuration

⏱️ **Time:** 10 minutes  
📁 **Files Changed:** `.github/dependabot.yml`

### Steps:

```bash
cat > .github/dependabot.yml << 'EOF'
# Dependabot configuration
# https://docs.github.com/en/code-security/dependabot/dependabot-version-updates

version: 2

updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "06:00"
      timezone: "America/New_York"
    open-pull-requests-limit: 5
    reviewers:
      - "davistroy"
    labels:
      - "dependencies"
      - "python"
    commit-message:
      prefix: "deps"
      include: "scope"
    groups:
      # Group minor/patch updates for dev dependencies
      dev-dependencies:
        patterns:
          - "pytest*"
          - "ruff"
          - "mypy"
          - "pre-commit"
          - "coverage"
        update-types:
          - "minor"
          - "patch"
      # Group AI SDK updates together
      ai-sdks:
        patterns:
          - "anthropic"
          - "google-generativeai"
        update-types:
          - "minor"
          - "patch"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    labels:
      - "dependencies"
      - "github-actions"
    commit-message:
      prefix: "ci"
    groups:
      actions:
        patterns:
          - "*"
EOF

git add .github/dependabot.yml
git commit -m "ci: add Dependabot configuration for automated updates"
```

-----

## Task 2.6: Add README Badges

⏱️ **Time:** 10 minutes  
📁 **Files Changed:** `README.md`

### Steps:

**Step 1:** Create badge block:

```bash
# Read current README
head -5 README.md

# Add badges after the title (adjust based on current structure)
```

**Step 2:** Insert badges at top of README.md (manually or via sed):

Add these lines after `# AI-Assisted Presentation Generator`:

```markdown
[![CI](https://github.com/davistroy/slide-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/davistroy/slide-generator/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
```

**Step 3:** Commit:

```bash
git add README.md
git commit -m "docs: add CI and quality badges to README"
```

-----

## Task 2.7: Create PR Template

⏱️ **Time:** 10 minutes  
📁 **Files Changed:** `.github/pull_request_template.md`

### Steps:

```bash
cat > .github/pull_request_template.md << 'EOF'
## Description

<!-- Describe your changes in detail -->

## Type of Change

<!-- Mark relevant options with [x] -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to change)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration/build change
- [ ] ♻️ Refactoring (no functional changes)
- [ ] 🧪 Test update

## Related Issues

<!-- Link any related issues: Fixes #123, Relates to #456 -->

## Checklist

<!-- Ensure all items are checked before requesting review -->

- [ ] My code follows the project's coding standards
- [ ] I have run `make lint` and fixed any issues
- [ ] I have run `make test` and all tests pass
- [ ] I have added tests for new functionality
- [ ] I have updated documentation as needed
- [ ] I have updated CHANGELOG.md

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Additional Notes

<!-- Any additional information reviewers should know -->
EOF

git add .github/pull_request_template.md
git commit -m "docs: add pull request template"
```

-----

## Task 2.8: Push and Create PR

⏱️ **Time:** 5 minutes

```bash
git push -u origin feature/phase-2-cicd

# Create PR (GitHub CLI)
gh pr create \
  --title "Phase 2: CI/CD Implementation" \
  --body "## Summary
Implements automated CI/CD pipeline with:
- GitHub Actions workflow for lint, test, security, and build
- Pre-commit hooks for local quality checks
- Dependabot for automated dependency updates
- PR template for consistent contributions

## Verification
- [ ] CI workflow runs successfully
- [ ] Pre-commit hooks install and run
- [ ] Badges display correctly
" \
  --base develop
```

-----

## Phase 2 Final Checklist

- [ ] `.github/workflows/ci.yml` exists and is valid YAML
- [ ] `.pre-commit-config.yaml` exists
- [ ] `.secrets.baseline` exists
- [ ] `.github/dependabot.yml` exists
- [ ] `.github/pull_request_template.md` exists
- [ ] `pre-commit install` succeeds
- [ ] `pre-commit run --all-files` completes
- [ ] Push triggers CI workflow
- [ ] CI workflow shows all jobs

-----

# REMAINING PHASES (Summary)

Due to length, here are the key tasks for remaining phases:

## Phase 3: Test Organization (3-4 hours)

- **3.1**: Create `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- **3.2**: Move root-level test files to `tests/integration/`
- **3.3**: Create `tests/conftest.py` with shared fixtures
- **3.4**: Add pytest markers to all tests
- **3.5**: Create sample fixture files
- **3.6**: Verify test discovery works

## Phase 4: Type Safety (6-8 hours)

- **4.1**: Create `plugin/types.py` with dataclasses
- **4.2**: Add type hints to `base_skill.py`
- **4.3**: Add type hints to `skill_registry.py`
- **4.4**: Add type hints to API clients
- **4.5**: Configure mypy per-module strictness
- **4.6**: Add type stubs for external libraries
- **4.7**: Add docstrings (Google style)

## Phase 5: Security (4-5 hours)

- **5.1**: Create `plugin/lib/validators.py`
- **5.2**: Create `plugin/lib/retry.py` with backoff
- **5.3**: Create `plugin/lib/rate_limiter.py`
- **5.4**: Add security scanning workflow
- **5.5**: Create secure config loader
- **5.6**: Add input sanitization

## Phase 6: Logging (5-7 hours)

- **6.1**: Create `plugin/lib/logging_config.py`
- **6.2**: Implement JSON structured logging
- **6.3**: Create `plugin/lib/metrics.py`
- **6.4**: Add progress reporting
- **6.5**: Integrate logging throughout codebase

## Phase 7: Async (8-12 hours)

- **7.1**: Create `plugin/lib/async_claude_client.py`
- **7.2**: Create `plugin/lib/async_gemini_client.py`
- **7.3**: Add async workflow orchestrator
- **7.4**: Implement connection pooling
- **7.5**: Add async tests

## Phase 8: Consolidation (10-15 hours)

- **8.1**: Document `presentation-skill/` structure
- **8.2**: Create migration plan
- **8.3**: Create `PowerPointAssemblySkill`
- **8.4**: Create `MarkdownParsingSkill`
- **8.5**: Update skill registry
- **8.6**: Add deprecation warnings
- **8.7**: Update CLI to use new skills
- **8.8**: Remove deprecated module

## Phase 9: Documentation (4-6 hours)

- **9.1**: Generate API docs with pdoc
- **9.2**: Create ADR directory and templates
- **9.3**: Write key ADRs
- **9.4**: Add architecture diagram to README
- **9.5**: Create CONTRIBUTING.md updates
- **9.6**: Final review and polish

-----

# Quick Reference Commands

```bash
# Phase 1 - Foundation
make help                    # Show all commands
make install-dev            # Install dev dependencies
make clean                  # Clean artifacts

# Phase 2 - CI/CD
pre-commit run --all-files  # Run all hooks
pre-commit autoupdate       # Update hook versions

# Phase 3 - Testing
make test                   # Run all tests
make test-unit             # Run unit tests only
make test-cov              # Run with coverage
pytest -m "not api"        # Skip API tests

# Phase 4 - Types
make type-check            # Run mypy
mypy plugin/ --strict      # Strict mode

# Phase 5 - Security
make security              # Run security scans
bandit -r plugin/          # Run bandit

# Phase 6 - Logging
# (Use logging config in code)

# Full verification
make ci                    # Run full CI locally
make all                   # Clean + install + check
```

-----

*Last updated: January 4, 2026*