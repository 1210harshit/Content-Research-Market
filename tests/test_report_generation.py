"""Tests for CSV import, competitor normalization and report generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from course_market_intelligence.analysis import scoring
from course_market_intelligence.connectors.manual_csv import (
    load_competitor_courses,
    validate_import,
)
from course_market_intelligence.schemas import Confidence
from course_market_intelligence.tools import _report_builder as rb
from course_market_intelligence.tools.generate_report import generate_report


@pytest.fixture
def competitor_csv(tmp_path: Path) -> Path:
    p = tmp_path / "competitors.csv"
    p.write_text(
        "platform,title,price,rating,reviews,duration_hours,level,skills\n"
        "Udemy,Intro to X,$99.99,4.6,1200,8,beginner,\"sql, python\"\n"
        "Coursera,X Specialization,Free,4.7,3400,20,intermediate,\"ml, stats\"\n",
        encoding="utf-8",
    )
    return p


def test_csv_import_validation(competitor_csv: Path):
    summary = validate_import("competitor_courses", competitor_csv)
    assert summary["rows"] == 2
    assert "title" in summary["columns"]


def test_competitor_normalization(competitor_csv: Path):
    courses = load_competitor_courses(competitor_csv)
    assert len(courses) == 2
    assert courses[0].platform == "Udemy"
    assert courses[0].rating == 4.6
    assert courses[0].review_count == 1200
    assert "sql" in courses[0].skills
    assert courses[0].source_type == "manual_csv"
    assert courses[0].data_confidence == Confidence.high


def test_invalid_import_type_raises(tmp_path: Path):
    p = tmp_path / "x.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_import("not_a_type", p)


def test_report_generation_writes_files(tmp_path: Path):
    bundle = scoring.build_bundle(
        {k: 70 for k in scoring.DEMAND_WEIGHTS},
        {k: 30 for k in scoring.COMPETITION_WEIGHTS},
        {k: 65 for k in scoring.GAP_WEIGHTS},
        {k: 60 for k in scoring.REVENUE_WEIGHTS},
        [Confidence.high, Confidence.medium],
    )
    context = rb.build_context(
        topic="Test Topic", working_title="TT", target_learner="learners",
        regions=["US"], depth="standard", keywords=[], seo_metrics=[],
        trends={"topic": "Test Topic", "trend_direction": "growing",
                "growth_rate_estimate": "n/a", "confidence": "low", "sources": []},
        competitor_courses=[], competition={"common_modules": [], "competition_level": "low",
                                            "competitor_strengths": [], "closest_competitors": [],
                                            "competitor_weaknesses": []},
        jobs={"related_job_titles": [], "skill_frequency": {},
              "estimated_job_posting_demand_bucket": "unknown"},
        social={}, gaps=[{"gap": "g1", "gap_type": "AI", "priority": "high",
                          "why_it_matters": "x"}],
        revenue={"scenarios": {}, "marketplace_risk_factors": [],
                 "recommended_udemy_list_price": 129.99,
                 "expected_realized_udemy_price": 23.4,
                 "recommended_b2b_licensing_band": "band"},
        positioning={"primary_recommended_title": "TT", "value_proposition": "vp",
                     "differentiation_strategy": "diff", "b2c_positioning": "b2c",
                     "b2b_positioning": "b2b", "title_options": ["TT"],
                     "ad_landing_keywords": ["k"], "target_learner": "learners"},
        blueprint={"recommended_total_duration_hours": 8, "recommended_number_of_modules": 5,
                   "modules": [], "capstone_projects": ["cap"], "learning_outcomes": ["lo"]},
        ai_angle={"ai_angle_strength": "high", "rationale": "r", "recommended_modules": []},
        source_audit=[{"domain": "udemy.com", "mode": "search_api",
                       "decision": "allowed", "reason": "ok"}],
        scores_bundle=bundle, limitations=["limited data"],
    )
    out = generate_report(context, formats=["markdown", "json", "csv", "html"],
                          out_dir=str(tmp_path))
    paths = out["report_paths"]
    assert Path(paths["markdown"]).exists()
    assert Path(paths["json"]).exists()
    assert Path(paths["html"]).exists()
    assert Path(paths["competitors_csv"]).exists()
    md = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert "Course Market Validation Report" in md
    assert "Go / No-Go" in md
