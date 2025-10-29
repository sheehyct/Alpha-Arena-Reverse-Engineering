# Integration Layer - Complete Guide

## What Was Built

The integration layer that combines Chrome Extension + Playwright data is now complete:

### New Components

1. **`src/sqlite_reader.py`** - Reads Chrome extension SQLite database
2. **`src/merger.py`** - Merges and deduplicates data from both sources
3. **`src/openmemory_exporter.py`** - Prepares data for OpenMemory MCP
4. **`src/integration_cli.py`** - Command-line interface for all operations

---

## What Needs to Be Running

### REQUIRED Services (keep these running):

#### 1. Chrome Extension Collector - PRIMARY DATA SOURCE

**Terminal 1:**
```bash
cd GPT_Implementation_Proposal/collector
node server.js
```

**What it does:**
- Listens on `localhost:8787`
- Receives real-time WebSocket/SSE data from Chrome extension
- Stores to `nof1_data.db` SQLite database
- Deduplicates by content hash

**How to verify it's working:**
```bash
# Check if server is running
netstat -ano | findstr :8787   # Windows
lsof -i :8787                  # Mac/Linux

# Check database has data
ls -lh GPT_Implementation_Proposal/collector/nof1_data.db
```

**Expected output:** Database file should be growing as messages are captured

---

#### 2. Chrome Browser with Extension Installed

**What you need:**
- Chrome browser open
- Navigate to https://nof1.ai/
- Extension automatically intercepts messages

**How to verify it's working:**
1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for: `"nof1.ai message interceptor loaded"`
4. Watch for POST requests to `localhost:8787/ingest`

---

#### 3. OpenMemory Backend (for semantic search) - OPTIONAL BUT RECOMMENDED

**Terminal 2:**
```bash
cd C:\Dev\openmemory\backend
npm run mcp
```

**What it does:**
- Provides semantic memory storage
- Enables queries like "find risk management strategies"
- Required for: `mcp__openmemory__openmemory_store` and `mcp__openmemory__openmemory_query`

**How to verify it's working:**
- MCP server should show in Claude Code tools
- Try: `mcp__openmemory__openmemory_list` to test connection

---

## How to Use the Integration Layer

### Step 1: Check What Data You Have

```bash
uv run python -m src.integration_cli stats
```

**Output shows:**
- Total messages from Chrome extension
- Total messages from Playwright scraper
- Merged count (after deduplication)
- Messages by model (DeepSeek, QWEN, Claude, etc.)
- Priority models with P/L rankings

---

### Step 2: Export Merged Data to JSON

**All models:**
```bash
uv run python -m src.integration_cli export-json data/integrated/all_models.json
```

**DeepSeek only (highest P/L):**
```bash
uv run python -m src.integration_cli export-json data/integrated/deepseek_only.json --model "deepseek-v3.1"
```

**QWEN3 only (second highest P/L):**
```bash
uv run python -m src.integration_cli export-json data/integrated/qwen_only.json --model "qwen3-max"
```

---

### Step 3: Prepare Data for OpenMemory

**Preview what will be exported:**
```bash
uv run python -m src.integration_cli prepare-openmemory --limit 5
```

**Save samples for inspection:**
```bash
uv run python -m src.integration_cli prepare-openmemory --output data/integrated/openmemory_samples.json --limit 10
```

**Create batch file for ALL messages:**
```bash
uv run python -m src.integration_cli export-openmemory-batch data/integrated/openmemory_batch.json
```

---

### Step 4: Send to OpenMemory (Claude Code does this)

**Option A: Manual (one message at a time)**

After running `prepare-openmemory`, Claude Code can call:
```
mcp__openmemory__openmemory_store(
    content="[formatted reasoning text]",
    tags=["model_deepseek_v3.1", "date_2025_10_29", ...],
    metadata={"model_name": "deepseek-v3.1", ...}
)
```

**Option B: Batch Import (recommended for large datasets)**

1. Create batch file:
```bash
uv run python -m src.integration_cli export-openmemory-batch data/integrated/batch.json --model "deepseek-v3.1"
```

2. Ask Claude Code:
> "Read `data/integrated/batch.json` and send all messages to OpenMemory using `mcp__openmemory__openmemory_store`"

---

## Query and Analysis

### Query OpenMemory (Semantic Search)

Once data is in OpenMemory, you can query by meaning:

```
mcp__openmemory__openmemory_query(
    query="DeepSeek risk management strategies for volatile markets",
    k=10
)
```

```
mcp__openmemory__openmemory_query(
    query="entry signals for Bitcoin trades",
    k=15
)
```

```
mcp__openmemory__openmemory_query(
    query="stop loss placement strategies",
    k=20
)
```

### Query by Tags

```
mcp__openmemory__openmemory_query(
    query="model_deepseek_v3.1 high_confidence",
    k=10
)
```

---

## Data Flow Diagram

```
DATA CAPTURE (PRIMARY)
======================

nof1.ai --> WebSocket/SSE --> Chrome Extension --> POST
                |
         Node Collector (localhost:8787)
                |
  GPT_Implementation_Proposal/collector/nof1_data.db


DATA CAPTURE (SECONDARY)
=========================

Claude Code --> Playwright MCP --> nof1.ai
                |
    Python ChainExtractor parses YAML snapshots
                |
          data/raw/*.json


INTEGRATION LAYER
=================

src/sqlite_reader.py reads extension DB
src/merger.py combines both sources
                |
    Deduplication by content hash + timestamp
                |
src/openmemory_exporter.py formats for MCP
                |
     data/integrated/*.json (output)


SEMANTIC STORAGE (MCP)
======================

Claude Code calls mcp__openmemory__openmemory_store
                |
    OpenMemory MCP Backend (C:\Dev\openmemory\backend)
                |
      Semantic indexing + vector embeddings
                |
  Query with mcp__openmemory__openmemory_query
```

---

## Priority Models (by P/L Performance)

When analyzing data, focus on these models in order:

### [1] DeepSeek Chat V3.1 - PRIMARY FOCUS
- **P/L:** Highest (winning by largest margin)
- **Value:** Best trading strategies to learn from
- **Export:** `--model "deepseek-v3.1"`

### [2] QWEN3 MAX - SECONDARY FOCUS
- **P/L:** Second highest
- **Value:** Alternative successful strategies
- **Export:** `--model "qwen3-max"`

### [3] Claude Sonnet 4.5 - TERTIARY FOCUS
- **P/L:** Negative (worse than BTC buy-and-hold)
- **Value:** Learn what NOT to do
- **Export:** `--model "claude-sonnet-4.5"`

---

## Quick Test Workflow

### Test the complete integration:

```bash
# 1. Check stats
uv run python -m src.integration_cli stats

# 2. Export DeepSeek data (highest P/L)
uv run python -m src.integration_cli export-json test_deepseek.json --model "deepseek-v3.1"

# 3. Prepare 3 samples for OpenMemory
uv run python -m src.integration_cli prepare-openmemory --output test_samples.json --limit 3 --model "deepseek-v3.1"

# 4. Review the samples
cat test_samples.json

# 5. Ask Claude Code to send to OpenMemory
```

Then tell Claude Code:
> "Read `test_samples.json` and send the first sample to OpenMemory using `mcp__openmemory__openmemory_store`"

---

## Troubleshooting

### Extension not capturing data

**Check:**
1. Is `node server.js` running in collector directory?
2. Is Chrome open with extension installed?
3. Check Chrome DevTools console for errors
4. Verify database exists: `ls GPT_Implementation_Proposal/collector/nof1_data.db`

**Fix:**
```bash
cd GPT_Implementation_Proposal/collector
node server.js
# Leave running, open new terminal for other commands
```

---

### "Database not found" error

**Problem:** Extension database doesn't exist yet

**Fix:** Start the collector and let it capture some data first:
```bash
cd GPT_Implementation_Proposal/collector
node server.js
# Open nof1.ai in Chrome, wait 2-3 minutes
```

---

### OpenMemory MCP not available

**Problem:** OpenMemory backend not running

**Check:**
```bash
# Look for OpenMemory tools in Claude Code
mcp__openmemory__openmemory_list
```

**Fix:**
```bash
cd C:\Dev\openmemory\backend
npm run mcp
# Leave running in separate terminal
```

---

### No Playwright data found

**Problem:** Haven't run Playwright scraper yet

**This is OK!** The extension is the primary source. Playwright is only for:
- Historical backfill (messages before extension was installed)
- Validation (verify extension didn't miss anything)

**To add Playwright data:**
Ask Claude Code to scrape using the Playwright MCP tools.

---

## Summary Checklist

Before running integration commands, make sure:

- [ ] **Node collector running** (`node server.js` in Terminal 1)
- [ ] **Chrome open** with nof1.ai loaded and extension active
- [ ] **OpenMemory running** (`npm run mcp` in Terminal 2) - optional but recommended
- [ ] **UV installed** (not pip!) for Python commands

Once everything is running:

- [ ] Run `stats` to see what data you have
- [ ] Export to JSON for analysis
- [ ] Prepare and send to OpenMemory for semantic search
- [ ] Query OpenMemory to find trading patterns

---

## What You Can Do Now

1. **Real-time capture**: Extension captures every message as it appears on nof1.ai
2. **Historical analysis**: Merge with Playwright data for complete timeline
3. **Semantic search**: "Find DeepSeek's aggressive entry strategies"
4. **Pattern discovery**: Compare risk management across models
5. **Strategy extraction**: Learn from highest P/L model (DeepSeek)

---

**Last Updated:** 2025-10-29
**Status:** Integration Layer Complete
