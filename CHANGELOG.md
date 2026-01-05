# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dependency version pinning with ranges
- MIT License file
- This changelog
- `.editorconfig` for consistent formatting
- `Makefile` with common development commands
- `pyproject.toml` for modern Python project configuration
- CI badges in README
- **CI/CD Pipeline**: GitHub Actions workflow with lint, test, security, and build jobs
- **Pre-commit hooks**: Ruff, trailing whitespace, YAML validation, secret detection
- **Dependabot**: Automated dependency updates for Python packages and GitHub Actions
- **Issue templates**: Bug report and feature request templates
- **PR template**: Standardized pull request checklist

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
