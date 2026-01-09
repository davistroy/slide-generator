# ADR-001: Dual API Strategy (Claude + Gemini)

## Status
Accepted

## Date
2025-01-08

## Context

The slide-generator project requires two distinct AI capabilities:
1. **Text Generation**: Research queries, content analysis, outline generation, content drafting, quality optimization
2. **Image Generation**: Creating visuals for presentation slides

We needed to select AI providers that excel in their respective domains while considering cost, performance, and quality.

## Decision

We adopt a **dual API strategy**:

- **Claude (Anthropic)**: All text-based operations
  - Research and content analysis
  - Insight extraction
  - Outline generation
  - Content drafting
  - Quality optimization
  - Clarifying questions

- **Gemini (Google)**: Image generation only
  - Slide graphics
  - Visual assets
  - No text operations

## Rationale

### Claude for Text Operations

1. **Superior text quality**: Claude excels at complex reasoning, nuanced writing, and maintaining consistent tone across long documents.

2. **Agent SDK support**: Claude's Agent SDK enables autonomous multi-step workflows with tool use, critical for the research phase.

3. **JSON mode reliability**: Claude reliably produces structured JSON output for parsing outlines, insights, and content.

4. **Context handling**: Claude handles large context windows well, essential when processing research results and generating comprehensive outlines.

### Gemini for Image Generation

1. **Native image generation**: Gemini has built-in image generation capabilities optimized for this task.

2. **Style control**: Gemini provides good control over aspect ratio, resolution, and style parameters.

3. **Cost efficiency**: Gemini's image generation pricing is competitive for batch image creation.

4. **API simplicity**: The image generation API is straightforward with clear parameters.

## Consequences

### Positive

- **Best-of-breed**: Each API is used for its strengths
- **Cost optimization**: Pay for specialized capabilities rather than general-purpose models
- **Quality**: Superior output quality in both text and images
- **Flexibility**: Can independently upgrade or swap providers for each capability

### Negative

- **Multiple API keys**: Requires managing two API credentials
- **Different error patterns**: Need to handle different error responses from each provider
- **Rate limiting complexity**: Must manage rate limits for two separate APIs
- **Dependency risk**: Changes to either API affect the system

### Mitigations

1. **Centralized configuration**: Single `.env` file for all API keys
2. **Unified error handling**: Common exception handling patterns across both APIs
3. **Global rate limiter**: `APIRateLimiter` class manages limits for both providers
4. **Abstraction layers**: Client classes abstract away API differences

## Implementation

### File Structure

```
plugin/lib/
├── claude_client.py        # Sync Claude client
├── async_claude_client.py  # Async Claude client
├── claude_agent.py         # Agent SDK integration
├── async_gemini_client.py  # Async Gemini client (images)
└── rate_limiter.py         # Shared rate limiting
```

### Usage Pattern

```python
# Text operations - always Claude
from plugin.lib.claude_client import get_claude_client
client = get_claude_client()
outline = client.generate_outline(research_data, insights_data)

# Image operations - always Gemini
async with get_async_gemini_client() as client:
    image = await client.generate_image(prompt, aspect_ratio="16:9")
```

## Alternatives Considered

1. **Single provider (Claude only)**: Claude lacks native image generation
2. **Single provider (Gemini only)**: Gemini text quality is lower for complex content generation
3. **OpenAI (DALL-E + GPT)**: Higher cost, less control over image style
4. **Stable Diffusion (self-hosted)**: Operational complexity, infrastructure costs

## References

- Claude API Documentation: https://docs.anthropic.com/
- Gemini API Documentation: https://ai.google.dev/
- Project CLAUDE.md: Technology stack section
