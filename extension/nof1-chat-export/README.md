# NOF1 ModelChat Exporter (Chrome Extension)

What it does:
- Injects small hooks to capture WebSocket, SSE, and JSON fetch payloads
- Periodically exports visible ModelChat text as a fallback
- Sends everything to a local collector at `http://127.0.0.1:8787/ingest`
- Manual DOM snapshot with `Alt+E`

Install:
1. Go to `chrome://extensions`
2. Enable Developer Mode
3. Click "Load unpacked" and select this folder
4. Open https://nof1.ai and keep the collector running

Notes:
- This extension does not bypass authentication or access controls.
- It only captures what your browser receives or renders.
