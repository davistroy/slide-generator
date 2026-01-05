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
