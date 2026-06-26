"""SerpAPI connector — compliant SERP API only."""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://serpapi.com/search"


async def search(query: str, num: int = 10, engine: str = "google") -> ConnectorResult:
    settings = get_settings()
    if not settings.has("serpapi_key"):
        return ConnectorResult.skipped(
            "serpapi", "SERPAPI_KEY not set.", source_type="search_api"
        )
    params = {"api_key": settings.serpapi_key, "q": query, "num": num, "engine": engine}
    try:
        resp = await guarded_get(_ENDPOINT, params=params)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("serpapi", f"request failed: {exc}")

    items = [
        {
            "title": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet"),
            "domain": it.get("displayed_link"),
        }
        for it in payload.get("organic_results", [])
    ]
    related = [q.get("question") for q in payload.get("related_questions", []) if q.get("question")]
    return ConnectorResult.ok(
        "serpapi", items, confidence="high", source_type="search_api",
        data={"related_questions": related},
    )
