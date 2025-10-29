(() => {
  // Inject hooks
  const s = document.createElement("script");
  s.src = chrome.runtime.getURL("injected.js");
  s.type = "text/javascript";
  (document.head || document.documentElement).appendChild(s);
  s.remove();

  const sendToBG = (payload) => {
    chrome.runtime.sendMessage({ source: "nof1-content", ...payload });
  };

  // Listen for page-level messages
  window.addEventListener("message", (event) => {
    if (!event.data || !event.data.__NOF1_EXPORT__) return;
    sendToBG(event.data);
  });

  // Manual scrape of ModelChat DOM when user presses Alt+E
  const extractModelChat = () => {
    // Best-effort heuristics
    const container = document.querySelector('main') || document.body;
    const sections = [];
    if (!container) return;

    const headings = Array.from(container.querySelectorAll("h1,h2,h3,summary,button"))
      .map(h => h.innerText?.trim().toUpperCase())
      .filter(Boolean);

    const textNodes = Array.from(container.querySelectorAll("*"))
      .filter(n => n.childElementCount === 0 && (n.innerText || "").trim().length > 0)
      .map(n => n.innerText.trim());

    const blob = textNodes.join("\n");
    sendToBG({ kind: "dom_snapshot", data: blob, headings });
  };

  document.addEventListener("keydown", (e) => {
    if (e.altKey && e.key.toLowerCase() === "e") {
      extractModelChat();
    }
  });

  // Initial ping
  sendToBG({ kind: "ready" });
})();
