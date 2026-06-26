"""YouTube Data API connector — official API only (never scraping).

Used for public course/tutorial discovery and aggregate signals. Comments are
NOT collected here; if ever added they must be aggregated/summarized only and
must never store personal data.
"""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_SEARCH = "https://www.googleapis.com/youtube/v3/search"
_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"


async def search_courses(query: str, max_results: int = 15) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("youtube_api_key"):
        return ConnectorResult.skipped(
            "youtube", "YOUTUBE_API_KEY not set.", source_type="official_api"
        )
    params = {
        "key": settings.youtube_api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": min(50, max_results),
        "relevanceLanguage": "en",
    }
    try:
        resp = await guarded_get(_SEARCH, params=params)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("youtube", f"request failed: {exc}")

    items = []
    for it in payload.get("items", []):
        snip = it.get("snippet", {})
        vid = it.get("id", {}).get("videoId")
        items.append({
            "platform": "YouTube",
            "course_title": snip.get("title"),
            "provider_or_instructor": snip.get("channelTitle"),
            "url": f"https://www.youtube.com/watch?v={vid}" if vid else None,
            "last_updated": snip.get("publishedAt"),
            "source_type": "official_api",
        })
    return ConnectorResult.ok("youtube", items, confidence="high", source_type="official_api")
