# VERIQLENS - Product Requirements Document

**Version:** 0.1 | **Date:** 23 Sep 2026 | **Owner:** Thangam | **Former name:** AEGISYN
**Tagline:** An intelligent lens that verifies truth. (VERI = verify, Q = IQ, LENS = sees through deception)

## 1. Overview
VERIQLENS is an AI agent that silently watches your digital world (gallery, social feeds, downloads) and tells you what is real and what is fake, without you having to do anything.

## 2. Problem
AI-generated and manipulated images spread faster than people can verify them. Today a user must download an image, find a checker, upload it and interpret the result. Almost nobody does that, so fakes get shared.

## 3. Goals / Non-goals
**Goals:** one-tap or zero-tap verification; a clear Real / Suspicious / Fake label; an explainable forensic report; privacy as the foundation (no image ever retained).
**Non-goals (for now):** video/audio deepfake detection, legal-grade forensic certification, content moderation or takedown, storing user history.

## 4. Users
| User | Need |
|---|---|
| Everyday social media user | Know if a viral image is fake before sharing |
| Journalist / student / researcher | Quick first-pass screening with a citable report ID |
| Family members of scam targets | Catch fake profile photos, fake proofs |

## 5. Phases
| Phase | Scope | Status |
|---|---|---|
| 1 - Web app | Upload image -> AI analysis -> Real/Fake + confidence + report | Web app already built by owner. This repo adds a hardened reference backend, UI and report format with a **placeholder detector** |
| 2 - Mobile app (gallery) | Background gallery scan, bottom-right badge per photo (green REAL / red FAKE / yellow SUSPICIOUS), tap for full report | Designed only (section 8). Not built |
| 3 - Social media sidebar agent | Browser extension overlays a badge on Instagram / X / Facebook images, no download needed | Working prototype in `extension/` (needs trained model, hosted HTTPS API, and per-site tuning) |

## 6. Functional requirements
**Phase 1**
- F1. Accept JPG / PNG / WEBP up to 16 MB; reject everything else.
- F2. Return verdict, AI score (%), risk level, forensic signals, recommendation, unique Report ID (`VQL-YYYY-XXXXXX`), UTC timestamp, model name.
- F3. Verdict wording is probabilistic ("LIKELY AI-GENERATED"), never absolute.
- F4. Works without login.

**Phase 2**
- F5. Scan new gallery images in the background (WorkManager on Android), on-device.
- F6. Show a colored badge bottom-right on each thumbnail; tap opens the report screen.
- F7. Cache results locally (hash -> verdict) so images are scanned once.
- F8. User can pause scanning and choose which albums are scanned.

**Phase 3**
- F9. Content script badges images above a minimum size in the feed.
- F10. Click badge opens the report panel.
- F11. Throttled queue to respect rate limits; visible "?" state on failure.

## 7. Security and privacy architecture (5 layers)
| Layer | Requirement | Reference implementation |
|---|---|---|
| 1 Input validation | Type check, 16 MB limit, extension whitelist, malware scan, no executables | Done in `backend/app.py` (ClamAV is a hook, not wired) |
| 2 Zero persistent storage | RAM only, never in DB, no cloud backup, auto-delete within 60 s | Done: image never touches disk, references dropped after analysis |
| 3 Transport | TLS 1.3, HTTPS only, HSTS, CSP, no HTTP fallback | Headers done in app; TLS 1.3 + redirect must be configured on the reverse proxy |
| 4 Privacy by design | No login, tracking, cookies, IP logging | Done. IP is only used as a salted hash held in RAM for rate limiting |
| 5 Abuse prevention | 10 req/min per client, CSRF, upload flood block, bot detection | Rate limit + single-use CSRF token done. Bot detection is not implemented |

Follows OWASP Top 10, Privacy by Design and Zero Trust principles.
**Privacy promise:** We never store, share, or sell your images. Your image lives for analysis only, then it's gone.
**Phase 2 rule:** gallery images must be analysed **on-device**. Uploading a whole gallery to a server would contradict the privacy promise.

## 8. Architecture
```
Phase 1  Browser --HTTPS--> Flask API --> detector.analyze() --> report JSON
Phase 2  Android app (MediaStore + WorkManager) --> on-device TFLite model --> local cache --> badge overlay
Phase 3  Extension content.js --> background.js (fetch + upload) --> API --> badge + report panel
```
Detector contract (`backend/detector.py`): `analyze(PIL.Image) -> dict` with keys `verdict, badge, ai_score, risk, signals, recommendation, model`. Swap in the trained model without touching the API, UI or extension.

## 9. Report format
```
VERIQLENS FORENSIC REPORT
Report ID : VQL-2026-4F9A1C
Analyzed  : 23 Sep 2026, 14:32 UTC
VERDICT   : LIKELY AI-GENERATED
AI Score  : 87.4%     Risk: HIGH
Signals   : GAN frequency artifact; pixel noise inconsistency; face boundary irregularity
Advice    : Do not share until verified
```

## 10. Success metrics
- Detection quality on a held-out set (target to be agreed: precision >= 90% on FAKE label, false-positive rate on real photos < 5%).
- Median analysis time < 3 s (web), < 500 ms per image on-device.
- 0 images retained (verified by test and code review).
- Task completion: user gets a verdict in <= 2 taps (web) / 0 taps (Phase 2-3).

## 11. Risks
| Risk | Mitigation |
|---|---|
| Detector errors, especially false "FAKE" on real photos | Probabilistic wording, "Suspicious" band, publish accuracy honestly, keep a feedback path |
| New generators evade the model | Regular retraining, versioned model name in every report |
| Privacy contradiction in Phase 2/3 | On-device inference for gallery; for extension, disclose that the image is sent for analysis and never stored |
| Social platform policies (Instagram/X/Facebook) on scraping or overlays | Legal/policy review before public release; the extension only reads what the user already sees |
| Name conflicts | Check domain, GitHub, Play Store and trademark for "VERIQLENS" before launch |

## 12. Roadmap
| When | What |
|---|---|
| Now | Finish Phase 1: trained model plugged in, security layers verified |
| 3rd year | Phase 1 web app 100% working |
| Final year project | Phase 2 mobile gallery badge |
| Future | Phase 3 social agent, then full platform |

## 13. Open questions
1. Which dataset and model architecture for the trained detector?
2. Android only first, or Android + iOS?
3. Extension distribution: Chrome Web Store, or side-loaded for the demo?
