const $ = (id) => document.getElementById(id);

async function analyzeFile(file) {
  const status = $("status"), box = $("report");
  box.hidden = true;
  status.textContent = "Analyzing...";
  try {
    const { token } = await (await fetch("/api/token")).json();
    const fd = new FormData();
    fd.append("image", file);
    const res = await fetch("/api/analyze", { method: "POST", headers: { "X-CSRF-Token": token }, body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Analysis failed");
    status.textContent = "";
    render(data);
  } catch (e) {
    status.textContent = e.message;
  }
}

function el(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;   // textContent only: no HTML injection
  if (cls) n.className = cls;
  return n;
}

function render(r) {
  const box = $("report");
  box.replaceChildren(el("h2", r.verdict, "v-" + r.badge));
  const dl = el("dl");
  [["Report ID", r.report_id], ["Analyzed", r.analyzed_at], ["AI score", r.ai_score + "%"],
   ["Risk level", r.risk], ["Signals", r.signals.join("; ")], ["Advice", r.recommendation],
   ["Model", r.model]].forEach(([k, v]) => { dl.append(el("dt", k), el("dd", v)); });
  box.append(dl);
  box.hidden = false;
}

$("file").addEventListener("change", (e) => e.target.files[0] && analyzeFile(e.target.files[0]));
