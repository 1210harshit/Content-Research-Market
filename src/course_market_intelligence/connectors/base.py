"""Shared connector helpers.

Every connector returns a :class:`ConnectorResult` so callers can uniformly
tell whether real data, an estimate, or a compliant skip occurred — and surface
that in the source audit. Connectors never raise on missing credentials; they
return a ``skipped`` result with a clear reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConnectorResult:
    provider: str
    status: str  # "ok" | "skipped" | "error"
    data: Any = None
    reason: str = ""
    confidence: str = "low"
    source_type: str = "official_api"
    items: list[dict] = field(default_factory=list)

    @classmethod
    def skipped(cls, provider: str, reason: str, source_type: str = "official_api") -> ConnectorResult:
        return cls(provider=provider, status="skipped", reason=reason,
                   source_type=source_type, items=[])

    @classmethod
    def error(cls, provider: str, reason: str) -> ConnectorResult:
        return cls(provider=provider, status="error", reason=reason, items=[])

    @classmethod
    def ok(cls, provider: str, items: list[dict], confidence: str = "high",
           source_type: str = "official_api", data: Any = None) -> ConnectorResult:
        return cls(provider=provider, status="ok", items=items, confidence=confidence,
                   source_type=source_type, data=data)
