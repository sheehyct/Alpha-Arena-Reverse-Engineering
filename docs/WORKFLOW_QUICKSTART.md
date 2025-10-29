# Workflow QuickStart Guide

Simple guide to use the automated workflow scripts.

---

## Three Workflow Scripts

1. **start_capture.py** - Monitor data capture in real-time
2. **sync_to_openmemory.py** - Export data for OpenMemory
3. **analyze_strategies.py** - Interactive query builder

---

## Workflow 1: Start Capture Monitor

**Command:**
```bash
uv run python workflows/start_capture.py
```

**What it does:**
- Checks if Node.js collector is running
- Shows instructions if not running
- Monitors database in real-time
- Displays live statistics (updates every 5 seconds)
- Shows new messages as they arrive

**Keep this terminal open** - Monitors continuously until you press Ctrl+C.

**Output Example:**
```
Capture Status
--------------
Uptime:          00:15:23
Total Messages:  47 (+3 new)
Last Message:    2025-10-29T14:32:15
Messages/min:    3.06

By Model
--------
deepseek-v3.1       23  [1] Highest P/L
qwen3-max           15  [2] Second P/L
claude-sonnet-4.5    9  [3] Negative P/L
```

---

## Workflow 2: Sync to OpenMemory

**Export all models:**
```bash
uv run python workflows/sync_to_openmemory.py
```

**Export DeepSeek only (recommended):**
```bash
uv run python workflows/sync_to_openmemory.py --model "deepseek-v3.1"
```

**Export QWEN3:**
```bash
uv run python workflows/sync_to_openmemory.py --model "qwen3-max"
```

**Skip confirmation:**
```bash
uv run python workflows/sync_to_openmemory.py --model "deepseek-v3.1" --yes
```

**What it does:**
1. Checks prerequisites (database exists)
2. Merges Chrome Extension + Playwright data
3. Deduplicates messages
4. Shows data summary by model
5. Creates batch export file
6. Displays instructions for Claude Code

**Output:** Creates file in `data/openmemory_export/`

**Next step:** Tell Claude Code to import the batch file (see on-screen instructions)

---

## Workflow 3: Analyze Strategies

**Interactive mode:**
```bash
uv run python workflows/analyze_strategies.py
```

**List all available queries:**
```bash
uv run python workflows/analyze_strategies.py --list
```

**Run specific query:**
```bash
uv run python workflows/analyze_strategies.py --query 5
```

**What it does:**
- Shows 10 pre-defined query patterns
- Interactive menu system
- Generates MCP commands for Claude Code
- Custom query builder
- Model comparison tools

**Pre-defined Queries:**
1. Risk Management Strategies
2. Entry Signals - Trending Markets
3. Exit Strategies - Profit Taking
4. Stop Loss Placement
5. DeepSeek Winning Patterns (HIGH VALUE)
6. QWEN3 Strategies
7. Claude Negative Patterns (what NOT to do)
8. Bitcoin Strategies
9. Portfolio Diversification
10. Market Regime Adaptation

---

## Complete Example: Start to Finish

### Terminal Setup

**Terminal 1: Capture Monitor (Keep Open)**
```bash
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/start_capture.py
```

**Terminal 2: OpenMemory Backend (Keep Open)**
```bash
cd C:\Dev\openmemory\backend
npm run mcp
```

**Terminal 3: Operations (Run as needed)**
```bash
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
# Run sync and analyze commands here
```

---

### Step-by-Step Workflow

**Step 1: Start Monitoring**

In Terminal 1, start the capture monitor. If collector isn't running, follow on-screen instructions:
```bash
# Open new terminal for collector
cd GPT_Implementation_Proposal/collector
node server.js
```

Then open Chrome and navigate to https://nof1.ai/

---

**Step 2: Wait for Data**

Watch Terminal 1 as messages arrive. Wait until you have at least 20-30 messages (about 10-15 minutes).

---

**Step 3: Export to OpenMemory**

In Terminal 3:
```bash
uv run python workflows/sync_to_openmemory.py --model "deepseek-v3.1"
```

Note the batch filename in the output.

---

**Step 4: Import via Claude Code**

Tell Claude Code:
```
Read the file data/openmemory_export/openmemory_batch_deepseek-v3.1_TIMESTAMP.json
and import all messages to OpenMemory using mcp__openmemory__openmemory_store
for each item. Show progress.
```

---

**Step 5: Query and Analyze**

In Terminal 3:
```bash
uv run python workflows/analyze_strategies.py
```

Select option 5 (DeepSeek Winning Patterns), copy the MCP command, and tell Claude Code to execute it.

---

## Command Reference

### start_capture.py

**Basic:**
```bash
uv run python workflows/start_capture.py
```

**Stop:** Press Ctrl+C

No command-line options. Fully automated.

---

### sync_to_openmemory.py

**Options:**
- `--model MODEL` or `-m MODEL` - Export only specific model
- `--yes` or `-y` - Skip confirmation prompts

**Examples:**
```bash
# All models with confirmation
uv run python workflows/sync_to_openmemory.py

# DeepSeek only, auto-confirm
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y

# QWEN3 with confirmation
uv run python workflows/sync_to_openmemory.py --model "qwen3-max"
```

---

### analyze_strategies.py

**Options:**
- `--list` or `-l` - List all queries and exit
- `--query ID` or `-q ID` - Show specific query details

**Examples:**
```bash
# Interactive menu
uv run python workflows/analyze_strategies.py

# List all queries
uv run python workflows/analyze_strategies.py -l

# Show query #5 details
uv run python workflows/analyze_strategies.py -q 5
```

**Interactive Options:**
- `1-10` - Select pre-defined query
- `c` - Custom query builder
- `comp` - Compare models
- `help` - Show help
- `q` - Quit

---

## Professional Usage Patterns

### Pattern 1: Continuous Monitoring

**Setup (once per day):**
```bash
# Terminal 1
uv run python workflows/start_capture.py

# Terminal 2
cd C:\Dev\openmemory\backend && npm run mcp
```

Leave these running all day.

**Periodic sync (every 2-4 hours):**
```bash
# Terminal 3
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y
# Import via Claude Code
```

---

### Pattern 2: Batch Analysis

**Collect data all day, analyze at end:**

**Evening:**
```bash
# Export all captured data
uv run python workflows/sync_to_openmemory.py -y

# Import via Claude Code

# Run multiple analyses
uv run python workflows/analyze_strategies.py
# Select queries 1, 2, 3, 4, 5 in sequence
```

---

### Pattern 3: Model Comparison

**Export each model separately:**
```bash
uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y
uv run python workflows/sync_to_openmemory.py -m "qwen3-max" -y
uv run python workflows/sync_to_openmemory.py -m "claude-sonnet-4.5" -y
```

**Import all via Claude Code**

**Compare:**
```bash
uv run python workflows/analyze_strategies.py
# Select 'comp' for model comparison
```

---

## Architecture Benefits

### Separation of Concerns
- **Capture**: Real-time monitoring only
- **Sync**: Data preparation only
- **Analyze**: Query generation only

### Modularity
- Each script runs independently
- No tight coupling
- Easy to debug

### Composability
- Scripts can be chained
- Can run in sequence or parallel
- Flexible workflows

### Observability
- Clear progress indicators
- Real-time statistics
- Error messages with context

### Idempotency
- Safe to run multiple times
- Deduplication built-in
- No data loss on re-run

---

## Troubleshooting

### start_capture.py shows "Collector Not Running"

**Solution:** Start the Node.js collector:
```bash
cd GPT_Implementation_Proposal/collector
node server.js
```

---

### sync_to_openmemory.py shows "No messages available"

**Check:** Is data being captured?

**Solution:**
1. Verify capture monitor is running
2. Check Chrome is open to nof1.ai
3. Wait 5-10 minutes for messages to arrive

---

### analyze_strategies.py commands don't work

**Reason:** Commands must be executed by Claude Code, not your terminal.

**Solution:**
1. Copy the MCP command from analyzer
2. Tell Claude Code to execute it
3. Claude Code has MCP tools access

---

### Import to OpenMemory fails

**Check:**
1. Is OpenMemory backend running? (Terminal 2)
2. Did you specify the correct batch filename?
3. Does the file exist in data/openmemory_export/?

---

## What to Keep Running

### Always Running (while capturing):
- Terminal 1: `workflows/start_capture.py`
- Terminal 2: OpenMemory MCP backend
- Chrome browser with nof1.ai open

### Run Periodically:
- Terminal 3: `workflows/sync_to_openmemory.py`

### Run as Needed:
- Terminal 3: `workflows/analyze_strategies.py`

---

## File Locations

**Input:**
- `GPT_Implementation_Proposal/collector/nof1_data.db` - Extension database
- `data/raw/*.json` - Playwright scraped data

**Output:**
- `data/openmemory_export/*.json` - Batch files for import

**Scripts:**
- `workflows/start_capture.py` - Monitor
- `workflows/sync_to_openmemory.py` - Export
- `workflows/analyze_strategies.py` - Queries

---

## Quick Reference Card

```
START CAPTURE:     uv run python workflows/start_capture.py
EXPORT DATA:       uv run python workflows/sync_to_openmemory.py -m "deepseek-v3.1" -y
ANALYZE:           uv run python workflows/analyze_strategies.py

OPENMEMORY:        cd C:\Dev\openmemory\backend && npm run mcp
COLLECTOR:         cd GPT_Implementation_Proposal/collector && node server.js

PRIORITY MODEL:    deepseek-v3.1 (highest P/L)
```

---

**See Also:**
- INTEGRATION_GUIDE.md - Technical details
- IMPLEMENTATION_COMPLETE.md - What was built
- .session_startup_prompt.md - Architecture overview

**Last Updated:** 2025-10-29
