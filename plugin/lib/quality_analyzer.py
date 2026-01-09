"""
Content quality analysis for presentation slides.

Provides metrics and analysis for:
- Readability (Flesch-Kincaid)
- Tone consistency
- Bullet point parallelism
- Redundancy detection
- Citation completeness

Uses textstat for readability metrics and Claude API for linguistic analysis.
"""

import json
import logging
import re
from typing import Any

from anthropic import APIError, APIConnectionError, RateLimitError

from plugin.lib.claude_client import get_claude_client
from plugin.lib.json_utils import extract_json_from_response


logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """
    Analyze presentation content quality.

    Provides comprehensive quality metrics and identifies improvement opportunities.
    """

    def __init__(self):
        """Initialize quality analyzer."""
        self.client = get_claude_client()

    def analyze_presentation(
        self, slides: list[dict[str, Any]], style_guide: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Perform comprehensive quality analysis on presentation.

        Args:
            slides: List of slide content
            style_guide: Optional style parameters for comparison

        Returns:
            Dictionary with quality metrics and issues:
            {
                "overall_score": float (0-100),
                "readability_score": float,
                "tone_consistency_score": float,
                "structure_score": float,
                "citation_score": float,
                "issues": List[Dict],
                "recommendations": List[str]
            }
        """
        style_guide = style_guide or {}

        # Calculate individual metrics
        readability = self.calculate_readability(slides)
        tone_consistency = self.check_tone_consistency(
            slides, style_guide.get("tone", "professional")
        )
        parallelism = self.check_bullet_parallelism(slides)
        redundancy = self.detect_redundancy(slides)
        citations = self.validate_citations(slides)

        # Collect issues
        issues = []
        issues.extend(readability.get("issues", []))
        issues.extend(tone_consistency.get("issues", []))
        issues.extend(parallelism.get("issues", []))
        issues.extend(redundancy.get("issues", []))
        issues.extend(citations.get("issues", []))

        # Calculate overall score (weighted average)
        overall_score = (
            readability["score"] * 0.20
            + tone_consistency["score"] * 0.20
            + parallelism["score"] * 0.25
            + (100 - redundancy["redundancy_percentage"]) * 0.15
            + citations["score"] * 0.20
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            readability, tone_consistency, parallelism, redundancy, citations
        )

        return {
            "overall_score": round(overall_score, 1),
            "readability_score": readability["score"],
            "tone_consistency_score": tone_consistency["score"],
            "structure_score": parallelism["score"],
            "redundancy_percentage": redundancy["redundancy_percentage"],
            "citation_score": citations["score"],
            "issues": issues,
            "recommendations": recommendations,
            "details": {
                "readability": readability,
                "tone": tone_consistency,
                "structure": parallelism,
                "redundancy": redundancy,
                "citations": citations,
            },
        }

    def calculate_readability(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Calculate readability metrics for presentation content.

        Uses Flesch Reading Ease and approximations when textstat unavailable.

        Args:
            slides: List of slide content

        Returns:
            Readability analysis with score and issues
        """
        # Extract all text content
        all_text = []
        for slide in slides:
            bullets = slide.get("bullets", [])
            all_text.extend(bullets)

            # Also include speaker notes for comprehensive analysis
            notes = slide.get("speaker_notes", "")
            if notes:
                all_text.append(notes)

        combined_text = " ".join(all_text)

        if not combined_text.strip():
            return {"score": 100, "grade_level": "N/A", "issues": [], "metrics": {}}

        # Try to use textstat if available, otherwise use approximations
        try:
            import textstat

            flesch_score = textstat.flesch_reading_ease(combined_text)
            grade_level = textstat.flesch_kincaid_grade(combined_text)
            has_textstat = True
        except ImportError:
            # Approximate Flesch Reading Ease
            flesch_score = self._approximate_flesch_score(combined_text)
            grade_level = self._approximate_grade_level(flesch_score)
            has_textstat = False

        # Interpret score (Flesch Reading Ease scale)
        # 90-100: Very Easy (5th grade)
        # 80-89: Easy (6th grade)
        # 70-79: Fairly Easy (7th grade)
        # 60-69: Standard (8th-9th grade)
        # 50-59: Fairly Difficult (10th-12th grade)
        # 30-49: Difficult (College)
        # 0-29: Very Difficult (College graduate)

        # Target: 60-70 for professional presentations
        issues = []
        if flesch_score < 50:
            issues.append(
                {
                    "type": "readability",
                    "severity": "medium",
                    "message": f"Text is too complex (Flesch score: {flesch_score:.1f}). Simplify language.",
                    "suggestion": "Use shorter sentences and simpler words for better comprehension.",
                }
            )
        elif flesch_score > 80:
            issues.append(
                {
                    "type": "readability",
                    "severity": "low",
                    "message": f"Text may be too simple (Flesch score: {flesch_score:.1f}).",
                    "suggestion": "Consider if the vocabulary matches your audience's expertise level.",
                }
            )

        # Normalize score to 0-100 scale
        # Flesch score 60-70 = optimal (100 points)
        # Deviations reduce score
        if 60 <= flesch_score <= 70:
            normalized_score = 100
        elif flesch_score < 60:
            # Below 60: score decreases
            normalized_score = max(0, 100 - (60 - flesch_score) * 2)
        else:
            # Above 70: slight penalty
            normalized_score = max(70, 100 - (flesch_score - 70))

        return {
            "score": round(normalized_score, 1),
            "flesch_reading_ease": round(flesch_score, 1),
            "grade_level": grade_level if has_textstat else f"~{grade_level}",
            "interpretation": self._interpret_flesch_score(flesch_score),
            "issues": issues,
            "metrics": {
                "using_textstat": has_textstat,
                "total_words": len(combined_text.split()),
            },
        }

    def check_tone_consistency(
        self, slides: list[dict[str, Any]], target_tone: str = "professional"
    ) -> dict[str, Any]:
        """
        Check tone consistency across slides using Claude API.

        Args:
            slides: List of slide content
            target_tone: Target tone (professional, conversational, academic, etc.)

        Returns:
            Tone analysis with consistency score and issues
        """
        # Extract slide content for analysis
        slide_texts = []
        for i, slide in enumerate(slides, 1):
            title = slide.get("title", "")
            bullets = slide.get("bullets", [])
            text = f"Slide {i} - {title}: " + " ".join(bullets)
            slide_texts.append(text)

        combined_text = "\n\n".join(slide_texts[:10])  # Analyze first 10 slides

        if not combined_text.strip():
            return {
                "score": 100,
                "detected_tone": target_tone,
                "consistency": "high",
                "issues": [],
            }

        # Use Claude to analyze tone
        prompt = f"""Analyze the tone of this presentation content.

Target tone: {target_tone}

Content:
{combined_text}

Evaluate:
1. Is the tone consistent throughout?
2. Does it match the target tone ({target_tone})?
3. Are there any tone shifts or inconsistencies?

Return JSON:
{{
  "detected_tone": "primary tone observed",
  "matches_target": true/false,
  "consistency_rating": "high/medium/low",
  "tone_shifts": ["list of any tone inconsistencies"],
  "suggestions": ["how to improve tone consistency"]
}}"""

        system_prompt = """You are an expert editor analyzing presentation tone.
Return valid JSON with your analysis."""

        try:
            response = self.client.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            analysis = extract_json_from_response(response, strict=True)

        except (APIError, APIConnectionError, RateLimitError) as e:
            # API errors - fallback gracefully with logged warning
            logger.warning("Tone analysis API call failed: %s", e)
            return {
                "score": 75,
                "detected_tone": "unknown",
                "consistency": "unknown",
                "issues": [],
                "error": str(e),
            }
        except json.JSONDecodeError as e:
            # JSON parsing failed - fallback gracefully
            logger.warning("Failed to parse tone analysis response: %s", e)
            return {
                "score": 75,
                "detected_tone": "unknown",
                "consistency": "unknown",
                "issues": [],
                "error": f"JSON parse error: {e}",
            }

        # Calculate score
        matches_target = analysis.get("matches_target", True)
        consistency = analysis.get("consistency_rating", "medium")

        score = 100
        if not matches_target:
            score -= 30
        if consistency == "low":
            score -= 30
        elif consistency == "medium":
            score -= 15

        # Create issues from tone shifts
        issues = []
        for shift in analysis.get("tone_shifts", []):
            issues.append(
                {
                    "type": "tone",
                    "severity": "medium" if not matches_target else "low",
                    "message": shift,
                    "suggestion": analysis.get(
                        "suggestions", ["Maintain consistent tone throughout"]
                    )[0],
                }
            )

        return {
            "score": max(0, score),
            "detected_tone": analysis.get("detected_tone", "unknown"),
            "matches_target": matches_target,
            "consistency": consistency,
            "issues": issues,
            "analysis": analysis,
        }

    def check_bullet_parallelism(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Check bullet point grammatical parallelism.

        Args:
            slides: List of slide content

        Returns:
            Parallelism analysis with score and issues
        """
        issues = []
        total_slides_with_bullets = 0
        parallel_slides = 0

        for slide_idx, slide in enumerate(slides, 1):
            bullets = slide.get("bullets", [])

            if len(bullets) < 2:
                continue  # Need at least 2 bullets to check parallelism

            total_slides_with_bullets += 1

            # Check if bullets follow parallel structure
            is_parallel, issue = self._check_parallel_structure(bullets)

            if is_parallel:
                parallel_slides += 1
            else:
                issues.append(
                    {
                        "type": "structure",
                        "severity": "medium",
                        "slide_number": slide_idx,
                        "message": f"Slide {slide_idx}: Bullets not parallel - {issue}",
                        "suggestion": "Ensure all bullets use the same grammatical structure (e.g., all start with verbs, all start with nouns, etc.)",
                    }
                )

        # Calculate score
        if total_slides_with_bullets == 0:
            score = 100
        else:
            score = (parallel_slides / total_slides_with_bullets) * 100

        return {
            "score": round(score, 1),
            "slides_analyzed": total_slides_with_bullets,
            "parallel_slides": parallel_slides,
            "issues": issues,
        }

    def detect_redundancy(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Detect redundant concepts across slides.

        Args:
            slides: List of slide content

        Returns:
            Redundancy analysis with percentage and duplicate concepts
        """
        # Extract all bullets
        all_bullets = []
        bullet_sources = []  # Track which slide each bullet came from

        for slide_idx, slide in enumerate(slides, 1):
            bullets = slide.get("bullets", [])
            for bullet in bullets:
                all_bullets.append(bullet.lower().strip())
                bullet_sources.append(slide_idx)

        if not all_bullets:
            return {"redundancy_percentage": 0, "duplicates_found": 0, "issues": []}

        # Simple similarity detection (exact matches and very similar)
        duplicates = []
        checked = set()

        for i in range(len(all_bullets)):
            if i in checked:
                continue

            similar_bullets = [i]

            for j in range(i + 1, len(all_bullets)):
                if j in checked:
                    continue

                # Check exact match
                if (
                    all_bullets[i] == all_bullets[j]
                    or self._similarity_score(all_bullets[i], all_bullets[j]) > 0.8
                ):
                    similar_bullets.append(j)
                    checked.add(j)

            if len(similar_bullets) > 1:
                duplicates.append(
                    {
                        "text": all_bullets[i],
                        "slides": [bullet_sources[idx] for idx in similar_bullets],
                        "count": len(similar_bullets),
                    }
                )

        redundancy_percentage = (
            (len(checked) / len(all_bullets) * 100) if all_bullets else 0
        )

        # Create issues
        issues = []
        for dup in duplicates:
            issues.append(
                {
                    "type": "redundancy",
                    "severity": "low" if dup["count"] == 2 else "medium",
                    "message": f'Duplicate concept across slides {", ".join(map(str, dup["slides"]))}: "{dup["text"][:50]}..."',
                    "suggestion": "Consider consolidating or removing redundant content.",
                }
            )

        return {
            "redundancy_percentage": round(redundancy_percentage, 1),
            "duplicates_found": len(duplicates),
            "duplicate_concepts": duplicates[:5],  # Show first 5
            "issues": issues,
        }

    def validate_citations(self, slides: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate citation completeness.

        Args:
            slides: List of slide content

        Returns:
            Citation analysis with score and issues
        """
        total_slides = len(slides)
        slides_with_citations = 0
        missing_citations = []

        for slide_idx, slide in enumerate(slides, 1):
            slide_type = slide.get("outline", {}).get("slide_type", "CONTENT")

            # Skip title slides and section dividers
            if slide_type in ["TITLE SLIDE", "SECTION DIVIDER"]:
                continue

            citations = slide.get("citations", [])

            if citations and len(citations) > 0:
                slides_with_citations += 1
            else:
                # Check if slide makes claims that should be cited
                bullets = slide.get("bullets", [])
                if len(bullets) > 0:  # Content slides should have citations
                    missing_citations.append(slide_idx)

        # Calculate score
        content_slides = total_slides - len(
            [
                s
                for s in slides
                if s.get("outline", {}).get("slide_type")
                in ["TITLE SLIDE", "SECTION DIVIDER"]
            ]
        )

        if content_slides == 0:
            score = 100
        else:
            score = (slides_with_citations / content_slides) * 100

        # Create issues
        issues = []
        for slide_num in missing_citations:
            issues.append(
                {
                    "type": "citation",
                    "severity": "medium",
                    "slide_number": slide_num,
                    "message": f"Slide {slide_num}: Missing citations for claims",
                    "suggestion": "Add citations to support factual claims and data.",
                }
            )

        return {
            "score": round(score, 1),
            "total_slides": total_slides,
            "content_slides": content_slides,
            "slides_with_citations": slides_with_citations,
            "missing_citations": missing_citations,
            "issues": issues,
        }

    # Helper methods

    def _approximate_flesch_score(self, text: str) -> float:
        """Approximate Flesch Reading Ease without textstat."""
        words = text.split()
        sentences = re.split(r"[.!?]+", text)
        sentences = [s for s in sentences if s.strip()]

        if not sentences or not words:
            return 60.0  # Default middle score

        avg_sentence_length = len(words) / len(sentences)
        syllables = sum(self._count_syllables(word) for word in words)
        avg_syllables_per_word = syllables / len(words)

        # Flesch Reading Ease formula
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        return max(0, min(100, score))

    def _count_syllables(self, word: str) -> int:
        """Approximate syllable count."""
        word = word.lower()
        vowels = "aeiouy"
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent e
        if word.endswith("e"):
            syllable_count -= 1

        return max(1, syllable_count)

    def _approximate_grade_level(self, flesch_score: float) -> int:
        """Convert Flesch score to approximate grade level."""
        if flesch_score >= 90:
            return 5
        elif flesch_score >= 80:
            return 6
        elif flesch_score >= 70:
            return 7
        elif flesch_score >= 60:
            return 9
        elif flesch_score >= 50:
            return 11
        elif flesch_score >= 30:
            return 13
        else:
            return 16

    def _interpret_flesch_score(self, score: float) -> str:
        """Interpret Flesch Reading Ease score."""
        if score >= 90:
            return "Very Easy (5th grade)"
        elif score >= 80:
            return "Easy (6th grade)"
        elif score >= 70:
            return "Fairly Easy (7th grade)"
        elif score >= 60:
            return "Standard (8th-9th grade)"
        elif score >= 50:
            return "Fairly Difficult (10th-12th grade)"
        elif score >= 30:
            return "Difficult (College)"
        else:
            return "Very Difficult (College graduate)"

    def _check_parallel_structure(self, bullets: list[str]) -> tuple[bool, str]:
        """
        Check if bullets follow parallel grammatical structure.

        Returns:
            (is_parallel, issue_description)
        """
        if len(bullets) < 2:
            return True, ""

        # Extract first word of each bullet (remove punctuation)
        first_words = []
        for bullet in bullets:
            words = bullet.strip().split()
            if words:
                first_word = re.sub(r"[^\w\s]", "", words[0]).lower()
                first_words.append(first_word)

        if len(first_words) < 2:
            return True, ""

        # Check if all start with similar patterns
        # Common patterns: all verbs, all nouns, all gerunds (-ing)

        # Check for gerunds
        gerunds = sum(1 for word in first_words if word.endswith("ing"))
        if gerunds > 0 and gerunds != len(first_words):
            return (
                False,
                f"{gerunds}/{len(first_words)} start with -ing verbs (gerunds)",
            )

        # Check for verb-like patterns (common verbs)
        common_verbs = {
            "provides",
            "enables",
            "allows",
            "creates",
            "supports",
            "ensures",
            "maintains",
            "includes",
            "features",
            "offers",
            "requires",
        }
        verbs = sum(1 for word in first_words if word in common_verbs)
        if verbs > 0 and verbs != len(first_words):
            return False, f"{verbs}/{len(first_words)} start with action verbs"

        # If we can't definitively say it's not parallel, assume it is
        return True, ""

    def _similarity_score(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings (0-1).

        Uses simple word overlap metric.
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _generate_recommendations(
        self,
        readability: dict,
        tone: dict,
        parallelism: dict,
        redundancy: dict,
        citations: dict,
    ) -> list[str]:
        """Generate actionable recommendations from analysis results."""
        recommendations = []

        # Readability recommendations
        if readability["score"] < 70:
            recommendations.append(
                "Improve readability: Use shorter sentences and simpler vocabulary."
            )

        # Tone recommendations
        if not tone.get("matches_target", True):
            recommendations.append(
                f"Align tone with target ({tone.get('detected_tone', 'professional')} tone detected)."
            )

        # Parallelism recommendations
        if parallelism["score"] < 80:
            recommendations.append(
                "Improve bullet point parallelism: Ensure all bullets use the same grammatical structure."
            )

        # Redundancy recommendations
        if redundancy["redundancy_percentage"] > 20:
            recommendations.append(
                "Reduce redundancy: Consolidate or remove duplicate concepts across slides."
            )

        # Citation recommendations
        if citations["score"] < 80:
            recommendations.append(
                "Add citations: Ensure all factual claims are properly sourced."
            )

        return recommendations


# Convenience function
def get_quality_analyzer() -> QualityAnalyzer:
    """Get configured quality analyzer instance."""
    return QualityAnalyzer()
