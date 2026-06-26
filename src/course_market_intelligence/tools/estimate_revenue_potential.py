"""Tool: estimate_revenue_potential."""

from __future__ import annotations

from ..analysis.revenue_model import estimate
from ..schemas import (
    CompetitorCourse,
    JobMarketSignals,
    Keyword,
    TrendSignals,
)
from ._util import dump


def estimate_revenue_potential(
    topic: str,
    competitor_courses: list[dict] | None = None,
    keyword_metrics: list[dict] | None = None,
    trend_signals: dict | None = None,
    job_market_signals: dict | None = None,
    target_platforms: list[str] | None = None,
    pricing_strategy: str = "mixed",
    target_regions: list[str] | None = None,
) -> dict:
    """Estimate rough 12-month revenue scenarios (explicitly modelled estimates)."""
    courses = [CompetitorCourse(**c) if not isinstance(c, CompetitorCourse) else c
               for c in (competitor_courses or [])]
    keywords = [Keyword(**k) if not isinstance(k, Keyword) else k
                for k in (keyword_metrics or [])]
    trends = (TrendSignals(**trend_signals) if trend_signals
              and not isinstance(trend_signals, TrendSignals)
              else (trend_signals or TrendSignals(topic=topic)))
    jobs = (JobMarketSignals(**job_market_signals) if job_market_signals
            and not isinstance(job_market_signals, JobMarketSignals)
            else (job_market_signals or JobMarketSignals()))

    result = estimate(
        topic=topic,
        competitor_courses=courses,
        keywords=keywords,
        trends=trends,
        jobs=jobs,
        target_platforms=target_platforms,
        pricing_strategy=pricing_strategy,
        target_regions=target_regions,
    )
    return dump(result)
