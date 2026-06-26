"""Tool: collect_seo_metrics."""

from __future__ import annotations

from ..connectors import ahrefs, dataforseo, semrush
from ..connectors.manual_csv import load_seo_metrics
from ..schemas import Bucket, Confidence, SeoMetric
from ._util import dump

_PROVIDER_FUNCS = {
    "dataforseo": dataforseo.keyword_volumes,
    "semrush": semrush.keyword_overview,
    "ahrefs": ahrefs.keyword_overview,
}


def _bucket(volume: int | None) -> Bucket:
    if volume is None:
        return Bucket.unknown
    if volume >= 10000:
        return Bucket.high
    if volume >= 1000:
        return Bucket.medium
    return Bucket.low


async def collect_seo_metrics(
    keywords: list[str],
    regions: list[str] | None = None,
    providers: list[str] | None = None,
    fallback_to_estimates: bool = True,
    manual_csv_path: str | None = None,
) -> dict:
    """Collect SEO metrics from approved SEO APIs or a manual export."""
    providers = providers or ["dataforseo", "semrush", "ahrefs", "manual_csv"]
    collected: dict[str, SeoMetric] = {}
    used: list[str] = []
    skipped: list[dict] = []

    # 1. Manual CSV takes precedence (highest confidence, user-provided).
    if "manual_csv" in providers and manual_csv_path:
        for m in load_seo_metrics(manual_csv_path):
            m.volume_bucket = _bucket(m.monthly_search_volume)
            collected[m.keyword.lower()] = m
        used.append("manual_csv")

    # 2. API providers.
    for provider in providers:
        func = _PROVIDER_FUNCS.get(provider)
        if not func:
            continue
        result = await func(keywords)
        if result.status != "ok":
            skipped.append({"provider": provider, "reason": result.reason})
            continue
        used.append(provider)
        for row in result.items:
            kw = (row.get("keyword") or "").lower()
            if not kw or kw in collected:
                continue
            vol = row.get("monthly_search_volume")
            collected[kw] = SeoMetric(
                keyword=row.get("keyword"),
                monthly_search_volume=vol,
                volume_bucket=_bucket(vol),
                keyword_difficulty=row.get("keyword_difficulty"),
                cpc=row.get("cpc"),
                competition=str(row.get("competition")) if row.get("competition") is not None else None,
                confidence=Confidence.high,
                source=provider,
            )

    # 3. Estimated fallback for any keyword still missing.
    if fallback_to_estimates:
        for kw in keywords:
            if kw.lower() not in collected:
                collected[kw.lower()] = SeoMetric(
                    keyword=kw,
                    volume_bucket=Bucket.unknown,
                    confidence=Confidence.low,
                    source="estimate",
                )

    metrics = list(collected.values())
    return {
        "providers_used": used,
        "providers_skipped": skipped,
        "count": len(metrics),
        "metrics": dump(metrics),
    }
