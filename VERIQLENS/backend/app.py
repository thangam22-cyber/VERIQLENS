"""VERIQLENS backend (Phase 1). Images live in RAM only and are never written to disk."""
import hashlib
import io
import os
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_from_directory
from PIL import Image, UnidentifiedImageError

from detector import analyze

Image.MAX_IMAGE_PIXELS = 50_000_000          # decompression-bomb guard
MAX_BYTES = 16 * 1024 * 1024                 # Layer 1: 16 MB limit
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_FMT = {"JPEG", "PNG", "WEBP"}
RATE_LIMIT, WINDOW, TOKEN_TTL = 10, 60, 900  # Layer 5: 10 req/min per client

FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES

_SALT = secrets.token_bytes(16)   # per-process salt: IPs are hashed, kept in RAM only (Layer 4)
_hits = defaultdict(deque)
_tokens = {}


def _client_key():
    return hashlib.sha256(_SALT + (request.remote_addr or "").encode()).hexdigest()


def _rate_limited():
    now = time.time()
    if len(_hits) > 10_000:
        for k in [k for k, q in _hits.items() if not q or now - q[-1] > WINDOW]:
            del _hits[k]
    q = _hits[_client_key()]
    while q and now - q[0] > WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False


def _take_token(token):
    """CSRF token: single use, short lived."""
    now = time.time()
    for t in [t for t, exp in _tokens.items() if exp < now]:
        del _tokens[t]
    return _tokens.pop(token, 0) > now


def scan_for_malware(data: bytes) -> bool:
    """Layer 1 hook: plug ClamAV (clamd) in here. Returns True if clean.
    Current check only rejects Windows/Linux executables by magic bytes."""
    return not (data[:2] == b"MZ" or data[:4] == b"\x7fELF")


@app.after_request
def secure_headers(resp):
    resp.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' blob:; frame-ancestors 'none'"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:name>")
def assets(name):
    if name not in {"app.js", "style.css"}:
        return jsonify(error="Not found"), 404
    return send_from_directory(FRONTEND, name)


@app.get("/api/token")
def token():
    if _rate_limited():
        return jsonify(error="Too many requests"), 429
    t = secrets.token_urlsafe(24)
    _tokens[t] = time.time() + TOKEN_TTL
    return jsonify(token=t)


@app.post("/api/analyze")
def analyze_route():
    if _rate_limited():
        return jsonify(error="Too many requests. Try again in a minute."), 429
    if not _take_token(request.headers.get("X-CSRF-Token", "")):
        return jsonify(error="Invalid or expired token"), 403

    f = request.files.get("image")
    if not f or not f.filename:
        return jsonify(error="No image uploaded"), 400
    if os.path.splitext(f.filename.lower())[1] not in ALLOWED_EXT:
        return jsonify(error="Only JPG, PNG or WEBP allowed"), 415

    data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        return jsonify(error="File larger than 16 MB"), 413
    if not scan_for_malware(data):
        return jsonify(error="File rejected"), 400

    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()
        if fmt not in ALLOWED_FMT:
            return jsonify(error="Unsupported image format"), 415
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError):
        return jsonify(error="Not a valid image"), 400

    now = datetime.now(timezone.utc)
    report = analyze(img)
    report["report_id"] = f"VQL-{now.year}-{secrets.token_hex(3).upper()}"
    report["analyzed_at"] = now.strftime("%d %b %Y, %H:%M UTC")
    del data, img                                   # Layer 2: nothing retained
    return jsonify(report)


if __name__ == "__main__":
    # Dev only. Production: run behind Caddy/nginx with TLS 1.3 + HTTPS redirect.
    app.run(host="127.0.0.1", port=5000)
