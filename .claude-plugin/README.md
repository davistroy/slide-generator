# Slide Generator Plugin

## Quick Install

```
/plugin marketplace add davistroy/slide-generator
```

## Setup

1. Set environment variables:
   ```bash
   export ANTHROPIC_API_KEY=your-key
   export GOOGLE_API_KEY=your-key
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Generate a complete presentation:

```bash
python -m plugin.cli full-workflow "Your Topic" --template stratfield
```

Or run individual steps:

```bash
python -m plugin.cli research "Topic" --output research.json
python -m plugin.cli outline research.json --output outline.md
python -m plugin.cli draft-content outline.md --output content.md
python -m plugin.cli build-presentation content.md --template cfa
```

## Commands

| Command             | Description                   |
|---------------------|-------------------------------|
| `full-workflow`     | Complete 11-step generation   |
| `research`          | Autonomous topic research     |
| `outline`           | Generate presentation outline |
| `draft-content`     | Draft slide content           |
| `optimize-content`  | Quality optimization          |
| `generate-images`   | AI image generation           |
| `build-presentation`| Build PowerPoint file         |
| `health-check`      | Validate configuration        |

## Documentation

- [Full README](../README.md)
- [API Setup Guide](../SETUP_APIS.md)
- [Architecture](../API_ARCHITECTURE.md)
