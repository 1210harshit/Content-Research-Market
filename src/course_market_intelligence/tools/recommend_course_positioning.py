"""Tool: recommend_course_positioning."""

from __future__ import annotations

from ..analysis.ai_angle import recommend_ai_angle
from ..analysis.curriculum_design import recommend_positioning
from ..schemas import (
    CompetitionAnalysis,
    JobMarketSignals,
    Keyword,
    Level,
    TrendSignals,
)
from ._util import dump


def recommend_course_positioning(
    topic: str,
    working_title: str | None = None,
    target_learner: str = "",
    competition: dict | None = None,
    trends: dict | None = None,
    job_market: dict | None = None,
    keywords: list[dict] | None = None,
    level: str = "beginner",
    include_ai_angle: bool = True,
) -> dict:
    """Create course titles, subtitles, value props and differentiation."""
    comp = CompetitionAnalysis(**(competition or {})) if not isinstance(competition, CompetitionAnalysis) else competition
    trd = TrendSignals(**(trends or {"topic": topic})) if not isinstance(trends, TrendSignals) else trends
    jobs = JobMarketSignals(**(job_market or {})) if not isinstance(job_market, JobMarketSignals) else job_market
    kws = [Keyword(**k) if not isinstance(k, Keyword) else k for k in (keywords or [])]
    lvl = Level(level) if level in Level.__members__ else Level.beginner

    ai = recommend_ai_angle(topic, comp, jobs, trd) if include_ai_angle else {
        "ai_angle_strength": "n/a", "rationale": "AI angle excluded.",
        "recommended_modules": [], "positioning_line": "", "evidence": [],
    }
    positioning = recommend_positioning(
        topic=topic,
        working_title=working_title,
        target_learner=target_learner,
        competition=comp,
        trends=trd,
        ai_angle=ai,
        keywords=kws,
        level=lvl,
    )
    out = dump(positioning)
    out["ai_angle"] = ai
    return out
