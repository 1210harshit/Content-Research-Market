"""course-market-intelligence-mcp server (FastMCP, stdio).

Registers all 17 tools. IMPORTANT for stdio transport: never write to stdout;
all diagnostics go to stderr. Secrets are never logged or returned.
"""

from __future__ import annotations

import logging
import sys

from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .tools.analyze_competition import analyze_competition as _analyze_competition
from .tools.check_source_policy import check_source_policy as _check_source_policy
from .tools.collect_competitor_courses import (
    collect_competitor_courses as _collect_competitor_courses,
)
from .tools.collect_job_market_signals import (
    collect_job_market_signals as _collect_job_market_signals,
)
from .tools.collect_seo_metrics import collect_seo_metrics as _collect_seo_metrics
from .tools.collect_social_signals import collect_social_signals as _collect_social_signals
from .tools.collect_trend_signals import collect_trend_signals as _collect_trend_signals
from .tools.design_course_blueprint import design_course_blueprint as _design_course_blueprint
from .tools.discover_keywords import discover_keywords as _discover_keywords
from .tools.discover_sources import discover_sources as _discover_sources
from .tools.estimate_revenue_potential import (
    estimate_revenue_potential as _estimate_revenue_potential,
)
from .tools.export_research_assets import export_research_assets as _export_research_assets
from .tools.find_market_gaps import find_market_gaps as _find_market_gaps
from .tools.generate_report import generate_report as _generate_report
from .tools.import_manual_data import import_manual_data as _import_manual_data
from .tools.recommend_course_positioning import (
    recommend_course_positioning as _recommend_course_positioning,
)
from .tools.research_course_topic import research_course_topic as _research_course_topic

# Logging to stderr ONLY (stdout is the MCP transport channel).
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("course-market-intelligence-mcp")

settings = get_settings()
mcp = FastMCP(settings.server_name)


# --------------------------------------------------------------------------- #
# Tool registrations                                                          #
# --------------------------------------------------------------------------- #
@mcp.tool()
async def research_course_topic(
    topic: str,
    working_title: str | None = None,
    goal: str = "",
    target_learners: dict | None = None,
    platforms: list[str] | None = None,
    target_regions: list[str] | None = None,
    timeframe: str = "launching within 2-3 months",
    depth: str = "standard",
    allowed_source_modes: list[str] | None = None,
    include_ai_angle: bool = True,
    include_revenue_model: bool = True,
    include_curriculum_blueprint: bool = True,
    include_job_market: bool = True,
    include_social_signals: bool = True,
    freshness_window_days: int = 90,
    manual_data: dict | None = None,
) -> dict:
    """Run the full course market validation workflow and return a go/no-go verdict
    with scores, opportunities, risks, subtopics, revenue scenarios and report paths."""
    payload = {
        "topic": topic,
        "working_title": working_title,
        "goal": goal,
        "target_learners": target_learners or {},
        "platforms": platforms or ["Udemy", "Coursera", "LinkedIn Learning", "Go1",
                                   "edX", "FutureLearn", "YouTube", "Class Central"],
        "target_regions": target_regions or ["US", "UK", "EMEA"],
        "timeframe": timeframe,
        "depth": depth,
        "allowed_source_modes": allowed_source_modes or [
            "official_api", "search_api", "seo_api",
            "public_metadata", "manual_csv", "internal_data"],
        "include_ai_angle": include_ai_angle,
        "include_revenue_model": include_revenue_model,
        "include_curriculum_blueprint": include_curriculum_blueprint,
        "include_job_market": include_job_market,
        "include_social_signals": include_social_signals,
        "freshness_window_days": freshness_window_days,
        "manual_data": manual_data or {},
    }
    return await _research_course_topic(payload)


@mcp.tool()
async def discover_sources(
    topic: str,
    platforms: list[str] | None = None,
    target_regions: list[str] | None = None,
    source_types: list[str] | None = None,
    max_sources: int = 100,
) -> dict:
    """Find relevant online sources for a course topic with their allowed collection modes."""
    return _discover_sources(topic, platforms, target_regions, source_types, max_sources)


@mcp.tool()
async def check_source_policy(url_or_domain: str, intended_collection_mode: str) -> dict:
    """Check whether a source can be collected from with a given mode (policy + robots.txt)."""
    return await _check_source_policy(url_or_domain, intended_collection_mode)


@mcp.tool()
async def discover_keywords(
    topic: str,
    goal: str = "",
    target_learner: str = "",
    target_regions: list[str] | None = None,
    platforms: list[str] | None = None,
    max_keywords: int = 50,
    include_ai_angle: bool = True,
) -> dict:
    """Generate high-intent learner keywords with intent, funnel stage and recommended use."""
    return _discover_keywords(topic, goal, target_learner, target_regions,
                              platforms, max_keywords, include_ai_angle)


@mcp.tool()
async def collect_seo_metrics(
    keywords: list[str],
    regions: list[str] | None = None,
    providers: list[str] | None = None,
    fallback_to_estimates: bool = True,
    manual_csv_path: str | None = None,
) -> dict:
    """Collect SEO metrics from approved SEO APIs or a manual export."""
    return await _collect_seo_metrics(keywords, regions, providers,
                                      fallback_to_estimates, manual_csv_path)


@mcp.tool()
async def collect_trend_signals(
    topic: str,
    keywords: list[str] | None = None,
    regions: list[str] | None = None,
    time_window: str = "past_90_days",
    providers: list[str] | None = None,
    manual_csv_path: str | None = None,
) -> dict:
    """Collect freshness and trend data from compliant providers / exports."""
    return await _collect_trend_signals(topic, keywords, regions, time_window,
                                        providers, manual_csv_path)


@mcp.tool()
async def collect_competitor_courses(
    topic: str,
    keywords: list[str] | None = None,
    platforms: list[str] | None = None,
    max_courses_per_platform: int = 20,
    source_modes: list[str] | None = None,
    manual_csv_paths: dict | None = None,
) -> dict:
    """Collect normalized competitor course metadata from authorized sources only."""
    return await _collect_competitor_courses(
        topic, keywords, platforms, max_courses_per_platform,
        source_modes, manual_csv_paths,
    )


@mcp.tool()
async def analyze_competition(courses: list[dict], topic: str = "") -> dict:
    """Analyze the competitor landscape from normalized course records."""
    return _analyze_competition(courses, topic)


@mcp.tool()
async def collect_job_market_signals(
    topic: str,
    keywords: list[str] | None = None,
    regions: list[str] | None = None,
    target_learner: str = "",
    source_modes: list[str] | None = None,
    manual_csv_path: str | None = None,
) -> dict:
    """Determine whether the topic maps to real jobs / upskilling demand."""
    return await _collect_job_market_signals(topic, keywords, regions,
                                             target_learner, source_modes, manual_csv_path)


@mcp.tool()
async def collect_social_signals(
    topic: str,
    keywords: list[str] | None = None,
    source_modes: list[str] | None = None,
    manual_reviews_csv: str | None = None,
) -> dict:
    """Find aggregate learner pain points from compliant public/API sources (no personal data)."""
    return await _collect_social_signals(topic, keywords, source_modes, manual_reviews_csv)


@mcp.tool()
async def find_market_gaps(
    topic: str,
    competition: dict,
    keywords: list[dict] | None = None,
    job_market: dict | None = None,
    trends: dict | None = None,
    social: dict | None = None,
    include_ai_angle: bool = True,
    target_regions: list[str] | None = None,
) -> dict:
    """Find valuable missing subtopics and whitespace across all signals."""
    return _find_market_gaps(topic, competition, keywords, job_market,
                             trends, social, include_ai_angle, target_regions)


@mcp.tool()
async def estimate_revenue_potential(
    topic: str,
    competitor_courses: list[dict] | None = None,
    keyword_metrics: list[dict] | None = None,
    trend_signals: dict | None = None,
    job_market_signals: dict | None = None,
    target_platforms: list[str] | None = None,
    pricing_strategy: str = "mixed",
    target_regions: list[str] | None = None,
) -> dict:
    """Estimate rough 12-month revenue scenarios (explicitly modelled estimates)."""
    return _estimate_revenue_potential(
        topic, competitor_courses, keyword_metrics, trend_signals,
        job_market_signals, target_platforms, pricing_strategy, target_regions,
    )


@mcp.tool()
async def recommend_course_positioning(
    topic: str,
    working_title: str | None = None,
    target_learner: str = "",
    competition: dict | None = None,
    trends: dict | None = None,
    job_market: dict | None = None,
    keywords: list[dict] | None = None,
    level: str = "beginner",
    include_ai_angle: bool = True,
) -> dict:
    """Create course titles, subtitles, value propositions and differentiation."""
    return _recommend_course_positioning(
        topic, working_title, target_learner, competition, trends,
        job_market, keywords, level, include_ai_angle,
    )


@mcp.tool()
async def design_course_blueprint(
    topic: str,
    target_learner: str = "",
    goal: str = "",
    market_gaps: list[dict] | None = None,
    job_market_skills: list[str] | None = None,
    competitor_analysis: dict | None = None,
    preferred_duration: str = "auto",
) -> dict:
    """Create a market-backed course outline (modules, projects, outcomes)."""
    return _design_course_blueprint(
        topic, target_learner, goal, market_gaps, job_market_skills,
        competitor_analysis, preferred_duration,
    )


@mcp.tool()
async def generate_report(
    report_context: dict,
    formats: list[str] | None = None,
    out_dir: str | None = None,
) -> dict:
    """Write Markdown / JSON / CSV (+optional HTML) outputs from a report context."""
    return _generate_report(report_context, formats, out_dir)


@mcp.tool()
async def import_manual_data(
    import_type: str,
    file_path: str,
    validate_only: bool = False,
) -> dict:
    """Validate, normalize and load a manually-collected CSV/XLSX file."""
    return _import_manual_data(import_type, file_path, validate_only)


@mcp.tool()
async def export_research_assets(report_context: dict, out_dir: str | None = None) -> dict:
    """Export all collected/analyzed data and summarize confidence + compliance."""
    return _export_research_assets(report_context, out_dir)


def main() -> None:
    logger.info("Starting %s (stdio). Available providers: %s",
                settings.server_name, settings.available_providers())
    mcp.run()


if __name__ == "__main__":
    main()
