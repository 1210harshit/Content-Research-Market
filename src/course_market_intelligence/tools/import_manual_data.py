"""Tool: import_manual_data."""

from __future__ import annotations

from pathlib import Path

from ..config import get_settings
from ..connectors.manual_csv import (
    SUPPORTED_IMPORT_TYPES,
    load_competitor_courses,
    load_generic,
    load_job_market,
    load_seo_metrics,
    validate_import,
)
from ._util import dump

_LOADERS = {
    "competitor_courses": lambda p: dump(load_competitor_courses(p)),
    "platform_pricing": lambda p: dump(load_competitor_courses(p)),
    "course_catalog_exports": lambda p: dump(load_competitor_courses(p)),
    "keyword_metrics": lambda p: dump(load_seo_metrics(p)),
    "seo_metrics": lambda p: dump(load_seo_metrics(p)),
    "job_market_data": load_job_market,
    "course_reviews_summary": load_generic,
    "internal_sales_data": load_generic,
    "internal_lms_data": load_generic,
    "trend_exports": load_generic,
}


def import_manual_data(import_type: str, file_path: str, validate_only: bool = False) -> dict:
    """Validate, normalize and load a manually-collected CSV/XLSX file."""
    if import_type not in SUPPORTED_IMPORT_TYPES:
        return {
            "ok": False,
            "error": f"Unsupported import_type '{import_type}'.",
            "supported_import_types": SUPPORTED_IMPORT_TYPES,
        }

    path = Path(file_path)
    if not path.is_absolute():
        # Allow relative names against the manual_uploads dir.
        candidate = get_settings().manual_uploads_dir / file_path
        path = candidate if candidate.exists() else path

    if not path.exists():
        return {"ok": False, "error": f"File not found: {path}"}

    try:
        summary = validate_import(import_type, path)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Validation failed: {exc}"}

    if validate_only:
        return {"ok": True, "validated": True, "summary": summary}

    try:
        loader = _LOADERS[import_type]
        records = loader(str(path))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"Normalization failed: {exc}", "summary": summary}

    return {
        "ok": True,
        "import_type": import_type,
        "summary": summary,
        "record_count": len(records),
        "records": records,
        "source_type": "manual_csv",
        "confidence": "high",
    }
