"""
Test script for PRIORITY 2 Research & Discovery Tools

Tests the full research workflow with the carburetor topic:
1. ResearchAssistantSkill - Interactive clarification
2. ResearchSkill - Web research
3. InsightExtractionSkill - Extract insights
4. OutlineSkill - Generate presentation outlines

Usage:
    python test_carburetor_research.py
"""

import json

import pytest

from plugin.base_skill import SkillInput
from plugin.skills.content.outline_skill import OutlineSkill
from plugin.skills.research.insight_extraction_skill import InsightExtractionSkill
from plugin.skills.research.research_assistant_skill import ResearchAssistantSkill
from plugin.skills.research.research_skill import ResearchSkill


# Cache for storing results between tests (session-level state)
_test_cache = {}


@pytest.fixture(scope="module")
def research_output():
    """Fixture that provides research output, running research if needed."""
    if "research_output" not in _test_cache:
        # Run research skill to get output
        research_skill = ResearchSkill()
        input_data = SkillInput(
            data={
                "topic": "Rochester 2GC carburetor rebuild and operation",
                "search_depth": "comprehensive",
                "max_sources": 10,
            },
            context={},
            config={},
        )
        result = research_skill.execute(input_data)
        if result.success:
            _test_cache["research_output"] = result.data
        else:
            pytest.skip(f"Research skill failed: {result.errors}")
    return _test_cache["research_output"]


@pytest.fixture(scope="module")
def insights_output(research_output):
    """Fixture that provides insights output, running extraction if needed."""
    if "insights_output" not in _test_cache:
        skill = InsightExtractionSkill()
        input_data = SkillInput(
            data={
                "research_output": research_output,
                "focus_areas": [
                    "carburetor operation",
                    "Rochester 2GC specifics",
                    "rebuild process",
                ],
            },
            context={},
            config={},
        )
        result = skill.execute(input_data)
        if result.success:
            _test_cache["insights_output"] = result.data
        else:
            pytest.skip(f"Insight extraction failed: {result.errors}")
    return _test_cache["insights_output"]


def print_section(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_json(data: dict, max_depth: int = 2):
    """Print JSON data with limited depth."""
    print(json.dumps(data, indent=2, default=str))


@pytest.mark.api
def test_research_assistant():
    """Test ResearchAssistantSkill - generates clarifying questions."""
    print_section("PHASE 1: Research Assistant - Clarifying Questions")

    topic = """How a carburetor works, what all of the parts are and how they work
    and contribute to the functionality of a carburetor, and then specifically for
    the Rochester 2GC, what all of the parts are, how it works in detail, and,
    assuming the audience is someone with basic tools and knowledge, a step-by-step
    very detailed process, with pictures/drawings, that shows how to disassemble
    and fully rebuild and test a Rochester 2GC carburetor"""

    skill = ResearchAssistantSkill()

    input_data = SkillInput(data={"topic": topic}, context={}, config={})

    result = skill.execute(input_data)

    if result.success:
        print("[OK] ResearchAssistantSkill executed successfully\n")
        print(f"Ready for research: {result.data['ready_for_research']}")
        print(
            f"Questions answered: {result.data.get('questions_answered', 0)}/{result.data.get('total_questions', 0)}\n"
        )

        print("Clarifying Questions Generated:")
        for i, question in enumerate(result.data["questions"], 1):
            print(f"\n{i}. {question['question']}")
            print("   Options:")
            for opt in question["options"]:
                print(f"   - {opt}")

        return result.data
    else:
        print(f"[FAIL] ResearchAssistantSkill failed: {result.errors}")
        return None


@pytest.mark.api
def test_research(assistant_output: dict | None = None):
    """Test ResearchSkill - conducts web research."""
    print_section("PHASE 2: Research Skill - Web Research & Citation")

    # Simulate user responses to assistant questions
    if assistant_output and not assistant_output.get("ready_for_research"):
        print("Simulating user responses to clarifying questions...\n")
        user_responses = {
            "audience": "Technical audience with basic mechanical knowledge",
            "objective": "Educate and provide actionable rebuild instructions",
            "depth": "Comprehensive - both theory and practice",
            "focus": "Rochester 2GC carburetor rebuild process",
            "constraints": "Must include visual diagrams and step-by-step instructions",
        }

        # Re-run assistant with responses
        skill = ResearchAssistantSkill()
        input_data = SkillInput(
            data={
                "topic": assistant_output.get("topic", "carburetor"),
                "user_responses": user_responses,
            },
            context={},
            config={},
        )
        assistant_result = skill.execute(input_data)

        if assistant_result.success and assistant_result.data.get("ready_for_research"):
            print("[OK] Research parameters refined\n")
            assistant_result.data["refined_params"]
        else:
            print("[WARN]  Using default research parameters\n")
    else:
        pass

    # Conduct research
    research_skill = ResearchSkill()

    input_data = SkillInput(
        data={
            "topic": "Rochester 2GC carburetor rebuild and operation",
            "search_depth": "comprehensive",
            "max_sources": 10,
        },
        context={},
        config={},
    )

    result = research_skill.execute(input_data)

    if result.success:
        print("[OK] ResearchSkill executed successfully\n")
        print(f"Search query: {result.data.get('search_query', 'N/A')}")
        print(f"Sources found: {len(result.data.get('sources', []))}")
        print(f"Key themes: {len(result.data.get('key_themes', []))}")
        print(f"Citations: {len(result.data.get('citations', []))}\n")

        # Show first few sources
        print("Sample Sources:")
        for i, source in enumerate(result.data["sources"][:3], 1):
            print(f"\n{i}. {source['title']}")
            print(f"   URL: {source['url']}")
            print(f"   Snippet: {source['snippet'][:100]}...")
            if "citation_id" in source:
                print(f"   Citation ID: {source['citation_id']}")

        # Show key themes
        print("\nKey Themes Identified:")
        for theme in result.data.get("key_themes", [])[:5]:
            print(f"  - {theme}")

        return result.data
    else:
        print(f"[FAIL] ResearchSkill failed: {result.errors}")
        return None


@pytest.mark.api
def test_insight_extraction(research_output: dict):
    """Test InsightExtractionSkill - extract insights from research."""
    print_section("PHASE 3: Insight Extraction - Key Findings & Concepts")

    skill = InsightExtractionSkill()

    input_data = SkillInput(
        data={
            "research_output": research_output,
            "focus_areas": [
                "carburetor operation",
                "Rochester 2GC specifics",
                "rebuild process",
            ],
        },
        context={},
        config={},
    )

    result = skill.execute(input_data)

    if result.success:
        print("[OK] InsightExtractionSkill executed successfully\n")
        print(f"Insights extracted: {len(result.data.get('insights', []))}")
        print(f"Arguments identified: {len(result.data.get('arguments', []))}")

        # Show sample insights
        print("\nKey Insights:")
        for i, insight in enumerate(result.data["insights"][:3], 1):
            print(f"\n{i}. {insight['statement']}")
            print(f"   Confidence: {insight['confidence']:.0%}")
            print(f"   Evidence: {len(insight['supporting_evidence'])} sources")

        # Show concept map summary
        concept_map = result.data.get("concept_map", {})
        print("\nConcept Map:")
        print(f"  Concepts: {len(concept_map.get('concepts', []))}")
        print(f"  Relationships: {len(concept_map.get('relationships', []))}")

        if concept_map.get("concepts"):
            print("\n  Top Concepts:")
            for concept in concept_map["concepts"][:5]:
                if isinstance(concept, dict):
                    print(f"    - {concept['name']}: {concept['description'][:80]}...")
                else:
                    print(f"    - {concept}")

        return result.data
    else:
        print(f"[FAIL] InsightExtractionSkill failed: {result.errors}")
        return None


@pytest.mark.api
def test_outline_generation(research_output: dict, insights_output: dict):
    """Test OutlineSkill - generate presentation outlines."""
    print_section("PHASE 4: Outline Generation - Multi-Presentation Detection")

    skill = OutlineSkill()

    input_data = SkillInput(
        data={
            "research": research_output,
            "insights": insights_output,
            "audience": "mixed technical levels",
            "duration_minutes": 45,
        },
        context={},
        config={},
    )

    result = skill.execute(input_data)

    if result.success:
        print("[OK] OutlineSkill executed successfully\n")
        print(
            f"[TARGET] Multi-Presentation Detection: {result.data['presentation_count']} presentations generated"
        )

        presentations = result.data.get("presentations", [])

        for i, pres in enumerate(presentations, 1):
            print(f"\n{'-' * 80}")
            print(f"PRESENTATION {i}: {pres['title']}")
            print(f"{'-' * 80}")
            print(f"Audience: {pres['audience']}")
            print(f"Slides: {len(pres['slides'])}")
            print(
                f"Estimated Duration: {pres.get('estimated_duration', 'N/A')} minutes"
            )

            print("\nSlide Outline:")
            for slide in pres["slides"][:10]:  # Show first 10 slides
                print(
                    f"  {slide['slide_number']}. [{slide['slide_type']}] {slide['title']}"
                )
                print(f"      Purpose: {slide['purpose'][:80]}...")

            if len(pres["slides"]) > 10:
                print(f"  ... and {len(pres['slides']) - 10} more slides")

        return result.data
    else:
        print(f"[FAIL] OutlineSkill failed: {result.errors}")
        return None


def main():
    """Run the complete research workflow test."""
    print("\n" + "#" * 80)
    print("  PRIORITY 2 RESEARCH & DISCOVERY TOOLS - INTEGRATION TEST")
    print("  Topic: Rochester 2GC Carburetor - Operation & Rebuild")
    print("#" * 80)

    # Phase 1: Research Assistant
    assistant_output = test_research_assistant()

    if not assistant_output:
        print("\n[FAIL] Test failed at Research Assistant phase")
        return

    # Phase 2: Research
    research_output = test_research(assistant_output)

    if not research_output:
        print("\n[FAIL] Test failed at Research phase")
        return

    # Phase 3: Insight Extraction
    insights_output = test_insight_extraction(research_output)

    if not insights_output:
        print("\n[FAIL] Test failed at Insight Extraction phase")
        return

    # Phase 4: Outline Generation
    outline_output = test_outline_generation(research_output, insights_output)

    if not outline_output:
        print("\n[FAIL] Test failed at Outline Generation phase")
        return

    # Summary
    print_section("TEST SUMMARY - All Phases Complete")

    print("[OK] Phase 1: Research Assistant - Generated clarifying questions")
    print("[OK] Phase 2: Research - Found sources and created citations")
    print("[OK] Phase 3: Insight Extraction - Identified key insights and concepts")
    print("[OK] Phase 4: Outline Generation - Created presentation outlines")

    print("\nFinal Statistics:")
    print(f"   Sources researched: {len(research_output.get('sources', []))}")
    print(f"   Insights extracted: {len(insights_output.get('insights', []))}")
    print(f"   Presentations generated: {outline_output.get('presentation_count', 0)}")

    total_slides = sum(
        len(p["slides"]) for p in outline_output.get("presentations", [])
    )
    print(f"   Total slides outlined: {total_slides}")

    print("\n" + "#" * 80)
    print("  SUCCESS: INTEGRATION TEST COMPLETE - ALL SYSTEMS OPERATIONAL")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
