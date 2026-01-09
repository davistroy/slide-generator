"""
Async Gemini API Client for Image Generation

Async version of Gemini client for concurrent image generation.
Uses httpx for HTTP requests with connection pooling and retry logic.

Usage:
    async with AsyncGeminiClient() as client:
        image_data = await client.generate_image(
            prompt="A beautiful sunset over mountains",
            aspect_ratio="16:9"
        )

        # Batch generation
        images = await client.generate_images_batch(prompts, max_concurrent=5)
"""

import asyncio
import base64
import contextlib
import logging
import os
import time
from typing import Any, Callable, Literal

import httpx

from plugin.lib.connection_pool import ConnectionPool
from plugin.lib.rate_limiter import APIRateLimiter, get_global_rate_limiter
from plugin.types import ImageSpec


logger = logging.getLogger(__name__)


class AsyncGeminiClient:
    """
    Async client for Gemini API image generation.

    Features:
    - Async image generation with Gemini
    - Batch generation with concurrency control
    - Connection pooling
    - Automatic retries with exponential backoff
    - Rate limiting support
    - Context manager support

    Args:
        api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        model: Gemini model to use (default: gemini-3-pro-image-preview)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 2.0)
        rate_limit_delay: Delay between requests in seconds (default: 1.0)
        pool_size: Connection pool size (default: 10)
        timeout: Request timeout in seconds (default: 120.0)

    Example:
        >>> async with AsyncGeminiClient() as client:
        ...     image = await client.generate_image("A sunset", aspect_ratio="16:9")
        ...     with open("image.jpg", "wb") as f:
        ...         f.write(image)
    """

    # Gemini API endpoints
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    # Image size mappings
    IMAGE_SIZES = {
        "low": "STANDARD",
        "medium": "STANDARD",
        "high": "LARGE",
    }

    # Aspect ratio mappings
    ASPECT_RATIOS = {
        "16:9": "16:9",
        "9:16": "9:16",
        "4:3": "4:3",
        "3:4": "3:4",
        "1:1": "1:1",
        "5:4": "5:4",
    }

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3-pro-image-preview",
        max_retries: int = 3,
        retry_delay: float = 2.0,
        rate_limit_delay: float = 1.0,
        pool_size: int = 10,
        timeout: float = 120.0,
        rate_limiter: APIRateLimiter | None = None,
    ):
        """Initialize async Gemini client."""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. Set it in .env file or pass as parameter."
            )

        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_delay = rate_limit_delay

        # Connection pool settings
        self._pool_size = pool_size
        self._timeout = timeout
        self._pool: ConnectionPool | None = None

        # Rate limiting - use global limiter by default
        self.rate_limiter = rate_limiter or get_global_rate_limiter()
        self._last_request_time: float = 0.0
        self._rate_limit_lock = asyncio.Lock()

    async def __aenter__(self) -> "AsyncGeminiClient":
        """Enter async context manager."""
        await self._initialize_pool()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self._cleanup_pool()

    async def _initialize_pool(self) -> None:
        """Initialize connection pool."""
        self._pool = ConnectionPool(
            pool_size=self._pool_size,
            timeout=self._timeout,
        )
        await self._pool.__aenter__()

    async def _cleanup_pool(self) -> None:
        """Clean up connection pool."""
        if self._pool:
            await self._pool.__aexit__(None, None, None)
            self._pool = None

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests using global limiter."""
        # Use global rate limiter for cross-client rate limiting
        await self.rate_limiter.async_acquire("gemini")
        logger.debug("Rate limit acquired for Gemini API call")

        # Also apply local rate limiting for minimum delay between requests
        async with self._rate_limit_lock:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time

            if time_since_last < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_since_last)

            self._last_request_time = time.time()

    async def _retry_request(
        self, method: str, endpoint: str, **kwargs
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
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )

        # Apply rate limiting
        await self._apply_rate_limit()

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
                if (
                    400 <= e.response.status_code < 500
                    and e.response.status_code != 429
                ):
                    raise

                # Calculate backoff delay
                delay = self.retry_delay * (2**attempt)

                # For 429 (rate limit), use Retry-After header if available
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get("retry-after")
                    if retry_after:
                        with contextlib.suppress(ValueError):
                            delay = float(retry_after)

                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e

                # Wait before retry (except on last attempt)
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise last_error

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
        image_size: Literal["low", "medium", "high"] = "medium",
        negative_prompt: str | None = None,
        style_config: dict[str, Any] | None = None,
    ) -> bytes:
        """
        Generate a single image using Gemini (async).

        Args:
            prompt: Text description of the image to generate
            aspect_ratio: Aspect ratio (16:9, 9:16, 4:3, 3:4, 1:1, 5:4)
            image_size: Image size (low, medium, high)
            negative_prompt: Optional negative prompt
            style_config: Optional style configuration dict

        Returns:
            Image data as bytes (JPEG format)

        Raises:
            ValueError: If invalid aspect_ratio or image_size
            httpx.HTTPError: On API request failure

        Example:
            >>> image = await client.generate_image(
            ...     "Mountain sunset with dramatic clouds",
            ...     aspect_ratio="16:9",
            ...     image_size="high"
            ... )
        """
        # Validate aspect ratio
        if aspect_ratio not in self.ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect_ratio: {aspect_ratio}. "
                f"Must be one of: {', '.join(self.ASPECT_RATIOS.keys())}"
            )

        # Validate image size
        if image_size not in self.IMAGE_SIZES:
            raise ValueError(
                f"Invalid image_size: {image_size}. "
                f"Must be one of: {', '.join(self.IMAGE_SIZES.keys())}"
            )

        # Build full prompt with style config
        full_prompt = prompt
        if style_config:
            recipe = style_config.get("PromptRecipe", {})
            core_style = recipe.get("CoreStylePrompt", "")
            color_constraint = recipe.get("PaletteConstraintPrompt", "")
            text_enforcement = recipe.get("TextEnforcementPrompt", "")

            full_prompt = f"""{prompt}

STYLE DETAILS:
{core_style}

COLOR PALETTE:
{color_constraint}

TEXT RULES:
{text_enforcement}"""

        # Build request payload
        payload = {
            "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": self.ASPECT_RATIOS[aspect_ratio],
                    "imageSize": self.IMAGE_SIZES[image_size],
                },
            },
        }

        if negative_prompt:
            payload["generationConfig"]["imageConfig"]["negativePrompt"] = (
                negative_prompt
            )

        # Make API request
        endpoint = f"models/{self.model}:generateContent"
        params = {"key": self.api_key}

        response = await self._retry_request(
            "POST",
            endpoint,
            params=params,
            json=payload,
        )

        result = response.json()

        # Extract image data from response
        try:
            candidates = result.get("candidates", [])
            if not candidates:
                raise ValueError("No image generated in response")

            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    # Image is base64 encoded
                    image_data = part["inlineData"].get("data")
                    if image_data:
                        # Decode base64 to bytes
                        return base64.b64decode(image_data)

            raise ValueError("No image data found in response")

        except (KeyError, IndexError, ValueError) as e:
            raise ValueError(f"Failed to extract image from response: {e}")

    async def generate_image_from_spec(self, spec: ImageSpec) -> bytes:
        """
        Generate image from an ImageSpec object.

        Args:
            spec: ImageSpec with generation parameters

        Returns:
            Image data as bytes

        Example:
            >>> spec = ImageSpec(
            ...     description="A sunset",
            ...     resolution="high",
            ...     aspect_ratio="16:9"
            ... )
            >>> image = await client.generate_image_from_spec(spec)
        """
        return await self.generate_image(
            prompt=spec.description,
            aspect_ratio=spec.aspect_ratio,
            image_size=spec.resolution,
            style_config={"PromptRecipe": {"CoreStylePrompt": spec.style or ""}},
        )

    async def generate_images_batch(
        self,
        prompts: list[str],
        aspect_ratio: str = "16:9",
        image_size: Literal["low", "medium", "high"] = "medium",
        max_concurrent: int = 3,
        style_config: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[bytes]:
        """
        Generate multiple images concurrently.

        Args:
            prompts: List of text prompts
            aspect_ratio: Aspect ratio for all images
            image_size: Image size for all images
            max_concurrent: Maximum concurrent requests (default: 3)
            style_config: Optional style configuration
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of image data as bytes (in same order as prompts)

        Example:
            >>> prompts = ["sunset", "mountain", "ocean"]
            >>> images = await client.generate_images_batch(
            ...     prompts,
            ...     max_concurrent=2
            ... )
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0
        total = len(prompts)

        async def generate_with_semaphore(prompt: str) -> bytes:
            nonlocal completed
            async with semaphore:
                image = await self.generate_image(
                    prompt=prompt,
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                    style_config=style_config,
                )
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                return image

        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    async def generate_images_batch_with_specs(
        self,
        specs: list[ImageSpec],
        max_concurrent: int = 3,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[bytes]:
        """
        Generate multiple images from ImageSpec objects.

        Args:
            specs: List of ImageSpec objects
            max_concurrent: Maximum concurrent requests
            progress_callback: Optional callback(completed, total)

        Returns:
            List of image data as bytes (in same order as specs)

        Example:
            >>> specs = [
            ...     ImageSpec(description="sunset", resolution="high"),
            ...     ImageSpec(description="mountain", resolution="medium"),
            ... ]
            >>> images = await client.generate_images_batch_with_specs(specs)
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        completed = 0
        total = len(specs)

        async def generate_with_semaphore(spec: ImageSpec) -> bytes:
            nonlocal completed
            async with semaphore:
                image = await self.generate_image_from_spec(spec)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)
                return image

        tasks = [generate_with_semaphore(spec) for spec in specs]
        return await asyncio.gather(*tasks)

    def get_pool_stats(self) -> dict[str, Any] | None:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool stats or None if pool not initialized
        """
        if self._pool:
            return self._pool.get_stats().to_dict()
        return None


# Convenience function for getting an async Gemini client
def get_async_gemini_client(
    model: str = "gemini-3-pro-image-preview",
) -> AsyncGeminiClient:
    """
    Get a configured async Gemini client instance.

    Args:
        model: Gemini model to use

    Returns:
        AsyncGeminiClient instance (remember to use with 'async with')

    Example:
        >>> async with get_async_gemini_client() as client:
        ...     image = await client.generate_image("A sunset")
    """
    return AsyncGeminiClient(model=model)
