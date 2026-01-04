# Scripts Directory

This directory contains utility scripts organized by purpose and maintenance status.

## Directory Structure

```
scripts/
├── primary/               # Main scripts - actively maintained
│   ├── generate_prompts.py    # Generate AI image prompts (all resolutions)
│   └── generate_images.py     # Generate images from prompts (all resolutions)
└── generate_images_for_slides.py  # Standalone batch generator

```

**Archived (in `../archive/legacy-scripts/`):**
- `utilities/` - Duplicate helper scripts (archived in cleanup)
- `legacy/` - Older scripts superseded by primary scripts (archived in cleanup)

## Primary Scripts (Recommended)

These are the main scripts you should use for most tasks. They're actively maintained and have the latest features.

### generate_prompts.py
**Purpose:** Generate AI image prompts from presentation markdown

**Features:**
- Supports all resolutions (small/medium/high)
- Config-driven templates (`prompt_config.md`)
- Uses official parser (consistent with presentation generator)
- Comprehensive error handling and validation

**Usage:**
```bash
# Generate small resolution prompts (no embedded titles)
python scripts/primary/generate_prompts.py --resolution small

# Generate high resolution prompts (with titles)
python scripts/primary/generate_prompts.py --resolution high --output ./prompts/high

# Custom config and style
python scripts/primary/generate_prompts.py \
  --config my_config.md \
  --style templates/my_style.json \
  --resolution medium
```

**Command-line options:**
- `--resolution, -r`: Resolution (small/medium/high) - default: small
- `--presentation, -p`: Path to presentation markdown file
- `--style, -s`: Path to style JSON file
- `--config, -c`: Path to prompt_config.md
- `--output, -o`: Output directory for prompt files

### generate_images.py
**Purpose:** Generate actual images from prompts using Gemini API

**Features:**
- Supports all resolutions (small/medium/high)
- Automatic retry with exponential backoff
- Progress tracking and error recovery
- Config-driven API parameters

**Usage:**
```bash
# Generate small resolution images
python scripts/primary/generate_images.py --resolution small

# Generate high resolution 4K images
python scripts/primary/generate_images.py --resolution high

# Custom paths
python scripts/primary/generate_images.py \
  --resolution medium \
  --input ./prompts/medium \
  --output ./images/medium \
  --style templates/cfa_style.json
```

**Command-line options:**
- `--resolution, -r`: Resolution (small/medium/high) - default: small
- `--input, -i`: Input directory with prompt files
- `--output, -o`: Output directory for images
- `--style, -s`: Path to style JSON file
- `--config, -c`: Path to prompt_config.md

## Standalone Script

### generate_images_for_slides.py
Standalone batch generator that can process multiple slides at once with custom settings. Located in `scripts/` root directory.

**Usage:**
```bash
python scripts/generate_images_for_slides.py \
  --style templates/cfa_style.json \
  --slides presentation.md \
  --output ./images \
  --notext
```

## Archived Scripts

**Utilities and legacy scripts** have been archived to `../archive/legacy-scripts/` during project cleanup (v1.2.1). They included duplicate functionality now available in primary scripts. If you need them, they can be found in the archive directory.

## Complete Workflow Example

Here's how to use the primary scripts to generate a complete presentation:

```bash
# Step 1: Generate prompts for high resolution
python scripts/primary/generate_prompts.py \
  --resolution high \
  --presentation templates/example-presentation.md \
  --style templates/cfa_style.json \
  --output ./high-res/prompts

# Step 2: Generate images from those prompts
python scripts/primary/generate_images.py \
  --resolution high \
  --input ./high-res/prompts \
  --output ./high-res/images \
  --style templates/cfa_style.json

# Step 3: Generate the PowerPoint presentation
python presentation-skill/generate_presentation.py \
  templates/example-presentation.md \
  --template cfa \
  --output my-presentation.pptx

```

## Environment Setup

All scripts require proper environment setup:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your-key-here

# 3. Verify setup
python scripts/primary/generate_prompts.py --help
```

## Troubleshooting

### Script not found
If you get "file not found" errors, make sure you're running from the project root:
```bash
cd /path/to/slide-generator
python scripts/primary/generate_prompts.py ...
```

### ImportError for lib modules
Scripts add `lib/` to the Python path automatically. If you still get import errors:
```bash
# Set PYTHONPATH manually
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python scripts/primary/generate_prompts.py ...
```

### API key not found
Make sure your `.env` file exists and contains your API key:
```bash
# Check .env file exists
ls -la .env

# Verify content (without exposing key)
grep GOOGLE_API_KEY .env
```

## For Junior Developers

### What's the difference between primary, utilities, and legacy?

- **Primary scripts**: These are the "main" tools everyone should use. They're like the main entrance to a building - well-maintained, clearly marked, and designed for everyday use.

- **Utilities**: Helper scripts for specific tasks. Like side doors to a building - useful for specific purposes but not the main way in.

- **Legacy scripts**: Old versions kept for compatibility. Like keeping an old key that still works but you have a better one now.

### Which script should I use?

For most tasks, use the **primary scripts**:
- Need prompts? → `scripts/primary/generate_prompts.py`
- Need images? → `scripts/primary/generate_images.py`
- Need full presentation? → `presentation-skill/generate_presentation.py`

### Why reorganize scripts into directories?

1. **Organization**: Makes it easy to find the right script
2. **Clarity**: Shows which scripts are current vs. old
3. **Maintenance**: Developers know which scripts to update
4. **Learning**: New users can focus on primary scripts

---

**Last Updated:** January 3, 2026
**Reorganized in:** v1.2.1 Cleanup Release
