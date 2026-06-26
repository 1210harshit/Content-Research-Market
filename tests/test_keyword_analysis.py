"""Tests for keyword generation and scoring."""

from __future__ import annotations

from course_market_intelligence.analysis.keyword_analysis import (
    apply_seo_metrics,
    generate_keywords,
    keyword_demand_component,
)
from course_market_intelligence.schemas import Bucket, Confidence, SeoMetric


def test_generate_keywords_respects_limit():
    kws = generate_keywords("python", max_keywords=10)
    assert len(kws) == 10
    assert all(k.keyword for k in kws)


def test_generate_keywords_includes_topic():
    kws = generate_keywords("data science", max_keywords=30)
    joined = " ".join(k.keyword for k in kws)
    assert "data science" in joined


def test_ai_angle_toggle_excludes_ai_terms():
    kws = generate_keywords("excel", max_keywords=40, include_ai_angle=False)
    assert all("ai" not in k.keyword.split() for k in kws)


def test_apply_seo_metrics_overlays_buckets():
    kws = generate_keywords("sql", max_keywords=20)
    target = kws[0].keyword
    metrics = [SeoMetric(keyword=target, monthly_search_volume=15000,
                         volume_bucket=Bucket.high, keyword_difficulty=70,
                         confidence=Confidence.high)]
    apply_seo_metrics(kws, metrics)
    overlaid = next(k for k in kws if k.keyword == target)
    assert overlaid.volume_bucket == Bucket.high
    assert overlaid.difficulty_bucket == Bucket.high
    assert overlaid.confidence == Confidence.high


def test_keyword_demand_component_range():
    kws = generate_keywords("kubernetes", max_keywords=25)
    score = keyword_demand_component(kws)
    assert 0 <= score <= 100


def test_keyword_demand_empty():
    assert keyword_demand_component([]) == 0.0
