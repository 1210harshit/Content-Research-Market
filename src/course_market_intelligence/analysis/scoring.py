"""Transparent 0-100 scoring model.

Weights are defined exactly as specified in the product brief. Every score
returns a :class:`ScoreBreakdown` that exposes its weighted components and a
short rationale so the report can show *why* a number is what it is.
"""

from __future__ import annotations

from ..schemas import (
    Confidence,
    GoNoGo,
    ScoreBreakdown,
    ScoreBundle,
)

# --------------------------------------------------------------------------- #
# Weight tables                                                                #
# --------------------------------------------------------------------------- #
DEMAND_WEIGHTS = {
    "keyword_search_demand": 0.25,
    "trend_growth": 0.20,
    "job_market_relevance": 0.20,
    "competitor_proof_of_demand": 0.15,
    "b2b_corporate_relevance": 0.10,
    "timing_seasonality": 0.10,
}

COMPETITION_WEIGHTS = {
    "strong_competitors": 0.25,
    "review_enrollment_concentration": 0.20,
    "brand_strength": 0.20,
    "content_saturation": 0.20,
    "differentiation_difficulty": 0.15,
}

GAP_WEIGHTS = {
    "missing_high_value_subtopics": 0.25,
    "missing_job_market_skills": 0.20,
    "missing_ai_tooling_workflows": 0.15,
    "missing_projects_practice": 0.15,
    "regional_b2b_gaps": 0.15,
    "competitor_freshness_gaps": 0.10,
}

REVENUE_WEIGHTS = {
    "marketplace_demand": 0.25,
    "b2c_pricing_potential": 0.15,
    "b2b_licensing_potential": 0.25,
    "expected_conversion": 0.15,
    "repeat_team_purchase_potential": 0.10,
    "competition_adjusted_upside": 0.10,
}

OVERALL_WEIGHTS = {
    "demand": 0.35,
    "gap": 0.25,
    "revenue": 0.25,
    "inverse_competition_risk": 0.15,
}


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


def _weighted(components: dict[str, float], weights: dict[str, float]) -> float:
    total = 0.0
    for key, weight in weights.items():
        total += _clamp(components.get(key, 0.0)) * weight
    return round(_clamp(total), 1)


def score_demand(components: dict[str, float]) -> ScoreBreakdown:
    score = _weighted(components, DEMAND_WEIGHTS)
    rationale = _top_drivers(components, DEMAND_WEIGHTS)
    return ScoreBreakdown(score=score, components=_applied(components, DEMAND_WEIGHTS),
                          rationale=rationale)


def score_competition_risk(components: dict[str, float]) -> ScoreBreakdown:
    """Higher = MORE competition risk (worse)."""
    score = _weighted(components, COMPETITION_WEIGHTS)
    rationale = _top_drivers(components, COMPETITION_WEIGHTS)
    return ScoreBreakdown(score=score, components=_applied(components, COMPETITION_WEIGHTS),
                          rationale=rationale)


def score_gap(components: dict[str, float]) -> ScoreBreakdown:
    score = _weighted(components, GAP_WEIGHTS)
    rationale = _top_drivers(components, GAP_WEIGHTS)
    return ScoreBreakdown(score=score, components=_applied(components, GAP_WEIGHTS),
                          rationale=rationale)


def score_revenue(components: dict[str, float]) -> ScoreBreakdown:
    score = _weighted(components, REVENUE_WEIGHTS)
    rationale = _top_drivers(components, REVENUE_WEIGHTS)
    return ScoreBreakdown(score=score, components=_applied(components, REVENUE_WEIGHTS),
                          rationale=rationale)


def score_overall(demand: float, gap: float, revenue: float,
                  competition_risk: float) -> ScoreBreakdown:
    inverse_competition = _clamp(100.0 - competition_risk)
    components = {
        "demand": demand,
        "gap": gap,
        "revenue": revenue,
        "inverse_competition_risk": inverse_competition,
    }
    score = _weighted(components, OVERALL_WEIGHTS)
    return ScoreBreakdown(
        score=score,
        components=_applied(components, OVERALL_WEIGHTS),
        rationale=[
            f"Demand {demand} (35%), gap {gap} (25%), revenue {revenue} (25%), "
            f"inverse competition risk {inverse_competition} (15%)."
        ],
    )


def _applied(components: dict[str, float], weights: dict[str, float]) -> dict[str, float]:
    return {k: round(_clamp(components.get(k, 0.0)) * w, 2) for k, w in weights.items()}


def _top_drivers(components: dict[str, float], weights: dict[str, float], n: int = 3) -> list[str]:
    contributions = sorted(
        ((k, _clamp(components.get(k, 0.0)) * w) for k, w in weights.items()),
        key=lambda kv: kv[1],
        reverse=True,
    )
    out = []
    for key, contrib in contributions[:n]:
        out.append(f"{key.replace('_', ' ')} contributes {round(contrib, 1)} pts")
    return out


# --------------------------------------------------------------------------- #
# Decision rules                                                               #
# --------------------------------------------------------------------------- #
def decide(
    demand: float,
    gap: float,
    revenue: float,
    competition_risk: float,
    confidence: Confidence,
) -> GoNoGo:
    """Apply the documented decision rules."""
    if confidence == Confidence.low:
        # Low confidence overrides optimism unless signals are overwhelmingly strong.
        if not (demand >= 75 and gap >= 70 and revenue >= 60):
            return GoNoGo.hold_research_more

    demand_high = demand >= 65
    demand_med = demand >= 45
    gap_high = gap >= 60
    revenue_ok = revenue >= 50
    competition_manageable = competition_risk <= 65

    if demand_high and gap_high and revenue_ok and competition_manageable:
        return GoNoGo.strong_go
    if demand_med and (gap >= 45 or competition_manageable):
        return GoNoGo.conditional_go
    if demand < 40 and revenue < 45 and competition_risk >= 60 and gap < 45:
        return GoNoGo.no_go
    return GoNoGo.conditional_go


def assess_confidence(data_confidences: list[Confidence]) -> Confidence:
    """Aggregate per-signal confidences into an overall confidence label."""
    if not data_confidences:
        return Confidence.low
    weights = {Confidence.high: 1.0, Confidence.medium: 0.6, Confidence.low: 0.25}
    avg = sum(weights[c] for c in data_confidences) / len(data_confidences)
    n_high = sum(1 for c in data_confidences if c == Confidence.high)
    if avg >= 0.75 and n_high >= max(1, len(data_confidences) // 2):
        return Confidence.high
    if avg >= 0.45:
        return Confidence.medium
    return Confidence.low


def build_bundle(
    demand_components: dict[str, float],
    competition_components: dict[str, float],
    gap_components: dict[str, float],
    revenue_components: dict[str, float],
    data_confidences: list[Confidence],
) -> ScoreBundle:
    demand = score_demand(demand_components)
    competition = score_competition_risk(competition_components)
    gap = score_gap(gap_components)
    revenue = score_revenue(revenue_components)
    overall = score_overall(demand.score, gap.score, revenue.score, competition.score)
    confidence = assess_confidence(data_confidences)
    verdict = decide(demand.score, gap.score, revenue.score, competition.score, confidence)
    return ScoreBundle(
        demand=demand,
        competition_risk=competition,
        gap=gap,
        revenue=revenue,
        overall=overall,
        go_no_go=verdict,
        confidence=confidence,
    )
