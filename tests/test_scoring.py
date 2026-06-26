"""Tests for the scoring model and decision rules."""

from __future__ import annotations

from course_market_intelligence.analysis import scoring
from course_market_intelligence.schemas import Confidence, GoNoGo


def test_demand_score_bounds():
    comps = {k: 100.0 for k in scoring.DEMAND_WEIGHTS}
    assert scoring.score_demand(comps).score == 100.0
    comps0 = {k: 0.0 for k in scoring.DEMAND_WEIGHTS}
    assert scoring.score_demand(comps0).score == 0.0


def test_weights_sum_to_one():
    for table in (scoring.DEMAND_WEIGHTS, scoring.COMPETITION_WEIGHTS,
                  scoring.GAP_WEIGHTS, scoring.REVENUE_WEIGHTS, scoring.OVERALL_WEIGHTS):
        assert abs(sum(table.values()) - 1.0) < 1e-9


def test_overall_uses_inverse_competition():
    high = scoring.score_overall(demand=80, gap=80, revenue=80, competition_risk=10)
    low = scoring.score_overall(demand=80, gap=80, revenue=80, competition_risk=90)
    assert high.score > low.score


def test_decide_strong_go():
    verdict = scoring.decide(demand=80, gap=75, revenue=65,
                             competition_risk=40, confidence=Confidence.high)
    assert verdict == GoNoGo.strong_go


def test_decide_no_go():
    verdict = scoring.decide(demand=20, gap=20, revenue=20,
                             competition_risk=85, confidence=Confidence.high)
    assert verdict == GoNoGo.no_go


def test_low_confidence_forces_hold():
    verdict = scoring.decide(demand=60, gap=55, revenue=55,
                             competition_risk=40, confidence=Confidence.low)
    assert verdict == GoNoGo.hold_research_more


def test_assess_confidence_levels():
    assert scoring.assess_confidence([Confidence.high, Confidence.high]) == Confidence.high
    assert scoring.assess_confidence([Confidence.low, Confidence.low]) == Confidence.low


def test_build_bundle_returns_all_scores():
    bundle = scoring.build_bundle(
        {k: 70 for k in scoring.DEMAND_WEIGHTS},
        {k: 30 for k in scoring.COMPETITION_WEIGHTS},
        {k: 65 for k in scoring.GAP_WEIGHTS},
        {k: 60 for k in scoring.REVENUE_WEIGHTS},
        [Confidence.high, Confidence.medium],
    )
    assert 0 <= bundle.overall.score <= 100
    assert isinstance(bundle.go_no_go, GoNoGo)
