"""
Async Claude API Client for Research and Content Generation

Async version of ClaudeClient using httpx for HTTP requests.
Supports concurrent operations, connection pooling, and automatic retries.

Usage:
    async with AsyncClaudeClient() as client:
        text = await client.generate_text("What is AI?")

        # Stream response
        async for chunk in client.stream_text("Explain quantum computing"):
            print(chunk, end="")
"""

import asyncio
import json
import os
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from plugin.lib.connection_pool import ConnectionPool
from plugin.types import JSONObject

# Load environment variables
load_dotenv()


class AsyncClaudeClient:
    """
    Async client for Claude API operations.

    Features:
    - Async text generation with Claude
    - Streaming responses
    - Tool use support (for agent workflows)
    - Connection pooling
    - Automatic retries with exponential backoff
    - Context manager support

    Args:
        api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        model: Claude model to use (default: Claude Sonnet 4.5)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 1.0)
        pool_size: Connection pool size (default: 10)
        timeout: Request timeout in seconds (default: 60.0)

    Example:
        >>> async with AsyncClaudeClient() as client:
        ...     response = await client.generate_text("Hello!")
        ...     print(response)
    """

    # Anthropic API endpoint
    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        pool_size: int = 10,
        timeout: float = 60.0,
    ):
        """Initialize async Claude client."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in .env file or pass as parameter."
            )

        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Connection pool settings
        self._pool_size = pool_size
        self._timeout = timeout
        self._pool: Optional[ConnectionPool] = None

    async def __aenter__(self) -> "AsyncClaudeClient":
        """Enter async context manager."""
        await self._initialize_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self._cleanup_pool()

    async def _initialize_pool(self) -> None:
        """Initialize connection pool."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

        self._pool = ConnectionPool(
            pool_size=self._pool_size,
            timeout=self._timeout,
            headers=headers,
        )
        await self._pool.__aenter__()

    async def _cleanup_pool(self) -> None:
        """Clean up connection pool."""
        if self._pool:
            await self._pool.__aexit__(None, None, None)
            self._pool = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

    async def _retry_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            **kwargs: Additional request arguments

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: After all retries exhausted
        """
        if not self._pool:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        url = f"{self.API_BASE}/{endpoint}"
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self._pool.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                last_error = e

                # Don't retry on client errors (4xx except 429)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise

                # Calculate backoff delay
                delay = self.retry_delay * (2 ** attempt)

                # For 429 (rate limit), use Retry-After header if available
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("retry-after")
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except ValueError:
                            pass

                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e

                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise last_error

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        stop_sequences: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text using Claude (async).

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stop_sequences: Optional stop sequences
            **kwargs: Additional parameters for the API

        Returns:
            Generated text response

        Example:
            >>> text = await client.generate_text("Explain AI in simple terms")
        """
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            **kwargs
        }

        if system_prompt:
            payload["system"] = system_prompt

        if stop_sequences:
            payload["stop_sequences"] = stop_sequences

        response = await self._retry_request(
            "POST",
            "messages",
            json=payload,
        )

        result = response.json()
        return result["content"][0]["text"]

    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response with tool use support (async).

        Used for agent workflows where Claude can call tools.

        Args:
            prompt: The user prompt
            tools: List of tool definitions
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional API parameters

        Returns:
            Full API response with content and tool uses

        Example:
            >>> tools = [{"name": "search", "description": "Search the web", ...}]
            >>> response = await client.generate_with_tools("Find info on AI", tools)
        """
        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "tools": tools,
            **kwargs
        }

        if system_prompt:
            payload["system"] = system_prompt

        response = await self._retry_request(
            "POST",
            "messages",
            json=payload,
        )

        return response.json()

    async def stream_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate text with streaming response (async).

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional API parameters

        Yields:
            Text chunks as they are generated

        Example:
            >>> async for chunk in client.stream_text("Write a story"):
            ...     print(chunk, end="")
        """
        if not self._pool:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
            "stream": True,
            **kwargs
        }

        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.API_BASE}/messages"

        async with self._pool.stream("POST", url, json=payload) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                # Parse SSE format: "data: {...}"
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix

                    # Skip "[DONE]" message
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)

                        # Handle different event types
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                if text:
                                    yield text

                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        continue

    async def analyze_content(
        self,
        content: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content using Claude (async).

        Args:
            content: Content to analyze
            analysis_type: Type of analysis (insights, themes, summary, etc.)
            context: Additional context for analysis

        Returns:
            Analysis results as dictionary

        Example:
            >>> analysis = await client.analyze_content(text, "insights")
        """
        context_str = ""
        if context:
            context_str = "\n\nContext:\n" + "\n".join(
                f"- {k}: {v}" for k, v in context.items()
            )

        prompt = f"""Analyze the following content and extract {analysis_type}.

Content:
{content}
{context_str}

Provide your analysis as a JSON object."""

        system_prompt = f"""You are an expert content analyst. Extract {analysis_type}
from the provided content and return results as valid JSON."""

        response = await self.generate_text(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )

        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            # If parsing fails, return raw text
            return {"analysis": response}

    async def batch_generate(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        max_concurrent: int = 5,
        **kwargs
    ) -> List[str]:
        """
        Generate text for multiple prompts concurrently.

        Args:
            prompts: List of prompts to process
            system_prompt: Optional system prompt for all requests
            max_concurrent: Maximum concurrent requests (default: 5)
            **kwargs: Additional parameters for generate_text

        Returns:
            List of generated text responses (in same order as prompts)

        Example:
            >>> prompts = ["What is AI?", "What is ML?", "What is DL?"]
            >>> results = await client.batch_generate(prompts, max_concurrent=3)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_with_semaphore(prompt: str) -> str:
            async with semaphore:
                return await self.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    **kwargs
                )

        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def get_pool_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool stats or None if pool not initialized
        """
        if self._pool:
            return self._pool.get_stats().to_dict()
        return None


# Convenience function for getting an async client instance
def get_async_claude_client(model: str = "claude-sonnet-4-5-20250929") -> AsyncClaudeClient:
    """
    Get a configured async Claude client instance.

    Args:
        model: Claude model to use

    Returns:
        AsyncClaudeClient instance (remember to use with 'async with')

    Example:
        >>> async with get_async_claude_client() as client:
        ...     text = await client.generate_text("Hello!")
    """
    return AsyncClaudeClient(model=model)
