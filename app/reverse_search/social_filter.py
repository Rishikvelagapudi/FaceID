import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

# Regular expressions for identifying actionable, specific social-media evidence posts
PATTERNS = [
    # Instagram Reel / Post
    (
        r"https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)",
        "Instagram",
        "Reel",
        True,
    ),
    (
        r"https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)",
        "Instagram",
        "Post",
        True,
    ),
    (
        r"https?://(?:www\.)?instagram\.com/tv/([A-Za-z0-9_-]+)",
        "Instagram",
        "IGTV",
        True,
    ),
    # X / Twitter Status
    (
        r"https?://(?:www\.)?(?:twitter|x)\.com/[^/]+/status/([0-9]+)",
        "X / Twitter",
        "Status",
        True,
    ),
    # YouTube Video / Short
    (
        r"https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]+)",
        "YouTube",
        "Video",
        True,
    ),
    (
        r"https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)",
        "YouTube",
        "Short",
        True,
    ),
    (
        r"https?://youtu\.be/([A-Za-z0-9_-]+)",
        "YouTube",
        "Video",
        True,
    ),
    # TikTok Video
    (
        r"https?://(?:www\.)?tiktok\.com/@[^/]+/video/([0-9]+)",
        "TikTok",
        "Video",
        True,
    ),
    # Reddit Comment / Post
    (
        r"https?://(?:www\.)?reddit\.com/r/[^/]+/comments/([A-Za-z0-9]+)",
        "Reddit",
        "Post",
        True,
    ),
    # Facebook Post / Video
    (
        r"https?://(?:www\.)?facebook\.com/[^/]+/posts/([0-9]+)",
        "Facebook",
        "Post",
        True,
    ),
    (
        r"https?://(?:www\.)?facebook\.com/watch/\?v=([0-9]+)",
        "Facebook",
        "Video",
        True,
    ),
]

GENERIC_PLATFORM_DOMAINS = {
    "instagram.com": "Instagram",
    "twitter.com": "X / Twitter",
    "x.com": "X / Twitter",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "reddit.com": "Reddit",
    "facebook.com": "Facebook",
    "linkedin.com": "LinkedIn",
    "pinterest.com": "Pinterest",
    "vk.com": "VKontakte",
}

def classify_social_url(url: Optional[str]) -> Dict[str, Any]:
    """
    Classify whether a link is a specific, actionable social-media post
    or a generic aggregator/portal link.
    """
    if not url:
        return {
            "platform": "Unknown",
            "is_specific_post": False,
            "post_type": None,
            "post_id": None,
            "trust_score": 0.0,
        }

    for regex, platform, post_type, is_specific in PATTERNS:
        match = re.search(regex, url, re.IGNORECASE)
        if match:
            post_id = match.group(1) if match.groups() else None
            return {
                "platform": platform,
                "is_specific_post": True,
                "post_type": post_type,
                "post_id": post_id,
                "trust_score": 0.95,
            }

    # If not a specific post pattern, check if it's still a social media domain
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]

    for known_domain, platform in GENERIC_PLATFORM_DOMAINS.items():
        if domain == known_domain or domain.endswith("." + known_domain):
            return {
                "platform": platform,
                "is_specific_post": False,
                "post_type": "Generic Portal / Aggregator",
                "post_id": None,
                "trust_score": 0.50,
            }

    return {
        "platform": domain or "Web",
        "is_specific_post": False,
        "post_type": "Web Article / Forum",
        "post_id": None,
        "trust_score": 0.35,
    }

def annotate_trust_signals(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Annotate trust signals such as video detection, content corroboration,
    and specific social media classification.
    """
    link = item.get("link") or item.get("source_url") or ""
    classification = classify_social_url(link)

    # Detect video signal based on post type or title
    title = (item.get("title") or "").lower()
    is_video = (
        classification.get("post_type") in ("Reel", "Video", "Short", "IGTV")
        or "video" in title
        or "watch" in title
        or "reel" in title
    )

    return {
        "platform": classification["platform"],
        "is_specific_post": classification["is_specific_post"],
        "post_type": classification["post_type"],
        "post_id": classification["post_id"],
        "is_video": is_video,
        "trust_score": classification["trust_score"],
    }
