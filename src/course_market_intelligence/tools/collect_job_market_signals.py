"""Tool: collect_job_market_signals."""

from __future__ import annotations

from ..analysis.job_market_analysis import summarize_jobs
from ..connectors import job_market_api
from ..connectors.manual_csv import load_job_market
from ._util import dump


async def collect_job_market_signals(
    topic: str,
    keywords: list[str] | None = None,
    regions: list[str] | None = None,
    target_learner: str = "",
    source_modes: list[str] | None = None,
    manual_csv_path: str | None = None,
) -> dict:
    """Determine whether the topic maps to real jobs / upskilling demand."""
    source_modes = source_modes or ["official_api", "search_api", "manual_csv"]
    regions = regions or ["US", "UK", "EMEA"]
    raw_postings: list[dict] = []
    used: list[str] = []
    skipped: list[dict] = []

    if "manual_csv" in source_modes and manual_csv_path:
        raw_postings.extend(load_job_market(manual_csv_path))
        used.append("manual_csv")

    if "official_api" in source_modes and not raw_postings:
        for region in regions[:3]:
            res = await job_market_api.search_postings(topic, location=region)
            if res.status == "ok" and res.items:
                raw_postings.extend(res.items)
                used.append(f"jobs_api:{region}")
            else:
                skipped.append({"provider": f"jobs_api:{region}", "reason": res.reason})

    jobs = summarize_jobs(topic, raw_postings, target_learner)
    out = dump(jobs)
    out["providers_used"] = used
    out["providers_skipped"] = skipped
    out["postings_analyzed"] = len(raw_postings)
    return out
