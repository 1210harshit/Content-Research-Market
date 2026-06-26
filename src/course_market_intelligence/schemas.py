"""Pydantic schemas shared across tools, connectors, analysis and outputs.

These models define the normalized contracts so that every connector returns
data in the same shape and every analysis function can rely on it. All inputs
are validated through these models before any network call is made.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


# --------------------------------------------------------------------------- #
# Enums                                                                        #
# --------------------------------------------------------------------------- #
class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Bucket(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    unknown = "unknown"


class TrendDirection(str, Enum):
    growing = "growing"
    flat = "flat"
    declining = "declining"
    unknown = "unknown"


class CollectionMode(str, Enum):
    official_api = "official_api"
    affiliate_api = "affiliate_api"
    partner_api = "partner_api"
    partner_approved = "partner_approved"
    customer_export = "customer_export"
    youtube_data_api = "youtube_data_api"
    bing_search_api = "bing_search_api"
    search_api = "search_api"
    seo_api = "seo_api"
    public_metadata = "public_metadata"
    public_metadata_if_allowed = "public_metadata_if_allowed"
    manual_csv = "manual_csv"
    internal_data = "internal_data"


class Depth(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class GoNoGo(str, Enum):
    strong_go = "strong_go"
    conditional_go = "conditional_go"
    hold_research_more = "hold_research_more"
    no_go = "no_go"


class Level(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"
    mixed = "mixed"
    unknown = "unknown"


# --------------------------------------------------------------------------- #
# Source policy                                                                #
# --------------------------------------------------------------------------- #
class SourcePolicyResult(BaseModel):
    domain: str
    allowed: bool
    allowed_modes: list[str] = Field(default_factory=list)
    blocked_modes: list[str] = Field(default_factory=list)
    robots_txt_status: str = "not_checked"  # allowed|disallowed|unknown|not_checked
    terms_status: str = "unknown"  # allowed|restricted|unknown
    reason: str = ""
    safe_next_step: str = ""


# --------------------------------------------------------------------------- #
# Discovery                                                                    #
# --------------------------------------------------------------------------- #
class DiscoveredSource(BaseModel):
    source_name: str
    domain: str
    source_type: str
    relevance: Bucket = Bucket.unknown
    allowed_collection_modes: list[str] = Field(default_factory=list)
    requires_api_key: bool = False
    requires_manual_csv: bool = False
    source_policy_status: str = "unknown"
    reason_to_use: str = ""
    confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# Keywords                                                                     #
# --------------------------------------------------------------------------- #
class Keyword(BaseModel):
    keyword: str
    intent: str = "B2C"
    funnel_stage: str = "awareness"
    volume_bucket: Bucket = Bucket.unknown
    trend_direction: TrendDirection = TrendDirection.unknown
    difficulty_bucket: Bucket = Bucket.unknown
    platform_relevance: list[str] = Field(default_factory=list)
    recommended_use: str = "landing page"
    confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# SEO metrics                                                                  #
# --------------------------------------------------------------------------- #
class SeoMetric(BaseModel):
    keyword: str
    monthly_search_volume: int | None = None
    volume_bucket: Bucket = Bucket.unknown
    keyword_difficulty: int | None = None
    cpc: float | None = None
    competition: str | None = None
    related_keywords: list[str] = Field(default_factory=list)
    questions_people_ask: list[str] = Field(default_factory=list)
    serp_features: list[str] = Field(default_factory=list)
    top_ranking_domains: list[str] = Field(default_factory=list)
    regional_split: dict[str, Any] = Field(default_factory=dict)
    confidence: Confidence = Confidence.low
    source: str = "estimate"


# --------------------------------------------------------------------------- #
# Trend signals                                                                #
# --------------------------------------------------------------------------- #
class TrendSignals(BaseModel):
    topic: str
    trend_direction: TrendDirection = TrendDirection.unknown
    growth_rate_estimate: str | None = None
    seasonality: str | None = None
    recent_spikes: list[str] = Field(default_factory=list)
    emerging_related_terms: list[str] = Field(default_factory=list)
    declining_related_terms: list[str] = Field(default_factory=list)
    best_launch_window: str | None = None
    promotional_angles: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
    sources: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Competitor courses                                                           #
# --------------------------------------------------------------------------- #
class CompetitorCourse(BaseModel):
    platform: str
    course_title: str
    provider_or_instructor: str | None = None
    url: str | None = None
    rating: float | None = None
    review_count: int | None = None
    enrollment_count: int | None = None
    learner_count: int | None = None
    price_listed: str | None = None
    price_observed: str | None = None
    discount_status: str | None = None
    duration_hours: float | None = None
    number_of_lectures: int | None = None
    level: Level = Level.unknown
    language: str | None = None
    last_updated: str | None = None
    skills: list[str] = Field(default_factory=list)
    modules_or_topics: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    certificate: str = "unknown"  # yes|no|unknown
    b2b_relevance: Bucket = Bucket.unknown
    source_url: str | None = None
    source_type: str = "search_result"  # official_api|search_result|public_page|manual_csv
    fetched_at: str = Field(default_factory=utcnow_iso)
    data_confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# Competition analysis                                                         #
# --------------------------------------------------------------------------- #
class CompetitionAnalysis(BaseModel):
    closest_competitors: list[dict[str, Any]] = Field(default_factory=list)
    average_rating: float | None = None
    average_review_count: float | None = None
    average_enrollment_count: float | None = None
    average_duration_hours: float | None = None
    common_price_bands: list[str] = Field(default_factory=list)
    common_titles: list[str] = Field(default_factory=list)
    common_subtitles: list[str] = Field(default_factory=list)
    common_modules: list[str] = Field(default_factory=list)
    common_projects: list[str] = Field(default_factory=list)
    common_learning_outcomes: list[str] = Field(default_factory=list)
    common_formats: list[str] = Field(default_factory=list)
    competitor_strengths: list[str] = Field(default_factory=list)
    competitor_weaknesses: list[str] = Field(default_factory=list)
    overserved_subtopics: list[str] = Field(default_factory=list)
    underserved_subtopics: list[str] = Field(default_factory=list)
    outdated_competitor_coverage: list[str] = Field(default_factory=list)
    competition_level: Bucket = Bucket.unknown
    evidence_table: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# Job market                                                                   #
# --------------------------------------------------------------------------- #
class JobMarketSignals(BaseModel):
    related_job_titles: list[str] = Field(default_factory=list)
    skill_frequency: dict[str, int] = Field(default_factory=dict)
    seniority_level: str | None = None
    entry_level_fit: Bucket = Bucket.unknown
    upskilling_fit: Bucket = Bucket.unknown
    leadership_fit: Bucket = Bucket.unknown
    industries_hiring: list[str] = Field(default_factory=list)
    estimated_job_posting_demand_bucket: Bucket = Bucket.unknown
    salary_range_if_available: str | None = None
    regional_differences: dict[str, Any] = Field(default_factory=dict)
    recommended_cv_positioning: str | None = None
    recommended_linkedin_positioning: str | None = None
    course_to_role_mapping: list[dict[str, str]] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
    sources: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Social signals                                                               #
# --------------------------------------------------------------------------- #
class SocialSignals(BaseModel):
    common_learner_questions: list[str] = Field(default_factory=list)
    common_complaints: list[str] = Field(default_factory=list)
    confusing_subtopics: list[str] = Field(default_factory=list)
    requested_tools_templates_projects: list[str] = Field(default_factory=list)
    beginner_pain_points: list[str] = Field(default_factory=list)
    advanced_pain_points: list[str] = Field(default_factory=list)
    b2b_buyer_concerns: list[str] = Field(default_factory=list)
    evidence_snippets: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.low
    sources: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Market gaps                                                                  #
# --------------------------------------------------------------------------- #
class MarketGap(BaseModel):
    gap: str
    gap_type: str  # content|format|project|tooling|AI|region|B2B|job_market|assessment|freshness
    evidence: list[str] = Field(default_factory=list)
    why_it_matters: str = ""
    recommended_module_or_lesson: str = ""
    priority: Bucket = Bucket.medium
    commercial_value: Bucket = Bucket.medium
    confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# Revenue                                                                      #
# --------------------------------------------------------------------------- #
class RevenueScenario(BaseModel):
    name: str  # low|base|high
    enrollments: int
    realized_price: float
    b2b_deals: int = 0
    b2b_deal_value: float = 0.0
    annual_revenue: float = 0.0
    assumptions: list[str] = Field(default_factory=list)


class RevenueEstimate(BaseModel):
    recommended_udemy_list_price: float | None = None
    expected_realized_udemy_price: float | None = None
    recommended_b2b_licensing_band: str | None = None
    recommended_subscription_model: str | None = None
    scenarios: dict[str, RevenueScenario] = Field(default_factory=dict)
    enrollment_assumptions: list[str] = Field(default_factory=list)
    traffic_assumptions: list[str] = Field(default_factory=list)
    conversion_assumptions: list[str] = Field(default_factory=list)
    rating_review_assumptions: list[str] = Field(default_factory=list)
    promotion_assumptions: list[str] = Field(default_factory=list)
    b2b_deal_assumptions: list[str] = Field(default_factory=list)
    marketplace_risk_factors: list[str] = Field(default_factory=list)
    sensitivity_analysis: list[dict[str, Any]] = Field(default_factory=list)
    confidence: Confidence = Confidence.low


# --------------------------------------------------------------------------- #
# Positioning                                                                  #
# --------------------------------------------------------------------------- #
class CoursePositioning(BaseModel):
    title_options: list[str] = Field(default_factory=list)
    subtitle_options: list[str] = Field(default_factory=list)
    primary_recommended_title: str = ""
    target_learner: str = ""
    level: Level = Level.beginner
    course_format: str = "project-based"
    value_proposition: str = ""
    course_promise: str = ""
    differentiation_strategy: str = ""
    b2c_positioning: str = ""
    b2b_positioning: str = ""
    ai_angle_recommendation: str = ""
    seasonal_launch_angle: str = ""
    ad_landing_keywords: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Blueprint                                                                    #
# --------------------------------------------------------------------------- #
class Lesson(BaseModel):
    title: str
    summary: str = ""
    duration_minutes: int = 15


class Module(BaseModel):
    title: str
    objective: str = ""
    lessons: list[Lesson] = Field(default_factory=list)
    exercise: str | None = None
    quiz: str | None = None


class CourseBlueprint(BaseModel):
    recommended_total_duration_hours: float = 0.0
    recommended_number_of_modules: int = 0
    modules: list[Module] = Field(default_factory=list)
    practical_exercises: list[str] = Field(default_factory=list)
    quizzes: list[str] = Field(default_factory=list)
    templates: list[str] = Field(default_factory=list)
    checklists: list[str] = Field(default_factory=list)
    capstone_projects: list[str] = Field(default_factory=list)
    portfolio_projects: list[str] = Field(default_factory=list)
    learning_outcomes: list[str] = Field(default_factory=list)
    cv_linkedin_positioning: str = ""
    b2b_addon_modules: list[str] = Field(default_factory=list)
    ai_workflow_modules: list[str] = Field(default_factory=list)
    missing_market_modules: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Scores                                                                       #
# --------------------------------------------------------------------------- #
class ScoreBreakdown(BaseModel):
    score: float
    components: dict[str, float] = Field(default_factory=dict)
    rationale: list[str] = Field(default_factory=list)


class ScoreBundle(BaseModel):
    demand: ScoreBreakdown
    competition_risk: ScoreBreakdown
    gap: ScoreBreakdown
    revenue: ScoreBreakdown
    overall: ScoreBreakdown
    go_no_go: GoNoGo
    confidence: Confidence


# --------------------------------------------------------------------------- #
# Tool input schemas                                                           #
# --------------------------------------------------------------------------- #
class TargetLearner(BaseModel):
    profile: str = ""
    background: str = ""
    motivation: str = ""


class ResearchTopicInput(BaseModel):
    topic: str
    working_title: str | None = None
    goal: str = ""
    target_learners: TargetLearner = Field(default_factory=TargetLearner)
    platforms: list[str] = Field(
        default_factory=lambda: [
            "Udemy", "Coursera", "LinkedIn Learning", "Go1",
            "edX", "FutureLearn", "YouTube", "Class Central",
        ]
    )
    target_regions: list[str] = Field(default_factory=lambda: ["US", "UK", "EMEA"])
    timeframe: str = "launching within 2-3 months"
    depth: Depth = Depth.standard
    allowed_source_modes: list[str] = Field(
        default_factory=lambda: [
            "official_api", "search_api", "seo_api",
            "public_metadata", "manual_csv", "internal_data",
        ]
    )
    include_ai_angle: bool = True
    include_revenue_model: bool = True
    include_curriculum_blueprint: bool = True
    include_job_market: bool = True
    include_social_signals: bool = True
    freshness_window_days: int = 90

    @field_validator("topic")
    @classmethod
    def _topic_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("topic must be a non-empty string")
        return v.strip()
