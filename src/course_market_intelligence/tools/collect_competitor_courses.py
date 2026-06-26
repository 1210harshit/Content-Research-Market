"""Tool: collect_competitor_courses."""

from __future__ import annotations

from ..compliance import ComplianceAuditor, evaluate_gate
from ..connectors import (
    coursera_partner_api,
    go1_manual_import,
    search_bing,
    search_google_cse,
    serpapi,
    udemy_affiliate_api,
    youtube_data_api,
)
from ..connectors.manual_csv import load_competitor_courses
from ..schemas import CompetitorCourse, Confidence, Level
from ._util import dump

# Platform -> (domain, preferred official connector or None, official mode)
_PLATFORMS = {
    "Udemy": ("udemy.com", udemy_affiliate_api.search_courses, "affiliate_api"),
    "Coursera": ("coursera.org", coursera_partner_api.search_courses, "official_api"),
    "Go1": ("go1.com", go1_manual_import.search_courses, "official_api"),
    "YouTube": ("youtube.com", youtube_data_api.search_courses, "youtube_data_api"),
    "edX": ("edx.org", None, "search_api"),
    "FutureLearn": ("futurelearn.com", None, "search_api"),
    "Class Central": ("classcentral.com", None, "search_api"),
    "LinkedIn Learning": ("linkedin.com", None, "manual_csv"),
}


async def _search_api_fallback(platform: str, domain: str, query: str, limit: int) -> list[dict]:
    """Use a compliant search API to surface course listings as search results."""
    q = f"{query} {platform} course site:{domain}"
    for conn in (search_google_cse, search_bing, serpapi):
        res = await conn.search(q, num=limit)
        if res.status == "ok" and res.items:
            return [
                {
                    "platform": platform,
                    "course_title": it.get("title"),
                    "url": it.get("url"),
                    "source_type": "search_result",
                }
                for it in res.items
            ]
    return []


async def collect_competitor_courses(
    topic: str,
    keywords: list[str] | None = None,
    platforms: list[str] | None = None,
    max_courses_per_platform: int = 20,
    source_modes: list[str] | None = None,
    manual_csv_paths: dict[str, str] | None = None,
    auditor: ComplianceAuditor | None = None,
) -> dict:
    """Collect competitor course metadata from authorized sources only."""
    platforms = platforms or list(_PLATFORMS.keys())
    source_modes = source_modes or ["official_api", "search_api", "manual_csv"]
    manual_csv_paths = manual_csv_paths or {}
    auditor = auditor or ComplianceAuditor()
    query = (keywords[0] if keywords else topic)

    courses: list[CompetitorCourse] = []
    used: list[str] = []
    skipped: list[dict] = []

    for platform in platforms:
        cfg = _PLATFORMS.get(platform)
        if not cfg:
            continue
        domain, official_func, official_mode = cfg
        got = False

        # 1. Manual CSV (if provided for this platform) — always allowed, highest confidence.
        if platform in manual_csv_paths and "manual_csv" in source_modes:
            decision = await evaluate_gate(domain, "manual_csv", auditor=auditor)
            if decision.allowed:
                for c in load_competitor_courses(manual_csv_paths[platform], platform):
                    courses.append(c)
                used.append(f"{platform}:manual_csv")
                got = True

        # 2. Official / affiliate / partner API.
        if not got and official_func and "official_api" in source_modes:
            decision = await evaluate_gate(domain, official_mode, auditor=auditor)
            if decision.allowed:
                res = await official_func(query, max_courses_per_platform)
                if res.status == "ok" and res.items:
                    for raw in res.items:
                        courses.append(_normalize(raw, platform))
                    used.append(f"{platform}:{res.provider}")
                    got = True
                else:
                    skipped.append({"platform": platform, "mode": official_mode,
                                    "reason": res.reason})
            else:
                skipped.append({"platform": platform, "mode": official_mode,
                                "reason": decision.reason})

        # 3. Search API fallback (metadata via search results only).
        if not got and "search_api" in source_modes:
            decision = await evaluate_gate(domain, "search_api", auditor=auditor)
            if decision.allowed:
                rows = await _search_api_fallback(platform, domain, query,
                                                  max_courses_per_platform)
                if rows:
                    for raw in rows:
                        courses.append(_normalize(raw, platform, Confidence.low))
                    used.append(f"{platform}:search_api")
                    got = True
                else:
                    skipped.append({"platform": platform, "mode": "search_api",
                                    "reason": "No search API configured or no results."})
            else:
                skipped.append({"platform": platform, "mode": "search_api",
                                "reason": decision.reason})

        if not got:
            skipped.append({
                "platform": platform,
                "mode": "all",
                "reason": (
                    f"No compliant data path produced results for {platform}. "
                    "Provide a manual CSV export (import_manual_data) or API credentials."
                ),
            })

    return {
        "topic": topic,
        "count": len(courses),
        "courses": dump(courses),
        "sources_used": used,
        "sources_skipped": skipped,
    }


def _normalize(raw: dict, platform: str, confidence: Confidence | None = None) -> CompetitorCourse:
    level_raw = str(raw.get("level", "unknown")).lower()
    level = level_raw if level_raw in Level.__members__ else "unknown"
    src_type = raw.get("source_type", "search_result")
    conf = confidence or (
        Confidence.high if src_type in ("official_api", "manual_csv") else Confidence.low
    )
    return CompetitorCourse(
        platform=raw.get("platform", platform),
        course_title=raw.get("course_title") or "(untitled)",
        provider_or_instructor=raw.get("provider_or_instructor"),
        url=raw.get("url"),
        rating=raw.get("rating"),
        review_count=raw.get("review_count"),
        enrollment_count=raw.get("enrollment_count"),
        learner_count=raw.get("learner_count"),
        price_listed=str(raw["price_listed"]) if raw.get("price_listed") is not None else None,
        price_observed=str(raw["price_observed"]) if raw.get("price_observed") is not None else None,
        duration_hours=raw.get("duration_hours"),
        number_of_lectures=raw.get("number_of_lectures"),
        level=Level(level),
        language=raw.get("language"),
        last_updated=raw.get("last_updated"),
        skills=raw.get("skills", []) or [],
        modules_or_topics=raw.get("modules_or_topics", []) or [],
        projects=raw.get("projects", []) or [],
        certificate=raw.get("certificate", "unknown"),
        b2b_relevance=raw.get("b2b_relevance", "unknown"),
        source_url=raw.get("url"),
        source_type=src_type,
        data_confidence=conf,
    )
