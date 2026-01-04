# Test Data Summary

## Primary Test Prompt: Rochester 2GC Carburetor Rebuild

Your test prompt has been stored and integrated into the testing framework.

### The Prompt

```
I want to do some research, develop a detailed research document, and eventually
build a presentation or presentations on the following topic: how a carburetor
works, what all of the parts are and how they work and contribute to the
functionality of a carburetor, and then specifically for the Rochester 2GC,
what all of the parts are, how it works in detail, and, assuming the audience
is someone with basic tools and knowledge, a step-by-step very detailed process,
with pictures/drawings, that shows how to disassemble and fully rebuild and test
a Rochester 2GC carburetor
```

### Why This Is Excellent Test Data

This prompt is **perfect** for comprehensive testing because it:

✅ **Multi-Presentation Detection**
   - Will trigger detection of need for 3 separate presentations:
     1. General: "How Carburetors Work" (12-18 slides)
     2. Technical: "Rochester 2GC Complete Guide" (20-30 slides)
     3. Hands-On: "Rochester 2GC Rebuild Guide" (30-45 slides)

✅ **Visual-Heavy Content**
   - Requires 40+ detailed images
   - Tests image generation capacity
   - Tests various image types:
     * Exploded diagrams
     * Component close-ups
     * Assembly sequences
     * Cross-section views
     * Tool identification
     * Testing procedures

✅ **Complex Research Requirements**
   - Technical specifications needed
   - Historical context
   - Parts identification
   - Troubleshooting information
   - Safety considerations

✅ **Instructional Content**
   - Step-by-step procedures
   - Numbered sequences
   - Tool requirements
   - Safety warnings
   - Testing procedures
   - Troubleshooting tips

✅ **Different Audience Levels**
   - General understanding (beginners)
   - Technical detail (enthusiasts)
   - Hands-on practical (mechanics)

✅ **Quality Validation**
   - Technical accuracy crucial
   - Visual clarity essential
   - Step sequence must be logical
   - Safety information required

### Expected Outcomes

**Presentations:** 3
1. **General Carburetor Overview**
   - Audience: Anyone wanting to understand carburetors
   - Slides: 12-18
   - Focus: How carburetors work, basic principles

2. **Rochester 2GC Technical Guide**
   - Audience: Technical enthusiasts
   - Slides: 20-30
   - Focus: Detailed component breakdown, how it works

3. **Rochester 2GC Rebuild Guide**
   - Audience: DIY mechanics with basic tools
   - Slides: 30-45
   - Focus: Step-by-step disassembly, rebuild, testing

**Total Images:** 40-50+

**Research Depth:** Comprehensive

**Citation Requirements:** High (technical specs, safety data)

**API Calls (Estimated):**
- Research: ~20 calls
- Content: ~60 calls
- Images: ~50 calls
- Total: ~130 calls

**Expected Duration:** 45 minutes

**Expected Cost:** $3-5

### Storage Location

**File:** `tests/fixtures/test_prompts.json`

**Structure:**
```json
{
  "prompts": {
    "rochester_2gc_carburetor": {
      "id": "rochester_2gc_carburetor",
      "prompt": "...",
      "expected_outcomes": {
        "multi_presentation": true,
        "presentations": [...],
        ...
      },
      "test_scenarios": {...}
    }
  }
}
```

### Using in Tests

#### As Pytest Fixture

```python
def test_full_workflow(rochester_2gc_prompt_text):
    """Test full workflow with carburetor rebuild prompt."""
    result = orchestrator.execute_workflow(
        workflow_id="test-rochester-2gc",
        initial_input=rochester_2gc_prompt_text,
        config={}
    )

    assert result.success
    assert len(result.phase_results) == 4
```

#### Accessing Full Test Data

```python
def test_multi_presentation_detection(rochester_2gc_prompt):
    """Test multi-presentation detection."""
    expected = rochester_2gc_prompt["expected_outcomes"]

    assert expected["multi_presentation"] is True
    assert len(expected["presentations"]) == 3

    # Verify presentation types
    audiences = [p["audience"] for p in expected["presentations"]]
    assert "general" in audiences
    assert "technical" in audiences
    assert "hands_on" in audiences
```

#### Direct Access

```python
import json

with open("tests/fixtures/test_prompts.json") as f:
    data = json.load(f)

prompt = data["prompts"]["rochester_2gc_carburetor"]["prompt"]
```

### Test Scenarios Defined

1. **Full Workflow Test**
   - Tests: Complete workflow execution
   - Expected: All 3 presentations generated successfully
   - Duration: ~45 minutes
   - Artifacts: 12+ files

2. **Multi-Presentation Detection**
   - Tests: Outline skill detects need for 3 presentations
   - Expected: 3 separate outlines generated
   - Audiences: general, technical, hands_on

3. **Visual-Heavy Content**
   - Tests: Handling of many complex images
   - Expected: 40+ high-quality images
   - Types: Diagrams, close-ups, sequences

4. **Instructional Content**
   - Tests: Step-by-step content generation
   - Expected: Numbered steps, tools, safety, troubleshooting
   - Quality: Clear, sequential, comprehensive

### Running Tests with This Data

```bash
# Test full workflow with primary test data
pytest tests/e2e/test_full_workflow.py::test_full_workflow_complex_topic

# Test multi-presentation detection
pytest tests/e2e/test_multi_presentation.py -v

# Test visual-heavy content handling
pytest tests/quality/test_image_quality.py -v

# Test instructional content generation
pytest tests/quality/test_content_quality.py -v
```

### Generating Real Sample Data

Once implementation is complete, generate actual artifacts:

```bash
# Run the full workflow with this prompt
python -m plugin.cli full-workflow \
  "Rochester 2GC carburetor rebuild" \
  --template cfa \
  --output ./rochester-2gc-test \
  --save-all-artifacts

# Copy artifacts to test fixtures
cp rochester-2gc-test/research.json tests/fixtures/sample_research.json
cp rochester-2gc-test/outline-*.md tests/fixtures/
cp rochester-2gc-test/presentation-*.md tests/fixtures/
cp -r rochester-2gc-test/images tests/fixtures/sample_images/
```

This will create real sample data based on the actual workflow execution.

### Additional Test Prompts

Three other test prompts are also stored for different scenarios:

1. **ai_healthcare_simple**
   - Simple single presentation
   - Quick test case (15-20 min)
   - Standard research depth

2. **climate_change_complex**
   - Multi-presentation (2)
   - Different audiences (scientific, policy)
   - High citation requirements

3. **product_launch_quick**
   - Minimal research
   - Quick execution (10-15 min)
   - Low complexity

### Integration with CI/CD

The test data is automatically available in all test environments:

```yaml
# In CI pipeline
- name: Run E2E tests
  run: |
    pytest tests/e2e/test_full_workflow.py \
      --use-fixture rochester_2gc_prompt_text
```

### Success Criteria

When testing with this prompt, success means:

✅ **Multi-Presentation Detection**
   - 3 presentations detected and generated

✅ **Research Quality**
   - 15-20 relevant sources found
   - Technical specifications accurate
   - Safety information included

✅ **Content Quality**
   - All 3 presentations have appropriate depth
   - Step-by-step sequences logical
   - Technical terminology correct
   - Safety warnings present

✅ **Visual Quality**
   - 40+ images generated
   - Images relevant to content
   - Brand colors used appropriately
   - Diagrams clear and detailed

✅ **Overall Quality**
   - All presentations are valid .pptx files
   - Slide counts within expected ranges
   - Citations accurate
   - User satisfaction high

### Next Steps

1. **Implement Skills** - Build research, content, and image skills

2. **Run Real Test** - Execute workflow with this prompt

3. **Generate Samples** - Create real sample data files

4. **Validate Quality** - Ensure all success criteria met

5. **Iterate** - Refine based on actual results

---

**Your test data is ready!** 🚀

The Rochester 2GC carburetor rebuild prompt is now the primary test case for all workflow testing. As we build out each priority, we'll continuously test against this real-world, complex scenario to ensure the plugin can handle demanding use cases.
