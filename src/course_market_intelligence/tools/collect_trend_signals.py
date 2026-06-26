"""Tool: collect_trend_signals."""

from __future__ import annotations

from ..analysis.trend_analysis import summarize_trends
from ..connectors import search_bing, search_google_cse, serpapi
from ..connectors.manual_csv import load_generic
from ._util import dump


async def collect_trend_signals(
    topic: str,
    keywords: list[str] | None = None,
    regions: list[str] | None = None,
    time_window: str = "past_90_days",
    providers: list[str] | None = None,
    manual_csv_path: str | None = None,
) -> dict:
    """Collect freshness and trend data from compliant providers / exports."""
    providers = providers or ["search_api", "manual_csv"]
    raw_signals: list[dict] = []
    used: list[str] = []
    skipped: list[dict] = []

    # Manual trend export (e.g. Google Trends CSV, Exploding Topics export).
    if "manual_csv" in providers and manual_csv_path:
        rows = load_generic(manual_csv_path)
        emerging = [str(r.get("term") or r.get("keyword") or "") for r in rows if r]
        raw_signals.append({
            "direction": "growing" if rows else "unknown",
            "source": "manual_csv (trend export)",
            "emerging_terms": [e for e in emerging if e][:15],
            "confidence": "high",
        })
        used.append("manual_csv")

    # Search APIs give a weak freshness signal (presence of recent results).
    if "search_api" in providers:
        for name, conn in (("google_cse", search_google_cse), ("bing", search_bing),
                           ("serpapi", serpapi)):
            res = await conn.search(f"{topic} trends {time_window.replace('_', ' ')}")
            if res.status == "ok" and res.items:
                used.append(name)
                raw_signals.append({
                    "direction": "unknown",
                    "source": name,
                    "spikes": [it.get("title") for it in res.items[:3] if it.get("title")],
                    "confidence": "low",
                })
                break
            else:
                skipped.append({"provider": name, "reason": res.reason})

    trends = summarize_trends(topic, raw_signals)
    out = dump(trends)
    out["providers_used"] = used
    out["providers_skipped"] = skipped
    return out
