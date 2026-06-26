"""Tests for revenue scenario generation."""

from __future__ import annotations

from course_market_intelligence.analysis.revenue_model import estimate, revenue_components
from course_market_intelligence.schemas import (
    Bucket,
    CompetitorCourse,
    JobMarketSignals,
    Keyword,
    TrendDirection,
    TrendSignals,
)


def _inputs():
    courses = [
        CompetitorCourse(platform="Udemy", course_title="A", price_listed="$129.99",
                         review_count=2000, rating=4.6),
        CompetitorCourse(platform="Udemy", course_title="B", price_listed="$94.99",
                         review_count=800, rating=4.4),
    ]
    keywords = [Keyword(keyword="x", volume_bucket=Bucket.high) for _ in range(3)]
    trends = TrendSignals(topic="x", trend_direction=TrendDirection.growing)
    jobs = JobMarketSignals(estimated_job_posting_demand_bucket=Bucket.high,
                            upskilling_fit=Bucket.high, leadership_fit=Bucket.medium)
    return courses, keywords, trends, jobs


def test_three_scenarios_generated():
    courses, keywords, trends, jobs = _inputs()
    est = estimate("x", courses, keywords, trends, jobs)
    assert set(est.scenarios) == {"low", "base", "high"}


def test_high_scenario_exceeds_low():
    courses, keywords, trends, jobs = _inputs()
    est = estimate("x", courses, keywords, trends, jobs)
    assert est.scenarios["high"].annual_revenue > est.scenarios["low"].annual_revenue


def test_list_price_within_bounds():
    courses, keywords, trends, jobs = _inputs()
    est = estimate("x", courses, keywords, trends, jobs)
    assert 49.99 <= est.recommended_udemy_list_price <= 199.99


def test_revenue_with_no_competitors_low_confidence():
    _, keywords, trends, jobs = _inputs()
    est = estimate("x", [], keywords, trends, jobs)
    assert est.confidence.value in ("low", "medium")


def test_revenue_components_range():
    courses, keywords, trends, jobs = _inputs()
    est = estimate("x", courses, keywords, trends, jobs)
    comps = revenue_components(est, jobs, competition_risk=40, demand_score=70)
    assert all(0 <= v <= 100 for v in comps.values())
