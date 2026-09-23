import io, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import numpy as np
from PIL import Image
from app import app


def png_bytes():
    arr = (np.random.rand(200, 200, 3) * 255).astype("uint8")
    buf = io.BytesIO(); Image.fromarray(arr).save(buf, "PNG"); return buf.getvalue()


def post(c, name, data, token=True):
    h = {"X-CSRF-Token": c.get("/api/token").json["token"]} if token else {}
    return c.post("/api/analyze", data={"image": (io.BytesIO(data), name)}, headers=h)


def test_flow():
    app.config["TESTING"] = True
    c = app.test_client()
    r = post(c, "a.png", png_bytes())
    assert r.status_code == 200 and r.json["report_id"].startswith("VQL-")
    assert post(c, "a.png", png_bytes(), token=False).status_code == 403      # CSRF
    assert post(c, "a.exe", b"MZ....").status_code == 415                      # extension whitelist
    assert post(c, "a.png", b"MZ" + b"0" * 50).status_code == 400              # executable / not an image
    assert c.get("/").headers["X-Content-Type-Options"] == "nosniff"
