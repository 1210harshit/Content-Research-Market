"""Competitor landscape analysis and the competition-risk sub-scores."""

from __future__ import annotations

import statistics
from collections import Counter

from ..schemas import (
    Bucket,
    CompetitionAnalysis,
    CompetitorCourse,
    Confidence,
)

_STRONG_BRANDS = {
    "coursera", "google", "ibm", "meta", "microsoft", "aws", "amazon",
    "deeplearning.ai", "university", "stanford", "harvard", "mit", "linkedin",
}


def analyze(courses: list[CompetitorCourse], topic: str = "") -> CompetitionAnalysis:
    if not courses:
        return CompetitionAnalysis(
            competition_level=Bucket.unknown,
            confidence=Confidence.low,
        )

    ratings = [c.rating for c in courses if c.rating is not None]
    reviews = [c.review_count for c in courses if c.review_count is not None]
    enrollments = [c.enrollment_count or c.learner_count for c in courses
                   if (c.enrollment_count or c.learner_count) is not None]
    durations = [c.duration_hours for c in courses if c.duration_hours is not None]

    all_modules = [m for c in courses for m in c.modules_or_topics]
    all_projects = [p for c in courses for p in c.projects]
    all_titles = [c.course_title for c in courses if c.course_title]

    closest = _closest_competitors(courses)
    common_modules = _most_common(all_modules, 12)
    competition_level, comp_components = _competition_level(courses, reviews, enrollments)

    return CompetitionAnalysis(
        closest_competitors=closest,
        average_rating=round(statistics.mean(ratings), 2) if ratings else None,
        average_review_count=round(statistics.mean(reviews), 1) if reviews else None,
        average_enrollment_count=round(statistics.mean(enrollments), 1) if enrollments else None,
        average_duration_hours=round(statistics.mean(durations), 1) if durations else None,
        common_price_bands=_price_bands(courses),
        common_titles=_most_common([_title_signature(t) for t in all_titles], 6),
        common_subtitles=[],
        common_modules=common_modules,
        common_projects=_most_common(all_projects, 8),
        common_learning_outcomes=common_modules[:6],
        common_formats=_formats(courses),
        competitor_strengths=_strengths(courses, ratings, reviews),
        competitor_weaknesses=_weaknesses(courses),
        overserved_subtopics=common_modules[:5],
        underserved_subtopics=[],  # filled by gap_analysis
        outdated_competitor_coverage=_stale(courses),
        competition_level=competition_level,
        evidence_table=[_evidence_row(c) for c in courses[:15]],
        confidence=_confidence(courses),
    )


def _closest_competitors(courses: list[CompetitorCourse], n: int = 5) -> list[dict]:
    def strength(c: CompetitorCourse) -> float:
        return (c.rating or 0) * 10 + (c.review_count or 0) / 100.0
    ranked = sorted(courses, key=strength, reverse=True)[:n]
    return [
        {
            "title": c.course_title,
            "platform": c.platform,
            "provider": c.provider_or_instructor,
            "rating": c.rating,
            "review_count": c.review_count,
            "url": c.url,
        }
        for c in ranked
    ]


def _most_common(items: list[str], n: int) -> list[str]:
    norm = [i.strip() for i in items if i and i.strip()]
    return [item for item, _ in Counter(i.lower() for i in norm).most_common(n)]


def _title_signature(title: str) -> str:
    return title.strip()


def _price_bands(courses: list[CompetitorCourse]) -> list[str]:
    bands = Counter()
    for c in courses:
        price = _parse_price(c.price_observed or c.price_listed)
        if price is None:
            continue
        if price == 0:
            bands["free"] += 1
        elif price < 20:
            bands["$0-$20"] += 1
        elif price < 50:
            bands["$20-$50"] += 1
        elif price < 100:
            bands["$50-$100"] += 1
        elif price < 300:
            bands["$100-$300"] += 1
        else:
            bands["$300+"] += 1
    return [f"{band} ({count})" for band, count in bands.most_common()]


def _parse_price(price: str | None) -> float | None:
    if price is None:
        return None
    p = str(price).strip().lower()
    if p in ("free", "$0", "0"):
        return 0.0
    digits = "".join(ch for ch in p if ch.isdigit() or ch == ".")
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


def _formats(courses: list[CompetitorCourse]) -> list[str]:
    fmts = Counter()
    for c in courses:
        if c.projects:
            fmts["project-based"] += 1
        if c.certificate == "yes":
            fmts["certificate-bearing"] += 1
        if (c.duration_hours or 0) >= 20:
            fmts["long-form / comprehensive"] += 1
        elif (c.duration_hours or 0) and c.duration_hours < 3:
            fmts["microlearning / short"] += 1
    return [f for f, _ in fmts.most_common()]


def _strengths(courses, ratings, reviews) -> list[str]:
    out = []
    if ratings and statistics.mean(ratings) >= 4.4:
        out.append("Established competitors maintain high ratings (>=4.4).")
    if reviews and max(reviews) >= 5000:
        out.append("Market leaders have large review counts signalling strong demand.")
    if any(c.certificate == "yes" for c in courses):
        out.append("Several competitors offer certificates.")
    if not out:
        out.append("No dominant strengths detected; field may be fragmented.")
    return out


def _weaknesses(courses) -> list[str]:
    out = []
    if not any(c.projects for c in courses):
        out.append("Few competitors offer hands-on projects.")
    if not any(c.b2b_relevance in (Bucket.high, Bucket.medium) for c in courses):
        out.append("Limited B2B / corporate-ready positioning.")
    stale = _stale(courses)
    if stale:
        out.append("Some leading courses appear outdated.")
    if not out:
        out.append("No obvious structural weaknesses; differentiation must be earned.")
    return out


def _stale(courses) -> list[str]:
    stale = []
    for c in courses:
        lu = (c.last_updated or "").strip()
        if lu and any(year in lu for year in ("2019", "2020", "2021", "2022")):
            stale.append(f"{c.course_title} (last updated {lu})")
    return stale[:5]


def _competition_level(courses, reviews, enrollments) -> tuple[Bucket, dict]:
    strong = sum(1 for c in courses if (c.review_count or 0) >= 1000 or (c.rating or 0) >= 4.5)
    saturation = len(courses)
    brand = sum(
        1 for c in courses
        if any(b in (c.provider_or_instructor or "").lower() for b in _STRONG_BRANDS)
    )
    # concentration: share of reviews held by top course
    concentration = 0.0
    if reviews:
        total = sum(reviews)
        if total:
            concentration = max(reviews) / total

    level = Bucket.low
    if strong >= 5 or saturation >= 15 or concentration > 0.6:
        level = Bucket.high
    elif strong >= 2 or saturation >= 6:
        level = Bucket.medium
    return level, {"strong": strong, "saturation": saturation, "brand": brand,
                   "concentration": concentration}


def _evidence_row(c: CompetitorCourse) -> dict:
    return {
        "platform": c.platform,
        "title": c.course_title,
        "rating": c.rating,
        "reviews": c.review_count,
        "price": c.price_observed or c.price_listed,
        "duration_hours": c.duration_hours,
        "level": c.level.value if hasattr(c.level, "value") else c.level,
        "source_type": c.source_type,
        "confidence": c.data_confidence.value if hasattr(c.data_confidence, "value") else c.data_confidence,
    }


def _confidence(courses) -> Confidence:
    api = sum(1 for c in courses if c.source_type in ("official_api", "manual_csv"))
    if api >= max(3, len(courses) // 2):
        return Confidence.high
    if courses:
        return Confidence.medium
    return Confidence.low


# --------------------------------------------------------------------------- #
# Score components                                                             #
# --------------------------------------------------------------------------- #
def competition_components(analysis: CompetitionAnalysis,
                           courses: list[CompetitorCourse]) -> dict[str, float]:
    """Return 0-100 component scores for the competition-risk model (higher=worse)."""
    _, raw = _competition_level(
        courses,
        [c.review_count for c in courses if c.review_count is not None],
        [c.enrollment_count for c in courses if c.enrollment_count is not None],
    )
    strong = raw["strong"]
    saturation = raw["saturation"]
    brand = raw["brand"]
    concentration = raw["concentration"]

    strong_competitors = min(100.0, strong * 18.0)
    review_concentration = min(100.0, concentration * 100.0)
    brand_strength = min(100.0, brand * 25.0)
    content_saturation = min(100.0, saturation * 6.0)
    # Differentiation is harder when there are many strong, well-rated incumbents.
    differentiation_difficulty = min(100.0, (strong * 12.0) + (brand * 10.0))

    return {
        "strong_competitors": strong_competitors,
        "review_enrollment_concentration": review_concentration,
        "brand_strength": brand_strength,
        "content_saturation": content_saturation,
        "differentiation_difficulty": differentiation_difficulty,
    }


def competitor_proof_of_demand(courses: list[CompetitorCourse]) -> float:
    """Existence of well-reviewed competitors is proof learners pay for this."""
    if not courses:
        return 35.0
    well_reviewed = sum(1 for c in courses if (c.review_count or 0) >= 500)
    base = min(100.0, 40.0 + well_reviewed * 8.0)
    return base
