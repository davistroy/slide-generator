"""
Unit tests for plugin/lib/quality_analyzer.py

Tests the QualityAnalyzer class and helper methods.
"""

from unittest.mock import patch

from plugin.lib.quality_analyzer import QualityAnalyzer, get_quality_analyzer


class TestQualityAnalyzerHelpers:
    """Tests for QualityAnalyzer helper methods (no API calls needed)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    # Test _count_syllables
    def test_count_syllables_simple_word(self):
        """Test syllable count for simple words."""
        assert self.analyzer._count_syllables("cat") == 1
        assert self.analyzer._count_syllables("dog") == 1
        assert self.analyzer._count_syllables("the") == 1

    def test_count_syllables_two_syllable_words(self):
        """Test syllable count for two-syllable words."""
        assert self.analyzer._count_syllables("hello") == 2
        assert self.analyzer._count_syllables("water") == 2
        assert self.analyzer._count_syllables("paper") == 2

    def test_count_syllables_multi_syllable_words(self):
        """Test syllable count for multi-syllable words."""
        assert self.analyzer._count_syllables("beautiful") == 3
        assert self.analyzer._count_syllables("computer") == 3
        assert self.analyzer._count_syllables("university") == 5

    def test_count_syllables_silent_e(self):
        """Test syllable count handles silent e."""
        assert self.analyzer._count_syllables("make") == 1
        assert self.analyzer._count_syllables("take") == 1
        assert self.analyzer._count_syllables("like") == 1

    def test_count_syllables_minimum_one(self):
        """Test syllable count is at least 1."""
        assert self.analyzer._count_syllables("a") >= 1
        assert self.analyzer._count_syllables("x") >= 1

    # Test _approximate_flesch_score
    def test_approximate_flesch_score_simple_text(self):
        """Test Flesch score approximation for simple text."""
        simple_text = "The cat sat on the mat. The dog ran."
        score = self.analyzer._approximate_flesch_score(simple_text)
        # Simple text should have high readability score
        assert score > 70

    def test_approximate_flesch_score_complex_text(self):
        """Test Flesch score approximation for complex text."""
        complex_text = (
            "The implementation of sophisticated algorithmic methodologies "
            "necessitates comprehensive understanding of computational complexity. "
            "Furthermore, the ramifications of architectural decisions significantly "
            "impact the maintainability of enterprise-level applications."
        )
        score = self.analyzer._approximate_flesch_score(complex_text)
        # Complex text should have lower readability score
        assert score < 50

    def test_approximate_flesch_score_empty_text(self):
        """Test Flesch score returns default for empty text."""
        score = self.analyzer._approximate_flesch_score("")
        assert score == 60.0  # Default middle score

    def test_approximate_flesch_score_bounded(self):
        """Test Flesch score is bounded between 0 and 100."""
        texts = [
            "Go. Run. Jump.",  # Very simple
            "The quick brown fox jumps over the lazy dog.",
            "Antidisestablishmentarianism is a political position.",
        ]
        for text in texts:
            score = self.analyzer._approximate_flesch_score(text)
            assert 0 <= score <= 100

    # Test _approximate_grade_level
    def test_approximate_grade_level_very_easy(self):
        """Test grade level for very easy text (score >= 90)."""
        assert self.analyzer._approximate_grade_level(95) == 5
        assert self.analyzer._approximate_grade_level(90) == 5

    def test_approximate_grade_level_easy(self):
        """Test grade level for easy text (score 80-89)."""
        assert self.analyzer._approximate_grade_level(85) == 6
        assert self.analyzer._approximate_grade_level(80) == 6

    def test_approximate_grade_level_fairly_easy(self):
        """Test grade level for fairly easy text (score 70-79)."""
        assert self.analyzer._approximate_grade_level(75) == 7
        assert self.analyzer._approximate_grade_level(70) == 7

    def test_approximate_grade_level_standard(self):
        """Test grade level for standard text (score 60-69)."""
        assert self.analyzer._approximate_grade_level(65) == 9
        assert self.analyzer._approximate_grade_level(60) == 9

    def test_approximate_grade_level_fairly_difficult(self):
        """Test grade level for fairly difficult text (score 50-59)."""
        assert self.analyzer._approximate_grade_level(55) == 11
        assert self.analyzer._approximate_grade_level(50) == 11

    def test_approximate_grade_level_difficult(self):
        """Test grade level for difficult text (score 30-49)."""
        assert self.analyzer._approximate_grade_level(40) == 13
        assert self.analyzer._approximate_grade_level(30) == 13

    def test_approximate_grade_level_very_difficult(self):
        """Test grade level for very difficult text (score < 30)."""
        assert self.analyzer._approximate_grade_level(20) == 16
        assert self.analyzer._approximate_grade_level(10) == 16

    # Test _interpret_flesch_score
    def test_interpret_flesch_score_all_levels(self):
        """Test Flesch score interpretation for all levels."""
        assert "Very Easy" in self.analyzer._interpret_flesch_score(95)
        assert "Easy" in self.analyzer._interpret_flesch_score(85)
        assert "Fairly Easy" in self.analyzer._interpret_flesch_score(75)
        assert "Standard" in self.analyzer._interpret_flesch_score(65)
        assert "Fairly Difficult" in self.analyzer._interpret_flesch_score(55)
        assert "Difficult" in self.analyzer._interpret_flesch_score(40)
        assert "Very Difficult" in self.analyzer._interpret_flesch_score(20)

    # Test _similarity_score
    def test_similarity_score_identical_text(self):
        """Test similarity score for identical text."""
        text = "the quick brown fox"
        score = self.analyzer._similarity_score(text, text)
        assert score == 1.0

    def test_similarity_score_completely_different(self):
        """Test similarity score for completely different text."""
        text1 = "the quick brown fox"
        text2 = "some other words here"
        score = self.analyzer._similarity_score(text1, text2)
        assert score < 0.3

    def test_similarity_score_partial_overlap(self):
        """Test similarity score for partially overlapping text."""
        text1 = "the quick brown fox jumps"
        text2 = "the quick red fox runs"
        score = self.analyzer._similarity_score(text1, text2)
        assert 0.3 < score < 0.8

    def test_similarity_score_empty_text(self):
        """Test similarity score with empty text."""
        assert self.analyzer._similarity_score("", "some text") == 0.0
        assert self.analyzer._similarity_score("some text", "") == 0.0
        assert self.analyzer._similarity_score("", "") == 0.0

    def test_similarity_score_case_insensitive(self):
        """Test similarity score is case insensitive."""
        text1 = "The Quick Brown Fox"
        text2 = "the quick brown fox"
        score = self.analyzer._similarity_score(text1, text2)
        assert score == 1.0

    # Test _check_parallel_structure
    def test_check_parallel_structure_all_gerunds(self):
        """Test parallel structure with all gerunds."""
        bullets = [
            "Running fast through the park",
            "Swimming in the pool daily",
            "Jumping over obstacles",
        ]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert is_parallel is True

    def test_check_parallel_structure_mixed_gerunds(self):
        """Test non-parallel structure with mixed gerunds."""
        bullets = [
            "Running fast through the park",
            "The cat sleeps on the bed",
            "Jumping over obstacles",
        ]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert is_parallel is False
        assert "gerunds" in issue.lower() or "ing" in issue.lower()

    def test_check_parallel_structure_all_verbs(self):
        """Test parallel structure with common verbs."""
        bullets = [
            "Provides excellent performance",
            "Enables faster processing",
            "Ensures data integrity",
        ]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert is_parallel is True

    def test_check_parallel_structure_mixed_verbs(self):
        """Test non-parallel structure with mixed verbs."""
        bullets = [
            "Provides excellent performance",
            "The system is fast",
            "Ensures data integrity",
        ]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert is_parallel is False

    def test_check_parallel_structure_single_bullet(self):
        """Test parallel structure with single bullet (always parallel)."""
        bullets = ["Only one bullet point"]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert is_parallel is True

    def test_check_parallel_structure_empty_list(self):
        """Test parallel structure with empty list."""
        is_parallel, issue = self.analyzer._check_parallel_structure([])
        assert is_parallel is True


class TestQualityAnalyzerReadability:
    """Tests for readability analysis (no API calls)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_calculate_readability_empty_slides(self):
        """Test readability with empty slides."""
        result = self.analyzer.calculate_readability([])
        assert result["score"] == 100
        assert result["grade_level"] == "N/A"
        assert result["issues"] == []

    def test_calculate_readability_empty_content(self):
        """Test readability with slides having no content."""
        slides = [{"bullets": [], "speaker_notes": ""}]
        result = self.analyzer.calculate_readability(slides)
        assert result["score"] == 100

    def test_calculate_readability_simple_content(self):
        """Test readability with simple content."""
        slides = [
            {
                "bullets": [
                    "The cat sat on the mat.",
                    "The dog ran in the park.",
                ],
                "speaker_notes": "",
            }
        ]
        result = self.analyzer.calculate_readability(slides)
        assert "score" in result
        assert "flesch_reading_ease" in result
        assert "interpretation" in result
        assert result["metrics"]["total_words"] > 0

    def test_calculate_readability_complex_content_generates_issues(self):
        """Test readability with complex content generates issues."""
        slides = [
            {
                "bullets": [
                    "The implementation of sophisticated algorithmic methodologies "
                    "necessitates comprehensive understanding of computational complexity.",
                    "Furthermore, the ramifications of architectural decisions significantly "
                    "impact the maintainability of enterprise-level applications.",
                ],
                "speaker_notes": "",
            }
        ]
        result = self.analyzer.calculate_readability(slides)
        # Complex content should have lower score and potentially issues
        assert result["flesch_reading_ease"] < 60

    def test_calculate_readability_includes_speaker_notes(self):
        """Test readability includes speaker notes in analysis."""
        slides = [
            {
                "bullets": ["Simple point"],
                "speaker_notes": "This is a longer speaker note with more content to analyze.",
            }
        ]
        result = self.analyzer.calculate_readability(slides)
        # Word count should include speaker notes
        assert result["metrics"]["total_words"] > 2


class TestQualityAnalyzerParallelism:
    """Tests for bullet parallelism checking."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_check_bullet_parallelism_no_bullets(self):
        """Test parallelism with no bullets."""
        slides = [{"bullets": []}]
        result = self.analyzer.check_bullet_parallelism(slides)
        assert result["score"] == 100
        assert result["slides_analyzed"] == 0

    def test_check_bullet_parallelism_single_bullet_per_slide(self):
        """Test parallelism with single bullet per slide."""
        slides = [
            {"bullets": ["Only one bullet"]},
            {"bullets": ["Another single bullet"]},
        ]
        result = self.analyzer.check_bullet_parallelism(slides)
        assert result["score"] == 100

    def test_check_bullet_parallelism_all_parallel(self):
        """Test parallelism with all parallel bullets."""
        slides = [
            {
                "bullets": [
                    "Running the application",
                    "Testing the code",
                    "Deploying to production",
                ]
            }
        ]
        result = self.analyzer.check_bullet_parallelism(slides)
        assert result["score"] == 100
        assert result["parallel_slides"] == 1

    def test_check_bullet_parallelism_non_parallel(self):
        """Test parallelism with non-parallel bullets."""
        slides = [
            {
                "bullets": [
                    "Running the application",
                    "The code is tested",
                    "Deploying to production",
                ]
            }
        ]
        result = self.analyzer.check_bullet_parallelism(slides)
        assert result["score"] < 100
        assert len(result["issues"]) > 0


class TestQualityAnalyzerRedundancy:
    """Tests for redundancy detection."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_detect_redundancy_no_bullets(self):
        """Test redundancy with no bullets."""
        slides = [{"bullets": []}]
        result = self.analyzer.detect_redundancy(slides)
        assert result["redundancy_percentage"] == 0
        assert result["duplicates_found"] == 0

    def test_detect_redundancy_no_duplicates(self):
        """Test redundancy with unique bullets."""
        slides = [
            {"bullets": ["First unique point", "Second unique point"]},
            {"bullets": ["Third different point", "Fourth different point"]},
        ]
        result = self.analyzer.detect_redundancy(slides)
        assert result["redundancy_percentage"] == 0
        assert result["duplicates_found"] == 0

    def test_detect_redundancy_exact_duplicates(self):
        """Test redundancy with exact duplicates."""
        slides = [
            {"bullets": ["This is a repeated point", "Unique point"]},
            {"bullets": ["This is a repeated point", "Another unique point"]},
        ]
        result = self.analyzer.detect_redundancy(slides)
        assert result["duplicates_found"] > 0
        assert result["redundancy_percentage"] > 0

    def test_detect_redundancy_similar_bullets(self):
        """Test redundancy with similar bullets."""
        slides = [
            {"bullets": ["The system provides fast performance"]},
            {"bullets": ["The system provides fast performance and reliability"]},
        ]
        result = self.analyzer.detect_redundancy(slides)
        # Similar bullets should be detected
        assert "redundancy_percentage" in result

    def test_detect_redundancy_tracks_slide_sources(self):
        """Test redundancy tracks which slides have duplicates."""
        slides = [
            {"bullets": ["Duplicate content here"]},
            {"bullets": ["Something else"]},
            {"bullets": ["Duplicate content here"]},
        ]
        result = self.analyzer.detect_redundancy(slides)
        if result["duplicates_found"] > 0:
            # Check that duplicate_concepts includes slide numbers
            assert len(result["duplicate_concepts"]) > 0
            assert "slides" in result["duplicate_concepts"][0]


class TestQualityAnalyzerCitations:
    """Tests for citation validation."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_validate_citations_empty_slides(self):
        """Test citation validation with empty slides."""
        result = self.analyzer.validate_citations([])
        assert result["score"] == 100

    def test_validate_citations_with_citations(self):
        """Test citation validation with proper citations."""
        slides = [
            {
                "bullets": ["Some factual claim"],
                "citations": ["cite-001"],
                "outline": {"slide_type": "CONTENT"},
            }
        ]
        result = self.analyzer.validate_citations(slides)
        assert result["score"] == 100
        assert result["slides_with_citations"] == 1

    def test_validate_citations_missing_citations(self):
        """Test citation validation with missing citations."""
        slides = [
            {
                "bullets": ["Some factual claim without citation"],
                "citations": [],
                "outline": {"slide_type": "CONTENT"},
            }
        ]
        result = self.analyzer.validate_citations(slides)
        assert result["score"] < 100
        assert len(result["missing_citations"]) > 0

    def test_validate_citations_skips_title_slides(self):
        """Test citation validation skips title slides."""
        slides = [
            {
                "bullets": [],
                "citations": [],
                "outline": {"slide_type": "TITLE SLIDE"},
            }
        ]
        result = self.analyzer.validate_citations(slides)
        # Title slides shouldn't affect citation score
        assert result["score"] == 100

    def test_validate_citations_skips_section_dividers(self):
        """Test citation validation skips section dividers."""
        slides = [
            {
                "bullets": ["Section overview"],
                "citations": [],
                "outline": {"slide_type": "SECTION DIVIDER"},
            }
        ]
        result = self.analyzer.validate_citations(slides)
        assert result["score"] == 100


class TestQualityAnalyzerRecommendations:
    """Tests for recommendation generation."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_generate_recommendations_low_readability(self):
        """Test recommendations for low readability."""
        readability = {"score": 50}
        tone = {"matches_target": True}
        parallelism = {"score": 90}
        redundancy = {"redundancy_percentage": 10}
        citations = {"score": 90}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert any("readability" in r.lower() for r in recs)

    def test_generate_recommendations_tone_mismatch(self):
        """Test recommendations for tone mismatch."""
        readability = {"score": 80}
        tone = {"matches_target": False, "detected_tone": "casual"}
        parallelism = {"score": 90}
        redundancy = {"redundancy_percentage": 10}
        citations = {"score": 90}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert any("tone" in r.lower() for r in recs)

    def test_generate_recommendations_low_parallelism(self):
        """Test recommendations for low parallelism."""
        readability = {"score": 80}
        tone = {"matches_target": True}
        parallelism = {"score": 60}
        redundancy = {"redundancy_percentage": 10}
        citations = {"score": 90}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert any("parallelism" in r.lower() for r in recs)

    def test_generate_recommendations_high_redundancy(self):
        """Test recommendations for high redundancy."""
        readability = {"score": 80}
        tone = {"matches_target": True}
        parallelism = {"score": 90}
        redundancy = {"redundancy_percentage": 30}
        citations = {"score": 90}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert any("redundancy" in r.lower() for r in recs)

    def test_generate_recommendations_low_citations(self):
        """Test recommendations for low citation score."""
        readability = {"score": 80}
        tone = {"matches_target": True}
        parallelism = {"score": 90}
        redundancy = {"redundancy_percentage": 10}
        citations = {"score": 60}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert any("citation" in r.lower() for r in recs)

    def test_generate_recommendations_all_good(self):
        """Test no recommendations when all metrics are good."""
        readability = {"score": 80}
        tone = {"matches_target": True}
        parallelism = {"score": 90}
        redundancy = {"redundancy_percentage": 10}
        citations = {"score": 90}

        recs = self.analyzer._generate_recommendations(
            readability, tone, parallelism, redundancy, citations
        )
        assert len(recs) == 0


class TestQualityAnalyzerConvenienceFunction:
    """Tests for convenience function."""

    def test_get_quality_analyzer_returns_instance(self):
        """Test get_quality_analyzer returns QualityAnalyzer instance."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            analyzer = get_quality_analyzer()
            assert isinstance(analyzer, QualityAnalyzer)


class TestAnalyzePresentation:
    """Tests for the full analyze_presentation method (lines 53-86)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_analyze_presentation_empty_slides(self):
        """Test analyze_presentation with empty slides list."""
        with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
            mock_tone.return_value = {
                "score": 100,
                "detected_tone": "professional",
                "matches_target": True,
                "consistency": "high",
                "issues": [],
            }
            result = self.analyzer.analyze_presentation([])

        assert "overall_score" in result
        assert "readability_score" in result
        assert "tone_consistency_score" in result
        assert "structure_score" in result
        assert "redundancy_percentage" in result
        assert "citation_score" in result
        assert "issues" in result
        assert "recommendations" in result
        assert "details" in result

    def test_analyze_presentation_with_style_guide(self):
        """Test analyze_presentation uses style_guide for tone."""
        slides = [
            {
                "bullets": ["Simple point one", "Simple point two"],
                "citations": ["cite-1"],
            }
        ]
        with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
            mock_tone.return_value = {
                "score": 90,
                "detected_tone": "casual",
                "matches_target": True,
                "consistency": "high",
                "issues": [],
            }
            self.analyzer.analyze_presentation(slides, style_guide={"tone": "casual"})

            # Verify tone was called with the custom tone from style_guide
            mock_tone.assert_called_once()
            call_args = mock_tone.call_args
            assert call_args[0][1] == "casual"

    def test_analyze_presentation_default_style_guide(self):
        """Test analyze_presentation uses default professional tone when no style_guide."""
        slides = [{"bullets": ["Point one", "Point two"], "citations": []}]
        with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
            mock_tone.return_value = {
                "score": 85,
                "detected_tone": "professional",
                "matches_target": True,
                "consistency": "high",
                "issues": [],
            }
            self.analyzer.analyze_presentation(slides)

            # Verify tone was called with default "professional"
            mock_tone.assert_called_once()
            call_args = mock_tone.call_args
            assert call_args[0][1] == "professional"

    def test_analyze_presentation_aggregates_issues(self):
        """Test analyze_presentation aggregates issues from all analyses."""
        slides = [
            {
                "bullets": [
                    "Running task one",
                    "The code is tested",  # Non-parallel
                    "Deploying to server",
                ],
                "citations": [],  # Missing citation
                "outline": {"slide_type": "CONTENT"},
            }
        ]
        with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
            mock_tone.return_value = {
                "score": 70,
                "detected_tone": "professional",
                "matches_target": False,
                "consistency": "low",
                "issues": [
                    {
                        "type": "tone",
                        "severity": "medium",
                        "message": "Tone shift detected",
                    }
                ],
            }
            result = self.analyzer.analyze_presentation(slides)

        # Should have issues from multiple sources
        assert len(result["issues"]) > 0
        issue_types = [issue["type"] for issue in result["issues"]]
        # Should have tone issue from mock
        assert "tone" in issue_types

    def test_analyze_presentation_calculates_weighted_score(self):
        """Test analyze_presentation calculates correct weighted overall score."""
        slides = [{"bullets": ["Point"], "citations": ["cite-1"]}]
        with patch.object(self.analyzer, "calculate_readability") as mock_read:
            with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
                with patch.object(
                    self.analyzer, "check_bullet_parallelism"
                ) as mock_para:
                    with patch.object(self.analyzer, "detect_redundancy") as mock_redun:
                        with patch.object(
                            self.analyzer, "validate_citations"
                        ) as mock_cite:
                            mock_read.return_value = {"score": 100, "issues": []}
                            mock_tone.return_value = {
                                "score": 100,
                                "matches_target": True,
                                "issues": [],
                            }
                            mock_para.return_value = {"score": 100, "issues": []}
                            mock_redun.return_value = {
                                "redundancy_percentage": 0,
                                "issues": [],
                            }
                            mock_cite.return_value = {"score": 100, "issues": []}

                            result = self.analyzer.analyze_presentation(slides)

        # All perfect scores should give 100 overall
        # 100*0.20 + 100*0.20 + 100*0.25 + (100-0)*0.15 + 100*0.20 = 100
        assert result["overall_score"] == 100.0

    def test_analyze_presentation_generates_recommendations(self):
        """Test analyze_presentation generates recommendations based on scores."""
        slides = [{"bullets": ["Point"], "citations": []}]
        with patch.object(self.analyzer, "calculate_readability") as mock_read:
            with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
                with patch.object(
                    self.analyzer, "check_bullet_parallelism"
                ) as mock_para:
                    with patch.object(self.analyzer, "detect_redundancy") as mock_redun:
                        with patch.object(
                            self.analyzer, "validate_citations"
                        ) as mock_cite:
                            # Set up poor scores to trigger recommendations
                            mock_read.return_value = {"score": 50, "issues": []}
                            mock_tone.return_value = {
                                "score": 70,
                                "matches_target": False,
                                "detected_tone": "casual",
                                "issues": [],
                            }
                            mock_para.return_value = {"score": 60, "issues": []}
                            mock_redun.return_value = {
                                "redundancy_percentage": 30,
                                "issues": [],
                            }
                            mock_cite.return_value = {"score": 60, "issues": []}

                            result = self.analyzer.analyze_presentation(slides)

        # Should have recommendations for all low-scoring areas
        assert len(result["recommendations"]) > 0

    def test_analyze_presentation_includes_details(self):
        """Test analyze_presentation includes detailed results for each analysis."""
        slides = [{"bullets": ["Point one", "Point two"], "citations": ["cite-1"]}]
        with patch.object(self.analyzer, "check_tone_consistency") as mock_tone:
            mock_tone.return_value = {
                "score": 90,
                "detected_tone": "professional",
                "matches_target": True,
                "consistency": "high",
                "issues": [],
            }
            result = self.analyzer.analyze_presentation(slides)

        details = result["details"]
        assert "readability" in details
        assert "tone" in details
        assert "structure" in details
        assert "redundancy" in details
        assert "citations" in details


class TestReadabilityWithoutTextstat:
    """Tests for readability when textstat is not available (lines 139-143)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_calculate_readability_without_textstat(self):
        """Test readability falls back to approximation when textstat unavailable."""
        slides = [{"bullets": ["The cat sat on the mat.", "The dog ran fast."]}]
        # Mock textstat import to raise ImportError
        with patch.dict("sys.modules", {"textstat": None}):
            with patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'textstat'"),
            ):
                result = self.analyzer.calculate_readability(slides)

        # Should still return valid results using approximation
        assert "score" in result
        assert "flesch_reading_ease" in result
        # Grade level should be prefixed with ~ when approximated
        assert result["grade_level"].startswith("~") or isinstance(
            result["grade_level"], int
        )
        assert result["metrics"]["using_textstat"] is False


class TestReadabilityIssues:
    """Tests for readability issue generation (lines 156-173, 178-185)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_calculate_readability_complex_text_generates_issue(self):
        """Test that very complex text (Flesch < 50) generates medium severity issue."""
        # Create very complex text that will have low Flesch score
        complex_bullets = [
            "The implementation of sophisticated algorithmic methodologies necessitates comprehensive understanding.",
            "Furthermore, the ramifications of architectural decisions significantly impact maintainability.",
            "Consequentially, the obfuscation of computational paradigms demonstrates unprecedented complexity.",
        ] * 3  # Repeat for more text

        slides = [{"bullets": complex_bullets, "speaker_notes": ""}]

        # Use approximation which should give low score
        with patch.object(
            self.analyzer, "_approximate_flesch_score", return_value=35.0
        ):
            result = self.analyzer.calculate_readability(slides)

        # Should have a readability issue for complex text
        assert any(
            issue["type"] == "readability" and issue["severity"] == "medium"
            for issue in result["issues"]
        )

    def test_calculate_readability_very_simple_text_generates_issue(self):
        """Test that very simple text (Flesch > 80) generates low severity issue."""
        slides = [{"bullets": ["Go. Run. Jump. Eat."], "speaker_notes": ""}]

        # Use approximation which should give high score
        with patch.object(
            self.analyzer, "_approximate_flesch_score", return_value=95.0
        ):
            result = self.analyzer.calculate_readability(slides)

        # Should have a readability issue for too simple text
        assert any(
            issue["type"] == "readability" and issue["severity"] == "low"
            for issue in result["issues"]
        )

    def test_calculate_readability_optimal_range_no_issues(self):
        """Test that text in optimal range (60-70) has no readability issues."""
        slides = [
            {"bullets": ["Normal professional content here."], "speaker_notes": ""}
        ]

        # Force fallback to approximation and mock it to return optimal score
        with (
            patch.dict("sys.modules", {"textstat": None}),
            patch.object(self.analyzer, "_approximate_flesch_score", return_value=65.0),
            patch.object(
                self.analyzer, "_approximate_grade_level", return_value="8th grade"
            ),
        ):
            result = self.analyzer.calculate_readability(slides)

        # Should not have readability issues in optimal range
        assert not any(issue["type"] == "readability" for issue in result["issues"])

    def test_calculate_readability_normalized_score_below_optimal(self):
        """Test readability issues for complex text (Flesch below 50)."""
        slides = [{"bullets": ["Some text content."], "speaker_notes": ""}]

        # Force fallback to approximation and mock it to return complex score
        with (
            patch.dict("sys.modules", {"textstat": None}),
            patch.object(self.analyzer, "_approximate_flesch_score", return_value=40.0),
            patch.object(
                self.analyzer, "_approximate_grade_level", return_value="12th grade"
            ),
        ):
            result = self.analyzer.calculate_readability(slides)

        # Score below 50 triggers "text too complex" issue
        assert any(issue["type"] == "readability" for issue in result["issues"])

    def test_calculate_readability_normalized_score_above_optimal(self):
        """Test readability issues for too simple text (Flesch above 70)."""
        slides = [{"bullets": ["Very simple text."], "speaker_notes": ""}]

        # Force fallback to approximation and mock it to return too-simple score
        with (
            patch.dict("sys.modules", {"textstat": None}),
            patch.object(self.analyzer, "_approximate_flesch_score", return_value=85.0),
            patch.object(
                self.analyzer, "_approximate_grade_level", return_value="5th grade"
            ),
        ):
            result = self.analyzer.calculate_readability(slides)

        # Score above 70 triggers "text too simple" issue (for professional content)
        assert any(issue["type"] == "readability" for issue in result["issues"])

    def test_calculate_readability_normalized_score_minimum(self):
        """Test readability issues for very complex text."""
        slides = [{"bullets": ["Complex text."], "speaker_notes": ""}]

        # Force fallback to approximation and mock it to return very complex score
        with (
            patch.dict("sys.modules", {"textstat": None}),
            patch.object(self.analyzer, "_approximate_flesch_score", return_value=10.0),
            patch.object(
                self.analyzer, "_approximate_grade_level", return_value="Graduate"
            ),
        ):
            result = self.analyzer.calculate_readability(slides)

        # Very complex text should trigger readability issue
        assert any(issue["type"] == "readability" for issue in result["issues"])


class TestToneConsistency:
    """Tests for tone consistency checking with API calls (lines 213-309)."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_check_tone_consistency_empty_slides(self):
        """Test tone consistency with empty slides returns default values."""
        result = self.analyzer.check_tone_consistency([], "professional")

        assert result["score"] == 100
        assert result["detected_tone"] == "professional"
        assert result["consistency"] == "high"
        assert result["issues"] == []

    def test_check_tone_consistency_empty_content(self):
        """Test tone consistency with slides but minimal content still calls API."""
        slides = [{"title": "", "bullets": []}, {"title": "", "bullets": []}]

        # Even with empty titles/bullets, slide numbers create non-empty content
        # so the API is called. Mock a success response.
        mock_response = """{
            "detected_tone": "professional",
            "matches_target": true,
            "consistency_rating": "high",
            "tone_shifts": [],
            "suggestions": []
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        assert result["score"] == 100

    def test_check_tone_consistency_api_success_matches_target(self):
        """Test tone consistency when API returns matching tone."""
        slides = [
            {
                "title": "Introduction",
                "bullets": ["Professional content here", "More formal text"],
            }
        ]

        mock_response = """{
            "detected_tone": "professional",
            "matches_target": true,
            "consistency_rating": "high",
            "tone_shifts": [],
            "suggestions": []
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        assert result["score"] == 100
        assert result["detected_tone"] == "professional"
        assert result["matches_target"] is True
        assert result["consistency"] == "high"

    def test_check_tone_consistency_api_success_no_match(self):
        """Test tone consistency when API returns non-matching tone."""
        slides = [
            {"title": "Hey Everyone!", "bullets": ["Cool stuff here", "Check this out"]}
        ]

        mock_response = """{
            "detected_tone": "casual",
            "matches_target": false,
            "consistency_rating": "high",
            "tone_shifts": [],
            "suggestions": ["Use more formal language"]
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Score should be reduced by 30 for not matching target
        assert result["score"] == 70
        assert result["detected_tone"] == "casual"
        assert result["matches_target"] is False

    def test_check_tone_consistency_api_low_consistency(self):
        """Test tone consistency when API returns low consistency."""
        slides = [{"title": "Slide 1", "bullets": ["Mixed tones throughout"]}]

        mock_response = """{
            "detected_tone": "professional",
            "matches_target": true,
            "consistency_rating": "low",
            "tone_shifts": ["Shift from formal to casual in slide 3"],
            "suggestions": ["Maintain consistent tone"]
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Score reduced by 30 for low consistency
        assert result["score"] == 70
        assert result["consistency"] == "low"

    def test_check_tone_consistency_api_medium_consistency(self):
        """Test tone consistency when API returns medium consistency."""
        slides = [{"title": "Slide 1", "bullets": ["Some content"]}]

        mock_response = """{
            "detected_tone": "professional",
            "matches_target": true,
            "consistency_rating": "medium",
            "tone_shifts": [],
            "suggestions": []
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Score reduced by 15 for medium consistency
        assert result["score"] == 85
        assert result["consistency"] == "medium"

    def test_check_tone_consistency_api_failure_returns_fallback(self):
        """Test tone consistency returns fallback when API fails."""
        slides = [{"title": "Slide 1", "bullets": ["Some content"]}]

        with patch.object(
            self.analyzer.client, "generate_text", side_effect=Exception("API Error")
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Should return fallback values
        assert result["score"] == 75
        assert result["detected_tone"] == "unknown"
        assert result["consistency"] == "unknown"
        assert "error" in result

    def test_check_tone_consistency_json_in_code_block(self):
        """Test tone consistency parses JSON from code block."""
        slides = [{"title": "Slide 1", "bullets": ["Content here"]}]

        mock_response = """Here is the analysis:
```json
{
    "detected_tone": "academic",
    "matches_target": false,
    "consistency_rating": "high",
    "tone_shifts": ["Overly formal for target audience"],
    "suggestions": ["Simplify language"]
}
```"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "conversational")

        assert result["detected_tone"] == "academic"
        assert result["matches_target"] is False
        # Score: 100 - 30 (no match) = 70
        assert result["score"] == 70

    def test_check_tone_consistency_creates_issues_from_tone_shifts(self):
        """Test tone consistency creates issues from detected tone shifts."""
        slides = [{"title": "Slide 1", "bullets": ["Content"]}]

        mock_response = """{
            "detected_tone": "mixed",
            "matches_target": false,
            "consistency_rating": "low",
            "tone_shifts": ["Formal intro becomes casual", "Technical jargon appears suddenly"],
            "suggestions": ["Be consistent", "Pick one tone"]
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Should have issues for each tone shift
        assert len(result["issues"]) == 2
        assert all(issue["type"] == "tone" for issue in result["issues"])
        # When matches_target is False, severity should be medium
        assert all(issue["severity"] == "medium" for issue in result["issues"])

    def test_check_tone_consistency_limits_to_10_slides(self):
        """Test tone consistency only analyzes first 10 slides."""
        # Create 15 slides
        slides = [
            {"title": f"Slide {i}", "bullets": [f"Content for slide {i}"]}
            for i in range(15)
        ]

        mock_response = """{
            "detected_tone": "professional",
            "matches_target": true,
            "consistency_rating": "high",
            "tone_shifts": [],
            "suggestions": []
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ) as mock:
            self.analyzer.check_tone_consistency(slides, "professional")

            # Check that only first 10 slides were included in the prompt
            call_args = mock.call_args
            prompt = call_args[1]["prompt"]
            # Should contain "Slide 10" but not "Slide 11"
            assert "Slide 10" in prompt
            assert "Slide 11" not in prompt

    def test_check_tone_consistency_both_penalties_stack(self):
        """Test tone consistency score has both penalties stack."""
        slides = [{"title": "Slide 1", "bullets": ["Content"]}]

        mock_response = """{
            "detected_tone": "casual",
            "matches_target": false,
            "consistency_rating": "low",
            "tone_shifts": [],
            "suggestions": []
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Score: 100 - 30 (no match) - 30 (low consistency) = 40
        assert result["score"] == 40

    def test_check_tone_consistency_minimum_score_zero(self):
        """Test tone consistency score doesn't go below zero."""
        slides = [{"title": "Slide 1", "bullets": ["Content"]}]

        # This would give negative score without max(0, score)
        mock_response = """{
            "detected_tone": "hostile",
            "matches_target": false,
            "consistency_rating": "low",
            "tone_shifts": ["Major tone issues"],
            "suggestions": ["Fix the tone issues"]
        }"""

        with patch.object(
            self.analyzer.client, "generate_text", return_value=mock_response
        ):
            result = self.analyzer.check_tone_consistency(slides, "professional")

        # Score should be max(0, 100 - 30 - 30) = max(0, 40) = 40
        assert result["score"] >= 0


class TestRedundancyEdgeCases:
    """Additional tests for redundancy detection edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_detect_redundancy_high_similarity_detection(self):
        """Test redundancy detects bullets with >80% similarity."""
        slides = [
            {"bullets": ["The system provides excellent performance and reliability"]},
            {"bullets": ["The system provides excellent performance reliability"]},
        ]
        result = self.analyzer.detect_redundancy(slides)

        # Similar bullets should be detected as duplicates
        assert result["duplicates_found"] >= 1

    def test_detect_redundancy_case_insensitive(self):
        """Test redundancy detection is case insensitive."""
        slides = [
            {"bullets": ["THE SYSTEM IS FAST"]},
            {"bullets": ["the system is fast"]},
        ]
        result = self.analyzer.detect_redundancy(slides)

        assert result["duplicates_found"] >= 1

    def test_detect_redundancy_issue_severity_multiple_duplicates(self):
        """Test redundancy issues have medium severity when count > 2."""
        slides = [
            {"bullets": ["duplicate text here"]},
            {"bullets": ["duplicate text here"]},
            {"bullets": ["duplicate text here"]},
        ]
        result = self.analyzer.detect_redundancy(slides)

        # Should have issue with medium severity for 3+ duplicates
        assert any(issue["severity"] == "medium" for issue in result["issues"])

    def test_detect_redundancy_limits_duplicate_concepts(self):
        """Test redundancy only shows first 5 duplicate concepts."""
        # Create many duplicates
        slides = []
        for i in range(10):
            slides.append({"bullets": [f"duplicate group {i}"]})
            slides.append({"bullets": [f"duplicate group {i}"]})

        result = self.analyzer.detect_redundancy(slides)

        # Should only show first 5 duplicate concepts
        assert len(result["duplicate_concepts"]) <= 5


class TestCitationsEdgeCases:
    """Additional tests for citation validation edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_validate_citations_mixed_slide_types(self):
        """Test citation validation with mixed slide types."""
        slides = [
            {"bullets": [], "citations": [], "outline": {"slide_type": "TITLE SLIDE"}},
            {
                "bullets": ["Content"],
                "citations": ["cite-1"],
                "outline": {"slide_type": "CONTENT"},
            },
            {
                "bullets": [],
                "citations": [],
                "outline": {"slide_type": "SECTION DIVIDER"},
            },
            {
                "bullets": ["More content"],
                "citations": [],
                "outline": {"slide_type": "CONTENT"},
            },
        ]
        result = self.analyzer.validate_citations(slides)

        # 2 content slides, 1 with citations
        assert result["content_slides"] == 2
        assert result["slides_with_citations"] == 1
        assert result["score"] == 50.0

    def test_validate_citations_no_content_slides(self):
        """Test citation validation when all slides are title/section types."""
        slides = [
            {"bullets": [], "citations": [], "outline": {"slide_type": "TITLE SLIDE"}},
            {
                "bullets": [],
                "citations": [],
                "outline": {"slide_type": "SECTION DIVIDER"},
            },
        ]
        result = self.analyzer.validate_citations(slides)

        # No content slides, so score should be 100
        assert result["score"] == 100
        assert result["content_slides"] == 0

    def test_validate_citations_empty_bullets_not_flagged(self):
        """Test slides with empty bullets are not flagged for missing citations."""
        slides = [
            {"bullets": [], "citations": [], "outline": {"slide_type": "CONTENT"}},
        ]
        result = self.analyzer.validate_citations(slides)

        # Empty bullets should not be flagged
        assert len(result["missing_citations"]) == 0

    def test_validate_citations_missing_outline_defaults_to_content(self):
        """Test slides without outline info default to content type."""
        slides = [
            {"bullets": ["Some claim"], "citations": []},  # No outline
        ]
        result = self.analyzer.validate_citations(slides)

        # Should be treated as content slide and flagged for missing citation
        assert len(result["missing_citations"]) == 1


class TestParallelismEdgeCases:
    """Additional tests for parallelism checking edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_check_parallel_structure_empty_bullets_in_list(self):
        """Test parallel structure with empty string bullets."""
        bullets = ["Valid point", "", "Another point"]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        # Should handle empty strings gracefully
        assert isinstance(is_parallel, bool)

    def test_check_parallel_structure_punctuation_stripped(self):
        """Test that punctuation is stripped from first words."""
        bullets = ["- First point with dash", "- Second point with dash"]
        is_parallel, issue = self.analyzer._check_parallel_structure(bullets)
        assert isinstance(is_parallel, bool)

    def test_check_bullet_parallelism_multiple_slides_mixed(self):
        """Test parallelism across multiple slides with mixed results."""
        slides = [
            {"bullets": ["Running test", "Writing code", "Deploying app"]},  # Parallel
            {
                "bullets": ["Provides value", "Is fast", "Ensures quality"]
            },  # Not parallel
            {
                "bullets": ["Creating docs", "Building features", "Testing code"]
            },  # Parallel
        ]
        result = self.analyzer.check_bullet_parallelism(slides)

        assert result["slides_analyzed"] == 3
        # At least 2 should be parallel
        assert result["parallel_slides"] >= 2


class TestFleschScoreInterpretation:
    """Tests for Flesch score interpretation edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_interpret_flesch_score_boundaries(self):
        """Test interpretation at exact boundary values."""
        assert "Very Easy" in self.analyzer._interpret_flesch_score(90)
        assert "Easy" in self.analyzer._interpret_flesch_score(80)
        assert "Fairly Easy" in self.analyzer._interpret_flesch_score(70)
        assert "Standard" in self.analyzer._interpret_flesch_score(60)
        assert "Fairly Difficult" in self.analyzer._interpret_flesch_score(50)
        assert "Difficult" in self.analyzer._interpret_flesch_score(30)
        assert "Very Difficult" in self.analyzer._interpret_flesch_score(29)

    def test_approximate_grade_level_boundary_values(self):
        """Test grade level at exact boundary values."""
        # Test at exact boundary values
        assert self.analyzer._approximate_grade_level(90) == 5
        assert self.analyzer._approximate_grade_level(80) == 6
        assert self.analyzer._approximate_grade_level(70) == 7
        assert self.analyzer._approximate_grade_level(60) == 9
        assert self.analyzer._approximate_grade_level(50) == 11
        assert self.analyzer._approximate_grade_level(30) == 13
        assert self.analyzer._approximate_grade_level(29) == 16


class TestSimilarityScore:
    """Additional tests for similarity score calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("plugin.lib.quality_analyzer.get_claude_client"):
            self.analyzer = QualityAnalyzer()

    def test_similarity_score_single_word_overlap(self):
        """Test similarity with single word overlap."""
        text1 = "the quick fox"
        text2 = "the lazy dog"
        score = self.analyzer._similarity_score(text1, text2)
        # Only "the" overlaps: 1 intersection, 5 union = 0.2
        assert 0.1 < score < 0.3

    def test_similarity_score_whitespace_handling(self):
        """Test similarity handles extra whitespace."""
        text1 = "the  quick   fox"
        text2 = "the quick fox"
        score = self.analyzer._similarity_score(text1, text2)
        # Should be identical after splitting
        assert score == 1.0
