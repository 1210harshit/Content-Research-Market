"""Tool: discover_keywords."""

from __future__ import annotations

from ..analysis.keyword_analysis import generate_keywords
from ._util import dump


def discover_keywords(
    topic: str,
    goal: str = "",
    target_learner: str = "",
    target_regions: list[str] | None = None,
    platforms: list[str] | None = None,
    max_keywords: int = 50,
    include_ai_angle: bool = True,
) -> dict:
    """Generate high-intent keywords and search phrases learners might use."""
    keywords = generate_keywords(
        topic=topic,
        goal=goal,
        target_learner=target_learner,
        platforms=platforms,
        max_keywords=max_keywords,
        include_ai_angle=include_ai_angle,
    )
    return {
        "topic": topic,
        "regions": target_regions or ["US", "UK", "EMEA"],
        "count": len(keywords),
        "keywords": dump(keywords),
        "note": (
            "Volume/difficulty/trend are estimated buckets unless overlaid with "
            "collect_seo_metrics or a manual SEO export."
        ),
    }
