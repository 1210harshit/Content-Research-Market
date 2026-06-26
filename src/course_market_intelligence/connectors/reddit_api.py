"""Reddit connector — official API only, for aggregate learner pain points.

Uses Reddit's OAuth API for compliant public discussion search. Collects only
post titles/summaries to surface pain points — never personal data about users.
"""

from __future__ import annotations

import base64

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
_SEARCH_URL = "https://oauth.reddit.com/search"
_USER_AGENT = "course-market-intelligence-mcp/0.1 (compliant aggregate signals)"


async def _get_token() -> str | None:
    settings = get_settings()
    cred = base64.b64encode(
        f"{settings.reddit_client_id}:{settings.reddit_client_secret}".encode()
    ).decode()
    # Application-only OAuth (client credentials). No user login is automated.
    import httpx

    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {cred}", "User-Agent": _USER_AGENT},
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("access_token")


async def search_discussions(query: str, limit: int = 25) -> ConnectorResult:
    settings = get_settings()
    if not settings.has("reddit_client_id", "reddit_client_secret"):
        return ConnectorResult.skipped(
            "reddit", "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set.",
            source_type="official_api",
        )
    token = await _get_token()
    if not token:
        return ConnectorResult.error("reddit", "OAuth token request failed.")
    headers = {"Authorization": f"Bearer {token}", "User-Agent": _USER_AGENT}
    params = {"q": query, "limit": limit, "sort": "relevance", "type": "link"}
    try:
        resp = await guarded_get(_SEARCH_URL, params=params, headers=headers)
        if resp.status_code >= 400:
            return ConnectorResult.error("reddit", f"API returned {resp.status_code}.")
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("reddit", f"request failed: {exc}")

    items = []
    for child in payload.get("data", {}).get("children", []):
        d = child.get("data", {})
        # Title + subreddit only; deliberately no author / personal data.
        items.append({
            "title": d.get("title"),
            "subreddit": d.get("subreddit"),
            "num_comments": d.get("num_comments"),
            "summary": (d.get("selftext") or "")[:200],
        })
    return ConnectorResult.ok("reddit", items, confidence="medium", source_type="official_api")
