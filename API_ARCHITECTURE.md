# API Architecture

## Overview

The presentation generator uses a **hybrid AI approach** with different APIs and SDKs optimized for different tasks:

- **Claude Agent SDK (Anthropic)** - Agentic research with tool use
- **Claude API (Anthropic)** - Simple text generation and analysis
- **Gemini API (Google)** - Image generation only

**Why Agent SDK?** For complex research workflows, Claude agents autonomously call tools (web search, content extraction, citations), make decisions, and adapt their approach—resulting in better research quality with less code.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Input / Topic                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              RESEARCH & CONTENT (Claude Agent SDK + API)         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Research Assistant Skill (API)                       │   │
│  │    └─> Claude API: Generates clarifying questions       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 2. Research Skill (AGENT SDK with Tools)                │   │
│  │    ├─> Agent: Generates search queries autonomously     │   │
│  │    ├─> Tool: web_search() → Search APIs                 │   │
│  │    ├─> Tool: extract_content() → Content extractor      │   │
│  │    ├─> Tool: add_citation() → Citation manager          │   │
│  │    └─> Agent: Synthesizes findings                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 3. Insight Extraction Skill (API)                       │   │
│  │    └─> Claude API: Extracts insights, arguments         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 4. Outline Skill (API)                                  │   │
│  │    └─> Claude API: Generates presentation structure     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                      │                                           │
│                      ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 5. Content Drafting Skill (AGENT SDK - PRIORITY 3)     │   │
│  │    └─> Agent: Writes slide content with tool access     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
              Presentation Markdown
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                IMAGE GENERATION (Gemini API)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 6. Image Generator                                       │   │
│  │    └─> Gemini (gemini-3-pro-image-preview)             │   │
│  │        generates slide images                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
              Slide Images (.jpg)
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              PRESENTATION ASSEMBLY (Python)                      │
├─────────────────────────────────────────────────────────────────┤
│  └─> python-pptx assembles final .pptx with brand templates     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
          Final PowerPoint (.pptx)
```

---

## API Responsibilities

### Claude Agent SDK (Agentic Workflows with Tools)

**Model:** `claude-sonnet-4-5-20250929` (Claude Sonnet 4.5)

**Used For:**
1. **Research Skill** - Autonomous multi-step research workflow
   - Agent generates search queries
   - Agent calls web_search tool
   - Agent extracts content from sources
   - Agent manages citations
   - Agent synthesizes findings

**Why Agent SDK:**
- ✅ Autonomous decision-making (agent chooses what to search, what to extract)
- ✅ Tool use (web search, content extraction, citations)
- ✅ Multi-turn workflows with state management
- ✅ Adaptive behavior (adjusts based on results)
- ✅ Error recovery (retries, fallbacks)
- ✅ Better research quality (smarter than manual orchestration)

**Code Example:**
```python
from plugin.lib.claude_agent import get_research_agent

agent = get_research_agent()
results = agent.conduct_research(
    topic="Rochester 2GC carburetor",
    search_function=search,  # Agent calls this
    extract_function=extract,  # Agent calls this
    citation_function=cite  # Agent calls this
)
```

### Claude API (Simple Text Generation)

**Model:** `claude-sonnet-4-5-20250929` (Claude Sonnet 4.5)

**Used For:**
1. **Research Assistant** - Generate clarifying questions (one-shot)
2. **Insight Extraction** - Analyze sources and extract insights (one-shot)
3. **Outline Generation** - Create presentation structure (one-shot)
4. **Content Drafting** - Write slide content (PRIORITY 3)
5. **Content Optimization** - Improve quality (PRIORITY 3)

**Why Plain API:**
- ✅ Faster for single-turn tasks
- ✅ Lower cost (no tool overhead)
- ✅ Simpler implementation
- ✅ Predictable token usage

**Code Example:**
```python
from plugin.lib.claude_agent import get_insight_agent

agent = get_insight_agent()
insights = agent.extract_insights(
    sources=research_sources,
    focus_areas=["rebuild process"]
)
```

### Gemini API (Image Generation Only)

**Model:** `gemini-3-pro-image-preview`

**Used For:**
1. **Slide Image Generation** - Create visual graphics from prompts
2. **Visual Validation** - Analyze generated images (optional)

**Why Gemini:**
- Excellent image generation quality
- Good at following detailed visual prompts
- Brand-specific style adherence
- 4K resolution support

**NOT Used For:**
- Text generation
- Research
- Content analysis
- Anything non-visual

---

## Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Claude API - Research & Content
ANTHROPIC_API_KEY=sk-ant-...

# Gemini API - Images Only
GOOGLE_API_KEY=AIza...

# Optional: Model selection
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### Code Usage

**Research Agent (with Tools):**
```python
from plugin.lib.claude_agent import get_research_agent
from plugin.lib.web_search import WebSearch
from plugin.lib.content_extractor import ContentExtractor
from plugin.lib.citation_manager import CitationManager

# Initialize tools
web_search = WebSearch()
content_extractor = ContentExtractor()
citation_manager = CitationManager()

# Get research agent
agent = get_research_agent()

# Agent conducts research autonomously
results = agent.conduct_research(
    topic="Rochester 2GC carburetor rebuild",
    search_depth="comprehensive",
    max_sources=20,
    search_function=lambda q, n: web_search.search(q, max_results=n),
    extract_function=lambda url: content_extractor.extract(url),
    citation_function=lambda t, u, a=None: citation_manager.add_citation(t, u, author=a)
)
# Agent has searched, extracted content, added citations, and synthesized findings!
```

**Insight & Outline Agents (Simple API):**
```python
from plugin.lib.claude_agent import get_insight_agent, get_outline_agent

# Extract insights (one API call)
insight_agent = get_insight_agent()
insights = insight_agent.extract_insights(
    sources=results['sources'],
    focus_areas=["rebuild process", "common issues"]
)

# Generate outline (one API call)
outline_agent = get_outline_agent()
outline = outline_agent.generate_outline(
    research_data=results,
    insights_data=insights,
    audience="technical DIY mechanics",
    duration_minutes=45
)
```

**Gemini Client (Images):**
```python
from lib.gemini_client import GeminiClient

# Get Gemini client (images only)
gemini = GeminiClient()

# Generate slide image
image_path = gemini.generate_image(
    prompt=image_prompt,
    output_path="slide-01.jpg",
    style_config=style_config
)
```

---

## Fallback Strategy

**Primary:** Claude API (Anthropic)

**Fallback:** ChatGPT API (OpenAI) - Not yet implemented

If Claude API is unavailable:
1. System will attempt ChatGPT API as fallback
2. Set `OPENAI_API_KEY` in `.env`
3. Uses similar prompts/structure

**Image Generation:**
- Gemini only, no fallback needed
- Already proven stable and high-quality

---

## Cost Estimates

**Typical Carburetor Research + Presentation:**

### Claude Agent SDK (Research Phase):
- Research Agent (multi-turn with tools):
  - Turn 1-2: Generate queries (~1K tokens)
  - Turn 3-4: Process search results (~2K tokens)
  - Turn 5-8: Extract content (~4K tokens)
  - Turn 9-10: Synthesize findings (~2K tokens)
  - **Subtotal: ~9K tokens ≈ $0.04**

### Claude API (Analysis Phase):
- Insight Extraction: ~5K tokens ($0.02)
- Outline Generation: ~3K tokens ($0.01)
- **Subtotal: ~8K tokens ≈ $0.03**

- **Total Research + Analysis:** ~$0.07

### Claude API (Content Phase - PRIORITY 3):
- Content Drafting (20 slides): ~30K tokens ($0.120)
- Content Optimization: ~10K tokens ($0.040)
- **Total Content:** ~$0.16

### Gemini API (Images):
- Image Generation (20 slides): ~$2.00
- Visual Validation (optional): ~$0.50
- **Total Images:** ~$2.50

**Grand Total per Presentation:** ~$2.73

**Note:** Agent SDK adds ~$0.03 to research costs vs manual orchestration, but provides:
- Better research quality (agent makes smarter decisions)
- Autonomous workflow (less code to maintain)
- Error recovery and retry logic
- Adaptive behavior based on results

---

## Integration Status

### ✅ Implemented:
- Gemini image generation (production-ready)
- Claude Agent SDK for research workflows
- Claude API for insights and outlines
- Mock research skills with agent architecture

### 🚧 In Progress:
- Integrate ResearchAgent into ResearchSkill
- Add real web search API (Google Custom Search or Bing)
- Test with real carburetor research

### 📋 Planned (PRIORITY 3):
- Content drafting agent with Claude
- Content optimization with Claude
- ChatGPT fallback implementation

---

## Next Steps

1. **Install Anthropic SDK:**
   ```bash
   pip install anthropic
   ```

2. **Get Claude API Key:**
   - Visit https://console.anthropic.com/
   - Create an API key
   - Add to `.env` as `ANTHROPIC_API_KEY`

3. **Test Integration:**
   ```bash
   python test_claude_integration.py
   ```

4. **Add Real Search API:**
   - Google Custom Search API, or
   - Bing Search API
   - See `plugin/lib/web_search.py` for integration points

---

## Security Notes

- ✅ Never commit `.env` to git (in `.gitignore`)
- ✅ API keys loaded from environment only
- ✅ Separate keys for different services
- ✅ Production keys separate from development

---

## Support

**Claude API Issues:**
- Docs: https://docs.anthropic.com/
- Status: https://status.anthropic.com/

**Gemini API Issues:**
- Docs: https://ai.google.dev/docs
- Get Key: https://aistudio.google.com/app/apikey
