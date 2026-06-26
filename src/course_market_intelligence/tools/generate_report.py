"""Tool: generate_report — write Markdown/JSON/CSV (+optional HTML) outputs."""

from __future__ import annotations

from pathlib import Path

from ..config import get_settings
from ..outputs import csv_exports, html_report, json_report, markdown_report
from ._util import slugify


def generate_report(report_context: dict, formats: list[str] | None = None,
                    out_dir: str | None = None) -> dict:
    """Write the assembled report context to files and return their paths."""
    formats = formats or ["markdown", "json", "csv", "html"]
    settings = get_settings()
    base = Path(out_dir) if out_dir else settings.export_dir
    slug = slugify(report_context.get("topic", "topic"))

    paths: dict[str, str] = {}
    if "markdown" in formats:
        paths["markdown"] = markdown_report.write_markdown(report_context, base, slug)
    if "json" in formats:
        paths["json"] = json_report.write_json(report_context, base, slug)
    if "csv" in formats:
        paths.update(csv_exports.export_all(report_context, base, slug))
    if "html" in formats:
        paths["html"] = html_report.write_html(report_context, base, slug)

    return {
        "ok": True,
        "slug": slug,
        "report_paths": paths,
    }
