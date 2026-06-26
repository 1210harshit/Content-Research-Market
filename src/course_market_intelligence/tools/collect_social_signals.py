"""Tool: collect_social_signals.

Surfaces aggregate learner pain points from compliant sources only (Reddit API,
search snippets where allowed, user-provided review exports). Never collects
personal data; evidence is stored as short summaries.
"""

from __future__ import annotations

from ..connectors import reddit_api, search_bing, search_google_cse
from ..connectors.manual_csv import load_generic
from ..schemas import Confidence, SocialSignals
from ._util import dump

_COMPLAINT_HINTS = ("outdated", "boring", "too basic", "too fast", "no projects",
                    "confusing", "not enough", "waste", "disappointing")
_QUESTION_HINTS = ("how do i", "how to", "what is", "should i", "best way", "?")


async def collect_social_signals(
    topic: str,
    keywords: list[str] | None = None,
    source_modes: list[str] | None = None,
    manual_reviews_csv: str | None = None,
) -> dict:
    """Find learner pain points and unmet needs from compliant public sources."""
    source_modes = source_modes or ["official_api", "search_api", "manual_csv"]
    questions: list[str] = []
    complaints: list[str] = []
    requested: list[str] = []
    evidence: list[str] = []
    used: list[str] = []
    skipped: list[dict] = []

    # 1. Manual review export (e.g. exported course reviews) — highest signal.
    if "manual_csv" in source_modes and manual_reviews_csv:
        for row in load_generic(manual_reviews_csv):
            text = " ".join(str(v) for v in row.values()).lower()
            _classify(text, questions, complaints, requested, evidence)
        used.append("manual_csv")

    # 2. Reddit API (aggregate, no personal data).
    if "official_api" in source_modes:
        res = await reddit_api.search_discussions(f"{topic} course OR learning", limit=25)
        if res.status == "ok":
            used.append("reddit")
            for it in res.items:
                text = f"{it.get('title','')} {it.get('summary','')}".lower()
                _classify(text, questions, complaints, requested, evidence)
        else:
            skipped.append({"provider": "reddit", "reason": res.reason})

    # 3. Search snippets (questions people ask).
    if "search_api" in source_modes and len(questions) < 5:
        for conn, name in ((search_google_cse, "google_cse"), (search_bing, "bing")):
            res = await conn.search(f"{topic} course problems OR questions")
            if res.status == "ok" and res.items:
                used.append(name)
                for it in res.items:
                    _classify((it.get("snippet") or "").lower(), questions,
                              complaints, requested, evidence)
                break
            else:
                skipped.append({"provider": name, "reason": res.reason})

    confidence = Confidence.medium if used and "manual_csv" not in used else (
        Confidence.high if "manual_csv" in used else Confidence.low
    )
    signals = SocialSignals(
        common_learner_questions=_top(questions),
        common_complaints=_top(complaints),
        confusing_subtopics=_top([c for c in complaints if "confus" in c]),
        requested_tools_templates_projects=_top(requested),
        beginner_pain_points=_top([q for q in questions if "beginner" in q or "start" in q]),
        advanced_pain_points=_top([c for c in complaints if "advanced" in c or "depth" in c]),
        b2b_buyer_concerns=[],
        evidence_snippets=evidence[:10],
        confidence=confidence,
        sources=sorted(set(used)),
    )
    out = dump(signals)
    out["providers_used"] = used
    out["providers_skipped"] = skipped
    return out


def _classify(text, questions, complaints, requested, evidence):
    if not text.strip():
        return
    snippet = text[:160]
    if any(h in text for h in _QUESTION_HINTS):
        questions.append(snippet)
        evidence.append(f"Q: {snippet}")
    if any(h in text for h in _COMPLAINT_HINTS):
        complaints.append(snippet)
        evidence.append(f"Complaint: {snippet}")
    if "template" in text or "project" in text or "example" in text:
        requested.append(snippet)


def _top(items: list[str], n: int = 8) -> list[str]:
    seen, out = set(), []
    for i in items:
        k = i.strip()[:80]
        if k and k not in seen:
            seen.add(k)
            out.append(i.strip())
        if len(out) >= n:
            break
    return out
