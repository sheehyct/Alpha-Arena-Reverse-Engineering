# Quick Start Reference

## Start System (2 steps)

### 1. Start Collector
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis\collector"
node server.js
```
Leave running.

### 2. Open nof1.ai
Visit https://nof1.ai/ in Chrome. Leave tab open.

Data captures automatically every 60 seconds.

---

## Verify Capture

### Check Latest Messages
```powershell
cd "C:\Users\sheeh\OneDrive\Desktop\DeepSeek Analysis"
uv run python workflows/verify_extraction.py
```

### Show Recent Message IDs
```powershell
uv run python workflows/show_recent_messages.py
```

### Count by Model
```powershell
uv run python -c "import sqlite3; conn = sqlite3.connect('collector/nof1_data.db'); cursor = conn.cursor(); cursor.execute('SELECT model_name, COUNT(*) as count FROM model_chat GROUP BY model_name ORDER BY count DESC'); rows = cursor.fetchall(); print('Models captured:'); [print(f'  {r[0]}: {r[1]} messages') for r in rows]"
```

---

## Analysis

### Sync to OpenMemory
```powershell
uv run python workflows/sync_to_openmemory.py
```

### Interactive Query Tool
```powershell
uv run python workflows/analyze_strategies.py
```

### Real-Time Monitor
```powershell
uv run python workflows/start_capture.py
```

---

## Troubleshooting

### Extension Not Capturing
1. chrome://extensions/ - Reload extension
2. Ctrl+Shift+R on nof1.ai tab
3. Wait 60 seconds

### Collector Not Running
```powershell
cd collector
node server.js
```

### Database Location
```
collector/nof1_data.db
```

---

## VS Code Quick Run

Right-click any .py file > "Run Python File in Terminal"

---

For complete documentation: **USER_MANUAL.md**
