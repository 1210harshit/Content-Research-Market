"""Compliant public metadata fetcher.

ONLY fetches a public page after the compliance gate confirms the domain allows
a public-metadata mode AND robots.txt permits it for our user agent. Extracts
lightweight metadata (title, meta description, JSON-LD type) — never paid,
private, or copyrighted body content, and never personal data.
"""

from __future__ import annotations

import re

from ..compliance import USER_AGENT, ComplianceAuditor, evaluate_gate
from ..rate_limit import guarded_get
from .base import ConnectorResult

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
    re.IGNORECASE | re.DOTALL,
)


async def fetch_metadata(url: str, auditor: ComplianceAuditor | None = None) -> ConnectorResult:
    decision = await evaluate_gate(
        url, "public_metadata_if_allowed", auditor=auditor, check_robots_for_public=True
    )
    if not decision.allowed:
        return ConnectorResult.skipped(
            "public_metadata",
            f"Skipped per policy/robots: {decision.reason}",
            source_type="public_page",
        )
    try:
        resp = await guarded_get(url, headers={"User-Agent": USER_AGENT})
        if resp.status_code >= 400:
            return ConnectorResult.error("public_metadata", f"HTTP {resp.status_code}")
        html = resp.text
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("public_metadata", f"request failed: {exc}")

    title_m = _TITLE_RE.search(html)
    desc_m = _META_DESC_RE.search(html)
    item = {
        "url": url,
        "title": title_m.group(1).strip() if title_m else None,
        "description": desc_m.group(1).strip() if desc_m else None,
        "source_type": "public_page",
    }
    return ConnectorResult.ok(
        "public_metadata", [item], confidence="medium", source_type="public_page"
    )
