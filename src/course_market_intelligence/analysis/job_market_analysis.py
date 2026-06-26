"""Job-market signal interpretation and the demand sub-score it feeds."""

from __future__ import annotations

from collections import Counter

from ..schemas import Bucket, Confidence, JobMarketSignals


def summarize_jobs(
    topic: str,
    raw_postings: list[dict] | None = None,
    target_learner: str = "",
) -> JobMarketSignals:
    """Aggregate job posting payloads into normalized JobMarketSignals.

    Each raw posting may include: title, skills[], seniority, industry,
    salary, region, source.
    """
    raw_postings = raw_postings or []
    if not raw_postings:
        return JobMarketSignals(
            estimated_job_posting_demand_bucket=Bucket.unknown,
            confidence=Confidence.low,
            recommended_cv_positioning=(
                f"List {topic} as a practical, project-backed skill with measurable outcomes."
            ),
            recommended_linkedin_positioning=(
                f"Add {topic} to skills and feature a capstone project in Featured."
            ),
            sources=[],
        )

    titles = Counter()
    skills = Counter()
    industries = Counter()
    seniorities = Counter()
    regions: dict[str, int] = {}
    salaries: list[str] = []
    sources: set[str] = set()

    for p in raw_postings:
        if p.get("title"):
            titles[p["title"].strip()] += 1
        for s in p.get("skills", []) or []:
            skills[s.strip().lower()] += 1
        if p.get("industry"):
            industries[p["industry"].strip()] += 1
        if p.get("seniority"):
            seniorities[p["seniority"].strip().lower()] += 1
        if p.get("region"):
            regions[p["region"]] = regions.get(p["region"], 0) + 1
        if p.get("salary"):
            salaries.append(str(p["salary"]))
        if p.get("source"):
            sources.add(p["source"])

    demand_bucket = (
        Bucket.high if len(raw_postings) >= 200
        else Bucket.medium if len(raw_postings) >= 40
        else Bucket.low
    )

    entry = _fit(seniorities, ("junior", "entry", "associate", "intern"))
    upskill = _fit(seniorities, ("mid", "intermediate", "senior", "specialist"))
    leadership = _fit(seniorities, ("lead", "manager", "head", "director", "principal"))

    return JobMarketSignals(
        related_job_titles=[t for t, _ in titles.most_common(12)],
        skill_frequency=dict(skills.most_common(20)),
        seniority_level=seniorities.most_common(1)[0][0] if seniorities else None,
        entry_level_fit=entry,
        upskilling_fit=upskill,
        leadership_fit=leadership,
        industries_hiring=[i for i, _ in industries.most_common(8)],
        estimated_job_posting_demand_bucket=demand_bucket,
        salary_range_if_available=_salary_summary(salaries),
        regional_differences=regions,
        recommended_cv_positioning=(
            f"Frame {topic} around the top hiring skills: "
            f"{', '.join(list(skills)[:5]) or topic}."
        ),
        recommended_linkedin_positioning=(
            f"Target roles such as {', '.join([t for t, _ in titles.most_common(3)]) or topic}."
        ),
        course_to_role_mapping=[
            {"role": t, "evidence": f"{c} matching postings"}
            for t, c in titles.most_common(5)
        ],
        confidence=Confidence.high if len(sources) >= 1 and len(raw_postings) >= 40 else Confidence.medium,
        sources=sorted(sources),
    )


def _fit(seniorities: Counter, keys: tuple[str, ...]) -> Bucket:
    total = sum(seniorities.values()) or 1
    matched = sum(v for k, v in seniorities.items() if any(key in k for key in keys))
    ratio = matched / total
    return Bucket.high if ratio >= 0.4 else Bucket.medium if ratio >= 0.15 else Bucket.low


def _salary_summary(salaries: list[str]) -> str | None:
    if not salaries:
        return None
    return f"Reported across {len(salaries)} postings; e.g. {salaries[0]}"


def job_market_component(jobs: JobMarketSignals) -> float:
    """0-100 contribution of job-market relevance to demand score."""
    bucket_points = {Bucket.high: 95.0, Bucket.medium: 65.0,
                     Bucket.low: 35.0, Bucket.unknown: 45.0}
    base = bucket_points[jobs.estimated_job_posting_demand_bucket]
    if jobs.skill_frequency:
        base = min(100.0, base + 5.0)
    return base


def b2b_relevance_component(jobs: JobMarketSignals) -> float:
    """0-100 B2B / corporate relevance for the demand score."""
    score = 40.0
    if jobs.leadership_fit == Bucket.high:
        score += 25
    elif jobs.leadership_fit == Bucket.medium:
        score += 12
    if jobs.upskilling_fit == Bucket.high:
        score += 20
    elif jobs.upskilling_fit == Bucket.medium:
        score += 10
    if jobs.industries_hiring:
        score += 10
    return min(100.0, score)
