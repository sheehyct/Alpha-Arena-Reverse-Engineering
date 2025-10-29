# Debugging Chrome Extension - No Messages Being Captured

## Issue: Collector Running But No Messages Received

The Node.js collector is active, but the Chrome extension isn't sending data.

---

## Step-by-Step Debugging

### Step 1: Verify Extension is Installed

1. Open Chrome
2. Go to `chrome://extensions/`
3. Look for "nof1-chat-export" or similar
4. Verify:
   - [x] Extension is present
   - [x] "Enabled" toggle is ON
   - [x] No error messages shown

**If not installed:**
```bash
# Load unpacked extension
1. Go to chrome://extensions/
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select: GPT_Implementation_Proposal/extension/nof1-chat-export/
```

---

### Step 2: Check Extension Console for Errors

1. Go to `chrome://extensions/`
2. Find the extension
3. Click "service worker" (or "background page")
4. Check console for errors

**Common errors:**
- Network errors (can't reach localhost:8787)
- CORS errors
- Script injection failures

---

### Step 3: Check Page Console on nof1.ai

1. Open https://nof1.ai/ in Chrome
2. Press F12 to open DevTools
3. Go to Console tab
4. Look for messages from extension

**Should see:**
```
nof1.ai message interceptor loaded
[nof1-export] Detected message, sending to collector...
[nof1-export] Response: 200
```

**If you see:**
```
Failed to fetch
ERR_CONNECTION_REFUSED
```
- Collector not running or wrong port

---

### Step 4: Verify Collector is Listening

**Windows:**
```bash
netstat -ano | findstr :8787
```

**Should show:**
```
TCP    0.0.0.0:8787    0.0.0.0:0    LISTENING    [PID]
```

**If not showing:**
- Collector crashed
- Port blocked by firewall
- Wrong port configured

---

### Step 5: Check Extension Files

**Verify these files exist:**
```
GPT_Implementation_Proposal/extension/nof1-chat-export/
├── manifest.json
├── content.js
├── injected.js
├── service_worker.js
└── README.md
```

**Check manifest.json:**
```json
{
  "host_permissions": [
    "*://nof1.ai/*",
    "http://localhost:8787/*"
  ]
}
```

---

### Step 6: Manual Test - Send Test Request

Open new terminal:

```bash
# Test if collector is receiving requests
curl -X POST http://localhost:8787/ingest ^
  -H "Content-Type: application/json" ^
  -d "{\"test\": \"message\"}"
```

**Expected response:**
```
OK
```

**If this works:**
- Collector is fine
- Issue is with extension sending data

**If this fails:**
- Collector not running correctly

---

## Common Issues and Fixes

### Issue 1: Extension Not Injecting Scripts

**Symptom:** No console messages on nof1.ai page

**Fix:**
1. Reload extension at chrome://extensions/
2. Hard refresh nof1.ai (Ctrl+Shift+R)
3. Check DevTools console for injection

---

### Issue 2: CORS Blocking Requests

**Symptom:** "CORS policy" error in console

**Fix:**
The extension should bypass CORS, but if not:

1. Check manifest.json has correct host_permissions
2. Reload extension
3. Restart Chrome

---

### Issue 3: Wrong Collector URL

**Symptom:** Connection refused errors

**Fix:**
Check content.js or service_worker.js for collector URL:
```javascript
const COLLECTOR_URL = "http://localhost:8787/ingest";
```

Should match where collector is running.

---

### Issue 4: Messages Not Being Intercepted

**Symptom:** No errors, but no messages captured

**Possible causes:**
1. nof1.ai changed their WebSocket/SSE format
2. Extension selectors are outdated
3. Messages using different event names

**Fix:**
1. Open DevTools on nof1.ai
2. Go to Network tab
3. Look for WebSocket or EventSource connections
4. Check what data format is being used

---

## Quick Diagnostic Commands

**Check if collector is receiving ANY requests:**
```bash
# In collector terminal, should see:
POST /ingest
```

**If you see nothing:**
- Extension not sending
- Check extension console
- Check page console on nof1.ai

**If you see requests but database still empty:**
- Data validation failing
- Check collector logs for parse errors

---

## Extension Installation Checklist

- [ ] Extension loaded at chrome://extensions/
- [ ] Developer mode enabled
- [ ] Extension shows as "Enabled"
- [ ] No errors shown on extension page
- [ ] Chrome restarted after installation
- [ ] nof1.ai opened in new tab
- [ ] DevTools console shows extension loaded
- [ ] Collector running on port 8787
- [ ] Firewall not blocking localhost:8787

---

## Next Steps

### If Extension Console Shows Errors:

**Read the error message carefully:**
- Connection refused → Collector not running
- CORS error → Manifest permissions issue
- Script injection failed → Content script problem

### If No Errors But No Data:

**The extension might not be detecting messages:**
1. Check if nof1.ai structure changed
2. Update extension selectors
3. Check what events the page is using

### If Everything Looks Good But Still Not Working:

**Try this diagnostic:**

1. Open nof1.ai in Chrome
2. Open DevTools (F12)
3. Go to Console
4. Manually trigger data send:

```javascript
// Test sending data to collector
fetch('http://localhost:8787/ingest', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    test: 'manual',
    message: 'testing collector'
  })
}).then(r => r.text()).then(console.log).catch(console.error);
```

**If this works:**
- Collector is fine
- Extension needs debugging

**If this fails:**
- Check collector terminal for errors
- Verify port 8787 is open

---

## Get Detailed Logs

**Collector logs:**
Already shown in terminal where you ran `node server.js`

**Extension logs:**
1. chrome://extensions/
2. Click "service worker" (background script)
3. Console shows all extension activity

**Page logs:**
1. nof1.ai page
2. F12 → Console
3. Look for extension messages

---

## Contact Information

If you've checked everything and it's still not working, gather:

1. Screenshot of chrome://extensions/ showing extension
2. Console logs from extension (chrome://extensions/)
3. Console logs from nof1.ai page (F12)
4. Collector terminal output
5. Any error messages

This will help diagnose the specific issue.

---

**Last Updated:** 2025-10-29
