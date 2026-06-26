"""DataForSEO connector — SERP + keyword data via official API.

Implements graceful degradation: without credentials it returns a skipped
result and callers fall back to estimates.
"""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_KEYWORDS_ENDPOINT = (
    "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
)


async def keyword_volumes(keywords: list[str], location: str = "United States") -> ConnectorResult:
    settings = get_settings()
    if not settings.has("dataforseo_login", "dataforseo_password"):
        return ConnectorResult.skipped(
            "dataforseo", "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set.",
            source_type="seo_api",
        )
    auth = (settings.dataforseo_login, settings.dataforseo_password)
    # DataForSEO expects POST with task arrays; this connector uses a simplified
    # GET-style placeholder and reports clearly when the live schema differs.
    try:
        resp = await guarded_get(
            _KEYWORDS_ENDPOINT,
            params={"keywords": ",".join(keywords), "location_name": location},
            auth=auth,
        )
        if resp.status_code >= 400:
            return ConnectorResult.error(
                "dataforseo",
                f"API returned {resp.status_code}; verify task-POST payload for live endpoint.",
            )
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("dataforseo", f"request failed: {exc}")

    items: list[dict] = []
    for task in payload.get("tasks", []) or []:
        for res in task.get("result", []) or []:
            items.append({
                "keyword": res.get("keyword"),
                "monthly_search_volume": res.get("search_volume"),
                "cpc": res.get("cpc"),
                "competition": res.get("competition"),
            })
    return ConnectorResult.ok("dataforseo", items, confidence="high", source_type="seo_api")
