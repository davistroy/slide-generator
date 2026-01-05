# Contributing to Slide Generator

Thank you for your interest in contributing! This document provides guidelines
and information for contributors.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- API keys (see SETUP_APIS.md)

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/davistroy/slide-generator.git
   cd slide-generator
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   ```

3. Install development dependencies:
   ```bash
   make install-dev
   # or: pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

## Development Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Code Style

This project uses:
- **Ruff** for linting and formatting
- **MyPy** for type checking
- **Google-style docstrings**

Run checks before committing:
```bash
make check  # Runs lint, type-check, and tests
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific tests
pytest tests/unit/test_specific.py -v
```

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Formatting
- `refactor:` Code refactoring
- `test:` Tests
- `build:` Build system
- `ci:` CI configuration
- `chore:` Maintenance

Examples:
```
feat: add async image generation
fix: handle rate limit errors in Claude client
docs: update API documentation
```

## Adding New Skills

1. Create skill file in `plugin/skills/`:
   ```python
   from plugin.base_skill import BaseSkill, SkillInput, SkillOutput

   class MyNewSkill(BaseSkill):
       @property
       def skill_id(self) -> str:
           return "my-skill"

       # ... implement other methods
   ```

2. Register in `plugin/skills/__init__.py`

3. Add CLI command in `plugin/cli.py` (if needed)

4. Write tests in `tests/unit/`

5. Update documentation

## Pull Request Process

1. Create feature branch from `main`
2. Make changes with tests
3. Run `make check` to verify
4. Push and create PR
5. Fill out PR template
6. Address review feedback
7. Squash and merge when approved

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Questions?

Open an issue on GitHub for:
- Bug reports
- Feature requests
- Questions about the codebase
