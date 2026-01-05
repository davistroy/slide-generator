"""
Secure configuration loading and management.

This module provides:
- Secure loading of API keys from environment variables
- Configuration validation
- Sensitive value masking for logs
- Environment-specific configuration
- Integration with validators

Security features:
- No API keys from files in production
- Automatic validation of all loaded config
- Sensitive data masking in logs
- Environment-aware security policies
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Literal

from plugin.lib.validators import Validators
from plugin.types import SkillConfig, ValidationResult


logger = logging.getLogger(__name__)

Environment = Literal["development", "testing", "production"]


@dataclass
class EnvironmentConfig:
    """
    Environment-specific configuration settings.

    Attributes:
        name: Environment name
        allow_test_keys: Whether to allow test API keys
        require_https: Whether to require HTTPS for URLs
        strict_validation: Whether to enforce strict validation
        log_level: Default log level for this environment
    """

    name: Environment
    allow_test_keys: bool = False
    require_https: bool = False
    strict_validation: bool = False
    log_level: str = "INFO"

    @staticmethod
    def from_name(name: str) -> "EnvironmentConfig":
        """
        Create environment config from name.

        Args:
            name: Environment name

        Returns:
            EnvironmentConfig instance
        """
        name_lower = name.lower()

        if name_lower in ["prod", "production"]:
            return EnvironmentConfig(
                name="production",
                allow_test_keys=False,
                require_https=True,
                strict_validation=True,
                log_level="WARNING",
            )
        elif name_lower in ["test", "testing"]:
            return EnvironmentConfig(
                name="testing",
                allow_test_keys=True,
                require_https=False,
                strict_validation=True,
                log_level="INFO",
            )
        else:  # development
            return EnvironmentConfig(
                name="development",
                allow_test_keys=True,
                require_https=False,
                strict_validation=False,
                log_level="DEBUG",
            )


class SecureConfigLoader:
    """
    Secure configuration loader for API keys and sensitive settings.

    Loads configuration from environment variables with validation
    and security best practices.
    """

    # Environment variable names
    ENV_VAR_NAMES = {
        "claude_api_key": "ANTHROPIC_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "gemini_api_key": "GOOGLE_API_KEY",
        "google_api_key": "GOOGLE_API_KEY",
        "environment": "ENVIRONMENT",
    }

    # Default configuration values
    DEFAULTS: SkillConfig = {
        "model": "claude-sonnet-4-5-20250929",
        "max_tokens": 4096,
        "temperature": 1.0,
        "timeout": 300,
        "retry_attempts": 3,
        "verbose": False,
    }

    def __init__(
        self,
        environment: str | None = None,
        allow_defaults: bool = True,
    ):
        """
        Initialize secure config loader.

        Args:
            environment: Environment name (development/testing/production)
                        If None, reads from ENVIRONMENT env var
            allow_defaults: Whether to use default values for missing config
        """
        # Determine environment
        env_name = environment or os.getenv("ENVIRONMENT", "development")
        self.env_config = EnvironmentConfig.from_name(env_name)
        self.allow_defaults = allow_defaults

        logger.info(
            f"Initialized SecureConfigLoader for environment: {self.env_config.name}"
        )

    @staticmethod
    def mask_sensitive_value(value: str, show_chars: int = 4) -> str:
        """
        Mask sensitive value for safe logging.

        Shows only first and last N characters, masks the middle.

        Args:
            value: The sensitive value to mask
            show_chars: Number of characters to show at start/end

        Returns:
            Masked value safe for logging

        Examples:
            >>> SecureConfigLoader.mask_sensitive_value("sk-ant-api03-abcd1234")
            'sk-a...1234'
        """
        if not value:
            return "[empty]"

        if len(value) <= show_chars * 2:
            return "*" * len(value)

        start = value[:show_chars]
        end = value[-show_chars:]
        return f"{start}...{end}"

    def _load_from_env(self, key: str) -> str | None:
        """
        Load value from environment variable.

        Args:
            key: Configuration key name

        Returns:
            Value from environment or None
        """
        env_var = self.ENV_VAR_NAMES.get(key)
        if env_var:
            value = os.getenv(env_var)
            if value:
                return value.strip()
        return None

    def _validate_api_key(
        self,
        key: str,
        provider: str,
    ) -> ValidationResult:
        """
        Validate API key with environment-specific rules.

        Args:
            key: API key to validate
            provider: Provider name

        Returns:
            ValidationResult
        """
        result = Validators.validate_api_key(key, provider)

        # In production, don't allow test keys
        if not self.env_config.allow_test_keys and any(
            pattern in key.lower() for pattern in ["test", "demo", "example"]
        ):
            result.is_valid = False
            result.errors.append(
                f"Test API keys not allowed in {self.env_config.name} environment"
            )

        return result

    def load_api_key(
        self,
        provider: str,
        required: bool = True,
    ) -> str | None:
        """
        Load and validate API key for provider.

        Args:
            provider: Provider name ('claude', 'gemini', etc.)
            required: Whether the API key is required

        Returns:
            API key if found and valid, None if not required and missing

        Raises:
            ValueError: If required key is missing or invalid
        """
        provider_lower = provider.lower()
        config_key = f"{provider_lower}_api_key"

        # Load from environment
        api_key = self._load_from_env(config_key)

        if not api_key:
            if required:
                env_var = self.ENV_VAR_NAMES.get(config_key, config_key.upper())
                raise ValueError(
                    f"Required API key for {provider} not found. "
                    f"Set environment variable: {env_var}"
                )
            logger.debug(f"Optional API key for {provider} not found")
            return None

        # Validate API key
        validation = self._validate_api_key(api_key, provider)

        if not validation.is_valid:
            error_msg = f"Invalid API key for {provider}: " + "; ".join(
                validation.errors
            )
            if self.env_config.strict_validation:
                raise ValueError(error_msg)
            else:
                logger.warning(error_msg)

        # Log warnings
        for warning in validation.warnings:
            logger.warning(f"API key warning for {provider}: {warning}")

        masked_key = self.mask_sensitive_value(api_key)
        logger.info(f"Loaded API key for {provider}: {masked_key}")

        return api_key

    def load_skill_config(
        self,
        provider: str | None = None,
        **overrides: Any,
    ) -> SkillConfig:
        """
        Load complete skill configuration.

        Args:
            provider: API provider to load key for (if any)
            **overrides: Configuration overrides

        Returns:
            Complete SkillConfig dictionary

        Examples:
            >>> loader = SecureConfigLoader()
            >>> config = loader.load_skill_config(provider="claude", max_tokens=8192)
        """
        # Start with defaults
        config: SkillConfig = {}
        if self.allow_defaults:
            config.update(self.DEFAULTS)

        # Load API key if provider specified
        if provider:
            try:
                api_key = self.load_api_key(provider, required=False)
                if api_key:
                    config["api_key"] = api_key
            except ValueError as e:
                logger.error(f"Failed to load API key: {e}")
                # Don't include api_key in config if loading failed

        # Apply overrides
        for key, value in overrides.items():
            if value is not None:
                config[key] = value  # type: ignore

        # Validate numeric values
        if "max_tokens" in config and config["max_tokens"] <= 0:
            raise ValueError("max_tokens must be positive")

        if "temperature" in config:
            temp = config["temperature"]
            if not 0 <= temp <= 2:
                raise ValueError("temperature must be between 0 and 2")

        if "timeout" in config and config["timeout"] <= 0:
            raise ValueError("timeout must be positive")

        if "retry_attempts" in config and config["retry_attempts"] < 0:
            raise ValueError("retry_attempts must be non-negative")

        return config

    def get_safe_config_for_logging(
        self,
        config: SkillConfig,
    ) -> dict[str, Any]:
        """
        Get config dictionary safe for logging (with masked sensitive values).

        Args:
            config: Configuration to sanitize

        Returns:
            Dictionary safe for logging
        """
        safe_config = dict(config)

        # Mask API key
        if "api_key" in safe_config:
            safe_config["api_key"] = self.mask_sensitive_value(safe_config["api_key"])

        return safe_config

    def validate_url(self, url: str) -> ValidationResult:
        """
        Validate URL with environment-specific rules.

        Args:
            url: URL to validate

        Returns:
            ValidationResult
        """
        result = Validators.validate_url(url)

        # In production, require HTTPS
        if self.env_config.require_https and not url.startswith("https://"):
            result.is_valid = False
            result.errors.append(
                f"HTTPS required in {self.env_config.name} environment"
            )

        return result

    def validate_file_path(
        self,
        path: str,
        must_exist: bool = False,
    ) -> ValidationResult:
        """
        Validate file path with security checks.

        Args:
            path: File path to validate
            must_exist: Whether path must exist

        Returns:
            ValidationResult
        """
        return Validators.validate_file_path(path, must_exist=must_exist)


# Global config loader instance
_global_loader: SecureConfigLoader | None = None


def get_global_config_loader() -> SecureConfigLoader:
    """
    Get the global secure config loader instance.

    Returns:
        Global SecureConfigLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = SecureConfigLoader()
    return _global_loader


def load_api_key(provider: str, required: bool = True) -> str | None:
    """
    Convenience function to load API key using global loader.

    Args:
        provider: API provider name
        required: Whether key is required

    Returns:
        API key or None

    Examples:
        >>> from plugin.lib.secure_config import load_api_key
        >>> api_key = load_api_key("claude")
    """
    loader = get_global_config_loader()
    return loader.load_api_key(provider, required=required)


def load_skill_config(
    provider: str | None = None,
    **overrides: Any,
) -> SkillConfig:
    """
    Convenience function to load skill config using global loader.

    Args:
        provider: API provider name
        **overrides: Configuration overrides

    Returns:
        SkillConfig dictionary

    Examples:
        >>> from plugin.lib.secure_config import load_skill_config
        >>> config = load_skill_config(provider="claude", max_tokens=8192)
    """
    loader = get_global_config_loader()
    return loader.load_skill_config(provider=provider, **overrides)
