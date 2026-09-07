import os
from pathlib import Path
import requests

from app.reverse_search.base import ReverseImageSearchProvider

class SerpApiGoogleLensProvider(ReverseImageSearchProvider):
    name = "SerpApi Google Lens"
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY") or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "SERPAPI_KEY or SERPAPI_API_KEY is missing. Add it to your .env file."
            )
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))

    def search(self, image_path: Path, max_results: int = None):
        max_results = max_results or int(os.getenv("MAX_SEARCH_RESULTS", "10"))

        # Step 1: upload local image to SerpApi Image API.
        with open(image_path, "rb") as f:
            response = requests.post(
                "https://serpapi.com/image",
                params={"api_key": self.api_key},
                files={"image": (image_path.name, f, "application/octet-stream")},
                timeout=self.timeout,
            )
        response.raise_for_status()
        upload = response.json()

        if "error" in upload:
            raise RuntimeError(f"Image upload failed: {upload['error']}")

        image_id = upload.get("image_id")
        if not image_id:
            raise RuntimeError("SerpApi did not return an image_id.")

        # Step 2: real Google Lens reverse-image search.
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_lens",
                "image_id": image_id,
                "api_key": self.api_key,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise RuntimeError(f"Reverse search failed: {data['error']}")

        raw = data.get("visual_matches", [])
        results = []

        for item in raw[:max_results]:
            image_url = (
                item.get("thumbnail")
                or item.get("image")
                or item.get("original")
            )
            link = item.get("link") or item.get("source")

            results.append({
                "title": item.get("title"),
                "source": item.get("source"),
                "link": link,
                "image_url": image_url,
                "search_engine": "Google Lens via SerpApi",
            })

        return results
