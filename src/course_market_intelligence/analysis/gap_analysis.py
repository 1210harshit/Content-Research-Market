"""Market gap discovery by cross-referencing demand, competition and jobs."""

from __future__ import annotations

from ..schemas import (
    Bucket,
    CompetitionAnalysis,
    Confidence,
    JobMarketSignals,
    Keyword,
    MarketGap,
    SocialSignals,
    TrendSignals,
)


def find_gaps(
    topic: str,
    competition: CompetitionAnalysis,
    keywords: list[Keyword],
    jobs: JobMarketSignals,
    trends: TrendSignals,
    social: SocialSignals | None = None,
    include_ai_angle: bool = True,
    target_regions: list[str] | None = None,
) -> list[MarketGap]:
    gaps: list[MarketGap] = []
    covered = {m.lower() for m in competition.common_modules}
    social = social or SocialSignals()
    target_regions = target_regions or ["US", "UK", "EMEA"]

    # 1. Job-market skill gaps (content + job_market)
    for skill in list(jobs.skill_frequency.keys())[:10]:
        if skill.lower() not in covered:
            gaps.append(MarketGap(
                gap=f"In-demand skill not covered: {skill}",
                gap_type="job_market",
                evidence=[f"Appears in job postings ({jobs.skill_frequency[skill]}x)",
                          "Absent from common competitor modules"],
                why_it_matters="Maps the course directly to hiring demand.",
                recommended_module_or_lesson=f"Module: Applying {skill} on the job",
                priority=Bucket.high,
                commercial_value=Bucket.high,
                confidence=Confidence.medium,
            ))

    # 2. AI / tooling workflow gaps
    if include_ai_angle and not any("ai" in m for m in covered):
        gaps.append(MarketGap(
            gap=f"AI-assisted {topic} workflows are largely uncovered",
            gap_type="AI",
            evidence=["No AI workflow module among common competitor modules",
                      "Emerging AI-related search terms" if trends.emerging_related_terms else
                      "Strong general AI adoption trend"],
            why_it_matters="AI augmentation is a top differentiator and search driver.",
            recommended_module_or_lesson=f"Module: Using AI tools to accelerate {topic}",
            priority=Bucket.high,
            commercial_value=Bucket.high,
            confidence=Confidence.medium,
        ))

    # 3. Project / practice gaps
    if not competition.common_projects:
        gaps.append(MarketGap(
            gap="Hands-on, portfolio-grade projects are scarce",
            gap_type="project",
            evidence=["Few competitors list projects",
                      *(social.requested_tools_templates_projects[:2])],
            why_it_matters="Project-based courses convert better and aid job-readiness.",
            recommended_module_or_lesson="Capstone: build a portfolio-ready deliverable",
            priority=Bucket.high,
            commercial_value=Bucket.high,
            confidence=Confidence.medium,
        ))

    # 4. Job-readiness / assessment gaps
    gaps.append(MarketGap(
        gap="Job-readiness scaffolding (interview prep, CV mapping) is thin",
        gap_type="job_readiness",
        evidence=[f"Related roles: {', '.join(jobs.related_job_titles[:3]) or 'n/a'}"],
        why_it_matters="Differentiates a career-outcome course from generic tutorials.",
        recommended_module_or_lesson="Module: From course to hire (CV, LinkedIn, interview)",
        priority=Bucket.medium,
        commercial_value=Bucket.medium,
        confidence=Confidence.low,
    ))

    # 5. B2B / corporate gaps
    gaps.append(MarketGap(
        gap="Corporate / team-training packaging is missing",
        gap_type="B2B",
        evidence=["Competitor B2B positioning is limited",
                  *competition.competitor_weaknesses[:1]],
        why_it_matters="B2B licensing carries higher per-deal revenue and repeat purchases.",
        recommended_module_or_lesson="Add-on: team workbook, admin guide, assessment rubric",
        priority=Bucket.medium,
        commercial_value=Bucket.high,
        confidence=Confidence.low,
    ))

    # 6. Freshness / update gaps
    if competition.outdated_competitor_coverage:
        gaps.append(MarketGap(
            gap="Leading courses are outdated",
            gap_type="freshness",
            evidence=competition.outdated_competitor_coverage[:3],
            why_it_matters="A current, frequently-updated course wins comparison shoppers.",
            recommended_module_or_lesson="Maintain a 'what changed this year' update lesson",
            priority=Bucket.medium,
            commercial_value=Bucket.medium,
            confidence=Confidence.medium,
        ))

    # 7. Learner pain-point (content/format) gaps from social signals
    for pain in social.common_complaints[:3]:
        gaps.append(MarketGap(
            gap=f"Unaddressed learner complaint: {pain}",
            gap_type="content",
            evidence=[f"Reported in compliant social/forum signals: {pain}"],
            why_it_matters="Directly addressing complaints improves ratings and retention.",
            recommended_module_or_lesson=f"Design a lesson that explicitly resolves: {pain}",
            priority=Bucket.medium,
            commercial_value=Bucket.medium,
            confidence=social.confidence,
        ))

    # 8. Region-specific gaps
    if len(target_regions) > 1:
        gaps.append(MarketGap(
            gap=f"Region-specific guidance for {', '.join(target_regions)} is generic",
            gap_type="region",
            evidence=["Most marketplace courses are US-centric"],
            why_it_matters="Localized examples/compliance increase relevance in EMEA/UK.",
            recommended_module_or_lesson="Add regional case studies and compliance notes",
            priority=Bucket.low,
            commercial_value=Bucket.medium,
            confidence=Confidence.low,
        ))

    return gaps


def gap_components(gaps: list[MarketGap]) -> dict[str, float]:
    """Return 0-100 component scores for the gap model."""
    def count(types: tuple[str, ...], high_only: bool = False) -> int:
        return sum(
            1 for g in gaps
            if g.gap_type in types and (g.priority == Bucket.high or not high_only)
        )

    missing_subtopics = count(("content", "job_market"))
    missing_skills = count(("job_market",))
    missing_ai = count(("AI", "tooling"))
    missing_projects = count(("project",))
    regional_b2b = count(("region", "B2B"))
    freshness = count(("freshness",))

    return {
        "missing_high_value_subtopics": min(100.0, 30.0 + missing_subtopics * 18.0),
        "missing_job_market_skills": min(100.0, 25.0 + missing_skills * 20.0),
        "missing_ai_tooling_workflows": min(100.0, 20.0 + missing_ai * 40.0),
        "missing_projects_practice": min(100.0, 20.0 + missing_projects * 45.0),
        "regional_b2b_gaps": min(100.0, 20.0 + regional_b2b * 30.0),
        "competitor_freshness_gaps": min(100.0, 25.0 + freshness * 45.0),
    }
