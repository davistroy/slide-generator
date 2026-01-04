# Test Fixtures

This directory contains test data and fixtures for the presentation generation plugin.

## Files

### `test_prompts.json`

Contains test prompts for various workflow scenarios.

**Primary Test Prompt:** `rochester_2gc_carburetor`

This is our main test case - a complex, multi-presentation topic about carburetor rebuilding:
- Tests multi-presentation detection (expects 3 presentations)
- Tests visual-heavy content generation (40+ images expected)
- Tests instructional/step-by-step content
- Tests technical writing with detailed specifications
- High complexity, comprehensive research depth

**Other Test Prompts:**
- `ai_healthcare_simple` - Simple single presentation
- `climate_change_complex` - Multi-presentation for different audiences
- `product_launch_quick` - Quick workflow with minimal research

## Usage

### In Tests

```python
import json
from pathlib import Path

# Load test prompts
fixtures_dir = Path(__file__).parent.parent / "fixtures"
with open(fixtures_dir / "test_prompts.json") as f:
    test_data = json.load(f)

# Get primary test prompt
primary_prompt = test_data["prompts"]["rochester_2gc_carburetor"]["prompt"]

# Run workflow with test prompt
result = orchestrator.execute_workflow(
    workflow_id="test-rochester-2gc",
    initial_input=primary_prompt,
    config=config
)
```

### As Pytest Fixture

```python
# In conftest.py
@pytest.fixture
def rochester_2gc_prompt(fixtures_dir):
    """Load Rochester 2GC test prompt."""
    with open(fixtures_dir / "test_prompts.json") as f:
        data = json.load(f)
    return data["prompts"]["rochester_2gc_carburetor"]

# In test file
def test_multi_presentation_detection(rochester_2gc_prompt):
    prompt = rochester_2gc_prompt["prompt"]
    expected = rochester_2gc_prompt["expected_outcomes"]["presentations"]
    # ... test logic
```

## Expected Outcomes

Each test prompt includes:
- **prompt**: The actual user input
- **expected_presentations**: Number of presentations expected
- **expected_outcomes**: Detailed expectations for results
- **test_scenarios**: Specific test scenarios and success criteria

## Adding New Test Data

When adding new test prompts:

1. Add to `test_prompts.json` under `prompts`
2. Include all expected outcomes
3. Define test scenarios
4. Update this README
5. Add fixture to `conftest.py` if needed

## Sample Data Files (To Be Added)

These files will be added as implementation progresses:

- `sample_research.json` - Research output for Rochester 2GC
- `sample_outline_general.md` - Outline for general carburetor presentation
- `sample_outline_technical.md` - Outline for technical presentation
- `sample_outline_hands_on.md` - Outline for rebuild guide
- `sample_presentation_general.md` - Complete general presentation
- `sample_presentation_technical.md` - Complete technical presentation
- `sample_presentation_hands_on.md` - Complete rebuild guide
- `sample_images/` - Sample generated images
- `mock_api_responses/` - Mock API responses for testing
- `cfa_style.json` - CFA brand style configuration
- `stratfield_style.json` - Stratfield brand style configuration

## Generating Sample Data

To generate sample data from actual workflow runs:

```bash
# Run workflow with artifact saving
python -m plugin.cli full-workflow \
  "Rochester 2GC carburetor rebuild" \
  --template cfa \
  --output ./test-run \
  --save-all-artifacts

# Copy artifacts to fixtures
cp ./test-run/research.json tests/fixtures/sample_research.json
cp ./test-run/outline.md tests/fixtures/sample_outline_general.md
# ... etc
```

## Mock API Responses

Mock API responses are stored in `mock_api_responses/` directory:

- `gemini_research_*.json` - Mock Gemini responses for research
- `gemini_content_*.json` - Mock Gemini responses for content generation
- `gemini_images_*.json` - Mock Gemini responses for image generation
- `search_results_*.json` - Mock search API responses

These allow tests to run without actual API calls.
