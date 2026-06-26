"""Curriculum blueprint and course positioning generators.

These produce a market-backed outline by combining identified gaps,
job-market skills and competitor coverage. Output is a structured blueprint,
not marketing copy lifted from any source.
"""

from __future__ import annotations

from ..schemas import (
    CompetitionAnalysis,
    CourseBlueprint,
    CoursePositioning,
    Keyword,
    Lesson,
    Level,
    MarketGap,
    Module,
    TrendSignals,
)

_DURATION_PRESETS = {
    "short": (3.0, 4),
    "medium": (8.0, 7),
    "long": (16.0, 10),
}


def design_blueprint(
    topic: str,
    target_learner: str,
    goal: str,
    market_gaps: list[MarketGap],
    job_skills: list[str],
    competition: CompetitionAnalysis,
    preferred_duration: str = "auto",
) -> CourseBlueprint:
    duration_key = _resolve_duration(preferred_duration, competition)
    total_hours, n_modules = _DURATION_PRESETS[duration_key]

    high_gaps = [g for g in market_gaps if g.priority.value == "high"]
    gap_modules = [g.recommended_module_or_lesson for g in high_gaps]

    modules: list[Module] = []
    modules.append(Module(
        title=f"Foundations of {topic}",
        objective=f"Build the core mental model needed to apply {topic}.",
        lessons=[
            Lesson(title=f"What {topic} is and why it matters now"),
            Lesson(title="Key concepts and vocabulary"),
            Lesson(title="Tooling and setup"),
        ],
        quiz="Foundations check",
    ))

    # Skill-driven core modules
    for skill in (job_skills[:max(1, n_modules - 4)] or [f"Core {topic} workflow"]):
        modules.append(Module(
            title=f"Applying {skill}",
            objective=f"Use {skill} on realistic, job-relevant tasks.",
            lessons=[
                Lesson(title=f"{skill}: concepts"),
                Lesson(title=f"{skill}: hands-on walkthrough"),
                Lesson(title=f"{skill}: common mistakes"),
            ],
            exercise=f"Practice exercise: {skill}",
        ))

    # AI workflow module if a gap calls for it
    if any(g.gap_type == "AI" for g in market_gaps):
        modules.append(Module(
            title=f"AI-assisted {topic} workflows",
            objective="Accelerate work with AI tools while verifying quality.",
            lessons=[
                Lesson(title="Prompting patterns for the task"),
                Lesson(title="Validating and correcting AI output"),
            ],
            exercise="Automate one task end-to-end with AI",
        ))

    # Job-readiness capstone
    modules.append(Module(
        title="From course to outcome",
        objective="Turn skills into a portfolio artifact and job-ready positioning.",
        lessons=[
            Lesson(title="Capstone brief and rubric"),
            Lesson(title="CV / LinkedIn positioning"),
            Lesson(title="Interview and demo prep"),
        ],
        exercise="Capstone project",
    ))

    modules = modules[:n_modules] if len(modules) > n_modules else modules

    return CourseBlueprint(
        recommended_total_duration_hours=total_hours,
        recommended_number_of_modules=len(modules),
        modules=modules,
        practical_exercises=[m.exercise for m in modules if m.exercise],
        quizzes=[f"{m.title} quiz" for m in modules],
        templates=[f"{topic} starter template", f"{topic} checklist template"],
        checklists=[f"{topic} quality checklist", "Job-readiness checklist"],
        capstone_projects=[f"End-to-end {topic} capstone aligned to a real role"],
        portfolio_projects=[f"Portfolio piece demonstrating {topic} competency"],
        learning_outcomes=_learning_outcomes(topic, job_skills),
        cv_linkedin_positioning=(
            f"Add {topic} with a linked capstone; mirror in-demand skills "
            f"({', '.join(job_skills[:4]) or topic})."
        ),
        b2b_addon_modules=[g.recommended_module_or_lesson for g in market_gaps
                           if g.gap_type == "B2B"],
        ai_workflow_modules=[g.recommended_module_or_lesson for g in market_gaps
                             if g.gap_type == "AI"],
        missing_market_modules=gap_modules,
    )


def _resolve_duration(preferred: str, competition: CompetitionAnalysis) -> str:
    if preferred in _DURATION_PRESETS:
        return preferred
    avg = competition.average_duration_hours
    if avg is None:
        return "medium"
    if avg <= 4:
        return "short"
    if avg >= 14:
        return "long"
    return "medium"


def _learning_outcomes(topic: str, job_skills: list[str]) -> list[str]:
    outcomes = [
        f"Explain core {topic} concepts and when to apply them.",
        f"Complete realistic {topic} tasks independently.",
        "Produce a portfolio-ready capstone deliverable.",
    ]
    for s in job_skills[:3]:
        outcomes.append(f"Demonstrate {s} in a job-relevant scenario.")
    return outcomes


def recommend_positioning(
    topic: str,
    working_title: str | None,
    target_learner: str,
    competition: CompetitionAnalysis,
    trends: TrendSignals,
    ai_angle: dict,
    keywords: list[Keyword],
    level: Level = Level.beginner,
) -> CoursePositioning:
    titles = _title_options(topic, level)
    primary = working_title or titles[0]
    ad_keywords = [k.keyword for k in keywords
                   if k.recommended_use in ("ad keyword", "landing page")][:10]

    return CoursePositioning(
        title_options=titles,
        subtitle_options=[
            f"Hands-on, project-based {topic} for real-world outcomes",
            f"Go from beginner to job-ready in {topic}",
            f"{topic} with modern tools and an AI-assisted workflow",
        ],
        primary_recommended_title=primary,
        target_learner=target_learner or f"Aspiring/practising professionals in {topic}",
        level=level,
        course_format="project-based",
        value_proposition=(
            f"The most practical, current {topic} course — built around real tasks, "
            "portfolio projects and (where relevant) AI-assisted workflows."
        ),
        course_promise=f"Finish able to do {topic}, not just describe it.",
        differentiation_strategy=(
            "Lead with hands-on projects, freshness, job-readiness and an AI angle "
            "where competitors are generic or outdated."
        ),
        b2c_positioning="Project-based, outcome-focused marketplace course.",
        b2b_positioning="Team-licensable upskilling with workbook, rubric and admin guide.",
        ai_angle_recommendation=ai_angle.get("positioning_line", ""),
        seasonal_launch_angle=trends.best_launch_window or "Align with quarterly upskilling cycles.",
        ad_landing_keywords=ad_keywords or [f"{topic} course", f"learn {topic}"],
    )


def _title_options(topic: str, level: Level) -> list[str]:
    t = topic.strip().title()
    return [
        f"{t}: The Complete Hands-On Course",
        f"{t} Masterclass — Project-Based & Job-Ready",
        f"The Practical {t} Bootcamp",
        f"{t} for Professionals: From Basics to Real Projects",
        f"AI-Assisted {t}: Do More, Faster",
        f"{t} Certification Prep with Real Projects",
        f"Learn {t} by Building (Portfolio Projects Included)",
        f"{t} from Zero to Job-Ready",
    ]
