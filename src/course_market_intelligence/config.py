"""Runtime configuration loaded from environment variables.

Secrets are read from the environment ONLY. They are never logged or returned
through tool responses. Use ``Settings.has(...)`` to test for presence of a key
without exposing its value.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load a local .env if present. In production, real env vars take precedence.
load_dotenv(override=False)

# Repository root = three levels up from this file
# (.../src/course_market_intelligence/config.py -> repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]


def _get(name: str, default: str | None = None) -> str | None:
    val = os.environ.get(name)
    if val is None or val.strip() == "":
        return default
    return val.strip()


class Settings:
    """Process-wide settings. Instantiated once via :func:`get_settings`."""

    def __init__(self) -> None:
        self.server_name = _get("MCP_SERVER_NAME", "course-market-intelligence-mcp")

        # Search APIs
        self.google_cse_api_key = _get("GOOGLE_CSE_API_KEY")
        self.google_cse_engine_id = _get("GOOGLE_CSE_ENGINE_ID")
        self.bing_search_api_key = _get("BING_SEARCH_API_KEY")
        self.serpapi_key = _get("SERPAPI_KEY")
        self.dataforseo_login = _get("DATAFORSEO_LOGIN")
        self.dataforseo_password = _get("DATAFORSEO_PASSWORD")

        # SEO / trend APIs
        self.semrush_api_key = _get("SEMRUSH_API_KEY")
        self.ahrefs_api_key = _get("AHREFS_API_KEY")
        self.moz_api_key = _get("MOZ_API_KEY")
        self.similarweb_api_key = _get("SIMILARWEB_API_KEY")

        # Platform / content APIs
        self.youtube_api_key = _get("YOUTUBE_API_KEY")
        self.udemy_client_id = _get("UDEMY_CLIENT_ID")
        self.udemy_client_secret = _get("UDEMY_CLIENT_SECRET")
        self.coursera_api_key = _get("COURSERA_API_KEY")
        self.go1_api_key = _get("GO1_API_KEY")

        # Social
        self.reddit_client_id = _get("REDDIT_CLIENT_ID")
        self.reddit_client_secret = _get("REDDIT_CLIENT_SECRET")

        # Job market
        self.jobs_api_key = _get("JOBS_API_KEY")

        # Runtime
        self.cache_ttl_hours = int(_get("CACHE_TTL_HOURS", "72") or 72)
        self.max_results_per_source = int(_get("MAX_RESULTS_PER_SOURCE", "25") or 25)
        self.default_rate_limit_seconds = float(
            _get("DEFAULT_RATE_LIMIT_SECONDS", "2") or 2
        )
        self.request_timeout_seconds = float(_get("REQUEST_TIMEOUT_SECONDS", "30") or 30)
        self.max_retries = int(_get("MAX_RETRIES", "3") or 3)

        export_dir = _get("EXPORT_DIR", "data/exports") or "data/exports"
        self.export_dir = (REPO_ROOT / export_dir).resolve()

        db_url = _get("DATABASE_URL", "sqlite:///data/research_cache.sqlite")
        self.database_path = self._resolve_sqlite_path(db_url)

        self.manual_uploads_dir = (REPO_ROOT / "data" / "manual_uploads").resolve()
        self.cache_dir = (REPO_ROOT / "data" / "cache").resolve()
        self.source_policy_path = REPO_ROOT / "source_policy.yaml"

        self._ensure_dirs()

    @staticmethod
    def _resolve_sqlite_path(db_url: str | None) -> Path:
        if not db_url:
            db_url = "sqlite:///data/research_cache.sqlite"
        if db_url.startswith("sqlite:///"):
            rel = db_url[len("sqlite:///") :]
        else:
            rel = db_url
        p = Path(rel)
        if not p.is_absolute():
            p = REPO_ROOT / p
        return p.resolve()

    def _ensure_dirs(self) -> None:
        for d in (self.export_dir, self.manual_uploads_dir, self.cache_dir,
                  self.database_path.parent):
            d.mkdir(parents=True, exist_ok=True)

    def has(self, *attr_names: str) -> bool:
        """Return True only if every named credential attribute is present."""
        return all(bool(getattr(self, name, None)) for name in attr_names)

    def available_providers(self) -> dict[str, bool]:
        """Map of provider -> credentials-present, for diagnostics (no secrets)."""
        return {
            "google_cse": self.has("google_cse_api_key", "google_cse_engine_id"),
            "bing_search": self.has("bing_search_api_key"),
            "serpapi": self.has("serpapi_key"),
            "dataforseo": self.has("dataforseo_login", "dataforseo_password"),
            "semrush": self.has("semrush_api_key"),
            "ahrefs": self.has("ahrefs_api_key"),
            "moz": self.has("moz_api_key"),
            "similarweb": self.has("similarweb_api_key"),
            "youtube": self.has("youtube_api_key"),
            "udemy": self.has("udemy_client_id", "udemy_client_secret"),
            "coursera": self.has("coursera_api_key"),
            "go1": self.has("go1_api_key"),
            "reddit": self.has("reddit_client_id", "reddit_client_secret"),
            "jobs": self.has("jobs_api_key"),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
