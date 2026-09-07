from io import BytesIO
import os
import requests
from PIL import Image

TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "20"))

def download_image(url: str) -> Image.Image:
    headers = {
        "User-Agent": "Mozilla/5.0 FaceProof/1.0"
    }
    response = requests.get(
        url,
        headers=headers,
        timeout=TIMEOUT,
        allow_redirects=True
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "image" not in content_type:
        raise ValueError("Candidate URL did not return an image.")

    image = Image.open(BytesIO(response.content)).convert("RGB")
    return image
