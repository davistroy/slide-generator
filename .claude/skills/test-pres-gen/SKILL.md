# Test Presentation Generator Skill

## Description
Comprehensive testing of the presentation generator skill with full image generation, both templates (CFA and Stratfield), detailed inspection, and issue reporting.

## Instructions

You are tasked with performing a COMPLETE and THOROUGH test of the presentation generator skill. Follow these steps precisely:

### Phase 1: Setup and Preparation

1. **Create Todo List** - Use TodoWrite to create a comprehensive task list:
   - Parse presentation.md with parser
   - Check for GOOGLE_API_KEY environment variable
   - Generate images for all slides with graphics
   - Generate CFA presentation with images
   - Generate Stratfield presentation with images
   - Inspect CFA presentation thoroughly
   - Inspect Stratfield presentation thoroughly
   - Compare results to expected content
   - Create detailed test report
   - Identify issues and create fix plan

2. **Read Test File** - Read `tests/testfiles/presentation.md` to understand:
   - Total number of slides
   - Content types used (bullets, tables, numbered lists, code blocks, text)
   - Which slides have **Graphic** sections
   - Expected titles and content for each slide

3. **Environment Check**:
   - Check if GOOGLE_API_KEY is set
   - If not set, inform user and ask whether to:
     - Skip image generation (--skip-images)
     - Wait for user to set API key
     - Continue anyway (will fail during image generation)

### Phase 2: Parser Testing

4. **Test Parser** - Run parser directly:
   ```bash
   python presentation-skill/lib/parser.py tests/testfiles/presentation.md
   ```
   - Verify slide count matches expected
   - Check for any parsing errors
   - Verify titles are clean (no `**` artifacts)
   - Confirm content types are detected

### Phase 3: Image Generation (if API key available)

5. **Generate Slide Images**:
   ```bash
   python scripts/generate_images_for_slides.py \
     --slides tests/testfiles/presentation.md \
     --output tests/artifacts/images \
     --fast \
     --force
   ```
   - Track which slides get images
   - Monitor for API errors
   - Verify image files are created
   - Check image file sizes are reasonable

### Phase 4: Presentation Generation

6. **Generate CFA Presentation**:
   ```bash
   python presentation-skill/generate_presentation.py \
     tests/testfiles/presentation.md \
     --template cfa \
     --output tests/artifacts/comprehensive-test-cfa.pptx
   ```
   - Note: Use --skip-images if no API key
   - Capture any errors or warnings
   - Verify PPTX file is created

7. **Generate Stratfield Presentation**:
   ```bash
   python presentation-skill/generate_presentation.py \
     tests/testfiles/presentation.md \
     --template stratfield \
     --output tests/artifacts/comprehensive-test-stratfield.pptx
   ```
   - Note: Use --skip-images if no API key
   - Capture any errors or warnings
   - Verify PPTX file is created

### Phase 5: Deep Inspection

8. **Inspect CFA Presentation** - Use python-pptx to inspect:
   - Total slide count
   - For EACH slide:
     - Slide number and title
     - All text shapes and their content
     - Check for markdown artifacts (`**`, `*`, backticks)
     - Verify bullet points are properly formatted
     - Check table content (if rendered)
     - Verify images are embedded (if generated)
     - Count total characters in content
   - Create detailed slide-by-slide breakdown

9. **Inspect Stratfield Presentation** - Same inspection as CFA:
   - Total slide count
   - Slide-by-slide analysis
   - Text content verification
   - Markdown artifact check
   - Image verification

10. **Content Comparison** - For EACH slide:
    - Compare expected content from presentation.md
    - Verify all bullets/lists are present
    - Check tables are rendered (or documented as text)
    - Confirm numbered lists are preserved
    - Verify code blocks are included
    - Check plain text paragraphs are present

### Phase 6: Reporting

11. **Create Test Report** - Write to `tests/COMPREHENSIVE_TEST_REPORT.md`:

    ```markdown
    # Comprehensive Test Report - Presentation Generator v1.1.0

    **Date:** [timestamp]
    **Test File:** tests/testfiles/presentation.md
    **API Key Available:** [yes/no]
    **Images Generated:** [yes/no]

    ---

    ## Executive Summary

    - Total Slides Expected: [N]
    - Total Slides Generated: [N]
    - Success Rate: [percentage]
    - Issues Found: [count]
    - Critical Issues: [count]
    - Minor Issues: [count]

    ---

    ## Test Results by Phase

    ### Phase 1: Parser Testing
    - Status: [PASS/FAIL]
    - Slides Parsed: [N]
    - Errors: [list]

    ### Phase 2: Image Generation
    - Status: [PASS/FAIL/SKIPPED]
    - Images Generated: [N]
    - Errors: [list]

    ### Phase 3: CFA Presentation
    - Status: [PASS/FAIL]
    - Slides Generated: [N]
    - Errors: [list]

    ### Phase 4: Stratfield Presentation
    - Status: [PASS/FAIL]
    - Slides Generated: [N]
    - Errors: [list]

    ---

    ## Detailed Slide-by-Slide Analysis

    ### CFA Template Results

    #### Slide 1: [Title]
    - **Expected Content:** [summary]
    - **Actual Content:** [summary]
    - **Status:** [PASS/FAIL]
    - **Issues:** [list or "None"]
    - **Character Count:** [N]
    - **Has Image:** [yes/no]

    [Repeat for all slides]

    ### Stratfield Template Results

    [Same format as CFA]

    ---

    ## Content Type Analysis

    ### Bullet Lists
    - Total Expected: [N]
    - Total Found: [N]
    - Status: [PASS/FAIL]

    ### Numbered Lists
    - Total Expected: [N]
    - Total Found: [N]
    - Status: [PASS/FAIL]

    ### Tables
    - Total Expected: [N]
    - Total Rendered: [N]
    - Rendering Method: [native/text/missing]
    - Status: [PASS/FAIL]

    ### Code Blocks
    - Total Expected: [N]
    - Total Found: [N]
    - Status: [PASS/FAIL]

    ### Plain Text Paragraphs
    - Total Expected: [N]
    - Total Found: [N]
    - Status: [PASS/FAIL]

    ---

    ## Issues Found

    ### Critical Issues
    [List each critical issue with details]

    ### High Priority Issues
    [List each high priority issue]

    ### Medium Priority Issues
    [List each medium priority issue]

    ### Low Priority Issues
    [List each low priority issue]

    ---

    ## Comparison: CFA vs Stratfield

    - Content Consistency: [analysis]
    - Formatting Differences: [analysis]
    - Issues Unique to CFA: [list]
    - Issues Unique to Stratfield: [list]

    ---

    ## Performance Metrics

    - Parser Execution Time: [seconds]
    - Image Generation Time: [seconds]
    - CFA Generation Time: [seconds]
    - Stratfield Generation Time: [seconds]
    - Total Test Duration: [seconds]

    ---

    ## Recommendations

    [List specific recommendations based on findings]
    ```

12. **Create Fix Plan** - Write to `tests/FIX_PLAN.md` if issues found:

    ```markdown
    # Fix Plan for Issues Found in Comprehensive Testing

    **Generated:** [timestamp]
    **Based on:** COMPREHENSIVE_TEST_REPORT.md

    ---

    ## Issue #1: [Title]

    **Priority:** [Critical/High/Medium/Low]
    **Component:** [parser/assembler/template/image_gen]
    **File:** [specific file path]

    **Description:**
    [Detailed description of the issue]

    **Root Cause:**
    [Analysis of why this is happening]

    **Fix Strategy:**
    [Step-by-step plan to fix]

    **Files to Modify:**
    - [file:line_number]
    - [file:line_number]

    **Testing:**
    [How to verify the fix works]

    **Estimated Impact:**
    [How this affects users]

    ---

    [Repeat for each issue]

    ---

    ## Implementation Order

    1. [Issue #N] - [Reason for priority]
    2. [Issue #N] - [Reason for priority]
    3. [Issue #N] - [Reason for priority]

    ---

    ## Testing Plan After Fixes

    [Describe how to re-test after implementing fixes]
    ```

### Phase 7: Summary

13. **Present Summary to User** - Provide a concise summary:
    - Overall test status (PASS/FAIL)
    - Total issues found with breakdown by severity
    - Key findings and recommendations
    - Links to detailed reports
    - Next steps

---

## Important Notes

- **Be Thorough**: Don't skip any slides or steps
- **Track Progress**: Update todo list as you complete each phase
- **Detailed Inspection**: Actually open and inspect the PPTX files using python-pptx
- **Real Comparison**: Compare actual content against presentation.md expectations
- **Document Everything**: Capture all errors, warnings, and observations
- **Be Objective**: Report issues even if minor
- **Actionable Recommendations**: Fix plan should be specific and implementable

## Success Criteria

- All 20 slides generated successfully in both templates
- No markdown artifacts in any slide
- All content types properly rendered
- Images embedded correctly (if generated)
- No Unicode or encoding errors
- Detailed report created with findings
- Fix plan created if issues exist
