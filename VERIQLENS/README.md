# VERIQLENS

An intelligent lens that verifies truth. See `docs/PRD.md` for the full product spec.

## What's in this zip
| Path | What it is | Status |
|---|---|---|
| `docs/PRD.md` | Product requirements | Done |
| `backend/` | Flask API with 5-layer security, report generation | Working, tested |
| `backend/detector.py` | Detector | **Placeholder heuristics, not a trained model** |
| `frontend/` | Web upload + report page | Working |
| `extension/` | Chrome (Manifest V3) badge overlay for Instagram / X / Facebook | Prototype, untested on live sites |
| `tests/` | Smoke test (upload, CSRF, extension whitelist, headers) | Passing |
| Phase 2 mobile app | Designed in PRD section 8 | Not built |

## Run
```bash
cd backend && pip install -r requirements.txt && python app.py   # http://127.0.0.1:5000
python -m pytest tests                                            # from project root
```
## Load the extension
`chrome://extensions` -> Developer mode -> Load unpacked -> select `extension/`. Keep the backend running.

## Before real use
1. Replace `detector.analyze()` with your trained model.
2. Put the API behind Caddy/nginx with TLS 1.3 and an HTTP->HTTPS redirect; update `API` in `extension/background.js`.
3. Wire ClamAV into `scan_for_malware()`.
