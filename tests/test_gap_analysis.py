"""Tests for market gap discovery and scoring."""

from __future__ import annotations

from course_market_intelligence.analysis.gap_analysis import find_gaps, gap_components
from course_market_intelligence.schemas import (
    Bucket,
    CompetitionAnalysis,
    JobMarketSignals,
    Keyword,
    TrendDirection,
    TrendSignals,
)


def _fixtures():
    competition = CompetitionAnalysis(
        common_modules=["intro", "basics"],
        common_projects=[],
        outdated_competitor_coverage=["Old Course (last updated 2020)"],
        competition_level=Bucket.medium,
    )
    jobs = JobMarketSignals(
        skill_frequency={"forecasting": 12, "dashboards": 9},
        leadership_fit=Bucket.medium,
        upskilling_fit=Bucket.high,
    )
    trends = TrendSignals(topic="analytics", trend_direction=TrendDirection.growing,
                          emerging_related_terms=["ai analytics"])
    keywords = [Keyword(keyword="analytics course")]
    return competition, jobs, trends, keywords


def test_find_gaps_returns_multiple_types():
    competition, jobs, trends, keywords = _fixtures()
    gaps = find_gaps("analytics", competition, keywords, jobs, trends)
    types = {g.gap_type for g in gaps}
    assert "job_market" in types
    assert "AI" in types
    assert "project" in types


def test_ai_gap_skipped_when_disabled():
    competition, jobs, trends, keywords = _fixtures()
    gaps = find_gaps("analytics", competition, keywords, jobs, trends,
                     include_ai_angle=False)
    assert all(g.gap_type != "AI" for g in gaps)


def test_freshness_gap_detected():
    competition, jobs, trends, keywords = _fixtures()
    gaps = find_gaps("analytics", competition, keywords, jobs, trends)
    assert any(g.gap_type == "freshness" for g in gaps)


def test_gap_components_range():
    competition, jobs, trends, keywords = _fixtures()
    gaps = find_gaps("analytics", competition, keywords, jobs, trends)
    comps = gap_components(gaps)
    assert set(comps).issuperset({
        "missing_high_value_subtopics", "missing_job_market_skills",
        "missing_ai_tooling_workflows", "missing_projects_practice",
        "regional_b2b_gaps", "competitor_freshness_gaps",
    })
    assert all(0 <= v <= 100 for v in comps.values())
