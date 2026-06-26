"""Tool: find_market_gaps."""

from __future__ import annotations

from ..analysis.gap_analysis import find_gaps
from ..schemas import (
    CompetitionAnalysis,
    JobMarketSignals,
    Keyword,
    SocialSignals,
    TrendSignals,
)
from ._util import dump


def find_market_gaps(
    topic: str,
    competition: dict,
    keywords: list[dict] | None = None,
    job_market: dict | None = None,
    trends: dict | None = None,
    social: dict | None = None,
    include_ai_angle: bool = True,
    target_regions: list[str] | None = None,
) -> dict:
    """Find valuable missing subtopics and whitespace across signals."""
    comp = CompetitionAnalysis(**competition) if not isinstance(competition, CompetitionAnalysis) else competition
    kws = [Keyword(**k) if not isinstance(k, Keyword) else k for k in (keywords or [])]
    jobs = JobMarketSignals(**(job_market or {})) if not isinstance(job_market, JobMarketSignals) else job_market
    trd = TrendSignals(**(trends or {"topic": topic})) if not isinstance(trends, TrendSignals) else trends
    soc = SocialSignals(**(social or {})) if not isinstance(social, SocialSignals) else social

    gaps = find_gaps(
        topic=topic,
        competition=comp,
        keywords=kws,
        jobs=jobs,
        trends=trd,
        social=soc,
        include_ai_angle=include_ai_angle,
        target_regions=target_regions,
    )
    return {
        "topic": topic,
        "count": len(gaps),
        "gaps": dump(gaps),
    }
