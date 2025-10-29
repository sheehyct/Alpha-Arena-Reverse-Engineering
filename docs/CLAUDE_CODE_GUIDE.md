# Claude Code + MCP Scraping Guide

This guide shows how to use the new MCP-based scraper within Claude Code to extract chain of thought reasoning from nof1.ai.

## Why This Approach?

The new MCP-based implementation offers several advantages over the standalone scraper:

1. **Leverages Existing Infrastructure**: Uses the Playwright and OpenMemory MCP servers already configured in your workspace
2. **Semantic Storage**: Stores data in OpenMemory for intelligent querying
3. **Interactive Assistance**: Claude Code can help navigate, extract, and analyze data in real-time
4. **Better Error Handling**: Claude Code can adapt to page structure changes dynamically

## Setup

1. **Ensure MCP Servers are Running**:
   - Playwright MCP: `npx -y @playwright/mcp@latest`
   - OpenMemory MCP: Check that `C:\Dev\openmemory\backend` is running

2. **Install Dependencies**:
   ```bash
   cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
   uv sync
   ```

3. **Initialize Data Directories**:
   ```bash
   uv run python -m src.cli init
   ```

## Usage in Claude Code

### Step 1: View the Navigation Guide

Ask Claude Code to show you the scraping plan:

```
Show me the scraping guide for nof1.ai
```

Claude Code will execute:
```python
from src.scraper import Nof1Scraper
from pathlib import Path

scraper = Nof1Scraper(
    data_dir=Path("./data"),
    max_messages=20
)
scraper.print_navigation_guide()
```

### Step 2: Start Scraping

Tell Claude Code to start scraping:

```
Scrape the latest 10 messages from nof1.ai and store them in OpenMemory
```

Claude Code will:
1. Navigate to https://nof1.ai/
2. Click the MODELCHAT button
3. Get a snapshot of the page
4. Identify message elements
5. Expand each message
6. Extract chain of thought data
7. Store in local JSON and OpenMemory

### Step 3: Filter by Model (Optional)

To scrape a specific model:

```
Scrape only Claude Sonnet 4.5 messages from nof1.ai
```

### Step 4: Query the Data

After scraping, you can query OpenMemory:

```
Query OpenMemory for DeepSeek's risk management strategies
```

Claude Code will use:
```python
mcp__openmemory__openmemory_query(
    query="risk management strategy",
    sector="episodic",
    k=10
)
```

## Example Complete Session

Here's a full example of using Claude Code to scrape and analyze:

````
Human: I want to scrape chain of thought reasoning from nof1.ai and analyze DeepSeek's strategies