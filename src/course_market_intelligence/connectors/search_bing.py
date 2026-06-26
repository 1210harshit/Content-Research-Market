"""Bing Web Search API connector — compliant search API only."""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"


async def search(query: str, num: int = 10) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("bing_search_api_key"):
        return ConnectorResult.skipped(
            "bing_search", "BING_SEARCH_API_KEY not set.", source_type="search_api"
        )
    headers = {"Ocp-Apim-Subscription-Key": settings.bing_search_api_key}
    params = {"q": query, "count": min(50, num), "responseFilter": "Webpages"}
    try:
        resp = await guarded_get(_ENDPOINT, params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("bing_search", f"request failed: {exc}")

    web = payload.get("webPages", {}).get("value", [])
    items = [
        {
            "title": it.get("name"),
            "url": it.get("url"),
            "snippet": it.get("snippet"),
            "domain": it.get("displayUrl"),
        }
        for it in web
    ]
    return ConnectorResult.ok("bing_search", items, confidence="high", source_type="search_api")
