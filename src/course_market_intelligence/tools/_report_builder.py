"""Assemble the report context dict and compute scores from collected signals.

This is the glue between the collection tools, the scoring model and the output
writers. It is deliberately pure (no I/O) so it is easy to test.
"""

from __future__ import annotations

from ..analysis import scoring
from ..analysis.competitor_analysis import (
    competition_components,
    competitor_proof_of_demand,
)
from ..analysis.gap_analysis import gap_components
from ..analysis.job_market_analysis import b2b_relevance_component, job_market_component
from ..analysis.keyword_analysis import keyword_demand_component
from ..analysis.revenue_model import revenue_components
from ..analysis.trend_analysis import timing_component, trend_growth_component
from ..schemas import (
    CompetitionAnalysis,
    CompetitorCourse,
    Confidence,
    JobMarketSignals,
    Keyword,
    MarketGap,
    RevenueEstimate,
    TrendSignals,
)
from ._util import utcnow_iso


def _as(model_cls, data):
    if data is None:
        return model_cls() if model_cls is not JobMarketSignals else JobMarketSignals()
    if isinstance(data, model_cls):
        return data
    return model_cls(**data)


def compute_scores(
    keywords: list[Keyword],
    trends: TrendSignals,
    jobs: JobMarketSignals,
    competition: CompetitionAnalysis,
    competitor_courses: list[CompetitorCourse],
    gaps: list[MarketGap],
    revenue: RevenueEstimate,
) -> scoring.ScoreBundle:
    demand_components = {
        "keyword_search_demand": keyword_demand_component(keywords),
        "trend_growth": trend_growth_component(trends),
        "job_market_relevance": job_market_component(jobs),
        "competitor_proof_of_demand": competitor_proof_of_demand(competitor_courses),
        "b2b_corporate_relevance": b2b_relevance_component(jobs),
        "timing_seasonality": timing_component(trends),
    }
    comp_components = competition_components(competition, competitor_courses)
    g_components = gap_components(gaps)

    # Provisional demand/competition needed for revenue components.
    demand_provisional = scoring.score_demand(demand_components).score
    competition_provisional = scoring.score_competition_risk(comp_components).score
    rev_components = revenue_components(
        revenue, jobs, competition_provisional, demand_provisional
    )

    data_confidences = [
        _conf(trends.confidence),
        _conf(jobs.confidence),
        _conf(competition.confidence),
        _conf(revenue.confidence),
    ]
    return scoring.build_bundle(
        demand_components, comp_components, g_components, rev_components, data_confidences
    )


def _conf(c) -> Confidence:
    if isinstance(c, Confidence):
        return c
    try:
        return Confidence(c)
    except (ValueError, TypeError):
        return Confidence.low


def build_context(
    *,
    topic: str,
    working_title: str | None,
    target_learner: str,
    regions: list[str],
    depth: str,
    keywords: list[dict],
    seo_metrics: list[dict],
    trends: dict,
    competitor_courses: list[dict],
    competition: dict,
    jobs: dict,
    social: dict | None,
    gaps: list[dict],
    revenue: dict,
    positioning: dict,
    blueprint: dict,
    ai_angle: dict,
    source_audit: list[dict],
    scores_bundle: scoring.ScoreBundle,
    limitations: list[str],
) -> dict:
    bundle = scores_bundle
    go = bundle.go_no_go.value
    overall = bundle.overall.score

    summary = (
        f"For '{topic}', demand scores {bundle.demand.score}/100, competition risk "
        f"{bundle.competition_risk.score}/100, market gap {bundle.gap.score}/100 and "
        f"revenue potential {bundle.revenue.score}/100, for an overall {overall}/100 "
        f"({go.replace('_', ' ')}, {bundle.confidence.value} confidence)."
    )

    top_opportunities = [g["gap"] for g in gaps if g.get("priority") == "high"][:5] or [
        g["gap"] for g in gaps[:3]
    ]
    top_risks = (competition.get("competitor_strengths", [])[:2]
                 + revenue.get("marketplace_risk_factors", [])[:2]) or [
        "Limited verified data; treat estimates with caution."
    ]

    recommendation_narrative = _narrative(go, topic, bundle)
    next_actions = _next_actions(go, topic, source_audit)

    sources_used = [s for s in source_audit if s.get("decision") == "allowed"]
    sources_skipped = [s for s in source_audit if s.get("decision") == "skipped"]

    return {
        "topic": topic,
        "recommended_title": positioning.get("primary_recommended_title", working_title or topic),
        "target_learner": target_learner or positioning.get("target_learner", ""),
        "depth": depth,
        "regions": regions,
        "generated_at": utcnow_iso(),
        "go_no_go": go,
        "confidence": bundle.confidence.value,
        "summary": summary,
        "scores": {
            "demand": bundle.demand.score,
            "competition_risk": bundle.competition_risk.score,
            "gap": bundle.gap.score,
            "revenue": bundle.revenue.score,
            "overall": overall,
        },
        "scores_rationale": {
            "demand": bundle.demand.rationale,
            "competition_risk": bundle.competition_risk.rationale,
            "gap": bundle.gap.rationale,
            "revenue": bundle.revenue.rationale,
            "overall": bundle.overall.rationale,
        },
        "differentiation": positioning.get("differentiation_strategy", ""),
        "ai_angle_strength": ai_angle.get("ai_angle_strength", "n/a"),
        "ai_angle": ai_angle,
        "top_opportunities": top_opportunities,
        "top_risks": top_risks,
        "keywords": keywords,
        "seo_metrics": seo_metrics,
        "trends": trends,
        "trend_rows": _trend_rows(trends),
        "competitors": competitor_courses,
        "competition": competition,
        "jobs": jobs,
        "job_market_rows": _job_rows(jobs),
        "social": social or {},
        "gaps": gaps,
        "revenue": revenue,
        "revenue_rows": _revenue_rows(revenue),
        "positioning": positioning,
        "blueprint": blueprint,
        "recommendation_narrative": recommendation_narrative,
        "next_actions": next_actions,
        "limitations": limitations,
        "source_audit": source_audit,
        "sources_used": sources_used,
        "sources_skipped": sources_skipped,
    }


def _narrative(go: str, topic: str, bundle: scoring.ScoreBundle) -> str:
    mapping = {
        "strong_go": (
            f"Strong case to build '{topic}': demand and gaps are high while "
            "competition is manageable. Prioritize speed-to-market with the "
            "gap-driven differentiation."
        ),
        "conditional_go": (
            f"'{topic}' is viable but requires clear differentiation. Proceed only "
            "if you commit to the recommended gaps (projects, freshness, AI angle, B2B)."
        ),
        "hold_research_more": (
            f"Signals for '{topic}' are mixed or low-confidence. Add verified data "
            "(API access or manual exports) before committing budget."
        ),
        "no_go": (
            f"Not recommended now: '{topic}' shows weak demand/revenue against strong "
            "competition with no clear gap. Revisit with a narrower niche or angle."
        ),
    }
    return mapping.get(go, "")


def _next_actions(go: str, topic: str, source_audit: list[dict]) -> list[str]:
    actions = []
    skipped = [s for s in source_audit if s.get("decision") == "skipped"]
    if skipped:
        actions.append(
            "Improve confidence by adding the skipped sources via API keys or manual "
            f"CSV exports ({len(skipped)} skipped)."
        )
    if go in ("strong_go", "conditional_go"):
        actions += [
            "Lock the primary title and outline; validate with 3-5 target learners.",
            "Build the capstone project spec first (it drives differentiation).",
            "Prepare a B2B one-pager for corporate L&D outreach.",
        ]
    elif go == "hold_research_more":
        actions += [
            "Pull verified competitor data (Udemy Affiliate API / manual exports).",
            "Obtain SEO volumes for the top 15 keywords.",
        ]
    else:
        actions.append("Explore an adjacent niche or a more specific learner segment.")
    return actions


def _trend_rows(trends: dict) -> list[dict]:
    return [{
        "topic": trends.get("topic"),
        "trend_direction": trends.get("trend_direction"),
        "growth_rate_estimate": trends.get("growth_rate_estimate"),
        "best_launch_window": trends.get("best_launch_window"),
        "confidence": trends.get("confidence"),
        "sources": ", ".join(trends.get("sources", []) or []),
    }]


def _job_rows(jobs: dict) -> list[dict]:
    rows = []
    for role in jobs.get("related_job_titles", []) or []:
        rows.append({"related_job_title": role})
    for skill, freq in (jobs.get("skill_frequency", {}) or {}).items():
        rows.append({"skill": skill, "frequency": freq})
    if not rows:
        rows.append({"note": "No verified job-market data; signals estimated/unavailable."})
    return rows


def _revenue_rows(revenue: dict) -> list[dict]:
    rows = []
    for name, s in (revenue.get("scenarios", {}) or {}).items():
        rows.append({
            "scenario": name,
            "enrollments": s.get("enrollments"),
            "realized_price": s.get("realized_price"),
            "b2b_deals": s.get("b2b_deals"),
            "annual_revenue": s.get("annual_revenue"),
        })
    return rows
