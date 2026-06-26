"""Semrush connector — SEO keyword metrics via official API."""

from __future__ import annotations

from ..config import get_settings
from ..rate_limit import guarded_get
from .base import ConnectorResult

_ENDPOINT = "https://api.semrush.com/"


async def keyword_overview(keywords: list[str], database: str = "us") -> ConnectorResult:
    settings = get_settings()
    if not settings.has("semrush_api_key"):
        return ConnectorResult.skipped(
            "semrush", "SEMRUSH_API_KEY not set.", source_type="seo_api"
        )
    items: list[dict] = []
    for kw in keywords:
        params = {
            "type": "phrase_this",
            "key": settings.semrush_api_key,
            "phrase": kw,
            "database": database,
            "export_columns": "Ph,Nq,Cp,Co,Kd",
        }
        try:
            resp = await guarded_get(_ENDPOINT, params=params)
            if resp.status_code >= 400 or resp.text.startswith("ERROR"):
                continue
            lines = resp.text.strip().splitlines()
            if len(lines) < 2:
                continue
            cols = lines[0].split(";")
            vals = lines[1].split(";")
            row = dict(zip(cols, vals, strict=False))
            items.append({
                "keyword": row.get("Keyword", kw),
                "monthly_search_volume": _to_int(row.get("Search Volume")),
                "cpc": _to_float(row.get("CPC")),
                "competition": row.get("Competition"),
                "keyword_difficulty": _to_int(row.get("Keyword Difficulty Index")),
            })
        except Exception:  # noqa: BLE001
            continue
    if not items:
        return ConnectorResult.error("semrush", "No rows returned; check key/quota.")
    return ConnectorResult.ok("semrush", items, confidence="high", source_type="seo_api")


def _to_int(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
