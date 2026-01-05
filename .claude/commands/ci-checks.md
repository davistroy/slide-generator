---
name: ci-checks
description: Pull latest, run full CI checks locally, fix all issues, and push
---

# CI Checks - Local Validation and Fix

Run the complete CI pipeline locally, fix any issues found, and push the fixes.

## Steps to Execute

1. **Pull latest changes**
   ```bash
   git pull origin $(git branch --show-current)
   ```

2. **Run ruff linter and fix issues**
   ```bash
   ruff check . --fix
   ```

3. **Run ruff formatter**
   ```bash
   ruff format .
   ```

4. **Run pytest (unit tests only, skip API tests)**
   ```bash
   pytest tests/unit/ -v -m "not api" --tb=short
   ```

5. **If any files were modified, commit and push**
   ```bash
   git add -A
   git diff --cached --quiet || git commit -m "fix: resolve CI linter and test issues"
   git push
   ```

## Instructions

Execute each step above in order. If ruff or pytest find issues that can't be auto-fixed, manually fix them before proceeding. Report a summary of:
- Number of lint issues found/fixed
- Number of formatting changes
- Test results (passed/failed/skipped)
- Whether a commit was made and pushed
