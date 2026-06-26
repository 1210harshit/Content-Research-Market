"""Coursera connector — partner/official API only.

Coursera restricts scraping/data extraction without prior written consent, so
this connector ONLY operates through an authorized partner API key. Without it,
the caller is told to use search API or a manual CSV export.
"""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://api.coursera.org/api/courses.v1"


async def search_courses(query: str, limit: int = 20) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("coursera_api_key"):
        return ConnectorResult.skipped(
            "coursera",
            "COURSERA_API_KEY (partner-approved) not set. "
            "Use search_api or manual_csv; public scraping is disallowed without written consent.",
            source_type="official_api",
        )
    headers = {"Authorization": f"Bearer {settings.coursera_api_key}"}
    params = {"q": "search", "query": query, "limit": limit,
              "fields": "name,slug,partnerIds,workload,description"}
    try:
        resp = await guarded_get(_ENDPOINT, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("coursera", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("coursera", f"request failed: {exc}")

    items = []
    for c in payload.get("elements", []) or []:
        slug = c.get("slug")
        items.append({
            "platform": "Coursera",
            "course_title": c.get("name"),
            "url": f"https://www.coursera.org/learn/{slug}" if slug else None,
            "duration_hours": None,
            "certificate": "yes",
            "source_type": "official_api",
        })
    return ConnectorResult.ok("coursera", items, confidence="high", source_type="official_api")
