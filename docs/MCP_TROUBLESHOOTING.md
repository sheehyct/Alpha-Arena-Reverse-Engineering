# MCP Server Troubleshooting Guide
## For DeepSeek Analysis Workspace

---

## 🚨 THE ISSUE

**You said**: "I don't have access to mcp__playwright__* or mcp__openmemory__* tools"

**Root Cause**: This is a **KNOWN BUG** in Claude Code where `.claude/mcp.json` files don't always load properly. Multiple GitHub issues document this problem:
- Issue #5037: MCP servers in .claude/.mcp.json not loading properly
- Issue #5353: MCP Configuration Not Loading Despite Installed Packages
- Issue #9913: MCP Server Not Loading from Project .mcp.json
- Issue #2156: Claude Code CLI Isn't Detecting Project Scoped MCP Server

---

## ✅ SOLUTION APPLIED

**What was done**: Moved MCP configuration from `.claude/mcp.json` to `.mcp.json` in the workspace root.

**Location**: `C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\.mcp.json`

**Content**:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    },
    "openmemory": {
      "command": "C:\\Program Files\\nodejs\\npm.cmd",
      "args": ["run", "mcp"],
      "cwd": "C:\\Dev\\openmemory\\backend",
      "env": {}
    }
  }
}
```

---

## 🔄 NEXT STEPS FOR YOU

### Step 1: Restart Claude Code

**IMPORTANT**: Claude Code only loads MCP configuration at startup. You MUST restart.

**If using CLI**:
1. Type `exit` or press Ctrl+D
2. Reopen with: `cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis" && claude`

**If using VS Code extension**:
1. Close VS Code completely
2. Reopen and navigate to this folder
3. Start Claude Code from the Command Palette

### Step 2: Verify MCP Servers Loaded

After restarting, check your available tools. You should now see:

**Playwright Tools**:
- `mcp__playwright__browser_navigate`
- `mcp__playwright__browser_click`
- `mcp__playwright__browser_snapshot`
- `mcp__playwright__browser_type`
- `mcp__playwright__browser_take_screenshot`
- Plus 10+ more browser automation tools

**OpenMemory Tools**:
- `mcp__openmemory__openmemory_store`
- `mcp__openmemory__openmemory_query`
- `mcp__openmemory__openmemory_list`
- `mcp__openmemory__openmemory_get`
- `mcp__openmemory__openmemory_reinforce`

### Step 3: Test MCP Connection

Try this simple test:

```bash
# Test Playwright
mcp__playwright__browser_navigate(url="https://nof1.ai")

# Test OpenMemory
mcp__openmemory__openmemory_query(query="nof1 scraper", k=3)
```

If you see results, MCP servers are working! 🎉

---

## 🔍 IF STILL NOT WORKING

### Troubleshooting Checklist

#### 1. Verify Prerequisites

**Node.js and npm**:
```bash
node --version  # Should show v18+ or v20+
npm --version   # Should show 9+ or 10+
```

**npx available**:
```bash
npx --version
```

**OpenMemory backend**:
```bash
cd "C:\Dev\openmemory\backend"
npm run mcp  # Should start without errors
```

#### 2. Check Configuration File

**Verify .mcp.json exists in root**:
```bash
cat .mcp.json
```

Should show the configuration above. If not, the file wasn't copied correctly.

#### 3. Try Manual MCP Server Test

**Test Playwright MCP**:
```bash
npx -y @playwright/mcp@latest
```

Should output: "Playwright MCP server started" or similar.

**Test OpenMemory MCP**:
```bash
cd "C:\Dev\openmemory\backend"
npm run mcp
```

Should start server without errors.

#### 4. Alternative: Global Configuration

If workspace configuration still fails, use global config:

**Location**: `C:\Users\sheeh\.claude\mcp.json` (or `~/.claude/mcp.json`)

Copy the same configuration there. This makes MCP servers available in ALL workspaces.

#### 5. Check Timeout Issues

If servers timeout, increase the limit:

```bash
export MCP_TIMEOUT=30000  # 30 seconds (default is 10s)
```

Add to your shell profile (`.bashrc`, `.zshrc`, or PowerShell profile).

---

## 📋 WHAT ARE MCP SERVERS?

**MCP = Model Context Protocol**

Think of MCP servers as **external applications that provide tools** to Claude Code:

- **Playwright MCP**: A separate Node.js process that controls a browser
- **OpenMemory MCP**: A separate Node.js process that manages semantic memory

**Key Point**: You don't "implement" or "install" them in Python. They're external processes that Claude Code connects to.

### How MCP Works

```
Claude Code (you)
    ↓
Connects to MCP servers via stdin/stdout
    ↓
MCP Server (Playwright or OpenMemory)
    ↓
Provides tools like browser_navigate, openmemory_store
    ↓
You call these tools in your responses
```

### What This Workspace Does

**Python Code** (`src/scraper.py`, etc.):
- Provides data structures (Pydantic models)
- Handles storage logic (JSON files)
- Prepares data for YOU to store via MCP tools
- Does NOT call MCP directly (you do that)

**Your Job** (Claude Code):
1. Use `mcp__playwright__*` tools to navigate and scrape nof1.ai
2. Use Python scraper to parse the data
3. Use `mcp__openmemory__*` tools to store results

---

## 🎯 QUICK REFERENCE

### Configuration Hierarchy

From highest to lowest priority:
1. Enterprise policies (system-wide, managed)
2. Command-line arguments
3. Local project settings (`.claude/settings.local.json`)
4. Shared project settings (`.claude/settings.json`)
5. **Root MCP config (`.mcp.json`)** ← You are here
6. User global settings (`~/.claude/settings.json`)

### Known Working Locations

✅ **Root directory**: `.mcp.json` (MOST RELIABLE)
✅ **Global config**: `~/.claude/mcp.json` or `~/.claude.json`
❌ **Subdirectory**: `.claude/mcp.json` (HAS BUGS, don't use)

### File Formats

**MCP servers**: `.mcp.json` or `.claude/mcp.json`
**Settings**: `.claude/settings.json` or `.claude/settings.local.json`
**Both can coexist**: MCP config is separate from general settings

---

## 📚 ADDITIONAL RESOURCES

### OpenMemory Stored Knowledge

Previous session stored comprehensive memories about this project in OpenMemory. Query with:

```
mcp__openmemory__openmemory_query(
    query="nof1 scraper MCP configuration troubleshooting",
    k=5
)
```

Topics covered:
- Complete project architecture
- Playwright vs Chrome extension comparison
- File inventory and code details
- Key decisions and insights
- User requirements

### GitHub Issues

If you encounter new issues:
- https://github.com/anthropics/claude-code/issues
- Search for "MCP" to find related problems
- File new issue if your problem is unique

### Official Docs

- MCP Configuration: https://docs.claude.com/en/docs/claude-code/mcp
- Settings: https://docs.claude.com/en/docs/claude-code/settings
- Troubleshooting: https://docs.claude.com/en/docs/claude-code/troubleshooting

---

## ✨ EXPECTED OUTCOME

After restarting Claude Code with `.mcp.json` in the root directory, you should:

1. See 20+ new tools starting with `mcp__playwright__*` and `mcp__openmemory__*`
2. Be able to navigate to nof1.ai using browser tools
3. Store and query data using OpenMemory tools
4. Work seamlessly with the Python scraper code

**If this works**: You're ready to start scraping! Follow the workflow in `QUICKSTART.md`.

**If this doesn't work**: Try the global config approach or file a GitHub issue with details.

---

**Last Updated**: 2025-10-29
**Session Context**: Continuation from vectorbt workspace session
**Issue Tracker**: GitHub anthropics/claude-code issues #5037, #5353, #9913
