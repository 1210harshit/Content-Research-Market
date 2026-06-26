"""Manual CSV/XLSX import and normalization.

For restricted platforms (LinkedIn, Coursera without consent, job boards, etc.)
the user uploads a CSV/XLSX export. This module validates the columns, normalizes
values into the shared schemas, and is the single trusted ingestion path for
manual data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from ..schemas import CompetitorCourse, Confidence, Level, SeoMetric

# Column aliases -> canonical field name, per import type.
COMPETITOR_ALIASES = {
    "platform": "platform",
    "title": "course_title",
    "course_title": "course_title",
    "course": "course_title",
    "instructor": "provider_or_instructor",
    "provider": "provider_or_instructor",
    "provider_or_instructor": "provider_or_instructor",
    "url": "url",
    "link": "url",
    "rating": "rating",
    "stars": "rating",
    "reviews": "review_count",
    "review_count": "review_count",
    "num_reviews": "review_count",
    "enrollments": "enrollment_count",
    "enrollment_count": "enrollment_count",
    "students": "enrollment_count",
    "learners": "learner_count",
    "learner_count": "learner_count",
    "price": "price_listed",
    "price_listed": "price_listed",
    "list_price": "price_listed",
    "price_observed": "price_observed",
    "sale_price": "price_observed",
    "discount": "discount_status",
    "discount_status": "discount_status",
    "duration_hours": "duration_hours",
    "hours": "duration_hours",
    "duration": "duration_hours",
    "lectures": "number_of_lectures",
    "number_of_lectures": "number_of_lectures",
    "level": "level",
    "language": "language",
    "last_updated": "last_updated",
    "updated": "last_updated",
    "skills": "skills",
    "modules": "modules_or_topics",
    "modules_or_topics": "modules_or_topics",
    "topics": "modules_or_topics",
    "projects": "projects",
    "certificate": "certificate",
}

SEO_ALIASES = {
    "keyword": "keyword",
    "query": "keyword",
    "volume": "monthly_search_volume",
    "search_volume": "monthly_search_volume",
    "monthly_search_volume": "monthly_search_volume",
    "difficulty": "keyword_difficulty",
    "keyword_difficulty": "keyword_difficulty",
    "kd": "keyword_difficulty",
    "cpc": "cpc",
    "competition": "competition",
}

JOB_ALIASES = {
    "title": "title",
    "job_title": "title",
    "skills": "skills",
    "seniority": "seniority",
    "level": "seniority",
    "industry": "industry",
    "salary": "salary",
    "region": "region",
    "location": "region",
}

SUPPORTED_IMPORT_TYPES = [
    "competitor_courses",
    "keyword_metrics",
    "seo_metrics",
    "job_market_data",
    "platform_pricing",
    "course_reviews_summary",
    "internal_sales_data",
    "internal_lms_data",
    "trend_exports",
    "course_catalog_exports",
]


def _read_any(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    if p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p)
    return pd.read_csv(p)


def _normalize_columns(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in aliases:
            rename[col] = aliases[key]
    return df.rename(columns=rename)


def _split_list(val: Any) -> list[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if str(v).strip()]
    return [s.strip() for s in str(val).replace("|", ",").split(",") if s.strip()]


def _num(val: Any, cast=float):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return cast(str(val).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return None


def load_competitor_courses(path: str | Path, default_platform: str = "manual") -> list[CompetitorCourse]:
    df = _normalize_columns(_read_any(path), COMPETITOR_ALIASES)
    if "course_title" not in df.columns:
        raise ValueError(
            "CSV must contain a course title column (one of: title, course_title, course)."
        )
    courses: list[CompetitorCourse] = []
    for _, row in df.iterrows():
        d = row.to_dict()
        level_raw = str(d.get("level", "unknown")).strip().lower()
        level = level_raw if level_raw in Level.__members__ else "unknown"
        courses.append(CompetitorCourse(
            platform=str(d.get("platform") or default_platform),
            course_title=str(d.get("course_title")),
            provider_or_instructor=_str_or_none(d.get("provider_or_instructor")),
            url=_str_or_none(d.get("url")),
            rating=_num(d.get("rating")),
            review_count=_num(d.get("review_count"), int),
            enrollment_count=_num(d.get("enrollment_count"), int),
            learner_count=_num(d.get("learner_count"), int),
            price_listed=_str_or_none(d.get("price_listed")),
            price_observed=_str_or_none(d.get("price_observed")),
            discount_status=_str_or_none(d.get("discount_status")),
            duration_hours=_num(d.get("duration_hours")),
            number_of_lectures=_num(d.get("number_of_lectures"), int),
            level=Level(level),
            language=_str_or_none(d.get("language")),
            last_updated=_str_or_none(d.get("last_updated")),
            skills=_split_list(d.get("skills")),
            modules_or_topics=_split_list(d.get("modules_or_topics")),
            projects=_split_list(d.get("projects")),
            certificate=str(d.get("certificate", "unknown")).strip().lower()
            if d.get("certificate") is not None else "unknown",
            source_type="manual_csv",
            data_confidence=Confidence.high,
        ))
    return courses


def load_seo_metrics(path: str | Path) -> list[SeoMetric]:
    df = _normalize_columns(_read_any(path), SEO_ALIASES)
    if "keyword" not in df.columns:
        raise ValueError("CSV must contain a 'keyword' column.")
    out: list[SeoMetric] = []
    for _, row in df.iterrows():
        d = row.to_dict()
        out.append(SeoMetric(
            keyword=str(d.get("keyword")),
            monthly_search_volume=_num(d.get("monthly_search_volume"), int),
            keyword_difficulty=_num(d.get("keyword_difficulty"), int),
            cpc=_num(d.get("cpc")),
            competition=_str_or_none(d.get("competition")),
            confidence=Confidence.high,
            source="manual_csv",
        ))
    return out


def load_job_market(path: str | Path) -> list[dict]:
    df = _normalize_columns(_read_any(path), JOB_ALIASES)
    rows = []
    for _, row in df.iterrows():
        d = row.to_dict()
        rows.append({
            "title": _str_or_none(d.get("title")),
            "skills": _split_list(d.get("skills")),
            "seniority": _str_or_none(d.get("seniority")),
            "industry": _str_or_none(d.get("industry")),
            "salary": _str_or_none(d.get("salary")),
            "region": _str_or_none(d.get("region")),
            "source": "manual_csv",
        })
    return rows


def load_generic(path: str | Path) -> list[dict]:
    """Load any tabular export into a list of dict rows (for trend/internal data)."""
    df = _read_any(path)
    return df.fillna("").to_dict(orient="records")


def validate_import(import_type: str, path: str | Path) -> dict:
    """Validate an import without committing; returns a summary."""
    if import_type not in SUPPORTED_IMPORT_TYPES:
        raise ValueError(
            f"Unsupported import_type '{import_type}'. "
            f"Supported: {', '.join(SUPPORTED_IMPORT_TYPES)}"
        )
    df = _read_any(path)
    return {
        "import_type": import_type,
        "rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "path": str(path),
    }


def _str_or_none(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    return s or None
