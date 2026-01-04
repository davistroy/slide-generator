# Tests

Comprehensive test suite for the AI-Assisted Presentation Generation Plugin.

## Quick Start

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run specific test type
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m e2e               # End-to-end tests only

# Run with coverage
pytest --cov --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Test Organization

```
tests/
├── unit/              # Unit tests (60% of suite)
├── integration/       # Integration tests (30% of suite)
├── e2e/              # End-to-end tests (10% of suite)
├── performance/       # Performance and load tests
├── quality/          # Quality validation tests
├── manual/           # Manual test procedures
├── fixtures/         # Test data and fixtures
├── conftest.py       # Pytest configuration
└── README.md         # This file
```

## Primary Test Data

**Main Test Prompt:** Rochester 2GC Carburetor Rebuild

This comprehensive test case covers:
- Multi-presentation detection (3 presentations expected)
- Visual-heavy content (40+ images)
- Technical/instructional content
- Step-by-step procedures
- Complex research requirements

See `fixtures/test_prompts.json` for the complete prompt and expected outcomes.

## Using Test Fixtures

### Primary Test Prompt

```python
def test_full_workflow(rochester_2gc_prompt_text, workflow_orchestrator):
    """Test full workflow with primary test data."""
    result = workflow_orchestrator.execute_workflow(
        workflow_id="test-rochester-2gc",
        initial_input=rochester_2gc_prompt_text,
        config={}
    )

    assert result.success
    assert len(result.final_artifacts) > 0
```

### Expected Outcomes

```python
def test_multi_presentation_detection(rochester_2gc_prompt):
    """Test that multi-presentation is detected."""
    expected = rochester_2gc_prompt["expected_outcomes"]

    assert expected["multi_presentation"] is True
    assert len(expected["presentations"]) == 3

    # Check presentation types
    audiences = [p["audience"] for p in expected["presentations"]]
    assert "general" in audiences
    assert "technical" in audiences
    assert "hands_on" in audiences
```

## Running Tests

### By Test Type

```bash
# Unit tests (fast, run frequently)
pytest tests/unit -v

# Integration tests (moderate speed)
pytest tests/integration -v

# E2E tests (slow, run before commits)
pytest tests/e2e -v

# Performance tests (run periodically)
pytest tests/performance -v
```

### By Component

```bash
# Infrastructure tests
pytest tests/unit/test_base_skill.py
pytest tests/unit/test_skill_registry.py
pytest tests/unit/test_workflow_orchestrator.py

# Skill tests
pytest tests/unit/skills/

# Library tests
pytest tests/unit/lib/
```

### With Markers

```bash
# Run only slow tests
pytest -m slow

# Skip slow tests
pytest -m "not slow"

# Windows-only tests
pytest -m windows_only

# API tests (requires real APIs)
pytest -m api
```

### Coverage

```bash
# Run with coverage report
pytest --cov=plugin --cov-report=html

# Fail if coverage below 80%
pytest --cov=plugin --cov-fail-under=80

# Show missing lines
pytest --cov=plugin --cov-report=term-missing
```

## Test Development Workflow

### Test-Driven Development (TDD)

1. **Write test first:**
   ```python
   def test_research_skill_executes():
       """Test that research skill executes successfully."""
       skill = ResearchSkill()
       input = SkillInput(data={"topic": "test topic"})

       result = skill.execute(input)

       assert result.success
       assert "sources" in result.data
   ```

2. **Run test (should fail):**
   ```bash
   pytest tests/unit/skills/test_research_skill.py::test_research_skill_executes
   ```

3. **Implement feature:**
   ```python
   # Implement ResearchSkill.execute()
   ```

4. **Run test again (should pass):**
   ```bash
   pytest tests/unit/skills/test_research_skill.py::test_research_skill_executes
   ```

### Adding New Tests

1. Choose appropriate test file:
   - Unit: `tests/unit/test_<module>.py`
   - Integration: `tests/integration/test_<workflow>.py`
   - E2E: `tests/e2e/test_<scenario>.py`

2. Use descriptive test names:
   ```python
   def test_<scenario>_<expected_outcome>():
       """Clear description of what this tests."""
   ```

3. Follow AAA pattern:
   ```python
   def test_example():
       # Arrange
       skill = MySkill()
       input = SkillInput(data={...})

       # Act
       result = skill.execute(input)

       # Assert
       assert result.success
   ```

4. Use fixtures:
   ```python
   def test_with_fixture(rochester_2gc_prompt_text):
       """Test using test fixture."""
       assert "carburetor" in rochester_2gc_prompt_text
   ```

## Test Data

### Test Prompts

Located in `fixtures/test_prompts.json`:

1. **rochester_2gc_carburetor** (Primary)
   - Complex multi-presentation topic
   - Visual-heavy content
   - Instructional/technical

2. **ai_healthcare_simple**
   - Simple single presentation
   - Quick test case

3. **climate_change_complex**
   - Multi-presentation with different audiences
   - High citation requirements

4. **product_launch_quick**
   - Minimal research workflow
   - Quick execution

### Generating Sample Data

After implementing skills, generate real sample data:

```bash
# Run workflow and save artifacts
python -m plugin.cli full-workflow \
  "Rochester 2GC carburetor rebuild" \
  --template cfa \
  --output ./test-artifacts \
  --save-all-artifacts

# Copy to fixtures
cp test-artifacts/research.json tests/fixtures/sample_research.json
cp test-artifacts/outline.md tests/fixtures/sample_outline.md
# ... etc
```

## Continuous Integration

### Pre-Commit Checks

```bash
# Before every commit
pytest tests/unit -m "not slow" --maxfail=1
black plugin/ tests/
pylint plugin/
```

### Pre-Push Checks

```bash
# Before pushing
pytest tests/unit tests/integration -m "not slow"
pytest --cov --cov-fail-under=80
```

### CI Pipeline

See `.github/workflows/test.yml` for CI configuration.

## Debugging Tests

### Verbose Output

```bash
# Show all output
pytest -v -s

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

### Running Single Test

```bash
# Run specific test
pytest tests/unit/test_base_skill.py::TestBaseSkill::test_skill_requires_skill_id

# Run tests matching pattern
pytest -k "test_skill"
```

### Debugging with pdb

```python
def test_debug_example():
    import pdb; pdb.set_trace()
    # Test code here
```

Or use pytest's debugger:
```bash
pytest --pdb  # Drop into debugger on failure
```

## Test Reports

### HTML Coverage Report

```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

### JUnit XML (for CI)

```bash
pytest --junitxml=test-results.xml
```

### Test Duration Report

```bash
pytest --durations=10  # Show 10 slowest tests
```

## Success Criteria

See `PLUGIN_TEST_PLAN.md` for detailed success criteria.

**Quality Gates:**
- ✅ 80%+ code coverage before merge
- ✅ 85%+ coverage on skills
- ✅ All tests pass
- ✅ No critical bugs

**Performance Targets:**
- Full workflow: < 30 min (simple) / 60 min (complex)
- Research phase: < 5 min
- Content phase: < 5 min
- Image phase: < 10 min
- Average cost: < $5 per workflow

## Resources

- **Test Plan:** `PLUGIN_TEST_PLAN.md`
- **Implementation Plan:** `PLUGIN_IMPLEMENTATION_PLAN.md`
- **Plugin Documentation:** `plugin/README.md`
- **Pytest Docs:** https://docs.pytest.org/
