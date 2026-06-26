"""AI-angle recommendation: how to weave an AI workflow story into the course."""

from __future__ import annotations

from ..schemas import CompetitionAnalysis, JobMarketSignals, TrendSignals


def recommend_ai_angle(
    topic: str,
    competition: CompetitionAnalysis,
    jobs: JobMarketSignals,
    trends: TrendSignals,
) -> dict:
    ai_covered = any("ai" in m for m in competition.common_modules)
    emerging_ai = any("ai" in t.lower() for t in trends.emerging_related_terms)

    if not ai_covered:
        strength = "high"
        rationale = (
            "Competitors do not meaningfully cover AI-assisted workflows, so an "
            f"AI angle for {topic} is a clear differentiator."
        )
    else:
        strength = "medium"
        rationale = (
            f"Some competitors touch AI for {topic}; differentiate on depth, "
            "real tooling and reproducible workflows rather than novelty."
        )

    return {
        "ai_angle_strength": strength,
        "rationale": rationale,
        "recommended_modules": [
            f"Use AI assistants to accelerate {topic} tasks (prompting patterns, guardrails).",
            f"Automate repetitive {topic} steps with AI tools.",
            f"Quality-check and validate AI output in a {topic} context.",
            "Responsible-AI and accuracy/limitations for professional use.",
        ],
        "positioning_line": f"{topic} for the AI era: do it faster, verify it properly.",
        "evidence": [
            "AI coverage gap among competitors" if not ai_covered else "AI partially covered",
            "Emerging AI-related search terms" if emerging_ai else "Broad AI adoption trend",
        ],
    }
