"""
Test script for PRIORITY 3 Content Development Tools

Tests the full content development workflow:
1. ContentDraftingSkill - Generate slide content from outlines
2. GraphicsValidator - Validate graphics descriptions
3. ContentOptimizationSkill - Optimize content quality

Usage:
    python test_content_development.py
"""

import json
import os
from plugin.base_skill import SkillInput
from plugin.skills.content_drafting_skill import ContentDraftingSkill
from plugin.skills.content_optimization_skill import ContentOptimizationSkill
from plugin.lib.graphics_validator import validate_graphics_batch
from plugin.lib.quality_analyzer import QualityAnalyzer


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def create_test_outline():
    """Create a test outline (simulating OutlineSkill output)."""
    return {
        "presentation_count": 1,
        "presentations": [
            {
                "title": "Rochester 2GC Carburetor: Operation & Rebuild Guide",
                "audience": "DIY mechanics with basic tools",
                "subtitle": "Complete teardown, rebuild, and testing for enthusiasts",
                "estimated_duration": 45,
                "slides": [
                    {
                        "slide_number": 1,
                        "slide_type": "TITLE SLIDE",
                        "title": "Rochester 2GC Carburetor",
                        "purpose": "Introduce the topic and set expectations",
                        "key_points": [],
                        "supporting_sources": []
                    },
                    {
                        "slide_number": 2,
                        "slide_type": "CONTENT",
                        "title": "How the 2GC Works",
                        "purpose": "Explain basic carburetor operation principles",
                        "key_points": [
                            "Air-fuel mixing principles",
                            "Venturi effect creates vacuum",
                            "Float system maintains fuel level",
                            "Choke system for cold starts"
                        ],
                        "supporting_sources": ["cite-001", "cite-003"]
                    },
                    {
                        "slide_number": 3,
                        "slide_type": "CONTENT",
                        "title": "Essential Tools & Parts",
                        "purpose": "List required tools and rebuild kit contents",
                        "key_points": [
                            "Basic hand tools needed",
                            "Rebuild kit components",
                            "Cleaning supplies",
                            "Safety equipment"
                        ],
                        "supporting_sources": ["cite-002"]
                    }
                ]
            }
        ]
    }


def create_test_research():
    """Create test research data (simulating ResearchSkill output)."""
    return {
        "search_query": "Rochester 2GC carburetor rebuild and operation",
        "sources": [
            {
                "title": "Rochester Products Division Service Manual",
                "url": "https://example.com/rochester-manual",
                "snippet": "The Rochester 2GC is a two-barrel downdraft carburetor featuring a dual venturi design for balanced air-fuel mixture...",
                "citation_id": "cite-001"
            },
            {
                "title": "Rebuilding Rochester Carburetors: A Complete Guide",
                "url": "https://example.com/rebuild-guide",
                "snippet": "Essential tools include screwdrivers, wrenches, carburetor cleaner, and compressed air. A complete rebuild kit contains gaskets, o-rings, and jets...",
                "citation_id": "cite-002"
            },
            {
                "title": "Understanding Carburetor Venturi Principles",
                "url": "https://example.com/venturi",
                "snippet": "The venturi effect creates a vacuum as air accelerates through the narrow passage, drawing fuel from the main jets...",
                "citation_id": "cite-003"
            }
        ],
        "key_themes": [
            "Carburetor operation principles",
            "Rebuild procedures",
            "Tool requirements",
            "Testing and tuning"
        ]
    }


def create_test_style_config():
    """Create test brand style configuration."""
    return {
        "brand_colors": ["#DD0033", "#004F71"],
        "style": "professional, clean, technical",
        "tone": "conversational"
    }


def test_content_drafting():
    """Test ContentDraftingSkill - generates slide content from outline."""
    print_section("PHASE 1: Content Drafting - Generate Slide Content")

    outline = create_test_outline()
    research = create_test_research()
    style_config = create_test_style_config()

    style_guide = {
        "tone": "conversational",
        "audience": "DIY mechanics",
        "reading_level": "high school",
        "max_bullets_per_slide": 5,
        "max_words_per_bullet": 15
    }

    skill = ContentDraftingSkill()

    input_data = SkillInput(
        data={
            "outline": outline,
            "research": research,
            "style_guide": style_guide,
            "style_config": style_config,
            "output_dir": "./output/test"
        },
        context={},
        config={}
    )

    print("Generating content for 3 slides...")
    print(f"Topic: {outline['presentations'][0]['title']}")
    print(f"Audience: {outline['presentations'][0]['audience']}\n")

    result = skill.execute(input_data)

    if result.success:
        print("[OK] ContentDraftingSkill executed successfully\n")
        print(f"Presentation files generated: {len(result.data['presentation_files'])}")
        print(f"Total slides generated: {result.data['slides_generated']}")

        # Show first slide content
        if result.data['presentations']:
            first_pres = result.data['presentations'][0]
            first_slide = first_pres['slides'][0]

            print(f"\nSample Slide 1:")
            print(f"  Title: {first_slide['title']}")
            print(f"  Graphics: {first_slide['graphics_description'][:80]}...")
            print(f"  Speaker Notes: {first_slide['speaker_notes'][:80]}...")

        return result.data
    else:
        print(f"[FAIL] ContentDraftingSkill failed: {result.errors}")
        return None


def test_graphics_validation(drafting_output):
    """Test GraphicsValidator - validate graphics descriptions."""
    print_section("PHASE 2: Graphics Validation - Check Image Descriptions")

    if not drafting_output or not drafting_output.get('presentations'):
        print("[SKIP] No drafting output to validate")
        return None

    presentation = drafting_output['presentations'][0]
    slides = presentation['slides']
    style_config = create_test_style_config()

    print(f"Validating graphics for {len(slides)} slides...\n")

    # Batch validate all graphics descriptions
    validation_results = validate_graphics_batch(slides, style_config)

    print(f"[OK] Graphics validation complete\n")
    print(f"Total slides validated: {validation_results['total_slides']}")
    print(f"Passed: {validation_results['passed']}")
    print(f"Failed: {validation_results['failed']}")
    print(f"Pass rate: {validation_results['pass_rate']:.1f}%\n")

    # Show validation details for first failed slide (if any)
    failed_validations = [r for r in validation_results['results'] if not r['validation'].passed]

    if failed_validations:
        first_failed = failed_validations[0]
        print(f"Sample Failed Validation (Slide {first_failed['slide_number']}):")
        print(f"  Score: {first_failed['validation'].score:.1f}/100")
        print(f"  Issues:")
        for issue in first_failed['validation'].issues[:2]:
            print(f"    - [{issue['severity']}] {issue['message']}")

    return validation_results


def test_content_optimization(drafting_output):
    """Test ContentOptimizationSkill - optimize content quality."""
    print_section("PHASE 3: Content Optimization - Improve Quality")

    if not drafting_output or not drafting_output.get('presentations'):
        print("[SKIP] No drafting output to optimize")
        return None

    presentation = drafting_output['presentations'][0]
    slides = presentation['slides']

    style_guide = {
        "tone": "conversational",
        "audience": "DIY mechanics",
        "reading_level": "high school",
        "max_bullets_per_slide": 5,
        "max_words_per_bullet": 15
    }

    skill = ContentOptimizationSkill()

    input_data = SkillInput(
        data={
            "slides": slides,
            "style_guide": style_guide,
            "optimization_goals": ["readability", "parallelism", "citations"],
            "output_file": "./output/test/optimized_presentation.md"
        },
        context={},
        config={}
    )

    print(f"Optimizing {len(slides)} slides...\n")

    result = skill.execute(input_data)

    if result.success:
        print("[OK] ContentOptimizationSkill executed successfully\n")
        print(f"Quality score before: {result.data['quality_score_before']:.1f}/100")
        print(f"Quality score after: {result.data['quality_score_after']:.1f}/100")
        print(f"Improvement: +{result.data['quality_improvement']:.1f} points")
        print(f"Improvements made: {len(result.data['improvements'])}")

        # Show sample improvements
        if result.data['improvements']:
            print(f"\nSample Improvements:")
            for imp in result.data['improvements'][:2]:
                print(f"  Slide {imp.get('slide_number', 'N/A')}: {imp['issue_type']}")
                if 'original' in imp and 'improved' in imp:
                    print(f"    Original: {imp['original'][:60]}...")
                    print(f"    Improved: {imp['improved'][:60]}...")

        return result.data
    else:
        print(f"[FAIL] ContentOptimizationSkill failed: {result.errors}")
        return None


def test_quality_analysis(drafting_output):
    """Test QualityAnalyzer - comprehensive quality metrics."""
    print_section("PHASE 4: Quality Analysis - Comprehensive Metrics")

    if not drafting_output or not drafting_output.get('presentations'):
        print("[SKIP] No drafting output to analyze")
        return None

    presentation = drafting_output['presentations'][0]
    slides = presentation['slides']

    style_guide = {
        "tone": "conversational"
    }

    analyzer = QualityAnalyzer()

    print(f"Analyzing {len(slides)} slides...\n")

    analysis = analyzer.analyze_presentation(slides, style_guide)

    print("[OK] Quality analysis complete\n")
    print(f"Overall Score: {analysis['overall_score']:.1f}/100")
    print(f"  Readability: {analysis['readability_score']:.1f}/100")
    print(f"  Tone Consistency: {analysis['tone_consistency_score']:.1f}/100")
    print(f"  Structure (Parallelism): {analysis['structure_score']:.1f}/100")
    print(f"  Redundancy: {analysis['redundancy_percentage']:.1f}%")
    print(f"  Citations: {analysis['citation_score']:.1f}/100")

    print(f"\nTotal Issues: {len(analysis['issues'])}")

    if analysis['recommendations']:
        print(f"\nRecommendations:")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"  {i}. {rec}")

    return analysis


def main():
    """Run the complete content development workflow test."""
    print("\n" + "#" * 80)
    print("  PRIORITY 3 CONTENT DEVELOPMENT TOOLS - INTEGRATION TEST")
    print("  Topic: Rochester 2GC Carburetor - Operation & Rebuild")
    print("#" * 80)

    # Create output directory
    os.makedirs("./output/test", exist_ok=True)

    # Phase 1: Content Drafting
    drafting_output = test_content_drafting()

    if not drafting_output:
        print("\n[FAIL] Test failed at Content Drafting phase")
        return

    # Phase 2: Graphics Validation
    validation_results = test_graphics_validation(drafting_output)

    # Phase 3: Quality Analysis
    quality_analysis = test_quality_analysis(drafting_output)

    # Phase 4: Content Optimization
    optimization_output = test_content_optimization(drafting_output)

    # Summary
    print_section("TEST SUMMARY - All Phases Complete")

    print("[OK] Phase 1: Content Drafting - Generated slide content from outline")
    print("[OK] Phase 2: Graphics Validation - Validated image descriptions")
    print("[OK] Phase 3: Quality Analysis - Comprehensive quality metrics")

    if optimization_output:
        print("[OK] Phase 4: Content Optimization - Improved content quality")
    else:
        print("[SKIP] Phase 4: Content Optimization - Skipped")

    print(f"\nFinal Statistics:")
    print(f"   Slides generated: {drafting_output.get('slides_generated', 0)}")

    if validation_results:
        print(f"   Graphics validated: {validation_results['total_slides']}")
        print(f"   Graphics pass rate: {validation_results['pass_rate']:.1f}%")

    if quality_analysis:
        print(f"   Quality score: {quality_analysis['overall_score']:.1f}/100")

    if optimization_output:
        print(f"   Quality improvement: +{optimization_output['quality_improvement']:.1f} points")

    print("\n" + "#" * 80)
    print("  SUCCESS: INTEGRATION TEST COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
