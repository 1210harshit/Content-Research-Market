"""Tool: research_course_topic — the full market-validation workflow."""

from __future__ import annotations

from ..analysis.ai_angle import recommend_ai_angle
from ..analysis.competitor_analysis import analyze as analyze_competition_fn
from ..analysis.curriculum_design import design_blueprint, recommend_positioning
from ..analysis.gap_analysis import find_gaps
from ..analysis.revenue_model import estimate as estimate_revenue
from ..cache import get_cache
from ..compliance import ComplianceAuditor
from ..schemas import (
    CompetitorCourse,
    JobMarketSignals,
    Keyword,
    Level,
    ResearchTopicInput,
    SocialSignals,
    TrendSignals,
)
from . import _report_builder as rb
from ._util import dump, run_id_for
from .collect_competitor_courses import collect_competitor_courses
from .collect_job_market_signals import collect_job_market_signals
from .collect_seo_metrics import collect_seo_metrics
from .collect_social_signals import collect_social_signals
from .collect_trend_signals import collect_trend_signals
from .discover_keywords import discover_keywords
from .generate_report import generate_report

_DEPTH_LIMITS = {
    "quick": {"keywords": 20, "courses_per_platform": 8, "platforms": 4},
    "standard": {"keywords": 35, "courses_per_platform": 15, "platforms": 6},
    "deep": {"keywords": 50, "courses_per_platform": 20, "platforms": 8},
}


async def research_course_topic(payload: dict) -> dict:
    """Run the full course market validation workflow and produce a report."""
    inp = ResearchTopicInput(**payload)
    depth = inp.depth.value
    limits = _DEPTH_LIMITS[depth]
    auditor = ComplianceAuditor()
    manual = payload.get("manual_data", {}) or {}
    target_learner = inp.target_learners.profile or ""

    # 1. Seed keywords
    kw_out = discover_keywords(
        topic=inp.topic, goal=inp.goal, target_learner=target_learner,
        target_regions=inp.target_regions, platforms=inp.platforms,
        max_keywords=limits["keywords"], include_ai_angle=inp.include_ai_angle,
    )
    keywords = [Keyword(**k) for k in kw_out["keywords"]]
    keyword_strings = [k.keyword for k in keywords][:15]

    # 5. SEO metrics (if seo_api / manual allowed)
    seo_metrics: list[dict] = []
    if any(m in inp.allowed_source_modes for m in ("seo_api", "manual_csv")):
        seo_out = await collect_seo_metrics(
            keywords=keyword_strings, regions=inp.target_regions,
            manual_csv_path=manual.get("seo_metrics"),
        )
        seo_metrics = seo_out["metrics"]

    # 6. Trend signals
    trends_dict = await collect_trend_signals(
        topic=inp.topic, keywords=keyword_strings, regions=inp.target_regions,
        manual_csv_path=manual.get("trend_exports"),
    )
    trends = TrendSignals(**{k: v for k, v in trends_dict.items()
                            if k in TrendSignals.model_fields})

    # 4. Competitor courses
    comp_out = await collect_competitor_courses(
        topic=inp.topic, keywords=keyword_strings,
        platforms=inp.platforms[: limits["platforms"]],
        max_courses_per_platform=limits["courses_per_platform"],
        source_modes=[m for m in inp.allowed_source_modes
                      if m in ("official_api", "search_api", "public_metadata", "manual_csv")],
        manual_csv_paths=manual.get("competitor_courses_by_platform", {}),
        auditor=auditor,
    )
    competitor_courses = [CompetitorCourse(**c) for c in comp_out["courses"]]

    # 7. Job-market signals
    jobs = JobMarketSignals()
    if inp.include_job_market:
        jobs_dict = await collect_job_market_signals(
            topic=inp.topic, keywords=keyword_strings, regions=inp.target_regions,
            target_learner=target_learner,
            source_modes=[m for m in inp.allowed_source_modes
                          if m in ("official_api", "search_api", "manual_csv")],
            manual_csv_path=manual.get("job_market_data"),
        )
        jobs = JobMarketSignals(**{k: v for k, v in jobs_dict.items()
                                  if k in JobMarketSignals.model_fields})

    # 8. Social / learner pain points
    social = SocialSignals()
    if inp.include_social_signals:
        social_dict = await collect_social_signals(
            topic=inp.topic, keywords=keyword_strings,
            source_modes=[m for m in inp.allowed_source_modes
                          if m in ("official_api", "search_api", "manual_csv")],
            manual_reviews_csv=manual.get("course_reviews_summary"),
        )
        social = SocialSignals(**{k: v for k, v in social_dict.items()
                                 if k in SocialSignals.model_fields})

    # 9. Competition analysis
    competition = analyze_competition_fn(competitor_courses, inp.topic)

    # 10/11. Market gaps
    gaps = find_gaps(
        topic=inp.topic, competition=competition, keywords=keywords, jobs=jobs,
        trends=trends, social=social, include_ai_angle=inp.include_ai_angle,
        target_regions=inp.target_regions,
    )

    # AI angle
    ai_angle = (
        recommend_ai_angle(inp.topic, competition, jobs, trends)
        if inp.include_ai_angle else
        {"ai_angle_strength": "n/a", "rationale": "AI angle excluded.",
         "recommended_modules": [], "positioning_line": "", "evidence": []}
    )

    # 12. Revenue
    revenue = estimate_revenue(
        topic=inp.topic, competitor_courses=competitor_courses, keywords=keywords,
        trends=trends, jobs=jobs, target_platforms=inp.platforms,
        pricing_strategy="mixed", target_regions=inp.target_regions,
    ) if inp.include_revenue_model else estimate_revenue(
        inp.topic, [], [], trends, jobs
    )

    # 13. Positioning
    positioning = recommend_positioning(
        topic=inp.topic, working_title=inp.working_title, target_learner=target_learner,
        competition=competition, trends=trends, ai_angle=ai_angle, keywords=keywords,
        level=Level.beginner,
    )

    # 14. Blueprint
    blueprint = (
        design_blueprint(
            topic=inp.topic, target_learner=target_learner, goal=inp.goal,
            market_gaps=gaps, job_skills=list(jobs.skill_frequency.keys()),
            competition=competition, preferred_duration="auto",
        ) if inp.include_curriculum_blueprint else None
    )

    # Scores
    bundle = rb.compute_scores(
        keywords=keywords, trends=trends, jobs=jobs, competition=competition,
        competitor_courses=competitor_courses, gaps=gaps, revenue=revenue,
    )

    limitations = _limitations(auditor, competitor_courses, seo_metrics, jobs)

    # Assemble + write
    context = rb.build_context(
        topic=inp.topic, working_title=inp.working_title, target_learner=target_learner,
        regions=inp.target_regions, depth=depth,
        keywords=dump(keywords), seo_metrics=seo_metrics, trends=dump(trends),
        competitor_courses=dump(competitor_courses), competition=dump(competition),
        jobs=dump(jobs), social=dump(social), gaps=dump(gaps), revenue=dump(revenue),
        positioning=dump(positioning) if hasattr(positioning, "model_dump") else positioning,
        blueprint=dump(blueprint) if blueprint else {}, ai_angle=ai_angle,
        source_audit=auditor.as_rows(), scores_bundle=bundle, limitations=limitations,
    )

    report_formats = ["markdown", "json", "csv", "html"] if depth != "quick" else ["markdown", "json", "csv"]
    written = generate_report(context, formats=report_formats)

    # Record run in history
    run_id = run_id_for(inp.topic)
    try:
        get_cache().record_run(
            run_id, inp.topic, bundle.overall.score, bundle.go_no_go.value,
            {"scores": context["scores"], "go_no_go": bundle.go_no_go.value},
        )
    except Exception:  # noqa: BLE001
        pass

    return {
        "topic": inp.topic,
        "run_id": run_id,
        "recommended_title": context["recommended_title"],
        "go_no_go": bundle.go_no_go.value,
        "demand_score": bundle.demand.score,
        "competition_score": bundle.competition_risk.score,
        "gap_score": bundle.gap.score,
        "revenue_score": bundle.revenue.score,
        "overall_score": bundle.overall.score,
        "confidence": bundle.confidence.value,
        "summary": context["summary"],
        "top_opportunities": context["top_opportunities"],
        "top_risks": context["top_risks"],
        "recommended_subtopics": competition.common_modules[:10],
        "missing_market_subtopics": [g["gap"] for g in dump(gaps)][:10],
        "revenue_scenarios": revenue.model_dump(mode="json")["scenarios"],
        "report_paths": written["report_paths"],
        "sources_used": context["sources_used"],
        "sources_skipped": context["sources_skipped"],
        "limitations": limitations,
    }


def _limitations(auditor, competitor_courses, seo_metrics, jobs) -> list[str]:
    out: list[str] = []
    skipped = auditor.skipped()
    if skipped:
        out.append(
            f"{len(skipped)} source(s) skipped for compliance/credentials; "
            "results rely on available data."
        )
    if not competitor_courses:
        out.append("No competitor data collected — competition/revenue are weakly grounded.")
    elif all(c.source_type == "search_result" for c in competitor_courses):
        out.append("Competitor data is search-result-only (low confidence); "
                   "add API/manual data to verify prices, ratings and enrollments.")
    if all(m.get("source") == "estimate" for m in seo_metrics) and seo_metrics:
        out.append("SEO volumes are estimated buckets (no SEO API/export configured).")
    if jobs.estimated_job_posting_demand_bucket.value == "unknown":
        out.append("Job-market demand is unverified (no jobs API/export).")
    out.append("Revenue figures are modelled estimates, not verified competitor revenue.")
    return out
