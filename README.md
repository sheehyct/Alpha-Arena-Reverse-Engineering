# NOF1.AI Trading Model Analysis System

Automated capture and analysis of AI trading model decisions from nof1.ai, focusing on your highest-performing models: DeepSeek V3.1, QWEN3 MAX, and Claude Sonnet 4.5.

## System Overview

This system uses a Chrome extension to automatically capture trading decisions from nof1.ai every 60 seconds, storing them in a local SQLite database for analysis. Each captured message includes the full user prompt, chain of thought reasoning, and trading decisions.

## Quick Start

### 1. Start Data Collector
```powershell
cd collector
node server.js
```

### 2. Load Chrome Extension
1. Go to chrome://extensions/
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the extension/nof1-chat-export folder

### 3. Open nof1.ai
Visit https://nof1.ai/ and leave the tab open. Data captures automatically.

### 4. Verify Capture
```powershell
uv run python workflows/verify_extraction.py
```

## Complete Documentation

For detailed instructions, troubleshooting, and analysis workflows:

**See USER_MANUAL.md**

## Project Structure

```
collector/           Node.js data collector
extension/           Chrome extension for data capture
workflows/           Python scripts for analysis
src/                 Python modules
docs/                Technical documentation
archive/             Old/unused files
```

## Priority Models

1. **DeepSeek Chat V3.1** - Highest P/L (Primary focus)
2. **QWEN3 MAX** - Second highest P/L
3. **Claude Sonnet 4.5** - Negative P/L (learning what NOT to do)

## Key Features

- Automatic capture every 60 seconds
- Full message extraction (10,000-50,000 chars per message)
- Duplicate detection and prevention
- Real-time monitoring
- OpenMemory semantic search integration
- Pre-built analysis queries

## Requirements

- Windows 10/11
- Python 3.12+ (managed by uv)
- Node.js 18+
- Google Chrome
- Internet connection

## Support

See USER_MANUAL.md for:
- Step-by-step setup
- Troubleshooting guide
- Daily workflow
- Analysis tools
- File organization

## Data Captured Per Message

- User Prompt (8,000-10,000 chars): Market state, prices, indicators, positions
- Chain of Thought (1,000-5,000 chars): Model reasoning and analysis
- Trading Decisions (500-2,000 chars): Actions, confidence, stop loss, targets

## License

MIT License - Educational and research purposes only.

---

Last Updated: 2025-10-29
