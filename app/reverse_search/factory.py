import os
import logging
from app.reverse_search.serpapi_provider import SerpApiGoogleLensProvider
from app.reverse_search.bing_provider import AzureBingVisualSearchProvider
from app.reverse_search.tineye_provider import TinEyeProvider
from app.reverse_search.free_scraper_provider import FreeWebScraperProvider

def get_providers():
    """
    Instantiates and returns a list of configured providers.
    Order determines fallback priority.
    """
    providers = []
    
    # 0. Free Web Scraper (if enabled)
    if os.getenv("USE_FREE_SCRAPER", "").lower() == "true":
        try:
            providers.append(FreeWebScraperProvider())
            logging.info("Enabled completely FREE web scraper as primary provider.")
        except Exception as e:
            logging.warning(f"Failed to initialize FreeWebScraperProvider: {e}")
            
    # 1. SerpApi
    if os.getenv("SERPAPI_API_KEY"):
        try:
            providers.append(SerpApiGoogleLensProvider())
        except Exception as e:
            logging.warning(f"Failed to initialize SerpApiGoogleLensProvider: {e}")
            
    # 2. Bing Visual Search
    if os.getenv("BING_SEARCH_API_KEY"):
        try:
            providers.append(AzureBingVisualSearchProvider())
        except Exception as e:
            logging.warning(f"Failed to initialize AzureBingVisualSearchProvider: {e}")
            
    # 3. TinEye
    if os.getenv("TINEYE_API_KEY"):
        try:
            providers.append(TinEyeProvider())
        except Exception as e:
            logging.warning(f"Failed to initialize TinEyeProvider: {e}")
            
    if not providers:
        logging.warning("No reverse image search providers are configured! Please configure API keys in .env.")
        
    return providers
