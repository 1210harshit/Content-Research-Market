"""Source policy loading and enforcement.

The policy in ``source_policy.yaml`` is the single source of truth for what the
MCP is allowed to do per domain. Every fetch path MUST consult
:func:`evaluate` (directly or via :mod:`compliance`) before any network call.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import yaml

from .config import get_settings
from .schemas import SourcePolicyResult


def _normalize_domain(url_or_domain: str) -> str:
    raw = (url_or_domain or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        # Treat as a bare domain (possibly with path)
        raw = "https://" + raw
    netloc = urlparse(raw).netloc or urlparse(raw).path
    netloc = netloc.split("/")[0]
    if netloc.startswith("www."):
        netloc = netloc[4:]
    # Reduce host.sub.example.com -> example.com when a registered match exists
    return netloc


@lru_cache(maxsize=1)
def load_policy(path: str | None = None) -> dict:
    policy_path = Path(path) if path else get_settings().source_policy_path
    if not policy_path.exists():
        return {"defaults": {"allowed_modes": ["search_api", "manual_csv"],
                             "public_scraping": "policy_check_required"},
                "domains": {}, "source_classes": {}}
    with policy_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _match_domain_entry(policy: dict, domain: str) -> tuple[str | None, dict | None]:
    """Find the most specific configured domain entry for ``domain``."""
    domains = policy.get("domains", {}) or {}
    if domain in domains:
        return domain, domains[domain]
    # suffix match: api.udemy.com -> udemy.com
    for known, entry in domains.items():
        if domain == known or domain.endswith("." + known):
            return known, entry
    return None, None


def evaluate(url_or_domain: str, intended_mode: str | None = None) -> SourcePolicyResult:
    """Evaluate whether a domain (and optional mode) is permitted by policy."""
    policy = load_policy()
    domain = _normalize_domain(url_or_domain)
    defaults = policy.get("defaults", {}) or {}

    matched_name, entry = _match_domain_entry(policy, domain)
    if entry is None:
        entry = defaults
        source_label = "default policy (unknown domain)"
    else:
        source_label = f"policy entry for {matched_name}"

    allowed_modes = list(entry.get("allowed_modes", defaults.get("allowed_modes", [])))
    public_scraping = entry.get("public_scraping", defaults.get("public_scraping", "policy_check_required"))
    reason = entry.get("reason") or entry.get("notes") or f"Resolved via {source_label}."

    # Determine terms status from public_scraping flag
    if public_scraping is False or (isinstance(public_scraping, str) and public_scraping.startswith("false")):
        terms_status = "restricted"
    elif public_scraping is True:
        terms_status = "allowed"
    else:
        terms_status = "unknown"

    result = SourcePolicyResult(
        domain=domain or url_or_domain,
        allowed=True,
        allowed_modes=allowed_modes,
        blocked_modes=[],
        robots_txt_status="not_checked",
        terms_status=terms_status,
        reason=reason,
    )

    if intended_mode is not None:
        mode = intended_mode.strip()
        # public_metadata maps onto public_metadata_if_allowed for gating
        public_modes = {"public_metadata", "public_metadata_if_allowed"}
        is_allowed = mode in allowed_modes or (
            mode in public_modes and bool(public_modes & set(allowed_modes))
        )
        result.allowed = bool(is_allowed)
        result.blocked_modes = [] if is_allowed else [mode]

        if is_allowed and mode in public_modes:
            # Public metadata always requires robots.txt + ToS check first.
            result.robots_txt_status = "unknown"
            if public_scraping is False or (
                isinstance(public_scraping, str) and public_scraping.startswith("false")
            ):
                result.allowed = False
                result.blocked_modes = [mode]
                result.reason = (
                    f"{reason} Public scraping is disabled for this domain."
                )
                result.safe_next_step = (
                    "Use an official API, search API, or upload a manual CSV export instead."
                )
            else:
                result.safe_next_step = (
                    "Run check_source_policy / verify robots.txt and platform ToS "
                    "before fetching any public page."
                )
        elif is_allowed:
            result.safe_next_step = f"Proceed using collection mode '{mode}'."
        else:
            result.reason = (
                f"{reason} Mode '{mode}' is not in allowed_modes "
                f"({', '.join(allowed_modes) or 'none'})."
            )
            result.safe_next_step = (
                f"Choose one of the allowed modes: {', '.join(allowed_modes) or 'manual_csv'}."
            )

    return result


def is_mode_allowed(url_or_domain: str, mode: str) -> bool:
    return evaluate(url_or_domain, mode).allowed
