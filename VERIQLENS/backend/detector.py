"""VERIQLENS detector.

!! PLACEHOLDER !!  These are simple image-statistics heuristics so the whole pipeline
(upload -> analyze -> report) works end to end. They are NOT a trained deepfake model.
Replace `analyze()` internals with your trained model (ONNX / TFLite / PyTorch) and keep
the returned dict shape the same; the API, web app and extension need no changes.
"""
import numpy as np
from PIL import Image, ImageFilter

MODEL_NAME = "heuristic-v0 (not trained)"


def analyze(img: Image.Image) -> dict:
    gray = img.convert("RGB").convert("L").resize((256, 256))
    g = np.asarray(gray, dtype=np.float32)
    blur = np.asarray(gray.filter(ImageFilter.GaussianBlur(2)), dtype=np.float32)
    noise = float(np.std(g - blur))

    spec = np.abs(np.fft.fftshift(np.fft.fft2(g)))
    yy, xx = np.ogrid[:256, :256]
    radius = np.hypot(yy - 128, xx - 128)
    hf_ratio = float(spec[radius > 90].sum() / spec.sum())

    score, signals = 0.35, []
    if noise < 2.0:
        score += 0.25
        signals.append("Unusually smooth pixel noise")
    if hf_ratio < 0.02:
        score += 0.20
        signals.append("Weak high-frequency detail")
    if not img.getexif():
        score += 0.10
        signals.append("No camera metadata (EXIF)")
    score = min(score, 0.95)

    if score >= 0.65:
        verdict, risk, rec = "LIKELY AI-GENERATED", "HIGH", "Do not share until verified"
    elif score >= 0.45:
        verdict, risk, rec = "SUSPICIOUS", "MEDIUM", "Verify the source before sharing"
    else:
        verdict, risk, rec = "LIKELY REAL", "LOW", "No strong manipulation signals"

    return {
        "verdict": verdict,
        "badge": {"LIKELY AI-GENERATED": "red", "SUSPICIOUS": "yellow", "LIKELY REAL": "green"}[verdict],
        "ai_score": round(score * 100, 1),
        "risk": risk,
        "signals": signals or ["No strong forensic signals"],
        "recommendation": rec,
        "model": MODEL_NAME,
    }
