# MCP Server Setup Guide

## Important: Workspace Context

The MCP servers are loaded **per workspace** in Claude Code. To use the scraper with its MCP configuration, you need to:

1. **Switch to the new workspace**
2. **Verify MCP servers load**
3. **Test the connection**

---

## Step 1: Open the New Workspace

### Option A: Via Claude Code Menu
1. Open Claude Code
2. Go to: `File → Open Folder`
3. Navigate to: `C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis`
4. Click "Select Folder"

### Option B: Via Command Line
```bash
code "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
```

---

## Step 2: Verify MCP Configuration

After opening the workspace, Claude Code should automatically load the MCP servers from `.claude/mcp.json`.

### Check MCP Status

In Claude Code, you should see:
- 🟢 Playwright MCP server active
- 🟢 OpenMemory MCP server active

If you see 🔴 (red) or ⚠️ (warning), proceed to troubleshooting below.

---

## Step 3: Test MCP Servers

### Test 1: List MCP Resources
In Claude Code chat:
```
List available MCP resources
```

Expected output:
- `openmemory-config` from openmemory server
- Playwright browser tools available

### Test 2: Navigate to a Page
```
Use Playwright to navigate to https://example.com
```

If successful, you'll see browser navigation happen.

### Test 3: Store in OpenMemory
```
Store a test message in OpenMemory with the tag "test"
```

If successful, you'll get a memory ID back.

---

## Troubleshooting

### Issue: Playwright MCP Not Loading

**Cause**: NPX or Playwright package not available

**Solution 1**: Install Playwright globally
```bash
npm install -g @playwright/mcp
```

**Solution 2**: Install browsers
```bash
npx playwright install chromium
```

**Solution 3**: Verify npx works
```bash
npx -y @playwright/mcp@latest --version
```

### Issue: OpenMemory MCP Not Loading

**Cause**: OpenMemory server not running

**Solution**: Start OpenMemory backend
```bash
cd C:\Dev\openmemory\backend
npm install  # First time only
npm run mcp
```

**Verify it's running**: You should see output like:
```
OpenMemory MCP server listening...
```

### Issue: MCP Config Not Found

**Cause**: Workspace not loaded correctly

**Solution**:
1. Close Claude Code completely
2. Reopen with: `File → Open Folder → DeepSeek Analysis`
3. Check that the sidebar shows the correct workspace name

### Issue: Wrong MCP Servers Loading

**Cause**: Multiple workspaces open or cached config

**Solution**:
1. Close all Claude Code windows
2. Clear cache (if needed): Delete `%APPDATA%\Code\User\globalStorage\`
3. Reopen only the DeepSeek Analysis workspace

---

## Alternative: Use Existing Workspace MCP

If you prefer to use the vectorbt workspace's MCP servers:

### Option 1: Copy MCP Config
```bash
# Copy the working MCP config from vectorbt workspace
cp "C:\Strat_Trading_Bot\vectorbt-workspace\.claude\mcp.json" "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\.claude\mcp.json"
```

### Option 2: Modify Config to Use Same Servers
The `.claude/mcp.json` already references the same OpenMemory backend:
- ✅ OpenMemory: `C:\Dev\openmemory\backend`
- ✅ Playwright: Standard npm package

So the configuration should work identically.

---

## Verification Checklist

Run through this checklist to confirm everything works:

- [ ] Workspace opened: `C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis`
- [ ] `.claude/mcp.json` file exists in workspace
- [ ] Claude Code shows MCP servers as active (green indicators)
- [ ] Can list MCP resources (openmemory-config appears)
- [ ] Can navigate with Playwright
- [ ] Can store in OpenMemory
- [ ] Example script runs: `uv run python example.py`

---

## Quick Test Script

Once workspace is open, tell Claude Code:

```
Run a quick test:
1. Navigate to nof1.ai using Playwright
2. Take a snapshot of the page
3. Store a test entry in OpenMemory
4. Show me the storage stats
```

If all four steps succeed, you're ready to scrape!

---

## Manual Server Start (If Needed)

If MCP servers won't auto-start, you can run them manually:

### Terminal 1: OpenMemory
```bash
cd C:\Dev\openmemory\backend
npm run mcp
# Leave this running
```

### Terminal 2: Playwright (Usually auto-starts)
Playwright MCP is typically started automatically by Claude Code via npx.

### Terminal 3: Your Work
```bash
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
# Now Claude Code can use both servers
```

---

## Expected MCP Server Output

### Playwright MCP
When working, you'll see in Claude Code logs:
```
[MCP] playwright: Connected
[MCP] playwright: Ready for browser automation
```

### OpenMemory MCP
When working, you'll see:
```
[MCP] openmemory: Connected
[MCP] openmemory: Database ready
```

---

## If All Else Fails: Standalone Mode

The scraper can still work without MCP in "offline mode":

1. **Local Storage Only**: Data still saves to JSON files
2. **Manual Browser**: Use the old scraper approach
3. **CLI Tools**: All CLI commands work independently

To use standalone:
```bash
# Everything still works locally
uv run python -m src.cli stats
uv run python -m src.cli search "momentum"

# Example script still works
uv run python example.py
```

The only features that require MCP:
- Automated browser navigation
- OpenMemory semantic search

Everything else works fine!

---

## Success Indicators

You'll know MCP is working when:

1. **Claude Code shows**: 🟢 Playwright, 🟢 OpenMemory in status bar
2. **You can say**: "Navigate to nof1.ai" and it works
3. **You can say**: "Query OpenMemory for..." and get results
4. **ListMcpResourcesTool** returns resources

---

## Next Steps After Setup

Once MCP is working:

1. **First scrape**: "Navigate to nof1.ai and scrape 5 messages"
2. **Verify storage**: Check `data/raw/` for JSON files
3. **Query data**: "Query OpenMemory for DeepSeek strategies"
4. **View stats**: `uv run python -m src.cli stats`

---

## Need Help?

If setup issues persist:

1. Check the vectorbt workspace MCP config for comparison
2. Verify both servers work there first
3. Copy working config to new workspace
4. Ask Claude Code to "debug MCP server connection"

The infrastructure exists and works in the vectorbt workspace, so it's just a matter of loading the right configuration in the new workspace!
