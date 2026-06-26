"""Keyword generation and scoring heuristics.

When no SEO API is configured the system still produces a useful, clearly
*estimated* keyword set generated from the topic, goal and learner profile.
Real API metrics (when available) override the estimated buckets.
"""

from __future__ import annotations

from ..schemas import Bucket, Confidence, Keyword, SeoMetric, TrendDirection

# Modifier families mapped to (intent, funnel_stage, recommended_use)
_MODIFIERS = [
    ("{t} course", "B2C", "comparison", "title"),
    ("{t} tutorial", "B2C", "awareness", "section title"),
    ("{t} for beginners", "B2C", "awareness", "subtitle"),
    ("{t} certification", "certification", "purchase", "title"),
    ("{t} certificate", "certification", "purchase", "landing page"),
    ("learn {t}", "B2C", "awareness", "landing page"),
    ("{t} online course", "B2C", "comparison", "title"),
    ("{t} training", "B2B", "enterprise-buying", "title"),
    ("{t} for professionals", "career", "job-ready", "subtitle"),
    ("advanced {t}", "technical", "comparison", "section title"),
    ("{t} projects", "technical", "job-ready", "section title"),
    ("{t} bootcamp", "career", "purchase", "title"),
    ("{t} masterclass", "B2C", "purchase", "title"),
    ("{t} fundamentals", "academic", "awareness", "section title"),
    ("{t} job ready", "career", "job-ready", "landing page"),
    ("{t} for managers", "executive", "enterprise-buying", "subtitle"),
    ("{t} with ai", "technical", "comparison", "subtitle"),
    ("ai {t}", "technical", "awareness", "title"),
    ("{t} corporate training", "B2B", "enterprise-buying", "ad keyword"),
    ("{t} compliance", "compliance", "enterprise-buying", "section title"),
    ("{t} hands on", "technical", "job-ready", "subtitle"),
    ("{t} interview questions", "career", "job-ready", "section title"),
    ("how to learn {t}", "B2C", "awareness", "landing page"),
    ("best {t} course", "B2C", "comparison", "ad keyword"),
]

_PLATFORM_HINTS = {
    "certification": ["Coursera", "edX", "LinkedIn Learning"],
    "B2B": ["Go1", "LinkedIn Learning", "Coursera"],
    "career": ["Udemy", "Coursera", "LinkedIn Learning"],
    "technical": ["Udemy", "YouTube", "Coursera"],
    "executive": ["LinkedIn Learning", "Coursera", "Go1"],
    "compliance": ["Go1", "LinkedIn Learning"],
    "academic": ["edX", "Coursera", "FutureLearn"],
    "B2C": ["Udemy", "YouTube", "Class Central"],
}


def generate_keywords(
    topic: str,
    goal: str = "",
    target_learner: str = "",
    platforms: list[str] | None = None,
    max_keywords: int = 50,
    include_ai_angle: bool = True,
) -> list[Keyword]:
    topic = topic.strip()
    platforms = platforms or ["Udemy", "Coursera", "LinkedIn Learning", "Go1"]
    out: list[Keyword] = []
    seen: set[str] = set()

    for template, intent, funnel, use in _MODIFIERS:
        if (not include_ai_angle) and ("ai" in template.lower()):
            continue
        kw = template.format(t=topic).lower()
        if kw in seen:
            continue
        seen.add(kw)
        relevance = _PLATFORM_HINTS.get(intent, platforms)
        platform_relevance = [p for p in platforms if p in relevance] or platforms[:2]
        out.append(
            Keyword(
                keyword=kw,
                intent=intent,
                funnel_stage=funnel,
                volume_bucket=_estimate_volume_bucket(kw, topic),
                trend_direction=TrendDirection.unknown,
                difficulty_bucket=_estimate_difficulty(intent),
                platform_relevance=platform_relevance,
                recommended_use=use,
                confidence=Confidence.low,
            )
        )
        if len(out) >= max_keywords:
            break
    return out


def _estimate_volume_bucket(keyword: str, topic: str) -> Bucket:
    # Shorter, head-term keywords tend to have higher volume.
    words = keyword.split()
    if keyword in (f"{topic} course".lower(), f"learn {topic}".lower(), topic.lower()):
        return Bucket.high
    if len(words) <= 3:
        return Bucket.medium
    return Bucket.low


def _estimate_difficulty(intent: str) -> Bucket:
    if intent in ("B2C", "career"):
        return Bucket.high
    if intent in ("certification", "technical"):
        return Bucket.medium
    return Bucket.low


def apply_seo_metrics(keywords: list[Keyword], metrics: list[SeoMetric]) -> list[Keyword]:
    """Overlay real SEO buckets/trend onto generated keywords by exact match."""
    by_kw = {m.keyword.lower(): m for m in metrics}
    for kw in keywords:
        m = by_kw.get(kw.keyword.lower())
        if not m:
            continue
        if m.volume_bucket != Bucket.unknown:
            kw.volume_bucket = m.volume_bucket
        if m.keyword_difficulty is not None:
            kw.difficulty_bucket = (
                Bucket.high if m.keyword_difficulty >= 60
                else Bucket.medium if m.keyword_difficulty >= 35
                else Bucket.low
            )
        if m.confidence in (Confidence.high, Confidence.medium):
            kw.confidence = m.confidence
    return keywords


def keyword_demand_component(keywords: list[Keyword]) -> float:
    """0-100 contribution of keyword set to demand score."""
    if not keywords:
        return 0.0
    bucket_points = {Bucket.high: 100.0, Bucket.medium: 60.0,
                     Bucket.low: 30.0, Bucket.unknown: 40.0}
    avg = sum(bucket_points[k.volume_bucket] for k in keywords) / len(keywords)
    # Reward presence of high-intent career/certification/B2B keywords.
    high_intent = sum(
        1 for k in keywords
        if k.intent in ("career", "certification", "B2B", "executive", "compliance")
    )
    intent_bonus = min(15.0, high_intent * 1.5)
    return min(100.0, avg + intent_bonus)
