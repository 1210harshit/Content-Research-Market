"""Tool: design_course_blueprint."""

from __future__ import annotations

from ..analysis.curriculum_design import design_blueprint
from ..schemas import CompetitionAnalysis, MarketGap
from ._util import dump


def design_course_blueprint(
    topic: str,
    target_learner: str = "",
    goal: str = "",
    market_gaps: list[dict] | None = None,
    job_market_skills: list[str] | None = None,
    competitor_analysis: dict | None = None,
    preferred_duration: str = "auto",
) -> dict:
    """Create a market-backed course outline."""
    gaps = [MarketGap(**g) if not isinstance(g, MarketGap) else g
            for g in (market_gaps or [])]
    comp = CompetitionAnalysis(**(competitor_analysis or {})) if not isinstance(competitor_analysis, CompetitionAnalysis) else competitor_analysis

    blueprint = design_blueprint(
        topic=topic,
        target_learner=target_learner,
        goal=goal,
        market_gaps=gaps,
        job_skills=job_market_skills or [],
        competition=comp,
        preferred_duration=preferred_duration,
    )
    return dump(blueprint)
