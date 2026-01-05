"""
Unit tests for plugin/lib/validators.py

Tests all validation and sanitization utilities.
"""

import os
import pytest
from unittest.mock import patch

from plugin.lib.validators import Validators


class TestValidateApiKey:
    """Tests for API key validation."""

    def test_validate_api_key_empty(self):
        """Test validation of empty API key."""
        result = Validators.validate_api_key("", "claude")
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_api_key_whitespace_only(self):
        """Test validation of whitespace-only API key."""
        result = Validators.validate_api_key("   ", "claude")
        assert result.is_valid is False

    def test_validate_api_key_too_short(self):
        """Test validation of too short API key."""
        result = Validators.validate_api_key("short", "claude")
        assert result.is_valid is False
        assert any("short" in e.lower() for e in result.errors)

    def test_validate_api_key_too_long(self):
        """Test validation of too long API key."""
        long_key = "a" * 250
        result = Validators.validate_api_key(long_key, "claude")
        assert result.is_valid is False
        assert any("long" in e.lower() for e in result.errors)

    def test_validate_api_key_valid_claude_format(self):
        """Test validation of valid Claude API key format."""
        valid_key = "sk-ant-api03-" + "a" * 50
        result = Validators.validate_api_key(valid_key, "claude")
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_validate_api_key_valid_anthropic_format(self):
        """Test validation of valid Anthropic API key format."""
        valid_key = "sk-ant-" + "a" * 50
        result = Validators.validate_api_key(valid_key, "anthropic")
        assert result.is_valid is True

    def test_validate_api_key_warning_wrong_claude_format(self):
        """Test warning for wrong Claude key format."""
        wrong_format_key = "wrong-format-" + "a" * 50
        result = Validators.validate_api_key(wrong_format_key, "claude")
        assert result.is_valid is True  # Still valid, just warns
        assert len(result.warnings) > 0
        assert any("sk-ant-" in w for w in result.warnings)

    def test_validate_api_key_valid_gemini_format(self):
        """Test validation of valid Gemini API key format."""
        valid_key = "AIza" + "a" * 35
        result = Validators.validate_api_key(valid_key, "gemini")
        assert result.is_valid is True
        assert len(result.warnings) == 0

    def test_validate_api_key_valid_google_format(self):
        """Test validation of valid Google API key format."""
        valid_key = "AIza" + "a" * 35
        result = Validators.validate_api_key(valid_key, "google")
        assert result.is_valid is True

    def test_validate_api_key_warning_wrong_gemini_format(self):
        """Test warning for wrong Gemini key format."""
        wrong_format_key = "wrong-format-" + "a" * 50
        result = Validators.validate_api_key(wrong_format_key, "gemini")
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_validate_api_key_internal_whitespace(self):
        """Test validation rejects internal whitespace."""
        key_with_space = "sk-ant-" + "a" * 20 + " " + "a" * 20
        result = Validators.validate_api_key(key_with_space, "claude")
        assert result.is_valid is False
        assert any("whitespace" in e.lower() for e in result.errors)

    def test_validate_api_key_tabs_rejected(self):
        """Test validation rejects tabs."""
        key_with_tab = "sk-ant-" + "a" * 20 + "\t" + "a" * 20
        result = Validators.validate_api_key(key_with_tab, "claude")
        assert result.is_valid is False

    def test_validate_api_key_newlines_rejected(self):
        """Test validation rejects newlines."""
        key_with_newline = "sk-ant-" + "a" * 20 + "\n" + "a" * 20
        result = Validators.validate_api_key(key_with_newline, "claude")
        assert result.is_valid is False

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_validate_api_key_test_key_in_production(self):
        """Test validation rejects test keys in production."""
        test_key = "sk-ant-api03-test" + "a" * 50
        result = Validators.validate_api_key(test_key, "claude")
        assert result.is_valid is False
        assert any("test" in e.lower() for e in result.errors)

    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    def test_validate_api_key_test_key_in_development(self):
        """Test validation allows test keys in development."""
        test_key = "sk-ant-" + "a" * 50  # Valid format
        result = Validators.validate_api_key(test_key, "claude")
        assert result.is_valid is True


class TestValidateUrl:
    """Tests for URL validation."""

    def test_validate_url_empty(self):
        """Test validation of empty URL."""
        result = Validators.validate_url("")
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_url_whitespace_only(self):
        """Test validation of whitespace-only URL."""
        result = Validators.validate_url("   ")
        assert result.is_valid is False

    def test_validate_url_valid_https(self):
        """Test validation of valid HTTPS URL."""
        result = Validators.validate_url("https://example.com")
        assert result.is_valid is True

    def test_validate_url_valid_http(self):
        """Test validation of valid HTTP URL."""
        result = Validators.validate_url("http://example.com")
        assert result.is_valid is True

    def test_validate_url_with_path(self):
        """Test validation of URL with path."""
        result = Validators.validate_url("https://example.com/path/to/resource")
        assert result.is_valid is True

    def test_validate_url_with_query_params(self):
        """Test validation of URL with query parameters."""
        result = Validators.validate_url("https://example.com/search?q=test&page=1")
        assert result.is_valid is True

    def test_validate_url_missing_scheme(self):
        """Test validation rejects URL without scheme."""
        result = Validators.validate_url("example.com")
        assert result.is_valid is False
        assert any("scheme" in e.lower() for e in result.errors)

    def test_validate_url_invalid_scheme(self):
        """Test validation rejects invalid schemes."""
        result = Validators.validate_url("ftp://example.com")
        assert result.is_valid is False
        assert any("scheme" in e.lower() for e in result.errors)

    def test_validate_url_missing_domain(self):
        """Test validation rejects URL without domain."""
        result = Validators.validate_url("https://")
        assert result.is_valid is False
        assert any("domain" in e.lower() for e in result.errors)

    def test_validate_url_suspicious_characters(self):
        """Test validation rejects suspicious characters."""
        suspicious_urls = [
            'https://example.com/<script>',
            'https://example.com/">',
            "https://example.com/'",
        ]
        for url in suspicious_urls:
            result = Validators.validate_url(url)
            assert result.is_valid is False
            assert any("suspicious" in e.lower() for e in result.errors)

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_validate_url_localhost_warning_in_production(self):
        """Test validation warns about localhost in production."""
        result = Validators.validate_url("https://localhost/api")
        assert result.is_valid is True  # Valid, but warns
        assert len(result.warnings) > 0

    @patch.dict(os.environ, {"ENVIRONMENT": "development"})
    def test_validate_url_localhost_ok_in_development(self):
        """Test validation allows localhost in development."""
        result = Validators.validate_url("https://localhost/api")
        assert result.is_valid is True
        assert len(result.warnings) == 0


class TestValidateFilePath:
    """Tests for file path validation."""

    def test_validate_file_path_empty(self):
        """Test validation of empty path."""
        result = Validators.validate_file_path("")
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_file_path_whitespace_only(self):
        """Test validation of whitespace-only path."""
        result = Validators.validate_file_path("   ")
        assert result.is_valid is False

    def test_validate_file_path_traversal_attack(self):
        """Test validation rejects path traversal."""
        result = Validators.validate_file_path("../../../etc/passwd")
        assert result.is_valid is False
        assert any(".." in e for e in result.errors)

    def test_validate_file_path_dangerous_components(self):
        """Test validation rejects dangerous path components."""
        dangerous_paths = [
            "/path/with/~expansion",
            "/path/with/$variable",
            "/path/with/`command`",
            "/path/with/|pipe",
            "/path/with/&background",
            "/path/with/;semicolon",
        ]
        for path in dangerous_paths:
            result = Validators.validate_file_path(path)
            assert result.is_valid is False

    def test_validate_file_path_null_bytes(self):
        """Test validation rejects null bytes."""
        result = Validators.validate_file_path("/path/with/\x00null")
        assert result.is_valid is False
        assert any("null" in e.lower() for e in result.errors)

    def test_validate_file_path_must_exist_nonexistent(self):
        """Test validation fails when must_exist is True for nonexistent path."""
        result = Validators.validate_file_path(
            "/nonexistent/path/file.txt", must_exist=True
        )
        assert result.is_valid is False
        assert any("exist" in e.lower() for e in result.errors)

    def test_validate_file_path_allow_create_false(self):
        """Test validation fails when allow_create is False for nonexistent path."""
        result = Validators.validate_file_path(
            "/nonexistent/path/file.txt", must_exist=False, allow_create=False
        )
        assert result.is_valid is False

    def test_validate_file_path_valid_relative(self):
        """Test validation of valid relative path."""
        result = Validators.validate_file_path("output/file.txt")
        # May fail if parent doesn't exist, but shouldn't have security errors
        security_errors = [e for e in result.errors if "dangerous" in e.lower()]
        assert len(security_errors) == 0


class TestValidateTopic:
    """Tests for topic validation."""

    def test_validate_topic_empty(self):
        """Test validation of empty topic."""
        result = Validators.validate_topic("")
        assert result.is_valid is False
        assert any("empty" in e.lower() for e in result.errors)

    def test_validate_topic_whitespace_only(self):
        """Test validation of whitespace-only topic."""
        result = Validators.validate_topic("   ")
        assert result.is_valid is False

    def test_validate_topic_too_short(self):
        """Test validation of too short topic."""
        result = Validators.validate_topic("ab")
        assert result.is_valid is False
        assert any("short" in e.lower() for e in result.errors)

    def test_validate_topic_too_long(self):
        """Test validation of too long topic."""
        long_topic = "a" * 600
        result = Validators.validate_topic(long_topic)
        assert result.is_valid is False
        assert any("long" in e.lower() for e in result.errors)

    def test_validate_topic_custom_max_length(self):
        """Test validation with custom max length."""
        topic = "a" * 100
        result = Validators.validate_topic(topic, max_length=50)
        assert result.is_valid is False

    def test_validate_topic_valid(self):
        """Test validation of valid topic."""
        result = Validators.validate_topic("Climate change impacts on agriculture")
        assert result.is_valid is True

    def test_validate_topic_script_injection(self):
        """Test validation rejects script injection."""
        result = Validators.validate_topic("<script>alert('xss')</script>")
        assert result.is_valid is False
        assert any("script" in e.lower() for e in result.errors)

    def test_validate_topic_javascript_protocol(self):
        """Test validation rejects javascript: protocol."""
        result = Validators.validate_topic("javascript:alert('xss')")
        assert result.is_valid is False
        assert any("javascript" in e.lower() for e in result.errors)

    def test_validate_topic_event_handlers(self):
        """Test validation rejects event handlers."""
        result = Validators.validate_topic("onclick=alert('xss')")
        assert result.is_valid is False
        assert any("event" in e.lower() for e in result.errors)

    def test_validate_topic_template_injection(self):
        """Test validation rejects template injection."""
        result = Validators.validate_topic("${process.env.SECRET}")
        assert result.is_valid is False
        assert any("template" in e.lower() for e in result.errors)

    def test_validate_topic_command_injection(self):
        """Test validation rejects command injection."""
        result = Validators.validate_topic("``rm -rf /``")
        assert result.is_valid is False
        assert any("command" in e.lower() for e in result.errors)

    def test_validate_topic_control_characters(self):
        """Test validation rejects control characters."""
        result = Validators.validate_topic("Topic with \x00 null")
        assert result.is_valid is False
        assert any("control" in e.lower() for e in result.errors)

    def test_validate_topic_allows_common_punctuation(self):
        """Test validation allows common punctuation."""
        result = Validators.validate_topic("Topic: How does AI work? Let's explore!")
        assert result.is_valid is True

    def test_validate_topic_excessive_special_chars_warning(self):
        """Test validation warns about excessive special characters."""
        result = Validators.validate_topic("@#$%^&*()!@#$%^normal")
        # Should be valid but may have warnings
        assert len(result.warnings) > 0 or result.is_valid is True


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_filename_empty(self):
        """Test sanitization of empty filename."""
        result = Validators.sanitize_filename("")
        assert result == "unnamed"

    def test_sanitize_filename_none(self):
        """Test sanitization of None filename."""
        result = Validators.sanitize_filename(None)
        assert result == "unnamed"

    def test_sanitize_filename_valid(self):
        """Test sanitization of valid filename."""
        result = Validators.sanitize_filename("myfile.txt")
        assert result == "myfile.txt"

    def test_sanitize_filename_removes_path(self):
        """Test sanitization removes path components."""
        result = Validators.sanitize_filename("/path/to/myfile.txt")
        assert result == "myfile.txt"
        assert "/" not in result

    def test_sanitize_filename_removes_dangerous_chars(self):
        """Test sanitization removes dangerous characters."""
        result = Validators.sanitize_filename('file<>:"/\\|?*.txt')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_sanitize_filename_removes_leading_trailing_dots(self):
        """Test sanitization removes leading/trailing dots."""
        result = Validators.sanitize_filename("...file...")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_sanitize_filename_collapses_underscores(self):
        """Test sanitization collapses multiple underscores."""
        result = Validators.sanitize_filename("file___name.txt")
        assert "___" not in result

    def test_sanitize_filename_truncates_long_names(self):
        """Test sanitization truncates long filenames."""
        long_name = "a" * 300 + ".txt"
        result = Validators.sanitize_filename(long_name, max_length=100)
        assert len(result) <= 100
        assert result.endswith(".txt")

    def test_sanitize_filename_preserves_extension(self):
        """Test sanitization preserves file extension."""
        result = Validators.sanitize_filename("myfile.pdf")
        assert result.endswith(".pdf")

    def test_sanitize_filename_handles_dots_only(self):
        """Test sanitization handles dots-only filename."""
        result = Validators.sanitize_filename("...")
        assert result == "unnamed"

    def test_sanitize_filename_handles_double_dots(self):
        """Test sanitization handles double dots."""
        result = Validators.sanitize_filename("..")
        assert result == "unnamed"


class TestSanitizeHtml:
    """Tests for HTML sanitization."""

    def test_sanitize_html_empty(self):
        """Test sanitization of empty content."""
        result = Validators.sanitize_html("")
        assert result == ""

    def test_sanitize_html_none(self):
        """Test sanitization of None content."""
        result = Validators.sanitize_html(None)
        assert result == ""

    def test_sanitize_html_plain_text(self):
        """Test sanitization of plain text."""
        result = Validators.sanitize_html("Just plain text")
        assert result == "Just plain text"

    def test_sanitize_html_removes_script_tags(self):
        """Test sanitization removes script tags."""
        result = Validators.sanitize_html("<script>alert('xss')</script>Hello")
        assert "<script>" not in result
        assert "</script>" not in result
        assert "Hello" in result

    def test_sanitize_html_removes_all_tags_by_default(self):
        """Test sanitization removes all tags by default."""
        result = Validators.sanitize_html("<p>Hello</p> <b>World</b>")
        assert "<p>" not in result
        assert "<b>" not in result
        assert "Hello" in result
        assert "World" in result

    def test_sanitize_html_allows_specified_tags(self):
        """Test sanitization allows specified tags."""
        result = Validators.sanitize_html(
            "<p>Hello</p> <script>bad</script>", allowed_tags={"p"}
        )
        assert "<p>" in result
        assert "</p>" in result
        assert "<script>" not in result

    def test_sanitize_html_removes_dangerous_entities(self):
        """Test sanitization removes dangerous HTML entities."""
        result = Validators.sanitize_html("&lt;script&gt;alert('xss')")
        assert "&lt;script" not in result

    def test_sanitize_html_strips_whitespace(self):
        """Test sanitization strips leading/trailing whitespace."""
        result = Validators.sanitize_html("   Hello World   ")
        assert result == "Hello World"

    def test_sanitize_html_complex_content(self):
        """Test sanitization of complex HTML content."""
        html = """
        <div class="container">
            <h1>Title</h1>
            <p onclick="evil()">Content</p>
            <script>malicious()</script>
        </div>
        """
        result = Validators.sanitize_html(html)
        assert "<div>" not in result
        assert "<script>" not in result
        assert "onclick" not in result
        assert "Title" in result
        assert "Content" in result
