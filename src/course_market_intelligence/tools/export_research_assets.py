"""Tool: export_research_assets."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from ..config import get_settings
from ..outputs import csv_exports, json_report
from ._util import slugify


def export_research_assets(report_context: dict, out_dir: str | None = None) -> dict:
    """Export all collected/analyzed data and summarize confidence + compliance."""
    settings = get_settings()
    base = Path(out_dir) if out_dir else settings.export_dir
    slug = slugify(report_context.get("topic", "topic"))

    paths = {"json": json_report.write_json(report_context, base, slug)}
    paths.update(csv_exports.export_all(report_context, base, slug))

    # Data confidence summary across competitor records.
    conf_counts = Counter(
        c.get("data_confidence", "low") for c in report_context.get("competitors", [])
    )
    audit = report_context.get("source_audit", [])
    compliance_summary = {
        "sources_used": sum(1 for s in audit if s.get("decision") == "allowed"),
        "sources_skipped": sum(1 for s in audit if s.get("decision") == "skipped"),
        "skipped_reasons": [s.get("reason") for s in audit if s.get("decision") == "skipped"][:10],
    }

    return {
        "ok": True,
        "file_paths": paths,
        "export_summary": {
            "competitors": len(report_context.get("competitors", [])),
            "keywords": len(report_context.get("keywords", [])),
            "gaps": len(report_context.get("gaps", [])),
        },
        "data_confidence_summary": dict(conf_counts),
        "source_compliance_summary": compliance_summary,
    }
