"""Tool: discover_sources."""

from __future__ import annotations

from ..schemas import Bucket, Confidence, DiscoveredSource
from ..source_policy import evaluate
from ._util import dump

# Curated catalog of well-known sources by type. Domains map onto source_policy.
_CATALOG = [
    ("Udemy", "udemy.com", "course_marketplace"),
    ("Coursera", "coursera.org", "course_marketplace"),
    ("LinkedIn Learning", "linkedin.com", "b2b_learning"),
    ("edX", "edx.org", "course_marketplace"),
    ("FutureLearn", "futurelearn.com", "course_marketplace"),
    ("Class Central", "classcentral.com", "course_marketplace"),
    ("Go1", "go1.com", "b2b_learning"),
    ("Edflex", "edflex.com", "b2b_learning"),
    ("YouTube", "youtube.com", "youtube"),
    ("Google Search", "google.com", "news"),
    ("Bing Search", "bing.com", "news"),
    ("Reddit", "reddit.com", "social"),
    ("Quora", "quora.com", "forums"),
    ("Semrush", "semrush.com", "seo"),
    ("Ahrefs", "ahrefs.com", "seo"),
    ("DataForSEO", "dataforseo.com", "seo"),
    ("Exploding Topics", "explodingtopics.com", "trend"),
    ("Google Trends", "trends.google.com", "trend"),
]

_API_KEY_DOMAINS = {
    "udemy.com", "coursera.org", "go1.com", "youtube.com", "google.com",
    "bing.com", "reddit.com", "semrush.com", "ahrefs.com", "dataforseo.com",
}
_MANUAL_CSV_DOMAINS = {"linkedin.com", "coursera.org", "edflex.com"}


def discover_sources(
    topic: str,
    platforms: list[str] | None = None,
    target_regions: list[str] | None = None,
    source_types: list[str] | None = None,
    max_sources: int = 100,
) -> dict:
    """Find relevant online sources for a course topic using known source lists."""
    source_types = source_types or [
        "course_marketplace", "seo", "trend", "job_market", "social",
        "news", "b2b_learning", "youtube", "blogs", "forums",
    ]
    sources: list[DiscoveredSource] = []
    for name, domain, stype in _CATALOG:
        if stype not in source_types:
            continue
        policy = evaluate(domain)
        relevance = Bucket.high if stype in (
            "course_marketplace", "b2b_learning", "youtube"
        ) else Bucket.medium
        sources.append(DiscoveredSource(
            source_name=name,
            domain=domain,
            source_type=stype,
            relevance=relevance,
            allowed_collection_modes=policy.allowed_modes,
            requires_api_key=domain in _API_KEY_DOMAINS,
            requires_manual_csv=domain in _MANUAL_CSV_DOMAINS,
            source_policy_status="allowed" if policy.allowed_modes else "restricted",
            reason_to_use=f"Relevant {stype.replace('_', ' ')} source for '{topic}'.",
            confidence=Confidence.medium,
        ))
        if len(sources) >= max_sources:
            break
    return {
        "topic": topic,
        "count": len(sources),
        "sources": dump(sources),
    }
