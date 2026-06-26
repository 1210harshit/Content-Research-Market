"""Google Programmable Search (CSE) connector — compliant search API only."""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


async def search(query: str, num: int = 10) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("google_cse_api_key", "google_cse_engine_id"):
        return ConnectorResult.skipped(
            "google_cse",
            "GOOGLE_CSE_API_KEY / GOOGLE_CSE_ENGINE_ID not set.",
            source_type="search_api",
        )
    params = {
        "key": settings.google_cse_api_key,
        "cx": settings.google_cse_engine_id,
        "q": query,
        "num": min(10, num),
    }
    try:
        resp = await guarded_get(_ENDPOINT, params=params)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("google_cse", f"request failed: {exc}")

    items = [
        {
            "title": it.get("title"),
            "url": it.get("link"),
            "snippet": it.get("snippet"),
            "domain": it.get("displayLink"),
        }
        for it in payload.get("items", [])
    ]
    return ConnectorResult.ok("google_cse", items, confidence="high", source_type="search_api")
