"""Job-market connector — official/aggregated job API only.

Generic interface for a user-configured jobs API (e.g. an approved aggregator).
Without credentials it returns a skipped result; callers fall back to manual CSV
or estimated job-market signals. No scraping of job boards.
"""

from __future__ import annotations

# Generic endpoint; override JOBS_API_URL in env to point at your provider.
import os

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_DEFAULT_ENDPOINT = os.environ.get("JOBS_API_URL", "https://jobs.example-provider.com/v1/search")


async def search_postings(query: str, location: str = "US", limit: int = 50) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("jobs_api_key"):
        return ConnectorResult.skipped(
            "jobs",
            "JOBS_API_KEY not set. Provide a manual CSV (import_type='job_market_data') "
            "or configure an approved jobs API.",
            source_type="official_api",
        )
    headers = {"Authorization": f"Bearer {settings.jobs_api_key}"}
    params = {"q": query, "location": location, "limit": limit}
    try:
        resp = await guarded_get(_DEFAULT_ENDPOINT, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("jobs", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("jobs", f"request failed: {exc}")

    items = []
    for j in (payload.get("results") or payload.get("jobs") or []):
        items.append({
            "title": j.get("title"),
            "skills": j.get("skills", []),
            "seniority": j.get("seniority") or j.get("level"),
            "industry": j.get("industry"),
            "salary": j.get("salary"),
            "region": j.get("location") or location,
            "source": "jobs_api",
        })
    return ConnectorResult.ok("jobs", items, confidence="high", source_type="official_api")
