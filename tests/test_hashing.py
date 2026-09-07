from pathlib import Path
from PIL import Image
from app.image.hashing import fingerprint_image

def test_fingerprint(tmp_path: Path):
    p = tmp_path / "test.png"
    Image.new("RGB", (100, 100), "white").save(p)
    result = fingerprint_image(p)
    assert len(result["sha256"]) == 64
    assert len(result["phash"]) > 0
