import os
from pathlib import Path
import requests

from app.reverse_search.base import ReverseImageSearchProvider

class AzureBingVisualSearchProvider(ReverseImageSearchProvider):
    name = "Azure Bing Visual Search"

    def __init__(self):
        self.api_key = os.getenv("BING_SEARCH_API_KEY")
        if not self.api_key:
            raise RuntimeError("BING_SEARCH_API_KEY is not configured.")
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        self.endpoint = "https://api.bing.microsoft.com/v7.0/images/visualsearch"

    def search(self, image_path: Path, max_results: int = None):
        max_results = max_results or int(os.getenv("MAX_SEARCH_RESULTS", "10"))
        
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        
        with open(image_path, "rb") as f:
            files = {"image": (image_path.name, f, "application/octet-stream")}
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                timeout=self.timeout
            )
            
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Parse Bing response structure (simplified)
        tags = data.get("tags", [])
        for tag in tags:
            actions = tag.get("actions", [])
            for action in actions:
                if action.get("actionType") in ["PagesIncluding", "VisualSearch"]:
                    items = action.get("data", {}).get("value", [])
                    for item in items:
                        results.append({
                            "title": item.get("name"),
                            "source": item.get("hostPageDisplayUrl"),
                            "link": item.get("hostPageUrl"),
                            "image_url": item.get("contentUrl") or item.get("thumbnailUrl"),
                            "search_engine": self.name
                        })
                        if len(results) >= max_results:
                            return results
                            
        return results
