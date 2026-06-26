"""LinkedIn Learning — manual import only.

LinkedIn restricts scraping/crawling and automated copying of services. This
connector therefore does NOT fetch anything from LinkedIn. It only points the
user to the manual CSV import path and, optionally, validates a provided export.
"""

from __future__ import annotations

from pathlib import Path

from .base import ConnectorResult
from .manual_csv import load_competitor_courses


def info() -> ConnectorResult:
    return ConnectorResult.skipped(
        "linkedin_learning",
        "LinkedIn restricts automated scraping. Provide a manual CSV export "
        "(import_manual_data with import_type='competitor_courses') or use the "
        "official API if you have partner access.",
        source_type="manual_csv",
    )


def import_export(csv_path: str | Path) -> ConnectorResult:
    """Validate and load a manually-collected LinkedIn Learning CSV export."""
    try:
        courses = load_competitor_courses(csv_path, default_platform="LinkedIn Learning")
    except Exception as exc:  # noqa: BLE001
        return ConnectorResult.error("linkedin_learning", f"CSV import failed: {exc}")
    return ConnectorResult.ok(
        "linkedin_learning",
        [c.model_dump() for c in courses],
        confidence="high",
        source_type="manual_csv",
    )
