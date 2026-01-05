"""
Intelligent slide type classification using semantic content analysis.

Uses a hybrid approach combining:
- Rule-based classification for obvious cases (fast, ~80% of slides)
- Gemini-powered semantic analysis for ambiguous cases (intelligent, ~20%)

Classifies slides into one of 5 template types:
- title: Cover slide with logo, centered title, subtitle
- section: Section divider with single heading on colored background
- content: Text-heavy slide with bullets (no image placeholder)
- image: Visual-first slide with title and full-width image
- text_image: Balanced slide with left text panel + right image panel
"""

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass


try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

# Import Slide from parser (relative import)
from .parser import Slide


@dataclass
class TypeClassification:
    """Result of slide type classification."""

    slide_type: str  # "title", "section", "content", "image", "text_image"
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Explanation of why this type was chosen
    template_method: str  # Template method name: "add_title_slide", etc.


class SlideTypeClassifier:
    """
    Classifies slides into optimal template types using hybrid approach.

    Strategy:
    1. Rule-based classification for ~80% of slides (fast, deterministic)
    2. Gemini AI analysis for ~20% of ambiguous slides (intelligent)

    Template Types:
    - title: Main presentation cover (typically slide 1)
    - section: Section dividers between major topics
    - content: Text-heavy slides with bullets, no images
    - image: Visual-first slides with full-width images
    - text_image: Balanced slides with text panel + image panel
    """

    # Mapping of slide types to template methods
    SLIDE_TYPES = {
        "title": "add_title_slide",
        "section": "add_section_break",
        "content": "add_content_slide",
        "image": "add_image_slide",
        "text_image": "add_text_and_image_slide",
    }

    def __init__(self, api_key: str | None = None):
        """
        Initialize classifier.

        Args:
            api_key: Optional Google API key. If not provided, uses GOOGLE_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize Gemini client: {e}")
                print("[WARN] Classification will use rule-based approach only")

    def classify_slide(self, slide: Slide) -> TypeClassification:
        """
        Classify a single slide into optimal template type.

        Decision process:
        1. Try rule-based classification (fast path)
        2. If ambiguous, use Gemini semantic analysis
        3. Return classification with confidence score

        Args:
            slide: Slide object from parser

        Returns:
            TypeClassification with type, confidence, reasoning, and method name
        """
        # Try rule-based first (handles ~80% of cases)
        rule_result = self._rule_based_classify(slide)

        if rule_result is not None:
            return rule_result

        # Ambiguous case: use Gemini analysis if available
        if self.client:
            try:
                return self._gemini_classify(slide)
            except Exception as e:
                print(
                    f"[WARN] Gemini classification failed for slide {slide.number}: {e}"
                )
                print("[WARN] Falling back to default content slide")

        # Final fallback: content slide (safest default)
        return TypeClassification(
            slide_type="content",
            confidence=0.5,
            reasoning="Fallback: ambiguous slide, Gemini unavailable",
            template_method=self.SLIDE_TYPES["content"],
        )

    def _rule_based_classify(self, slide: Slide) -> TypeClassification | None:
        """
        Fast rule-based classification for obvious cases.

        Rules (in priority order):
        1. Explicit type markers in slide_type field
        2. Position heuristics (slide 1 = title)
        3. Content structure analysis

        Returns:
            TypeClassification if confident, None if ambiguous
        """
        slide_type_upper = slide.slide_type.upper()

        # Rule 1: Explicit type markers
        if "TITLE" in slide_type_upper and slide.number == 1:
            return TypeClassification(
                slide_type="title",
                confidence=1.0,
                reasoning="Explicit TITLE marker on slide 1",
                template_method=self.SLIDE_TYPES["title"],
            )

        if any(
            marker in slide_type_upper
            for marker in ["SECTION", "DIVIDER", "BREAK", "Q&A", "Q & A"]
        ):
            return TypeClassification(
                slide_type="section",
                confidence=0.95,
                reasoning=f"Explicit section marker: {slide.slide_type}",
                template_method=self.SLIDE_TYPES["section"],
            )

        if any(
            marker in slide_type_upper
            for marker in ["ARCHITECTURE", "DIAGRAM", "IMAGE"]
        ):
            # Check if it actually has a graphic description
            if slide.graphic:
                return TypeClassification(
                    slide_type="image",
                    confidence=0.95,
                    reasoning=f"Explicit image marker + graphic present: {slide.slide_type}",
                    template_method=self.SLIDE_TYPES["image"],
                )

        # Rule 2: Position heuristics
        if slide.number == 1 and not slide.content_bullets:
            return TypeClassification(
                slide_type="title",
                confidence=0.9,
                reasoning="First slide with no content = title slide",
                template_method=self.SLIDE_TYPES["title"],
            )

        # Rule 3: Content structure analysis
        has_graphic = bool(slide.graphic and slide.graphic.strip())
        has_bullets = bool(slide.content_bullets)
        bullet_count = len(slide.content_bullets) if has_bullets else 0

        # No content at all → section break
        if not has_graphic and not has_bullets:
            return TypeClassification(
                slide_type="section",
                confidence=0.85,
                reasoning="No content or graphic = section divider",
                template_method=self.SLIDE_TYPES["section"],
            )

        # Graphic but no bullets → image slide
        if has_graphic and not has_bullets:
            return TypeClassification(
                slide_type="image",
                confidence=0.9,
                reasoning="Has graphic, no bullets = visual-first image slide",
                template_method=self.SLIDE_TYPES["image"],
            )

        # Bullets but no graphic → content slide
        if has_bullets and not has_graphic:
            return TypeClassification(
                slide_type="content",
                confidence=0.9,
                reasoning="Has bullets, no graphic = text-only content slide",
                template_method=self.SLIDE_TYPES["content"],
            )

        # Both bullets and graphic → likely text_image, but check bullet count
        if has_bullets and has_graphic:
            # Few bullets (1-5) + graphic = balanced text_image
            if bullet_count >= 1 and bullet_count <= 5:
                return TypeClassification(
                    slide_type="text_image",
                    confidence=0.85,
                    reasoning=f"{bullet_count} bullets + graphic = balanced text+image slide",
                    template_method=self.SLIDE_TYPES["text_image"],
                )

            # Many bullets (6+) + graphic = ambiguous (could be content with decorative image)
            # Return None to trigger Gemini analysis
            return None

        # Ambiguous case
        return None

    def _gemini_classify(self, slide: Slide) -> TypeClassification:
        """
        Use Gemini API for semantic classification of ambiguous slides.

        Constructs a detailed prompt with:
        - Slide content (title, subtitle, bullets, graphic description)
        - Available template types with descriptions
        - Request for JSON classification with confidence + reasoning

        Args:
            slide: Slide object to classify

        Returns:
            TypeClassification from Gemini analysis
        """
        # Build prompt
        prompt = self._build_classification_prompt(slide)

        # Configure for text-only response
        config = types.GenerateContentConfig(
            response_modalities=["TEXT"],
            temperature=0.3,  # Lower temp for consistent classification
        )

        # Call Gemini
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",  # Fast model for classification
            contents=prompt,
            config=config,
        )

        # Parse JSON response
        return self._parse_classification_response(response.text, slide.number)

    def _build_classification_prompt(self, slide: Slide) -> str:
        """
        Build Gemini classification prompt.

        Args:
            slide: Slide to classify

        Returns:
            Prompt string
        """
        # Format bullet points for display
        bullet_preview = ""
        if slide.content_bullets:
            bullets_to_show = slide.content_bullets[:5]  # Show first 5
            for text, level in bullets_to_show:
                indent = "  " * level
                bullet_preview += f"\n{indent}- {text}"
            if len(slide.content_bullets) > 5:
                bullet_preview += (
                    f"\n... ({len(slide.content_bullets) - 5} more bullets)"
                )

        # Format graphic description
        graphic_preview = "None"
        if slide.graphic:
            graphic_preview = slide.graphic[:300]  # First 300 chars
            if len(slide.graphic) > 300:
                graphic_preview += "..."

        prompt = f"""You are a presentation design expert classifying slides into optimal templates.

AVAILABLE TEMPLATE TYPES:

1. **TITLE** - Cover slide with logo, main title, subtitle
   - Use for: Presentation opening, main title page
   - Layout: Branded background, centered large title, subtitle below
   - Typically used once at the beginning

2. **SECTION** - Section divider with single heading
   - Use for: Transitioning between major topics, section breaks
   - Layout: Colored background, large centered heading only
   - No bullets or detailed content

3. **CONTENT** - Text-heavy slide with bulleted content
   - Use for: Lists, explanations, detailed content
   - Layout: White background, title at top, bulleted text below
   - NO image placeholder - pure text

4. **IMAGE** - Visual-first slide with full-width image
   - Use for: Diagrams, architecture, showcase visuals
   - Layout: White background, title at top, large image filling most of slide
   - Minimal or no text content

5. **TEXT_IMAGE** - Balanced slide with text panel + image panel
   - Use for: Insights with supporting visuals, comparisons, examples
   - Layout: Left panel with bullets (50%), right panel with image (50%)
   - Best for 3-5 bullet points + relevant graphic

---

SLIDE TO CLASSIFY:

**Slide Number:** {slide.number}
**Declared Type:** {slide.slide_type}
**Title:** {slide.title}
**Subtitle:** {slide.subtitle or "None"}
**Bullet Points:** {len(slide.content_bullets)} total{bullet_preview}
**Graphic Description:** {graphic_preview}

---

TASK:

Analyze the slide content and classify it into ONE of the 5 template types above.

Consider:
- What is the primary purpose of this slide?
- Is it introducing a topic, dividing sections, presenting information, showing a visual, or combining text and visual?
- What layout would best serve the content?

Return ONLY a JSON object with this exact format (no markdown code blocks, no extra text):

{{
  "type": "title|section|content|image|text_image",
  "confidence": 0.95,
  "reasoning": "This slide has 4 bullet points and a chart description. The balanced content suggests TEXT_IMAGE layout for side-by-side comparison."
}}

Provide your classification now:"""

        return prompt

    def _parse_classification_response(
        self, response_text: str, slide_number: int
    ) -> TypeClassification:
        """
        Parse Gemini JSON response into TypeClassification.

        Handles:
        - JSON extraction from markdown code blocks
        - Malformed JSON (fallback to content slide)
        - Missing fields (provide defaults)

        Args:
            response_text: Raw Gemini response
            slide_number: Slide number (for logging)

        Returns:
            TypeClassification
        """
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```json\s*\n(.+?)\n```", response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Also try to extract JSON without markdown
            json_match = re.search(r'\{[^{}]*"type"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            # Parse JSON
            data = json.loads(response_text)

            slide_type = data.get("type", "content").lower()  # Normalize to lowercase
            confidence = float(data.get("confidence", 0.7))
            reasoning = data.get("reasoning", "Gemini classification")

            # Validate slide_type
            if slide_type not in self.SLIDE_TYPES:
                print(
                    f"[WARN] Invalid slide type from Gemini: {slide_type}. Using 'content'."
                )
                slide_type = "content"
                confidence = 0.5

            return TypeClassification(
                slide_type=slide_type,
                confidence=confidence,
                reasoning=f"Gemini AI: {reasoning}",
                template_method=self.SLIDE_TYPES[slide_type],
            )

        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse Gemini JSON for slide {slide_number}: {e}")
            print(f"[WARN] Response was: {response_text[:200]}...")
            return TypeClassification(
                slide_type="content",
                confidence=0.5,
                reasoning="Fallback: JSON parse error",
                template_method=self.SLIDE_TYPES["content"],
            )
        except Exception as e:
            print(
                f"[WARN] Unexpected error parsing Gemini response for slide {slide_number}: {e}"
            )
            return TypeClassification(
                slide_type="content",
                confidence=0.5,
                reasoning="Fallback: parsing error",
                template_method=self.SLIDE_TYPES["content"],
            )

    def classify_all_slides(
        self,
        slides: list[Slide],
        callback: Callable[[int, TypeClassification], None] | None = None,
    ) -> dict[int, TypeClassification]:
        """
        Classify all slides in a presentation.

        Args:
            slides: List of Slide objects
            callback: Optional callback(slide_number, classification) for progress updates

        Returns:
            Dict mapping slide numbers to TypeClassification objects
        """
        classifications = {}

        for slide in slides:
            classification = self.classify_slide(slide)
            classifications[slide.number] = classification

            if callback:
                callback(slide.number, classification)

        return classifications


# Convenience function for command-line testing
def main():
    """Test the classifier on sample slides (for development)."""
    import argparse

    parser = argparse.ArgumentParser(description="Test slide type classification")
    parser.add_argument("markdown_file", help="Path to presentation markdown file")
    args = parser.parse_args()

    from plugin.lib.presentation.parser import parse_presentation

    # Parse slides
    slides = parse_presentation(args.markdown_file)

    # Initialize classifier
    classifier = SlideTypeClassifier()

    # Classify all slides
    print(f"\nClassifying {len(slides)} slides...\n")
    print("=" * 80)

    for slide in slides:
        classification = classifier.classify_slide(slide)

        print(f"\nSlide {slide.number}: {slide.title[:60]}")
        print(f"  Declared Type: {slide.slide_type}")
        print(f"  -> Classified As: {classification.slide_type}")
        print(f"  -> Confidence: {classification.confidence:.2f}")
        print(f"  -> Method: {classification.template_method}")
        print(f"  -> Reasoning: {classification.reasoning}")

    print("\n" + "=" * 80)
    print("\nClassification complete!")


if __name__ == "__main__":
    main()
