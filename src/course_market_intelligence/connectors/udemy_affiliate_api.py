"""Udemy Affiliate API connector — official/affiliate API only.

Collects public course metadata (title, price, rating, reviews, etc.) through
the authorized affiliate API. Does not fetch any paid course content.
"""

from __future__ import annotations

import base64

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://www.udemy.com/api-2.0/courses/"


async def search_courses(query: str, page_size: int = 20) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("udemy_client_id", "udemy_client_secret"):
        return ConnectorResult.skipped(
            "udemy", "UDEMY_CLIENT_ID / UDEMY_CLIENT_SECRET not set. Use manual CSV import.",
            source_type="affiliate_api",
        )
    token = base64.b64encode(
        f"{settings.udemy_client_id}:{settings.udemy_client_secret}".encode()
    ).decode()
    headers = {"Authorization": f"Basic {token}", "Accept": "application/json, text/plain, */*"}
    params = {
        "search": query,
        "page_size": min(100, page_size),
        "fields[course]": (
            "title,url,price,rating,num_reviews,num_subscribers,"
            "num_lectures,content_info,instructional_level,visible_instructors,headline"
        ),
    }
    try:
        resp = await guarded_get(_ENDPOINT, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("udemy", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("udemy", f"request failed: {exc}")

    items = []
    for c in payload.get("results", []):
        instructors = c.get("visible_instructors") or []
        items.append({
            "platform": "Udemy",
            "course_title": c.get("title"),
            "provider_or_instructor": instructors[0].get("title") if instructors else None,
            "url": f"https://www.udemy.com{c.get('url')}" if c.get("url") else None,
            "rating": c.get("rating"),
            "review_count": c.get("num_reviews"),
            "enrollment_count": c.get("num_subscribers"),
            "number_of_lectures": c.get("num_lectures"),
            "price_listed": c.get("price"),
            "level": (c.get("instructional_level") or "unknown").split()[0].lower()
            if c.get("instructional_level") else "unknown",
            "duration_hours": _content_hours(c.get("content_info")),
            "source_type": "official_api",
        })
    return ConnectorResult.ok("udemy", items, confidence="high", source_type="official_api")


def _content_hours(content_info: str | None) -> float | None:
    if not content_info:
        return None
    # e.g. "12.5 total hours"
    digits = "".join(ch for ch in content_info.split("hour")[0] if ch.isdigit() or ch == ".")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None
