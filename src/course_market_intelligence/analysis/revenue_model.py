"""Revenue scenario modelling.

Produces low/base/high 12-month scenarios from transparent assumptions. Never
claims exact competitor revenue; everything here is an explicitly-labelled
estimate driven by configurable assumptions.
"""

from __future__ import annotations

import statistics

from ..schemas import (
    Bucket,
    CompetitorCourse,
    Confidence,
    JobMarketSignals,
    Keyword,
    RevenueEstimate,
    RevenueScenario,
    TrendSignals,
)

# Default marketplace assumptions (Udemy-style realized prices are far below list)
_UDEMY_REALIZED_FACTOR = 0.18  # heavy discounting on marketplace
_UDEMY_INSTRUCTOR_SHARE = 0.50  # blended organic/promo share approximation


def estimate(
    topic: str,
    competitor_courses: list[CompetitorCourse],
    keywords: list[Keyword],
    trends: TrendSignals,
    jobs: JobMarketSignals,
    target_platforms: list[str] | None = None,
    pricing_strategy: str = "mixed",
    target_regions: list[str] | None = None,
) -> RevenueEstimate:
    target_platforms = target_platforms or ["Udemy", "Coursera", "LinkedIn Learning", "Go1"]

    list_price = _recommend_list_price(competitor_courses)
    realized = round(list_price * _UDEMY_REALIZED_FACTOR, 2)

    demand_multiplier = _demand_multiplier(keywords, trends, jobs)
    base_enrollments = int(400 * demand_multiplier)

    scenarios = {
        "low": _scenario("low", int(base_enrollments * 0.4), realized,
                         b2b_deals=_b2b_deals(jobs, "low"),
                         strategy=pricing_strategy),
        "base": _scenario("base", base_enrollments, realized,
                          b2b_deals=_b2b_deals(jobs, "base"),
                          strategy=pricing_strategy),
        "high": _scenario("high", int(base_enrollments * 2.2), round(realized * 1.15, 2),
                          b2b_deals=_b2b_deals(jobs, "high"),
                          strategy=pricing_strategy),
    }

    confidence = (
        Confidence.medium
        if competitor_courses and (keywords or jobs.skill_frequency)
        else Confidence.low
    )

    return RevenueEstimate(
        recommended_udemy_list_price=list_price,
        expected_realized_udemy_price=realized,
        recommended_b2b_licensing_band=_b2b_band(jobs),
        recommended_subscription_model=(
            "Revenue-share on Coursera/LinkedIn Learning/Go1 catalogs; "
            "negotiate per-seat or per-catalog licensing for B2B."
        ),
        scenarios=scenarios,
        enrollment_assumptions=[
            f"Base ~{base_enrollments} paid enrollments in 12 months (demand multiplier {demand_multiplier:.2f}).",
            "Marketplace organic discovery + light paid promotion assumed.",
        ],
        traffic_assumptions=[
            "Search/marketplace impressions scale with keyword volume buckets.",
            "No guaranteed external ad budget modelled in the base case.",
        ],
        conversion_assumptions=[
            "Marketplace landing-page conversion 1-4% depending on rating ramp.",
        ],
        rating_review_assumptions=[
            "Course reaches 4.4+ rating within 3 months given gap-driven quality.",
        ],
        promotion_assumptions=[
            "Participates in marketplace-wide promotions (realized price << list price).",
        ],
        b2b_deal_assumptions=[
            f"B2B licensing band: {_b2b_band(jobs)}.",
            "High case assumes 2-6 corporate/team deals.",
        ],
        marketplace_risk_factors=[
            "Marketplace discounting compresses per-sale revenue.",
            "Ranking depends on early reviews and velocity.",
            "Platform policy / catalog acceptance is not guaranteed.",
        ],
        sensitivity_analysis=_sensitivity(realized, base_enrollments),
        confidence=confidence,
    )


def _recommend_list_price(courses: list[CompetitorCourse]) -> float:
    prices = []
    for c in courses:
        p = _parse_price(c.price_listed or c.price_observed)
        if p:
            prices.append(p)
    if prices:
        median = statistics.median(prices)
        return round(max(49.99, min(199.99, median)), 2)
    return 129.99


def _parse_price(price: str | None) -> float | None:
    if not price:
        return None
    digits = "".join(ch for ch in str(price) if ch.isdigit() or ch == ".")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _demand_multiplier(keywords: list[Keyword], trends: TrendSignals,
                       jobs: JobMarketSignals) -> float:
    mult = 1.0
    high_vol = sum(1 for k in keywords if k.volume_bucket == Bucket.high)
    mult += min(1.0, high_vol * 0.1)
    if trends.trend_direction.value == "growing":
        mult += 0.4
    elif trends.trend_direction.value == "declining":
        mult -= 0.3
    if jobs.estimated_job_posting_demand_bucket == Bucket.high:
        mult += 0.4
    elif jobs.estimated_job_posting_demand_bucket == Bucket.medium:
        mult += 0.15
    return max(0.3, round(mult, 2))


def _b2b_deals(jobs: JobMarketSignals, case: str) -> int:
    base = {"low": 0, "base": 1, "high": 4}[case]
    if jobs.leadership_fit == Bucket.high or jobs.upskilling_fit == Bucket.high:
        base += {"low": 0, "base": 1, "high": 2}[case]
    return base


def _b2b_band(jobs: JobMarketSignals) -> str:
    if jobs.leadership_fit == Bucket.high or jobs.estimated_job_posting_demand_bucket == Bucket.high:
        return "$3,000-$15,000 per team/seat-bundle license"
    return "$1,500-$8,000 per team license"


def _scenario(name: str, enrollments: int, realized_price: float,
              b2b_deals: int, strategy: str) -> RevenueScenario:
    b2b_value = 6000.0 if "B2B" in strategy or "mixed" in strategy else 0.0
    b2c_revenue = enrollments * realized_price * _UDEMY_INSTRUCTOR_SHARE
    b2b_revenue = b2b_deals * b2b_value
    annual = round(b2c_revenue + b2b_revenue, 2)
    return RevenueScenario(
        name=name,
        enrollments=enrollments,
        realized_price=realized_price,
        b2b_deals=b2b_deals,
        b2b_deal_value=b2b_value,
        annual_revenue=annual,
        assumptions=[
            f"{enrollments} enrollments @ realized ${realized_price} (50% net share)",
            f"{b2b_deals} B2B deal(s) @ ${b2b_value:.0f}",
        ],
    )


def _sensitivity(realized: float, base_enrollments: int) -> list[dict]:
    rows = []
    for conv_factor in (0.5, 1.0, 1.5):
        enr = int(base_enrollments * conv_factor)
        rows.append({
            "enrollment_factor": conv_factor,
            "enrollments": enr,
            "b2c_net_revenue": round(enr * realized * _UDEMY_INSTRUCTOR_SHARE, 2),
        })
    return rows


def revenue_components(
    estimate_obj: RevenueEstimate,
    jobs: JobMarketSignals,
    competition_risk: float,
    demand_score: float,
) -> dict[str, float]:
    """Return 0-100 component scores for the revenue model."""
    base = estimate_obj.scenarios.get("base")
    base_rev = base.annual_revenue if base else 0.0

    marketplace_demand = min(100.0, demand_score)
    b2c_pricing = min(100.0, ((estimate_obj.expected_realized_udemy_price or 0) / 40.0) * 100.0)
    b2b_potential = (
        90.0 if jobs.leadership_fit == Bucket.high or jobs.upskilling_fit == Bucket.high
        else 60.0 if jobs.upskilling_fit == Bucket.medium else 35.0
    )
    expected_conversion = min(100.0, 40.0 + (base_rev / 5000.0))
    repeat_team = b2b_potential * 0.8
    competition_adjusted = max(0.0, 100.0 - competition_risk)

    return {
        "marketplace_demand": marketplace_demand,
        "b2c_pricing_potential": b2c_pricing,
        "b2b_licensing_potential": b2b_potential,
        "expected_conversion": expected_conversion,
        "repeat_team_purchase_potential": repeat_team,
        "competition_adjusted_upside": competition_adjusted,
    }
