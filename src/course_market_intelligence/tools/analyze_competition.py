"""Tool: analyze_competition."""

from __future__ import annotations

from ..analysis.competitor_analysis import analyze
from ..schemas import CompetitorCourse
from ._util import dump


def analyze_competition(courses: list[dict], topic: str = "") -> dict:
    """Analyze the competitor landscape from normalized course records."""
    parsed = [CompetitorCourse(**c) if not isinstance(c, CompetitorCourse) else c
              for c in courses]
    result = analyze(parsed, topic)
    return dump(result)
