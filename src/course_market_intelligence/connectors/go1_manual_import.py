"""Go1 — partner/customer API or manual import.

Prefers approved Go1 partner/customer access. Without an API key it falls back
to the manual CSV/customer-export path; it never scrapes public Go1 pages.
"""

from __future__ import annotations

from pathlib import Path

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult
from .manual_csv import load_competitor_courses

_ENDPOINT = "https://api.go1.com/v3/learning-objects"


async def search_courses(query: str, limit: int = 20) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("go1_api_key"):
        return ConnectorResult.skipped(
            "go1",
            "GO1_API_KEY (partner/customer) not set. Use a customer export / manual CSV.",
            source_type="manual_csv",
        )
    headers = {"Authorization": f"Bearer {settings.go1_api_key}"}
    params = {"title": query, "limit": limit}
    try:
        resp = await guarded_get(_ENDPOINT, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("go1", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("go1", f"request failed: {exc}")

    items = []
    for c in (payload.get("hits") or payload.get("data") or []):
        items.append({
            "platform": "Go1",
            "course_title": c.get("title"),
            "provider_or_instructor": c.get("provider", {}).get("name") if isinstance(c.get("provider"), dict) else c.get("provider"),
            "url": c.get("url"),
            "duration_hours": (c.get("duration") or 0) / 3600 if c.get("duration") else None,
            "b2b_relevance": "high",
            "source_type": "official_api",
        })
    return ConnectorResult.ok("go1", items, confidence="high", source_type="official_api")


def import_export(csv_path: str | Path) -> ConnectorResult:
    try:
        courses = load_competitor_courses(csv_path, default_platform="Go1")
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("go1", f"CSV import failed: {exc}")
    return ConnectorResult.ok("go1", [c.model_dump() for c in courses],
                              confidence="high", source_type="manual_csv")
