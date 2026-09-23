// Change to your deployed HTTPS API before publishing.
const API = "http://localhost:5000";
const EXT = { "image/png": "png", "image/webp": "webp" };

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type !== "scan") return;
  (async () => {
    try {
      const blob = await (await fetch(msg.url)).blob();
      const { token } = await (await fetch(API + "/api/token")).json();
      const fd = new FormData();
      fd.append("image", blob, "image." + (EXT[blob.type] || "jpg"));
      const res = await fetch(API + "/api/analyze", { method: "POST", headers: { "X-CSRF-Token": token }, body: fd });
      sendResponse(await res.json());
    } catch (e) {
      sendResponse({ error: String(e) });
    }
  })();
  return true; // async response
});
