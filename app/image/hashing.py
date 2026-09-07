import hashlib
from pathlib import Path
from PIL import Image
import imagehash

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def fingerprint_image(path: Path) -> dict:
    image = Image.open(path)
    image.verify()
    image = Image.open(path).convert("RGB")
    return {
        "sha256": sha256_file(path),
        "phash": str(imagehash.phash(image)),
    }
