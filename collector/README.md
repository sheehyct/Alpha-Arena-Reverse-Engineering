# NOF1 Collector (Node)

Purpose:
- Accepts events from the Chrome extension
- Validates payloads with JSON Schema (Ajv)
- Writes consolidated rows into `nof1_data.db` using the same schema your Python analyzer expects

Run:
```bash
cd collector
npm install
node server.js            # or: PORT=8787 DB_PATH=./nof1_data.db node server.js
curl http://127.0.0.1:8787/health
```

Flow:
Extension → POST /ingest → buffer → consolidate → insert into SQLite (model_chat)

Notes:
- Dedup uses a 16-char SHA256 hash of `raw_content`
- You can point DB_PATH to the same file your Python tools use


## Structured field extraction
- Parses JSON frames (WebSocket/SSE/fetch) for `action`, `confidence`, `positions`, `market_data`, and `reasoning`
- Fallback regex from visible DOM if JSON missing
- UPSERT on `message_hash` enriches rows over time
