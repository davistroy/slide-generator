"""
Input validation utilities for the slide-generator plugin system.

This module provides:
- API key validation
- URL validation
- File path validation and sanitization
- Topic validation
- HTML sanitization

All validators return ValidationResult from plugin.types.
"""

import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from plugin.types import ValidationResult


class Validators:
    """Static validation utilities for input sanitization and security."""

    # Common test API key patterns to reject in production
    TEST_KEY_PATTERNS = [
        r"test",
        r"demo",
        r"example",
        r"sk-ant-api\d{2}-test",
        r"AIza[a-zA-Z0-9_-]{35}test",
        r"1{20,}",
        r"0{20,}",
    ]

    # Dangerous path components
    DANGEROUS_PATH_COMPONENTS = [
        "..",
        "~",
        "$",
        "`",
        "|",
        "&",
        ";",
        "\n",
        "\r",
    ]

    # Valid URL schemes
    VALID_URL_SCHEMES = ["http", "https"]

    # HTML tag pattern for basic sanitization
    HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

    @staticmethod
    def validate_api_key(key: str, provider: str) -> ValidationResult:
        """
        Validate API key format for security and correctness.

        Args:
            key: The API key to validate
            provider: The API provider ('claude', 'gemini', 'anthropic', 'google')

        Returns:
            ValidationResult with validation status and any errors

        Examples:
            >>> result = Validators.validate_api_key("sk-ant-api03-...", "claude")
            >>> if result.is_valid:
            ...     print("Valid key")
        """
        errors = []
        warnings = []

        # Check if key is empty
        if not key or not key.strip():
            errors.append(f"API key for {provider} is empty")
            return ValidationResult(is_valid=False, errors=errors)

        key = key.strip()

        # Check minimum length
        if len(key) < 20:
            errors.append(
                f"API key for {provider} is too short (minimum 20 characters)"
            )

        # Check maximum length (reasonable upper bound)
        if len(key) > 200:
            errors.append(
                f"API key for {provider} is too long (maximum 200 characters)"
            )

        # Provider-specific validation
        provider_lower = provider.lower()

        if provider_lower in ["claude", "anthropic"]:
            # Anthropic keys typically start with sk-ant-
            if not key.startswith("sk-ant-"):
                warnings.append(
                    f"API key for {provider} doesn't match expected format (should start with 'sk-ant-')"
                )

        elif provider_lower in ["gemini", "google"]:
            # Google API keys typically start with AIza
            if not key.startswith("AIza"):
                warnings.append(
                    f"API key for {provider} doesn't match expected format (should start with 'AIza')"
                )

        # Check for obvious test values (only in production-like environments)
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["production", "prod"]:
            for pattern in Validators.TEST_KEY_PATTERNS:
                if re.search(pattern, key, re.IGNORECASE):
                    errors.append(
                        f"API key for {provider} appears to be a test key (not allowed in production)"
                    )
                    break

        # Check for whitespace (keys shouldn't have internal whitespace)
        if " " in key or "\t" in key or "\n" in key:
            errors.append(f"API key for {provider} contains invalid whitespace")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """
        Validate URL format and security.

        Args:
            url: The URL to validate

        Returns:
            ValidationResult with validation status and any errors

        Examples:
            >>> result = Validators.validate_url("https://example.com")
            >>> result.is_valid
            True
        """
        errors = []
        warnings = []

        # Check if URL is empty
        if not url or not url.strip():
            errors.append("URL is empty")
            return ValidationResult(is_valid=False, errors=errors)

        url = url.strip()

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            errors.append(f"Invalid URL format: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)

        # Check scheme
        if not parsed.scheme:
            errors.append("URL is missing scheme (http/https)")
        elif parsed.scheme.lower() not in Validators.VALID_URL_SCHEMES:
            errors.append(
                f"URL scheme '{parsed.scheme}' is not allowed (use http or https)"
            )

        # Check netloc (domain)
        if not parsed.netloc:
            errors.append("URL is missing domain")

        # Warn about localhost/internal IPs in production
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["production", "prod"]:
            if parsed.netloc.lower() in ["localhost", "127.0.0.1", "0.0.0.0"]:
                warnings.append(
                    "URL points to localhost (may not be accessible in production)"
                )

        # Check for suspicious characters
        suspicious_chars = ["<", ">", '"', "'", "`"]
        for char in suspicious_chars:
            if char in url:
                errors.append(f"URL contains suspicious character: {char}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    @staticmethod
    def validate_file_path(
        path: str, must_exist: bool = False, allow_create: bool = True
    ) -> ValidationResult:
        """
        Validate file path for security (path traversal attacks, etc.).

        Args:
            path: The file path to validate
            must_exist: If True, path must exist
            allow_create: If True, allows paths that don't exist (for new files)

        Returns:
            ValidationResult with validation status and any errors

        Examples:
            >>> result = Validators.validate_file_path("/tmp/output.txt")
            >>> result.is_valid
            True
        """
        errors = []
        warnings = []

        # Check if path is empty
        if not path or not path.strip():
            errors.append("File path is empty")
            return ValidationResult(is_valid=False, errors=errors)

        path = path.strip()

        # Check for dangerous path components
        for component in Validators.DANGEROUS_PATH_COMPONENTS:
            if component in path:
                errors.append(
                    f"File path contains dangerous component: '{component}'"
                )

        # Check for null bytes
        if "\x00" in path:
            errors.append("File path contains null bytes")

        # Normalize path to check for traversal
        try:
            normalized_path = os.path.normpath(path)
            absolute_path = os.path.abspath(normalized_path)

            # Check if normalized path escapes expected boundaries
            # This is a basic check - in production you'd want to define allowed directories
            if ".." in normalized_path.split(os.sep):
                errors.append(
                    "File path contains directory traversal attempts (..)"
                )

        except Exception as e:
            errors.append(f"Invalid file path: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)

        # Check existence if required
        if must_exist:
            if not os.path.exists(absolute_path):
                errors.append(f"File path does not exist: {path}")
        elif not allow_create:
            if not os.path.exists(absolute_path):
                errors.append(f"File path does not exist and creation is not allowed")

        # Check if parent directory exists for new files
        if not os.path.exists(absolute_path):
            parent_dir = os.path.dirname(absolute_path)
            if parent_dir and not os.path.exists(parent_dir):
                errors.append(f"Parent directory does not exist: {parent_dir}")

        # Warn about system directories in production
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["production", "prod"]:
            system_dirs = ["/etc", "/sys", "/proc", "/dev", "/bin", "/sbin"]
            for sys_dir in system_dirs:
                if absolute_path.startswith(sys_dir):
                    warnings.append(
                        f"File path is in system directory: {sys_dir} (potentially dangerous)"
                    )

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    @staticmethod
    def validate_topic(topic: str, max_length: int = 500) -> ValidationResult:
        """
        Validate research topic for security and reasonableness.

        Args:
            topic: The research topic to validate
            max_length: Maximum allowed length for topic

        Returns:
            ValidationResult with validation status and any errors

        Examples:
            >>> result = Validators.validate_topic("Climate change impacts")
            >>> result.is_valid
            True
        """
        errors = []
        warnings = []

        # Check if topic is empty
        if not topic or not topic.strip():
            errors.append("Topic is empty")
            return ValidationResult(is_valid=False, errors=errors)

        topic = topic.strip()

        # Check minimum length
        if len(topic) < 3:
            errors.append("Topic is too short (minimum 3 characters)")

        # Check maximum length
        if len(topic) > max_length:
            errors.append(
                f"Topic is too long (maximum {max_length} characters, got {len(topic)})"
            )

        # Check for suspicious patterns
        suspicious_patterns = [
            (r"<script", "HTML script tags"),
            (r"javascript:", "JavaScript protocol"),
            (r"on\w+\s*=", "Event handlers"),
            (r"\$\{", "Template injection"),
            (r"``", "Command injection"),
        ]

        for pattern, description in suspicious_patterns:
            if re.search(pattern, topic, re.IGNORECASE):
                errors.append(f"Topic contains suspicious pattern: {description}")

        # Check for excessive special characters
        special_char_count = sum(1 for c in topic if not c.isalnum() and not c.isspace())
        if special_char_count > len(topic) * 0.3:
            warnings.append(
                "Topic contains many special characters (may indicate injection attempt)"
            )

        # Check for control characters
        if any(ord(c) < 32 and c not in ["\n", "\r", "\t"] for c in topic):
            errors.append("Topic contains control characters")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)

    @staticmethod
    def sanitize_filename(filename: str, max_length: int = 255) -> str:
        """
        Sanitize filename for safe filesystem use.

        Args:
            filename: The filename to sanitize
            max_length: Maximum allowed filename length

        Returns:
            Sanitized filename safe for filesystem use

        Examples:
            >>> Validators.sanitize_filename("my/bad\\filename?.txt")
            'my_bad_filename.txt'
        """
        if not filename:
            return "unnamed"

        # Get the base name (remove any path components)
        filename = os.path.basename(filename)

        # Replace dangerous characters with underscores
        dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(dangerous_chars, "_", filename)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Replace multiple underscores with single underscore
        sanitized = re.sub(r"_+", "_", sanitized)

        # Truncate to max length while preserving extension
        if len(sanitized) > max_length:
            name, ext = os.path.splitext(sanitized)
            max_name_length = max_length - len(ext)
            sanitized = name[:max_name_length] + ext

        # If empty after sanitization, use default
        if not sanitized or sanitized in [".", ".."]:
            sanitized = "unnamed"

        return sanitized

    @staticmethod
    def sanitize_html(content: str, allowed_tags: Optional[set] = None) -> str:
        """
        Basic HTML sanitization by removing tags.

        Note: This is a basic implementation. For production use with
        user-generated content, consider using a library like bleach.

        Args:
            content: The HTML content to sanitize
            allowed_tags: Set of allowed tag names (e.g., {'p', 'br', 'strong'})
                         If None, removes all tags

        Returns:
            Sanitized content with HTML tags removed or filtered

        Examples:
            >>> Validators.sanitize_html("<script>alert('xss')</script>Hello")
            'Hello'
        """
        if not content:
            return ""

        if allowed_tags is None:
            # Remove all HTML tags
            sanitized = Validators.HTML_TAG_PATTERN.sub("", content)
        else:
            # Remove only disallowed tags
            def replace_tag(match):
                tag_content = match.group(0)
                # Extract tag name
                tag_match = re.match(r"</?(\w+)", tag_content)
                if tag_match:
                    tag_name = tag_match.group(1).lower()
                    if tag_name in allowed_tags:
                        return tag_content
                return ""

            sanitized = Validators.HTML_TAG_PATTERN.sub(replace_tag, content)

        # Remove any remaining HTML entities that might be dangerous
        dangerous_entities = ["&lt;script", "&lt;iframe", "&lt;object"]
        for entity in dangerous_entities:
            sanitized = sanitized.replace(entity, "")

        return sanitized.strip()
