"""Trend signal interpretation and the demand sub-scores derived from trends."""

from __future__ import annotations

from ..schemas import Confidence, TrendDirection, TrendSignals


def summarize_trends(
    topic: str,
    raw_signals: list[dict] | None = None,
) -> TrendSignals:
    """Combine provider trend payloads into a single TrendSignals object.

    Each raw signal may contain: direction, growth_rate, seasonality,
    spikes, emerging_terms, declining_terms, source, confidence.
    Without providers, returns an explicitly low-confidence 'unknown' result.
    """
    raw_signals = raw_signals or []
    if not raw_signals:
        return TrendSignals(
            topic=topic,
            trend_direction=TrendDirection.unknown,
            growth_rate_estimate="unknown (no trend provider configured)",
            confidence=Confidence.low,
            sources=[],
            promotional_angles=_default_promo_angles(topic),
        )

    directions = [s.get("direction") for s in raw_signals if s.get("direction")]
    direction = _majority_direction(directions)
    emerging: list[str] = []
    declining: list[str] = []
    spikes: list[str] = []
    sources: list[str] = []
    for s in raw_signals:
        emerging += s.get("emerging_terms", []) or []
        declining += s.get("declining_terms", []) or []
        spikes += s.get("spikes", []) or []
        if s.get("source"):
            sources.append(s["source"])

    confidence = _aggregate_confidence(raw_signals)
    return TrendSignals(
        topic=topic,
        trend_direction=direction,
        growth_rate_estimate=_first(raw_signals, "growth_rate") or "unknown",
        seasonality=_first(raw_signals, "seasonality"),
        recent_spikes=_dedup(spikes),
        emerging_related_terms=_dedup(emerging),
        declining_related_terms=_dedup(declining),
        best_launch_window=_first(raw_signals, "best_launch_window"),
        promotional_angles=_default_promo_angles(topic),
        confidence=confidence,
        sources=_dedup(sources),
    )


def _majority_direction(directions: list[str]) -> TrendDirection:
    if not directions:
        return TrendDirection.unknown
    counts: dict[str, int] = {}
    for d in directions:
        counts[d] = counts.get(d, 0) + 1
    best = max(counts, key=lambda k: counts[k])
    try:
        return TrendDirection(best)
    except ValueError:
        return TrendDirection.unknown


def _aggregate_confidence(raw_signals: list[dict]) -> Confidence:
    confs = [s.get("confidence", "low") for s in raw_signals]
    if any(c == "high" for c in confs) and len(raw_signals) >= 2:
        return Confidence.high
    if any(c in ("high", "medium") for c in confs):
        return Confidence.medium
    return Confidence.low


def _first(raw_signals: list[dict], key: str):
    for s in raw_signals:
        if s.get(key):
            return s[key]
    return None


def _dedup(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for i in items:
        k = i.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(i.strip())
    return out


def _default_promo_angles(topic: str) -> list[str]:
    return [
        f"Position {topic} as a job-ready, project-based skill.",
        f"Bundle an AI-assisted workflow angle into {topic}.",
        "Run a New Year / new-quarter upskilling campaign.",
        "Offer a B2B team-licensing tier for corporate L&D buyers.",
    ]


def trend_growth_component(trends: TrendSignals) -> float:
    """0-100 contribution of trend direction to demand score."""
    base = {
        TrendDirection.growing: 90.0,
        TrendDirection.flat: 55.0,
        TrendDirection.declining: 20.0,
        TrendDirection.unknown: 45.0,
    }[trends.trend_direction]
    if trends.emerging_related_terms:
        base = min(100.0, base + 5.0)
    return base


def timing_component(trends: TrendSignals) -> float:
    if trends.best_launch_window:
        return 75.0
    if trends.seasonality:
        return 60.0
    return 50.0
