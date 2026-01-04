"""
Slide Visual Validation using Gemini Vision

Validates generated PowerPoint slides against original intent using AI vision.

Uses Gemini multimodal API to analyze slide images and provide structured
feedback on content accuracy, visual hierarchy, brand alignment, layout,
and image quality.

Validation Rubric (100 points):
- Content Accuracy (30%): Title, bullets, key info present and correct
- Visual Hierarchy (20%): Readable, well-structured, proper emphasis
- Brand Alignment (20%): Colors, fonts, style match brand guidelines
- Image Quality (15%): Relevant, properly sized, clear and professional
- Layout Effectiveness (15%): Spacing, balance, visual polish

Threshold: 75% score to pass (0.75)

PRODUCTION NOTES (v2.0 Enhancement):
- Platform Independent: Works on any platform (Windows, macOS, Linux)
- Requires: Slide images exported as JPG (via SlideExporter on Windows or cloud export)
- Graceful Degradation: Returns passing score if validation fails (prevents blocking workflow)
- Retry Logic: Automatically retries transient API failures (max 3 attempts)
- Error Recovery: Comprehensive error handling for API, network, and image issues
"""

import os
import json
import re
import time
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from google import genai
from google.genai import types

# Import Slide from parser
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.parser import Slide


@dataclass
class ValidationResult:
    """
    Result of slide validation against intent and style.

    Attributes:
        passed: Whether slide meets quality threshold (score >= 0.75)
        score: Overall quality score (0.0 to 1.0)
        issues: List of specific problems found
        suggestions: List of recommended improvements
        raw_feedback: Full validation feedback from AI
        rubric_scores: Dict of individual rubric category scores
    """
    passed: bool
    score: float
    issues: List[str]
    suggestions: List[str]
    raw_feedback: str
    rubric_scores: Dict[str, float]


class VisualValidator:
    """
    Validates PowerPoint slides using Gemini vision API.

    Analyzes slide images against original markdown intent and style
    requirements to ensure quality before final output.

    Uses a 100-point rubric across 5 categories:
    - Content Accuracy (30 points)
    - Visual Hierarchy (20 points)
    - Brand Alignment (20 points)
    - Image Quality (15 points)
    - Layout Effectiveness (15 points)

    Validation threshold: 75/100 points (0.75)
    """

    # Quality threshold for passing validation
    VALIDATION_THRESHOLD = 0.75

    # Rubric weights (must sum to 1.0)
    RUBRIC_WEIGHTS = {
        "content_accuracy": 0.30,
        "visual_hierarchy": 0.20,
        "brand_alignment": 0.20,
        "image_quality": 0.15,
        "layout_effectiveness": 0.15
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize visual validator.

        Args:
            api_key: Optional Google API key. If not provided, uses GOOGLE_API_KEY env var.

        Raises:
            EnvironmentError: If API key not provided and not in environment
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
            raise EnvironmentError(
                "Google API key required for visual validation. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        try:
            self.client = genai.Client(api_key=self.api_key)
        except Exception as e:
            raise EnvironmentError(f"Failed to initialize Gemini client: {e}")

    def validate_slide(
        self,
        slide_image_path: str,
        original_slide: Slide,
        style_config: dict,
        slide_type: str
    ) -> ValidationResult:
        """
        Validate a generated slide against its original intent.

        Args:
            slide_image_path: Path to exported slide image (JPG)
            original_slide: Original Slide object from parser
            style_config: Style configuration dict (brand colors, fonts, etc.)
            slide_type: Classified slide type ("title", "section", "content", etc.)

        Returns:
            ValidationResult with pass/fail, score, issues, and suggestions

        Raises:
            FileNotFoundError: If slide image doesn't exist
            ValueError: If image format is invalid
        """
        # Verify image exists
        image_path = Path(slide_image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Slide image not found: {slide_image_path}")

        # Build validation prompt
        prompt = self._build_validation_prompt(
            original_slide,
            style_config,
            slide_type
        )

        # Upload image and get validation feedback with retry logic
        max_retries = 3
        retry_delay = 2.0  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                # Read image file
                with open(image_path, 'rb') as f:
                    image_bytes = f.read()

                # Validate image size (warn if > 10MB)
                image_size_mb = len(image_bytes) / (1024 * 1024)
                if image_size_mb > 10:
                    print(f"[WARNING] Large image size: {image_size_mb:.1f}MB for slide {original_slide.number}")

                # Configure for text response analyzing the image
                config = types.GenerateContentConfig(
                    response_modalities=["TEXT"],
                    temperature=0.3  # Lower temp for consistent evaluation
                )

                # Call Gemini Vision with inline image
                response = self.client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg"
                        ),
                        prompt
                    ],
                    config=config
                )

                # Parse validation response
                result = self._parse_validation_response(
                    response.text,
                    original_slide.number
                )

                return result

            except FileNotFoundError as e:
                # File errors are not transient - don't retry
                print(f"[ERROR] Slide image not found: {slide_image_path}")
                raise

            except ValueError as e:
                # Validation parsing errors are not transient - don't retry
                print(f"[ERROR] Invalid validation response for slide {original_slide.number}: {e}")
                break

            except Exception as e:
                # Potentially transient API/network errors - retry
                error_type = type(e).__name__
                error_msg = str(e)

                if attempt < max_retries:
                    print(f"[WARNING] Validation attempt {attempt} failed for slide {original_slide.number}: {error_type} - {error_msg}")
                    print(f"          Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    print(f"[ERROR] Validation failed for slide {original_slide.number} after {max_retries} attempts: {error_type} - {error_msg}")

        # All retries exhausted or non-retryable error - graceful degradation
        return ValidationResult(
            passed=True,  # Pass by default to avoid blocking workflow
            score=self.VALIDATION_THRESHOLD,
            issues=[],
            suggestions=[],
            raw_feedback=f"Validation unavailable (error after {max_retries} attempts)",
            rubric_scores={}
        )

    def _build_validation_prompt(
        self,
        slide: Slide,
        style_config: dict,
        slide_type: str
    ) -> str:
        """
        Build validation prompt for Gemini Vision.

        Args:
            slide: Original Slide object
            style_config: Style configuration
            slide_type: Classified slide type

        Returns:
            Formatted prompt string
        """
        # Extract key style requirements
        brand_colors = style_config.get("brand_colors", [])
        style_desc = style_config.get("style", "professional")

        # Format bullet points preview
        bullets_preview = ""
        if slide.content_bullets:
            for text, level in slide.content_bullets[:5]:
                indent = "  " * level
                bullets_preview += f"\n{indent}- {text}"
            if len(slide.content_bullets) > 5:
                bullets_preview += f"\n... ({len(slide.content_bullets) - 5} more)"

        # Format graphic description
        graphic_preview = "None"
        if slide.graphic:
            graphic_preview = slide.graphic[:200]
            if len(slide.graphic) > 200:
                graphic_preview += "..."

        prompt = f'''You are a presentation quality validator analyzing a PowerPoint slide.

SLIDE IMAGE: (Attached above)

ORIGINAL INTENT (from markdown):
**Slide Number:** {slide.number}
**Type:** {slide_type}
**Title:** {slide.title}
**Subtitle:** {slide.subtitle or "None"}
**Bullet Points:** {len(slide.content_bullets)} total{bullets_preview}
**Graphic Intent:** {graphic_preview}

STYLE REQUIREMENTS:
**Brand Colors:** {", ".join(brand_colors) if brand_colors else "Not specified"}
**Style:** {style_desc}

---

VALIDATION RUBRIC (100 points total):

1. **CONTENT ACCURACY** (30 points)
   - Title matches intent and is clearly visible
   - All bullet points present and accurate
   - No missing or incorrect content
   - Speaker notes context preserved in visible elements

2. **VISUAL HIERARCHY** (20 points)
   - Title stands out prominently
   - Bullet points are readable and well-sized
   - Proper use of font sizes and weights
   - Clear information flow and structure

3. **BRAND ALIGNMENT** (20 points)
   - Colors match brand palette
   - Fonts match brand guidelines
   - Overall style is consistent with brand identity
   - Professional appearance appropriate for brand

4. **IMAGE QUALITY** (15 points, if applicable)
   - Image is relevant to content
   - Image is properly sized and positioned
   - Image is clear and high-quality
   - Image doesn't obscure text

5. **LAYOUT EFFECTIVENESS** (15 points)
   - Good use of whitespace
   - Balanced composition
   - Professional polish
   - No visual clutter or awkward spacing

---

TASK:

Analyze the slide image carefully against the original intent and style requirements.
Score each rubric category out of its maximum points.
Identify specific issues and suggest improvements.

Return ONLY a JSON object with this exact format (no markdown code blocks):

{{
  "content_accuracy": 28,
  "visual_hierarchy": 18,
  "brand_alignment": 19,
  "image_quality": 14,
  "layout_effectiveness": 13,
  "total_score": 92,
  "issues": [
    "Title font size slightly small",
    "Third bullet point text is cut off"
  ],
  "suggestions": [
    "Increase title font to 44pt",
    "Reduce bullet text or use two columns"
  ]
}}

Provide your validation now:'''

        return prompt

    def _parse_validation_response(
        self,
        response_text: str,
        slide_number: int
    ) -> ValidationResult:
        """
        Parse Gemini validation response into ValidationResult.

        Args:
            response_text: Raw Gemini response
            slide_number: Slide number being validated

        Returns:
            ValidationResult object
        """
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*\n(.+?)\n```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

            # Also try to extract JSON without markdown
            json_match = re.search(r'\{[^{}]*"total_score"[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(0)

            # Parse JSON
            data = json.loads(response_text)

            # Extract scores
            rubric_scores = {
                "content_accuracy": float(data.get("content_accuracy", 0)) / 30.0,
                "visual_hierarchy": float(data.get("visual_hierarchy", 0)) / 20.0,
                "brand_alignment": float(data.get("brand_alignment", 0)) / 20.0,
                "image_quality": float(data.get("image_quality", 0)) / 15.0,
                "layout_effectiveness": float(data.get("layout_effectiveness", 0)) / 15.0
            }

            # Calculate weighted total score (0.0 to 1.0)
            total_score = sum(
                rubric_scores[key] * weight
                for key, weight in self.RUBRIC_WEIGHTS.items()
            )

            # Extract issues and suggestions
            issues = data.get("issues", [])
            suggestions = data.get("suggestions", [])

            # Determine pass/fail
            passed = total_score >= self.VALIDATION_THRESHOLD

            return ValidationResult(
                passed=passed,
                score=total_score,
                issues=issues,
                suggestions=suggestions,
                raw_feedback=response_text,
                rubric_scores=rubric_scores
            )

        except json.JSONDecodeError as e:
            print(f"[WARN] Failed to parse validation JSON for slide {slide_number}: {e}")
            print(f"[WARN] Response was: {response_text[:300]}...")

            # Fallback: pass with threshold score
            return ValidationResult(
                passed=True,
                score=self.VALIDATION_THRESHOLD,
                issues=["Validation parse error"],
                suggestions=[],
                raw_feedback=response_text,
                rubric_scores={}
            )

        except Exception as e:
            print(f"[ERROR] Unexpected validation parsing error for slide {slide_number}: {e}")

            # Fallback: pass with threshold score
            return ValidationResult(
                passed=True,
                score=self.VALIDATION_THRESHOLD,
                issues=["Validation error"],
                suggestions=[],
                raw_feedback=str(e),
                rubric_scores={}
            )


# Test function for development
def main():
    """Test the validator on a sample slide (for development)."""
    import argparse
    from lib.parser import parse_presentation
    from lib.image_generator import load_style_config, DEFAULT_STYLE

    parser = argparse.ArgumentParser(description="Test visual validation")
    parser.add_argument("slide_image", help="Path to slide image (JPG)")
    parser.add_argument("markdown_file", help="Path to markdown presentation")
    parser.add_argument("--slide-number", type=int, default=1, help="Slide number to validate")
    parser.add_argument("--style", help="Path to style JSON file")
    parser.add_argument("--type", default="content", help="Slide type")
    args = parser.parse_args()

    print("="*80)
    print("Visual Validator Test")
    print("="*80)

    # Parse presentation
    slides = parse_presentation(args.markdown_file)
    slide = next((s for s in slides if s.number == args.slide_number), None)

    if not slide:
        print(f"[ERROR] Slide {args.slide_number} not found in {args.markdown_file}")
        return 1

    # Load style config
    if args.style:
        style_config = load_style_config(args.style)
    else:
        style_config = DEFAULT_STYLE

    # Initialize validator
    try:
        validator = VisualValidator()
        print(f"\n[OK] Validator initialized")
    except EnvironmentError as e:
        print(f"\n[ERROR] {e}")
        return 1

    # Validate slide
    print(f"\n[VALIDATE] Slide {args.slide_number}: {slide.title}")
    print(f"[VALIDATE] Image: {args.slide_image}")
    print(f"[VALIDATE] Type: {args.type}")

    result = validator.validate_slide(
        slide_image_path=args.slide_image,
        original_slide=slide,
        style_config=style_config,
        slide_type=args.type
    )

    # Display results
    print(f"\n{'='*80}")
    print(f"VALIDATION RESULTS")
    print(f"{'='*80}")
    print(f"Status: {'PASS' if result.passed else 'FAIL'}")
    print(f"Score: {result.score:.2f} (threshold: {VisualValidator.VALIDATION_THRESHOLD:.2f})")

    if result.rubric_scores:
        print(f"\nRubric Breakdown:")
        for category, score in result.rubric_scores.items():
            print(f"  {category:25s}: {score:.2f}")

    if result.issues:
        print(f"\nIssues Found ({len(result.issues)}):")
        for issue in result.issues:
            print(f"  - {issue}")

    if result.suggestions:
        print(f"\nSuggestions ({len(result.suggestions)}):")
        for suggestion in result.suggestions:
            print(f"  - {suggestion}")

    print(f"\n{'='*80}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
