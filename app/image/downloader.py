from io import BytesIO
import os
import requests
from PIL import Image

TIMEOUT = float(os.getenv("CANDIDATE_DOWNLOAD_TIMEOUT", "3.5"))
_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=1)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session

def download_image(url: str, fallback_url: str = None) -> Image.Image:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    session = _get_session()
    
    urls_to_try = [u for u in [url, fallback_url] if u]
    last_err = None

    for target_url in urls_to_try:
        try:
            response = session.get(
                target_url,
                headers=headers,
                timeout=TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()

            content = response.content
            # Quick magic byte check for images
            if not (content[:4] in (b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1', b'\xff\xd8\xff\xdb', b'\xff\xd8\xff\xee') 
                    or content[:8] == b'\x89PNG\r\n\x1a\n' 
                    or content[:4] == b'RIFF'
                    or content[:4] == b'GIF8'):
                content_type = response.headers.get("content-type", "").lower()
                if "image" not in content_type:
                    raise ValueError(f"Candidate URL did not return image data: {content_type}")

            image = Image.open(BytesIO(content)).convert("RGB")
            # Downscale massive candidate images to max 1024px
            if max(image.size) > 1024:
                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            return image
        except Exception as exc:
            last_err = exc
            continue

    raise ValueError(f"Failed to download candidate image: {last_err}")

