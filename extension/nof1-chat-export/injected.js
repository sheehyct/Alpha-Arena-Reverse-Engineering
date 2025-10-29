(() => {
  const post = (payload) => {
    window.postMessage({ __NOF1_EXPORT__: true, ...payload }, "*");
  };

  // Hook WebSocket
  const _WS = window.WebSocket;
  window.WebSocket = function(url, protocols) {
    const ws = new _WS(url, protocols);
    try {
      ws.addEventListener("message", (evt) => {
        try {
          post({ kind: "ws_message", url, data: evt.data });
        } catch {}
      });
      ws.addEventListener("open", () => post({ kind: "ws_open", url }));
      ws.addEventListener("close", () => post({ kind: "ws_close", url }));
      ws.addEventListener("error", () => post({ kind: "ws_error", url }));
    } catch {}
    return ws;
  };
  window.WebSocket.prototype = _WS.prototype;

  // Hook EventSource (SSE)
  const _ES = window.EventSource;
  window.EventSource = function(url, config) {
    const es = new _ES(url, config);
    try {
      es.addEventListener("message", (evt) => {
        try {
          post({ kind: "sse_message", url, data: evt.data });
        } catch {}
      });
      es.addEventListener("open", () => post({ kind: "sse_open", url }));
      es.addEventListener("error", () => post({ kind: "sse_error", url }));
    } catch {}
    return es;
  };
  window.EventSource.prototype = _ES.prototype;

  // Hook fetch for JSON
  const _fetch = window.fetch;
  window.fetch = async (...args) => {
    const res = await _fetch(...args);
    try {
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        const clone = res.clone();
        const data = await clone.text(); // keep raw; collector can JSON.parse
        post({ kind: "fetch_json", url: (args[0] && args[0].toString()) || "", data });
      }
    } catch {}
    return res;
  };

  // Observe visible chat text for fallback
  const collectVisible = () => {
    try {
      const root = document.querySelector("main") || document.body;
      if (!root) return null;

      // Heuristics: look for blocks that contain ModelChat-like content
      const blocks = Array.from(root.querySelectorAll("*"))
        .filter(n => n.childElementCount === 0 && (n.innerText || "").trim().length > 60)
        .map(n => n.innerText.trim());

      const textBlob = blocks.slice(-60).join("\n\n"); // recent area
      return textBlob;
    } catch {
      return null;
    }
  };

  // Periodic visible dump
  setInterval(() => {
    const text = collectVisible();
    if (text) post({ kind: "visible_text", data: text });
  }, 5000);

  // Periodic API polling for conversations (since fetch hook may miss cached responses)
  let lastConversationsHash = null;
  setInterval(() => {
    fetch('/api/conversations')
      .then(res => res.text())
      .then(data => {
        // Only send if data has changed (simple hash check)
        const dataHash = data.length + data.substring(0, 100);
        if (dataHash !== lastConversationsHash) {
          lastConversationsHash = dataHash;
          post({ kind: "fetch_json", url: "https://nof1.ai/api/conversations", data });
        }
      })
      .catch(() => {}); // Silently fail if endpoint not available
  }, 60000); // Every 60 seconds

  // Also fetch immediately on load
  setTimeout(() => {
    fetch('/api/conversations')
      .then(res => res.text())
      .then(data => {
        lastConversationsHash = data.length + data.substring(0, 100);
        post({ kind: "fetch_json", url: "https://nof1.ai/api/conversations", data });
      })
      .catch(() => {});
  }, 3000); // 3 seconds after page load
})();
