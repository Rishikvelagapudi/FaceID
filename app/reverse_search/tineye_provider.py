import os
from pathlib import Path
import requests

from app.reverse_search.base import ReverseImageSearchProvider

class TinEyeProvider(ReverseImageSearchProvider):
    name = "TinEye"

    def __init__(self):
        self.api_key = os.getenv("TINEYE_API_KEY")
        if not self.api_key:
            raise RuntimeError("TINEYE_API_KEY is not configured.")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        self.endpoint = "https://api.tineye.com/rest/search"

    def search(self, image_path: Path, max_results: int = None):
        max_results = max_results or int(os.getenv("MAX_SEARCH_RESULTS", "10"))
        
        with open(image_path, "rb") as f:
            files = {"image": (image_path.name, f, "application/octet-stream")}
            response = requests.post(
                self.endpoint,
                data={"api_key": self.api_key},
                files=files,
                timeout=self.timeout
            )
            
        response.raise_for_status()
        data = response.json()
        
        results = []
        matches = data.get("results", {}).get("matches", [])
        
        for match in matches:
            backlinks = match.get("backlinks", [])
            for link_info in backlinks:
                results.append({
                    "title": link_info.get("url"),
                    "source": match.get("domain"),
                    "link": link_info.get("backlink"),
                    "image_url": link_info.get("url"),
                    "search_engine": self.name
                })
                if len(results) >= max_results:
                    return results
                    
        return results
