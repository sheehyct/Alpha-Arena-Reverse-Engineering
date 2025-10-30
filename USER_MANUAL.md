# NOF1.AI Trading Model Analysis - User Manual

## Overview

This system automatically captures trading model decisions from nof1.ai and stores them for analysis. It tracks your priority models: DeepSeek V3.1 (highest P/L), QWEN3 MAX (second highest), and Claude Sonnet 4.5.

## Quick Start Guide

### Step 1: Start the Data Collector

The collector receives data from the Chrome extension and saves it to a SQLite database.

**Option A: Using PowerShell**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector"
node server.js
```

**Option B: Using VS Code**
1. Open `collector/server.js` in VS Code
2. Right-click in the file
3. Select "Run JavaScript File in Terminal"

**What you should see:**
```
NOF1 collector listening on http://127.0.0.1:8787  DB=nof1_data.db
```

**Leave this terminal running.**

---

### Step 2: Install Chrome Extension (One-Time Setup)

1. Open Chrome browser
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Navigate to: `C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\extension\nof1-chat-export`
6. Click "Select Folder"

**Verify:** Extension shows as "Enabled" with green toggle

---

### Step 3: Open nof1.ai

1. Go to https://nof1.ai/ in Chrome
2. Leave the tab open (models run automatically)
3. Extension polls for new data every 60 seconds

**Data is captured automatically - no interaction needed.**

---

## Verifying Data Capture

### Check Captured Messages

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/verify_extraction.py
```

**VS Code:**
1. Open `workflows/verify_extraction.py`
2. Right-click > "Run Python File in Terminal"

**What you should see:**
- Latest 3 messages displayed
- Model names: deepseek-chat-v3.1, qwen3-max, claude-sonnet-4-5
- USER_PROMPT: YES
- CHAIN_OF_THOUGHT: YES
- TRADING_DECISIONS: YES
- Extracted reasoning: 10,000-50,000 characters

---

### Check Model Counts

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python -c "import sqlite3; conn = sqlite3.connect('collector/nof1_data.db'); cursor = conn.cursor(); cursor.execute('SELECT model_name, COUNT(*) as count FROM model_chat GROUP BY model_name ORDER BY count DESC'); rows = cursor.fetchall(); print('Models captured:'); [print(f'  {r[0]}: {r[1]} messages') for r in rows]"
```

**What you should see:**
```
Models captured:
  qwen3-max: 24 messages
  claude-sonnet-4-5: 19 messages
  deepseek-chat-v3.1: 15 messages
  gemini-2.5-pro: 19 messages
  gpt-5: 17 messages
  grok-4: 17 messages
```

---

## Analysis Workflows

### 1. Quick Statistics and Search

Fast command-line tool for basic statistics and keyword searches.

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"

# Show statistics
uv run python workflows/quick_analysis.py

# Search for keyword
uv run python workflows/quick_analysis.py --search "MACD" --limit 10
uv run python workflows/quick_analysis.py --search "risk management" --limit 5
```

**VS Code:**
1. Open `workflows/quick_analysis.py`
2. Right-click > "Run Python File in Terminal"

**What you should see:**
```
=== Quick Statistics ===

Total messages: 142

By model:
  qwen3-max: 31
  gemini-2.5-pro: 24
  claude-sonnet-4-5: 23
  deepseek-chat-v3.1: 19
```

---

### 2. Interactive Local Data Analysis

Comprehensive interactive tool for analyzing captured trading data from SQLite.

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/analyze_local_data.py
```

**VS Code:**
1. Open `workflows/analyze_local_data.py`
2. Right-click > "Run Python File in Terminal"

**Available Options:**
1. Search for keyword in reasoning
2. Show trading decision statistics
3. Analyze keyword frequency
4. Compare models by keywords
5. Export model reasoning to file
6. Show overview by model

**What it does:**
- Search chain of thought reasoning for patterns
- Compare how different models approach trading
- Export specific model data for deep analysis
- Analyze keyword frequency across all models
- Filter by specific models

---

### 3. Local Strategy Analysis (Pre-Built Queries)

Interactive tool with 10 pre-built trading strategy queries for fast pattern discovery.

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/analyze_strategies_local.py

# List all queries
uv run python workflows/analyze_strategies_local.py --list

# Run specific query
uv run python workflows/analyze_strategies_local.py --query 5

# View full message
uv run python workflows/analyze_strategies_local.py --view 2128
```

**VS Code:**
1. Open `workflows/analyze_strategies_local.py`
2. Right-click > "Run Python File in Terminal"

**Pre-Built Queries:**
1. Risk Management Strategies
2. Entry Signals - Trending Markets
3. Exit Strategies - Profit Taking
4. Stop Loss Placement
5. DeepSeek Winning Patterns (Priority Model #1)
6. QWEN3 Strategies (Priority Model #2)
7. Claude Analysis Patterns (Priority Model #3)
8. Technical Indicators (MACD, RSI, MA)
9. Market Conditions (Volatility, Trending)
10. All Priority Models Comparison

**What it does:**
- Pre-configured keyword lists for common patterns
- Model-specific queries for priority models
- Interactive menu with query descriptions
- View full message reasoning directly from results
- Custom query builder for ad-hoc searches

**Recommended Workflow:**
1. Run query #5 (DeepSeek Winning Patterns)
2. Note interesting message IDs from results
3. Use `--view <ID>` to read full reasoning
4. Extract patterns and compare with query #6 (QWEN3)

---

### 4. Sync to OpenMemory (Optional - Advanced)

For semantic search capabilities, you can optionally sync data to OpenMemory.

**Note:** Local analysis is faster and works directly with your database.
Only use OpenMemory if you need semantic similarity search.

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/start_capture.py
```

**VS Code:**
1. Open `workflows/start_capture.py`
2. Right-click > "Run Python File in Terminal"

**What you should see:**
- Total messages captured
- Messages per model
- Latest capture timestamp
- Updates every 5 seconds

**Press Ctrl+C to stop monitoring.**

---

## Troubleshooting

### Collector Not Receiving Data

1. **Check collector is running:**
   - Look for "NOF1 collector listening on http://127.0.0.1:8787"
   - If not running, start it (Step 1)

2. **Check extension is loaded:**
   - Go to `chrome://extensions/`
   - Verify "nof1-chat-export" shows as Enabled
   - If not, reload the extension (click reload icon)

3. **Hard refresh nof1.ai:**
   - Press `Ctrl+Shift+R` on nof1.ai tab
   - Wait 60 seconds for next poll cycle

4. **Check for errors:**
   - Press F12 on nof1.ai tab
   - Go to Console tab
   - Look for red errors mentioning "NOF1" or "export"

---

### No Data in Database

1. **Verify collector shows activity:**
   ```
   [DEBUG] Processing 100 conversations from API
   [DEBUG] Saved conversation: deepseek-chat-v3.1 (...)
   ```

2. **If no activity after 60 seconds:**
   - Reload extension at `chrome://extensions/`
   - Hard refresh nof1.ai tab (`Ctrl+Shift+R`)

3. **Check database exists:**
   ```powershell
   ls "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector\nof1_data.db"
   ```

---

### Extension Crashes/Errors

1. **Reload the extension:**
   - Go to `chrome://extensions/`
   - Find "nof1-chat-export"
   - Click reload icon (circular arrow)

2. **Clear cached data:**
   - Close all nof1.ai tabs
   - Reload extension
   - Open fresh nof1.ai tab

3. **Check Chrome DevTools:**
   - Right-click extension icon
   - Select "Inspect popup" or "Inspect background page"
   - Check Console for errors

---

## File Organization

```
DeepSeek Analysis/
├── collector/              Chrome extension data collector (Node.js)
│   ├── server.js          Main collector server
│   ├── schema.json        Data validation schema
│   └── nof1_data.db       SQLite database (captured data)
│
├── extension/             Chrome extension files
│   └── nof1-chat-export/
│       ├── manifest.json  Extension configuration
│       ├── content.js     Page content script
│       ├── injected.js    API hooks and polling
│       └── service_worker.js  Background message handler
│
├── workflows/             Analysis and workflow scripts
│   ├── verify_extraction.py     Check captured data quality
│   ├── sync_to_openmemory.py    Export to OpenMemory
│   ├── analyze_strategies.py   Interactive query tool
│   └── start_capture.py         Real-time monitoring
│
├── src/                   Python modules
│   ├── sqlite_reader.py   Database reading and parsing
│   ├── merger.py          Data merging and deduplication
│   ├── openmemory_exporter.py  OpenMemory export formatting
│   └── integration_cli.py CLI interface for data operations
│
├── docs/                  Technical documentation
├── archive/               Old/unused scripts
├── data/                  Export files and batch data
├── tests/                 Test scripts
│
├── USER_MANUAL.md         This file
├── README.md              Project overview
├── QUICKSTART.md          Quick reference guide
└── pyproject.toml         Python dependencies
```

---

## Daily Workflow

### Morning Setup (5 minutes)

1. **Start collector:**
   ```powershell
   cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector"
   node server.js
   ```

2. **Open nof1.ai in Chrome**
   - Leave tab open all day
   - Data captures automatically every 60 seconds

3. **Verify capture after 2 minutes:**
   ```powershell
   cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
   uv run python workflows/verify_extraction.py
   ```

---

### End of Day Analysis (10 minutes)

1. **Check total messages captured:**
   ```powershell
   uv run python -c "import sqlite3; conn = sqlite3.connect('collector/nof1_data.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM model_chat'); print(f'Total messages: {cursor.fetchone()[0]}')"
   ```

2. **Sync to OpenMemory for analysis:**
   ```powershell
   uv run python workflows/sync_to_openmemory.py
   ```

3. **Analyze patterns:**
   ```powershell
   uv run python workflows/analyze_strategies.py
   ```
   - Select query #4 (DeepSeek Winning Patterns)
   - Select query #5 (QWEN Strategy Analysis)
   - Select query #6 (Claude Decision Analysis)

4. **Compare priority models:**
   - Select query #2 (Model Comparison)
   - Focus on DeepSeek vs QWEN vs Claude

---

## Priority Models

### 1. DeepSeek Chat V3.1
- **Status:** PRIMARY MODEL
- **P/L:** Highest profitability
- **Analysis Focus:** Winning patterns, entry timing, confidence thresholds
- **Database ID:** `deepseek-chat-v3.1`

### 2. QWEN3 MAX
- **Status:** SECONDARY MODEL
- **P/L:** Second highest profitability
- **Analysis Focus:** Strategy differences from DeepSeek, unique patterns
- **Database ID:** `qwen3-max`

### 3. Claude Sonnet 4.5
- **Status:** LEARNING MODEL
- **P/L:** Negative (learning what NOT to do)
- **Analysis Focus:** Failed trade analysis, risk management mistakes
- **Database ID:** `claude-sonnet-4-5`

---

## Data Structure

Each captured message contains:

### User Prompt (8,000-10,000 chars)
- Current market state (BTC, ETH, SOL, etc.)
- Price data (OHLC)
- Technical indicators (MACD, RSI, EMA)
- Open positions
- Account balance
- Historical performance

### Chain of Thought (1,000-5,000 chars)
- Model's reasoning process
- Market analysis
- Risk assessment
- Strategy justification

### Trading Decisions (500-2,000 chars)
- Recommended actions (buy/sell/hold)
- Position sizes
- Confidence scores (0-1)
- Stop loss levels
- Take profit targets
- Risk amount (USD)

---

## Support

For issues or questions:

1. Check Troubleshooting section above
2. Review collector terminal output for errors
3. Check Chrome DevTools Console (F12)
4. Verify extension is enabled at `chrome://extensions/`

---

## System Requirements

- Windows 10/11
- Python 3.12+ (managed by uv)
- Node.js 18+ (for collector)
- Google Chrome browser
- Internet connection to nof1.ai

---

## Backup and Maintenance

### Backup Database

```powershell
cp "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector\nof1_data.db" "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\data\backups\nof1_data_$(Get-Date -Format 'yyyyMMdd').db"
```

### Clear Old Data (if needed)

```powershell
rm "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector\nof1_data.db"
```

Note: Collector will create a fresh database on next startup.

---

## Export Individual Messages

### Show Recent Message IDs

**PowerShell:**
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/show_recent_messages.py
```

**VS Code:**
1. Open `workflows/show_recent_messages.py`
2. Right-click > "Run Python File in Terminal"

**What you should see:**
```
Latest 10 Messages:
----------------------------------------------------------------------
  ID 522: deepseek-chat-v3.1 (2025-10-29T14:32:15.123Z)
  ID 521: qwen3-max (2025-10-29T14:31:45.789Z)
  ID 520: claude-sonnet-4-5 (2025-10-29T14:31:20.456Z)
  ...
----------------------------------------------------------------------
```

**Show more messages:**
```powershell
uv run python workflows/show_recent_messages.py --limit 20
```

### Export Message Content

**PowerShell:**
```powershell
# Export specific message ID
uv run python archive/export_message.py 522
```

**What it does:**
- Creates `extracted_message_<id>.txt` with full extracted content
- Includes USER_PROMPT, CHAIN_OF_THOUGHT, TRADING_DECISIONS sections
---

Last Updated: 2025-10-29
Version: 1.0
