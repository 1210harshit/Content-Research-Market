"""Small shared helpers for tools."""

from __future__ import annotations

import re
from datetime import UTC, datetime


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:60] or "topic"


def run_id_for(topic: str) -> str:
    # Deterministic-ish run id without Date.now in scripts; uses utcnow at runtime.
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return f"{slugify(topic)}-{stamp}"


def utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def dump(obj):
    """Pydantic-or-plain to dict/list of dicts."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [dump(o) for o in obj]
    return obj
