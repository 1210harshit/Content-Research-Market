"""SQLite-backed cache and research history.

Caches normalized data and (where compliant) raw metadata keyed by
domain + mode + query. Never caches secrets, personal data, or paid/restricted
content. Callers are responsible for not passing such data in.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    domain TEXT,
    source_mode TEXT,
    query TEXT,
    normalized_json TEXT,
    raw_json TEXT,
    fetched_at TEXT,
    expires_at TEXT,
    confidence TEXT,
    source_policy_status TEXT
);
CREATE TABLE IF NOT EXISTS research_runs (
    run_id TEXT PRIMARY KEY,
    topic TEXT,
    created_at TEXT,
    overall_score REAL,
    go_no_go TEXT,
    summary_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_cache_domain ON cache(domain);
CREATE INDEX IF NOT EXISTS idx_runs_topic ON research_runs(topic);
"""


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_key(domain: str, mode: str, query: str) -> str:
    raw = f"{domain.lower()}|{mode.lower()}|{query.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Cache:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or get_settings().database_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def get(self, domain: str, mode: str, query: str) -> dict[str, Any] | None:
        key = _make_key(domain, mode, query)
        row = self._conn.execute(
            "SELECT * FROM cache WHERE cache_key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        expires_at = row["expires_at"]
        if expires_at:
            try:
                if datetime.fromisoformat(expires_at) < _utcnow():
                    return None
            except ValueError:
                return None
        return {
            "normalized": json.loads(row["normalized_json"]) if row["normalized_json"] else None,
            "raw": json.loads(row["raw_json"]) if row["raw_json"] else None,
            "fetched_at": row["fetched_at"],
            "expires_at": row["expires_at"],
            "confidence": row["confidence"],
            "source_policy_status": row["source_policy_status"],
        }

    def set(
        self,
        domain: str,
        mode: str,
        query: str,
        normalized: Any,
        raw: Any = None,
        confidence: str = "low",
        ttl_hours: int | None = None,
        source_policy_status: str = "allowed",
    ) -> None:
        key = _make_key(domain, mode, query)
        ttl = ttl_hours if ttl_hours is not None else get_settings().cache_ttl_hours
        now = _utcnow()
        expires = now + timedelta(hours=ttl)
        self._conn.execute(
            """INSERT OR REPLACE INTO cache
               (cache_key, domain, source_mode, query, normalized_json, raw_json,
                fetched_at, expires_at, confidence, source_policy_status)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                key, domain, mode, query,
                json.dumps(normalized, default=str) if normalized is not None else None,
                json.dumps(raw, default=str) if raw is not None else None,
                now.isoformat(), expires.isoformat(), confidence, source_policy_status,
            ),
        )
        self._conn.commit()

    def record_run(self, run_id: str, topic: str, overall_score: float,
                   go_no_go: str, summary: dict[str, Any]) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO research_runs
               (run_id, topic, created_at, overall_score, go_no_go, summary_json)
               VALUES (?,?,?,?,?,?)""",
            (run_id, topic, _utcnow().isoformat(), overall_score, go_no_go,
             json.dumps(summary, default=str)),
        )
        self._conn.commit()

    def list_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT run_id, topic, created_at, overall_score, go_no_go "
            "FROM research_runs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self._conn.close()


_cache_singleton: Cache | None = None


def get_cache() -> Cache:
    global _cache_singleton
    if _cache_singleton is None:
        _cache_singleton = Cache()
    return _cache_singleton
