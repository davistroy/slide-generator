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
