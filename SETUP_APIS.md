# API Setup Guide

Quick guide to set up Claude and Gemini APIs for the presentation generator.

---

## Step 1: Install Dependencies

```bash
pip install anthropic google-genai python-dotenv
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Step 2: Get Your API Keys

### Claude API Key (for Research & Content)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Copy your key (starts with `sk-ant-...`)

**Pricing:**
- Sonnet 4.5: $3 per million input tokens, $15 per million output tokens
- Typical carburetor research: ~$0.20

### Gemini API Key (for Images)

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click **Get API Key** or **Create API Key**
4. Copy your key (starts with `AIza...`)

**Pricing:**
- Image generation: ~$0.10 per image
- Typical 20-slide deck: ~$2.00

---

## Step 3: Configure Environment

### Create .env File

```bash
# Copy the example file
cp .env.example .env
```

### Edit .env File

Open `.env` in a text editor and add your keys:

```bash
# Claude API - Research & Content Generation
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here

# Gemini API - Image Generation Only
GOOGLE_API_KEY=AIzaSy-your-actual-key-here

# Optional: Model selection
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

**IMPORTANT:**
- Never commit `.env` to git (it's in `.gitignore`)
- Keep your keys secure
- Regenerate keys if exposed

---

## Step 4: Test Your Setup

### Test Claude API

```bash
python -c "
from plugin.lib.claude_client import get_claude_client

client = get_claude_client()
print('✓ Claude API connected successfully!')

# Test generation
response = client.generate_text('Say hello!')
print(f'Response: {response}')
"
```

**Expected Output:**
```
✓ Claude API connected successfully!
Response: Hello! How can I help you today?
```

### Test Gemini API

```bash
python -c "
from lib.gemini_client import GeminiClient

client = GeminiClient()
print('✓ Gemini API connected successfully!')
print(f'Model: {client.model}')
"
```

**Expected Output:**
```
✓ Gemini API connected successfully!
Model: gemini-3-pro-image-preview
```

---

## Step 5: Run Full Integration Test

```bash
python test_carburetor_research.py
```

This will test:
1. Research Assistant (Claude)
2. Research Skill (Claude + Web Search)
3. Insight Extraction (Claude)
4. Outline Generation (Claude)

---

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

**Solution:**
1. Check `.env` file exists in project root
2. Check key is correctly named `ANTHROPIC_API_KEY`
3. Restart your terminal/Python session

### "Invalid API key"

**Solution:**
1. Verify key copied correctly (no extra spaces)
2. Check key is active in console.anthropic.com
3. Regenerate key if needed

### "Rate limit exceeded"

**Solution:**
1. Claude: Default limit is 50 requests/min
2. Gemini: Free tier has daily limits
3. Wait a few minutes or upgrade plan

### "Module 'anthropic' not found"

**Solution:**
```bash
pip install anthropic
```

---

## Usage Examples

### Research a Topic

```python
from plugin.lib.claude_client import get_claude_client

claude = get_claude_client()

# Generate search queries
queries = claude.generate_search_queries(
    topic="How carburetors work and Rochester 2GC rebuild",
    num_queries=5,
    depth="comprehensive"
)

print("Search queries:", queries)
```

### Extract Insights

```python
# After getting research sources...
insights = claude.extract_insights(
    sources=research_sources,
    focus_areas=["carburetor operation", "rebuild process"]
)

print(f"Found {len(insights['insights'])} insights")
```

### Generate Outline

```python
outline = claude.generate_outline(
    research_data=research_output,
    insights_data=insights_output,
    audience="technical DIY mechanics",
    duration_minutes=45
)

print(f"{outline['presentation_count']} presentations generated")
for pres in outline['presentations']:
    print(f"- {pres['title']}: {len(pres['slides'])} slides")
```

---

## Cost Management

### Track API Usage

**Claude Console:**
- https://console.anthropic.com/settings/usage

**Gemini AI Studio:**
- https://aistudio.google.com/app/prompts

### Set Spending Limits

**Claude:**
- Settings → Billing → Set monthly limit

**Gemini:**
- Free tier: 60 requests/minute
- Paid tier: Configure in Google Cloud Console

### Estimate Before Running

```python
# Estimate tokens for Claude
content_length = len(research_text)
estimated_tokens = content_length // 4  # Rough estimate
estimated_cost = (estimated_tokens / 1_000_000) * 3  # $3 per million

print(f"Estimated cost: ${estimated_cost:.4f}")
```

---

## Next Steps

1. ✅ APIs configured
2. ✅ Test successful
3. 🔄 Run carburetor research test
4. 📋 Integrate real web search (Google Custom Search)
5. 📋 Implement PRIORITY 3 (Content Drafting)

---

## Support

**Claude API:**
- Documentation: https://docs.anthropic.com/
- Status page: https://status.anthropic.com/
- Support: support@anthropic.com

**Gemini API:**
- Documentation: https://ai.google.dev/docs
- Community: https://developers.google.com/community
- Issue tracker: https://issuetracker.google.com/

**This Project:**
- GitHub issues: https://github.com/davistroy/slide-generator/issues
- Pull request: https://github.com/davistroy/slide-generator/pull/4
