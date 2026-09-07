import os
import requests
from pathlib import Path
from bs4 import BeautifulSoup

from app.reverse_search.base import ReverseImageSearchProvider

class FreeWebScraperProvider(ReverseImageSearchProvider):
    name = "Free Yandex Scraper"

    def __init__(self):
        self.timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        # We use a dummy API endpoint for now or try Yandex directly.
        # Note: True web scraping in production often requires proxies.
        self.endpoint = "https://yandex.com/images/search?rpt=imageview"

    def search(self, image_path: Path, max_results: int = None):
        max_results = max_results or int(os.getenv("MAX_SEARCH_RESULTS", "10"))
        
        # Disguise the request as a normal browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        with open(image_path, "rb") as f:
            files = {"upfile": (image_path.name, f, "image/jpeg")}
            response = requests.post(
                self.endpoint,
                headers=headers,
                files=files,
                timeout=self.timeout
            )
            
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # Attempt to parse Yandex's "Sites where the image is displayed" blocks
        for item in soup.find_all("div", class_="CbirSites-Item"):
            if len(results) >= max_results:
                break
                
            title_tag = item.find("div", class_="CbirSites-ItemTitle")
            link_tag = item.find("a", class_="Link")
            
            if link_tag:
                link = link_tag.get("href")
                if link:
                    title = title_tag.text.strip() if title_tag else "Scraped Result"
                    results.append({
                        "title": title,
                        "source": "yandex.com",
                        "link": link,
                        "image_url": link,  # A real scraper would extract the preview image
                        "search_engine": self.name
                    })

        # If CbirSites fails, fallback to general Similar Images
        if not results:
            for item in soup.find_all("a", class_="serp-item__link"):
                if len(results) >= max_results:
                    break
                link = item.get("href")
                if link:
                    if link.startswith("//"): link = "https:" + link
                    elif link.startswith("/"): link = "https://yandex.com" + link
                        
                    results.append({
                        "title": "Similar Image Scraped",
                        "source": "yandex.com",
                        "link": link,
                        "image_url": link,
                        "search_engine": self.name
                    })

        if not results:
            # We either got a CAPTCHA or the HTML structure changed.
            raise RuntimeError("Free scraper found 0 results. Yandex may have blocked the request or changed their HTML layout.")
            
        return results
