# Claude Agent SDK Integration

## Overview

This project uses the **Claude Agent SDK** for agentic workflows with tool use, and **plain API** for simple text generation.

---

## When to Use What

### Use Agent SDK (Tool-Using Agents)

**ResearchAgent** - For research workflows:
```python
from plugin.lib.claude_agent import get_research_agent

agent = get_research_agent()

# Agent autonomously:
# 1. Generates search queries
# 2. Calls web_search tool
# 3. Extracts content from URLs
# 4. Adds citations
# 5. Synthesizes findings

results = agent.conduct_research(
    topic="Rochester 2GC carburetor rebuild",
    search_depth="comprehensive",
    max_sources=20,
    search_function=my_search_func,      # You provide
    extract_function=my_extract_func,    # You provide
    citation_function=my_citation_func   # You provide
)
```

**Benefits:**
- ✅ Agent decides what to search for
- ✅ Agent manages multi-step workflow
- ✅ Tool calls are automatic
- ✅ Built-in retry and error handling
- ✅ Conversation state management

### Use Plain API (Simple Generation)

**InsightAgent / OutlineAgent** - For single-shot analysis:
```python
from plugin.lib.claude_agent import get_insight_agent

agent = get_insight_agent()

# Single API call, structured output
insights = agent.extract_insights(
    sources=research_sources,
    focus_areas=["rebuild process"]
)
```

**Benefits:**
- ✅ Faster for one-shot tasks
- ✅ Simpler implementation
- ✅ Lower cost (no tool overhead)
- ✅ Predictable token usage

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   ResearchAgent                         │
│                  (Agent SDK + Tools)                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent Loop:                                           │
│  ┌─────────────────────────────────────────────┐      │
│  │ 1. Agent: "I need to search for X"         │      │
│  │    └─> tool_use: web_search("query")       │      │
│  └─────────────────────────────────────────────┘      │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────┐      │
│  │ 2. Tool Executor: Run search_function()    │      │
│  │    └─> Return results to agent             │      │
│  └─────────────────────────────────────────────┘      │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────┐      │
│  │ 3. Agent: "Extract content from top URLs"  │      │
│  │    └─> tool_use: extract_content(url)      │      │
│  └─────────────────────────────────────────────┘      │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────┐      │
│  │ 4. Tool Executor: Run extract_function()   │      │
│  │    └─> Return content to agent             │      │
│  └─────────────────────────────────────────────┘      │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────┐      │
│  │ 5. Agent: "Add citations for sources"      │      │
│  │    └─> tool_use: add_citation(...)         │      │
│  └─────────────────────────────────────────────┘      │
│           │                                            │
│           ▼                                            │
│  ┌─────────────────────────────────────────────┐      │
│  │ 6. Agent: "Here's my analysis" (final)     │      │
│  └─────────────────────────────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘

Agent autonomously decides:
- Which tools to call
- What parameters to use
- When to stop
```

---

## Tool Definitions

The Agent SDK uses structured tool definitions that Claude understands:

```python
{
    "name": "web_search",
    "description": "Search the web for information on a topic",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to execute"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10
            }
        },
        "required": ["query"]
    }
}
```

**Claude sees this and knows:**
- It can call `web_search` to search
- It needs to provide a `query` parameter
- It can optionally specify `num_results`

---

## Complete Example: Research Workflow

```python
from plugin.lib.claude_agent import get_research_agent
from plugin.lib.web_search import WebSearch
from plugin.lib.content_extractor import ContentExtractor
from plugin.lib.citation_manager import CitationManager

# Initialize tools
web_search = WebSearch()
content_extractor = ContentExtractor()
citation_manager = CitationManager()

# Create agent
agent = get_research_agent()

# Define tool functions that agent can call
def search_function(query: str, num_results: int = 10):
    """Agent calls this to search."""
    results = web_search.search(query, max_results=num_results)
    return [
        {
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet
        }
        for r in results
    ]

def extract_function(url: str):
    """Agent calls this to extract content."""
    content = content_extractor.extract(url)
    return {
        "title": content.title,
        "content": content.content[:5000],  # Limit for context
        "author": content.author
    }

def citation_function(title: str, url: str, author: str = None):
    """Agent calls this to add citation."""
    return citation_manager.add_citation(title, url, author=author)

# Agent conducts research autonomously
results = agent.conduct_research(
    topic="How Rochester 2GC carburetor works and rebuild process",
    search_depth="comprehensive",
    max_sources=15,
    search_function=search_function,
    extract_function=extract_function,
    citation_function=citation_function
)

# Agent has:
# - Searched multiple queries
# - Extracted content from best sources
# - Created citations
# - Synthesized findings

print(f"Sources found: {len(results['sources'])}")
print(f"Citations: {len(results['citations'])}")
print(f"Summary: {results['summary'][:200]}...")
```

---

## Agent Conversation Flow

### What Happens Behind the Scenes:

**Turn 1: Agent → Tool Request**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01A",
      "name": "web_search",
      "input": {
        "query": "Rochester 2GC carburetor parts diagram",
        "num_results": 10
      }
    }
  ]
}
```

**Turn 2: User → Tool Result**
```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01A",
      "content": "[{\"title\": \"2GC Parts Breakdown\", \"url\": \"...\"}]"
    }
  ]
}
```

**Turn 3: Agent → Another Tool Request**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01B",
      "name": "extract_content",
      "input": {
        "url": "https://example.com/2gc-parts"
      }
    }
  ]
}
```

**Turn 4: User → Tool Result**
```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01B",
      "content": "{\"content\": \"The Rochester 2GC has...\"}"
    }
  ]
}
```

**Turn 5: Agent → Final Analysis**
```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Based on my research, here are the key findings..."
    }
  ]
}
```

The **agent loop** automatically manages this conversation!

---

## Benefits of Agent SDK

### 1. Autonomous Decision Making

**Without Agent SDK (Manual):**
```python
# You decide everything
queries = ["query1", "query2", "query3"]  # Manual
for query in queries:
    results = search(query)               # Manual
    for result in results[:5]:            # Manual
        content = extract(result.url)     # Manual
        analyze(content)                  # Manual
```

**With Agent SDK:**
```python
# Agent decides everything
results = agent.conduct_research(
    topic="carburetor rebuild",
    search_function=search_func
)
# Agent chose queries, selected URLs, decided what to extract
```

### 2. Adaptive Workflow

Agent can:
- Generate more queries if initial results insufficient
- Extract content only from most relevant sources
- Skip low-quality sources automatically
- Adjust search depth based on findings

### 3. Error Recovery

Agent handles:
- Failed search queries (tries variations)
- Broken URLs (skips and tries next)
- Malformed content (moves to next source)
- Rate limits (adjusts behavior)

### 4. Context Awareness

Agent remembers:
- What it already searched
- Which sources it already extracted
- Which citations it already created
- What information is still missing

---

## Cost Comparison

**Carburetor Research Example:**

### Agent SDK (ResearchAgent):
```
Turn 1: Agent plans (500 tokens)
Turn 2: Tool call web_search (200 tokens)
Turn 3: Tool results returned (500 tokens)
Turn 4: Agent analyzes results (800 tokens)
Turn 5: Tool call extract_content x5 (400 tokens)
Turn 6: Tool results returned (3000 tokens)
Turn 7: Agent synthesizes (1000 tokens)
Turn 8: Final output (2000 tokens)

Total: ~8,400 tokens ≈ $0.03
```

### Plain API (Manual orchestration):
```
Call 1: Generate queries (800 tokens)
Call 2: Analyze results (1500 tokens)
Call 3: Synthesize (2000 tokens)

Total: ~4,300 tokens ≈ $0.02
```

**Verdict:** Agent SDK costs ~50% more but provides:
- Better results (agent makes smart decisions)
- Less code (no manual orchestration)
- More robust (automatic error handling)

**Worth it** for complex research workflows!

---

## Integration with Research Skills

### Updated ResearchSkill (using Agent):

```python
from plugin.lib.claude_agent import get_research_agent

class ResearchSkill(BaseSkill):
    def __init__(self):
        self.agent = get_research_agent()
        self.web_search = WebSearch()
        self.content_extractor = ContentExtractor()
        self.citation_manager = CitationManager()

    def execute(self, input_data: SkillInput) -> SkillOutput:
        topic = input_data.get("topic")
        depth = input_data.get("search_depth", "standard")

        # Agent conducts research autonomously
        results = self.agent.conduct_research(
            topic=topic,
            search_depth=depth,
            search_function=self._search,
            extract_function=self._extract,
            citation_function=self._cite
        )

        return SkillOutput.success_result(data=results)

    def _search(self, query: str, num_results: int = 10):
        """Tool function for agent."""
        return self.web_search.search(query, max_results=num_results)

    def _extract(self, url: str):
        """Tool function for agent."""
        return self.content_extractor.extract(url)

    def _cite(self, title: str, url: str, author: str = None):
        """Tool function for agent."""
        return self.citation_manager.add_citation(title, url, author=author)
```

---

## Debugging Agent Workflows

### Enable Verbose Logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("claude_agent")

# See tool calls in real-time
agent = get_research_agent()
results = agent.conduct_research(...)
```

### Inspect Conversation History:

```python
agent = get_research_agent()
results = agent.conduct_research(...)

# See what agent did
for i, msg in enumerate(agent.conversation_history):
    print(f"\nTurn {i+1}: {msg['role']}")
    print(msg['content'][:200])
```

---

## Best Practices

### 1. Provide Good Tool Functions

**Bad:**
```python
def search_function(query):
    return []  # Always returns empty
```

**Good:**
```python
def search_function(query, num_results=10):
    try:
        results = api.search(query, limit=num_results)
        return [{
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet[:200]
        } for r in results]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
```

### 2. Set Reasonable Limits

```python
# Prevent runaway costs
agent.conduct_research(
    topic=topic,
    max_sources=20,           # Limit sources
    search_function=search,
    # Agent will stop after 10 iterations automatically
)
```

### 3. Handle Edge Cases

```python
def extract_function(url):
    # Validate URL
    if not url.startswith("http"):
        return {"error": "Invalid URL"}

    # Timeout protection
    try:
        content = extract_with_timeout(url, timeout=10)
        return {
            "content": content.text[:10000],  # Limit size
            "title": content.title
        }
    except TimeoutError:
        return {"error": "Extraction timeout"}
```

---

## Next Steps

1. ✅ Agent SDK integrated for research workflows
2. 🔄 Update ResearchSkill to use ResearchAgent
3. 📋 Add real web search API (Google Custom Search)
4. 📋 Test with carburetor research prompt
5. 📋 Expand to content drafting agent (PRIORITY 3)

---

## Further Reading

- [Claude API Documentation](https://docs.anthropic.com/)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Agent Patterns](https://docs.anthropic.com/en/docs/build-with-claude/agent-patterns)
- [Best Practices](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
