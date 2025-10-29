import express from "express";
import morgan from "morgan";
import Database from "better-sqlite3";
import Ajv from "ajv";
import fs from "fs";
import crypto from "crypto";

const PORT = process.env.PORT || 8787;
const DB_PATH = process.env.DB_PATH || "nof1_data.db";

// JSON schema
const schema = JSON.parse(fs.readFileSync(new URL("./schema.json", import.meta.url)));
const ajv = new Ajv({ allErrors: true, strict: false });
const validate = ajv.compile(schema);

// Open DB
const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");

db.exec(`
CREATE TABLE IF NOT EXISTS model_chat (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model_name TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  message_hash TEXT UNIQUE NOT NULL,
  reasoning TEXT,
  action TEXT,
  confidence REAL,
  positions TEXT,
  market_data TEXT,
  raw_content TEXT,
  scraped_at TEXT NOT NULL,
  UNIQUE(model_name, message_hash)
);
CREATE TABLE IF NOT EXISTS scraper_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_timestamp TEXT NOT NULL,
  models_checked INTEGER,
  new_messages INTEGER,
  errors TEXT
);
CREATE INDEX IF NOT EXISTS idx_model_time ON model_chat(model_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_hash ON model_chat(message_hash);
`);

// Helpers
function sha16(s) {
  return crypto.createHash("sha256").update(s).digest("hex").slice(0,16);
}

function safeJsonParse(s) {
  try { return JSON.parse(s); } catch { return null; }
}

function parseNdjsonOrSse(chunk) {
  // Accept raw JSON, NDJSON, or SSE lines like "data: {...}"
  const out = [];
  const lines = String(chunk).split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  for (let line of lines) {
    if (line.startsWith("data:")) line = line.slice(5).trim();
    if (!line) continue;
    const obj = safeJsonParse(line);
    if (obj) out.push(obj);
  }
  // If nothing parsed and the whole chunk is JSON
  if (out.length === 0) {
    const obj = safeJsonParse(chunk);
    if (obj) out.push(obj);
  }
  return out;
}

function pick(obj, keys) {
  const out = {};
  for (const k of keys) if (obj && Object.prototype.hasOwnProperty.call(obj, k)) out[k] = obj[k];
  return out;
}

function toPositionsStruct(val) {
  // Normalize a variety of possible shapes into [{symbol, side, size, leverage, entry, stop, takeProfit}]
  const arr = [];
  const add = (p) => {
    if (!p) return;
    const sym = p.symbol || p.ticker || p.asset || p.coin;
    const side = (p.side || p.position || p.direction || "").toString().toUpperCase();
    const size = p.size ?? p.qty ?? p.quantity ?? null;
    const lev  = p.leverage ?? p.lev ?? null;
    const entry = p.entry ?? p.avgEntry ?? null;
    const stop  = p.stop ?? p.stopLoss ?? p.sl ?? null;
    const tp    = p.takeProfit ?? p.tp ?? null;
    arr.push({ symbol: sym || null, side: side || null, size, leverage: lev, entry, stop, takeProfit: tp });
  };
  if (Array.isArray(val)) val.forEach(add);
  else if (val && typeof val === "object") add(val);
  return arr;
}

function extractFromJsonObjects(jsonObjects) {
  const acc = {
    model_name: null,
    action: null,
    confidence: null,
    positions: [],
    market_data: {},
    reasoning_blocks: []
  };

  const lower = (s) => String(s || "").toLowerCase();

  for (const obj of jsonObjects) {
    // Common wrappers
    const data = obj.data || obj.payload || obj.message || obj;
    const meta = obj.meta || obj.context || {};

    // NOF1.AI SPECIFIC: Check for conversations array
    if (data.conversations && Array.isArray(data.conversations)) {
      for (const conv of data.conversations) {
        // Extract model name from conversation ID (e.g., "gemini-2.5-pro_1761770397")
        if (conv.id && !acc.model_name) {
          const idMatch = conv.id.match(/^([a-z0-9\-\.]+?)_\d+/i);
          if (idMatch) acc.model_name = lower(idMatch[1]).replace(/\s+/g,"-");
        }

        // Extract user_prompt, cot_trace (chain of thought), llm_response (trading decisions)
        if (typeof conv.user_prompt === "string" && conv.user_prompt.length > 20) {
          acc.reasoning_blocks.push("USER_PROMPT:\n" + conv.user_prompt);
        }

        // Chain of thought - check both cot_trace and cot_trace_summary
        if (typeof conv.cot_trace === "string" && conv.cot_trace.length > 20) {
          acc.reasoning_blocks.push("CHAIN_OF_THOUGHT:\n" + conv.cot_trace);
        } else if (typeof conv.cot_trace_summary === "string" && conv.cot_trace_summary.length > 20) {
          acc.reasoning_blocks.push("CHAIN_OF_THOUGHT:\n" + conv.cot_trace_summary);
        }

        // Trading decisions from llm_response
        if (conv.llm_response) {
          if (typeof conv.llm_response === "string" && conv.llm_response.length > 20) {
            acc.reasoning_blocks.push("TRADING_DECISIONS:\n" + conv.llm_response);
          } else if (typeof conv.llm_response === "object") {
            acc.reasoning_blocks.push("TRADING_DECISIONS:\n" + JSON.stringify(conv.llm_response, null, 2));
          }
        }
      }
    }

    // Model name (fallback to generic)
    const modelCand = data.model || data.modelName || meta.model || obj.model || obj.modelName;
    if (modelCand && !acc.model_name) acc.model_name = lower(modelCand).replace(/\s+/g,"-");

    // Reasoning text (generic fallback)
    const rKeys = ["reasoning", "rationale", "trace", "thoughts", "analysis", "explanation", "reasoningTrace"];
    for (const k of rKeys) {
      if (typeof data[k] === "string" && data[k].length > 20) acc.reasoning_blocks.push(data[k]);
    }
    if (typeof data.message === "string" && data.message.length > 20) acc.reasoning_blocks.push(data.message);
    if (typeof data.content === "string" && data.content.length > 20) acc.reasoning_blocks.push(data.content);

    // Action
    const a = data.action || data.decision || data.tradeAction || data.order?.side;
    if (a && !acc.action) {
      const al = lower(a);
      if (/(buy|long)/.test(al)) acc.action = "buy";
      else if (/(sell|short|close short)/.test(al)) acc.action = "sell";
      else if (/(hold|wait|no[-\s]?trade)/.test(al)) acc.action = "hold";
      else if (/close/.test(al)) acc.action = "close";
      else acc.action = a.toString();
    }

    // Confidence
    const c = data.confidence ?? data.confidenceScore ?? data.score ?? data.probability;
    if (c != null && acc.confidence == null) {
      const num = Number(c);
      if (!Number.isNaN(num)) acc.confidence = num;
    }

    // Positions
    if (data.position || data.positions || data.order) {
      const pSrc = data.positions ?? data.position ?? data.order;
      const ps = toPositionsStruct(pSrc);
      if (ps.length) acc.positions.push(...ps);
    }

    // Market data heuristic
    const mdKeys = ["price","last","bid","ask","symbol","ticker","spread","vol","volume","openInterest","high","low","mark"];
    for (const k of mdKeys) {
      if (data[k] != null && acc.market_data[k] == null) acc.market_data[k] = data[k];
    }
    if (data.market || data.marketData) {
      const m = data.market || data.marketData;
      if (typeof m === "object") {
        for (const [k,v] of Object.entries(m)) if (acc.market_data[k] == null) acc.market_data[k] = v;
      }
    }
  }

  return acc;
}

function extractFromVisibleText(text) {
  const out = {
    model_name: null,
    action: null,
    confidence: null,
    positions: [],
    market_data: {},
    reasoning: null
  };
  const t = String(text);

  // Model
  const mm = t.match(/model\s*[:\-]\s*([A-Za-z0-9\.\-\s\+]+)/i);
  if (mm) out.model_name = mm[1].trim().toLowerCase().replace(/\s+/g,"-");
  else {
    const m2 = t.match(/\b(DeepSeek|Qwen|Claude|Grok|GPT|Gemini)[^\n]*/i);
    if (m2) out.model_name = m2[0].trim().toLowerCase().replace(/\s+/g,"-");
  }

  // Action
  const am = t.match(/\b(buy|sell|hold|close)\b/i);
  if (am) out.action = am[1].toLowerCase();

  // Confidence
  const cm = t.match(/confidence\s*[:\-]?\s*(\d+(?:\.\d+)?)/i);
  if (cm) out.confidence = Number(cm[1]);

  // Positions
  const pm = [...t.matchAll(/\b(long|short)\b[^A-Za-z0-9]{0,6}([A-Z]{2,10})/gi)];
  for (const m of pm) {
    out.positions.push({ symbol: m[2].toUpperCase(), side: m[1].toUpperCase(), size: null, leverage: null, entry: null, stop: null, takeProfit: null });
  }

  // Reasoning
  out.reasoning = t.length > 80 ? t : null;
  return out;
}

// In-memory buffers per origin
const BUFFERS = new Map();  // key: origin -> { visible, jsons: [], lastAt, modelId }

function upsertBuffer(origin) {
  if (!BUFFERS.has(origin)) BUFFERS.set(origin, { visible: "", jsons: [], lastAt: Date.now(), modelId: null });
  return BUFFERS.get(origin);
}

function extractModelIdFromJson(jsonStr) {
  // Quick check for model ID without full JSON parse
  try {
    const data = JSON.parse(jsonStr);
    if (data.conversations && Array.isArray(data.conversations) && data.conversations.length > 0) {
      const conv = data.conversations[0];
      if (conv.id) {
        const match = conv.id.match(/^([a-z0-9\-\.]+?)_\d+/i);
        if (match) return match[1];
      }
      if (conv.model_id) return conv.model_id;
    }
  } catch {
    // Not a conversation JSON, ignore
  }
  return null;
}

function processConversation(conv, origin) {
  // Process a single conversation object directly (from /api/conversations array)
  if (!conv || !conv.model_id) return 0;

  const model_name = conv.model_id.toLowerCase().replace(/\s+/g, "-");
  const timestamp = new Date().toISOString();

  // Build reasoning from conversation fields
  const reasoningParts = [];
  if (conv.user_prompt && conv.user_prompt.length > 20) {
    reasoningParts.push("USER_PROMPT:\n" + conv.user_prompt);
  }
  if (conv.cot_trace && conv.cot_trace.length > 20) {
    reasoningParts.push("\nCHAIN_OF_THOUGHT:\n" + conv.cot_trace);
  } else if (conv.cot_trace_summary && conv.cot_trace_summary.length > 20) {
    reasoningParts.push("\nCHAIN_OF_THOUGHT:\n" + conv.cot_trace_summary);
  }
  if (conv.llm_response) {
    const responseStr = typeof conv.llm_response === "string"
      ? conv.llm_response
      : JSON.stringify(conv.llm_response, null, 2);
    if (responseStr.length > 20) {
      reasoningParts.push("\nTRADING_DECISIONS:\n" + responseStr);
    }
  }

  const reasoning = reasoningParts.join("\n").slice(0, 50000); // Allow up to 50k chars for long model responses
  const raw_content = JSON.stringify(conv);
  const message_hash = sha16(conv.id || raw_content);
  const scraped_at = new Date().toISOString();

  // Extract action/confidence from llm_response if it's an object
  let action = null;
  let confidence = null;
  if (conv.llm_response && typeof conv.llm_response === "object") {
    // Try to find action/confidence in response
    for (const [key, val] of Object.entries(conv.llm_response)) {
      if (val && typeof val === "object") {
        if (val.signal) action = val.signal;
        if (val.confidence != null) confidence = val.confidence;
      }
    }
  }

  const stmt = db.prepare(`
    INSERT INTO model_chat
    (model_name, timestamp, message_hash, reasoning, action, confidence, positions, market_data, raw_content, scraped_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(message_hash) DO UPDATE SET
      model_name = COALESCE(excluded.model_name, model_chat.model_name),
      reasoning = COALESCE(NULLIF(excluded.reasoning, ''), model_chat.reasoning),
      action = COALESCE(excluded.action, model_chat.action),
      confidence = COALESCE(excluded.confidence, model_chat.confidence),
      scraped_at = excluded.scraped_at
  `);

  const info = stmt.run(model_name, timestamp, message_hash, reasoning, action, confidence, "[]", "{}", raw_content, scraped_at);

  if (info.changes > 0) {
    console.log(`[DEBUG] Saved conversation: ${model_name} (${conv.id})`);
  }

  return info.changes;
}

function consolidateAndPersist(origin) {
  const buf = BUFFERS.get(origin);
  if (!buf) {
    console.log("[DEBUG] No buffer for origin:", origin);
    return 0;
  }
  const now = Date.now();
  const timeSinceLastUpdate = now - buf.lastAt;
  const jsonCount = buf.jsons?.length || 0;

  // Calculate total content size
  const raw = [buf.visible, buf.jsons.join("\n")].filter(Boolean).join("\n\n").trim();
  const contentLength = raw.length;

  console.log("[DEBUG] Buffer state:", {
    origin,
    modelId: buf.modelId || "none",
    timeSinceLastUpdate,
    visibleLength: buf.visible?.length || 0,
    jsonCount,
    contentLength
  });

  // Persist if: (quiet period reached) OR (buffer has enough chunks) OR (content is large enough)
  const quietPeriodReached = timeSinceLastUpdate >= 500;
  const bufferFull = jsonCount >= 15; // Persist after 15 JSON chunks
  const contentLarge = contentLength >= 5000; // Persist if content exceeds 5KB

  if (!quietPeriodReached && !bufferFull && !contentLarge) {
    console.log("[DEBUG] Waiting - not quiet yet, buffer not full, content not large enough");
    return 0;
  }

  const reason = bufferFull ? "buffer full (15+ chunks)" :
                 contentLarge ? `content large (${contentLength} chars)` :
                 "quiet period reached";
  console.log("[DEBUG] Persisting! Reason:", reason);
  console.log("[DEBUG] Raw content length:", contentLength);

  if (!raw || contentLength < 20) {
    console.log("[DEBUG] Content too short, skipping. Length:", contentLength);
    return 0; // reduced from 80 to 20 chars minimum
  }

  // Extract from JSON chunks
  const allObjs = buf.jsons.flatMap(parseNdjsonOrSse);
  const fromJson = extractFromJsonObjects(allObjs);

  // Extract from visible text as fallback
  const fromText = extractFromVisibleText(buf.visible || "");

  const model_name = fromJson.model_name || fromText.model_name || "unknown-model";
  const timestamp = new Date().toISOString();
  const message_hash = sha16(raw);
  const reasoning = (fromJson.reasoning_blocks.join("\n\n") || fromText.reasoning || "").slice(0, 50000);
  const action = fromJson.action || fromText.action || null;
  const confidence = fromJson.confidence != null ? fromJson.confidence : fromText.confidence;
  const positionsArr = [...fromJson.positions, ...fromText.positions];
  const positions = JSON.stringify(positionsArr);
  const market_data = JSON.stringify(fromJson.market_data);
  const scraped_at = new Date().toISOString();

  // Upsert
  const stmt = db.prepare(`
    INSERT INTO model_chat
    (model_name, timestamp, message_hash, reasoning, action, confidence, positions, market_data, raw_content, scraped_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(message_hash) DO UPDATE SET
      model_name = COALESCE(excluded.model_name, model_chat.model_name),
      reasoning = COALESCE(NULLIF(excluded.reasoning, ''), model_chat.reasoning),
      action = COALESCE(excluded.action, model_chat.action),
      confidence = COALESCE(excluded.confidence, model_chat.confidence),
      positions = CASE WHEN excluded.positions != '[]' THEN excluded.positions ELSE model_chat.positions END,
      market_data = CASE WHEN excluded.market_data != '{}' THEN excluded.market_data ELSE model_chat.market_data END,
      scraped_at = excluded.scraped_at
  `);

  const info = stmt.run(model_name, timestamp, message_hash, reasoning, action, confidence, positions, market_data, raw, scraped_at);

  // Reset buffer after a write
  if (info.changes > 0) {
    BUFFERS.set(origin, { visible: "", jsons: [], lastAt: now, modelId: null });
  }
  return info.changes;
}

const app = express();
app.use(express.json({ limit: "10mb" }));
app.use(morgan("tiny"));

app.get("/health", (req, res) => {
  // Minimal stats
  const cnt = db.prepare("SELECT COUNT(*) as c FROM model_chat").get().c;
  res.json({ ok: true, db: DB_PATH, rows: cnt });
});

app.post("/ingest", (req, res) => {
  const body = req.body;
  const valid = validate(body);
  if (!valid) return res.status(400).json({ error: "schema_validation_failed", details: validate.errors });

  let inserted = 0;
  for (const evt of body.events) {
    const origin = new URL(evt.url || "https://nof1.ai/").origin;
    const buf = upsertBuffer(origin);

    switch (evt.payload.kind) {
      case "visible_text":
      case "dom_snapshot":
        if (evt.payload.data && evt.payload.data.length > 40) {
          buf.visible = evt.payload.data;
          buf.lastAt = Date.now();
        }
        break;
      case "fetch_json":
      case "sse_message":
      case "ws_message":
        if (typeof evt.payload.data === "string" && evt.payload.data.length > 0) {
          // Try to parse as conversations array
          try {
            const parsed = JSON.parse(evt.payload.data);
            if (parsed.conversations && Array.isArray(parsed.conversations)) {
              console.log(`[DEBUG] Processing ${parsed.conversations.length} conversations from API`);
              // Process each conversation as a separate database row
              for (const conv of parsed.conversations) {
                inserted += processConversation(conv, origin);
              }
              break; // Skip buffering for conversations API
            }
          } catch (e) {
            // Not valid JSON or not conversations array, continue to buffering
          }

          // Not conversations array, use buffering approach
          const incomingModelId = extractModelIdFromJson(evt.payload.data);
          if (incomingModelId && buf.modelId && incomingModelId !== buf.modelId) {
            console.log(`[DEBUG] Model switch detected: ${buf.modelId} -> ${incomingModelId}, flushing buffer`);
            inserted += consolidateAndPersist(origin);
            const freshBuf = upsertBuffer(origin);
            freshBuf.modelId = incomingModelId;
            freshBuf.jsons.push(evt.payload.data);
            freshBuf.lastAt = Date.now();
          } else {
            if (incomingModelId && !buf.modelId) {
              buf.modelId = incomingModelId;
            }
            buf.jsons.push(evt.payload.data);
            buf.lastAt = Date.now();
          }
        }
        break;
      default:
        break;
    }
    inserted += consolidateAndPersist(origin);
  }

  res.json({ ok: true, inserted });
});

// Manual flush endpoint for debugging
app.post("/flush", (req, res) => {
  let total = 0;
  for (const origin of Array.from(BUFFERS.keys())) total += consolidateAndPersist(origin);
  res.json({ ok: true, inserted: total });
});

app.listen(PORT, () => {
  console.log(`NOF1 collector listening on http://127.0.0.1:${PORT}  DB=${DB_PATH}`);
});
