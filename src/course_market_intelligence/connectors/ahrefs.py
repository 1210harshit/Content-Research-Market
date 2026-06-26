"""Ahrefs connector — SEO keyword metrics via official API v3."""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://api.ahrefs.com/v3/keywords-explorer/overview"


async def keyword_overview(keywords: list[str], country: str = "us") -> ConnectorResult:
    settings = get_settings()
    if not settings.has("ahrefs_api_key"):
        return ConnectorResult.skipped(
            "ahrefs", "AHREFS_API_KEY not set.", source_type="seo_api"
        )
    headers = {"Authorization": f"Bearer {settings.ahrefs_api_key}"}
    params = {"keywords": ",".join(keywords), "country": country}
    try:
        resp = await guarded_get(_ENDPOINT, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("ahrefs", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("ahrefs", f"request failed: {exc}")

    items = [
        {
            "keyword": row.get("keyword"),
            "monthly_search_volume": row.get("volume"),
            "keyword_difficulty": row.get("difficulty"),
            "cpc": row.get("cpc"),
        }
        for row in payload.get("keywords", []) or []
    ]
    return ConnectorResult.ok("ahrefs", items, confidence="high", source_type="seo_api")
