"""
JSON utilities for parsing LLM responses.

This module provides utilities for extracting JSON from LLM responses,
which often contain JSON wrapped in markdown code blocks.
"""

import json
import re
from typing import Any


class JSONExtractionError(Exception):
    """Raised when JSON cannot be extracted from a response."""

    def __init__(self, message: str, response_preview: str = ""):
        super().__init__(message)
        self.response_preview = response_preview


def extract_json_from_response(
    response: str,
    fallback: dict[str, Any] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """
    Extract JSON from an LLM response that may contain markdown code blocks.

    Handles common response formats:
    - ```json\n{...}\n```
    - ```\n{...}\n```
    - Raw JSON string

    Args:
        response: The LLM response text
        fallback: Optional fallback value if parsing fails (default: None)
        strict: If True, raise exception on failure; if False, return fallback

    Returns:
        Parsed JSON as a dictionary

    Raises:
        JSONExtractionError: If strict=True and JSON cannot be extracted

    Examples:
        >>> extract_json_from_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}

        >>> extract_json_from_response('invalid', fallback={'error': True})
        {'error': True}
    """
    if not response or not response.strip():
        if strict:
            raise JSONExtractionError("Empty response received")
        return fallback if fallback is not None else {}

    json_str = _extract_json_string(response)

    try:
        result = json.loads(json_str)
        if isinstance(result, dict):
            return result
        elif isinstance(result, list):
            # Wrap list in a dict for consistency
            return {"items": result}
        else:
            # Primitive value - wrap it
            return {"value": result}

    except json.JSONDecodeError as e:
        if strict:
            preview = response[:200] + "..." if len(response) > 200 else response
            raise JSONExtractionError(
                f"Failed to parse JSON: {e}", response_preview=preview
            ) from e

        return fallback if fallback is not None else {}


def extract_json_list_from_response(
    response: str,
    fallback: list[Any] | None = None,
    strict: bool = False,
) -> list[Any]:
    """
    Extract a JSON list from an LLM response.

    Similar to extract_json_from_response but expects and returns a list.

    Args:
        response: The LLM response text
        fallback: Optional fallback value if parsing fails (default: [])
        strict: If True, raise exception on failure; if False, return fallback

    Returns:
        Parsed JSON as a list

    Raises:
        JSONExtractionError: If strict=True and JSON list cannot be extracted
    """
    if not response or not response.strip():
        if strict:
            raise JSONExtractionError("Empty response received")
        return fallback if fallback is not None else []

    json_str = _extract_json_string(response)

    try:
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and "items" in result:
            # Unwrap if it was wrapped
            return result["items"]
        else:
            # Single item - wrap in list
            return [result]

    except json.JSONDecodeError as e:
        if strict:
            preview = response[:200] + "..." if len(response) > 200 else response
            raise JSONExtractionError(
                f"Failed to parse JSON list: {e}", response_preview=preview
            ) from e

        return fallback if fallback is not None else []


def _extract_json_string(response: str) -> str:
    """
    Extract the JSON string from a response, handling markdown code blocks.

    Args:
        response: The raw response text

    Returns:
        The extracted JSON string (not yet parsed)
    """
    response = response.strip()

    # Try to extract from ```json ... ``` block
    if "```json" in response:
        try:
            json_str = response.split("```json")[1].split("```")[0].strip()
            return json_str
        except IndexError:
            pass

    # Try to extract from ``` ... ``` block
    if "```" in response:
        try:
            json_str = response.split("```")[1].split("```")[0].strip()
            # Skip if it looks like a language identifier (no newline)
            if "\n" in json_str or json_str.startswith("{") or json_str.startswith("["):
                return json_str
        except IndexError:
            pass

    # Try to find JSON object or array directly
    # Look for first { or [ and matching closing bracket
    json_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", response)
    if json_match:
        return json_match.group(1)

    # Return as-is and let json.loads handle it
    return response


def safe_json_loads(
    text: str,
    default: Any = None,
) -> Any:
    """
    Safely parse a JSON string, returning a default value on failure.

    Unlike extract_json_from_response, this doesn't handle markdown
    code blocks - use it only for raw JSON strings.

    Args:
        text: The JSON string to parse
        default: Value to return if parsing fails

    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
