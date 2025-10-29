const STATE = {
  queue: [],
  flushTimer: null,
  endpoint: "http://127.0.0.1:8787/ingest",
  batchSize: 20,
  flushMs: 2000
};

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.source === "nof1-content") {
    // Wrap payload minimally
    STATE.queue.push({
      received_at: new Date().toISOString(),
      url: sender.tab?.url || sender.url || "unknown",
      payload: msg
    });
    scheduleFlush();
  }
});

function scheduleFlush() {
  if (STATE.flushTimer) return;
  STATE.flushTimer = setTimeout(async () => {
    const batch = STATE.queue.splice(0, STATE.batchSize);
    STATE.flushTimer = null;
    if (batch.length === 0) return;

    try {
      await fetch(STATE.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events: batch })
      });
    } catch (e) {
      // Swallow errors; collector might be offline
    }
  }, STATE.flushMs);
}

// Simple commands via chrome.storage (optional)
chrome.storage.onChanged.addListener((changes) => {
  if (changes.nof1_endpoint) {
    STATE.endpoint = changes.nof1_endpoint.newValue || STATE.endpoint;
  }
});
