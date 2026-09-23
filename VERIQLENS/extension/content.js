// Adds a bottom-right badge on feed images. Queue is throttled to respect the 10 req/min API limit
// (each scan uses 2 requests: token + analyze), so ~1 image per 12 s. Raise the limit for real use.
const COLORS = { green: "#1e8e4e", red: "#d33a3a", yellow: "#c98a00", gray: "#666" };
const seen = new WeakSet();
const queue = [];
let busy = false;

function badge(img) {
  const parent = img.parentElement;
  if (getComputedStyle(parent).position === "static") parent.style.position = "relative";
  const b = document.createElement("div");
  Object.assign(b.style, { position: "absolute", right: "6px", bottom: "6px", zIndex: 9999, padding: "2px 8px",
    borderRadius: "10px", font: "600 11px system-ui", color: "#fff", cursor: "pointer", background: COLORS.gray });
  b.textContent = "VQL ...";
  parent.appendChild(b);
  return b;
}

function showReport(r) {
  const p = document.createElement("div");
  Object.assign(p.style, { position: "fixed", right: "16px", bottom: "16px", zIndex: 2147483647, width: "280px",
    background: "#fff", color: "#111", border: "1px solid #ccc", borderRadius: "10px", padding: "12px", font: "13px system-ui" });
  const lines = [r.verdict, "ID: " + r.report_id, "AI score: " + r.ai_score + "%", "Risk: " + r.risk,
    "Signals: " + r.signals.join("; "), r.recommendation, "(click to close)"];
  lines.forEach((t, i) => { const d = document.createElement("div"); d.textContent = t; if (i === 0) d.style.fontWeight = "700"; p.appendChild(d); });
  p.onclick = () => p.remove();
  document.body.appendChild(p);
}

function pump() {
  if (busy || !queue.length) return;
  busy = true;
  const { img, b } = queue.shift();
  chrome.runtime.sendMessage({ type: "scan", url: img.currentSrc || img.src }, (r) => {
    if (!r || r.error) { b.textContent = "VQL ?"; }
    else {
      b.textContent = r.verdict === "LIKELY REAL" ? "REAL" : r.verdict === "SUSPICIOUS" ? "SUSPICIOUS" : "FAKE";
      b.style.background = COLORS[r.badge];
      b.onclick = (e) => { e.stopPropagation(); e.preventDefault(); showReport(r); };
    }
    setTimeout(() => { busy = false; pump(); }, 12000);
  });
}

function scan() {
  document.querySelectorAll("img").forEach((img) => {
    if (seen.has(img) || img.naturalWidth < 200 || !img.parentElement) return;
    seen.add(img);
    queue.push({ img, b: badge(img) });
  });
  pump();
}

new MutationObserver(() => scan()).observe(document.body, { childList: true, subtree: true });
scan();
